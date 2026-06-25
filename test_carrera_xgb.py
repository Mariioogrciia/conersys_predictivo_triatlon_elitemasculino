import pandas as pd
import joblib

def test_model_xgb():
    print("1. Cargando el modelo XGBoost local...")
    try:
        model_dict = joblib.load('models/model_local.pkl')
        model = model_dict['model']
        feature_cols = model_dict['feature_cols']
        print("Modelo cargado correctamente.")
    except Exception as e:
        print("Error cargando el modelo XGBoost:", e)
        return

    print("2. Cargando el dataset procesado...")
    df = pd.read_csv(r'data\processed\trm_2025_azure_automl.csv')

    # Seleccionamos una prueba al azar que tenga bastantes participantes
    carreras = df['PRUEBA_ID'].value_counts()
    carrera_test = carreras.index[0]
    print(f"3. Seleccionando la prueba ID: {carrera_test} ({carreras.iloc[0]} participantes)")

    # Filtramos los atletas de esa carrera
    df_carrera = df[df['PRUEBA_ID'] == carrera_test].copy()
    
    # Nos guardamos la posición real para comparar (PUESTO_TARGET)
    resultados_reales = df_carrera[['ATLETA_ID_HASH', 'PUESTO_TARGET']].copy()
    
    # Seleccionamos exactamente las columnas que el modelo XGBoost espera
    # Rellenamos posibles nulos con 0 por si acaso
    X_test = df_carrera[feature_cols].fillna(0).copy()

    print("4. Realizando predicciones...")
    try:
        predicciones = model.predict(X_test)
    except Exception as e:
        print("Error al predecir:", e)
        return

    # Juntamos los resultados
    resultados_reales['prediccion_modelo'] = predicciones
    
    # IMPORTANTE: El modelo está prediciendo "PUNTOS", no "Posición". 
    # Quien tiene más puntos es el que gana. Ordenamos de MAYOR a MENOR.
    resultados_ordenados = resultados_reales.sort_values(by='prediccion_modelo', ascending=False)
    
    # Ranking Relativo 1, 2, 3...
    resultados_ordenados['ranking_predicho'] = range(1, len(resultados_ordenados) + 1)
    
    # Ordenar por PUESTO_TARGET real para ver cómo los colocó el modelo
    print("\n--- RESULTADOS DEL TOP 15 REAL Y DÓNDE LOS PREDIJO EL MODELO ---")
    resultados_finales = resultados_ordenados.sort_values(by='PUESTO_TARGET')
    print(resultados_finales[['ATLETA_ID_HASH', 'PUESTO_TARGET', 'ranking_predicho', 'prediccion_modelo']].head(15).to_string(index=False))

if __name__ == "__main__":
    test_model_xgb()
