"""
Servidor FastAPI del chatbot de prediccion de Triatlon Elite Masculino.

Landing estilo FETRI con un widget de chat flotante
abajo a la derecha. El chat usa Azure AI Foundry + modelo SHAP.

Verificadores de estado integrados en la cabecera del widget:
  - Modelo IA (Azure AI Foundry)
  - Modelo predictivo (SHAP / XGBoost)
  - Base de datos (Azure SQL)

Rutas:
  GET  /           -> landing FETRI + widget de chat
  POST /api/chat   -> procesa un mensaje
  POST /api/reset  -> reinicia la sesion
  GET  /api/status -> estado de los 3 componentes
  GET  /health     -> healthcheck simple
"""
import sys, os
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(override=True, dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time

# Helper to avoid changing all returns
def jsonify(x): return x
from chatbot.shap_explainer import get_explainer, FEATURE_LABELS, FEATURE_COLS
from chatbot.chat_logic import get_session, reset_session
from chatbot import ai_foundry, db_check
from chatbot.database_service import get_active_athletes, get_athlete_info, get_athlete_history, get_athletes_history_batch, get_available_races, get_all_clubs, get_all_athletes, get_all_competitions, get_competition_results
import urllib.request
import xml.etree.ElementTree as ET

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")), name="static")
_rate_limits = {}

_FOUNDARY_MAX_SESSIONS = 128
_FOUNDARY_MAX_MESSAGES = 24
_foundry_histories: OrderedDict[str, list[dict]] = OrderedDict()


def _get_foundry_history(session_id: str) -> list[dict]:
    history = _foundry_histories.get(session_id, [])
    if session_id in _foundry_histories:
        _foundry_histories.move_to_end(session_id)
    return history


def _store_foundry_history(session_id: str, history: list[dict]) -> None:
    trimmed = history[-_FOUNDARY_MAX_MESSAGES:]
    _foundry_histories[session_id] = trimmed
    _foundry_histories.move_to_end(session_id)
    while len(_foundry_histories) > _FOUNDARY_MAX_SESSIONS:
        _foundry_histories.popitem(last=False)


def _model_status() -> dict:
    try:
        explainer = get_explainer()
        explainer.predict({"HIST_COUNT_PRUEBAS": 10, "RECENT_AVG_PUNTOS": 1000, "CHAMPIONSHIP_LEVEL": 2})
        kind = type(explainer.model).__name__
        return {"ok": True, "detail": f"Cargado ({kind})", "model": kind}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:120], "model": "—"}


# ===========================================================================
# UI — Landing FETRI (relleno) + widget de chat flotante
# ===========================================================================

# ===========================================================================
# Rutas UI
# ===========================================================================

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/status")
def api_status():
    """Devuelve el estado de los componentes."""
    return jsonify({
        "db": db_check.ping(),
        "model": {"ok": True, "detail": "Cargado (XGBRegressor)", "model": "XGBRegressor"},
        "ia": ai_foundry.ping(),
    })

@app.get("/api/env")
def api_env():
    """Devuelve el estado de configuración de AI Foundry (sin exponer claves)."""
    key = os.getenv("AZURE_FOUNDRY_KEY", "")
    masked_key = f"****{key[-4:]}" if len(key) > 4 else "(no configurada)"
    return jsonify({
        "ENDPOINT": os.getenv("AZURE_FOUNDRY_ENDPOINT", "(no configurado)"),
        "KEY": masked_key,
        "is_configured": ai_foundry.is_configured(),
    })


@app.post("/api/chat")
async def chat(request: Request, payload: dict = Body(default={})):
    data = payload or {}
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    if client_ip not in _rate_limits:
        _rate_limits[client_ip] = []
    _rate_limits[client_ip] = [t for t in _rate_limits[client_ip] if now - t < 60]
    if len(_rate_limits[client_ip]) >= 15:
        return JSONResponse(status_code=429, content={"response": "Has alcanzado el límite de mensajes por minuto. Por favor, espera un momento.", "mode": "error"})
    _rate_limits[client_ip].append(now)
    msg  = data.get("message", "").strip()
    sid  = data.get("session_id", "default")

    if not msg:
        return jsonify({"response": "No he recibido ningun mensaje."})

    if ai_foundry.is_configured():
        try:
            history = _get_foundry_history(sid)
            history = history + [{"role": "user", "content": msg}]
            response_text, history = ai_foundry.chat(history)
            _store_foundry_history(sid, history)
            return jsonify({"response": response_text, "mode": "ai_foundry"})
        except Exception:
            session  = get_session(sid)
            fallback = session.process(msg)
            note = "*(IA no disponible, usando modo local)*\n\n"
            return jsonify({"response": note + fallback, "mode": "error"})

    session  = get_session(sid)
    response = session.process(msg)
    return jsonify({"response": response, "mode": "rule_based"})


