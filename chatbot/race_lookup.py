"""
Busqueda de carreras de triatlon en los datos de FETRI.

Dado el nombre (o ciudad) de una prueba, devuelve su localizacion, nivel de
campeonato y condiciones climaticas, ya convertidas a las variables que usa
el modelo predictivo. Asi el chatbot puede predecir con datos reales de la
prueba sin que el usuario los introduzca a mano.
"""
import os
import math
import unicodedata
from collections import Counter
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRUEBAS_CSV = os.path.join(BASE_DIR, "data", "processed", "pruebas_2025.csv")

# Palabras tan comunes en los nombres que no aportan para distinguir una carrera.
# Incluye codigos de serie/modalidad/distancia que aparecen en muchas pruebas.
STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "por", "y", "en", "para",
    "campeonato", "espana", "europa", "mundo", "mundial", "triatlon", "duatlon",
    "acuatlon", "aquabike", "prueba", "clasificatorio", "copa", "circuito",
    "open", "trofeo", "liga", "memorial", "gran", "grand", "2025", "2026",
    # codigos de serie y modalidad
    "prn", "tri", "duo", "cto", "oly", "spr", "sprint", "supersprint",
    "md", "ld", "pto", "cros", "cross", "relevos", "parejas", "invierno",
    "distancia", "larga", "media", "corta", "ciudad", "villa",
    # palabras en ingles habituales en nombres internacionales
    "world", "triathlon", "championship", "championships", "series", "cup",
    "age", "group", "standard", "distance", "elite", "para",
}

# IDF minimo que debe alcanzar al menos una palabra coincidente para aceptar la
# carrera: evita falsos positivos por palabras genericas. Una palabra distintiva
# (p.ej. una ciudad poco frecuente) supera holgadamente este valor.
DISTINCTIVE_IDF = 3.5

_df_cache: pd.DataFrame | None = None
_idf: dict[str, float] = {}


