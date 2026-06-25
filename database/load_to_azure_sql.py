# ============================================================================
# SCRIPT DE CARGA DE DATOS A AZURE SQL DATABASE - TFM TRIATLÓN (FETRI)
# ============================================================================
# Requisitos: 
# pip install pandas sqlalchemy pyodbc

import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# 1. Configuración de Conexión a Azure SQL Database
# Reemplaza con tus credenciales de Azure
AZURE_SERVER = os.getenv("AZURE_SERVER", "tu-servidor.database.windows.net")
AZURE_DB = os.getenv("AZURE_DB", "tu-base-de-datos")
AZURE_USER = os.getenv("AZURE_USER", "tu-usuario")
AZURE_PASSWORD = os.getenv("AZURE_PASSWORD", "tu-contraseña")

# Limpiar comillas literales que puedan venir del archivo .env
if AZURE_SERVER: AZURE_SERVER = AZURE_SERVER.replace('"', '').replace("'", "")
if AZURE_DB: AZURE_DB = AZURE_DB.replace('"', '').replace("'", "")
if AZURE_USER: AZURE_USER = AZURE_USER.replace('"', '').replace("'", "")
if AZURE_PASSWORD: AZURE_PASSWORD = AZURE_PASSWORD.replace('"', '').replace("'", "")

# Rutas de los CSVs generados en tu máquina local
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CLUBES = os.path.join(WORKSPACE, "data", "processed", "clubes_geo_2025.csv")
CSV_DEPORTISTAS = os.path.join(WORKSPACE, "data", "processed", "deportistas_2025.csv")
CSV_PRUEBAS = os.path.join(WORKSPACE, "data", "processed", "pruebas_2025.csv")
CSV_RESULTADOS = os.path.join(WORKSPACE, "data", "processed", "resultados_2025.csv")

MISSING_TOKENS = {'NAN', 'NONE', 'NULL', ''}


def normalize_missing_strings(series):
    normalized = series.astype('string').str.strip()
    return normalized.mask(normalized.str.upper().isin(MISSING_TOKENS))

