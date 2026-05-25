import os
import json
import pandas as pd
from geocode_clubs import normalizar_provincia

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'club_geocache.json')

# Base de datos de palabras clave específicas adicionales para resolver los clubes restantes
ADDITIONAL_TOWNS_DB = {
    'EIBAR': ('EIBAR', 'GIPUZKOA', 43.1834, -2.4715),
    'GETARIA': ('GETARIA', 'GIPUZKOA', 43.303, -2.2037),
    'GETAI': ('GETARIA', 'GIPUZKOA', 43.303, -2.2037),
    'ORDIZIA': ('ORDIZIA', 'GIPUZKOA', 43.053, -2.179),
    'ALZIRA': ('ALZIRA', 'VALENCIA', 39.15, -0.443),
    'PICASSENT': ('PICASSENT', 'VALENCIA', 39.362, -0.459),
    'VINAROS': ('VINARÒS', 'CASTELLÓN', 40.4705, 0.4754),
    'VINARÒS': ('VINARÒS', 'CASTELLÓN', 40.4705, 0.4754),
    'VINARÓS': ('VINARÒS', 'CASTELLÓN', 40.4705, 0.4754),
    'ALMAZORA': ('ALMASSORA', 'CASTELLÓN', 39.9431, -0.0631),
    'ALMASSORA': ('ALMASSORA', 'CASTELLÓN', 39.9431, -0.0631),
    'TARANCON': ('TARANCÓN', 'CUENCA', 40.0076, -3.0074),
    'TARANCÓN': ('TARANCÓN', 'CUENCA', 40.0076, -3.0074),
    'CALELLA': ('CALELLA', 'BARCELONA', 41.6133, 2.659),
    'IBIZA': ('IBIZA', 'BALEARES', 38.9089, 1.4324),
    'EIVISSA': ('IBIZA', 'BALEARES', 38.9089, 1.4324),
    'GARRIGA': ('LA GARRIGA', 'BARCELONA', 41.684, 2.285),
    'AÑORGA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'ANORGA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'HELIOS': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'CARCAIXENT': ('CARCAIXENT', 'VALENCIA', 39.1235, -0.4503),
    'GRANOLLERS': ('GRANOLLERS', 'BARCELONA', 41.6079, 2.2882),
    'TEGALA': ('TEGUISE', 'LAS PALMAS', 29.0601, -13.5594),
    'AOIZ': ('AOIZ', 'NAVARRA', 42.785, -1.369),
    'MARKINA': ('MARKINA-XEMEIN', 'BIZKAIA', 43.2681, -2.4969),
    'LEA-ARTIBAI': ('MARKINA-XEMEIN', 'BIZKAIA', 43.2681, -2.4969),
    'SAKANA': ('ALSASUA', 'NAVARRA', 42.894, -2.166),
    'ALTSASU': ('ALSASUA', 'NAVARRA', 42.894, -2.166),
    'EGUES': ('VALLE DE EGÜÉS', 'NAVARRA', 42.827, -1.558),
    'EGÜÉS': ('VALLE DE EGÜÉS', 'NAVARRA', 42.827, -1.558),
    'PISUERGA': ('VALLADOLID', 'VALLADOLID', 41.6523, -4.7245),
    'PACENSE': ('BADAJOZ', 'BADAJOZ', 38.8794, -6.9706),
    'ESPALMADOR': ('FORMENTERA', 'BALEARES', 38.718, 1.428),
    'MAJADAHONDA': ('MAJADAHONDA', 'MADRID', 40.4727, -3.8773),
    'REINOSA': ('REINOSA', 'CANTABRIA', 42.9991, -4.1377),
    'TOMELLOSO': ('TOMELLOSO', 'CIUDAD REAL', 39.1583, -3.0212),
    'GALIZANO': ('RIBAMONTÁN AL MAR', 'CANTABRIA', 43.46, -3.67),
    'FUENTES': ('FUENTES DE EBRO', 'ZARAGOZA', 41.51, -0.63),
    'TRIYAIZA': ('YAIZA', 'LAS PALMAS', 28.9559, -13.7669),
    'YAIZA': ('YAIZA', 'LAS PALMAS', 28.9559, -13.7669),
    'MONCADA': ('MONCADA', 'VALENCIA', 39.5444, -0.3956),
    'OLLERIA': ('L\'OLLERÍA', 'VALENCIA', 38.913, -0.432),
    'L\'OLLERIA': ('L\'OLLERÍA', 'VALENCIA', 38.913, -0.432),
    'JEREZ': ('JEREZ DE LOS CABALLEROS', 'BADAJOZ', 38.32, -6.77),
    'WE RUN': ('TERRASSA', 'BARCELONA', 41.5642, 2.0125),
    'VILLALBA': ('COLLADO VILLALBA', 'MADRID', 40.642, -4.01),
    'SANT CUGAT': ('SANT CUGAT DEL VALLÈS', 'BARCELONA', 41.472, 2.086),
    'SA POBLA': ('SA POBLA', 'BALEARES', 39.769, 3.027),
    'POBLA': ('SA POBLA', 'BALEARES', 39.769, 3.027),
    'ERREKA': ('DONESTEBE', 'NAVARRA', 43.131, -1.696),
    'FUERTRI': ('PUERTO DEL ROSARIO', 'LAS PALMAS', 28.50, -13.86),
    'MOLINS DE REI': ('MOLINS DE REI', 'BARCELONA', 41.4137, 2.0163),
    'MOLINS': ('MOLINS DE REI', 'BARCELONA', 41.4137, 2.0163),
    'BAENA': ('BAENA', 'CÓRDOBA', 37.6186, -4.3256),
    'CORIA': ('CORIA DEL RÍO', 'SEVILLA', 37.2831, -6.0506),
    'PALIBA': ('PALENCIA', 'PALENCIA', 42.0094, -4.5283),
    'UROLA': ('ZUMARRAGA', 'GIPUZKOA', 43.086, -2.316),
    'VEDRA': ('VEDRA', 'A CORUÑA', 42.776, -8.482),
    'BASAURI': ('BASAURI', 'BIZKAIA', 43.2361, -2.8872),
    'URBIKO': ('BASAURI', 'BIZKAIA', 43.2361, -2.8872),
    'AMOREBIETA': ('AMOREBIETA-ETXANO', 'BIZKAIA', 43.2206, -2.7308),
    'AETT': ('AMOREBIETA-ETXANO', 'BIZKAIA', 43.2206, -2.7308),
    'SOPELA': ('SOPELA', 'BIZKAIA', 43.3764, -2.9814),
    'CALVIÀ': ('CALVIÀ', 'BALEARES', 39.565, 2.503),
    'CALVIA': ('CALVIÀ', 'BALEARES', 39.565, 2.503),
    'CHICLANERO': ('CHICLANA DE LA FRONTERA', 'CÁDIZ', 36.4173, -6.1458),
    'OLIVAR': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'SANTISORA': ('GUÍA DE ISORA', 'SANTA CRUZ DE TENERIFE', 28.2111, -16.7788),
    'MUGARRA': ('DURANGO', 'BIZKAIA', 43.1689, -2.6308),
    'ALCOY': ('ALCOY', 'ALICANTE', 38.6983, -0.4736),
    'TRIALCOY': ('ALCOY', 'ALICANTE', 38.6983, -0.4736),
    'USANSOLO': ('USANSOLO', 'BIZKAIA', 43.23, -2.82),
    'SON SERVERA': ('SON SERVERA', 'BALEARES', 39.62, 3.36),
    'SABADELL': ('SABADELL', 'BARCELONA', 41.5433, 2.1094),
    'PUNTA UMBRIA': ('PUNTA UMBRÍA', 'HUELVA', 37.1857, -6.9693),
    'PUNTA UMBRÍA': ('PUNTA UMBRÍA', 'HUELVA', 37.1857, -6.9693),
    'VALLBONA': ('VALLBONA D\'ANOIA', 'BARCELONA', 41.518, 1.708),
    'MANRESA': ('MANRESA', 'BARCELONA', 41.728, 1.828),
    'VIANES': ('VIANA', 'NAVARRA', 42.514, -2.364),
    'MASNOU': ('EL MASNOU', 'BARCELONA', 41.48, 2.31),
    'MONOVER': ('MONÓVER', 'ALICANTE', 38.5086, -0.8389),
    'CALA MILLOR': ('SON SERVERA', 'BALEARES', 39.62, 3.36),
    'CALPE': ('CALPE', 'ALICANTE', 38.6436, 0.0456),
    'ROTEÑOS': ('ROTA', 'CÁDIZ', 36.621, -6.36),
    'MATARO': ('MATARÓ', 'BARCELONA', 41.5381, 2.4447),
    'ARANDA': ('ARANDA DE DUERO', 'BURGOS', 41.6704, -3.6894),
    'TRISAGRA': ('MOCEJÓN', 'TOLEDO', 39.93, -3.91),
    'TFC LLANERA': ('LLANERA', 'ASTURIAS', 43.4402, -5.8502),
    'VILLANUEVA DE LA SERENA': ('VILLANUEVA DE LA SERENA', 'BADAJOZ', 38.97, -5.80),
    'MARCHAMALO': ('MARCHAMALO', 'GUADALAJARA', 40.6698, -3.2036),
    'COMO PEZ EN EL AGUA': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'MONTIJO': ('MONTIJO', 'BADAJOZ', 38.91, -6.617),
    'SAN AGUSTIN DEL GUADALIX': ('SAN AGUSTÍN DEL GUADALIX', 'MADRID', 40.6783, -3.6147),
    'CALIFAS': ('POSADAS', 'CÓRDOBA', 37.81, -5.11),
    'ENKARTERRI': ('BALMASEDA', 'BIZKAIA', 43.178, -3.195),
    'TRIARIOS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'MUNDOS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TORREJON': ('TORREJÓN DE ARDOZ', 'MADRID', 40.4589, -3.4795),
    'SPAR TENERIFE': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'TADER': ('MOLINA DE SEGURA', 'MURCIA', 38.05, -1.21),
    'TRITRAIL': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'ATLETI': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'ARGANDA': ('ARGANDA DEL REY', 'MADRID', 40.3015, -3.4385),
    'MORALZARZAL': ('MORALZARZAL', 'MADRID', 40.6806, -3.9715),
    'ALCORCON': ('ALCORCÓN', 'MADRID', 40.3458, -3.8249),
    'CAMPOS DE CASTILLA': ('PALENCIA', 'PALENCIA', 42.0094, -4.5283),
    'AL-BALLUT': ('POZOBLANCO', 'CÓRDOBA', 38.379, -4.848),
    'ZUMAIA': ('ZUMAIA', 'GIPUZKOA', 43.298, -2.256),
    'VILLALBILLA': ('VILLALBILLA', 'MADRID', 40.435, -3.30),
    'ALTZA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'OBERENA': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'MUNIBE': ('AZKOITIA', 'GIPUZKOA', 43.18, -2.3167),
    'ALGECIRAS': ('ALGECIRAS', 'CÁDIZ', 36.1408, -5.4562),
    'TRICANET': ('CANET D\'EN BERENGUER', 'VALENCIA', 39.6789, -0.2205),
    'ROLLERBIKE': ('SORIA', 'SORIA', 41.764, -2.4688),
    'A7': ('ALCOY', 'ALICANTE', 38.6983, -0.4736),
    'EQTR': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'JEREZANA': ('JEREZ DE LA FRONTERA', 'CÁDIZ', 36.685, -6.126),
    'RDS': ('BARCELONA', 'BARCELONA', 41.3851, 2.1734),
    'TRICAN': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'INDARPAK': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'TRIALHAMA': ('ALHAMA DE MURCIA', 'MURCIA', 37.8514, -1.4247),
    'TRIBOOST': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'URDAITRI': ('BERMEO', 'BIZKAIA', 43.418, -2.721),
    'TRIKIMANES': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'JAZ': ('EIBAR', 'GIPUZKOA', 43.1834, -2.4715),
    'LA BLANCA': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'TRIGOI': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'ALOÑA': ('OÑATI', 'GIPUZKOA', 43.033, -2.417),
    'CANDETLÓN': ('CANDELARIA', 'SANTA CRUZ DE TENERIFE', 28.354, -16.371),
    'COTON': ('NEGREIRA', 'A CORUÑA', 42.909, -8.735),
    'CINCO COLINAS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRITANDEM': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRIELX': ('ELCHE', 'ALICANTE', 38.2669, -0.6988),
    'TRISUREST': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'CD TRIBARIA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'Z5': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'APOL*ANA': ('ALICANTE', 'ALICANTE', 38.3452, -0.481),
    'TRIPATE': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'OCLE': ('LLANES', 'ASTURIAS', 43.42, -4.75),
    'KISERS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRIWILD': ('FUENSALIDA', 'TOLEDO', 40.0594, -4.3603),
    'MYSTERY MAN': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'LA TRIBU': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRINORTE': ('OVIEDO', 'ASTURIAS', 43.3603, -5.8448),
    'PCABEZA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'TRIFLAVI': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'CAPEX': ('VILLAFRANCA DE LOS BARROS', 'BADAJOZ', 38.56, -6.22),
    'CE GELATO': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'BIZI': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'TOLOSALDEKO': ('TOLOSA', 'GIPUZKOA', 43.136, -2.071),
    'XPORTXPERIENCE': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRIRUNNER': ('CARTAGENA', 'MURCIA', 37.6051, -0.9862),
    'GREGO': ('VALENCIA', 'VALENCIA', 39.4699, -0.3763),
    'COIX': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'ROBERTO RAMOS': ('SEGOVIA', 'SEGOVIA', 40.9429, -4.1088),
    'ENTRENA@TRIJUANSA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'OSCENSE': ('HUESCA', 'HUESCA', 42.1318, -0.4078),
    'TRIDIMONIS': ('VALENCIA', 'VALENCIA', 39.4699, -0.3763),
    'KORTA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'TGCBINN': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TEGALA': ('TEGUISE', 'LAS PALMAS', 29.0601, -13.5594),
    'AOIZ': ('AOIZ', 'NAVARRA', 42.785, -1.369),
    'TRISUD': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'TRIATLONCIEM': ('CIEMPOZUELOS', 'MADRID', 40.158, -3.619),
    'ARTE FISICO': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'CALIMA': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'READAPTAT': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'CERRO PUERTA': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'SPORT&FUN': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'RESIST4': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'MAREA VIVA': ('CÁDIZ', 'CÁDIZ', 36.5271, -6.2923),
    'T3': ('ADEJE', 'SANTA CRUZ DE TENERIFE', 28.1227, -16.7297),
}

def refine_more():
    print("Iniciando refinamiento profundo masivo geográfico offline de desconocidos...")
    
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)
        
    print(f"Cargadas {len(cache)} entradas de caché.")
    updated = 0
    
    for club in list(cache.keys()):
        # Si el club es DESCONOCIDA o no tiene provincia estándar
        if cache[club]['ciudad'] == 'DESCONOCIDA' or cache[club]['provincia'] == 'DESCONOCIDA':
            club_clean = str(club).strip().upper()
            
            matched = False
            for key, (ciudad, prov, la, lo) in ADDITIONAL_TOWNS_DB.items():
                if key in club_clean:
                    prov_std = normalizar_provincia(prov)
                    cache[club] = {
                        'lat': la,
                        'lng': lo,
                        'ciudad': ciudad,
                        'provincia': prov_std
                    }
                    matched = True
                    updated += 1
                    print(f"   [DEEP RESOLVED] {club[:35]:<35} -> {ciudad} ({prov_std})")
                    break
                    
    # Guardar caché final
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
        
    print(f"Refinamiento profundo completado. {updated} clubes resueltos offline.")

if __name__ == "__main__":
    refine_more()
