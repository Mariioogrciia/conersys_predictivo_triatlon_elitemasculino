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
    "HIST_COUNT_PRUEBAS": {
        "question": "Cuantas pruebas ha disputado el atleta en total?",
        "hint": "Ejemplo: 15",
        "type": "int",
    },
    "RECENT_AVG_PUNTOS": {
        "question": "Cual es la media de puntos en sus ultimas pruebas?",
        "hint": "Ejemplo: 1200 — si no lo sabes escribe 0",
        "type": "float",
    },
    "CHAMPIONSHIP_LEVEL": {
        "question": "Cual es el nivel del campeonato?\n**1** = Nacional / Europeo\n**2** = Regional / Autonomico\n**3** = Provincial / Local",
        "hint": "Escribe 1, 2 o 3",
        "type": "int",
    },
}

REQUIRED_ORDER = ["HIST_COUNT_PRUEBAS", "RECENT_AVG_PUNTOS", "CHAMPIONSHIP_LEVEL"]

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
    if any(k in t for k in ["predic", "rendimiento", "como quedara", "resultado", "puntos que", "analiza", "analisis", "cuantos puntos"]):
        return "predict"
    return "chat"

# ---------------------------------------------------------------------------
# Extraccion de parametros desde texto libre
# ---------------------------------------------------------------------------

def extract_params(text: str) -> dict:
    t = text.lower()
    params = {}

    # HIST_COUNT_PRUEBAS
    m = re.search(r'(\d+)\s*(?:prueba|carrera|competici|vez|veces)', t)
    if m:
        params["HIST_COUNT_PRUEBAS"] = int(m.group(1))

    # RECENT_AVG_PUNTOS / HIST_AVG_PUNTOS
    m = re.search(r'(?:media|promedio|avg)\s+(?:de\s+)?(\d+(?:[.,]\d+)?)\s*(?:puntos?|pts)?', t)
    if not m:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*puntos?\s*de\s*(?:media|promedio)', t)
    if not m:
        m = re.search(r'(\d{3,4}(?:[.,]\d+)?)\s*puntos?(?!\s*de\s*(?:nivel|campeonato))', t)
    if m:
        val = float(m.group(1).replace(',', '.'))
        params["RECENT_AVG_PUNTOS"] = val
        params.setdefault("HIST_AVG_PUNTOS", round(val * 0.9, 1))
        params.setdefault("HIST_MAX_PUNTOS", round(val * 1.4, 1))
        params.setdefault("HIST_STD_PUNTOS", round(val * 0.2, 1))

    # CHAMPIONSHIP_LEVEL — "campeonato local/provincial" = nivel 3, no confundir con ES_LOCAL
    if any(k in t for k in ["nacional", "europeo", "mundial", "nivel 1", "nivel uno"]):
        params["CHAMPIONSHIP_LEVEL"] = 1
    elif any(k in t for k in ["regional", "autonomic", "nivel 2", "nivel dos"]):
        params["CHAMPIONSHIP_LEVEL"] = 2
    elif any(k in t for k in ["provincial", "nivel 3", "nivel tres", "campeonato local", "camp. local"]):
        params["CHAMPIONSHIP_LEVEL"] = 3

    # ES_LOCAL — "prueba local", "compite en casa", "es local" (sin ser nivel campeonato)
    local_pos = t.find("local")
    if local_pos >= 0:
        before = t[max(0, local_pos - 20):local_pos]
        if "campeonato" not in before and "nivel" not in before and "camp." not in before:
            params["ES_LOCAL"] = 1
    if any(k in t for k in ["en casa", "su ciudad", "de casa", "juega en casa"]):
        params["ES_LOCAL"] = 1
    if any(k in t for k in ["fuera", "desplaz", "visitante", "no es local"]):
        params["ES_LOCAL"] = 0

    # TEMPERATURA_MAX
    m = re.search(r'(\d+)\s*(?:grados?|°c|ºc|temp)', t)
    if m:
        temp = float(m.group(1))
        params["TEMPERATURA_MAX"] = temp
        if temp >= 35:
            params["IS_EXTREME_HEAT"] = 1

    # IS_EXTREME_HEAT
    if any(k in t for k in ["calor extremo", "mucho calor", "ola de calor", "calor intenso"]):
        params["IS_EXTREME_HEAT"] = 1

    # IS_WET_RACE
    if any(k in t for k in ["lluvia", "lluvioso", "mojad", "wet", "agua"]):
        params["IS_WET_RACE"] = 1

    # DAYS_SINCE_LAST_RACE
    m = re.search(r'(\d+)\s*d[iíi]as?\s*(?:desde|de descanso|sin competi|de recupera)', t)
    if m:
        params["DAYS_SINCE_LAST_RACE"] = int(m.group(1))

    # FATIGUE_INDEX
    if any(k in t for k in ["muy fatigado", "muy cansado", "agotado", "sin fuerzas"]):
        params["FATIGUE_INDEX"] = 0.9
    elif any(k in t for k in ["fatigado", "cansado", "con fatiga"]):
        params["FATIGUE_INDEX"] = 0.5
    elif any(k in t for k in ["descansado", "fresco", "recuperado", "en forma"]):
        params["FATIGUE_INDEX"] = 0.1

    # VIAJE_DISTANCIA_KM
    m = re.search(r'(\d+)\s*km\s*(?:de viaje|desde|de distancia|de su casa)', t)
    if m:
        params["VIAJE_DISTANCIA_KM"] = float(m.group(1))

    # ALTITUD
    m = re.search(r'(\d+)\s*m(?:etros?)?\s*(?:de altitud|snm|sobre el mar|sobre nivel)', t)
    if m:
        params["ALTITUD"] = float(m.group(1))

    return params


