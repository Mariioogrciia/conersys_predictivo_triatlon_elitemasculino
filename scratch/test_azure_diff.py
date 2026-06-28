import sys, json, ssl, urllib.request
sys.path.append(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\.env")
import os

from chatbot.shap_explainer import get_explainer

explainer = get_explainer()

# Atleta 1: Experimentado, bueno
features1 = {
    "n_races_before": 25,
    "avg_finish_pos_last_3": 3.0,
    "avg_finish_pos_last_5": 4.0,
    "best_finish_pos_ever": 1,
    "win_rate": 0.15,
    "podium_rate": 0.40,
    "top10_rate": 0.80,
    "days_since_last_race": 14,
    "position_std_dev": 3.0,
    "current_top10_streak": 5,
}

# Atleta 2: Novato
features2 = {
    "n_races_before": 2,
    "avg_finish_pos_last_3": 35.0,
    "avg_finish_pos_last_5": 35.0,
    "best_finish_pos_ever": 30,
    "win_rate": 0.0,
    "podium_rate": 0.0,
    "top10_rate": 0.0,
    "days_since_last_race": 90,
    "position_std_dev": 5.0,
    "current_top10_streak": 0,
}

# Atleta 3: Medio
features3 = {
    "n_races_before": 10,
    "avg_finish_pos_last_3": 12.0,
    "avg_finish_pos_last_5": 15.0,
    "best_finish_pos_ever": 5,
    "win_rate": 0.0,
    "podium_rate": 0.10,
    "top10_rate": 0.40,
    "days_since_last_race": 30,
    "position_std_dev": 8.0,
    "current_top10_streak": 0,
}

print("=== Azure ML predictions with DIFFERENT features ===")
p1 = explainer.predict(features1)
print(f"Atleta experimentado (avg_pos=3): {p1:.2f}")

p2 = explainer.predict(features2)
print(f"Atleta novato (avg_pos=35):       {p2:.2f}")

p3 = explainer.predict(features3)
print(f"Atleta medio (avg_pos=12):        {p3:.2f}")

print(f"\nDiferencia max: {abs(p2-p1):.2f}")
