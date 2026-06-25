"""Script de prueba para el módulo SHAP del chatbot."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.shap_explainer import get_explainer

explainer = get_explainer()

features_bueno = {
    "athlete_ranking_triatlon": 5,
    "n_races_before": 35,
    "avg_finish_pos_last_3": 3.0,
    "win_rate": 0.4,
    "race_temperature": 20.0,
    "race_city": "Madrid",
    "days_since_last_race": 15,
}

features_novato = {
    "athlete_ranking_triatlon": 150,
    "n_races_before": 2,
    "avg_finish_pos_last_3": 35.0,
    "win_rate": 0.0,
    "race_temperature": 38.0,
    "race_city": "Sevilla",
    "days_since_last_race": 60,
}

for name, features in [("ATLETA TOP (favorito)", features_bueno),
                        ("ATLETA NOVATO (calor extremo)", features_novato)]:
    print(f"\n{'='*60}")
    print(f"CASO: {name}")
    print("="*60)
    result = explainer.explain(features, top_n=5)
    print(f"Prediccion: {result['prediction']} posicion")
    print(f"Base value: {result['base_value']} posicion")
    print()
    print("--- EXPLICACION PARA CHATBOT ---")
    print(result["explanation_text"])
    print()
    print("--- SHAP values (top 5) ---")
    for feat, val in sorted(result["shap_values"].items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
        print(f"  {feat:30s}: {val:+.2f}")
