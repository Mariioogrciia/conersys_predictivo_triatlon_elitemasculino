"""
Integracion con Azure AI Foundry para el chatbot de Triatlon.

Usa function calling: el LLM decide cuando invocar la prediccion SHAP,
extrae los parametros del lenguaje natural y genera la respuesta.

Variables de entorno necesarias:
  AZURE_FOUNDRY_ENDPOINT   -> https://<resource>.openai.azure.com/
  AZURE_FOUNDRY_KEY        -> tu API key de Azure AI Foundry
  AZURE_FOUNDRY_MODEL      -> nombre del deployment (ej: gpt-4o, gpt-4o-mini)
  AZURE_FOUNDRY_API_VERSION -> (opcional) version de la API, default 2024-12-01-preview
"""
import os
import json
from chatbot.shap_explainer import get_explainer, FEATURE_LABELS
from chatbot import race_lookup

# ---------------------------------------------------------------------------
# System prompt del asistente
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres "Coach", el comentarista y analista oficial experto en triatlón de élite masculino de la FETRI. Vives y respiras este deporte. Tu misión es predecir y comentar el rendimiento de los atletas utilizando el modelo predictivo de Inteligencia Artificial (Azure Machine Learning) del que dispones.

==========================
TEMÁTICA Y TONO
==========================
- Hablas ÚNICAMENTE de triatlón (atletas, carreras, segmentos, clima, rendimiento).
- Rechazas cualquier pregunta fuera de este ámbito de forma firme pero profesional.
- Tu tono es el de un analista deportivo riguroso, claro y mesurado.
- NUNCA uses jerga informática con el usuario ("machine learning", "SHAP", "JSON", "XGBoost", "features"). Traduce la matemática a "lenguaje de carrera" ("el estado de forma reciente", "su experiencia", "las condiciones de calor").

==========================
CÓMO FUNCIONA EL MODELO PREDICTIVO (¡CRÍTICO!)
==========================
El modelo analiza a los atletas y predice directamente su POSICIÓN FINAL ESPERADA en la meta (de la 1 a la 60+). NUNCA PREDICE "PUNTOS".
- Posición 1.0 - 3.0: Nivel excepcional, claro candidato a ganar o pisar el podio.
- Posición 4.0 - 10.0: Nivel muy alto, lucha por los puestos de honor (Top 10).
- Posición 11.0 - 25.0: Nivel medio-alto, sólido competidor en el grupo perseguidor.
- Posición 26.0+: Parte trasera del pelotón o con dificultades bajo estas condiciones.

==========================
CÓMO INTERPRETAR LOS FACTORES MATEMÁTICOS (SHAP)
==========================
El modelo te pasará los factores que alteran la posición de un atleta. Tienes que leerlos así:
- Impacto POSITIVO (+): SIGNIFICA QUE EMPEORA AL ATLETA. Suma números a su posición (por ejemplo, le hace pasar del puesto 5 al 12). Se lee como: "Le penaliza", "Le retrasa", "Juega en su contra".
- Impacto NEGATIVO (-): SIGNIFICA QUE FAVORECE AL ATLETA. Resta números a su posición (por ejemplo, le hace pasar del puesto 10 al 4). Se lee como: "Le beneficia", "Le empuja hacia el podio", "Juega a su favor".
- Nunca leas los números exactos con decimales aburridos, intégralos en tu discurso (ej: "Su histórico de abandonos le penaliza severamente, apartándolo de los puestos de cabeza...").

==========================
TUS HERRAMIENTAS Y CÓMO USARLAS
==========================
Tienes acceso a datos reales mediante herramientas:
1. `resultados_carrera`: Úsala si el usuario pregunta quién ganó o cómo quedó una prueba concreta del calendario. Si no hay resultados cargados en la base de datos, díselo e invítale a simular la carrera.
2. `buscar_carrera`: Úsala SIEMPRE que se mencione una prueba futura o pasada de la que se quiera simular algo, para obtener sus condiciones reales (temperatura, altitud, etc).
3. `analizar_atleta_oficial`: ¡Tú superpoder! Úsala SIEMPRE que el usuario te pregunte por qué un atleta real (ej. "David Cantero") está en cierta posición, o pida un análisis de su perfil. La herramienta buscará su historial real en la base de datos de la FETRI y te dará su posición base estimada y sus fortalezas/debilidades reales.
4. `predecir_rendimiento`: Úsala para predicciones hipotéticas o inventadas por el usuario, rellenando tú mismo los parámetros que intuyas a partir de su descripción verbal.

