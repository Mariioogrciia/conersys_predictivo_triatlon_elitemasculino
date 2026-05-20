import os, json, time, re
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

WORKSPACE  = 'c:\\Users\\mario\\Downloads\\Re_ Reunión TFM Conersys '
CSV_CLUBES = os.path.join(WORKSPACE, 'data', 'processed', 'clubes_geo_2025.csv')
CACHE_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'club_geocache.json')

# Correcciones manuales: clave = nombre exacto del club en MAYUSCULAS
# Añadir aqui cualquier club cuyo nombre engane al geocoder automatico
CORRECCIONES = {
    'CLUB DE TRIATLON DIABLILLOS DE RIVAS': ('RIVAS-VACIAMADRID', 40.3543, -3.5308),
    'CLUB DE TRIATLÓN DIABLILLOS DE RIVAS': ('RIVAS-VACIAMADRID', 40.3543, -3.5308),
    'C.T. DIABLILLOS DE RIVAS':             ('RIVAS-VACIAMADRID', 40.3543, -3.5308),
    'DIABLILLOS DE RIVAS TRIATLON':         ('RIVAS-VACIAMADRID', 40.3543, -3.5308),
}

PREFIJOS = [
    (r'^CLUB' + r'\s+(?:DE\s+)?TRIATL[OÓ]N\s+'),
    (r'^CLUB' + r'\s+(?:DE\s+)?TRIATH?LON\s+'),
    (r'^CLUB' + r'\s+DEPORTIVO\s+'),
    (r'^CLUB' + r'\s+'),
    (r'^C\.T\.\s+'),
    (r'^C\.E\.\s+'),
    (r'^C\.D\.\s+'),
    (r'^TRIATL[OÓ]N\s+'),
    (r'^TRIATH?LON\s+'),
    (r'^CIDADE\s+DE\s+'),
]
SUFIJOS = [
    (r'\s+TRIATL[OÓ]N$'),
    (r'\s+TRIATH?LON$'),
    (r'\s+KIROL\s+ELKARTEA$'),
    (r'\s+KIROL\s+TALDEA$'),
    (r'\s+KLUBA$'),
    (r'\s+FLUVIAL$'),
    (r'\s+TRIATLOI\s+KLUBA$'),
]

def limpiar(nombre_club):
    n = nombre_club.strip()
    for p in PREFIJOS:
        n = re.sub(p, '', n, flags=re.IGNORECASE).strip()
    for s in SUFIJOS:
        n = re.sub(s, '', n, flags=re.IGNORECASE).strip()
    principal = n.split('-')[0].strip()
    qs, seen = [], set()
    for q in ([n + ', Espana'] if n != nombre_club else []) + ([principal + ', Espana'] if principal and principal != n else []) + [nombre_club + ', Espana']:
        if q not in seen:
            seen.add(q)
            qs.append(q)
    return qs

def municipio(raw):
    for campo in ['city', 'town', 'village', 'municipality', 'county', 'state_district']:
        if campo in raw:
            return raw[campo].upper()
    return 'DESCONOCIDA'

def main():
    print('=' * 70)
    print('  GEOCODIFICACION REAL DE CLUBES - Nominatim (OpenStreetMap)')
    print('  Sin coste, sin clave API')
    print('=' * 70)
    if not os.path.exists(CSV_CLUBES):
        print(f'[ERROR] No se encontro: {CSV_CLUBES}'); return
    df = pd.read_csv(CSV_CLUBES)
    print(f'Cargados {len(df)} clubes')
    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    print(f'Cache: {len(cache)} entradas previas')
    geo = Nominatim(user_agent='tfm_triatlon_fetri_2025', timeout=10)
    lats, lngs, cities = [], [], []
    nuevos = manuales = de_cache = errores = 0
    for idx, row in df.iterrows():
        club = str(row['club']).strip().upper()
        done = False
        for k, (ciudad, lat, lng) in CORRECCIONES.items():
            if k.upper() in club or club == k.upper():
                lats.append(lat); lngs.append(lng); cities.append(ciudad)
                manuales += 1; done = True
                print(f'[MANUAL] {club[:55]:<55} -> {ciudad}')
                break
        if done: continue
        if club in cache:
            e = cache[club]
            lats.append(e['lat']); lngs.append(e['lng']); cities.append(e['ciudad'])
            de_cache += 1; continue
        ok = False
        for q in limpiar(club):
            try:
                time.sleep(1.1)
                loc = geo.geocode(q, addressdetails=True, language='es', country_codes='es')
                if loc:
                    m = municipio(loc.raw.get('address', {}))
                    la, lo = loc.latitude, loc.longitude
                    cache[club] = {'lat': la, 'lng': lo, 'ciudad': m}
                    lats.append(la); lngs.append(lo); cities.append(m)
                    nuevos += 1; ok = True
                    print(f'[OK]   {club[:55]:<55} -> {m} ({la:.4f}, {lo:.4f})')
                    break
            except (GeocoderTimedOut, GeocoderUnavailable): time.sleep(3)
            except Exception as e: print(f'[ERR] {club[:40]}: {e}'); break
        if not ok:
            cache[club] = {'lat': row['lat'], 'lng': row['lng'], 'ciudad': str(row['ciudad_sede'])}
            lats.append(row['lat']); lngs.append(row['lng']); cities.append(str(row['ciudad_sede']))
            errores += 1
            print(f'[FAIL] {club[:55]:<55} -> sin resultado, manteniendo anterior')
        if (idx + 1) % 25 == 0:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f'  >> Cache guardada ({idx + 1}/{len(df)} procesados)')
    df['lat'] = lats; df['lng'] = lngs; df['ciudad_sede'] = cities
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    df.to_csv(CSV_CLUBES, index=False, encoding='utf-8')
    reales = len(df[(df['lat'] != 40.4168) | (df['lng'] != -3.7038)])
    print('\n' + '=' * 70)
    print('  RESULTADO FINAL')
    print('=' * 70)
    print(f'  Total clubes            : {len(df)}')
    print(f'  Corregidos manualmente  : {manuales}')
    print(f'  Geocodificados Nominatim: {nuevos}')
    print(f'  Desde cache             : {de_cache}')
    print(f'  Sin resultado (fallback): {errores}')
    print(f'  Coords reales resueltas : {reales}')
    print(f'  Aun con fallback Madrid : {len(df) - reales}')
    print(f'  CSV: {CSV_CLUBES}')
    print('=' * 70)

if __name__ == '__main__': main()
