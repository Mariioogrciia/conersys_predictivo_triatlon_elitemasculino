import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

def train_anomaly_detector():
    print("Iniciando entrenamiento del detector de anomalías (Isolation Forest)...")
    
    # Rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "dataset_automl_entrenamiento (1).csv")
    model_dir = os.path.join(base_dir, "models")
    model_path = os.path.join(model_dir, "model_anomaly.pkl")
    
    os.makedirs(model_dir, exist_ok=True)
    
    # Cargar datos
    if not os.path.exists(dataset_path):
        print(f"ERROR: No se encuentra el dataset en {dataset_path}")
        return
        
    df = pd.read_csv(dataset_path)
    print(f"Dataset cargado con {len(df)} registros.")
    
    # Seleccionar solo columnas numéricas para Isolation Forest
    # Ignorar target y columnas categóricas puras o IDs
    cols_to_drop = ['finish_position', 'athlete_club', 'athlete_federation', 'race_city', 'race_event_desc', 'race_phase', 'race_climate_type', 'race_type']
    
    X = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    X = X.select_dtypes(include=['float64', 'int64'])
    
    # Rellenar nulos con la media temporalmente para que IF no falle
    X = X.fillna(X.mean())
    
    # Entrenar Isolation Forest
    # Asumimos que aproximadamente el 5% de los casos pueden ser DSQ/anómalos
    clf = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )
    
    print("Entrenando modelo...")
    clf.fit(X)
    
    # Guardar el modelo y la lista de features que espera
    anomaly_model = {
        "model": clf,
        "features": X.columns.tolist()
    }
    
    joblib.dump(anomaly_model, model_path)
    print(f"Modelo guardado exitosamente en: {model_path}")
    
    # Prueba rápida
    predictions = clf.predict(X)
    anomalies = (predictions == -1).sum()
    print(f"Prueba finalizada: Detectados {anomalies} casos anómalos ({anomalies/len(df)*100:.1f}%) en el set de entrenamiento.")

if __name__ == "__main__":
    train_anomaly_detector()
