import os
import json
import re
import pandas as pd
from geocode_clubs import normalizar_provincia, CORRECCIONES

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'triatlon_masculino', 'trm_2025_original.xlsx')
CACHE_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'club_geocache.json')
CSV_CLUBES = os.path.join(WORKSPACE, 'data', 'processed', 'clubes_geo_2025.csv')

# Diccionario masivo de ciudades y provincias españolas oficiales para mapear de forma offline
TOWNS_DB = {
    # Galicia
    'CORUÑA': ('A CORUÑA', 'A CORUÑA', 43.3623, -8.4115),
    'CORUNA': ('A CORUÑA', 'A CORUÑA', 43.3623, -8.4115),
    'SANTIAGO': ('SANTIAGO DE COMPOSTELA', 'A CORUÑA', 42.8782, -8.5448),
    'COMPOSTELA': ('SANTIAGO DE COMPOSTELA', 'A CORUÑA', 42.8782, -8.5448),
    'FERROL': ('FERROL', 'A CORUÑA', 43.4834, -8.2333),
    'NARON': ('NARÓN', 'A CORUÑA', 43.5014, -8.1925),
    'NARÓN': ('NARÓN', 'A CORUÑA', 43.5014, -8.1925),
    'CARBALLO': ('CARBALLO', 'A CORUÑA', 43.213, -8.691),
    'FOGAR': ('CARBALLO', 'A CORUÑA', 43.213, -8.691),
    'CEDEIRA': ('CEDEIRA', 'A CORUÑA', 43.6701, -8.0538),
    'RIANXO': ('RIANXO', 'A CORUÑA', 42.6464, -8.8183),
    'BETANZOS': ('BETANZOS', 'A CORUÑA', 43.2808, -8.2114),
    'ARTEIXO': ('ARTEIXO', 'A CORUÑA', 43.3048, -8.5052),
    'RIVEIRA': ('RIBEIRA', 'A CORUÑA', 42.5548, -8.9931),
    'RIBEIRA': ('RIBEIRA', 'A CORUÑA', 42.5548, -8.9931),
    'HERCULES': ('A CORUÑA', 'A CORUÑA', 43.3623, -8.4115),
    'NEGREIRA': ('NEGREIRA', 'A CORUÑA', 42.909, -8.735),
    'COTON': ('NEGREIRA', 'A CORUÑA', 42.909, -8.735),
    'VEDRA': ('VEDRA', 'A CORUÑA', 42.776, -8.482),
    'LUGO': ('LUGO', 'LUGO', 43.0125, -7.5558),
    'FLUVIAL': ('LUGO', 'LUGO', 43.0125, -7.5558),
    'PORTOMARIN': ('PORTOMARÍN', 'LUGO', 42.8071, -7.6161),
    'PORTOMARÍN': ('PORTOMARÍN', 'LUGO', 42.8071, -7.6161),
    'OURENSE': ('OURENSE', 'OURENSE', 42.3358, -7.8639),
    'VIGO': ('VIGO', 'PONTEVEDRA', 42.2223, -8.7567),
    'BOUZAS': ('VIGO', 'PONTEVEDRA', 42.2223, -8.7567),
    'PONTEVEDRA': ('PONTEVEDRA', 'PONTEVEDRA', 42.431, -8.6444),
    'VILAGARCIA': ('VILAGARCÍA DE AROUSA', 'PONTEVEDRA', 42.5948, -8.7669),
    'MAR DE VIGO': ('VIGO', 'PONTEVEDRA', 42.2223, -8.7567),
    'SALNES': ('SANXENXO', 'PONTEVEDRA', 42.4015, -8.852),
    'SANXENXO': ('SANXENXO', 'PONTEVEDRA', 42.4015, -8.852),
    'SANGENJO': ('SANXENXO', 'PONTEVEDRA', 42.4015, -8.852),
    'VAO': ('VIGO', 'PONTEVEDRA', 42.2223, -8.7567),

    # Asturias
    'OVIEDO': ('OVIEDO', 'ASTURIAS', 43.3603, -5.8448),
    'VETUSTA': ('OVIEDO', 'ASTURIAS', 43.3603, -5.8448),
    'GIJON': ('GIJÓN', 'ASTURIAS', 43.5357, -5.6615),
    'GIJÓN': ('GIJÓN', 'ASTURIAS', 43.5357, -5.6615),
    'AVILES': ('AVILÉS', 'ASTURIAS', 43.5558, -5.9248),
    'AVILÉS': ('AVILÉS', 'ASTURIAS', 43.5558, -5.9248),
    'LUGONES': ('SIERO', 'ASTURIAS', 43.4044, -5.8121),
    'SIERO': ('SIERO', 'ASTURIAS', 43.4044, -5.8121),
    'CASTRILLON': ('CASTRILLÓN', 'ASTURIAS', 43.5358, -5.9744),
    'CASTRILLÓN': ('CASTRILLÓN', 'ASTURIAS', 43.5358, -5.9744),
    'LLANERA': ('LLANERA', 'ASTURIAS', 43.4402, -5.8502),
    'OCLE': ('LLANES', 'ASTURIAS', 43.42, -4.75),

    # Cantabria
    'SANTANDER': ('SANTANDER', 'CANTABRIA', 43.4623, -3.81),
    'BULL': ('SANTANDER', 'CANTABRIA', 43.4623, -3.81),
    'TORRELAVEGA': ('TORRELAVEGA', 'CANTABRIA', 43.3487, -4.0515),
    'POLANCO': ('POLANCO', 'CANTABRIA', 43.3853, -4.0163),
    'GALIZANO': ('RIBAMONTÁN AL MAR', 'CANTABRIA', 43.46, -3.67),

    # País Vasco
    'BILBAO': ('BILBAO', 'BIZKAIA', 43.263, -2.935),
    'BILBAOTRI': ('BILBAO', 'BIZKAIA', 43.263, -2.935),
    'PORTUGALETE': ('PORTUGALETE', 'BIZKAIA', 43.3189, -3.0199),
    'PEÑOTA': ('PORTUGALETE', 'BIZKAIA', 43.3189, -3.0199),
    'PENOTA': ('PORTUGALETE', 'BIZKAIA', 43.3189, -3.0199),
    'ALUSIGMA': ('PORTUGALETE', 'BIZKAIA', 43.3189, -3.0199),
    'SANTURTZI': ('SANTURTZI', 'BIZKAIA', 43.3283, -3.0315),
    'SESTAO': ('SESTAO', 'BIZKAIA', 43.3081, -3.0089),
    'GETXO': ('GETXO', 'BIZKAIA', 43.3484, -3.0119),
    'GALDAKAO': ('GALDAKAO', 'BIZKAIA', 43.2307, -2.8449),
    'AMANDARRI': ('GERNIKA-LUMO', 'BIZKAIA', 43.3144, -2.6779),
    'GERNIKA': ('GERNIKA-LUMO', 'BIZKAIA', 43.3144, -2.6779),
    'SAN SEBASTIAN': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'SAN SEBASTIÁN': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'DONOSTIA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'YEPA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'TRIKUA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),
    'ZARAUTZ': ('ZARAUTZ', 'GIPUZKOA', 43.2835, -2.1723),
    'ZARAUZ': ('ZARAUTZ', 'GIPUZKOA', 43.2835, -2.1723),
    'HONDARRIBIA': ('HONDARRIBIA', 'GIPUZKOA', 43.3625, -1.7915),
    'BIOSNAR': ('HONDARRIBIA', 'GIPUZKOA', 43.3625, -1.7915),
    'AZKOITIA': ('AZKOITIA', 'GIPUZKOA', 43.18, -2.3167),
    'AZKOITRI': ('AZKOITIA', 'GIPUZKOA', 43.18, -2.3167),
    'BERGARA': ('BERGARA', 'GIPUZKOA', 43.1175, -2.4172),
    'VERGARA': ('BERGARA', 'GIPUZKOA', 43.1175, -2.4172),
    'ANTXINTXIKA': ('BERGARA', 'GIPUZKOA', 43.1175, -2.4172),
    'VITORIA': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'GASTEIZ': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'VIBIKE': ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717),
    'EIBAR': ('EIBAR', 'GIPUZKOA', 43.1834, -2.4715),
    'GETARIA': ('GETARIA', 'GIPUZKOA', 43.303, -2.2037),
    'GETAI': ('GETARIA', 'GIPUZKOA', 43.303, -2.2037),
    'ORDIZIA': ('ORDIZIA', 'GIPUZKOA', 43.053, -2.179),
    'MARKINA': ('MARKINA-XEMEIN', 'BIZKAIA', 43.2681, -2.4969),
    'LEA-ARTIBAI': ('MARKINA-XEMEIN', 'BIZKAIA', 43.2681, -2.4969),
    'UROLA': ('ZUMARRAGA', 'GIPUZKOA', 43.086, -2.316),
    'BASAURI': ('BASAURI', 'BIZKAIA', 43.2361, -2.8872),
    'URBIKO': ('BASAURI', 'BIZKAIA', 43.2361, -2.8872),
    'AMOREBIETA': ('AMOREBIETA-ETXANO', 'BIZKAIA', 43.2206, -2.7308),
    'AETT': ('AMOREBIETA-ETXANO', 'BIZKAIA', 43.2206, -2.7308),
    'SOPELA': ('SOPELA', 'BIZKAIA', 43.3764, -2.9814),
    'MUGARRA': ('DURANGO', 'BIZKAIA', 43.1689, -2.6308),
    'USANSOLO': ('USANSOLO', 'BIZKAIA', 43.23, -2.82),
    'ALOÑA': ('OÑATI', 'GIPUZKOA', 43.033, -2.417),
    'MUNIBE': ('AZKOITIA', 'GIPUZKOA', 43.18, -2.3167),
    'ZUMAIA': ('ZUMAIA', 'GIPUZKOA', 43.298, -2.256),
    'ALTZA': ('SAN SEBASTIÁN', 'GIPUZKOA', 43.3183, -1.9812),

    # Navarra
    'PAMPLONA': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'SALTOKI': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'TRIKIDEAK': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'BURLADA': ('BURLADA', 'NAVARRA', 42.823, -1.6141),
    'HIRU HERRI': ('BURLADA', 'NAVARRA', 42.823, -1.6141),
    'ARANGUREN': ('ARANGUREN', 'NAVARRA', 42.7753, -1.5755),
    'TUDELA': ('TUDELA', 'NAVARRA', 42.0621, -1.603),
    'AZAGRESA': ('AZAGRA', 'NAVARRA', 42.2987, -1.8601),
    'AOIZ': ('AOIZ', 'NAVARRA', 42.785, -1.369),
    'SAKANA': ('ALSASUA', 'NAVARRA', 42.894, -2.166),
    'ALTSASU': ('ALSASUA', 'NAVARRA', 42.894, -2.166),
    'EGUES': ('VALLE DE EGÜÉS', 'NAVARRA', 42.827, -1.558),
    'EGÜÉS': ('VALLE DE EGÜÉS', 'NAVARRA', 42.827, -1.558),
    'ERREKA': ('DONESTEBE', 'NAVARRA', 43.131, -1.696),
    'OBERENA': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'VIANES': ('VIANA', 'NAVARRA', 42.514, -2.364),

    # Aragón
    'ZARAGOZA': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'CASABLANCA': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'TRANSNATUR': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'ALCAÑIZ': ('ALCAÑIZ', 'TERUEL', 41.05, -0.13),
    'TRAGAMILLAS': ('ALCAÑIZ', 'TERUEL', 41.05, -0.13),
    'CALATAYUD': ('CALATAYUD', 'ZARAGOZA', 41.353, -1.6428),
    'HELIOS': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'OLIVAR': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),

    # Cataluña
    'BARCELONA': ('BARCELONA', 'BARCELONA', 41.3851, 2.1734),
    'KATOA': ('BARCELONA', 'BARCELONA', 41.3851, 2.1734),
    'FASTTRIATLON': ('BARCELONA', 'BARCELONA', 41.3851, 2.1734),
    'PRAT': ('EL PRAT DE LLOBREGAT', 'BARCELONA', 41.3283, 2.0944),
    'VIC': ('VIC', 'BARCELONA', 41.9301, 2.2548),
    'IGUALADA': ('IGUALADA', 'BARCELONA', 41.581, 1.617),
    'CORNELLA': ('CORNELLÀ DE LLOBREGAT', 'BARCELONA', 41.3574, 2.0722),
    'TARRASSA': ('TERRASSA', 'BARCELONA', 41.5642, 2.0125),
    'TERRASSA': ('TERRASSA', 'BARCELONA', 41.5642, 2.0125),
    'TARRAGONA': ('TARRAGONA', 'TARRAGONA', 41.1176, 1.2473),
    'LLEIDA': ('LLEIDA', 'LLEIDA', 41.6176, 0.6201),
    'LERIDA': ('LLEIDA', 'LLEIDA', 41.6176, 0.6201),
    'GIRONA': ('GIRONA', 'GIRONA', 41.9794, 2.8214),
    'GERONA': ('GIRONA', 'GIRONA', 41.9794, 2.8214),
    'BANYOLES': ('BANYOLES', 'GIRONA', 42.1179, 2.7667),
    'CALELLA': ('CALELLA', 'BARCELONA', 41.6133, 2.659),
    'GARRIGA': ('LA GARRIGA', 'BARCELONA', 41.684, 2.285),
    'GRANOLLERS': ('GRANOLLERS', 'BARCELONA', 41.6079, 2.2882),
    'WE RUN': ('TERRASSA', 'BARCELONA', 41.5642, 2.0125),
    'SANT CUGAT': ('SANT CUGAT DEL VALLÈS', 'BARCELONA', 41.472, 2.086),
    'MOLINS DE REI': ('MOLINS DE REI', 'BARCELONA', 41.4137, 2.0163),
    'MOLINS': ('MOLINS DE REI', 'BARCELONA', 41.4137, 2.0163),
    'SABADELL': ('SABADELL', 'BARCELONA', 41.5433, 2.1094),
    'VALLBONA': ('VALLBONA D\'ANOIA', 'BARCELONA', 41.518, 1.708),
    'MANRESA': ('MANRESA', 'BARCELONA', 41.728, 1.828),
    'MASNOU': ('EL MASNOU', 'BARCELONA', 41.48, 2.31),
    'MATARO': ('MATARÓ', 'BARCELONA', 41.5381, 2.4447),
    'RDS': ('BARCELONA', 'BARCELONA', 41.3851, 2.1734),

    # Com. Valenciana
    'VALENCIA': ('VALENCIA', 'VALENCIA', 39.4699, -0.3763),
    'CORRE-CUITA': ('VALENCIA', 'VALENCIA', 39.4699, -0.3763),
    'BETERA': ('BÉTERA', 'VALENCIA', 39.5921, -0.4578),
    'BÉTERA': ('BÉTERA', 'VALENCIA', 39.5921, -0.4578),
    'ALGEMESI': ('ALGEMESÍ', 'VALENCIA', 39.1891, -0.4366),
    'ALGEMESÍ': ('ALGEMESÍ', 'VALENCIA', 39.1891, -0.4366),
    'PUÇOL': ('PUÇOL', 'VALENCIA', 39.6172, -0.3028),
    'PUZOL': ('PUÇOL', 'VALENCIA', 39.6172, -0.3028),
    'TRIPUÇOL': ('PUÇOL', 'VALENCIA', 39.6172, -0.3028),
    'GANDIA': ('GANDIA', 'VALENCIA', 38.9681, -0.1803),
    'DELIKIA': ('GANDIA', 'VALENCIA', 38.9681, -0.1803),
    'CEDEIRA': ('GANDIA', 'VALENCIA', 38.9681, -0.1803),
    'ALICANTE': ('ALICANTE', 'ALICANTE', 38.3452, -0.481),
    'TRIALACANT': ('ALICANTE', 'ALICANTE', 38.3452, -0.481),
    'ELCHE': ('ELCHE', 'ALICANTE', 38.2669, -0.6988),
    'CASTELLON': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'CASTELLÓN': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'ONTINYENT': ('ONTINYENT', 'VALENCIA', 38.822, -0.609),
    'XATIVA': ('XÀTIVA', 'VALENCIA', 38.9898, -0.5216),
    'TORREVIEJA': ('TORREVIEJA', 'ALICANTE', 37.9778, -0.6831),
    'ALZIRA': ('ALZIRA', 'VALENCIA', 39.15, -0.443),
    'PICASSENT': ('PICASSENT', 'VALENCIA', 39.362, -0.459),
    'VINAROS': ('VINARÒS', 'CASTELLÓN', 40.4705, 0.4754),
    'VINARÒS': ('VINARÒS', 'CASTELLÓN', 40.4705, 0.4754),
    'VINARÓS': ('VINARÒS', 'CASTELLÓN', 40.4705, 0.4754),
    'ALMAZORA': ('ALMASSORA', 'CASTELLÓN', 39.9431, -0.0631),
    'ALMASSORA': ('ALMASSORA', 'CASTELLÓN', 39.9431, -0.0631),
    'MONCADA': ('MONCADA', 'VALENCIA', 39.5444, -0.3956),
    'OLLERIA': ('L\'OLLERÍA', 'VALENCIA', 38.913, -0.432),
    'L\'OLLERIA': ('L\'OLLERÍA', 'VALENCIA', 38.913, -0.432),
    'CARCAIXENT': ('CARCAIXENT', 'VALENCIA', 39.1235, -0.4503),
    'TRICANET': ('CANET D\'EN BERENGUER', 'VALENCIA', 39.6789, -0.2205),
    'MONOVER': ('MONÓVER', 'ALICANTE', 38.5086, -0.8389),
    'CALPE': ('CALPE', 'ALICANTE', 38.6436, 0.0456),
    'ALCOY': ('ALCOY', 'ALICANTE', 38.6983, -0.4736),
    'TRIALCOY': ('ALCOY', 'ALICANTE', 38.6983, -0.4736),
    'TRITRAIL': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),

    # Madrid
    'MADRID': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'DIABLILLOS': ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'RIVAS': ('RIVAS-VACIAMADRID', 'MADRID', 40.3543, -3.5308),
    'ALCOBENDAS': ('ALCOBENDAS', 'MADRID', 40.5475, -3.6421),
    'MÓSTOLES': ('MÓSTOLES', 'MADRID', 40.3232, -3.8676),
    'MOSTOLES': ('MÓSTOLES', 'MADRID', 40.3232, -3.8676),
    'LAS ROZAS': ('LAS ROZAS DE MADRID', 'MADRID', 40.4943, -3.8679),
    'ROZAS': ('LAS ROZAS DE MADRID', 'MADRID', 40.4943, -3.8679),
    'ALCALA': ('ALCALÁ DE HENARES', 'MADRID', 40.482, -3.364),
    'ALCALÁ': ('ALCALÁ DE HENARES', 'MADRID', 40.482, -3.364),
    'COMPLUTUM': ('ALCALÁ DE HENARES', 'MADRID', 40.482, -3.364),
    'BOADILLA': ('BOADILLA DEL MONTE', 'MADRID', 40.4069, -3.8761),
    'VICALVARO': ('MADRID', 'MADRID', 40.4018, -3.5951),
    'CARABANCHEL': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'SQUALI': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRES CANTOS': ('TRES CANTOS', 'MADRID', 40.6007, -3.708),
    'PARLA': ('PARLA', 'MADRID', 40.2374, -3.7741),
    'ALCORCON': ('ALCORCÓN', 'MADRID', 40.3458, -3.8249),
    'ALCORCÓN': ('ALCORCÓN', 'MADRID', 40.3458, -3.8249),
    'RELOJ': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'ECOSPORT': ('ALCOBENDAS', 'MADRID', 40.5475, -3.6421),
    'S03': ('VALDEMORILLO', 'MADRID', 40.5011, -4.0682),
    'VALDEMORILLO': ('VALDEMORILLO', 'MADRID', 40.5011, -4.0682),
    'VALMAYOR': ('VALDEMORILLO', 'MADRID', 40.5011, -4.0682),
    'ARGANDA': ('ARGANDA DEL REY', 'MADRID', 40.3015, -3.4385),
    'MORALZARZAL': ('MORALZARZAL', 'MADRID', 40.6806, -3.9715),
    'COLMENAR VIEJO': ('COLMENAR VIEJO', 'MADRID', 40.6589, -3.7672),
    'POZUELO': ('POZUELO DE ALARCÓN', 'MADRID', 40.4312, -3.7876),
    'ALPEDRETE': ('ALPEDRETE', 'MADRID', 40.6586, -4.0232),
    'COSLADA': ('COSLADA', 'MADRID', 40.4259, -3.5656),
    'TORREJÓN': ('TORREJÓN DE ARDOZ', 'MADRID', 40.4589, -3.4795),
    'MARLINS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'MAJADAHONDA': ('MAJADAHONDA', 'MADRID', 40.4727, -3.8773),
    'VILLALBA': ('COLLADO VILLALBA', 'MADRID', 40.642, -4.01),
    'COMO PEZ EN EL AGUA': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'SAN AGUSTIN DEL GUADALIX': ('SAN AGUSTÍN DEL GUADALIX', 'MADRID', 40.6783, -3.6147),
    'TRIARIOS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'MUNDOS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'ATLETI': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'VILLALBILLA': ('VILLALBILLA', 'MADRID', 40.435, -3.30),
    'EQTR': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRITANDEM': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRIPATE': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'KISERS': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'MYSTERY MAN': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'LA TRIBU': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TRIFLAVI': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'CE GELATO': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'XPORTXPERIENCE': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'COIX': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'TGCBINN': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'READAPTAT': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'SPORT&FUN': ('MADRID', 'MADRID', 40.4168, -3.7038),
    'RESIST4': ('MADRID', 'MADRID', 40.4168, -3.7038),

    # Castilla y León
    'SORIA': ('SORIA', 'SORIA', 41.764, -2.4688),
    'SORIANO': ('SORIA', 'SORIA', 41.764, -2.4688),
    'ROLLERBIKE': ('SORIA', 'SORIA', 41.764, -2.4688),
    'VALLADOLID': ('VALLADOLID', 'VALLADOLID', 41.6523, -4.7245),
    'SEGOVIA': ('SEGOVIA', 'SEGOVIA', 40.9429, -4.1088),
    'LACERTA': ('SEGOVIA', 'SEGOVIA', 40.9429, -4.1088),
    'SALAMANCA': ('SALAMANCA', 'SALAMANCA', 40.9701, -5.6635),
    'SALMANTINA': ('SALAMANCA', 'SALAMANCA', 40.9701, -5.6635),
    'BURGOS': ('BURGOS', 'BURGOS', 42.344, -3.6969),
    'TRAGALEGUAS': ('BURGOS', 'BURGOS', 42.344, -3.6969),
    'LEON': ('LEÓN', 'LEÓN', 42.5987, -5.5671),
    'LEÓN': ('LEÓN', 'LEÓN', 42.5987, -5.5671),
    'CUELLAR': ('CUÉLLAR', 'SEGOVIA', 41.401, -4.316),
    'LAGUNA DE DUERO': ('LAGUNA DE DUERO', 'VALLADOLID', 41.5828, -4.7214),
    'ARANDA': ('ARANDA DE DUERO', 'BURGOS', 41.6704, -3.6894),

    # Castilla-La Mancha
    'ALBACETE': ('ALBACETE', 'ALBACETE', 38.9942, -1.8585),
    'TOLEDO': ('TOLEDO', 'TOLEDO', 39.8628, -4.0273),
    'TOLEDANO': ('TOLEDO', 'TOLEDO', 39.8628, -4.0273),
    'TRIFENIX': ('TOLEDO', 'TOLEDO', 39.8628, -4.0273),
    'CIUDAD REAL': ('CIUDAD REAL', 'CIUDAD REAL', 38.9848, -3.9274),
    'FORJADORES': ('CIUDAD REAL', 'CIUDAD REAL', 38.9848, -3.9274),
    'GUADALAJARA': ('GUADALAJARA', 'GUADALAJARA', 40.634, -3.163),
    'MARCHAMALO': ('MARCHAMALO', 'GUADALAJARA', 40.6698, -3.2036),
    'CUENCA': ('CUENCA', 'CUENCA', 40.0704, -2.1374),
    'TRISCHOOL': ('CUENCA', 'CUENCA', 40.0704, -2.1374),
    'ALMANSA': ('ALMANSA', 'ALBACETE', 38.8682, -1.0979),
    'TARANCON': ('TARANCÓN', 'CUENCA', 40.0076, -3.0074),
    'TARANCÓN': ('TARANCÓN', 'CUENCA', 40.0076, -3.0074),
    'TRIWILD': ('FUENSALIDA', 'TOLEDO', 40.0594, -4.3603),
    'TRISAGRA': ('MOCEJÓN', 'TOLEDO', 39.93, -3.91),

    # La Rioja
    'LA RIOJA': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'RIOJA': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'TRITONES': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'TRIGOI': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),

    # Extremadura
    'CACERES': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'CÁCERES': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'CHAMO': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'PLASENCIA': ('PLASENCIA', 'CÁCERES', 40.03, -6.09),
    'BADAJOZ': ('BADAJOZ', 'BADAJOZ', 38.8794, -6.9706),
    'ALMENDRALEJO': ('ALMENDRALEJO', 'BADAJOZ', 38.6826, -6.4082),
    'MONTIJO': ('MONTIJO', 'BADAJOZ', 38.91, -6.617),
    'VILLANUEVA DE LA SERENA': ('VILLANUEVA DE LA SERENA', 'BADAJOZ', 38.97, -5.80),
    'CAPEX': ('VILLAFRANCA DE LOS BARROS', 'BADAJOZ', 38.56, -6.22),

    # Andalucía
    'SEVILLA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'ISBILYA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'MALAGA': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'MÁLAGA': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'TRITRAIN4YOU': ('MÁLAGA', 'MÁLAGA', 36.7213, -4.4214),
    'GRANADA': ('GRANADA', 'GRANADA', 37.1773, -3.5986),
    'SULAYR': ('GRANADA', 'GRANADA', 37.1773, -3.5986),
    'CADIZ': ('CÁDIZ', 'CÁDIZ', 36.5271, -6.2923),
    'CÁDIZ': ('CÁDIZ', 'CÁDIZ', 36.5271, -6.2923),
    'CHICLANA': ('CHICLANA DE LA FRONTERA', 'CÁDIZ', 36.4173, -6.1458),
    'BARROSA': ('CHICLANA DE LA FRONTERA', 'CÁDIZ', 36.4173, -6.1458),
    'ALMERIA': ('ALMERÍA', 'ALMERÍA', 36.834, -2.4637),
    'ALMERÍA': ('ALMERÍA', 'ALMERÍA', 36.834, -2.4637),
    'GALOSPORT': ('ALMERÍA', 'ALMERÍA', 36.834, -2.4637),
    'EJIDO': ('EL EJIDO', 'ALMERÍA', 36.7761, -2.8142),
    'HUELVA': ('HUELVA', 'HUELVA', 37.2614, -6.9447),
    'ANTHUS': ('HUELVA', 'HUELVA', 37.2614, -6.9447),
    'JAEN': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'JAÉN': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'BABYSCHOOL': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'CORDOBA': ('CÓRDOBA', 'CÓRDOBA', 37.8882, -4.7794),
    'CÓRDOBA': ('CÓRDOBA', 'CÓRDOBA', 37.8882, -4.7794),
    'GUADIATO': ('PEÑARROYA-PUEBLONUEVO', 'CÓRDOBA', 38.3026, -5.2715),
    'MONTILLA': ('MONTILLA', 'CÓRDOBA', 37.5811, -4.6415),
    'MARBELLA': ('MARBELLA', 'MÁLAGA', 36.5075, -4.8858),
    'ALOHA': ('MARBELLA', 'MÁLAGA', 36.5075, -4.8858),
    'CEUTA': ('CEUTA', 'CEUTA', 35.8894, -5.3198),
    'MELILLA': ('MELILLA', 'MELILLA', 35.2923, -2.9381),
    'ECIJA': ('ÉCIJA', 'SEVILLA', 37.5417, -5.0833),
    'ÉCIJA': ('ÉCIJA', 'SEVILLA', 37.5417, -5.0833),
    'BENALMADENA': ('BENALMÁDENA', 'MÁLAGA', 36.594, -4.522),
    'ALGECIRAS': ('ALGECIRAS', 'CÁDIZ', 36.1408, -5.4562),
    'JEREZANA': ('JEREZ DE LA FRONTERA', 'CÁDIZ', 36.685, -6.126),
    'PCABEZA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'ENTRENA@TRIJUANSA': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'TRISUD': ('SEVILLA', 'SEVILLA', 37.3891, -5.9845),
    'CERRO PUERTA': ('JAÉN', 'JAÉN', 37.7796, -3.7849),
    'MAREA VIVA': ('CÁDIZ', 'CÁDIZ', 36.5271, -6.2923),
    'CHICLANERO': ('CHICLANA DE LA FRONTERA', 'CÁDIZ', 36.4173, -6.1458),
    'CARCAIXENT': ('CARCAIXENT', 'VALENCIA', 39.1235, -0.4503),
    'BAENA': ('BAENA', 'CÓRDOBA', 37.6186, -4.3256),
    'CORIA': ('CORIA DEL RÍO', 'SEVILLA', 37.2831, -6.0506),
    'AL-BALLUT': ('POZOBLANCO', 'CÓRDOBA', 38.379, -4.848),

    # Murcia
    'MURCIA': ('MURCIA', 'MURCIA', 37.9922, -1.1307),
    'CARTAGENA': ('CARTAGENA', 'MURCIA', 37.6051, -0.9862),
    'MANDARACHE': ('CARTAGENA', 'MURCIA', 37.6051, -0.9862),
    'MOLINA': ('MOLINA DE SEGURA', 'MURCIA', 38.05, -1.21),
    'YECLA': ('YECLA', 'MURCIA', 38.6144, -1.1158),
    'LORCA': ('LORCA', 'MURCIA', 37.6715, -1.7017),
    'AGUILAS': ('ÁGUILAS', 'MURCIA', 37.4062, -1.5839),
    'ÁGUILAS': ('ÁGUILAS', 'MURCIA', 37.4062, -1.5839),
    'ARCHENA': ('ARCHENA', 'MURCIA', 38.1178, -1.3025),
    'SIPCAM': ('ARCHENA', 'MURCIA', 38.1178, -1.3025),
    'ALCANTARILLA': ('ALCANTARILLA', 'MURCIA', 37.97, -1.21),
    'GUERRITA': ('ALCANTARILLA', 'MURCIA', 37.97, -1.21),
    'TRIALHAMA': ('ALHAMA DE MURCIA', 'MURCIA', 37.8514, -1.4247),
    'TRIRUNNER': ('CARTAGENA', 'MURCIA', 37.6051, -0.9862),
    'TADER': ('MOLINA DE SEGURA', 'MURCIA', 38.05, -1.21),

    # Canarias
    'TENERIFE': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'RESISTENTIA': ('ADEJE', 'SANTA CRUZ DE TENERIFE', 28.1227, -16.7297),
    'REALES': ('LOS REALEJOS', 'SANTA CRUZ DE TENERIFE', 28.3503, -16.585),
    'PALMAS': ('LAS PALMAS DE GRAN CANARIA', 'LAS PALMAS', 28.1235, -15.4363),
    'TINAJO': ('TINAJO', 'LAS PALMAS', 29.0617, -13.6756),
    'TRIDENTE': ('TINAJO', 'LAS PALMAS', 29.0617, -13.6756),
    'OCEAN': ('TEGUISE', 'LAS PALMAS', 29.0601, -13.5594),
    'ALISIOS': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'TEGALA': ('TEGUISE', 'LAS PALMAS', 29.0601, -13.5594),
    'TRIYAIZA': ('YAIZA', 'LAS PALMAS', 28.9559, -13.7669),
    'YAIZA': ('YAIZA', 'LAS PALMAS', 28.9559, -13.7669),
    'FUERTRI': ('PUERTO DEL ROSARIO', 'LAS PALMAS', 28.50, -13.86),
    'SANTISORA': ('GUÍA DE ISORA', 'SANTA CRUZ DE TENERIFE', 28.2111, -16.7788),
    'TRICAN': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'SPAR TENERIFE': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'CANDETLÓN': ('CANDELARIA', 'SANTA CRUZ DE TENERIFE', 28.354, -16.371),
    'CALIMA': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'T3': ('ADEJE', 'SANTA CRUZ DE TENERIFE', 28.1227, -16.7297),

    # Baleares
    'BALEARS': ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502),
    'BALEARES': ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502),
    'CALDENTEY': ('MANACOR', 'BALEARES', 39.5693, 3.2096),
    'PORTOCOLOM': ('FELANITX', 'BALEARES', 39.421, 3.262),
    'RAIGUER': ('INCA', 'BALEARES', 39.721, 2.911),
    'IBIZA': ('IBIZA', 'BALEARES', 38.9089, 1.4324),
    'ESPALMADOR': ('FORMENTERA', 'BALEARES', 38.718, 1.428),
    'SA POBLA': ('SA POBLA', 'BALEARES', 39.769, 3.027),
    'POBLA': ('SA POBLA', 'BALEARES', 39.769, 3.027),
    'CALVIÀ': ('CALVIÀ', 'BALEARES', 39.565, 2.503),
    'CALVIA': ('CALVIÀ', 'BALEARES', 39.565, 2.503),
    'SON SERVERA': ('SON SERVERA', 'BALEARES', 39.62, 3.36),
    'CALA MILLOR': ('SON SERVERA', 'BALEARES', 39.62, 3.36),
}

