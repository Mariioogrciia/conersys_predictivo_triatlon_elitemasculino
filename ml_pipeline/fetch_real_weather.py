import os
import json
import requests
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELITE_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'elite_masculina_triatlon')
OUTPUT_JSON = os.path.join(BASE_DIR, 'data', 'raw', 'clima_carreras.json')

# Copy of geo lookup from build_dataset.py
GEO_DATA = {
    "Águilas":              (37.4049, -1.5832),
    "Roquetas de Mar":      (36.7643, -2.6147),
    "Albacete":             (38.9942, -1.8585),
    "Ciudad Real":          (38.9848, -3.9274),
    "Centro Niemeyer":      (43.5573, -5.9247),  # Avilés
    "Avilés":               (43.5573, -5.9247),
    "La Nucía":             (38.6189, -0.1261),
    "Soria":                (41.7636, -2.4649),
    "Cáceres":              (39.4753, -6.3724),
    "Banyoles":             (42.1189, 2.7644),
    "Pamplona":             (42.8125, -1.6458),
    "Alcobendas":           (40.5334, -3.6421),
    "Oropesa del Mar/Orpesa": (40.0967, 0.1358),
    "Oropesa":              (40.0967, 0.1358),
    "Almazán":              (41.4862, -2.5327),
    "Madrid":               (40.4168, -3.7038),
    "Calahorra":            (42.3050, -1.9653),
    "Peníscola/Peñíscola":  (40.3577, 0.4076),
    "Peñíscola":            (40.3577, 0.4076),
    "Cartagena - Murcia":   (37.6257, -0.9966),
    "Cartagena":            (37.6257, -0.9966),
    "Vitoria-Gasteiz":      (42.8467, -2.6716),
    "Pontevedra":           (42.4311, -8.6443),
    "Coruña, A":            (43.3623, -8.4115),
    "A Coruña":             (43.3623, -8.4115),
    "Mérida":               (38.9160, -6.3435),
    "Punta Umbría":         (37.1768, -6.9595),
    "Narón":                (43.5233, -8.1541),
    "Tarazona":             (41.9047, -1.7260),
    "Fuente Álamo":         (37.7147, -1.1713),
    "Fuente Álamo de Murcia": (37.7147, -1.1713),
    "Calasparra":           (38.2294, -1.6978),
    "Berlanga de Duero":    (41.4583, -2.8583),
    "Platja d'Aro":         (41.8172, 3.0672),
    "Ansó":                 (42.7578, -0.8289),
    "Reinosa":              (43.0017, -4.1375),
    "Orihuela":             (38.0849, -0.9441),
    "Playas de Orihuela":   (37.9413, -0.7528),
    "Sevilla":              (37.3886, -5.9823),
    "Ibiza":                (38.9067, 1.4206),
    "Mallorca":             (39.6953, 3.0176),
    "Peguera":              (39.5386, 2.4353),
    "Valencia":             (39.4699, -0.3763),
    "Salou":                (41.0764, 1.1416),
    "Xilxes":               (39.7611, -0.2122),
    "TriXilxes":            (39.7611, -0.2122),
    "Catalunya":            (41.5912, 1.5209),
    "Valladolid":           (41.6520, -4.7286),
    "Huesca":               (42.1362, -0.4087),
    "Huelva":               (37.2614, -6.9447),
    "Girona":               (41.9794, 2.8214),
    "Navarra":              (42.8125, -1.6458),
    "Santa Eulària des Riu":(38.9833, 1.5333),
    "Jerez de los Caballeros":(38.3214, -6.7722),
    "Alcudia":              (39.8530, 3.1194),
    "Zaragoza":             (41.6488, -0.8891),
    "Illes Balears":        (39.5700, 2.6502),
    "Aguilar de Campoo":    (42.7944, -4.2567),
}

def get_geo_coords(city):
    if not city:
        return None, None
    if city in GEO_DATA:
        return GEO_DATA[city]
    city_lower = city.lower()
    for key, data in GEO_DATA.items():
        if key.lower() in city_lower or city_lower in key.lower():
            return data
    for keyword in GEO_DATA.keys():
        if keyword.lower() in city_lower:
            return GEO_DATA[keyword]
    return None, None

def parse_date_sort(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return None

# 1. Identify all unique races
print("Extracting unique races...")
unique_races = {}

json_files = [f for f in os.listdir(ELITE_DIR) if f.endswith('.json')]
for filename in json_files:
    filepath = os.path.join(ELITE_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        continue
    
    for result in data.get('results', []):
        race_id = result.get('ChId')
        city = result.get('ChdCity', '')
        date_str = parse_date_sort(result.get('ChdDateSort'))
        if race_id and city and date_str:
            lat, lng = get_geo_coords(city)
            if lat and lng:
                unique_races[race_id] = {
                    'city': city,
                    'date': date_str,
                    'lat': lat,
                    'lng': lng
                }

print(f"Found {len(unique_races)} unique races with geo coordinates.")

# 2. Fetch weather for each
weather_cache = {}

print("Fetching historical weather from Open-Meteo...")
for race_id, info in unique_races.items():
    date = info['date']
    lat = info['lat']
    lng = info['lng']
    
    # Avoid future dates (if any are wrongly marked 2026 and it's before that date)
    # Open-Meteo archive only works for past up to ~5 days ago.
    # We'll just try and if it fails or returns None, it stays empty.
    
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lng}&start_date={date}&end_date={date}&daily=temperature_2m_mean,relative_humidity_2m_mean&timezone=Europe%2FMadrid"
    
    try:
        r = requests.get(url)
        if r.status_code == 200:
            res = r.json()
            daily = res.get('daily', {})
            temps = daily.get('temperature_2m_mean', [])
            hums = daily.get('relative_humidity_2m_mean', [])
            
            t = temps[0] if temps and temps[0] is not None else ''
            h = hums[0] if hums and hums[0] is not None else ''
            
            weather_cache[race_id] = {
                'temperature': t,
                'humidity': h
            }
            print(f"  {info['city']:25s} | {date} | T: {t}C | Hum: {h}%")
        else:
            print(f"  API Error for {info['city']} on {date}: {r.status_code}")
    except Exception as e:
        print(f"  Exception for {info['city']} on {date}: {e}")
        
    time.sleep(0.5) # Be nice to the API

# 3. Save cache
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(weather_cache, f, indent=2)

print(f"Saved {len(weather_cache)} weather records to {OUTPUT_JSON}")
