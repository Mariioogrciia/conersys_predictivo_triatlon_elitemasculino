import os, json, time, re
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Detección dinámica de WORKSPACE (portabilidad absoluta)
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CLUBES = os.path.join(WORKSPACE, 'data', 'processed', 'clubes_geo_2025.csv')
CACHE_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'club_geocache.json')

# Correcciones manuales: clave = nombre exacto del club en MAYUSCULAS
# Mapea a: (ciudad_sede, provincia, lat, lng)
CORRECCIONES = {
    'CLUB DE TRIATLON DIABLILLOS DE RIVAS': ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'CLUB DE TRIATLÓN DIABLILLOS DE RIVAS': ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'C.T. DIABLILLOS DE RIVAS':             ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'DIABLILLOS DE RIVAS TRIATLON':         ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
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

# Diccionario inteligente de traducción de palabras clave de sponsors/marcas a municipios reales
# Esto ayuda a Nominatim a geolocalizar la consulta exacta en OSM y extraer la provincia estructurada real
KEYWORDS_MUNICIPIOS = {
    'ALUSIGMA': 'PORTUGALETE',
    'PEÑOTA': 'PORTUGALETE',
    'PENOTA': 'PORTUGALETE',
    'SALTOKI': 'PAMPLONA',
    'DELIKIA': 'GANDIA',
    'BARROSA': 'CHICLANA DE LA FRONTERA',
    'AMANDARRI': 'GERNIKA-LUMO',
    'TRANSNATUR': 'ZARAGOZA',
    'GALOSPORT': 'ALMERIA',
    'TRIPUÇOL': 'PUÇOL',
    'TRIPUCOL': 'PUÇOL',
    'BABYSCHOOL': 'JAEN',
    'ANTXINTXIKA': 'BERGARA',
    'REALES': 'LOS REALEJOS',
    'RESISTENTIA': 'ADEJE',
    'LACERTA': 'SEGOVIA',
    'TRAGAMILLAS': 'ALCAÑIZ',
    'BULL': 'SANTANDER',
    'SIPCAM': 'ARCHENA',
    'CHAMO DIAZ': 'CACERES',
    'ROLLERBIKE': 'SORIA',
    'ANTHUS': 'HUELVA',
    'HIRU HERRI': 'BURLADA',
    'OZONO': 'SANTA CRUZ DE TENERIFE',
    'YEPA': 'SAN SEBASTIAN',
    'GUADIATO': 'PEÑARROYA-PUEBLONUEVO',
    'ALOHA': 'MARBELLA',
    'ZARAUZKO': 'ZARAUTZ',
    'BIOSNAR': 'HONDARRIBIA',
    'VIBIKE': 'VITORIA-GASTEIZ',
    'AZKOITRI': 'AZKOITIA',
    'SULAYR': 'GRANADA',
    'ISBILYA': 'SEVILLA',
    'VICALVARO': 'MADRID',
    'BOADILLA': 'BOADILLA DEL MONTE',
    'TRIKUA': 'SAN SEBASTIAN',
    'CASTRILLON': 'CASTRILLON',
    'SQUALI': 'MADRID',
    'CARABANCHEL': 'MADRID',
    'ROZAS': 'LAS ROZAS DE MADRID',
    'COMPLUTUM': 'ALCALA DE HENARES',
    'A CORRE-CUITA': 'VALENCIA',
    'CORRE CUITA': 'VALENCIA',
    'CORRE-CUITA': 'VALENCIA',
    'RIVEIRA': 'RIBEIRA',
    'HERCULES': 'A CORUÑA',
    'ELCHE': 'ELCHE',
}

# Mapeo heurístico offline de palabras clave de clubes a su municipio, provincia, latitud y longitud.
# Esto asegura una resolución geográfica perfecta de alta fidelidad si Nominatim está caído, bloqueado o rate-limited.
HEURISTIC_MAPPING = {
    'ALBACETE': ('ALBACETE', 'ALBACETE', 38.9942, -1.8585),
    'RIVAS': ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'DIABLILLOS': ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'DELIKIA': ('GANDIA', 'VALENCIA', 38.9681, -0.1803),
    'BETERA': ('BÉTERA', 'VALENCIA', 39.5921, -0.4578),
    'BÉTERA': ('BÉTERA', 'VALENCIA', 39.5921, -0.4578),
    'SORIANO': ('SORIA', 'SORIA', 41.764, -2.4688),
    'SORIA': ('SORIA', 'SORIA', 41.764, -2.4688),
    'RIOJA': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'FERROL': ('FERROL', 'A CORUÑA', 43.4834, -8.2333),
    'TOLEDO': ('TOLEDO', 'TOLEDO', 39.8628, -4.0273),
    'REALES': ('LOS REALEJOS', 'SANTA CRUZ DE TENERIFE', 28.3503, -16.585),
    'OVIEDO': ('OVIEDO', 'ASTURIAS', 43.3603, -5.8448),
    'CORDOBA': ('CÓRDOBA', 'CÓRDOBA', 37.8882, -4.7794),
    'CÓRDOBA': ('CÓRDOBA', 'CÓRDOBA', 37.8882, -4.7794),
    'CASABLANCA': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'GALOSPORT': ('ALMERÍA', 'ALMERÍA', 36.834, -2.4637),
    'ALMERIA': ('ALMERÍA', 'ALMERÍA', 36.834, -2.4637),
    'ALMERÍA': ('ALMERÍA', 'ALMERÍA', 36.834, -2.4637),
    'RESISTENTIA': ('ADEJE', 'SANTA CRUZ DE TENERIFE', 28.1227, -16.7297),
    'ORIHUELA': ('ORIHUELA', 'ALICANTE', 38.0848, -0.944),
    'BALEARS': ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502),
    'BALEARES': ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502),
    'ALGEMESI': ('ALGEMESÍ', 'VALENCIA', 39.1891, -0.4366),
    'ALGEMESÍ': ('ALGEMESÍ', 'VALENCIA', 39.1891, -0.4366),
    'NARON': ('NARÓN', 'A CORUÑA', 43.5014, -8.1925),
    'NARÓN': ('NARÓN', 'A CORUÑA', 43.5014, -8.1925),
    'PALMAS': ('LAS PALMAS DE GRAN CANARIA', 'LAS PALMAS', 28.1235, -15.4363),
    'MELILLA': ('MELILLA', 'MELILLA', 35.2923, -2.9381),
    'BARCELONA': ('BARCELONA', 'BARCELONA', 41.3851, 2.1734),
    'ALCOBENDAS': ('ALCOBENDAS', 'MADRID', 40.5475, -3.6421),
    'SEVILLA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'MOSTOLES': ('MÓSTOLES', 'MADRID', 40.3232, -3.8676),
    'MÓSTOLES': ('MÓSTOLES', 'MADRID', 40.3232, -3.8676),
    'SANTANDER': ('SANTANDER', 'CANTABRIA', 43.4623, -3.81),
    'ALCAÑIZ': ('ALCAÑIZ', 'TERUEL', 41.05, -0.13),
    'ELCHE': ('ELCHE', 'ALICANTE', 38.2669, -0.6988),
    'SAN SEBASTIAN': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'DONOSTIA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'VICALVARO': ('MADRID', 'MADRID', 40.4018, -3.5951),
    'LORCA': ('LORCA', 'MURCIA', 37.6715, -1.7017),
    'LACERTA': ('SEGOVIA', 'SEGOVIA', 40.9429, -4.1088),
    'BOADILLA': ('BOADILLA DEL MONTE', 'MADRID', 40.4069, -3.8761),
    'MURCIA': ('MURCIA', 'MURCIA', 37.9922, -1.1307),
    'ZARAGOZA': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'PUÇOL': ('PUÇOL', 'VALENCIA', 39.6172, -0.3028),
    'PUZOL': ('PUÇOL', 'VALENCIA', 39.6172, -0.3028),
    'JAEN': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'JAÉN': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'VERGARA': ('BERGARA', 'GIPUZKOA', 43.1175, -2.4172),
    'BERGARA': ('BERGARA', 'GIPUZKOA', 43.1175, -2.4172),
    'SALMANTINA': ('SALAMANCA', 'SALAMANCA', 40.9701, -5.6635),
    'SALAMANCA': ('SALAMANCA', 'SALAMANCA', 40.9701, -5.6635),
    'CACERES': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'CÁCERES': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'AGUILAS': ('ÁGUILAS', 'MURCIA', 37.4062, -1.5839),
    'ÁGUILAS': ('ÁGUILAS', 'MURCIA', 37.4062, -1.5839),
    'CASTRILLON': ('CASTRILLÓN', 'ASTURIAS', 43.5358, -5.9744),
    'CASTRILLÓN': ('CASTRILLÓN', 'ASTURIAS', 43.5358, -5.9744),
    'YECLA': ('YECLA', 'MURCIA', 38.6144, -1.1158),
    'LAS ROZAS': ('LAS ROZAS DE MADRID', 'MADRID', 40.4943, -3.8679),
    'ROZAS': ('LAS ROZAS DE MADRID', 'MADRID', 40.4943, -3.8679),
    'ALCALA': ('ALCALÁ DE HENARES', 'MADRID', 40.482, -3.364),
    'ALCALÁ': ('ALCALÁ DE HENARES', 'MADRID', 40.482, -3.364),
    'PLASENCIA': ('PLASENCIA', 'CÁCERES', 40.03, -6.09),
    'TORRELAVEGA': ('TORRELAVEGA', 'CANTABRIA', 43.3487, -4.0515),
    'TINAJO': ('TINAJO', 'LAS PALMAS', 29.0617, -13.6756),
    'LUGONES': ('SIERO', 'ASTURIAS', 43.4044, -5.8121),
    'CASTELLON': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'CASTELLÓN': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'MALAGA': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'MÁLAGA': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'VALLADOLID': ('VALLADOLID', 'VALLADOLID', 41.6523, -4.7245),
    'GRANADA': ('GRANADA', 'GRANADA', 37.1773, -3.5986),
    'CADIZ': ('CÁDIZ', 'CÁDIZ', 36.5271, -6.2923),
    'CÁDIZ': ('CÁDIZ', 'CÁDIZ', 36.5271, -6.2923),
    'EJIDO': ('EL EJIDO', 'ALMERÍA', 36.7761, -2.8142),
    'VILAGARCIA': ('VILAGARCÍA DE AROUSA', 'PONTEVEDRA', 42.5948, -8.7669),
    'ALCANTARILLA': ('ALCANTARILLA', 'MURCIA', 37.97, -1.21),
    'ARANGUREN': ('ARANGUREN', 'NAVARRA', 42.7753, -1.5755),
    'GALDAKAO': ('GALDAKAO', 'BIZKAIA', 43.2307, -2.8449),
    'GUADIATO': ('PEÑARROYA-PUEBLONUEVO', 'CÓRDOBA', 38.3026, -5.2715),
    'MARBELLA': ('MARBELLA', 'MÁLAGA', 36.5075, -4.8858),
    'ZARAUZ': ('ZARAUTZ', 'GIPUZKOA', 43.2835, -2.1723),
    'ZARAUTZ': ('ZARAUTZ', 'GIPUZKOA', 43.2835, -2.1723),
    'PORTUGALETE': ('PORTUGALETE', 'BIZKAIA', 43.3189, -3.0199),
    'PAMPLONA': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'GANDIA': ('GANDIA', 'VALENCIA', 38.9681, -0.1803),
    'BURLADA': ('BURLADA', 'NAVARRA', 42.823, -1.6141),
    'VITORIA': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'GASTEIZ': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'HONDARRIBIA': ('HONDARRIBIA', 'GIPUZKOA', 43.3625, -1.7915),
    'AZKOITIA': ('AZKOITIA', 'GIPUZKOA', 43.18, -2.3167),
    'BOUZAS': ('VIGO', 'PONTEVEDRA', 42.2223, -8.7567),
    'VIGO': ('VIGO', 'PONTEVEDRA', 42.2223, -8.7567),
    'PONTEVEDRA': ('PONTEVEDRA', 'PONTEVEDRA', 42.431, -8.6444),
    'SANTIAGO': ('SANTIAGO DE COMPOSTELA', 'A CORUÑA', 42.8782, -8.5448),
    'COMPOSTELA': ('SANTIAGO DE COMPOSTELA', 'A CORUÑA', 42.8782, -8.5448),
    'LUGO': ('LUGO', 'LUGO', 43.0125, -7.5558),
    'OURENSE': ('OURENSE', 'OURENSE', 42.3358, -7.8639),
    'GIJON': ('GIJÓN', 'ASTURIAS', 43.5357, -5.6615),
    'GIJÓN': ('GIJÓN', 'ASTURIAS', 43.5357, -5.6615),
    'AVILÉS': ('AVILÉS', 'ASTURIAS', 43.5558, -5.9248),
    'AVILES': ('AVILÉS', 'ASTURIAS', 43.5558, -5.9248),
    'SANTURTZI': ('SANTURTZI', 'BIZKAIA', 43.3283, -3.0315),
    'SESTAO': ('SESTAO', 'BIZKAIA', 43.3081, -3.0089),
    'BILBAO': ('BILBAO', 'BIZKAIA', 43.263, -2.935),
    'GETXO': ('GETXO', 'BIZKAIA', 43.3484, -3.0119),
    'SAN SEBASTIÁN DE LOS REYES': ('SAN SEBASTIÁN DE LOS REYES', 'MADRID', 40.5473, -3.6264),
    'CEUTA': ('CEUTA', 'CEUTA', 35.8894, -5.3198),
    'AMANDARRI': ('GUERNICA Y LUNO', 'BIZKAIA', 43.3144, -2.6779),
}