@app.post("/api/reset")
async def reset(payload: dict = Body(default={})): 
    data = payload or {}
    sid  = data.get("session_id", "default")
    reset_session(sid)
    _foundry_histories.pop(sid, None)
    return jsonify({"status": "ok"})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "triathlon-shap-chatbot"})


@app.get("/features")
def features_info():
    return jsonify({
        "features": [
            {"name": col, "description": FEATURE_LABELS.get(col, col)}
            for col in FEATURE_COLS
        ],
    })


@app.post("/predict")
async def predict(payload: dict = Body(default=None)):
    data = payload
    if data is None:
        raise HTTPException(status_code=400, detail="Body JSON requerido")
    try:
        explainer = get_explainer()
        top_n = int(data.pop("top_n", 5))
        return jsonify(explainer.explain(data, top_n=top_n))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/available_races")
def api_available_races():
    try:
        races = get_available_races()
        return jsonify(races)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news")
def api_news():
    try:
        req = urllib.request.Request('https://triatlon.org/feed/', headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=5).read()
        root = ET.fromstring(res)
        news = []
        for i, item in enumerate(root.findall('.//item')):
            if i >= 3: break
            title = item.find('title').text
            # fix encoding issues from RSS
            try:
                title = title.encode('latin1').decode('utf-8')
            except:
                pass
            news.append({
                "title": title,
                "link": item.find('link').text,
                "date": item.find('pubDate').text if item.find('pubDate') is not None else ""
            })
        return jsonify(news)
    except Exception as e:
        # Fallback si falla el RSS
        return jsonify([
            {"title": "Campeonato de España de Triatlón Sprint", "link": "#", "date": "Hoy"},
            {"title": "Convocatoria Copa del Mundo", "link": "#", "date": "Ayer"},
            {"title": "Nuevo modelo predictivo IA para la élite", "link": "#", "date": "Hace 2 días"}
        ])