==========================
REGLAS FINALES
==========================
- Si no sabes algo, usa las herramientas antes de rendirte.
- Si una carrera no existe, ofrece simular una con condiciones inventadas.
- Si te piden predecir sin darte datos apenas, invéntate tú el perfil estándar en los parámetros y dale una respuesta, ¡nunca pidas requisitos mínimos!
- Responde siempre en español, de forma estructurada pero fluida.
- FORMATO: NO uses sintaxis Markdown (no uses '#', '##', asteriscos '**', ni listas numeradas complejas). Usa texto plano puro, separando las ideas con saltos de línea normales y utilizando emojis discretos (ej: 🔸 o 🔹) para enumerar puntos si es estrictamente necesario."""

# ---------------------------------------------------------------------------
# Definicion de la herramienta SHAP (function calling)
# ---------------------------------------------------------------------------

PREDICTION_TOOL = {
    "type": "function",
    "function": {
        "name": "predecir_rendimiento",
        "description": (
            "Predice la POSICIÓN EXACTA que obtendrá un atleta de triatlón en una prueba y devuelve "
            "los factores que más influyen. Llámala con CUALQUIER dato que tengas, aunque sea "
            "solo uno o ninguno: los campos que no pases se rellenan automáticamente con valores "
            "normales. NO esperes a tener todos los datos; predice con lo disponible."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "athlete_age_at_race": {
                    "type": "number",
                    "description": "Edad del atleta en el momento de la carrera."
                },
                "athlete_federation": {
                    "type": "string",
                    "description": "Federacion autonómica o nacional del atleta."
                },
                "athlete_ranking_triatlon": {
                    "type": "number",
                    "description": "Posicion actual del atleta en el ranking de triatlon de la FETRI (1 = mejor)."
                },
                "athlete_has_wt_id": {
                    "type": "integer",
                    "description": "Si el atleta tiene identificador de World Triathlon (1) o no (0)."
                },
                "n_races_before": {
                    "type": "integer",
                    "description": "Numero total de pruebas disputadas por el atleta a lo largo de su carrera."
                },
                "n_elite_races_before": {
                    "type": "integer",
                    "description": "Numero de carreras de nivel elite disputadas previamente."
                },
                "avg_finish_pos_last_3": {
                    "type": "number",
                    "description": "Posicion media de llegada en sus ultimas 3 carreras."
                },
                "avg_finish_pos_last_5": {
                    "type": "number",
                    "description": "Posicion media de llegada en sus ultimas 5 carreras."
                },
                "best_finish_pos_ever": {
                    "type": "number",
                    "description": "Mejor posicion de llegada en toda su carrera."
                },
                "best_finish_pos_season": {
                    "type": "number",
                    "description": "Mejor posicion de llegada en la temporada actual."
                },
                "avg_swim_rank_last_5": {
                    "type": "number",
                    "description": "Posicion media en natacion en las ultimas 5 carreras."
                },
                "avg_bike_rank_last_5": {
                    "type": "number",
                    "description": "Posicion media en ciclismo en las ultimas 5 carreras."
                },
                "avg_run_rank_last_5": {
                    "type": "number",
                    "description": "Posicion media en carrera a pie en las ultimas 5 carreras."
                },
                "win_rate": {
                    "type": "number",
                    "description": "Porcentaje de victorias (0.0 a 1.0). Ej: 0.15 = gana el 15% de sus carreras."
                },
                "podium_rate": {
                    "type": "number",
                    "description": "Porcentaje de podios (top 3) sobre total de carreras (0.0 a 1.0)."
                },
                "top10_rate": {
                    "type": "number",
                    "description": "Porcentaje de top 10 sobre total de carreras (0.0 a 1.0)."
                },
                "dnf_rate": {
                    "type": "number",
                    "description": "Porcentaje de abandonos sobre total de carreras (0.0 a 1.0)."
                },
                "days_since_last_race": {
                    "type": "integer",
                    "description": "Dias transcurridos desde la ultima competicion del atleta."
                },
                "ranking_momentum": {
                    "type": "number",
                    "description": "Impulso reciente del atleta en puntos o rendimiento."
                },
                "ranking_trend": {
                    "type": "string",
                    "description": "Tendencia reciente del ranking: subiendo, bajando o estable."
                },
                "ranking_change_recent": {
                    "type": "number",
                    "description": "Cambio reciente observado en su nivel o puntos."
                },
                "race_temperature": {
                    "type": "number",
                    "description": "Temperatura maxima prevista para la prueba en grados Celsius."
                },
                "race_humidity": {
                    "type": "number",
                    "description": "Humedad media prevista para la prueba en porcentaje (0-100)."
                },
                "race_altitude_m": {
                    "type": "number",
                    "description": "Altitud de la prueba en metros sobre el nivel del mar."
                },
                "race_lat": {
                    "type": "number",
                    "description": "Latitud de la prueba."
                },
                "race_lng": {
                    "type": "number",
                    "description": "Longitud de la prueba."
                },
                "race_city": {
                    "type": "string",
                    "description": "Ciudad donde se celebra la prueba."
                },
                "race_near_coast": {
                    "type": "integer",
                    "description": "1 si la prueba es cerca de la costa, 0 si es interior."
                },
                "race_climate_type": {
                    "type": "string",
                    "description": "Tipo de clima dominante en la prueba."
                },
                "race_month": {
                    "type": "integer",
                    "description": "Mes de la carrera (1-12)."
                },
                "race_day_of_week": {
                    "type": "integer",
                    "description": "Dia de la semana de la carrera (0=lunes, 6=domingo)."
                },
                "race_type": {
                    "type": "string",
                    "description": "Tipo de carrera: sprint, olimpico, etc."
                },
                "form_score": {
                    "type": "number",
                    "description": "Estado de forma actual del atleta (0 a 100, donde 100 es la mejor forma)."
                },
                "avg_pos_high_altitude": {
                    "type": "number",
                    "description": "Posicion media historica del atleta en carreras de altura."
                },
                "avg_pos_low_altitude": {
                    "type": "number",
                    "description": "Posicion media historica del atleta en carreras a baja altitud."
                },
                "avg_pos_coastal": {
                    "type": "number",
                    "description": "Posicion media historica del atleta en carreras costeras."
                },
                "avg_pos_inland": {
                    "type": "number",
                    "description": "Posicion media historica del atleta en carreras de interior."
                },
                "avg_pos_hot": {
                    "type": "number",
                    "description": "Posicion media historica del atleta con calor."
                },
                "avg_pos_cold": {
                    "type": "number",
                    "description": "Posicion media historica del atleta con frio."
                },
                "performance_altitude_bias": {
                    "type": "number",
                    "description": "Sesgo de rendimiento del atleta en altura."
                },
                "performance_coast_bias": {
                    "type": "number",
                    "description": "Sesgo de rendimiento del atleta en costa."
                },
                "performance_heat_bias": {
                    "type": "number",
                    "description": "Sesgo de rendimiento del atleta con calor."
                },
                "n_participants_race": {
                    "type": "number",
                    "description": "Numero estimado de participantes en la carrera."
                },
                "avg_ranking_opponents": {
                    "type": "number",
                    "description": "Ranking medio de los rivales de la carrera."
                },
                "pct_opponents_ranked_higher": {
                    "type": "number",
                    "description": "Porcentaje de rivales con mejor ranking que el atleta."
                },
                "n_races_at_city": {
                    "type": "integer",
                    "description": "Numero de carreras previas del atleta en esa ciudad."
                },
                "n_previous_wins_at_city": {
                    "type": "integer",
                    "description": "Numero de victorias previas del atleta en esa ciudad."
                },
                "position_std_dev": {
                    "type": "number",
                    "description": "Desviacion estandar de sus posiciones historicas."
                },
                "current_podium_streak": {
                    "type": "integer",
                    "description": "Racha actual de podios consecutivos."
                },
                "current_top10_streak": {
                    "type": "integer",
                    "description": "Racha actual de top 10 consecutivos."
                },
            },
            "required": [],
        },
    },
}

RACE_TOOL = {
    "type": "function",
    "function": {
        "name": "buscar_carrera",
        "description": (
            "Busca en el calendario oficial de la FETRI una carrera de triatlon por su nombre o "
            "ciudad y devuelve su localizacion, fecha, altitud, coordenadas y condiciones climaticas "
            "(temperatura, humedad, lluvia, viento) y nivel de campeonato. Usala SIEMPRE que el "
            "usuario mencione el nombre o la ciudad de una prueba, antes de predecir, para usar "
            "datos reales."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "Nombre o ciudad de la carrera a buscar. Ej: 'Banyoles', 'Campeonato de Espana Pontevedra'."
                },
            },
            "required": ["consulta"],
        },
    },
}

RESULTS_TOOL = {
    "type": "function",
    "function": {
        "name": "resultados_carrera",
        "description": (
            "Devuelve la clasificacion REAL (ganador y primeros puestos, con nombres de atletas y "
            "clubes) de una carrera de triatlon ya disputada de la temporada 2025. Usala SIEMPRE que "
            "el usuario pregunte quien gano, quien quedo primero, el podio o la clasificacion de una "
            "prueba concreta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "Nombre o ciudad de la carrera. Ej: 'A Coruna', 'Campeonato de Espana Sprint'."
                },
                "top_n": {
                    "type": "integer",
                    "description": "Cuantos puestos devolver (por defecto 5)."
                },
            },
            "required": ["consulta"],
        },
    },
}

EXPLAIN_ATHLETE_TOOL = {
    "type": "function",
    "function": {
        "name": "analizar_atleta_oficial",
        "description": (
            "Busca el perfil oficial de un atleta en la base de datos, extrae sus métricas reales y "
            "calcula la explicación matemática (SHAP) de su rendimiento esperado. "
            "Úsala SIEMPRE que el usuario pregunte por qué un atleta está en una posición concreta, "
            "o pida una explicación del nivel o rendimiento de una persona específica."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre_atleta": {
                    "type": "string",
                    "description": "Nombre del atleta a analizar (ej. 'David Cantero', 'Eloy Canales')."
                },
            },
            "required": ["nombre_atleta"],
        },
    },
}

TOOLS = [PREDICTION_TOOL, RACE_TOOL, RESULTS_TOOL, EXPLAIN_ATHLETE_TOOL]

# ---------------------------------------------------------------------------
# Ejecucion de herramientas
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, raw_args: str) -> str:
    """Ejecuta la herramienta solicitada por el LLM y devuelve el resultado como JSON."""
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        return json.dumps({"error": "Argumentos JSON invalidos"})

    # --- Busqueda de carrera ---
    if tool_name == "buscar_carrera":
        try:
            return json.dumps(
                race_lookup.buscar(args.get("consulta", "")),
                ensure_ascii=False, indent=2, default=str
            )
        except Exception as e:
            return json.dumps({"error": f"Error buscando la carrera: {str(e)}"})

    # --- Resultados / clasificacion de una carrera ---
    if tool_name == "resultados_carrera":
        try:
            return json.dumps(
                race_lookup.resultados(args.get("consulta", ""), int(args.get("top_n", 5))),
                ensure_ascii=False, indent=2, default=str
            )
        except Exception as e:
            return json.dumps({"error": f"Error obteniendo resultados: {str(e)}"})

    # --- Analizar Atleta Oficial ---
    if tool_name == "analizar_atleta_oficial":
        try:
            from chatbot.database_service import get_active_athletes, get_athletes_history_batch
            from chatbot.chatbot_api import build_athlete_features
            
            nombre_query = args.get("nombre_atleta", "").lower()
            athletes = get_active_athletes()
            history_map = get_athletes_history_batch()
            
            # Calculate ranking for ALL athletes (same logic as /api/ranking)
            for ath in athletes:
                doc = ath["documento"]
                hist = history_map.get(doc, [])
                puntos = sorted([h.get("puntos", 0) for h in hist if h.get("puntos") is not None], reverse=True)[:3]
                ath["total_puntos"] = sum(puntos)
                ath["n_elite"] = sum(1 for h in hist if (h.get("championship_level") or 3) <= 2)
            
            athletes.sort(key=lambda x: x["total_puntos"], reverse=True)
            for i, ath in enumerate(athletes):
                ath["ranking_real"] = float(i + 1)
            
            # Find the target athlete
            target_ath = None
            for ath in athletes:
                if nombre_query in ath["nombre"].lower():
                    target_ath = ath
                    break
                    
            if not target_ath:
                return json.dumps({"error": f"No se encontró al atleta '{nombre_query}' en la base de datos."})
                
            history = history_map.get(target_ath["documento"], [])
            
            features = build_athlete_features(target_ath, history)
            
            explainer = get_explainer()
            result = explainer.explain(features, top_n=7)
            
            return json.dumps({
                "atleta": target_ath["nombre"],
                "club": target_ath["club"],
                "posicion_estimada_base": round(result["prediction"], 1),
                "explicacion_resumen": result["explanation_text"],
                "top_factores": [
                    {
                        "factor": FEATURE_LABELS.get(f["feature"], f["feature"]),
                        "impacto_puestos": round(f["shap_impact"], 1),
                        "efecto": "mejora prediccion" if f["shap_impact"] < 0 else "empeora prediccion",
                        "valor_utilizado": f["value"],
                    }
                    for f in result["top_factors"]
                ]
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error analizando atleta: {str(e)}"})

    if tool_name != "predecir_rendimiento":
        return json.dumps({"error": f"Herramienta desconocida: {tool_name}"})

    try:
        explainer = get_explainer()
        result = explainer.explain(args, top_n=7)

        return json.dumps({
            "posicion_estimada": round(result["prediction"], 1),
            "valor_base_modelo": round(result["base_value"], 1),
            "nota_valor_base": "Posición media esperada del dataset. La diferencia con la predicción final se explica sumando y restando los impactos SHAP.",
            "top_factores": [
                {
                    "factor": FEATURE_LABELS.get(f["feature"], f["feature"]),
                    "impacto_puestos": round(f["shap_impact"], 1),
                    "efecto": "mejora prediccion" if f["shap_impact"] < 0 else "empeora prediccion",
                    "valor_utilizado": f["value"],
                }
                for f in result["top_factors"]
            ],
            "todos_los_factores": {
                FEATURE_LABELS.get(feat, feat): round(val, 2)
                for feat, val in result["shap_values"].items()
            },
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error en la prediccion: {str(e)}"})

# ---------------------------------------------------------------------------
# Cliente Azure AI Foundry
# ---------------------------------------------------------------------------

def is_configured() -> bool:
    """Devuelve True si las variables de entorno de AI Foundry estan definidas."""
    return bool(os.getenv("AZURE_FOUNDRY_ENDPOINT")) and bool(os.getenv("AZURE_FOUNDRY_KEY"))


def ping() -> dict:
    """
    Verifica que el modelo de AI Foundry responde.
    Devuelve {ok: bool, detail: str, model: str}.
    """
    if not is_configured():
        return {"ok": False, "detail": "No configurado (.env)", "model": "—"}

    model = os.getenv("AZURE_FOUNDRY_MODEL", "gpt-4o")
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=3,
        )
        _ = resp.choices[0].message.content
        return {"ok": True, "detail": "Conectado", "model": model}
    except Exception as e:
        err = str(e)
        if "DeploymentNotFound" in err or "404" in err:
            detail = f"Deployment '{model}' no encontrado"
        elif "401" in err or "Unauthorized" in err:
            detail = "API Key invalida"
        else:
            detail = err[:120]
        return {"ok": False, "detail": detail, "model": model}


def _get_client():
    """Crea y devuelve el cliente AzureOpenAI."""
    from openai import AzureOpenAI  # openai >= 1.0

    endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT", "").rstrip("/")
    api_key  = os.getenv("AZURE_FOUNDRY_KEY", "")
    version  = os.getenv("AZURE_FOUNDRY_API_VERSION", "2024-08-01-preview")

    if not endpoint or not api_key:
        raise EnvironmentError(
            "Faltan variables de entorno: AZURE_FOUNDRY_ENDPOINT y AZURE_FOUNDRY_KEY"
        )

    return AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=version)


def chat(history: list[dict]) -> tuple[str, list[dict]]:
    """
    Envia el historial al modelo de AI Foundry y gestiona el function calling.

    Args:
        history: Lista de mensajes en formato OpenAI (sin system prompt).
                 Ejemplo: [{"role": "user", "content": "Predice para ..."}]

    Returns:
        (respuesta_texto, historial_actualizado)
        El historial actualizado incluye todos los mensajes del turno actual
        y puede guardarse para el siguiente turno.
    """
    model  = os.getenv("AZURE_FOUNDRY_MODEL", "gpt-4o")
    client = _get_client()

    # Evitar limite de tokens recortando mensajes antiguos
    char_count = sum(len(str(m.get("content", ""))) for m in history)
    while char_count > 15000 and len(history) > 2:
        popped = history.pop(0)
        char_count -= len(str(popped.get("content", "")))
        # Asegurar que el historial que queda empieza con un mensaje de 'user' u 'assistant' sin colgar 'tool' responses solos
        while history and history[0].get("role") == "tool":
            popped = history.pop(0)
            char_count -= len(str(popped.get("content", "")))

    # Construir el contexto completo con el system prompt
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    # Agentic loop: iterar hasta obtener respuesta sin tool calls (max 5 rondas)
    for _ in range(5):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1200,
        )

        msg = response.choices[0].message

        # Sin tool calls -> respuesta final del LLM
        if not msg.tool_calls:
            final_text = msg.content or ""
            history = history + [{"role": "assistant", "content": final_text}]
            return final_text, history

        # El LLM quiere llamar a una herramienta
        # 1. Registrar la respuesta del asistente con los tool_calls
        assistant_msg: dict = {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id":       tc.id,
                    "type":     "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        }
        messages.append(assistant_msg)
        history  = history + [assistant_msg]

        # 2. Ejecutar cada tool call y registrar el resultado
        for tc in msg.tool_calls:
            tool_result = execute_tool(tc.function.name, tc.function.arguments)
            tool_msg: dict = {
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      tool_result,
            }
            messages.append(tool_msg)
            history = history + [tool_msg]

    return "Se alcanzó el limite de iteraciones. Por favor, reformula tu pregunta.", history
