import os
import json
import re
import pandas as pd
import numpy as np
import hashlib

# Configuración de rutas
WORKSPACE = r"c:\Users\mario\Downloads\Re_ Reunión TFM Conersys "
EXCEL_PATH = os.path.join(WORKSPACE, "data", "raw", "triatlon_masculino", "trm_2025_original.xlsx")
JSON_PATH = os.path.join(WORKSPACE, "data", "raw", "Campeonatos", "championships%3A2025.json")

# Salidas Normalizadas (para Azure SQL o análisis relacional)
OUT_DEPORTISTAS = os.path.join(WORKSPACE, "data", "processed", "deportistas_2025.csv")
OUT_PRUEBAS = os.path.join(WORKSPACE, "data", "processed", "pruebas_2025.csv")
OUT_CLUBES_GEO = os.path.join(WORKSPACE, "data", "processed", "clubes_geo_2025.csv")
OUT_RESULTADOS = os.path.join(WORKSPACE, "data", "processed", "resultados_2025.csv")

def normalize_word(w):
    w = w.upper()
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'À': 'A', 'È': 'E', 'Ì': 'I', 'Ò': 'O', 'Ù': 'U',
        'Ä': 'A', 'Ë': 'E', 'Ï': 'I', 'Ö': 'O', 'Ü': 'U',
        'Ñ': 'N'
    }
    for orig, rep in replacements.items():
        w = w.replace(orig, rep)
    return re.sub(r'[^A-Z0-9]', '', w)

def get_tokens(text):
    if not isinstance(text, str):
        return set()
    words = text.split()
    tokens = set()
    for w in words:
        norm = normalize_word(w)
        if norm and len(norm) > 1:
            tokens.add(norm)
    return tokens

