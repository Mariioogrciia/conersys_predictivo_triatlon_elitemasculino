"""Script de prueba para el módulo SHAP del chatbot."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.shap_explainer import get_explainer

explainer = get_explainer()

# Atleta con buen historial en prueba local
features_bueno = {
    "CHAMPIONSHIP_LEVEL": 2,
    "ALTITUD": 200.0,
    "TEMPERATURA_MAX": 22.0,
    "HUMEDAD_MEDIA": 65.0,
    "PRECIPITACION": 0.0,
    "VIENTO_MAX": 10.0,
    "IS_EXTREME_HEAT": 0,
    "IS_WET_RACE": 0,
    "VIAJE_DISTANCIA_KM": 50.0,
    "ES_LOCAL": 1,
    "MES_CARRERA": 6,
    "MES_SIN": 1.0,
    "MES_COS": 0.0,
    "DAYS_SINCE_LAST_RACE": 21,
    "FATIGUE_INDEX": 0.1,
    "CLUB_POWER_SCORE": 80.0,
    "RECENT_AVG_PUNTOS": 1400.0,
    "HIST_AVG_PUNTOS": 1200.0,
    "HIST_STD_PUNTOS": 150.0,
    "HIST_MAX_PUNTOS": 1800.0,
    "HIST_COUNT_PRUEBAS": 15,
}

# Atleta novato con calor extremo
features_novato = {
    "CHAMPIONSHIP_LEVEL": 3,
    "ALTITUD": 650.0,
    "TEMPERATURA_MAX": 38.0,
    "HUMEDAD_MEDIA": 80.0,
    "PRECIPITACION": 0.0,
    "VIENTO_MAX": 25.0,
    "IS_EXTREME_HEAT": 1,
    "IS_WET_RACE": 0,
    "VIAJE_DISTANCIA_KM": 400.0,
    "ES_LOCAL": 0,
    "MES_CARRERA": 8,
    "MES_SIN": 0.0,
    "MES_COS": -1.0,
    "DAYS_SINCE_LAST_RACE": 5,
    "FATIGUE_INDEX": 0.9,
    "CLUB_POWER_SCORE": 20.0,
    "RECENT_AVG_PUNTOS": 200.0,
    "HIST_AVG_PUNTOS": 150.0,
    "HIST_STD_PUNTOS": 80.0,
    "HIST_MAX_PUNTOS": 300.0,
    "HIST_COUNT_PRUEBAS": 2,
}

for name, features in [("ATLETA VETERANO (prueba local)", features_bueno),
                        ("ATLETA NOVATO (calor extremo, lejos)", features_novato)]:
    print(f"\n{'='*60}")
    print(f"CASO: {name}")
    print("="*60)
    result = explainer.explain(features, top_n=5)
    print(f"Prediccion: {result['prediction']} puntos")
    print(f"Base value: {result['base_value']} puntos")
    print()
    print("--- EXPLICACION PARA CHATBOT ---")
    print(result["explanation_text"])
    print()
    print("--- SHAP values (todos) ---")
    for feat, val in sorted(result["shap_values"].items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"  {feat:30s}: {val:+.2f}")
