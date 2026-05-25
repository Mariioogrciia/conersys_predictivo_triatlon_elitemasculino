"""
Script para resolver los clubes restantes con matching flexible (ignora acentos).
"""
import os, json, unicodedata
import pandas as pd

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(WORKSPACE, 'data', 'raw', 'club_geocache.json')
CSV_CLUBES = os.path.join(WORKSPACE, 'data', 'processed', 'clubes_geo_2025.csv')

def strip_accents(s):
    """Elimina todos los acentos de una cadena para comparación flexible."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    ).upper()

# Mapeo: palabra clave (sin acentos) -> (ciudad, provincia, lat, lng)
# Usamos contains para que no importe la codificación exacta
KEYWORD_MAP = [
    # Catalan clubs
    ('SALOU', 'TRIATL', ('SALOU', 'TARRAGONA', 41.0764, 1.1414)),
    ('VINAR', 'TRIATL', ('VINARÒS', 'CASTELLÓN', 40.4706, 0.4753)),
    ('CREU GROGA', 'CALELLA', ('CALELLA', 'BARCELONA', 41.6147, 2.6536)),
    ('GRANOLLERS', '', ('GRANOLLERS', 'BARCELONA', 41.6082, 2.2876)),
    ('LA GARRIGA', '', ('LA GARRIGA', 'BARCELONA', 41.6808, 2.2836)),
    ('PICORNELL', '', ('BARCELONA', 'BARCELONA', 41.3642, 2.1506)),
    ('PLATJA LLARGA', '', ('TARRAGONA', 'TARRAGONA', 41.1189, 1.2445)),
    ('TRITRAIL', 'CASTELL', ('CASTELLÓN DE LA PLANA', 'CASTELLÓN', 39.9864, -0.0513)),
    ('OLLERIA', 'REPTES', ("L'OLLERIA", 'VALENCIA', 38.9167, -0.5500)),
    ('CORNELLA', '', ('CORNELLÀ DE LLOBREGAT', 'BARCELONA', 41.3531, 2.0706)),
    ('PORTOCOLOM', '', ('FELANITX', 'BALEARES', 39.4258, 3.1489)),
    ('PRORUNNERS', '', ('BARCELONA', 'BARCELONA', 41.3851, 2.1734)),
    # Valencia
    ('MONCADA', 'AVANT', ('MONCADA', 'VALENCIA', 39.5486, -0.3953)),
    ('CARCAIXENT', '', ('CARCAIXENT', 'VALENCIA', 39.1244, -0.4417)),
    ('PICASSENT', '', ('PICASSENT', 'VALENCIA', 39.3583, -0.4583)),
    ('CANET', 'BERENGUER', ('CANET DE BERENGUER', 'VALENCIA', 39.6833, -0.2167)),
    ('SAN VICENTE', 'TRIATLON', ('SAN VICENTE DEL RASPEIG', 'ALICANTE', 38.3964, -0.5253)),
    ('PROSAN', 'TRIATL', ('VALENCIA', 'VALENCIA', 39.4699, -0.3763)),
    # Madrid
    ('RETIRO', 'MADRID', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('MORALZARZAL', '', ('MORALZARZAL', 'MADRID', 40.6733, -3.9622)),
    ('COSLADA', '', ('COSLADA', 'MADRID', 40.4239, -3.5615)),
    ('TRES CANTOS', '', ('TRES CANTOS', 'MADRID', 40.6009, -3.7074)),
    ('TRIMAD', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('TRIATLON ATLETI', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('MARLINS', 'MADRID', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('401', 'TETRASOD', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    # Basque Country
    ('ORDIZIA', '', ('ORDIZIA', 'GIPUZKOA', 43.0539, -2.1736)),
    ('TOLOSALDEKO', '', ('TOLOSA', 'GIPUZKOA', 43.1346, -2.0781)),
    ('ANORGA', '', ('SAN SEBASTIÁN', 'GIPUZKOA', 43.2883, -1.9976)),
    ('UROLA', 'TRIATLOI', ('AZPEITIA', 'GIPUZKOA', 43.1833, -2.2667)),
    ('GETAITRI', '', ('GETARIA', 'GIPUZKOA', 43.3067, -2.2028)),
    ('EIBAR', '', ('EIBAR', 'GIPUZKOA', 43.1847, -2.4722)),
    ('ZUMAIAKO', '', ('ZUMAIA', 'GIPUZKOA', 43.2953, -2.2531)),
    ('ALONA MENDI', '', ('OÑATI', 'GIPUZKOA', 43.0333, -2.4167)),
    ('TRIGOI', '', ('AZKOITIA', 'GIPUZKOA', 43.18, -2.3167)),
    ('ZUMEATARRA', '', ('ZUMARRAGA', 'GIPUZKOA', 43.0886, -2.3153)),
    ('URDAITRI', '', ('BERMEO', 'BIZKAIA', 43.4217, -2.7222)),
    ('MUGARRA', '', ('MUNGIA', 'BIZKAIA', 43.3544, -2.8472)),
    ('USANSOLOKO', '', ('GALDAKAO', 'BIZKAIA', 43.2307, -2.8449)),
    ('ENKARTERRI', '', ('BALMASEDA', 'BIZKAIA', 43.1947, -3.1906)),
    ('ALARABI', 'MARKINA', ('MARKINA-XEMEIN', 'BIZKAIA', 43.2689, -2.4928)),
    ('BIZI TRIATLOI', '', ('BILBAO', 'BIZKAIA', 43.263, -2.935)),
    ('EGURRE', '', ('DURANGO', 'BIZKAIA', 43.1711, -2.6328)),
    ('LEA LA BLANCA', '', ('LEKEITIO', 'BIZKAIA', 43.3633, -2.5025)),
    ('HIRUKO', '', ('BARAKALDO', 'BIZKAIA', 43.2956, -2.9925)),
    ('INDARPAK', '', ('BILBAO', 'BIZKAIA', 43.263, -2.935)),
    ('FORONDA', 'DIDA', ('VITORIA-GASTEIZ', 'ÁLAVA', 42.8467, -2.6717)),
    ('OINKARIAK', 'AMURRIO', ('AMURRIO', 'ÁLAVA', 43.0531, -3.0003)),
    ('OBERENA', '', ('PAMPLONA', 'NAVARRA', 42.8157, -1.6522)),
    ('VALLE DE EGUES', '', ('VALLE DE EGÜÉS', 'NAVARRA', 42.8333, -1.5833)),
    ('AZAGRESA', '', ('AZAGRA', 'NAVARRA', 42.3153, -1.8928)),
    # Galicia
    ('NEGREIRA', '', ('NEGREIRA', 'A CORUÑA', 42.9067, -8.5583)),
    ('ARTEIXO', '', ('ARTEIXO', 'A CORUÑA', 43.3044, -8.5089)),
    ('VEDRA', '', ('VEDRA', 'A CORUÑA', 42.7789, -8.4761)),
    ('CORUNA', 'TRIATLON', ('A CORUÑA', 'A CORUÑA', 43.3623, -8.4115)),
    ('FOGAR', '', ('CARBALLO', 'A CORUÑA', 43.2131, -8.6911)),
    # Cantabria
    ('POLANCO', '', ('POLANCO', 'CANTABRIA', 43.3917, -4.0253)),
    # Murcia
    ('POZO ESTRECHO', '', ('CARTAGENA', 'MURCIA', 37.6017, -1.0017)),
    ('MANDARACHE', 'SANTA ANA', ('CARTAGENA', 'MURCIA', 37.6017, -1.0017)),
    ('MANDARACHE', 'CARTAGENA', ('CARTAGENA', 'MURCIA', 37.6017, -1.0017)),
    ('TRIALHAMA', '', ('ALHAMA DE MURCIA', 'MURCIA', 37.8508, -1.4267)),
    # Andalucia
    ('ALCORES', '', ('ALCALÁ DE GUADAÍRA', 'SEVILLA', 37.3378, -5.8442)),
    ('JEREZANA', '', ('JEREZ DE LA FRONTERA', 'CÁDIZ', 36.6817, -6.1378)),
    # Aragón
    ('ZARATECNO', '', ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891)),
    ('HELIOS', 'JAB', ('ZARAGOZA', 'ZARAGOZA', 41.6488, -0.8891)),
    ('OSCENSE', '', ('HUESCA', 'HUESCA', 42.1401, -0.4089)),
    # CLM
    ('FUENSALIDA', '', ('FUENSALIDA', 'TOLEDO', 39.9275, -4.3283)),
    ('TRISAGRA', '', ('OLÍAS DEL REY', 'TOLEDO', 39.9328, -3.9911)),
    ('TARANCON', '', ('TARANCÓN', 'CUENCA', 40.0128, -3.0053)),
    # Extremadura
    ('CAPEX', '', ('VILLAFRANCA DE LOS BARROS', 'BADAJOZ', 38.5667, -6.3333)),
    # Canarias
    ('TRIMEDANO', '', ('EL MÉDANO', 'SANTA CRUZ DE TENERIFE', 28.0447, -16.5358)),
    ('FUERTRI', '', ('PUERTO DEL ROSARIO', 'LAS PALMAS', 28.5004, -13.8627)),
    # Baleares
    ('BALEAR', 'XTREM', ('CALVIÀ', 'BALEARES', 39.5653, 2.5067)),
    ('PALMARUNNERS', '', ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502)),
    ('ESPALMADOR', '', ('FORMENTERA', 'BALEARES', 38.7068, 1.4342)),
    ('SA POBLA', '', ('SA POBLA', 'BALEARES', 39.7622, 3.0203)),
    ('SON SERVERA', '', ('SON SERVERA', 'BALEARES', 39.6258, 3.3861)),
    ('MARATHON', 'MALLORCA', ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502)),
    ('IBIZA', '', ('IBIZA', 'BALEARES', 38.9067, 1.4206)),
    # Castilla y León
    ('TRAGALEGUAS', 'BURGOS', ('BURGOS', 'BURGOS', 42.3439, -3.6969)),
    # La Rioja
    ('ENTRENO LR', '', ('LOGROÑO', 'LA RIOJA', 42.4627, -2.445)),
    # Ceuta
    ('TRIATLON CEUTA', '', ('CEUTA', 'CEUTA', 35.8894, -5.3198)),
    # Lanzarote
    ('TRIYAIZA', '', ('YAIZA', 'LAS PALMAS', 28.9528, -13.7647)),
    # Misc identifiable
    ('UNIVERSITAT POLITECNICA', 'VALENCIA', ('VALENCIA', 'VALENCIA', 39.4799, -0.3405)),
    ('EL CID', 'TRIATLON', ('VALENCIA', 'VALENCIA', 39.4699, -0.3763)),
    ('TRIDAN', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('TRIFLAVI', '', ('AVILÉS', 'ASTURIAS', 43.5558, -5.9248)),
    ('TRIBOOST', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('TRIACADEMY', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('CANDETLON', '', ('PRAVIA', 'ASTURIAS', 43.4917, -6.1042)),
    ('TRIATOR', '', ('TORRELAVEGA', 'CANTABRIA', 43.3487, -4.0515)),
    ('FUENSANTA', 'IMPULSO', ('FUENSANTA', 'ALBACETE', 39.0, -2.07)),
    ('SABADELL', 'TRIATLO', ('SABADELL', 'BARCELONA', 41.5463, 2.1079)),
    ('ALMAZORA', '', ('ALMASSORA', 'CASTELLÓN', 39.9469, -0.0608)),
    ('K1T', 'TRIATL', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('NOSPORTLIMIT', '', ('PALMA DE MALLORCA', 'BALEARES', 39.5696, 2.6502)),
    ('TRIASPE', '', ('ALICANTE', 'ALICANTE', 38.3452, -0.4810)),
    ('AGUAVERDE', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('TRIATLONCIEM', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
    ('TRIGLOBEROS', '', ('MADRID', 'MADRID', 40.4168, -3.7038)),
]

def main():
    print("=" * 70)
    print("  CORRECCIÓN FLEXIBLE DE CLUBES (sin acentos)")
    print("=" * 70)

    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    df = pd.read_csv(CSV_CLUBES, encoding='utf-8')
    updated = 0

    for idx, row in df.iterrows():
        if row['provincia'] != 'DESCONOCIDA':
            continue
        club = str(row['club']).strip()
        club_norm = strip_accents(club)

        for kw1, kw2, (ciudad, provincia, lat, lng) in KEYWORD_MAP:
            kw1_norm = strip_accents(kw1)
            kw2_norm = strip_accents(kw2) if kw2 else ''

            if kw1_norm in club_norm:
                if kw2_norm == '' or kw2_norm in club_norm:
                    df.at[idx, 'lat'] = lat
                    df.at[idx, 'lng'] = lng
                    df.at[idx, 'ciudad_sede'] = ciudad
                    df.at[idx, 'provincia'] = provincia
                    # Also save to cache
                    cache[club.upper()] = {'lat': lat, 'lng': lng, 'ciudad': ciudad, 'provincia': provincia}
                    updated += 1
                    print(f"  [FIX] {club[:45]:<45} -> {ciudad} ({provincia})")
                    break

    # Save
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    df.to_csv(CSV_CLUBES, index=False, encoding='utf-8')

    desconocidos = len(df[df['provincia'] == 'DESCONOCIDA'])
    resueltos = len(df[df['provincia'] != 'DESCONOCIDA'])
    print(f"\nClubs actualizados: {updated}")
    print(f"Provincias resueltas: {resueltos}/{len(df)}")
    print(f"Aún desconocidos: {desconocidos}/{len(df)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
