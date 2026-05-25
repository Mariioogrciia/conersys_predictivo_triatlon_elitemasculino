import os
import json
import pandas as pd
from geocode_clubs import normalizar_provincia

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CLUBES = os.path.join(WORKSPACE, 'data', 'processed', 'clubes_geo_2025.csv')
CACHE_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'club_geocache.json')

# Diccionario offline masivo para asociar subcadenas a ciudades reales, provincias oficiales y coordenadas de alta fidelidad
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

    # Cantabria
    'SANTANDER': ('SANTANDER', 'CANTABRIA', 43.4623, -3.81),
    'BULL': ('SANTANDER', 'CANTABRIA', 43.4623, -3.81),
    'TORRELAVEGA': ('TORRELAVEGA', 'CANTABRIA', 43.3487, -4.0515),
    'POLANCO': ('POLANCO', 'CANTABRIA', 43.3853, -4.0163),

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

    # Navarra
    'PAMPLONA': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'SALTOKI': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'TRIKIDEAK': ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522),
    'BURLADA': ('BURLADA', 'NAVARRA', 42.823, -1.6141),
    'HIRU HERRI': ('BURLADA', 'NAVARRA', 42.823, -1.6141),
    'ARANGUREN': ('ARANGUREN', 'NAVARRA', 42.7753, -1.5755),
    'TUDELA': ('TUDELA', 'NAVARRA', 42.0621, -1.603),
    'AZAGRESA': ('AZAGRA', 'NAVARRA', 42.2987, -1.8601),

    # Aragón
    'ZARAGOZA': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'CASABLANCA': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'TRANSNATUR': ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891),
    'ALCAÑIZ': ('ALCAÑIZ', 'TERUEL', 41.05, -0.13),
    'TRAGAMILLAS': ('ALCAÑIZ', 'TERUEL', 41.05, -0.13),
    'CALATAYUD': ('CALATAYUD', 'ZARAGOZA', 41.353, -1.6428),

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
    'ALICANTE': ('ALICANTE', 'ALICANTE', 38.3452, -0.481),
    'TRIALACANT': ('ALICANTE', 'ALICANTE', 38.3452, -0.481),
    'ELCHE': ('ELCHE', 'ALICANTE', 38.2669, -0.6988),
    'CASTELLON': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'CASTELLÓN': ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513),
    'ONTINYENT': ('ONTINYENT', 'VALENCIA', 38.822, -0.609),
    'XATIVA': ('XÀTIVA', 'VALENCIA', 38.9898, -0.5216),
    'TORREVIEJA': ('TORREVIEJA', 'ALICANTE', 37.9778, -0.6831),

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

    # Castilla y León
    'SORIA': ('SORIA', 'SORIA', 41.764, -2.4688),
    'SORIANO': ('SORIA', 'SORIA', 41.764, -2.4688),
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

    # La Rioja
    'LA RIOJA': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'RIOJA': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),
    'TRITONES': ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445),

    # Extremadura
    'CACERES': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'CÁCERES': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'CHAMO': ('CÁCERES', 'CÁCERES', 39.4753, -6.3722),
    'PLASENCIA': ('PLASENCIA', 'CÁCERES', 40.03, -6.09),
    'BADAJOZ': ('BADAJOZ', 'BADAJOZ', 38.8794, -6.9706),
    'ALMENDRALEJO': ('ALMENDRALEJO', 'BADAJOZ', 38.6826, -6.4082),
    'MONTIJO': ('MONTIJO', 'BADAJOZ', 38.91, -6.617),
    'VILLANUEVA DE LA SERENA': ('VILLANUEVA DE LA SERENA', 'BADAJOZ', 38.97, -5.80),

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

    # Canarias
    'TENERIFE': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),
    'RESISTENTIA': ('ADEJE', 'SANTA CRUZ DE TENERIFE', 28.1227, -16.7297),
    'REALES': ('LOS REALEJOS', 'SANTA CRUZ DE TENERIFE', 28.3503, -16.585),
    'PALMAS': ('LAS PALMAS DE GRAN CANARIA', 'LAS PALMAS', 28.1235, -15.4363),
    'TINAJO': ('TINAJO', 'LAS PALMAS', 29.0617, -13.6756),
    'TRIDENTE': ('TINAJO', 'LAS PALMAS', 29.0617, -13.6756),
    'OCEAN': ('TEGUISE', 'LAS PALMAS', 29.0601, -13.5594),
    'ALISIOS': ('SANTA CRUZ DE TENERIFE', 'SANTA CRUZ DE TENERIFE', 28.463, -16.259),

    # Baleares
    'BALEARS': ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502),
    'BALEARES': ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502),
    'CALDENTEY': ('MANACOR', 'BALEARES', 39.5693, 3.2096),
    'PORTOCOLOM': ('FELANITX', 'BALEARES', 39.421, 3.262),
    'RAIGUER': ('INCA', 'BALEARES', 39.721, 2.911),
}

def refine():
    print("Iniciando refinamiento masivo geográfico offline de provincias y municipios...")
    
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)
        
    print(f"Cargadas {len(cache)} entradas de caché.")
    updated = 0
    
    for club in list(cache.keys()):
        club_clean = str(club).strip().upper()
        
        # 1. Comprobar si el nombre del club tiene acoplamiento directo con nuestra base de datos de municipios
        matched = False
        for key, (ciudad, prov, la, lo) in TOWNS_DB.items():
            if key in club_clean:
                # Estandarizar la provincia
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
                
        # 2. Si no coincide con nuestra base de datos de municipios, al menos intentar estandarizar su provincia actual
        if not matched:
            orig_prov = cache[club].get('provincia', 'DESCONOCIDA')
            std_prov = normalizar_provincia(orig_prov)
            if orig_prov != std_prov:
                cache[club]['provincia'] = std_prov
                updated += 1
                
    # Guardar caché final
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
        
    print(f"Refinamiento completado. Actualizados/Estandarizados {updated} registros en la caché.")

if __name__ == "__main__":
    refine()
