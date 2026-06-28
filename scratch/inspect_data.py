import sys
sys.path.append(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\.env")
from chatbot.database_service import get_active_athletes, get_athletes_history_batch, get_athlete_info
import json

# Get 3 athletes
athletes = get_active_athletes(limit=3, offset=0)
docs = [a["documento"] for a in athletes]
history = get_athletes_history_batch(docs)

# Print first athlete info
doc = docs[0]
info = get_athlete_info(doc)
print("=== ATHLETE INFO ===")
print(json.dumps(info, indent=2, default=str))

print(f"\n=== HISTORY for {doc} ({len(history[doc])} races) ===")
for i, h in enumerate(history[doc][:5]):
    print(f"  Race {i}: {json.dumps(h, indent=4, default=str)}")

# Print second athlete
doc2 = docs[1]
print(f"\n=== HISTORY for {doc2} ({len(history[doc2])} races) ===")
for i, h in enumerate(history[doc2][:3]):
    print(f"  Race {i}: {json.dumps(h, indent=4, default=str)}")
