"""
Motor de conversacion del chatbot de prediccion de triatlon.
Gestiona el estado de la sesion, extrae parametros de texto libre en espanol
y genera respuestas en lenguaje natural con explicaciones SHAP.
"""
import re
from chatbot.shap_explainer import get_explainer, FEATURE_LABELS

# ---------------------------------------------------------------------------
# Configuracion de parametros del modelo
# ---------------------------------------------------------------------------

PARAMS_CONFIG = {
    "athlete_ranking_triatlon": {
        "question": "¿Cuál es la posición actual del atleta en el ranking general de triatlón?",
        "hint": "Ejemplo: 15 (escribe 999 si no tiene ranking o es debutante)",
        "type": "int",
    },
    "n_races_before": {
        "question": "¿Cuántas carreras ha disputado el atleta en total?",
        "hint": "Ejemplo: 20",
        "type": "int",
    },
    "avg_finish_pos_last_3": {
        "question": "¿Cuál es su posición media en las últimas 3 carreras?",
        "hint": "Ejemplo: 5.5",
        "type": "float",
    },
}

REQUIRED_ORDER = ["athlete_ranking_triatlon", "n_races_before", "avg_finish_pos_last_3"]

# ---------------------------------------------------------------------------
# Deteccion de intencion
# ---------------------------------------------------------------------------

def detect_intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["reset", "nueva pred", "nuevo", "reinici", "empezar", "otra vez", "otro atleta", "limpiar"]):
        return "reset"
    if any(k in t for k in ["ayuda", "help", "como funciona", "que puedes", "instrucciones", "que haces"]):
        return "help"
    if any(k in t for k in ["explica", "por que", "porque", "factores", "shap", "razon", "detalle", "mas info", "mas detalle"]):
        return "explain"
    if any(k in t for k in ["predic", "rendimiento", "como quedara", "resultado", "posicion", "analiza", "analisis"]):
        return "predict"
    return "chat"

# ---------------------------------------------------------------------------
# Extraccion de parametros desde texto libre
# ---------------------------------------------------------------------------

def extract_params(text: str) -> dict:
    t = text.lower()
    params = {}

    # athlete_ranking_triatlon
    m = re.search(r'ranking\s*(\d+)', t)
    if not m:
        m = re.search(r'posici[oó]n\s*(\d+)\s*(?:en\s*el\s*)?ranking', t)
    if m:
        params["athlete_ranking_triatlon"] = int(m.group(1))

    # n_races_before
    m = re.search(r'(\d+)\s*(?:carrera|prueba|competici|vez|veces)', t)
    if m:
        params["n_races_before"] = int(m.group(1))

    # avg_finish_pos_last_3
    m = re.search(r'(?:media|promedio)\s*(?:de\s*)?(?:posici[oó]n\s*)?(\d+(?:[.,]\d+)?)', t)
    if not m:
        m = re.search(r'posici[oó]n\s*(?:media|promedio)\s*(?:de\s*)?(\d+(?:[.,]\d+)?)', t)
    if m:
        val = float(m.group(1).replace(',', '.'))
        params["avg_finish_pos_last_3"] = val
        params.setdefault("avg_finish_pos_last_5", round(val * 1.1, 1))
        params.setdefault("best_finish_pos_ever", max(1.0, round(val * 0.5, 1)))

    # win_rate
    m = re.search(r'(\d+)\s*%\s*(?:de\s*)?victorias', t)
    if m:
        params["win_rate"] = float(m.group(1)) / 100.0

    # race_temperature
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:grados?|°c|ºc|temp)', t)
    if m:
        temp = float(m.group(1).replace(',', '.'))
        params["race_temperature"] = temp

    # days_since_last_race
    m = re.search(r'(\d+)\s*d[iíi]as?\s*(?:desde|sin)', t)
    if m:
        params["days_since_last_race"] = int(m.group(1))

    return params


