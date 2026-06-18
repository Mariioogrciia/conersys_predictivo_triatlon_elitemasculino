"""Test del endpoint Flask con el cliente de prueba de Flask."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.chatbot_api import app

client = app.test_client()

payload = json.dumps({
    "CHAMPIONSHIP_LEVEL": 2,
    "RECENT_AVG_PUNTOS": 1400.0,
    "HIST_AVG_PUNTOS": 1200.0,
    "HIST_MAX_PUNTOS": 1800.0,
    "HIST_COUNT_PRUEBAS": 15,
    "ES_LOCAL": 1,
    "DAYS_SINCE_LAST_RACE": 21,
    "TEMPERATURA_MAX": 22.0,
    "FATIGUE_INDEX": 0.1,
    "CLUB_POWER_SCORE": 80.0,
    "top_n": 3,
})

print("=== POST /explain ===")
resp = client.post("/explain", data=payload, content_type="application/json")
data = json.loads(resp.data)
print("STATUS:", resp.status_code)
print("PREDICTION:", data.get("prediction"), "puntos")
print()
print("EXPLANATION:")
print(data.get("explanation"))
print()
print("TOP FACTORS:")
for f in data.get("top_factors", []):
    label = f["label"]
    impact = f["impact"]
    direction = f["direction"]
    print(f"  {label}: {impact:+.0f} pts ({direction})")

print()
print("=== GET /health ===")
resp2 = client.get("/health")
print(json.loads(resp2.data))

print()
print("=== GET /features ===")
resp3 = client.get("/features")
features_data = json.loads(resp3.data)
print(f"Features disponibles: {len(features_data['features'])}")
for feat in features_data["features"]:
    print(f"  - {feat['name']}: {feat['description']}")
