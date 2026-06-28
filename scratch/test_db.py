import sys
sys.path.append(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\.env")
from chatbot.database_service import get_active_athletes, get_athletes_history_batch

try:
    print("Obteniendo atletas...")
    athletes = get_active_athletes(limit=2, offset=0)
    print(f"Atletas: {[a['documento'] for a in athletes]}")
    docs = [ath["documento"] for ath in athletes if ath.get("documento")]
    if docs:
        print("Obteniendo historial batch...")
        history = get_athletes_history_batch(docs)
        print(f"Historial obtenido. Claves: {list(history.keys())}")
    else:
        print("No hay docs.")
except Exception as e:
    print(f"Error: {e}")
