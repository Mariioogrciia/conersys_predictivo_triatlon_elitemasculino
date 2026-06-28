import sys
sys.path.append(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\.env")
from chatbot.shap_explainer import get_explainer

try:
    print("Obteniendo explainer...")
    explainer = get_explainer()
    print("Explainer listo.")
    features = {"n_races_before": 10, "avg_finish_pos_last_3": 5}
    print("Prediciendo...")
    res = explainer.predict(features)
    print(f"Predicción: {res}")
except Exception as e:
    print(f"Error: {e}")