def try_parse_direct(text: str, param_key: str):
    """Parsea una respuesta directa a la pregunta de un parametro concreto."""
    t = text.strip().lower()
    m = re.search(r'(\d+(?:[.,]\d+)?)', t)
    if m:
        val = float(m.group(1).replace(',', '.'))
        if param_key in ("n_races_before", "athlete_ranking_triatlon", "days_since_last_race"):
            return int(val)
        return val
    return None

# ---------------------------------------------------------------------------
# Generacion de texto de prediccion
# ---------------------------------------------------------------------------

def _prediction_response(result: dict, params: dict) -> str:
    pos = result["prediction"]

    if pos <= 3:
        nivel = "excepcional — candidato al podio"
    elif pos <= 10:
        nivel = "muy alto — top 10 probable"
    elif pos <= 25:
        nivel = "medio — pelotón principal"
    else:
        nivel = "bajo — parte trasera"

    lines = [
        f"**Predicción: Posición {pos:.0f}**",
        f"*Rendimiento {nivel}*\n",
        "**Principales factores (análisis SHAP):**\n",
    ]

    for i, f in enumerate(result["top_factors"], 1):
        # Para la explicación, si impact > 0 significa que su posición sube (peor), así que penaliza.
        # En la UI esto se mapea a rojo/verde, pero aquí mandamos texto.
        arr = "▲" if f["shap_impact"] > 0 else "▼"
        sign = "+" if f["shap_impact"] > 0 else ""
        lines.append(f"  {i}. {arr} *{f['label']}*: {sign}{f['shap_impact']:.1f} posiciones")

    lines.append("")

    if params.get("race_temperature", 0) >= 35:
        lines.append("Calor: Calor extremo detectado — factor de riesgo.")
    hist = int(params.get("n_races_before", 10))
    if hist < 3:
        lines.append("Aviso: Historial muy reducido — predicción con alta incertidumbre.")

    lines.append("\n*Escribe **explicar mas** para el análisis SHAP completo, o **nueva prediccion** para otro atleta.*")
    return "\n".join(lines)


def _full_explain_response(result: dict) -> str:
    lines = [
        f"**Análisis SHAP completo — Posición {result['prediction']:.0f} predicha**\n",
        f"Valor base del modelo: *Posición {result['base_value']:.0f}* (media global del dataset)\n",
        "Impacto de cada variable:\n",
    ]
    for feat, val in sorted(result["shap_values"].items(), key=lambda x: abs(x[1]), reverse=True):
        sign = "+" if val > 0 else ""
        effect = "empeora" if val > 0 else "mejora"
        label = FEATURE_LABELS.get(feat, feat)
        arr = "▲" if val > 0 else "▼"
        lines.append(f"  {arr} **{label}**: {sign}{val:.1f} posiciones ({effect})")
    lines.append("\n*Escribe **nueva prediccion** para analizar otro atleta.*")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Sesion de conversacion
# ---------------------------------------------------------------------------

WELCOME_TEXT = (
    "¡Hola! Soy el asistente de predicción del **Triatlón Élite Masculino**. "
    "Natación + Ciclismo + Running\n\n"
    "Utilizo machine learning con explicaciones **SHAP** para predecir la posición "
    "de los atletas y explicarte *exactamente por qué* el modelo llega a esa conclusión.\n\n"
    "Puedes decirme cosas como:\n"
    "> *\"Atleta con ranking 15, 20 pruebas, y posición media de 5.5\"*\n\n"
    "O escribe **predecir** para que te guíe paso a paso."
)

HELP_TEXT = (
    "**¿Cómo funciono?**\n\n"
    "Soy un chatbot entrenado con datos de la FETRI. Uso **XGBoost + SHAP** para predecir "
    "la posición de llegada de un atleta y explicar qué factores influyen.\n\n"
    "**Para predecir necesito (mínimo):**\n"
    "1. Posición actual en el ranking\n"
    "2. Número total de carreras disputadas\n"
    "3. Posición media en sus últimas 3 carreras\n\n"
    "**Ejemplos de frases que entiendo:**\n"
    "> *\"Ranking 10, 30 carreras, media de posición 4\"*\n"
    "> *\"predecir\"* — te guío con preguntas\n\n"
    "Escribe **predecir** para empezar."
)


