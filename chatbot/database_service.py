import os
from contextlib import contextmanager

import pyodbc

pyodbc.pooling = True

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos Azure SQL.
    """
    server = (os.getenv("AZURE_SERVER", "") or "").replace('"', "").replace("'", "")
    db     = (os.getenv("AZURE_DB", "") or "").replace('"', "").replace("'", "")
    user   = (os.getenv("AZURE_USER", "") or "").replace('"', "").replace("'", "")
    pwd    = (os.getenv("AZURE_PASSWORD", "") or "").replace('"', "").replace("'", "")

    if not server or not db:
        raise ValueError("Faltan variables de entorno para Azure SQL (AZURE_SERVER, AZURE_DB).")

    drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    preferred = None
    for cand in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]:
        if cand in drivers:
            preferred = cand
            break
    
    if not preferred:
        raise pyodbc.Error("No se encontró un driver ODBC válido para SQL Server.")

    conn_str = (
        f"DRIVER={{{preferred}}};SERVER={server};DATABASE={db};"
        f"UID={user};PWD={pwd};Encrypt=yes;TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

    return pyodbc.connect(conn_str)


@contextmanager
def _db_cursor():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
    finally:
        conn.close()


def get_active_athletes():
    """
    Obtiene TODOS los atletas activos masculinos para poder rankear globalmente.
    """
    query = """
    SELECT d.documento, d.nombre, d.club, d.ggee
    FROM dbo.deportistas d
    WHERE d.documento IN (
        SELECT DISTINCT deportista_documento 
        FROM dbo.resultados 
        WHERE ranking_type_id = 6
    )
    """

    with _db_cursor() as cursor:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_athlete_history(documento: str):
    """
    Obtiene el historial de pruebas de un atleta en específico.
    """
    query = """
    SELECT r.puntos, r.puesto, p.nombre, p.fecha, p.ciudad, p.championship_level, p.altitud, p.temperatura_max, p.humedad_media, p.precipitacion
    FROM dbo.resultados r
    JOIN dbo.pruebas p ON r.prueba_id = p.id
    WHERE r.deportista_documento = ? AND r.ranking_type_id = 6
    ORDER BY p.fecha DESC;
    """

    with _db_cursor() as cursor:
        cursor.execute(query, (documento,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_athletes_history_batch(documentos: list = None):
    """
    Obtiene el historial de TODOS los atletas en una sola consulta.
    Devuelve un diccionario { documento: [ historial ] }
    """
    query = """
    SELECT r.deportista_documento, r.puntos, r.puesto, p.nombre, p.fecha, p.ciudad, p.championship_level, p.altitud, p.temperatura_max, p.humedad_media, p.precipitacion
    FROM dbo.resultados r
    JOIN dbo.pruebas p ON r.prueba_id = p.id
    WHERE r.ranking_type_id = 6
    """

    params = ()
    if documentos:
        documentos = [doc for doc in documentos if doc]
        if documentos:
            placeholders = ", ".join("?" for _ in documentos)
            query += f" AND r.deportista_documento IN ({placeholders})"
            params = tuple(documentos)

    query += " ORDER BY p.fecha DESC;"

    with _db_cursor() as cursor:
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]

        history_map = {}
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            doc = row_dict.pop('deportista_documento')
            if doc not in history_map:
                history_map[doc] = []
            history_map[doc].append(row_dict)

        return history_map


def get_athlete_info(documento: str):
    """
    Obtiene los datos básicos de un atleta específico.
    """
    query = """
    SELECT d.documento, d.nombre, d.club, d.ggee, c.ciudad_sede, c.provincia
    FROM dbo.deportistas d
    LEFT JOIN dbo.clubes_geo c ON d.club = c.club
    WHERE d.documento = ?;
    """

    with _db_cursor() as cursor:
        cursor.execute(query, (documento,))
        row = cursor.fetchone()
        if not row:
            return None

        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))


def get_available_races():
    """
    Obtiene la lista de carreras reales disponibles en la base de datos
    (ranking_type_id = 6) para el simulador.
    """
    query = """
    SELECT DISTINCT p.id, p.nombre, p.fecha, p.ciudad, p.provincia, p.lat, p.lng, p.temperatura_max, p.altitud, p.humedad_media, p.precipitacion
    FROM dbo.pruebas p
    JOIN dbo.resultados r ON p.id = r.prueba_id
    WHERE r.ranking_type_id = 6
    ORDER BY p.fecha DESC, p.nombre;
    """

    with _db_cursor() as cursor:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_all_clubs():
    query = """
    SELECT club, ciudad_sede, provincia, lat, lng 
    FROM dbo.clubes_geo
    ORDER BY club;
    """

    with _db_cursor() as cursor:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_all_athletes():
    query = """
    SELECT documento, nombre, club, ggee
    FROM dbo.deportistas
    ORDER BY nombre;
    """

    with _db_cursor() as cursor:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_all_competitions():
    query = """
    SELECT id, nombre, fecha, ciudad, provincia, championship_level, altitud, temperatura_max, humedad_media
    FROM dbo.pruebas
    WHERE nombre NOT LIKE '%PLANTILLA%'
      AND nombre NOT LIKE '%EJEMPLO%'
      AND nombre NOT LIKE '%Relevos%'
      AND nombre NOT LIKE '%Equipos%'
      AND nombre NOT LIKE '%Clubes%'
      AND nombre NOT LIKE '%Aquabike%'
      AND nombre NOT LIKE '%Duatlón%'
      AND nombre NOT LIKE '%Media Distancia%'
      AND nombre NOT LIKE '%Larga Distancia%'
      AND nombre NOT LIKE '%Copa del Rey%'
      AND nombre NOT LIKE '%Cros%'
      AND nombre NOT LIKE '%Invierno%'
    ORDER BY fecha DESC;
    """

    with _db_cursor() as cursor:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_competition_results(prueba_id: int):
    query = """
    SELECT r.puesto, d.nombre as atleta, d.club, r.puntos, d.documento
    FROM dbo.resultados r
    JOIN dbo.deportistas d ON r.deportista_documento = d.documento
    WHERE r.prueba_id = ? AND r.ranking_type_id = 6
    ORDER BY r.puesto ASC;
    """

    with _db_cursor() as cursor:
        cursor.execute(query, (prueba_id,))
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