def normalizar_provincia(prov):
    if not prov:
        return 'DESCONOCIDA'
    prov = prov.strip().upper()
    
    # Mapeo de sinónimos comunes, comarcas y traducciones autonómicas a las 52 provincias oficiales de España
    mapping = {
        'ARABA': 'ÁLAVA', 'ALAVA': 'ÁLAVA', 'ÁLAVA': 'ÁLAVA',
        'ALACANT': 'ALICANTE', 'ALICANTE': 'ALICANTE', 'LA VEGA BAJA': 'ALICANTE',
        'ILLES BALEARS': 'BALEARES', 'BALEARS': 'BALEARES', 'BALEARIC ISLANDS': 'BALEARES', 'ISLAS BALEARES': 'BALEARES', 'EIVISSA': 'BALEARES', 'IBIZA': 'BALEARES', 'MALLORCA': 'BALEARES', 'MENORCA': 'BALEARES',
        'CASTELLO': 'CASTELLÓN', 'CASTELLON': 'CASTELLÓN', 'CASTELLÓN': 'CASTELLÓN',
        'A CORUÑA': 'A CORUÑA', 'CORUÑA': 'A CORUÑA', 'LA CORUÑA': 'A CORUÑA', 'LA CORUNA': 'A CORUÑA', 'A CORUNA': 'A CORUÑA', 'SANTIAGO': 'A CORUÑA', 'FERROL': 'A CORUÑA',
        'GIRONA': 'GIRONA', 'GERONA': 'GIRONA', 'GARROTXA': 'GIRONA',
        'GIPUZKOA': 'GIPUZKOA', 'GUIPUZCOA': 'GIPUZKOA', 'GUIPÚZCOA': 'GIPUZKOA',
        'LLEIDA': 'LLEIDA', 'LERIDA': 'LLEIDA', 'SEGRIA': 'LLEIDA', 'NOGUERA': 'LLEIDA',
        'OURENSE': 'OURENSE', 'ORENSE': 'OURENSE',
        'BIZKAIA': 'BIZKAIA', 'VIZCAYA': 'BIZKAIA',
        'VALÈNCIA': 'VALENCIA', 'VALENCIA': 'VALENCIA',
        'TENERIFE': 'SANTA CRUZ DE TENERIFE', 'S.C. TENERIFE': 'SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE': 'SANTA CRUZ DE TENERIFE',
        'PALMAS': 'LAS PALMAS', 'GRAN CANARIA': 'LAS PALMAS', 'LAS PALMAS': 'LAS PALMAS',
        'LA RIOJA': 'LA RIOJA', 'RIOJA': 'LA RIOJA',
        'NAVARRA': 'NAVARRA', 'NAFARROA': 'NAVARRA', 'COMUNIDAD FORAL DE NAVARRA': 'NAVARRA', 'PAMPLONA': 'NAVARRA', 'RIBERA': 'NAVARRA',
        'PRINCIPADO DE ASTURIAS': 'ASTURIAS', 'ASTURIAS': 'ASTURIAS',
        'CANTABRIA': 'CANTABRIA',
        'REGION DE MURCIA': 'MURCIA', 'REGIO DE MURCIA': 'MURCIA', 'MURCIA': 'MURCIA', 'ALTO GUADALENTIN': 'MURCIA', 'ALTIPLANO': 'MURCIA', 'NOROESTE': 'MURCIA', 'CAMPO DE CARTAGENA': 'MURCIA',
        'COMUNIDAD DE MADRID': 'MADRID', 'MADRID': 'MADRID',
        'BAHIA DE CADIZ': 'CÁDIZ', 'CÁDIZ': 'CÁDIZ', 'CADIZ': 'CÁDIZ',
        'O SALNES': 'PONTEVEDRA', 'PONTEVEDRA': 'PONTEVEDRA',
        'MALAGA': 'MÁLAGA', 'MÁLAGA': 'MÁLAGA', 'COSTA DEL SOL': 'MÁLAGA',
        'VEGA DE GRANADA': 'GRANADA', 'ALPUJARRA': 'GRANADA', 'GRANADA': 'GRANADA',
        'ANOIA': 'BARCELONA', 'VALLES OCCIDENTAL': 'BARCELONA', 'MARESME': 'BARCELONA', 'BARCELONA': 'BARCELONA',
        'VALLE DEL ALMANZORA': 'ALMERÍA', 'ALMERÍA': 'ALMERÍA', 'ALMERIA': 'ALMERÍA',
        'ALTO CAMPO': 'TARRAGONA', 'TARRAGONA': 'TARRAGONA',
        'CÁCERES': 'CÁCERES', 'CACERES': 'CÁCERES',
        'CÓRDOBA': 'CÓRDOBA', 'CORDOBA': 'CÓRDOBA',
        'CIUDAD REAL': 'CIUDAD REAL',
        'GUADALAJARA': 'GUADALAJARA',
        'TOLEDO': 'TOLEDO',
        'SEGOVIA': 'SEGOVIA',
        'SALAMANCA': 'SALAMANCA',
        'HUELVA': 'HUELVA',
        'JAÉN': 'JAÉN', 'JAEN': 'JAÉN',
        'SEVILLA': 'SEVILLA',
        'BADAJOZ': 'BADAJOZ',
        'CEUTA': 'CEUTA',
        'MELILLA': 'MELILLA',
        'TERUEL': 'TERUEL',
        'ZARAGOZA': 'ZARAGOZA',
        'PALENCIA': 'PALENCIA',
        'SORIA': 'SORIA',
        'BURGOS': 'BURGOS',
        'ÁVILA': 'ÁVILA', 'AVILA': 'ÁVILA',
        'ZAMORA': 'ZAMORA',
        'LEÓN': 'LEÓN', 'LEON': 'LEÓN',
        'HUESCA': 'HUESCA',
        'CUENCA': 'CUENCA',
    }
    
    # Buscar coincidencias en el mapeo
    for key, val in mapping.items():
        if key in prov or prov in key:
            return val
            
    # Limpiezas genéricas
    prov = prov.replace('PROVINCIA DE ', '').replace('PROVINCIA D\'', '').replace('PROVINCIA DE', '')
    prov = prov.replace('COMUNIDAD DE ', '').replace('COMUNIDAD FORAL DE ', '').replace('PRINCIPADO DE ', '')
    
    # Quitar tildes para estandarizar
    replacements = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ü': 'U'}
    for orig, rep in replacements.items():
        prov = prov.replace(orig, rep)
        
    return prov.strip()

