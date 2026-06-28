"""
Diagnóstico: ¿Cambia el ranking entre dos carreras distintas?
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(override=True)

from chatbot.shap_explainer import get_explainer, FEATURE_COLS
from chatbot.chatbot_api import build_athlete_features

print(f"Modelo espera {len(FEATURE_COLS)} features")

# Simular 2 atletas ficticios
ath_A = {"nombre": "Atleta Calor", "club": "TEST", "documento": "A", "ranking_real": 5.0, "provincia": "Sevilla"}
ath_B = {"nombre": "Atleta Altitud", "club": "TEST", "documento": "B", "ranking_real": 10.0, "provincia": "Madrid"}

hist_A = [
    {"puesto": 1, "puntos": 100, "fecha": "2025-06-01", "ciudad": "Sevilla", "championship_level": 2, "altitud": 10, "temperatura_max": 35, "humedad_media": 30},
    {"puesto": 2, "puntos": 90, "fecha": "2025-05-01", "ciudad": "Malaga", "championship_level": 2, "altitud": 15, "temperatura_max": 32, "humedad_media": 40},
    {"puesto": 15, "puntos": 40, "fecha": "2025-04-01", "ciudad": "Jaca", "championship_level": 2, "altitud": 820, "temperatura_max": 12, "humedad_media": 60},
    {"puesto": 12, "puntos": 50, "fecha": "2025-03-01", "ciudad": "Granada", "championship_level": 2, "altitud": 738, "temperatura_max": 15, "humedad_media": 50},
]

hist_B = [
    {"puesto": 1, "puntos": 100, "fecha": "2025-06-01", "ciudad": "Jaca", "championship_level": 2, "altitud": 820, "temperatura_max": 12, "humedad_media": 60},
    {"puesto": 3, "puntos": 80, "fecha": "2025-05-01", "ciudad": "Granada", "championship_level": 2, "altitud": 738, "temperatura_max": 18, "humedad_media": 50},
    {"puesto": 14, "puntos": 45, "fecha": "2025-04-01", "ciudad": "Sevilla", "championship_level": 2, "altitud": 10, "temperatura_max": 35, "humedad_media": 30},
    {"puesto": 10, "puntos": 55, "fecha": "2025-03-01", "ciudad": "Merida", "championship_level": 2, "altitud": 217, "temperatura_max": 36, "humedad_media": 35},
]

explainer = get_explainer()

race_hot = {"race_city": "Merida", "race_temperature": 36.0, "race_altitude_m": 217.0, "race_humidity": 35.0, "race_lat": 38.92, "race_lng": -6.34}
feat_A_hot = build_athlete_features(ath_A, hist_A, race_overrides=race_hot)
feat_B_hot = build_athlete_features(ath_B, hist_B, race_overrides=race_hot)

pred_A_hot = explainer.predict(feat_A_hot)
pred_B_hot = explainer.predict(feat_B_hot)
print(f"\nMerida 36C: A={pred_A_hot:.1f}  B={pred_B_hot:.1f}  Ganador={'A' if pred_A_hot < pred_B_hot else 'B'}")

race_cold = {"race_city": "Jaca", "race_temperature": 12.0, "race_altitude_m": 820.0, "race_humidity": 60.0, "race_lat": 42.57, "race_lng": -0.55}
feat_A_cold = build_athlete_features(ath_A, hist_A, race_overrides=race_cold)
feat_B_cold = build_athlete_features(ath_B, hist_B, race_overrides=race_cold)

pred_A_cold = explainer.predict(feat_A_cold)
pred_B_cold = explainer.predict(feat_B_cold)
print(f"Jaca 12C 820m: A={pred_A_cold:.1f}  B={pred_B_cold:.1f}  Ganador={'A' if pred_A_cold < pred_B_cold else 'B'}")

print(f"\nCambia ranking? {(pred_A_hot < pred_B_hot) != (pred_A_cold < pred_B_cold)}")
print(f"Delta A (hot->cold): {pred_A_cold - pred_A_hot:+.2f}")
print(f"Delta B (hot->cold): {pred_B_cold - pred_B_hot:+.2f}")

produced = set(feat_A_hot.keys())
expected = set(FEATURE_COLS)
print(f"\nFeatures producidas: {len(produced)}, esperadas: {len(expected)}, match: {len(produced & expected)}")
missing = expected - produced
if missing: print(f"FALTAN: {missing}")