def to_alpha(text):
    text = str(text).upper().strip()
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ü': 'U', 'Ñ': 'N',
        '': 'O',
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Dejar solo caracteres alfanuméricos
    return re.sub(r'[^A-Z0-9]', '', text)

def deep_refine():
    print("Iniciando geocodificación profunda de alta fidelidad con normalización de caracteres corruptos...")
    
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)
        
    print(f"Cargadas {len(cache)} entradas en la caché.")
    updated = 0
    
    # Pre-calcular versiones alfanuméricas del diccionario
    alpha_db = {}
    for key, val in TOWNS_DB.items():
        alpha_db[to_alpha(key)] = val
        
    for club in list(cache.keys()):
        # Normalizar el nombre del club para matching (eliminando tildes y caracteres rotos como )
        club_alpha = to_alpha(club)
        
        # 1. Comprobar si coincide con el manual de correcciones directamente (limpiando encoding)
        matched = False
        for k, (ciudad, prov, lat, lng) in CORRECCIONES.items():
            if to_alpha(k) in club_alpha:
                prov_std = normalizar_provincia(prov)
                cache[club] = {
                    'lat': lat,
                    'lng': lng,
                    'ciudad': ciudad,
                    'provincia': prov_std
                }
                matched = True
                updated += 1
                break
                
        # 2. Si no coincide, comprobar contra nuestra base de datos de municipios oficiales alfanuméricos
        if not matched:
            for key_alpha, (ciudad, prov, la, lo) in alpha_db.items():
                if key_alpha in club_alpha:
                    prov_std = normalizar_provincia(prov)
                    cache[club] = {
                        'lat': la,
                        'lng': lo,
                        'ciudad': ciudad,
                        'provincia': prov_std
                    }
                    matched = True
                    updated += 1
                    break
                    
        # 3. Forzar estandarización de la provincia si aún no se ha mapeado
        if not matched:
            orig_prov = cache[club].get('provincia', 'DESCONOCIDA')
            std_prov = normalizar_provincia(orig_prov)
            if orig_prov != std_prov:
                cache[club]['provincia'] = std_prov
                updated += 1
                
    # Guardar caché final
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
        
    print(f"Refinamiento profundo completado. {updated} entradas de la caché optimizadas e inyectadas.")

if __name__ == "__main__":
    deep_refine()
