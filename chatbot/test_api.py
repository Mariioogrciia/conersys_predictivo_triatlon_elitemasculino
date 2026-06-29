"""Test del endpoint FastAPI con TestClient de Starlette."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from fastapi.testclient import TestClient
from chatbot.chatbot_api import app

client = TestClient(app)

print("=== GET /health ===")
resp = client.get("/health")
print("STATUS:", resp.status_code)
print(resp.json())

print()
print("=== GET /features ===")
resp = client.get("/features")
features_data = resp.json()
print(f"Features disponibles: {len(features_data['features'])}")
for feat in features_data["features"]:
    print(f"  - {feat['name']}: {feat['description']}")

print()
print("=== GET /api/status ===")
resp = client.get("/api/status")
print("STATUS:", resp.status_code)
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))

print()
print("=== POST /predict (atleta ejemplo) ===")
payload = {
    "athlete_ranking_triatlon": 15,
    "n_races_before": 20,
    "avg_finish_pos_last_3": 5.5,
    "top_n": 3,
}
resp = client.post("/predict", json=payload)
data = resp.json()
print("STATUS:", resp.status_code)
print("PREDICTION:", data.get("prediction"), "posición estimada")
print()
print("TOP FACTORS:")
for f in data.get("top_factors", []):
    label = f["label"]
    impact = f["shap_impact"]
    direction = f["direction"]
    print(f"  {label}: {impact:+.1f} posiciones ({direction})")
