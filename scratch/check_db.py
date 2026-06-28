from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path='.env')
from chatbot.database_service import get_db_connection
import sys

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_type='BASE TABLE'")
    print([row[0] for row in cursor.fetchall()])
    
    # Also fetch schema of deportistas, clubes_geo, noticias?
    cursor.execute("SELECT table_name, column_name FROM information_schema.columns")
    columns = {}
    for row in cursor.fetchall():
        t, c = row[0], row[1]
        columns.setdefault(t, []).append(c)
    import json
    print(json.dumps(columns, indent=2))
except Exception as e:
    print(e)