def limpiar(nombre_club):
    n = nombre_club.strip()
    for p in PREFIJOS:
        n = re.sub(p, '', n, flags=re.IGNORECASE).strip()
    for s in SUFIJOS:
        n = re.sub(s, '', n, flags=re.IGNORECASE).strip()
        
    # Inyectar sugerencia de municipio geográfico real si hay coincidencia de palabras clave
    sugerencias = []
    for key, mun in KEYWORDS_MUNICIPIOS.items():
        if key in nombre_club:
            sugerencias.append(f"{mun}, Espana")
            
    principal = n.split('-')[0].strip()
    qs, seen = [], set()
    
    # Priorizar la búsqueda de las sugerencias reales para asegurar la geolocalización correcta
    for q in sugerencias:
        if q not in seen:
            seen.add(q)
            qs.append(q)
            
    for q in ([n + ', Espana'] if n != nombre_club else []) + ([principal + ', Espana'] if principal and principal != n else []) + [nombre_club + ', Espana']:
        if q not in seen:
            seen.add(q)
            qs.append(q)
    return qs

def municipio(address):
    for campo in ['city', 'town', 'village', 'municipality', 'hamlet', 'suburb']:
        if campo in address:
            return address[campo].upper()
    return 'DESCONOCIDA'

def provincia_from_address(address):
    # En España, Nominatim devuelve la provincia en 'county'
    # En comunidades uniprovinciales, sirve como provincia su 'state' o 'province'
    for campo in ['county', 'province', 'state']:
        if campo in address:
            val = address[campo]
            norm = normalizar_provincia(val)
            if norm in ['MADRID', 'CANTABRIA', 'NAVARRA', 'ASTURIAS', 'MURCIA', 'LA RIOJA', 'CEUTA', 'MELILLA', 'ILLES BALEARS', 'BALEARES']:
                return norm
            if campo == 'county':
                return norm
    for campo in ['county', 'province', 'state', 'region']:
        if campo in address:
            return normalizar_provincia(address[campo])
    return 'DESCONOCIDA'

