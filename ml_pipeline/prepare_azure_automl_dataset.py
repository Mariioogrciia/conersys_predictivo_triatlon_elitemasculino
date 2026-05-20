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
OUTPUT_PATH = os.path.join(WORKSPACE, "data", "processed", "trm_2025_azure_automl.csv")

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
    # Dejar solo caracteres alfabéticos
    return re.sub(r'[^A-Z0-9]', '', w)

def get_tokens(text):
    if not isinstance(text, str):
        return set()
    words = text.split()
    tokens = set()
    for w in words:
        norm = normalize_word(w)
        if norm and len(norm) > 1: # ignorar letras sueltas
            tokens.add(norm)
    return tokens

def calculate_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia Haversine en kilómetros entre dos coordenadas geográficas."""
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return 0.0
    if lat1 == 0.0 or lon1 == 0.0 or lat2 == 0.0 or lon2 == 0.0:
        return 0.0 # Sin coordenadas
    
    # Convertir a radianes
    rlat1, rlon1 = np.radians(lat1), np.radians(lon1)
    rlat2, rlon2 = np.radians(lat2), np.radians(lon2)
    
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    
    a = np.sin(dlat/2)**2 + np.cos(rlat1) * np.cos(rlat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0 # Radio de la Tierra en km
    return c * r

def run():
    print("Iniciando la preparación del dataset de Triatlón Masculino 2025 para Azure AutoML...")
    
    # 1. Cargar el JSON de campeonatos y crear catálogo indexado
    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encontró el archivo JSON en: {JSON_PATH}")
        return
        
    print(f"Cargando campeonatos desde JSON: {JSON_PATH}")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        championships_data = json.load(f)
        
    pruebas_json = []
    for item in championships_data:
        c = item.get('c', {})
        name = c.get('Name', '').strip()
        if name:
            pruebas_json.append({
                'id': c.get('Id'),
                'name': name,
                'fecha': c.get('StartDate', '2025-12-31')[:10], # Solo YYYY-MM-DD
                'championship_level': c.get('ChampionshipLevel', 'C'),
                'ciudad': c.get('City', 'DESCONOCIDA'),
                'provincia': c.get('Province', 'DESCONOCIDA'),
                'lat': float(c.get('Lat', 0.0)) if c.get('Lat') else 0.0,
                'lng': float(c.get('Lng', 0.0)) if c.get('Lng') else 0.0,
                'tokens': get_tokens(name)
            })
            
    print(f"Cargadas {len(pruebas_json)} pruebas desde el JSON.")

    # 2. Cargar el Excel de Rankings Masculino 2025
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encontró el Excel en: {EXCEL_PATH}")
        return
        
    print(f"Cargando rankings de Triatlón Masculino 2025: {EXCEL_PATH}")
    df_raw = pd.read_excel(EXCEL_PATH)
    print(f"Matriz de entrada: {df_raw.shape[0]} atletas x {df_raw.shape[1]} columnas.")

    # 3. Mapear las columnas de carreras usando algoritmos de token-matching robustos
    metadatos_cols = ['PUESTO', 'PUNTOS', 'DOCUMENTO', 'NOMBRE', 'CLUB', 'NUMERO PRUEBAS', 'GGEE', 'VIGENTE']
    carreras_cols = [col for col in df_raw.columns if col not in metadatos_cols]
    
    print(f"Identificadas {len(carreras_cols)} columnas de carreras. Realizando Token-Matching...")
    
    # Palabras clave de localización geográfica en los nombres de carreras para evitar falsos positivos
    locations = [
        "CORUNA", "AGUILAS", "FUENTE", "ALAMO", "ORIHUELA", "VOLCANO", "MEDITERRANEAN", 
        "JOVELLANOS", "ALMERIA", "OLIVA", "RASILLO", "DONOSTIA", "ROQUETAS", "NAGORE", 
        "CEUTA", "TENERIFE", "VALENCIANA", "CATALUNA", "BALEARES", "MADRID", "MURCIA", 
        "ANDALUCIA", "LEON", "EXTREMADURA", "CANTABRIA", "ARAGON", "RIOJA", "EUSKADI", 
        "GALICIA", "MANCHA", "CANARIAS", "ASTURIAS", "MELILLA"
    ]
    
    carreras_mapeadas = []
    
    for col in carreras_cols:
        col_tokens = get_tokens(col)
        best_match = None
        best_score = 0
        
        for p in pruebas_json:
            common = col_tokens.intersection(p['tokens'])
            score = len(common)
            
            # Boost por coincidencia de localización
            for loc in locations:
                if loc in col_tokens and loc in p['tokens']:
                    score += 5
                    
            # Boost por coincidencia de año
            if "2025" in col_tokens and "2025" in p['tokens']:
                score += 1
            if "2024" in col_tokens and "2024" in p['tokens']:
                score += 1
                
            if score > best_score:
                best_score = score
                best_match = p
                
        # Si el score supera el umbral, usamos los datos reales del JSON
        if best_score >= 3 and best_match is not None:
            carreras_mapeadas.append({
                'columna_excel': col,
                'id': best_match['id'],
                'fecha': best_match['fecha'],
                'championship_level': best_match['championship_level'],
                'lat': best_match['lat'],
                'lng': best_match['lng'],
                'provincia': best_match['provincia']
            })
        else:
            # Fallback seguro con datos por defecto para no perder la carrera
            carreras_mapeadas.append({
                'columna_excel': col,
                'id': 99999,
                'fecha': '2025-12-31',
                'championship_level': 'C',
                'lat': 0.0,
                'lng': 0.0,
                'provincia': 'DESCONOCIDA'
            })
            
    # Ordenar carreras cronológicamente para evitar data leakage
    carreras_mapeadas = sorted(carreras_mapeadas, key=lambda x: x['fecha'])
    print(f"Mapeo y ordenación completada. {len([c for c in carreras_mapeadas if c['id'] != 99999])} carreras vinculadas con éxito a fechas precisas.")

    # 4. Inicializar Geocodificación de Clubes (Basado en la regla de negocio del usuario: Ceuta es Ceuta, Bétera es Bétera, Rivas es Rivas, etc.)
    print("Inicializando geocodificación geográfica de Clubes basada en reglas de negocio...")
    
    # Base de datos de coordenadas por ciudades y palabras clave de clubes
    cities_coords = {
        # Reglas explícitas del usuario
        "CEUTA": (35.8893, -5.3213),
        "BETERA": (39.5921, -0.4578),
        "RIVAS": (40.3644, -3.5261),
        "DIABLILLOS": (40.3644, -3.5261), # Diablillos de Rivas
        
        # Capitales de provincia y principales localizaciones en España
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
        
        # Clubs específicos y sus localizaciones
        "ALUSIGMA": (43.3197, -3.0202), # Portugalete (Bilbao)
        "PEÑOTA": (43.3197, -3.0202), # Portugalete (Bilbao)
        "PENOTA": (43.3197, -3.0202), # Portugalete
        "SALTOKI": (42.8125, -1.6458), # Pamplona
        "DELIKIA": (38.9678, -0.1802), # Gandia
        "BARROSA": (36.4173, -6.1458), # Chiclana de la Frontera
        "AMANDARRI": (43.3153, -2.6791), # Gernika
        "CASABLANCA": (41.6488, -0.8891), # Zaragoza
        "TRANSNATUR": (41.6488, -0.8891), # Zaragoza
        "GALOSPORT": (36.8381, -2.4597), # Almeria
        "ALGEMESI": (39.1892, -0.4372),
        "NARON": (43.5014, -8.1914),
        "TRAGAMILLAS": (41.0503, -0.1311), # Alcañiz
        "LACERTA": (40.9429, -4.1088), # Segovia
        "ALCORES": (37.3883, -5.7202), # Viso del Alcor
        "TRIPUÇOL": (39.6172, -0.3014),
        "TRIPUCOL": (39.6172, -0.3014),
        "BABYSCHOOL": (37.7796, -3.7849), # Jaén
        "ANTXINTXIKA": (43.0658, -2.4883), # Debagoiena
        "SALMANTINA": (40.9701, -5.6635), # Salamanca
        "TRIECIJA": (37.5414, -5.0792), # Écija
        "PLASENCIA": (40.0303, -6.0894),
        "TORRELAVEGA": (43.3492, -4.0478),
        "TINAJO": (29.0628, -13.6753), # Lanzarote
        
        # Localidades adicionales comunes en los clubes
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

    # Intentamos cargar también el JSON del calendario si está disponible para añadir más ciudades
    cities_db = {}
    calendar_cities_path = os.path.join(WORKSPACE, "data", "raw", "calendar_cities_db.json")
    if os.path.exists(calendar_cities_path):
        try:
            with open(calendar_cities_path, 'r', encoding='utf-8') as f:
                cities_db = json.load(f)
        except Exception as e:
            print(f"Error al cargar calendar_cities_db.json: {e}")

    # Combinar los diccionarios
    merged_lookup = {**cities_db, **cities_coords}
    
    # Crear un diccionario normalizado
    norm_lookup = {}
    for k, v in merged_lookup.items():
        # Usamos normalize_word para cada palabra en el nombre de la localización
        words = str(k).split()
        norm_words = []
        for w in words:
            nw = normalize_word(w)
            if nw:
                norm_words.append(nw)
        norm_key = " ".join(norm_words)
        if len(norm_key) >= 2: # Evitar ruidos muy pequeños
            norm_lookup[norm_key] = v
            
    # Ordenar por longitud de clave descendente para priorizar nombres más largos
    sorted_locs = sorted(norm_lookup.keys(), key=len, reverse=True)

    clubes_unicos = df_raw['CLUB'].dropna().unique()
    club_coords = {}
    
    for c in clubes_unicos:
        c_clean = str(c).strip().upper()
        # Normalizar el nombre del club
        c_words = c_clean.split()
        norm_club_words = []
        for w in c_words:
            nw = normalize_word(w)
            if nw:
                norm_club_words.append(nw)
        norm_club = " ".join(norm_club_words)
        
        found = False
        for loc in sorted_locs:
            # Buscar coincidencia de palabra completa o subcadena directa
            if re.search(r'\b' + re.escape(loc) + r'\b', norm_club) or loc in norm_club:
                club_coords[c_clean] = norm_lookup[loc]
                found = True
                break
        
        if not found:
            # Fallback al centro geográfico de España (Madrid)
            club_coords[c_clean] = (40.4168, -3.7038)


    # 5. Transformación e Ingeniería de Características Cronológica (Rolling Features)
    print("\nTransformando datos a formato largo y calculando rolling features cronológicamente...")
    
    # deportista_id -> lista de puntuaciones obtenidas en orden cronológico
    historial_deportistas = {}
    registros_finales = []
    
    # Recorremos cada carrera en estricto orden cronológico
    for idx, c_meta in enumerate(carreras_mapeadas):
        carrera_col = c_meta['columna_excel']
        fecha_carrera = c_meta['fecha']
        level = c_meta['championship_level']
        c_lat = c_meta['lat']
        c_lng = c_meta['lng']
        
        # Filtrar atletas que corrieron esta carrera
        df_carrera = df_raw[['DOCUMENTO', 'NOMBRE', 'CLUB', 'GGEE', carrera_col]].copy()
        df_carrera = df_carrera.dropna(subset=[carrera_col])
        df_carrera = df_carrera[df_carrera[carrera_col] > 0]
        
        if df_carrera.empty:
            continue
            
        # Calcular puesto real dinámico en la carrera en base a puntos (de mayor a menor)
        df_carrera = df_carrera.sort_values(by=carrera_col, ascending=False)
        df_carrera['puesto'] = range(1, len(df_carrera) + 1)
        
        for _, row in df_carrera.iterrows():
            dni = str(row['DOCUMENTO']).strip()
            nombre = str(row['NOMBRE']).strip().upper()
            club = str(row['CLUB']).strip().upper() if pd.notna(row['CLUB']) else "SIN CLUB"
            ggee = str(row['GGEE']).strip().upper() if pd.notna(row['GGEE']) else "ABSOLUTO"
            puntos = float(row[carrera_col])
            puesto = int(row['puesto'])
            
            # Generar identificador único seguro (hash de DNI para Azure AutoML respetando RGPD)
            dni_hash = hashlib.sha256(dni.encode('utf-8')).hexdigest()[:16]
            
            # Obtener historial del atleta *antes* de esta carrera
            hist = historial_deportistas.get(dni, [])
            
            # Calcular características acumuladas (Rolling Features) sin fuga de datos (data leakage)
            if len(hist) > 0:
                hist_avg = float(np.mean(hist))
                hist_std = float(np.std(hist)) if len(hist) > 1 else 0.0
                hist_max = float(np.max(hist))
                hist_count = len(hist)
            else:
                # Valores por defecto para su primera carrera
                hist_avg = 0.0
                hist_std = 0.0
                hist_max = 0.0
                hist_count = 0
                
            # Calcular distancia de viaje
            club_lat, club_lng = club_coords.get(club, (0.0, 0.0))
            viaje_km = calculate_haversine(club_lat, club_lng, c_lat, c_lng)
            
            # Extraer mes
            try:
                mes = int(fecha_carrera.split("-")[1])
            except:
                mes = 6
                
            # Añadir registro final estructurado
            registros_finales.append({
                'ATLETA_ID_HASH': dni_hash,
                'CLUB': club,
                'GGEE': ggee,
                'PRUEBA_ID': int(c_meta['id']),
                'CHAMPIONSHIP_LEVEL': level,
                'VIAJE_DISTANCIA_KM': viaje_km,
                'MES_CARRERA': mes,
                'HIST_AVG_PUNTOS': hist_avg,
                'HIST_STD_PUNTOS': hist_std,
                'HIST_MAX_PUNTOS': hist_max,
                'HIST_COUNT_PRUEBAS': hist_count,
                'PUESTO_TARGET': puesto,
                'PUNTOS_TARGET': puntos
            })
            
            # Guardar la puntuación de esta carrera en su historial para las siguientes
            if dni not in historial_deportistas:
                historial_deportistas[dni] = []
            historial_deportistas[dni].append(puntos)
            
    # 6. Guardar el dataset tabular final
    df_final = pd.DataFrame(registros_finales)
    print(f"\nGeneradas {df_final.shape[0]} participaciones individuales enriquecidas.")
    
    # Barajar el dataset aleatoriamente (buena práctica para machine learning)
    df_final = df_final.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    print(f"Exportando dataset a: {OUTPUT_PATH}")
    df_final.to_csv(OUTPUT_PATH, index=False, encoding='utf-8')
    print("¡DATASET GENERADO CON ÉXITO! Listo para entrenar en Azure Machine Learning AutoML.")
    
    # Imprimir un resumen de los datos generados
    print("\nResumen del Dataset para Azure:")
    print(df_final.head(5).to_string())

if __name__ == '__main__':
    run()
