import os
import pandas as pd
import numpy as np
import hashlib
from datetime import datetime

# Configuración de rutas
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_DEPORTISTAS = os.path.join(WORKSPACE, "data", "processed", "deportistas_2025.csv")
IN_PRUEBAS = os.path.join(WORKSPACE, "data", "processed", "pruebas_2025.csv")
IN_CLUBES = os.path.join(WORKSPACE, "data", "processed", "clubes_geo_2025.csv")
IN_RESULTADOS = os.path.join(WORKSPACE, "data", "processed", "resultados_2025.csv")
OUTPUT_PATH = os.path.join(WORKSPACE, "data", "processed", "trm_2025_azure_automl.csv")

def calculate_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia Haversine en kilómetros entre dos coordenadas geográficas."""
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return 0.0
    if lat1 == 0.0 or lon1 == 0.0 or lat2 == 0.0 or lon2 == 0.0:
        return 0.0
    
    rlat1, rlon1 = np.radians(lat1), np.radians(lon1)
    rlat2, rlon2 = np.radians(lat2), np.radians(lon2)
    
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    
    a = np.sin(dlat/2)**2 + np.cos(rlat1) * np.cos(rlat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0 # Radio de la Tierra en km
    return c * r

def run():
    print("Iniciando la preparación del dataset de Triatlón Masculino 2025 para Azure AutoML (Sólo Elite)...")
    
    df_dep = pd.read_csv(IN_DEPORTISTAS)
    df_pru = pd.read_csv(IN_PRUEBAS)
    df_clu = pd.read_csv(IN_CLUBES)
    df_res = pd.read_csv(IN_RESULTADOS)
    
    # Joins iniciales
    df_res = df_res.merge(df_dep, left_on='deportista_documento', right_on='DOCUMENTO', how='inner')
    df_res = df_res.merge(df_pru, left_on='prueba_id', right_on='id', how='inner')
    df_res = df_res.merge(df_clu, left_on='CLUB', right_on='club', how='left')
    
    # Asegurar que está ordenado por fecha cronológicamente
    df_res = df_res.sort_values(by=['fecha', 'prueba_id', 'puesto']).reset_index(drop=True)
    
    historial_deportistas = {}
    historial_clubes = {} # Para el Club Power Score sin data leakage
    registros_finales = []
    fmt = "%Y-%m-%d"
    
    for _, row in df_res.iterrows():
        dni = str(row['DOCUMENTO']).strip()
        dni_hash = hashlib.sha256(dni.encode('utf-8')).hexdigest()[:16]
        club = str(row['CLUB']).strip()
        ggee = str(row['GGEE']).strip()
        puntos = float(row['puntos'])
        puesto = int(row['puesto'])
        fecha_carrera = str(row['fecha'])[:10]
        
        hist = historial_deportistas.get(dni, [])
        club_hist = historial_clubes.get(club, [])
        
        try:
            current_date = datetime.strptime(fecha_carrera, fmt)
        except:
            current_date = datetime(2025, 6, 1)
        
        # --- ROLLING FEATURES ATLETA (Momentum) ---
        if len(hist) > 0:
            hist_puntos = [x['puntos'] for x in hist]
            hist_avg = float(np.mean(hist_puntos))
            hist_std = float(np.std(hist_puntos)) if len(hist) > 1 else 0.0
            hist_max = float(np.max(hist_puntos))
            hist_count = len(hist)
            
            recent_3 = hist[-3:]
            recent_puntos = [x['puntos'] for x in recent_3]
            recent_avg = float(np.mean(recent_puntos))
            
            last_fecha_str = hist[-1]['fecha']
            try:
                d1 = datetime.strptime(last_fecha_str, fmt)
                days_since = (current_date - d1).days
                if days_since < 0: days_since = 0
            except:
                days_since = 30
                
            # Calcular fatiga (carreras en los últimos 30 días)
            races_last_30d = 0
            for x in hist:
                try:
                    d_hist = datetime.strptime(x['fecha'], fmt)
                    if 0 <= (current_date - d_hist).days <= 30:
                        races_last_30d += 1
                except:
                    pass
            fatigue_index = races_last_30d / (days_since + 1.0)
            
        else:
            hist_avg = 0.0
            hist_std = 0.0
            hist_max = 0.0
            hist_count = 0
            recent_avg = 0.0
            days_since = 365 # Default long rest
            fatigue_index = 0.0
            
        # --- ROLLING FEATURE CLUB (Target Encoding Dinámico) ---
        if len(club_hist) > 0:
            club_power_score = float(np.mean(club_hist))
        else:
            club_power_score = 0.0
            
        # --- GEOGRAFÍA Y CLIMA ---
        club_lat = float(row.get('lat_y', 40.4168)) if pd.notna(row.get('lat_y')) else 40.4168
        club_lng = float(row.get('lng_y', -3.7038)) if pd.notna(row.get('lng_y')) else -3.7038
        c_lat = float(row['lat_x'])
        c_lng = float(row['lng_x'])
        
        viaje_km = calculate_haversine(club_lat, club_lng, c_lat, c_lng)
        
        club_prov = str(row.get('provincia_y', 'DESCONOCIDA')).strip().upper()
        race_prov = str(row.get('provincia_x', 'DESCONOCIDA')).strip().upper()
        es_local = 1 if club_prov == race_prov and club_prov != 'DESCONOCIDA' else 0
        
        temp_max = float(row.get('temperatura_max', 20.0))
        precip = float(row.get('precipitacion', 0.0))
        
        # Flags extremos
        is_extreme_heat = 1 if temp_max > 30.0 else 0
        is_wet_race = 1 if precip > 0.0 else 0
        
        # Cíclicas del mes
        mes = current_date.month
        mes_sin = np.sin(2 * np.pi * mes / 12)
        mes_cos = np.cos(2 * np.pi * mes / 12)
            
        registros_finales.append({
            'ATLETA_ID_HASH': dni_hash,
            'CLUB': club,
            'GGEE': ggee,
            'PRUEBA_ID': int(row['prueba_id']),
            'CHAMPIONSHIP_LEVEL': row['championship_level'],
            'ALTITUD': float(row.get('altitud', 0.0)),
            'TEMPERATURA_MAX': temp_max,
            'HUMEDAD_MEDIA': float(row.get('humedad_media', 60.0)),
            'PRECIPITACION': precip,
            'VIENTO_MAX': float(row.get('viento_max', 10.0)),
            'IS_EXTREME_HEAT': is_extreme_heat,
            'IS_WET_RACE': is_wet_race,
            'VIAJE_DISTANCIA_KM': viaje_km,
            'ES_LOCAL': es_local,
            'MES_CARRERA': mes,
            'MES_SIN': mes_sin,
            'MES_COS': mes_cos,
            'DAYS_SINCE_LAST_RACE': days_since,
            'FATIGUE_INDEX': fatigue_index,
            'CLUB_POWER_SCORE': club_power_score,
            'RECENT_AVG_PUNTOS': recent_avg,
            'HIST_AVG_PUNTOS': hist_avg,
            'HIST_STD_PUNTOS': hist_std,
            'HIST_MAX_PUNTOS': hist_max,
            'HIST_COUNT_PRUEBAS': hist_count,
            'PUESTO_TARGET': puesto,
            'PUNTOS_TARGET': puntos
        })
        
        # Registrar para el siguiente ciclo cronológico (Atleta y Club)
        if dni not in historial_deportistas:
            historial_deportistas[dni] = []
        historial_deportistas[dni].append({'puntos': puntos, 'fecha': fecha_carrera})
        
        if club != 'SIN CLUB':
            if club not in historial_clubes:
                historial_clubes[club] = []
            historial_clubes[club].append(puntos)
        
    df_final = pd.DataFrame(registros_finales)
    print(f"\\nGeneradas {df_final.shape[0]} participaciones exclusivas de Élite con Advanced Features.")
    
    # Shuffle determinista
    df_final = df_final.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    print(f"Exportando dataset enriquecido a: {OUTPUT_PATH}")
    df_final.to_csv(OUTPUT_PATH, index=False, encoding='utf-8')
    print("¡DATASET GENERADO CON ÉXITO! Listo para Azure Machine Learning.")
    
    print("\\nResumen de Nuevas Variables:")
    print(df_final[['IS_EXTREME_HEAT', 'IS_WET_RACE', 'MES_SIN', 'MES_COS', 'FATIGUE_INDEX', 'CLUB_POWER_SCORE']].head(5).to_string())

if __name__ == '__main__':
    run()
