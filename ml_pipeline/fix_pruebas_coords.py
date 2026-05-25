"""
Script para asignar coordenadas reales a las pruebas/campeonatos que tienen lat/lng = 0.
Extrae la ciudad del nombre de la prueba y asigna coordenadas + altitud real via Open-Meteo.
"""
import os, json, time, unicodedata, re
import pandas as pd
import urllib.request

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PRUEBAS = os.path.join(WORKSPACE, 'data', 'processed', 'pruebas_2025.csv')
WEATHER_CACHE = os.path.join(WORKSPACE, 'data', 'raw', 'race_weather_cache.json')

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').upper()

def normalize_key(s):
    return re.sub(r'[^A-Z0-9]+', '', strip_accents(str(s)))

# Mapeo de pruebas por ID o por palabra clave en el nombre -> (lat, lng, ciudad)
PRUEBA_COORDS = {
    # --- Roquetas de Mar (Almería) ---
    'ROQUETAS': (36.7644, -2.6148),
    # --- Gijón (Asturias) ---
    'GIJON': (43.5357, -5.6615),
    # --- Oropesa del Mar (Castellón) - Mediterranean Epic ---
    'OROPESA': (40.0986, 0.1372),
    'MEDITERRANEAN EPIC': (40.0986, 0.1372),
    # --- Banyoles (Girona) ---
    'BANYOLES': (42.1194, 2.7644),
    # --- Torremolinos (Málaga) ---
    'TORREMOLINOS': (36.6222, -4.4994),
    # --- Águilas (Murcia) ---
    'AGUILAS': (37.4062, -1.5839),
    # --- Calahorra (La Rioja) ---
    'CALAHORRA': (42.3050, -1.9653),
    # --- Almazán (Soria) ---
    'ALMAZAN': (41.4858, -2.5317),
    # --- Ceuta ---
    'CEUTA': (35.8894, -5.3198),
    # --- Calella (Barcelona) ---
    'CALELLA': (41.6147, 2.6536),
    # --- Alcúdia (Mallorca) ---
    'ALCUDIA': (39.8531, 3.1208),
    # --- Lanzarote ---
    'LANZAROTE': (28.9638, -13.5477),
    # --- Vitoria-Gasteiz ---
    'VITORIA': (42.8467, -2.6717),
    'GASTEIZ': (42.8467, -2.6717),
    # --- Salou (Tarragona) ---
    'SALOU': (41.0764, 1.1414),
    # --- Xilxes (Castellón) ---
    'XILXES': (39.7558, -0.1958),
    'TRILXILXES': (39.7558, -0.1958),
    # --- Volcano Triathlon = Lanzarote ---
    'VOLCANO': (28.9638, -13.5477),
    # --- La Palma ---
    'LA PALMA': (28.6835, -17.7642),
    # --- Bilbao ---
    'BILBAO': (43.2630, -2.9350),
    # --- Castilla y León (Valladolid capital por defecto) ---
    'DESAFIO CASTILLA Y LEON': (41.6523, -4.7245),
    # --- Madrid ---
    'MADRID': (40.4168, -3.7038),
    # --- Santander ---
    'SANTANDER': (43.4623, -3.8100),
    # --- Albacete ---
    'ALBACETE': (38.9942, -1.8585),
    # --- Zarautz ---
    'ZARAUZKO': (43.2835, -2.1723),
    'ZARAUTZ': (43.2835, -2.1723),
    # --- Catalunya/Banyoles ---
    'CATALUNYA': (42.1194, 2.7644),
    # --- Galicia (Pontevedra capital por defecto para AUT) ---
    'GALICIA': (42.4310, -8.6444),
    # --- Baleares (Palma) ---
    'BALEARES': (39.5696, 2.6502),
    # --- Cantabria (Santander) ---
    'CANTABRIA': (43.4623, -3.8100),
    # --- Andalucía (Sevilla capital) ---
    'ANDALUCIA': (37.3891, -5.9845),
    # --- Aragón (Zaragoza) ---
    'ARAGON': (41.6488, -0.8891),
    # --- Asturias (Oviedo) ---
    'ASTURIAS': (43.3603, -5.8448),
    # --- Comunitat Valenciana ---
    'COMUNITAT VALENCIANA': (39.4699, -0.3763),
    # --- Castilla-La Mancha (Toledo) ---
    'CASTILLA-LA MANCHA': (39.8628, -4.0273),
    'CASTILLA LA MANCHA': (39.8628, -4.0273),
    # --- La Rioja (Logroño) ---
    'LA RIOJA': (42.4627, -2.4450),
    # --- Extremadura (Mérida) ---
    'EXTREMADURA': (38.9161, -6.3436),
    # --- Navarra (Pamplona) ---
    'NAVARRA': (42.8157, -1.6522),
    # --- Murcia ---
    'MURCIA': (37.9922, -1.1307),
    # --- Almería ---
    'ALMERIA': (36.8340, -2.4637),
    # --- Melilla ---
    'MELILLA': (35.2923, -2.9381),
    # --- Valencia ---
    'VALENCIA': (39.4699, -0.3763),
    # --- Castilla y León (Valladolid) ---
    'CASTILLA Y LEON': (41.6523, -4.7245),
    # --- Media Distancia sin ciudad especificada (usar Pontevedra, sede habitual) ---
    'MEDIA DISTANCIA': (42.4310, -8.6444),
    # --- Clasificatorio Olímpico sin ciudad ---
    'CLASIFICATORIO': (40.4168, -3.7038),
    # --- Peñíscola ---
    'PENISCOLA': (40.3606, 0.4083),
}