class ConversationSession:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = "welcome"
        self.params: dict = {}
        self.pending_param: str | None = None
        self.last_result: dict | None = None

    def process(self, text: str) -> str:
        text = text.strip()
        intent = detect_intent(text)

        if intent == "reset":
            self.reset()
            return "¡Sesión reiniciada! ¿Quieres analizar a otro atleta? Escribe **predecir** o cuéntame sobre el atleta."

        if intent == "help":
            return HELP_TEXT

        if self.state == "welcome":
            return self._from_welcome(text, intent)
        if self.state == "collecting":
            return self._from_collecting(text, intent)
        if self.state == "predicted":
            return self._from_predicted(text, intent)

        return self._from_welcome(text, intent)

    # -- state handlers --

    def _from_welcome(self, text: str, intent: str) -> str:
        extracted = extract_params(text)
        self.params.update(extracted)

        if intent in ("predict", "chat") or extracted:
            self.state = "collecting"
            next_q = self._next_missing()
            if next_q is None:
                return self._predict()
            prefix = "¡Perfecto! Voy a analizar al atleta.\n\n" if not extracted else "He recogido algunos datos. "
            return prefix + self._ask(next_q)

        return WELCOME_TEXT

    def _from_collecting(self, text: str, intent: str) -> str:
        if intent == "explain" and self.last_result:
            return _full_explain_response(self.last_result)

        if self.pending_param:
            val = try_parse_direct(text, self.pending_param)
            if val is not None:
                self.params[self.pending_param] = val
                self.pending_param = None
            else:
                self.params.update(extract_params(text))
        else:
            self.params.update(extract_params(text))

        next_q = self._next_missing()
        if next_q:
            return self._ask(next_q)
        return self._predict()

    def _from_predicted(self, text: str, intent: str) -> str:
        if intent == "explain":
            return _full_explain_response(self.last_result) if self.last_result else "No hay predicción activa."

        if intent in ("predict", "reset") or any(k in text.lower() for k in ["nueva", "otro atleta", "analiza"]):
            self.params = {}
            self.pending_param = None
            self.last_result = None
            self.state = "collecting"
            return "¡Vamos a analizar otro atleta!\n\n" + self._ask("athlete_ranking_triatlon")

        extracted = extract_params(text)
        if extracted:
            self.params.update(extracted)
            return self._predict()

        return (
            "Puedo ayudarte con:\n"
            "- **explicar mas** — ver el análisis SHAP completo\n"
            "- **nueva prediccion** — analizar otro atleta\n"
            "- **ayuda** — ver todas las opciones"
        )

    # -- helpers --

    def _next_missing(self) -> str | None:
        for p in REQUIRED_ORDER:
            if p not in self.params:
                return p
        return None

    def _ask(self, param_key: str) -> str:
        cfg = PARAMS_CONFIG[param_key]
        self.pending_param = param_key
        return f"{cfg['question']}\n\n*{cfg['hint']}*"

    def _predict(self) -> str:
        try:
            explainer = get_explainer()
            result = explainer.explain(self.params, top_n=5)
            self.last_result = result
            self.state = "predicted"
            return _prediction_response(result, self.params)
        except Exception as e:
            return f"Error al calcular la predicción: {e}\n\nEscribe **reset** para reiniciar."


# ---------------------------------------------------------------------------
# Store de sesiones en memoria
# ---------------------------------------------------------------------------

_sessions: dict[str, ConversationSession] = {}


def get_session(sid: str) -> ConversationSession:
    if sid not in _sessions:
        _sessions[sid] = ConversationSession()
    return _sessions[sid]


def reset_session(sid: str) -> ConversationSession:
    _sessions[sid] = ConversationSession()
    return _sessions[sid]