def connect_and_load():
    print("Iniciando proceso de carga a Azure SQL Database...")
    
    # Comprobar que los archivos existen
    for path, name in [(CSV_CLUBES, "Clubes"), (CSV_DEPORTISTAS, "Deportistas"), 
                       (CSV_PRUEBAS, "Pruebas"), (CSV_RESULTADOS, "Resultados")]:
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo CSV de {name} en: {path}")
            print("Por favor, ejecuta primero 'ml_pipeline/generate_normalized_datasets.py' para crearlos.")
            return

    # Validar credenciales por defecto antes de continuar
    if "tu-" in AZURE_SERVER or "tu-" in AZURE_DB:
        print("\n[ATENCIÓN] Configuración requerida:")
        print("Por favor, abre este script ('database/load_to_azure_sql.py') y edita las líneas 14-17")
        print("con los datos de tu servidor de Azure SQL Database antes de ejecutarlo.")
        return

    # Crear la cadena de conexión para SQLAlchemy usando el driver ODBC de SQL Server
    # Nota: Azure SQL requiere cifrado (Encrypt=yes)
    connection_string = (
        f"mssql+pyodbc://{AZURE_USER}:{AZURE_PASSWORD}@{AZURE_SERVER}/{AZURE_DB}"
        "?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
    )
    
    try:
        print("Estableciendo conexión segura con Azure SQL Database...")
        engine = create_engine(connection_string, fast_executemany=True)
        
        # 0. Limpiar tablas existentes para evitar conflictos
        print("\n[0/5] Limpiando base de datos...")
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("IF OBJECT_ID('dbo.resultados', 'U') IS NOT NULL DROP TABLE dbo.resultados;"))
            conn.execute(text("IF OBJECT_ID('dbo.pruebas', 'U') IS NOT NULL DROP TABLE dbo.pruebas;"))
            conn.execute(text("IF OBJECT_ID('dbo.deportistas', 'U') IS NOT NULL DROP TABLE dbo.deportistas;"))
            conn.execute(text("IF OBJECT_ID('dbo.clubes_geo', 'U') IS NOT NULL DROP TABLE dbo.clubes_geo;"))
            conn.execute(text("IF OBJECT_ID('dbo.dataset_entrenamiento', 'U') IS NOT NULL DROP TABLE dbo.dataset_entrenamiento;"))
        print("-> ¡Tablas limpiadas!")

        # 1. Cargar Dataset Entrenamiento Azure AutoML
        print("\n[1/5] Cargando Dataset Entrenamiento Azure AutoML...")
        CSV_AUTOML = os.path.join(WORKSPACE, "data", "raw", "elite_masculina_triatlon", "dataset", "dataset_automl_entrenamiento.csv")
        if os.path.exists(CSV_AUTOML):
            df_automl = pd.read_csv(CSV_AUTOML)
            df_automl.to_sql('dataset_entrenamiento', con=engine, if_exists='replace', index=False, schema='dbo')
            print(f"-> ¡Éxito! {len(df_automl)} filas cargadas en 'dbo.dataset_entrenamiento'.")
        else:
            print("-> Aviso: No se encontró el dataset de AutoML.")
        
        # 2. Cargar Clubes (Debe ser primero por restricción de FK)
        print("\n[2/5] Cargando Clubes Geocodificados...")
        df_clubes = pd.read_csv(CSV_CLUBES)
        # Limpieza de nulos si existieran
        df_clubes['club'] = normalize_missing_strings(df_clubes['club'].astype(str).str.strip())
        df_clubes['ciudad_sede'] = normalize_missing_strings(df_clubes['ciudad_sede'].astype(str).str.strip())
        df_clubes['provincia'] = normalize_missing_strings(df_clubes['provincia'].astype(str).str.strip())
        df_clubes = df_clubes.dropna(subset=['club'])
        df_clubes.to_sql('clubes_geo', con=engine, if_exists='replace', index=False, schema='dbo')
        print(f"-> ¡Éxito! {len(df_clubes)} clubes cargados en 'dbo.clubes_geo'.")
        
        # 3. Cargar Deportistas
        print("\n[3/5] Cargando Deportistas...")
        df_deportistas = pd.read_csv(CSV_DEPORTISTAS)
        df_deportistas.columns = [c.lower() for c in df_deportistas.columns]
        for col in ['documento', 'nombre', 'club', 'ggee']:
            df_deportistas[col] = normalize_missing_strings(df_deportistas[col].astype(str).str.strip())
        df_deportistas = df_deportistas.dropna(subset=['documento'])
        # Reemplazar nulos en Club por None (NULL en SQL) para evitar romper la FK
        df_deportistas['club'] = df_deportistas['club'].replace({np.nan: None})
        df_deportistas['ggee'] = df_deportistas['ggee'].replace({np.nan: "ABSOLUTO"})
        
        # Filtrar atletas cuyos clubes no estén en la tabla de clubes_geo por seguridad relacional
        valid_clubs = set(df_clubes['club'])
        df_deportistas['club'] = df_deportistas['club'].apply(lambda x: x if x in valid_clubs else None)
        
        df_deportistas.to_sql('deportistas', con=engine, if_exists='replace', index=False, schema='dbo')
        print(f"-> ¡Éxito! {len(df_deportistas)} deportistas cargados en 'dbo.deportistas'.")
        
        # 4. Cargar Pruebas
        print("\n[4/5] Cargando Pruebas (Campeonatos)...")
        df_pruebas = pd.read_csv(CSV_PRUEBAS)
        df_pruebas = df_pruebas.dropna(subset=['id'])
        df_pruebas.to_sql('pruebas', con=engine, if_exists='replace', index=False, schema='dbo')
        print(f"-> ¡Éxito! {len(df_pruebas)} pruebas cargadas en 'dbo.pruebas'.")
        
        # 5. Cargar Resultados (Tabla de Hechos Central)
        print("\n[5/5] Cargando Resultados (Tabla de Hechos)...")
        df_resultados = pd.read_csv(CSV_RESULTADOS)
        
        # Validaciones de integridad referencial locales antes de subir a Azure
        valid_atletas = set(df_deportistas['documento'])
        valid_pruebas = set(df_pruebas['id'])
        
        initial_count = len(df_resultados)
        df_resultados = df_resultados[
            df_resultados['deportista_documento'].isin(valid_atletas) & 
            df_resultados['prueba_id'].isin(valid_pruebas)
        ]
        filtered_count = len(df_resultados)
        if initial_count != filtered_count:
            print(f"   [Aviso] Se omitieron {initial_count - filtered_count} filas de resultados para mantener la integridad referencial.")
            
        df_resultados.to_sql('resultados', con=engine, if_exists='replace', index=False, schema='dbo')
        print(f"-> ¡Éxito! {len(df_resultados)} participaciones cargadas en 'dbo.resultados'.")
        
        print("\n=========================================================================")
        print("¡TODOS LOS DATASETS SE HAN SUBIDO CORRECTAMENTE A AZURE SQL DATABASE!")
        print("=========================================================================")
        
    except Exception as e:
        print("\nError durante la conexión o inserción en Azure SQL Database:")
        print(str(e))
        print("\nConsejos de resolución:")
        print("1. Verifica que tu IP local esté habilitada en el Firewall de tu Azure SQL Server.")
        print("2. Asegúrate de tener instalado el driver de SQL Server (ODBC Driver 17 or 18).")
        print("3. Comprueba el nombre de servidor, base de datos, usuario y contraseña.")

if __name__ == "__main__":
    connect_and_load()
