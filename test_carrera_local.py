import pandas as pd
import joblib

def test_model():
    print("1. Cargando el modelo...")
    try:
        model_dict = joblib.load('models/model_local.pkl')
        model = model_dict['model']
        feature_cols = model_dict['feature_cols']
    except Exception as e:
        print("Error cargando el modelo:", e)
        return

    print("2. Cargando el dataset de entrenamiento...")
    df = pd.read_csv(r'data\raw\elite_masculina_triatlon\dataset\dataset_automl_entrenamiento.csv')

    # Seleccionamos una carrera al azar que tenga bastantes participantes
    carreras = df['race_event_desc'].value_counts()
    carrera_test = carreras.index[0] # Cogemos la carrera con más participantes en el dataset
    print(f"3. Seleccionando la carrera de prueba: {carrera_test}")

    # Filtramos los atletas que participaron en esa carrera
    df_carrera = df[df['race_event_desc'] == carrera_test].copy()
    
    # Nos guardamos la posición real para comparar luego
    resultados_reales = df_carrera[['athlete_name', 'finish_position'] if 'athlete_name' in df.columns else ['finish_position']].copy()
    
    # Seleccionamos exactamente las columnas con las que el modelo fue entrenado
    # Aseguramos de imputar posibles nulos si no estuvieran tratados (aunque dataset_automl_entrenamiento debería estar limpio)
    X_test = df_carrera[feature_cols].copy()

    print("4. Realizando predicciones...")
    try:
        predicciones = model.predict(X_test)
    except Exception as e:
        print("Error al predecir. Es posible que el modelo espere otras columnas o requiera pre-procesamiento:", e)
        return

    # Juntamos los resultados
    resultados_reales['prediccion_modelo'] = predicciones
    
    # Hacemos el truco del "Ranking Relativo"
    # Ordenamos a los atletas según lo que predijo el modelo (de menor número a mayor)
    resultados_ordenados = resultados_reales.sort_values(by='prediccion_modelo')
    
    # Les asignamos la nueva posición 1, 2, 3... según ese orden
    resultados_ordenados['ranking_relativo_predicho'] = range(1, len(resultados_ordenados) + 1)
    
    print("\n--- RESULTADOS DE LA PRUEBA (Top 10 Predicho) ---")
    print(resultados_ordenados[['finish_position', 'prediccion_modelo', 'ranking_relativo_predicho']].head(10).to_string(index=False))

if __name__ == "__main__":
    test_model()