CITY_COORDS = {
    'IBIZA': (38.9067, 1.4206),
    'TIAS': (28.9639, -13.6495),
    'TINAJO': (29.0617, -13.6756),
    'CALVIA': (39.5650, 2.5030),
    'CAMARGO': (43.4069, -3.8450),
    'CHICLANADELAFRONTERA': (36.4173, -6.1458),
    'CASTRILLON': (43.5358, -5.9744),
    'VALDES': (43.5424, -6.5355),
    'ILLESCAS': (40.1220, -3.8459),
    'MUTILVA': (42.7962, -1.6158),
    'CARTAGENA': (37.6051, -0.9862),
    'AGUILARDECAMPOO': (42.7946, -4.2602),
}

PROVINCE_COORDS = {
    'ILLESBALEARS': (39.5696, 2.6502),
    'BALEARES': (39.5696, 2.6502),
    'LASPALMAS': (28.9638, -13.5477),
    'CANTABRIA': (43.4623, -3.8100),
    'CADIZ': (36.5162, -6.2992),
    'ASTURIAS': (43.3603, -5.8448),
    'TOLEDO': (39.8628, -4.0273),
    'NAVARRA': (42.8157, -1.6522),
    'MURCIA': (37.9922, -1.1307),
    'PALENCIA': (42.0090, -4.5277),
}


def load_city_db_lookup():
    lookup = {}
    db_path = os.path.join(WORKSPACE, 'data', 'raw', 'calendar_cities_db.json')
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for city, coords in data.items():
                if isinstance(coords, list) and len(coords) >= 2:
                    lookup[normalize_key(city)] = (float(coords[0]), float(coords[1]))
        except Exception:
            pass

    return lookup


def load_prueba_city_lookup():
    lookup = {}
    for key, coords in PRUEBA_COORDS.items():
        lookup[normalize_key(key)] = coords
    return lookup


CITY_DB_LOOKUP = load_city_db_lookup()
PRUEBA_CITY_LOOKUP = load_prueba_city_lookup()

def get_elevation(lat, lng):
    """Obtiene la altitud real usando Open-Meteo Elevation API."""
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=5)
        data = json.loads(res.read().decode('utf-8'))
        return data.get('elevation', [0.0])[0]
    except:
        return 0.0

def get_weather(lat, lng, date_str):
    """Obtiene datos meteorológicos reales usando Open-Meteo Archive API."""
    try:
        url = (f"https://archive-api.open-meteo.com/v1/archive?"
               f"latitude={lat}&longitude={lng}"
               f"&start_date={date_str}&end_date={date_str}"
               f"&daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_mean"
               f"&timezone=Europe/Madrid")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=10)
        data = json.loads(res.read().decode('utf-8'))
        daily = data.get('daily', {})
        return {
            'temperatura_max': (daily.get('temperature_2m_max') or [20.0])[0] or 20.0,
            'precipitacion': (daily.get('precipitation_sum') or [0.0])[0] or 0.0,
            'viento_max': (daily.get('wind_speed_10m_max') or [10.0])[0] or 10.0,
            'humedad_media': (daily.get('relative_humidity_2m_mean') or [60.0])[0] or 60.0,
        }
    except Exception as e:
        print(f"    [WARN] No se pudo obtener clima: {e}")
        return None

