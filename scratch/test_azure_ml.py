import sys, json, ssl, urllib.request
sys.path.append(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\.env")
import os

endpoint = os.getenv("AZURE_ML_ENDPOINT")
key = os.getenv("AZURE_ML_KEY")

print(f"Endpoint: {endpoint}")
print(f"Key: {key[:20]}...")

# Test with a simple payload (51 features)
from chatbot.shap_explainer import get_explainer, FEATURE_COLS
explainer = get_explainer()

# Build a sample dataframe
features = {"n_races_before": 10, "avg_finish_pos_last_3": 5.0}
df = explainer._to_dataframe(features)
print(f"\nColumns ({len(df.columns)}): {list(df.columns[:5])}...")
print(f"Values sample: {df.values[0][:5]}...")

# Try calling Azure directly
data = {
    "input_data": {
        "columns": df.columns.tolist(),
        "data": df.values.tolist()
    }
}
body = json.dumps(data).encode()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {key}',
    'azureml-model-deployment': 'blue'
}
req = urllib.request.Request(endpoint, body, headers)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    print("\nCalling Azure ML endpoint...")
    response = urllib.request.urlopen(req, context=ctx, timeout=10)
    result = response.read().decode()
    print(f"Azure ML response: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf8', 'ignore')}")
except Exception as e:
    print(f"Error: {e}")

# Also test local model
local_pred = float(explainer.model.predict(df)[0])
print(f"\nLocal model prediction: {local_pred}")
