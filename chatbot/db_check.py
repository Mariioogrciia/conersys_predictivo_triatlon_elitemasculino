"""
Verificacion de la conexion a Azure SQL Database para el panel de estado.
"""
import os


def ping() -> dict:
    """
    Intenta conectar a Azure SQL con las credenciales del .env.
    Devuelve {ok: bool, detail: str, server: str}.
    """
    server = (os.getenv("AZURE_SERVER", "") or "").replace('"', "").replace("'", "")
    db     = (os.getenv("AZURE_DB", "") or "").replace('"', "").replace("'", "")
    user   = (os.getenv("AZURE_USER", "") or "").replace('"', "").replace("'", "")
    pwd    = (os.getenv("AZURE_PASSWORD", "") or "").replace('"', "").replace("'", "")

    if not server or not db or "tu-" in server:
        return {"ok": False, "detail": "No configurada (.env)", "server": "—"}

    try:
        import pyodbc
    except ImportError:
        return {"ok": False, "detail": "pyodbc no instalado", "server": server}

    # Elegir el driver ODBC disponible
    drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    preferred = None
    for cand in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]:
        if cand in drivers:
            preferred = cand
            break
    if not preferred:
        return {"ok": False, "detail": "Sin driver ODBC de SQL Server", "server": server}

    conn_str = (
        f"DRIVER={{{preferred}}};SERVER={server};DATABASE={db};"
        f"UID={user};PWD={pwd};Encrypt=yes;TrustServerCertificate=no;"
        f"Connection Timeout=8;"
    )

    try:
        conn = pyodbc.connect(conn_str, timeout=8)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return {"ok": True, "detail": f"Conectada ({preferred})", "server": server}
    except Exception as e:
        msg = str(e)
        if "Login failed" in msg:
            detail = "Login fallido (usuario/password)"
        elif "Cannot open server" in msg or "not currently allowed" in msg:
            detail = "IP no permitida en el firewall de Azure"
        elif "timeout" in msg.lower():
            detail = "Timeout de conexion"
        else:
            detail = msg[:120]
        return {"ok": False, "detail": detail, "server": server}