def _normalize(s: str) -> str:
    """Minusculas sin acentos ni signos, para comparar nombres de forma robusta."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.lower().strip()


def _tokens(s: str) -> list[str]:
    """Palabras de >=3 letras, sin signos."""
    norm = _normalize(s).replace("/", " ").replace("-", " ")
    return [w for w in "".join(c if c.isalnum() else " " for c in norm).split() if len(w) >= 3]


def _load() -> pd.DataFrame:
    global _df_cache, _idf
    if _df_cache is None:
        df = pd.read_csv(PRUEBAS_CSV)
        df["_nombre_norm"] = df["nombre"].map(_normalize)
        df["_ciudad_norm"] = df["ciudad"].map(_normalize)
        df["_tokens"] = (df["nombre"].fillna("") + " " + df["ciudad"].fillna("")).map(
            lambda s: set(_tokens(s))
        )
        # IDF: cuanto mas rara es una palabra, mas peso (una ciudad pesa mas que "campeonato")
        n = len(df)
        doc_freq = Counter()
        for toks in df["_tokens"]:
            for t in toks:
                doc_freq[t] += 1
        _idf = {t: math.log((n + 1) / (f + 1)) + 1.0 for t, f in doc_freq.items()}
        _df_cache = df
    return _df_cache


def _to_features(row: pd.Series) -> dict:
    """Convierte una fila de prueba a las variables del modelo."""
    temp = float(row.get("temperatura_max") or 0)
    prec = float(row.get("precipitacion") or 0)
    hum  = float(row.get("humedad_media") or 0)

    # Mes de la carrera
    mes = None
    try:
        mes = datetime.strptime(str(row.get("fecha")).strip(), "%Y-%m-%d").month
    except Exception:
        pass

    feats = {
        "race_temperature": temp,
        "race_humidity": hum,
        "race_altitude_m": float(row.get("altitud") or 0),
        "race_city": str(row.get("ciudad") or ""),
    }
    if mes:
        feats["race_month"] = mes
    return feats


def _rank(consulta: str) -> list[tuple[float, int]]:
    """Devuelve [(score, idx)] de carreras ordenadas por relevancia a la consulta."""
    df = _load()
    q_tokens = [t for t in _tokens(consulta) if t not in STOPWORDS]
    if not q_tokens:
        q_tokens = _tokens(consulta)
    if not q_tokens:
        return []

    scores = []
    for idx, row in df.iterrows():
        if "ejemplo" in row["_nombre_norm"] or "plantilla" in row["_nombre_norm"]:
            continue
        toks = row["_tokens"]
        matched = [t for t in q_tokens if t in toks]
        if not matched:
            continue
        # Exigir al menos una palabra distintiva (no generica) para aceptar la carrera
        if max(_idf.get(t, 1.0) for t in matched) < DISTINCTIVE_IDF:
            continue
        score = sum(_idf.get(t, 1.0) for t in matched)
        scores.append((score, idx))
    scores.sort(reverse=True)
    return scores


def _carrera_dict(row: pd.Series) -> dict:
    return {
        "id": int(row["id"]),
        "nombre": row["nombre"],
        "ciudad": row["ciudad"],
        "provincia": row["provincia"],
        "fecha": row["fecha"],
        "nivel_campeonato": int(row.get("championship_level") or 2),
        "altitud_m": float(row.get("altitud") or 0),
        "temperatura_max_c": float(row.get("temperatura_max") or 0),
        "humedad_media_pct": float(row.get("humedad_media") or 0),
        "precipitacion_mm": float(row.get("precipitacion") or 0),
        "viento_max_kmh": float(row.get("viento_max") or 0),
    }


def buscar(consulta: str, max_resultados: int = 5) -> dict:
    """
    Busca una carrera por nombre o ciudad, puntuando por relevancia.
    Las palabras distintivas (ciudades) pesan mas que las comunes ("campeonato").

    Returns dict:
      - encontrada (bool)
      - si hay un claro ganador: datos completos + features de la carrera
      - si hay empate entre varias: lista de candidatas para que el usuario aclare
    """
    df = _load()
    if not _normalize(consulta):
        return {"encontrada": False, "motivo": "consulta vacia"}

    scores = _rank(consulta)
    if not scores:
        return {"encontrada": False, "motivo": f"no hay carreras que coincidan con '{consulta}'"}

    best_score = scores[0][0]

    # Candidatas relevantes: las que estan cerca del mejor score (>=60%)
    top = [(s, i) for s, i in scores if s >= best_score * 0.6]

    # Ganador claro: el mejor destaca y no hay otra carrera casi igual de relevante
    clear_winner = len(top) == 1 or (len(scores) > 1 and scores[0][0] >= scores[1][0] * 1.5)

    if clear_winner:
        row = df.loc[scores[0][1]]
        return {"encontrada": True, "carrera": _carrera_dict(row), "features": _to_features(row)}

    return {
        "encontrada": True,
        "multiples": True,
        "candidatas": [
            {"nombre": df.loc[i]["nombre"], "ciudad": df.loc[i]["ciudad"], "fecha": df.loc[i]["fecha"]}
            for _, i in top[:max_resultados]
        ],
    }


# ---------------------------------------------------------------------------
# Resultados reales de una carrera (ganador y podio)
# ---------------------------------------------------------------------------

_resultados_cache = None
_deportistas_cache = None


def _load_resultados():
    global _resultados_cache, _deportistas_cache
    if _resultados_cache is None:
        _resultados_cache = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "resultados_2025.csv"))
        _deportistas_cache = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "deportistas_2025.csv"))
    return _resultados_cache, _deportistas_cache


def resultados(consulta: str, top_n: int = 5) -> dict:
    """
    Devuelve la clasificacion real (ganador y primeros puestos) de una carrera ya disputada.
    Util para responder 'quien gano X'.
    """
    df = _load()
    scores = _rank(consulta)
    if not scores:
        return {"encontrada": False, "motivo": f"no hay carreras que coincidan con '{consulta}'"}

    res, dep = _load_resultados()

    # Buscar, entre las carreras mas relevantes, la primera que tenga resultados cargados
    elegido_idx = None
    for _, idx in scores[:8]:
        pid = int(df.loc[idx]["id"])
        if (res["prueba_id"] == pid).any():
            elegido_idx = idx
            break

    if elegido_idx is None:
        # La carrera existe pero no hay clasificacion cargada para ella
        row = df.loc[scores[0][1]]
        return {
            "encontrada": True,
            "hay_resultados": False,
            "carrera": {"nombre": row["nombre"], "ciudad": row["ciudad"], "fecha": row["fecha"]},
            "motivo": "Esta carrera no tiene clasificacion cargada en los datos.",
        }

    row = df.loc[elegido_idx]
    pid = int(row["id"])
    clasif = (
        res[res["prueba_id"] == pid]
        .sort_values("puesto")
        .merge(dep, left_on="deportista_documento", right_on="DOCUMENTO", how="left")
    )

    podio = []
    for _, r in clasif.head(top_n).iterrows():
        podio.append({
            "puesto": int(r["puesto"]),
            "atleta": r.get("NOMBRE") if pd.notna(r.get("NOMBRE")) else "Desconocido",
            "club": r.get("CLUB") if pd.notna(r.get("CLUB")) else "",
            "puntos": round(float(r["puntos"]), 1),
        })

    return {
        "encontrada": True,
        "hay_resultados": True,
        "carrera": {"nombre": row["nombre"], "ciudad": row["ciudad"], "fecha": row["fecha"]},
        "ganador": podio[0] if podio else None,
        "clasificacion": podio,
        "n_participantes": int((res["prueba_id"] == pid).sum()),
    }
