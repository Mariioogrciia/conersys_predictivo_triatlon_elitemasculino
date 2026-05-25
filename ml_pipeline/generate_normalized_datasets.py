import os
import json
import re
import time
import urllib.request
import pandas as pd
import numpy as np
import hashlib

# Configuración de rutas
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

def fetch_weather_and_altitude(lat, lng, fecha):
    # Valores por defecto en caso de fallo o nulos
    altitud = 0.0
    temp = 20.0
    humedad = 60.0
    precip = 0.0
    viento = 10.0
    
    if lat == 0.0 or lng == 0.0 or fecha == '2025-12-31':
        return altitud, temp, humedad, precip, viento
        
    # Consultar Altitud (Open-Meteo Elevation API)
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            elevations = data.get('elevation', [])
            if elevations:
                altitud = float(elevations[0])
    except Exception as e:
        print(f"   [Elevation API] Fallo al obtener altitud ({lat}, {lng}): {e}")
        
    # Consultar Clima Histórico (Open-Meteo Archive API)
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lng}&start_date={fecha}&end_date={fecha}&daily=temperature_2m_max,relative_humidity_2m_mean,precipitation_sum,wind_speed_10m_max&timezone=Europe/Madrid"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            daily = data.get('daily', {})
            
            temp_list = daily.get('temperature_2m_max', [])
            if temp_list and temp_list[0] is not None:
                temp = float(temp_list[0])
                
            hum_list = daily.get('relative_humidity_2m_mean', [])
            if hum_list and hum_list[0] is not None:
                humedad = float(hum_list[0])
                
            precip_list = daily.get('precipitation_sum', [])
            if precip_list and precip_list[0] is not None:
                precip = float(precip_list[0])
                
            wind_list = daily.get('wind_speed_10m_max', [])
            if wind_list and wind_list[0] is not None:
                viento = float(wind_list[0])
    except Exception as e:
        print(f"   [Weather API] Fallo al obtener clima para ({lat}, {lng}) en {fecha}: {e}")
        
    return altitud, temp, humedad, precip, viento

def run_normalization():
    print("Iniciando la generación de Datasets Normalizados (Snowflake Schema)...")
    import urllib.request # Importación diferida local segura
    
    # ==========================================
    # 1. GENERAR DATASET DE PRUEBAS (CAMPEONATOS + CLIMA + ALTITUD)
    # ==========================================
    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encontró {JSON_PATH}")
        return
        
    print("Procesando Campeonatos desde JSON...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        championships_data = json.load(f)
        
    # Cargar caché del clima para evitar llamadas repetidas redundantes
    weather_cache = {}
    weather_cache_path = os.path.join(WORKSPACE, "data", "raw", "race_weather_cache.json")
    if os.path.exists(weather_cache_path):
        try:
            with open(weather_cache_path, 'r', encoding='utf-8') as f:
                weather_cache = json.load(f)
            print(f"Cargado caché de clima: {len(weather_cache)} registros climáticos.")
        except Exception as e:
            print(f"Aviso al cargar caché de clima: {e}")
            
    pruebas_list = []
    pruebas_json_lookup = [] # Para token-matching posterior
    cache_dirty = False
    
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
            
            # Resolver clima y altitud
            cache_key = f"{lat},{lng},{fecha}"
            if cache_key in weather_cache:
                entry = weather_cache[cache_key]
                altitud = entry.get('altitud', 0.0)
                temp_max = entry.get('temperatura_max', 20.0)
                hum_mean = entry.get('humedad_media', 60.0)
                precip = entry.get('precipitacion', 0.0)
                wind_max = entry.get('viento_max', 10.0)
            else:
                print(f"   [Weather Query] Buscando clima y altitud para '{name[:40]}' ({fecha})...")
                altitud, temp_max, hum_mean, precip, wind_max = fetch_weather_and_altitude(lat, lng, fecha)
                weather_cache[cache_key] = {
                    'altitud': altitud,
                    'temperatura_max': temp_max,
                    'humedad_media': hum_mean,
                    'precipitacion': precip,
                    'viento_max': wind_max
                }
                cache_dirty = True
                time.sleep(0.5) # Pausa amigable para evitar saturación de la API de Open-Meteo
            
            pruebas_list.append({
                'id': p_id,
                'season': season,
                'nombre': name,
                'championship_level': level,
                'fecha': fecha,
                'ciudad': ciudad,
                'provincia': provincia,
                'lat': lat,
                'lng': lng,
                'altitud': altitud,
                'temperatura_max': temp_max,
                'humedad_media': hum_mean,
                'precipitacion': precip,
                'viento_max': wind_max
            })
            
            pruebas_json_lookup.append({
                'id': p_id,
                'name': name,
                'fecha': fecha,
                'championship_level': level,
                'lat': lat,
                'lng': lng,
                'provincia': provincia,
                'tokens': get_tokens(name)
            })
            
    # Guardar caché si ha cambiado
    if cache_dirty:
        with open(weather_cache_path, 'w', encoding='utf-8') as f:
            json.dump(weather_cache, f, ensure_ascii=False, indent=2)
        print("Caché de clima histórico guardado con éxito.")
        
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
    
    # FILTRO ELITE MASCULINA: Quedarnos solo con ABSOLUTO y SUB-23
    print("Filtrando para mantener exclusivamente Elite Masculina (ABSOLUTO y SUB-23)...")
    df_raw = df_raw[df_raw['GGEE'].isin(['ABSOLUTO', 'SUB-23'])].copy()
    
    # Mantener el registro más completo de cada deportista (por documento)
    df_deportistas = df_raw[['DOCUMENTO', 'NOMBRE', 'CLUB', 'GGEE']].drop_duplicates(subset=['DOCUMENTO'])
    df_deportistas.to_csv(OUT_DEPORTISTAS, index=False, encoding='utf-8')
    print(f"-> Exportado Dataset de Deportistas (Elite): {df_deportistas.shape[0]} registros en {OUT_DEPORTISTAS}")

    # ==========================================
    # 2b. Clubes y Geocodificación desde Caché de Nominatim
    # ==========================================
    print("Procesando Clubes y Coordenadas desde Caché de Nominatim...")
    
    cache = {}
    cache_path = os.path.join(WORKSPACE, "data", "raw", "club_geocache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"Cargado caché de geocodificación: {len(cache)} clubes registrados.")
        except Exception as e:
            print(f"Aviso: No se pudo cargar club_geocache.json ({e}). Se inicializará vacío.")
    else:
        print("Aviso: No se encontró club_geocache.json. Por favor, ejecuta geocode_clubs.py para poblarlo.")

    unique_clubs = df_raw['CLUB'].dropna().unique()
    clubes_geo_list = []
    
    for c in unique_clubs:
        c_clean = str(c).strip().upper()
        
        # Buscar en la caché geocodificada de OSM
        if c_clean in cache:
            entry = cache[c_clean]
            ciudad_sede = entry.get('ciudad', 'DESCONOCIDA')
            provincia = entry.get('provincia', 'DESCONOCIDA')
            lat = entry.get('lat', 40.4168)
            lng = entry.get('lng', -3.7038)
        else:
            ciudad_sede = 'DESCONOCIDA'
            provincia = 'DESCONOCIDA'
            lat = 40.4168
            lng = -3.7038
            
        clubes_geo_list.append({
            'club': c_clean,
            'ciudad_sede': ciudad_sede,
            'provincia': provincia,
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