def run_normalization():
    print("Iniciando la generación de Datasets Normalizados (Snowflake Schema)...")
    
    # ==========================================
    # 1. GENERAR DATASET DE PRUEBAS (CAMPEONATOS)
    # ==========================================
    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encontró {JSON_PATH}")
        return
        
    print("Procesando Campeonatos desde JSON...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        championships_data = json.load(f)
        
    pruebas_list = []
    pruebas_json_lookup = [] # Para token-matching posterior
    
    for item in championships_data:
        c = item.get('c', {})
        name = c.get('Name', '').strip()
        if name:
            p_id = c.get('Id')
            season = int(c.get('Season', 2025))
            level = c.get('ChampionshipLevel', 'C')
            fecha = c.get('StartDate', '2025-12-31')[:10]
            ciudad = c.get('City', 'DESCONOCIDA').strip().upper()
            provincia = c.get('Province', 'DESCONOCIDA').strip().upper()
            lat = float(c.get('Lat', 0.0)) if c.get('Lat') else 0.0
            lng = float(c.get('Lng', 0.0)) if c.get('Lng') else 0.0
            
            pruebas_list.append({
                'id': p_id,
                'season': season,
                'nombre': name,
                'championship_level': level,
                'fecha': fecha,
                'ciudad': ciudad,
                'provincia': provincia,
                'lat': lat,
                'lng': lng
            })
            
            pruebas_json_lookup.append({
                'id': p_id,
                'name': name,
                'fecha': fecha,
                'championship_level': level,
                'lat': lat,
                'lng': lng,
                'tokens': get_tokens(name)
            })
            
    df_pruebas = pd.DataFrame(pruebas_list)
    df_pruebas.to_csv(OUT_PRUEBAS, index=False, encoding='utf-8')
    print(f"-> Exportado Dataset de Pruebas: {df_pruebas.shape[0]} registros en {OUT_PRUEBAS}")

    # ==========================================
    # 2. PROCESAR RANKINGS EXCEL (ATLETAS & CLUBES & RESULTADOS)
    # ==========================================
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encontró {EXCEL_PATH}")
        return
        
    print("Cargando rankings de Triatlón Masculino 2025...")
    df_raw = pd.read_excel(EXCEL_PATH)
    
    # 2a. Deportistas (Deduplicados)
    print("Procesando Deportistas...")
    # Limpiamos DNI/documento
    df_raw['DOCUMENTO'] = df_raw['DOCUMENTO'].astype(str).str.strip()
    df_raw['NOMBRE'] = df_raw['NOMBRE'].astype(str).str.strip().str.upper()
    df_raw['CLUB'] = df_raw['CLUB'].astype(str).str.strip().str.upper().fillna("SIN CLUB")
    df_raw['GGEE'] = df_raw['GGEE'].astype(str).str.strip().str.upper().fillna("ABSOLUTO")
    
    # Mantener el registro más completo de cada deportista (por documento)
    df_deportistas = df_raw[['DOCUMENTO', 'NOMBRE', 'CLUB', 'GGEE']].drop_duplicates(subset=['DOCUMENTO'])
    df_deportistas.to_csv(OUT_DEPORTISTAS, index=False, encoding='utf-8')
    print(f"-> Exportado Dataset de Deportistas: {df_deportistas.shape[0]} registros en {OUT_DEPORTISTAS}")

    # 2b. Clubes y Geocodificación (Ceuta es Ceuta, Bétera es Bétera, Rivas es Rivas)
    print("Procesando Clubes y Coordenadas...")
    cities_coords = {
        "CEUTA": (35.8893, -5.3213),
        "BETERA": (39.5921, -0.4578),
        "RIVAS": (40.3644, -3.5261),
        "DIABLILLOS": (40.3644, -3.5261),
        "CORUNA": (43.3623, -8.4115),
        "VIATORIA": (42.8467, -2.6724),
        "GASTEIZ": (42.8467, -2.6724),
        "ALBACETE": (38.9874, -1.8516),
        "ALICANTE": (38.3452, -0.4810),
        "ALACANT": (38.3452, -0.4810),
        "ALMERIA": (36.8381, -2.4597),
        "OVIEDO": (43.3603, -5.8448),
        "GIJON": (43.5322, -5.6610),
        "AVILA": (40.6567, -4.7002),
        "BADAJOZ": (38.8794, -6.9706),
        "BARCELONA": (41.3851, 2.1734),
        "BILBAO": (43.2630, -2.9350),
        "BILBO": (43.2630, -2.9350),
        "BURGOS": (42.3440, -3.6969),
        "CACERES": (39.4753, -6.3724),
        "CADIZ": (36.5298, -6.2926),
        "SANTANDER": (43.4623, -3.8099),
        "CASTELLON": (39.9864, -0.0513),
        "CIUDAD REAL": (38.9848, -3.9274),
        "CORDOBA": (37.8882, -4.7794),
        "CUENCA": (40.0704, -2.1374),
        "DONOSTIA": (43.3183, -1.9812),
        "SAN SEBASTIAN": (43.3183, -1.9812),
        "GIRONA": (41.9794, 2.8214),
        "GERONA": (41.9794, 2.8214),
        "GRANADA": (37.1773, -3.5986),
        "GUADALAJARA": (40.6292, -3.1617),
        "HUELVA": (37.2614, -6.9447),
        "HUESCA": (42.1362, -0.4085),
        "BALEARES": (39.5696, 2.6502),
        "BALEARS": (39.5696, 2.6502),
        "PALMA": (39.5696, 2.6502),
        "JAEN": (37.7796, -3.7849),
        "LOGRONO": (42.4627, -2.4450),
        "RIOJA": (42.4627, -2.4450),
        "LAS PALMAS": (28.1235, -15.4363),
        "LEON": (42.5987, -5.5671),
        "LERIDA": (41.6176, 0.6200),
        "LLEIDA": (41.6176, 0.6200),
        "LUGO": (43.0125, -7.5558),
        "MADRID": (40.4168, -3.7038),
        "MALAGA": (36.7213, -4.4214),
        "MELILLA": (35.2923, -2.9381),
        "MURCIA": (37.9922, -1.1307),
        "PAMPLONA": (42.8125, -1.6458),
        "IRUNA": (42.8125, -1.6458),
        "ORENSE": (42.3358, -7.8639),
        "OURENSE": (42.3358, -7.8639),
        "PALENCIA": (42.0096, -4.5286),
        "PONTEVEDRA": (42.4310, -8.6444),
        "SALAMANCA": (40.9701, -5.6635),
        "TENERIFE": (28.4636, -16.2518),
        "SEGOVIA": (40.9429, -4.1088),
        "SEVILLA": (37.3891, -5.9845),
        "SORIA": (41.7640, -2.4688),
        "TARRAGONA": (41.1189, 1.2445),
        "TERUEL": (40.3457, -1.1065),
        "TOLEDO": (39.8628, -4.0273),
        "VALENCIA": (39.4699, -0.3763),
        "VALLADOLID": (41.6523, -4.7245),
        "ZAMORA": (41.5033, -5.7463),
        "ZARAGOZA": (41.6488, -0.8891),
        "ALUSIGMA": (43.3197, -3.0202),
        "PEÑOTA": (43.3197, -3.0202),
        "PENOTA": (43.3197, -3.0202),
        "SALTOKI": (42.8125, -1.6458),
        "DELIKIA": (38.9678, -0.1802),
        "BARROSA": (36.4173, -6.1458),
        "AMANDARRI": (43.3153, -2.6791),
        "CASABLANCA": (41.6488, -0.8891),
        "TRANSNATUR": (41.6488, -0.8891),
        "GALOSPORT": (36.8381, -2.4597),
        "ALGEMESI": (39.1892, -0.4372),
        "NARON": (43.5014, -8.1914),
        "TRAGAMILLAS": (41.0503, -0.1311),
        "LACERTA": (40.9429, -4.1088),
        "ALCORES": (37.3883, -5.7202),
        "TRIPUÇOL": (39.6172, -0.3014),
        "TRIPUCOL": (39.6172, -0.3014),
        "BABYSCHOOL": (37.7796, -3.7849),
        "ANTXINTXIKA": (43.0658, -2.4883),
        "SALMANTINA": (40.9701, -5.6635),
        "TRIECIJA": (37.5414, -5.0792),
        "PLASENCIA": (40.0303, -6.0894),
        "TORRELAVEGA": (43.3492, -4.0478),
        "TINAJO": (29.0628, -13.6753),
        "PRAT": (41.3283, 2.0914),
        "POLANCO": (43.3853, -4.0153),
        "ARCHENA": (38.1172, -1.2983),
        "CANET": (39.6783, -0.2183),
        "ALMANSA": (38.8683, -1.0978),
        "RIAS BAIXAS": (42.4310, -8.6444),
        "ALISIOS": (28.4636, -16.2518),
        "ALHAMA": (37.8503, -1.4253),
        "AZAGRESA": (42.2983, -1.8983),
        "AZAGRA": (42.2983, -1.8983),
        "MOLINERA": (36.6850, -6.1261),
        "AL FANADIC": (37.8882, -4.7794),
        "FOGAR": (43.2123, -8.6912),
        "CORRE CUITA": (39.4699, -0.3763),
        "TODO POR UN SUEÑO": (36.8381, -2.4597),
        "TRIDAN": (37.9778, -0.6833),
        "SIPCAM": (38.1172, -1.2983),
        "TRIACADEMY": (39.5696, 2.6502),
        "CHAMO DIAZ": (39.4753, -6.3724),
        "BULL": (43.4623, -3.8099),
        "OCEAN": (28.4636, -16.2518),
        "ROLLERBIKE": (41.7640, -2.4688),
        "ANTHUS": (37.2614, -6.9447),
        "HIRU HERRI": (42.8258, -1.6022),
        "LAW": (39.4699, -0.3763),
        "OZONO": (28.4636, -16.2518),
        "YEPA": (43.3183, -1.9812),
        "LAGUNA": (41.5833, -4.7222),
        "ALCANTARILLA": (37.9714, -1.2131),
        "GUERRITA": (37.9714, -1.2131),
        "ARANGUREN": (42.7931, -1.5458),
        "TRIKIMANES": (36.7213, -4.4214),
        "GALDAKAO": (43.2308, -2.8458),
        "MOZOILO": (43.2308, -2.8458),
        "UR GAZIA": (42.8125, -1.6458),
        "GUADIATO": (38.2630, -5.2678),
        "ALOHA": (36.5074, -4.8858),
        "ZARAUZKO": (43.2842, -2.1714),
        "ZARAUTZ": (43.2842, -2.1714),
        "HONDARRIBI": (43.3639, -1.7914),
        "BIOSNAR": (43.3639, -1.7914),
        "VIBIKE": (42.8467, -2.6724),
        "MIJAS": (36.5958, -4.6372),
        "AZKOITRI": (43.1783, -2.3114),
        "AZKOITIA": (43.1783, -2.3114),
        "MEDITERRANEO": (36.7213, -4.4214),
        "AL ANDALUS": (37.3891, -5.9845),
        "LA BLANCA": (42.8467, -2.6724),
        "TRIGOI": (38.9892, -0.5212),
        "SULAYR": (37.1773, -3.5986),
        "SANTIAGO": (42.8782, -8.5448),
        "COMPOSTELA": (42.8782, -8.5448),
        "SANTIAGO DE COMPOSTELA": (42.8782, -8.5448),
        "ORIHUELA": (38.0848, -0.9472),
        "EQTR": (38.0848, -0.9472),
        "M1": (41.3851, 2.1734),
        "FASTTRIATLON": (41.3851, 2.1734),
        "KATOA": (41.3851, 2.1734),
        "REALES": (28.3842, -16.5878),
        "RESISTENTIA": (28.1219, -16.7291),
        "DIABLILLOS DE RIVAS": (40.3644, -3.5261),
    }

    # Intentamos cargar calendar_cities_db.json
    cities_db = {}
    calendar_cities_path = os.path.join(WORKSPACE, "data", "raw", "calendar_cities_db.json")
    if os.path.exists(calendar_cities_path):
        try:
            with open(calendar_cities_path, 'r', encoding='utf-8') as f:
                cities_db = json.load(f)
        except Exception as e:
            print(f"No se pudo cargar calendar_cities_db.json: {e}")

    merged_lookup = {**cities_db, **cities_coords}
    norm_lookup = {}
    for k, v in merged_lookup.items():
        words = str(k).split()
        norm_words = []
        for w in words:
            nw = normalize_word(w)
            if nw:
                norm_words.append(nw)
        norm_key = " ".join(norm_words)
        if len(norm_key) >= 2:
            norm_lookup[norm_key] = v
            
    sorted_locs = sorted(norm_lookup.keys(), key=len, reverse=True)
    
    unique_clubs = df_raw['CLUB'].dropna().unique()
    clubes_geo_list = []
    
    for c in unique_clubs:
        c_clean = str(c).strip().upper()
        c_words = c_clean.split()
        norm_club_words = []
        for w in c_words:
            nw = normalize_word(w)
            if nw:
                norm_club_words.append(nw)
        norm_club = " ".join(norm_club_words)
        
        lat, lng = 40.4168, -3.7038 # Madrid default fallback
        ciudad_sede = "DESCONOCIDA"
        
        for loc in sorted_locs:
            if re.search(r'\b' + re.escape(loc) + r'\b', norm_club) or loc in norm_club:
                lat, lng = norm_lookup[loc]
                ciudad_sede = loc
                break
                
        clubes_geo_list.append({
            'club': c_clean,
            'ciudad_sede': ciudad_sede,
            'lat': lat,
            'lng': lng
        })
        
    df_clubes_geo = pd.DataFrame(clubes_geo_list)
    df_clubes_geo.to_csv(OUT_CLUBES_GEO, index=False, encoding='utf-8')
    print(f"-> Exportado Dataset de Clubes: {df_clubes_geo.shape[0]} registros en {OUT_CLUBES_GEO}")

    # ==========================================
    # 3. GENERAR TABLA DE HECHOS: RESULTADOS (Fact Table)
    # ==========================================
    print("Mapeando carreras del Excel a Pruebas del JSON para generar la tabla de hechos...")
    metadatos_cols = ['PUESTO', 'PUNTOS', 'DOCUMENTO', 'NOMBRE', 'CLUB', 'NUMERO PRUEBAS', 'GGEE', 'VIGENTE']
    carreras_cols = [col for col in df_raw.columns if col not in metadatos_cols]
    
    locations_list = [
        "CORUNA", "AGUILAS", "FUENTE", "ALAMO", "ORIHUELA", "VOLCANO", "MEDITERRANEAN", 
        "JOVELLANOS", "ALMERIA", "OLIVA", "RASILLO", "DONOSTIA", "ROQUETAS", "NAGORE", 
        "CEUTA", "TENERIFE", "VALENCIANA", "CATALUNA", "BALEARES", "MADRID", "MURCIA", 
        "ANDALUCIA", "LEON", "EXTREMADURA", "CANTABRIA", "ARAGON", "RIOJA", "EUSKADI", 
        "GALICIA", "MANCHA", "CANARIAS", "ASTURIAS", "MELILLA"
    ]
    
    carreras_mapeadas = {}
    for col in carreras_cols:
        col_tokens = get_tokens(col)
        best_match = None
        best_score = 0
        
        for p in pruebas_json_lookup:
            common = col_tokens.intersection(p['tokens'])
            score = len(common)
            for loc in locations_list:
                if loc in col_tokens and loc in p['tokens']:
                    score += 5
            if "2025" in col_tokens and "2025" in p['tokens']:
                score += 1
            if "2024" in col_tokens and "2024" in p['tokens']:
                score += 1
            if score > best_score:
                best_score = score
                best_match = p
                
        if best_score >= 3 and best_match is not None:
            carreras_mapeadas[col] = best_match['id']
            
    print(f"Vinculadas {len(carreras_mapeadas)} de {len(carreras_cols)} columnas del Excel a Pruebas del JSON.")
    
    resultados_list = []
    # Usaremos ranking_type_id = 6 para TRM (Triatlón Masculino 2025)
    ranking_type_id = 6 
    season = 2025
    
    for col, prueba_id in carreras_mapeadas.items():
        # Filtrar atletas que participaron
        df_c = df_raw[['DOCUMENTO', col]].copy().dropna(subset=[col])
        df_c = df_c[df_c[col] > 0]
        
        # Calcular puesto en esa carrera en particular
        df_c = df_c.sort_values(by=col, ascending=False)
        df_c['puesto_carrera'] = range(1, len(df_c) + 1)
        
        for _, row in df_c.iterrows():
            resultados_list.append({
                'season': season,
                'ranking_type_id': ranking_type_id,
                'deportista_documento': str(row['DOCUMENTO']).strip(),
                'prueba_id': int(prueba_id),
                'puntos': float(row[col]),
                'puesto': int(row['puesto_carrera'])
            })
            
    df_resultados = pd.DataFrame(resultados_list)
    df_resultados.to_csv(OUT_RESULTADOS, index=False, encoding='utf-8')
    print(f"-> Exportado Dataset de Hechos (Resultados): {df_resultados.shape[0]} registros en {OUT_RESULTADOS}")
    print("\n¡PROCESAMIENTO Y EXPORTACIÓN COMPLETADA CON ÉXITO!")

if __name__ == "__main__":
    run_normalization()