def try_parse_direct(text: str, param_key: str):
    """Parsea una respuesta directa a la pregunta de un parametro concreto."""
    t = text.strip().lower()
    if param_key == "ES_LOCAL":
        if any(k in t for k in ["si", "yes", "s", "1", "casa", "local"]):
            return 1
        if any(k in t for k in ["no", "n", "0", "fuera"]):
            return 0
        return None
    if param_key == "CHAMPIONSHIP_LEVEL":
        if "1" in t or "nacional" in t or "europeo" in t:
            return 1
        if "2" in t or "regional" in t:
            return 2
        if "3" in t or "provincial" in t or "local" in t:
            return 3
    m = re.search(r'(\d+(?:[.,]\d+)?)', t)
    if m:
        val = float(m.group(1).replace(',', '.'))
        if param_key in ("HIST_COUNT_PRUEBAS", "CHAMPIONSHIP_LEVEL", "DAYS_SINCE_LAST_RACE"):
            return int(val)
        return val
    return None

# ---------------------------------------------------------------------------
# Generacion de texto de prediccion
# ---------------------------------------------------------------------------

def _prediction_response(result: dict, params: dict) -> str:
    pts = result["prediction"]

    if pts >= 1600:
        nivel = "excepcional — candidato al podio"
        icon = "Medalla de oro"
    elif pts >= 1200:
        nivel = "muy alto — top 5 probable"
        icon = "Trofeo"
    elif pts >= 800:
        nivel = "alto — clasificacion top-10"
        icon = "Bien"
    elif pts >= 400:
        nivel = "medio"
        icon = "Grafico"
    else:
        nivel = "bajo — por debajo de la media"
        icon = "Aviso"

    lines = [
        f"**Prediccion: {pts:.0f} puntos**",
        f"*Rendimiento {nivel}*\n",
        "**Principales factores (analisis SHAP):**\n",
    ]

    for i, f in enumerate(result["top_factors"], 1):
        arr = "▲" if f["shap_impact"] > 0 else "▼"
        sign = "+" if f["shap_impact"] > 0 else ""
        lines.append(f"  {i}. {arr} *{f['label']}*: {sign}{f['shap_impact']:.0f} pts")

    lines.append("")

    if params.get("ES_LOCAL") == 1:
        lines.append("Casa: Compite en casa — ventaja local aplicada.")
    if params.get("IS_EXTREME_HEAT") == 1:
        lines.append("Calor: Calor extremo — factor de riesgo.")
    if params.get("IS_WET_RACE") == 1:
        lines.append("Lluvia: Prueba lluviosa — condiciones variables.")
    hist = int(params.get("HIST_COUNT_PRUEBAS", 10))
    if hist < 3:
        lines.append("Aviso: Historial muy reducido — prediccion con alta incertidumbre.")

    lines.append("\n*Escribe **explicar mas** para el analisis SHAP completo, o **nueva prediccion** para otro atleta.*")
    return "\n".join(lines)