def resolve_coords(nombre, ciudad, provincia):
    """Resuelve coordenadas por ciudad y, solo como último recurso, por nombre."""
    ciudad_key = normalize_key(ciudad)
    provincia_key = normalize_key(provincia)
    nombre_norm = strip_accents(nombre)

    if ciudad_key in CITY_COORDS:
        return CITY_COORDS[ciudad_key], 'city'

    if ciudad_key in PRUEBA_CITY_LOOKUP:
        return PRUEBA_CITY_LOOKUP[ciudad_key], 'city'

    if ciudad_key in CITY_DB_LOOKUP:
        return CITY_DB_LOOKUP[ciudad_key], 'db'

    if ciudad_key in PROVINCE_COORDS:
        return PROVINCE_COORDS[ciudad_key], 'province'

    if provincia_key in PROVINCE_COORDS:
        return PROVINCE_COORDS[provincia_key], 'province'

    sorted_keys = sorted(PRUEBA_COORDS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        key_norm = strip_accents(key)
        if key_norm in nombre_norm:
            return PRUEBA_COORDS[key], 'name'

    return None, None

def main():
    print("=" * 70)
    print("  CORRECCIÓN DE COORDENADAS DE PRUEBAS/CAMPEONATOS")
    print("=" * 70)

    df = pd.read_csv(CSV_PRUEBAS, encoding='utf-8')
    zeros = df[(df['lat'] == 0) & (df['lng'] == 0)]
    print(f"Pruebas con lat/lng = 0: {len(zeros)} de {len(df)}")

    # Cargar caché de clima
    weather_cache = {}
    if os.path.exists(WEATHER_CACHE):
        with open(WEATHER_CACHE, 'r', encoding='utf-8') as f:
            weather_cache = json.load(f)

    fixed = 0
    weather_updated = 0

    for idx, row in df.iterrows():
        nombre = str(row['nombre'])
        ciudad = str(row.get('ciudad', ''))
        provincia = str(row.get('provincia', ''))
        coords, source = resolve_coords(nombre, ciudad, provincia)

        if coords:
            lat, lng = coords
            current_lat = float(row.get('lat', 0) or 0)
            current_lng = float(row.get('lng', 0) or 0)
            coords_changed = abs(current_lat - lat) > 1e-9 or abs(current_lng - lng) > 1e-9

            if coords_changed:
                df.at[idx, 'lat'] = lat
                df.at[idx, 'lng'] = lng

            if coords_changed or float(row.get('altitud', 0) or 0) == 0:
                alt = get_elevation(lat, lng)
                df.at[idx, 'altitud'] = alt
                time.sleep(0.3)

                fecha = str(row.get('fecha', ''))
                if fecha and fecha != 'nan':
                    cache_key = f"{lat},{lng},{fecha}"
                    if cache_key not in weather_cache or weather_cache[cache_key].get('temperatura_max') == 20.0:
                        weather = get_weather(lat, lng, fecha)
                        if weather:
                            df.at[idx, 'temperatura_max'] = weather['temperatura_max']
                            df.at[idx, 'precipitacion'] = weather['precipitacion']
                            df.at[idx, 'viento_max'] = weather['viento_max']
                            df.at[idx, 'humedad_media'] = weather['humedad_media']
                            weather_cache[cache_key] = {
                                'altitud': alt,
                                'temperatura_max': weather['temperatura_max'],
                                'humedad_media': weather['humedad_media'],
                                'precipitacion': weather['precipitacion'],
                                'viento_max': weather['viento_max'],
                            }
                            weather_updated += 1
                        time.sleep(0.3)

            if coords_changed:
                fixed += 1

            print(f"  [OK:{source:<7}] {nombre[:55]:<55} -> ({lat:.4f}, {lng:.4f})")
        else:
            print(f"  [??] {nombre[:55]:<55} -> Sin match")

    df.to_csv(CSV_PRUEBAS, index=False, encoding='utf-8')

    with open(WEATHER_CACHE, 'w', encoding='utf-8') as f:
        json.dump(weather_cache, f, ensure_ascii=False, indent=2)

    remaining = len(df[(df['lat'] == 0) & (df['lng'] == 0)])
    print(f"\nPruebas corregidas: {fixed}")
    print(f"Clima actualizado: {weather_updated}")
    print(f"Aún sin coordenadas: {remaining}")
    print("=" * 70)

if __name__ == '__main__':
    main()