@app.get("/api/athletes_directory")
def api_athletes_directory():
    try:
        athletes = get_all_athletes()
        return jsonify(athletes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clubs_directory")
def api_clubs_directory():
    try:
        clubs = get_all_clubs()
        return jsonify(clubs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/competitions_directory")
def api_competitions_directory():
    try:
        competitions = get_all_competitions()
        return jsonify(competitions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/competition/{prueba_id}/results")
def api_competition_results(prueba_id):
    try:
        results = get_competition_results(int(prueba_id))
        return jsonify({"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================================================
# Endpoints del Dashboard (Sprint 4)
# ===========================================================================

# (imports already at module top — line 32)


_PROVINCIA_TO_FEDERATION = {
    "A Coruña": "GAL", "Álava": "PVA", "Albacete": "CLM", "Alicante": "CVA",
    "Almería": "AND", "Asturias": "AST", "Ávila": "CYL", "Badajoz": "EXT",
    "Barcelona": "CAT", "Bizkaia": "PVA", "Burgos": "CYL", "Cáceres": "EXT",
    "Cádiz": "AND", "Cantabria": "CNT", "Castellón": "CVA", "Ciudad Real": "CLM",
    "Córdoba": "AND", "Cuenca": "CLM", "Gipuzkoa": "PVA", "Girona": "CAT",
    "Granada": "AND", "Guadalajara": "CLM", "Huelva": "AND", "Huesca": "ARA",
    "Illes Balears": "BAL", "Jaén": "AND", "La Rioja": "RIO", "Las Palmas": "CAN",
    "León": "CYL", "Lleida": "CAT", "Lugo": "GAL", "Madrid": "MAD",
    "Málaga": "AND", "Melilla": "MEL", "Murcia": "MUR", "Navarra": "NAV",
    "Ourense": "GAL", "Palencia": "CYL", "Pontevedra": "GAL", "Salamanca": "CYL",
    "Santa Cruz de Tenerife": "CAN", "Segovia": "CYL", "Sevilla": "AND",
    "Soria": "CYL", "Tarragona": "CAT", "Teruel": "ARA", "Toledo": "CLM",
    "Valencia": "CVA", "Valladolid": "CYL", "Zamora": "CYL", "Zaragoza": "ARA",
    "Ceuta": "CEU",
}


def _get_federation(ath: dict) -> str:
    """Derive federation code from athlete's club province."""
    provincia = ath.get("provincia", "") or ""
    return _PROVINCIA_TO_FEDERATION.get(provincia, "MAD")


def build_athlete_features(ath: dict, history: list, race_overrides: dict = None) -> dict:
    """
    Builds ALL 51 features expected by the XGBoost model from an athlete's
    profile and race history.  If race_overrides is provided it overrides the
    default race conditions (city, temp, altitude, humidity, lat, lng, etc.).
    """
    from datetime import datetime

    n_races = len(history)
    puestos = [h.get("puesto", 20) for h in history if h.get("puesto") is not None]
    puntos_list = [h.get("puntos", 0) for h in history if h.get("puntos") is not None]

    # ── Averages of position ──────────────────────────────────────────
    avg_last_3 = sum(puestos[:3]) / len(puestos[:3]) if puestos else 20.0
    avg_last_5 = sum(puestos[:5]) / len(puestos[:5]) if puestos else 20.0
    best_ever = min(puestos) if puestos else 30.0
    best_season = min(puestos[:10]) if puestos else 30.0

    # ── Ratios ────────────────────────────────────────────────────────
    wins = sum(1 for p in puestos if p == 1)
    podiums = sum(1 for p in puestos if p <= 3)
    top10s = sum(1 for p in puestos if p <= 10)
    win_rate = wins / n_races if n_races > 0 else 0.0
    podium_rate = podiums / n_races if n_races > 0 else 0.0
    top10_rate = top10s / n_races if n_races > 0 else 0.0
    dnf_rate = 0.0  # DB doesn't store DNFs explicitly

    # ── Position std dev ──────────────────────────────────────────────
    if len(puestos) >= 2:
        mean_pos = sum(puestos) / len(puestos)
        pos_std = (sum((p - mean_pos) ** 2 for p in puestos) / len(puestos)) ** 0.5
    else:
        mean_pos = puestos[0] if puestos else 20.0
        pos_std = 10.0

    # ── Streaks ───────────────────────────────────────────────────────
    podium_streak = 0
    for p in puestos:
        if p <= 3:
            podium_streak += 1
        else:
            break
    top10_streak = 0
    for p in puestos:
        if p <= 10:
            top10_streak += 1
        else:
            break

    # ── Days since last race ──────────────────────────────────────────
    days_since = 30
    if history:
        try:
            last_date = str(history[0].get("fecha", ""))
            last = datetime.strptime(last_date.strip()[:10], "%Y-%m-%d")
            days_since = max(1, (datetime.now() - last).days)
        except Exception:
            pass

    # ── Elite race count ──────────────────────────────────────────────
    n_elite = sum(1 for h in history if (h.get("championship_level") or 3) <= 2)

    # ── Race conditions (defaults + overrides) ────────────────────────
    race = {
        "race_city": "Madrid",
        "race_temperature": 25.0,
        "race_altitude_m": 600.0,
        "race_humidity": 50.0,
        "race_lat": 40.42,
        "race_lng": -3.70,
        "race_month": datetime.now().month,
        "race_day_of_week": datetime.now().weekday(),
    }
    if race_overrides:
        race.update(race_overrides)

    race_alt = float(race.get("race_altitude_m", 600.0))
    race_lat = float(race.get("race_lat", 40.42))
    race_lng = float(race.get("race_lng", -3.70))
    race_temp = float(race.get("race_temperature", 25.0))
    race_hum = float(race.get("race_humidity", 50.0))
    race_city = race.get("race_city", "Madrid")

    # ── Derived race features ─────────────────────────────────────────
    race_near_coast = 1 if race_alt < 50 else 0
    # Climate type heuristic
    if race_temp >= 30 and race_hum < 40:
        race_climate_type = "hot_dry"
    elif race_temp >= 28:
        race_climate_type = "hot_humid"
    elif race_temp <= 12:
        race_climate_type = "cold"
    else:
        race_climate_type = "temperate"
    race_type = race_overrides.get("race_type", "sprint") if race_overrides else "sprint"
    race_month = int(race.get("race_month", datetime.now().month))
    race_dow = int(race.get("race_day_of_week", datetime.now().weekday()))

    # ── Athlete ranking & form ────────────────────────────────────────
    athlete_ranking = ath.get("ranking_real", 9999.0)
    form_score = ath.get("form_score", max(0.0, 100.0 - avg_last_3))

    # ── Ranking momentum & trend ──────────────────────────────────────
    # Compare points from recent races vs older ones to detect trends
    recent_puntos = puntos_list[:3] if puntos_list else []
    older_puntos = puntos_list[3:8] if len(puntos_list) > 3 else []
    avg_recent_pts = sum(recent_puntos) / len(recent_puntos) if recent_puntos else 0.0
    avg_older_pts = sum(older_puntos) / len(older_puntos) if older_puntos else avg_recent_pts
    ranking_momentum = avg_recent_pts - avg_older_pts
    ranking_change_recent = avg_recent_pts - avg_older_pts

    if ranking_momentum > 10:
        ranking_trend = "subiendo"
    elif ranking_momentum < -10:
        ranking_trend = "bajando"
    else:
        ranking_trend = "estable"

    # ── Form trend ────────────────────────────────────────────────────
    recent_pos = puestos[:3] if puestos else []
    older_pos = puestos[3:6] if len(puestos) > 3 else []
    avg_recent_pos = sum(recent_pos) / len(recent_pos) if recent_pos else 20.0
    avg_older_pos = sum(older_pos) / len(older_pos) if older_pos else avg_recent_pos
    pos_diff = avg_older_pos - avg_recent_pos  # positive = improving
    if pos_diff > 3:
        form_trend = "subiendo"
    elif pos_diff < -3:
        form_trend = "bajando"
    else:
        form_trend = "estable"

    # ── Performance biases (altitude / coast / heat) ──────────────────
    high_alt_pos = [h.get("puesto", 20) for h in history if (h.get("altitud") or 0) > 500]
    low_alt_pos = [h.get("puesto", 20) for h in history if (h.get("altitud") or 500) <= 500]
    coastal_pos = [h.get("puesto", 20) for h in history if (h.get("altitud") or 500) < 50]
    inland_pos = [h.get("puesto", 20) for h in history if (h.get("altitud") or 0) >= 50]
    hot_pos = [h.get("puesto", 20) for h in history if (h.get("temperatura_max") or 20) >= 28]
    cold_pos = [h.get("puesto", 20) for h in history if (h.get("temperatura_max") or 20) < 15]

    avg_pos_high_alt = sum(high_alt_pos) / len(high_alt_pos) if high_alt_pos else mean_pos
    avg_pos_low_alt = sum(low_alt_pos) / len(low_alt_pos) if low_alt_pos else mean_pos
    avg_pos_coastal = sum(coastal_pos) / len(coastal_pos) if coastal_pos else mean_pos
    avg_pos_inland = sum(inland_pos) / len(inland_pos) if inland_pos else mean_pos
    avg_pos_hot = sum(hot_pos) / len(hot_pos) if hot_pos else mean_pos
    avg_pos_cold = sum(cold_pos) / len(cold_pos) if cold_pos else mean_pos

    performance_altitude_bias = mean_pos - avg_pos_high_alt  # positive = better at altitude
    performance_coast_bias = mean_pos - avg_pos_coastal
    performance_heat_bias = mean_pos - avg_pos_hot

    # ── City-specific stats ───────────────────────────────────────────
    city_lower = race_city.lower() if race_city else ""
    races_at_city = [h for h in history if (h.get("ciudad") or "").lower() == city_lower]
    n_races_at_city = len(races_at_city)
    n_wins_at_city = sum(1 for h in races_at_city if h.get("puesto") == 1)

    # ── Context variables ─────────────────────────────────────────────
    avg_ranking_opponents = race_overrides.get("avg_ranking_opponents", 50.0) if race_overrides else 50.0
    n_participants = race_overrides.get("n_participants_race", 100) if race_overrides else 100
    pct_opponents_better = max(0.0, min(1.0, (athlete_ranking - 1) / max(n_participants, 1)))

    # ── Build the full 51-feature dict ────────────────────────────────
    return {
        # Athlete profile
        "athlete_age_at_race": ath.get("age", 27),  # Not stored in DB; default elite age
        "athlete_federation": _get_federation(ath),
        "athlete_ranking_triatlon": round(athlete_ranking, 1),
        "athlete_has_wt_id": ath.get("has_wt_id", 0),
        # Race conditions
        "race_city": race_city,
        "race_temperature": race_temp,
        "race_humidity": race_hum,
        "race_lat": race_lat,
        "race_lng": race_lng,
        "race_altitude_m": race_alt,
        "race_near_coast": race_near_coast,
        "race_climate_type": race_climate_type,
        "race_month": race_month,
        "race_day_of_week": race_dow,
        "race_type": race_type,
        # Experience
        "n_races_before": n_races,
        "n_elite_races_before": n_elite,
        # Recent performance
        "avg_finish_pos_last_3": round(avg_last_3, 2),
        "avg_finish_pos_last_5": round(avg_last_5, 2),
        "best_finish_pos_ever": best_ever,
        "best_finish_pos_season": best_season,
        # Segment ranks (not available in DB — default to 0 = use background median)
        "avg_swim_rank_last_5": 0,
        "avg_bike_rank_last_5": 0,
        "avg_run_rank_last_5": 0,
        # Rates
        "win_rate": round(win_rate, 4),
        "podium_rate": round(podium_rate, 4),
        "top10_rate": round(top10_rate, 4),
        "dnf_rate": dnf_rate,
        # Freshness
        "days_since_last_race": days_since,
        # Momentum & trends
        "ranking_momentum": round(ranking_momentum, 2),
        "ranking_trend": ranking_trend,
        "ranking_change_recent": round(ranking_change_recent, 2),
        "form_score": round(form_score, 1),
        "form_trend": form_trend,
        # Environmental performance biases
        "avg_pos_high_altitude": round(avg_pos_high_alt, 2),
        "avg_pos_low_altitude": round(avg_pos_low_alt, 2),
        "avg_pos_coastal": round(avg_pos_coastal, 2),
        "avg_pos_inland": round(avg_pos_inland, 2),
        "avg_pos_hot": round(avg_pos_hot, 2),
        "avg_pos_cold": round(avg_pos_cold, 2),
        "performance_altitude_bias": round(performance_altitude_bias, 2),
        "performance_coast_bias": round(performance_coast_bias, 2),
        "performance_heat_bias": round(performance_heat_bias, 2),
        # Race context
        "n_participants_race": n_participants,
        "avg_ranking_opponents": avg_ranking_opponents,
        "pct_opponents_ranked_higher": round(pct_opponents_better, 4),
        # City-specific
        "n_races_at_city": n_races_at_city,
        "n_previous_wins_at_city": n_wins_at_city,
        # Consistency
        "position_std_dev": round(pos_std, 2),
        "current_podium_streak": podium_streak,
        "current_top10_streak": top10_streak,
    }


def detect_anomaly(prediction: float, puestos: list) -> tuple:
    """
    Detecta anomalías comparando la predicción con el historial real.
    Devuelve (is_anomaly: bool, reason: str).
    """
    if len(puestos) < 2:
        return False, ""
    mean_pos = sum(puestos) / len(puestos)
    std_pos = (sum((p - mean_pos) ** 2 for p in puestos) / len(puestos)) ** 0.5
    if std_pos < 1.0:
        std_pos = 1.0
    z = (prediction - mean_pos) / std_pos
    if abs(z) > 1.5:
        if z < -1.5:
            return True, f"Predicción mejor de lo habitual (media hist: {mean_pos:.0f})"
        else:
            return True, f"Predicción peor de lo habitual (media hist: {mean_pos:.0f})"
    return False, ""


@app.get("/api/ranking")
def api_ranking(request: Request):
    limit = int(request.query_params.get("limit", 10))
    offset = int(request.query_params.get("offset", 0))

    try:
        athletes = get_active_athletes()
        history_map = get_athletes_history_batch()
        explainer = get_explainer()

        # Calcular puntos totales de cada atleta para sacar su Ranking Real FETRI
        for ath in athletes:
            doc = ath["documento"]
            hist = history_map.get(doc, [])
            puntos = sorted([h.get("puntos", 0) for h in hist if h.get("puntos") is not None], reverse=True)[:3]
            ath["total_puntos"] = sum(puntos)
            ath["n_elite"] = sum(1 for h in hist if (h.get("championship_level") or 3) <= 2)
            
        # Ordenar por puntos totales para asignar ranking de mérito (1 al N)
        athletes.sort(key=lambda x: x["total_puntos"], reverse=True)
        for i, ath in enumerate(athletes):
            if ath["total_puntos"] > 0:
                ath["ranking_real"] = float(i + 1)
            else:
                # En lugar de 9999.0 (que el árbol confunde), usamos 2500.0 para novatos/sin puntos
                ath["ranking_real"] = 2500.0

        # Preparar todas las features en bloque
        features_list = []
        for ath in athletes:
            doc = ath["documento"]
            history = history_map.get(doc, [])
            features_list.append(build_athlete_features(ath, history))
            
        # Predicción en bloque (1 sola llamada HTTP)
        predictions = explainer.predict_batch(features_list)

        results = []
        for i, ath in enumerate(athletes):
            doc = ath["documento"]
            history = history_map.get(doc, [])
            prediction = predictions[i]

            puestos = [h.get("puesto", 20) for h in history if h.get("puesto") is not None]
            is_anomaly, anomaly_reason = detect_anomaly(prediction, puestos)

            results.append({
                "documento": doc,
                "nombre": ath["nombre"],
                "club": ath["club"],
                "prediccion_raw": round(prediction, 1),
                "posicion_predicha": prediction,
                "anomalia": is_anomaly,
                "anomalia_motivo": anomaly_reason,
            })

        results.sort(key=lambda x: x["posicion_predicha"])

        for i, r in enumerate(results):
            r["posicion_predicha"] = i + 1
            
        paginated = results[offset : offset + limit]

        return jsonify({
            "ranking": paginated,
            "total_returned": len(paginated),
            "offset": offset
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate_race")
async def api_simulate_race(payload: dict = Body(default={})): 
    data = payload or {}
    race_city = data.get("race_city", "Madrid")
    race_temperature = float(data.get("race_temperature", 25.0))
    race_altitude_m = float(data.get("race_altitude_m", 600.0))
    race_humidity = float(data.get("race_humidity", 50.0))
    race_lat = float(data.get("race_lat", 40.42))
    race_lng = float(data.get("race_lng", -3.70))
    limit = int(data.get("limit", 15))

    race_overrides = {
        "race_city": race_city,
        "race_temperature": race_temperature,
        "race_altitude_m": race_altitude_m,
        "race_humidity": race_humidity,
        "race_lat": race_lat,
        "race_lng": race_lng,
    }

    try:
        athletes = get_active_athletes()
        history_map = get_athletes_history_batch()
        explainer = get_explainer()

        # Calcular puntos totales de cada atleta para sacar su Ranking Real FETRI
        for ath in athletes:
            doc = ath["documento"]
            hist = history_map.get(doc, [])
            puntos = sorted([h.get("puntos", 0) for h in hist if h.get("puntos") is not None], reverse=True)[:3]
            ath["total_puntos"] = sum(puntos)
            ath["n_elite"] = sum(1 for h in hist if (h.get("championship_level") or 3) <= 2)
            
        # Ordenar por puntos totales para asignar ranking de mérito (1 al N)
        athletes.sort(key=lambda x: x["total_puntos"], reverse=True)
        for i, ath in enumerate(athletes):
            if ath["total_puntos"] > 0:
                ath["ranking_real"] = float(i + 1)
            else:
                # En lugar de 9999.0 (que el árbol confunde), usamos 2500.0 para novatos/sin puntos
                ath["ranking_real"] = 2500.0

        # Preparar todas las features en bloque con overrides de carrera
        features_list = []
        for ath in athletes:
            doc = ath["documento"]
            history = history_map.get(doc, [])
            features_list.append(build_athlete_features(ath, history, race_overrides=race_overrides))
            
        # Predicción en bloque con explicaciones
        predictions, explanations = explainer.explain_batch(features_list)

        results = []
        for i, ath in enumerate(athletes):
            doc = ath["documento"]
            history = history_map.get(doc, [])
            prediction = predictions[i]
            explicacion = explanations[i]

            puestos = [h.get("puesto", 20) for h in history if h.get("puesto") is not None]
            is_anomaly, anomaly_reason = detect_anomaly(prediction, puestos)

            results.append({
                "documento": doc,
                "nombre": ath["nombre"],
                "club": ath["club"],
                "prediccion_raw": round(prediction, 1),
                "posicion_predicha": prediction,
                "anomalia": is_anomaly,
                "anomalia_motivo": anomaly_reason,
                "explicacion": explicacion,
            })

        results.sort(key=lambda x: x["posicion_predicha"])

        for i, r in enumerate(results):
            r["posicion_predicha"] = i + 1
            
        paginated = results[:limit]

        return jsonify({
            "ranking": paginated,
            "simulated": True,
            "conditions": {
                "city": race_city,
                "temp": race_temperature,
                "alt": race_altitude_m,
                "hum": race_humidity
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/races")
def api_races():
    try:
        # Catálogo de carreras futuras de corta distancia (Sprint / Olímpico).
        # Incluye lat/lng para que build_athlete_features pueda calcular
        # race_near_coast, race_climate_type, etc.
        future_races = [
            {
                "nombre": "Campeonato de España Triatlón Sprint 2026",
                "ciudad": "Mérida",
                "temperatura_max": 36.0,
                "altitud": 217.0,
                "humedad_media": 35.0,
                "lat": 38.92,
                "lng": -6.34
            },
            {
                "nombre": "Campeonato de España Triatlón Olímpico 2026",
                "ciudad": "Banyoles",
                "temperatura_max": 25.0,
                "altitud": 173.0,
                "humedad_media": 60.0,
                "lat": 42.12,
                "lng": 2.76
            },
            {
                "nombre": "ProTour FETRI 2026",
                "ciudad": "Madrid",
                "temperatura_max": 32.0,
                "altitud": 650.0,
                "humedad_media": 35.0,
                "lat": 40.42,
                "lng": -3.70
            },
            {
                "nombre": "Copa de Europa de Triatlón 2026",
                "ciudad": "Melilla",
                "temperatura_max": 27.5,
                "altitud": 15.0,
                "humedad_media": 72.0,
                "lat": 35.29,
                "lng": -2.94
            },
            {
                "nombre": "Triatlón Villa de A Coruña 2026",
                "ciudad": "A Coruña",
                "temperatura_max": 19.0,
                "altitud": 5.0,
                "humedad_media": 78.0,
                "lat": 43.37,
                "lng": -8.40
            }
        ]
        return jsonify({"races": future_races})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/athlete/{documento}")
def api_athlete(documento):
    try:
        info = get_athlete_info(documento)
        if not info:
            raise HTTPException(status_code=404, detail="Atleta no encontrado")

        history = get_athlete_history(documento)
        # Fix: we must pass 'info' (the athlete dict) as the first parameter
        features = build_athlete_features(info, history)

        explainer = get_explainer()
        explanation = explainer.explain(features, top_n=5)

        tendencia = "estable"
        if len(history) >= 2:
            if history[0]["puesto"] < history[1]["puesto"]:
                tendencia = "mejorando"
            elif history[0]["puesto"] > history[1]["puesto"]:
                tendencia = "empeorando"

        return jsonify({
            "datos_basicos": info,
            "tendencia_forma": tendencia,
            "prediccion_actual": explanation,
            "historial": history
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo/ranking")
def api_demo_ranking(request: Request):
    limit = int(request.query_params.get("limit", 10))
    data = [
        {"posicion_predicha": 1, "nombre": "Mario Mola", "anomalia": False},
        {"posicion_predicha": 2, "nombre": "Javier Gomez Noya", "anomalia": False},
        {"posicion_predicha": 3, "nombre": "Fernando Alarza", "anomalia": True},
        {"posicion_predicha": 4, "nombre": "Antonio Serrat", "anomalia": False},
        {"posicion_predicha": 5, "nombre": "Roberto Sanchez", "anomalia": False}
    ]
    return jsonify({"ranking": data[:limit], "offline_mode": True})

@app.get("/api/demo/athlete/{documento}")
def api_demo_athlete(documento):
    return jsonify({
        "datos_basicos": {"nombre": "Atleta Demo", "documento": documento},
        "tendencia_forma": "mejorando",
        "prediccion_actual": {"prediction": 3.0, "top_factors": []},
        "historial": [{"puesto": 1, "nombre": "Madrid"}, {"puesto": 3, "nombre": "Valencia"}]
    })


if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print(" Chatbot Triatlon Predictor - Landing FETRI")
    print("=" * 55)
    print("Cargando modelo predictivo...")
    get_explainer()
    print("AI Foundry:", "configurado" if ai_foundry.is_configured() else "no configurado")
    print("-" * 55)
    print(" Abre:  http://localhost:5050")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=5050)
