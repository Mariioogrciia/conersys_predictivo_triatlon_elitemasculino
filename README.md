# 🏊🚴🏃 Predictivo Triatlón Élite Masculino
**Conersys · TFM Máster IA · Tajamar Tech 2025-26**
Mario García · Alejandro Benítez
 
---
 
## 🟡 Sprint actual — Sprint 1: ETL y datos
 📋 **Detalle completo del sprint → [sprints/sprint1.md](sprints/sprint1.md)**

> **18/05/2026 → 25/05/2026**
 
**Objetivo:** Tener los datos limpios, enriquecidos y cargados en Azure antes de tocar ningún modelo.
 
### ¿En qué estamos ahora mismo?
 
| Tarea | Responsable | Estado |
|---|---|---|
| Carga CSV bruto a Blob Storage | Mario | ✅ Hecho |
| Notebook EDA (exploración inicial) | Alejandro | 🟡 En curso |
| Limpieza de nulos y outliers | Mario | ⚪ Pendiente |
| Enriquecimiento (altitud, temp, desnivel) | Alejandro | ⚪ Pendiente |
| Carga a Azure SQL Database | Ambos | ⚪ Pendiente |
| Identificar registros DSQ/DNF | Ambos | ⚪ Pendiente |

> **Estados:** ✅ Hecho · 🟡 En curso · ⚪ Pendiente · 🔴 AVISAR YA
 
---
 
## 🗺️ Índice rápido
 
| Quiero... | Voy a... |
|---|---|
| Entender el proyecto desde cero | [📄 docs/CONTEXTO_PROYECTO.md](docs/CONTEXTO_PROYECTO.md) |
| Ver qué ficheros de datos tenemos | [📋 docs/lista_todos_los_excel.md](docs/lista_todos_los_excel.md) |
| Ver o tocar el esquema de base de datos | [🗄️ database/azure_sql_schema.sql](database/azure_sql_schema.sql) |
| Cargar datos en Azure SQL | [⬆️ database/load_to_azure_sql.py](database/load_to_azure_sql.py) |
| Ejecutar el ETL | [🔧 ml_pipeline/importacion_y_limpieza.ipynb](ml_pipeline/importacion_y_limpieza.ipynb) |
| Preparar datos para AutoML | [🤖 ml_pipeline/prepare_azure_automl_data...](ml_pipeline/) |
| Ver la planificación completa | [📅 sprints/](sprints/) |
 
---
 
## 📅 Todos los sprints
 
| Sprint | Qué hace | Fechas | Estado |
|---|---|---|---|
| [📁 Sprint 1](sprints/sprint1.md) | ETL, limpieza y enriquecimiento de datos | 07/04 – 04/05 | 🟡 En curso |
| [📁 Sprint 2](sprints/sprint2.md) | Entrenamiento del modelo predictivo (AutoML) | 04/05 – 18/05 | ⚪ Pendiente |
| [📁 Sprint 3](sprints/sprint3.md) | API REST + Chatbot con Azure OpenAI | 18/05 – 01/06 | ⚪ Pendiente |
| [📁 Sprint 4](sprints/sprint4.md) | Dashboard Blazor + integración final | 01/06 – 22/06 | ⚪ Pendiente |
 
> **Estados:** ✅ Completado · 🟡 En curso · 🔴 Bloqueado · ⚪ Pendiente
 
---
 
## 🏗️ Arquitectura de la solución
 
```
┌──────────────────────────────────────────────────────────────┐
│  CAPA 1 · DATOS                                              │
│  Blob Storage (raw/) ──► Azure SQL Database ──► Redis Cache  │
├──────────────────────────────────────────────────────────────┤
│  CAPA 2 · MACHINE LEARNING  (Azure ML)                       │
│  ML Notebooks ──► ML Model Registry ──► ML Online Endpoint   │
├──────────────────────────────────────────────────────────────┤
│  CAPA 3 · BACKEND                                            │
│  Container Apps (FastAPI)  +  Azure OpenAI (GPT-4o Chatbot)  │
├──────────────────────────────────────────────────────────────┤
│  CAPA 4 · FRONTEND + CI/CD                                   │
│  Static Web Apps (Blazor WASM)  +  GitHub Actions            │
└──────────────────────────────────────────────────────────────┘
```
 
> Las capas 3 y 4 se construyen en los Sprints 3 y 4. De momento el foco está en las capas 1 y 2.
 
---
 
## 🛠️ Cómo trabajar con el proyecto
 
### Configurar el entorno por primera vez
 
**1. Clonar el repo**
```bash
git clone https://github.com/Mariioograciia/conersys_predictivo_triatlon_elitemasculino.git
cd conersys_predictivo_triatlon_elitemasculino
```
 
**2. Instalar dependencias**
```bash
pip install pandas numpy scikit-learn xgboost shap pyodbc azure-storage-blob python-dotenv
```
 
**3. Crear el fichero `.env`** en la raíz del proyecto (nunca se sube a GitHub, ya está en `.gitignore`)
```
AZURE_SQL_SERVER=tu-servidor.database.windows.net
AZURE_SQL_DATABASE=conersys-triatlon
AZURE_SQL_USER=tu-usuario
AZURE_SQL_PASSWORD=tu-contraseña
AZURE_BLOB_CONNECTION_STRING=tu-cadena-de-conexion
```
> Las credenciales reales están en el canal de Teams del proyecto.
 
---
 
### Flujo de trabajo diario
 
```
1. git pull                        ← Siempre primero, para estar al día
2. Trabajar en tu rama             ← Nunca directamente en main
3. git add · git commit · git push ← Commits pequeños y descriptivos
4. Pull Request a main             ← El otro lo revisa antes de mergear
```
 
**Nombrado de ramas:**
```
sprint1/etl-limpieza-nulos
sprint1/enriquecimiento-pruebas
sprint2/feature-engineering
```
 
**Formato de commits:**
```
feat: añadir limpieza de outliers en tiempos finales
fix: corregir join entre atletas y pruebas en el ETL
docs: actualizar sprint1.md con tareas completadas
```
 
---
 
### Ejecutar el pipeline ETL (Sprint 1)
 
```bash
# Opción A: Jupyter local
jupyter notebook ml_pipeline/importacion_y_limpieza.ipynb
 
# Opción B: Azure ML Notebooks (recomendado)
# Subir el notebook desde Azure ML Studio > Notebooks > ml_pipeline/
```
 
---
 
### Cargar datos a Azure SQL
 
```bash
python database/load_to_azure_sql.py
```
> Requiere el `.env` configurado y que el schema ya esté creado (`azure_sql_schema.sql`).
 
---
 
## 📁 Estructura del repositorio
 
```
conersys_predictivo_triatlon_elitemasculino/
│
├── 📂 database/
│   ├── azure_sql_schema.sql          # Esquema de tablas: atletas, pruebas, resultados
│   └── load_to_azure_sql.py          # Carga los datos procesados a Azure SQL
│
├── 📂 docs/
│   ├── CONTEXTO_PROYECTO.md          # Descripción del problema y decisiones clave
│   └── lista_todos_los_excel.md      # Inventario de ficheros del cliente
│
├── 📂 ml_pipeline/
│   ├── importacion_y_limpieza.ipynb  # ETL principal — empezar aquí
│   ├── generate_normalized_datasets  # Genera datasets normalizados para el modelo
│   ├── geocode_clubs.py              # Geocodificación de clubes
│   └── prepare_azure_automl_data     # Prepara los datos para Azure AutoML
│
├── 📂 sprints/# 🏊🚴🏃 Predictivo Triatlón Élite Masculino.
 
Entrega final: 22/06/2026*