def _full_explain_response(result: dict) -> str:
    lines = [
        f"**Analisis SHAP completo — {result['prediction']:.0f} puntos predichos**\n",
        f"Valor base del modelo: *{result['base_value']:.0f} pts* (media global del dataset)\n",
        "Impacto de cada variable:\n",
    ]
    for feat, val in sorted(result["shap_values"].items(), key=lambda x: abs(x[1]), reverse=True):
        sign = "+" if val > 0 else ""
        effect = "favorece" if val > 0 else "penaliza"
        label = FEATURE_LABELS.get(feat, feat)
        arr = "▲" if val > 0 else "▼"
        lines.append(f"  {arr} **{label}**: {sign}{val:.1f} pts ({effect})")
    lines.append("\n*Escribe **nueva prediccion** para analizar otro atleta.*")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Sesion de conversacion
# ---------------------------------------------------------------------------

WELCOME_TEXT = (
    "Hola! Soy el asistente de prediccion del **Triatlon Elite Masculino**. "
    "Natacion + Ciclismo + Running\n\n"
    "Utilizo machine learning con explicaciones **SHAP** para predecir el rendimiento "
    "de los atletas y explicarte *exactamente por que* el modelo llega a esa prediccion.\n\n"
    "Puedes decirme cosas como:\n"
    "> *\"Atleta con 15 pruebas, media de 1200 puntos, campeonato regional, prueba local\"*\n\n"
    "O escribe **predecir** para que te guie paso a paso."
)

HELP_TEXT = (
    "**Como funciono?**\n\n"
    "Soy un chatbot entrenado con datos de la FETRI. Uso **XGBoost + SHAP** para predecir "
    "los puntos de un atleta y explicar que factores influyen.\n\n"
    "**Para predecir necesito (minimo):**\n"
    "1. Numero total de pruebas disputadas\n"
    "2. Media de puntos reciente del atleta\n"
    "3. Nivel del campeonato (1=Nacional, 2=Regional, 3=Provincial)\n\n"
    "**Opcionales que mejoran la prediccion:**\n"
    "Temperatura, si es local o fuera, fatiga, dias de descanso...\n\n"
    "**Ejemplos de frases que entiendo:**\n"
    "> *\"20 pruebas, 1400 puntos de media, nacional, prueba local\"*\n"
    "> *\"Atleta novato con 3 carreras y 200 puntos, regional, mucho calor\"*\n"
    "> *\"predecir\"* — te guio con preguntas\n\n"
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
            return "Sesion reiniciada! Quieres analizar a otro atleta? Escribe **predecir** o cuentame sobre el atleta."

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
            prefix = "Perfecto! Voy a analizar al atleta.\n\n" if not extracted else "He recogido algunos datos. "
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
            return _full_explain_response(self.last_result) if self.last_result else "No hay prediccion activa."

        if intent in ("predict", "reset") or any(k in text.lower() for k in ["nueva", "otro atleta", "analiza"]):
            self.params = {}
            self.pending_param = None
            self.last_result = None
            self.state = "collecting"
            return "Vamos a analizar otro atleta!\n\n" + self._ask("HIST_COUNT_PRUEBAS")

        extracted = extract_params(text)
        if extracted:
            self.params.update(extracted)
            return self._predict()

        return (
            "Puedo ayudarte con:\n"
            "- **explicar mas** — ver el analisis SHAP completo\n"
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
            return f"Error al calcular la prediccion: {e}\n\nEscribe **reset** para reiniciar."


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