def main():
    print('=' * 70)
    print('  GEOCODIFICACION DINAMICA DE CLUBES - Nominatim (OpenStreetMap)')
    print('  Extracción automatizada de Municipios y Provincias Reales')
    print('=' * 70)
    
    if not os.path.exists(CSV_CLUBES):
        print(f'[ERROR] No se encontro: {CSV_CLUBES}'); return
    df = pd.read_csv(CSV_CLUBES, encoding='utf-8')
    print(f'Cargados {len(df)} clubes desde CSV.')
    
    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    print(f'Cache: {len(cache)} entradas previas')
    
    geo = Nominatim(user_agent='tfm_triatlon_fetri_2025_v2', timeout=1)
    lats, lngs, cities, provinces = [], [], [], []
    nuevos = manuales = de_cache = errores = 0
    
    nominatim_available = True
    
    for idx, row in df.iterrows():
        club = str(row['club']).strip().upper()
        done = False
        
        # 1. Correcciones manuales directas
        for k, (ciudad, prov, lat, lng) in CORRECCIONES.items():
            if k.upper() in club or club == k.upper():
                cache[club] = {'lat': lat, 'lng': lng, 'ciudad': ciudad, 'provincia': prov}
                lats.append(lat); lngs.append(lng); cities.append(ciudad); provinces.append(prov)
                manuales += 1; done = True
                print(f'[MANUAL] {club[:40]:<40} -> {ciudad} ({prov})')
                break
        if done: continue
        
        # 2. Leer desde la caché si ya se resolvió antes
        if club in cache:
            e = cache[club]
            lats.append(e['lat']); lngs.append(e['lng']); cities.append(e['ciudad']); provinces.append(e['provincia'])
            de_cache += 1; continue
            
        # 3. Consultar dinámicamente en Nominatim (OSM)
        ok = False
        if nominatim_available:
            for q in limpiar(club):
                try:
                    time.sleep(1.2) # Respetar política de uso de Nominatim (max 1 req/s)
                    loc = geo.geocode(q, addressdetails=True, language='es', country_codes='es')
                    if loc:
                        address = loc.raw.get('address', {})
                        m = municipio(address)
                        prov = provincia_from_address(address)
                        la, lo = loc.latitude, loc.longitude
                        
                        cache[club] = {'lat': la, 'lng': lo, 'ciudad': m, 'provincia': prov}
                        lats.append(la); lngs.append(lo); cities.append(m); provinces.append(prov)
                        nuevos += 1; ok = True
                        print(f'[OK]    {club[:40]:<40} -> {m} ({prov})')
                        break
                except (GeocoderTimedOut, GeocoderUnavailable):
                    print("   [Nominatim] API no disponible (timeout o rate-limit). Activando circuit breaker offline.")
                    nominatim_available = False
                    break
                except Exception as e:
                    print(f'[ERR]   {club[:30]}: {e}')
                    break
                
        if not ok:
            # Intentar fallback heurístico inteligente antes del fallback genérico
            heur_match = None
            for key, (ciudad, prov, la, lo) in HEURISTIC_MAPPING.items():
                if key in club:
                    heur_match = (ciudad, prov, la, lo)
                    break
            
            if heur_match:
                ciudad, prov, la, lo = heur_match
                cache[club] = {'lat': la, 'lng': lo, 'ciudad': ciudad, 'provincia': prov}
                lats.append(la); lngs.append(lo); cities.append(ciudad); provinces.append(prov)
                manuales += 1
                ok = True
                print(f'[HEUR]  {club[:40]:<40} -> {ciudad} ({prov})')
            else:
                # Fallback seguro a Madrid
                # ¡CRÍTICO! NO guardamos 'DESCONOCIDA' en caché para que lo intente en el futuro
                # cache[club] = {'lat': 40.4168, 'lng': -3.7038, 'ciudad': 'DESCONOCIDA', 'provincia': 'DESCONOCIDA'}
                lats.append(40.4168); lngs.append(-3.7038); cities.append('DESCONOCIDA'); provinces.append('DESCONOCIDA')
                errores += 1
                print(f'[FAIL]  {club[:40]:<40} -> Fallback Madrid')
            
        if (idx + 1) % 25 == 0:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f'  >> Cache parcial guardada ({idx + 1}/{len(df)} procesados)')
            
    df['lat'] = lats
    df['lng'] = lngs
    df['ciudad_sede'] = cities
    df['provincia'] = provinces
    
    # Guardar caché final
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
        
    df.to_csv(CSV_CLUBES, index=False, encoding='utf-8')
    reales = len(df[df['provincia'] != 'DESCONOCIDA'])
    
    print('\n' + '=' * 70)
    print('  RESULTADO FINAL')
    print('=' * 70)
    print(f'  Total clubes            : {len(df)}')
    print(f'  Corregidos manualmente  : {manuales}')
    print(f'  Geocodificados OSM      : {nuevos}')
    print(f'  Desde cache             : {de_cache}')
    print(f'  Fallbacks (Sin resol.)  : {errores}')
    print(f'  Provincias resueltas    : {reales}')
    print(f'  CSV: {CSV_CLUBES}')
    print('=' * 70)

if __name__ == '__main__': main()
