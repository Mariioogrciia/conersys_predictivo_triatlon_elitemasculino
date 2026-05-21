# 🏊🚴🏃 Predictivo Triatlón Élite Masculino
### Conersys · TFM Máster IA · Tajamar Tech 2025-26
 
> **Mario García · Alejandro Benítez**
 
Pipeline de ingeniería de datos y modelo predictivo de rendimiento para el **Triatlón de Rango Mundial Masculino (TRM 2025)**, desplegado íntegramente en **Microsoft Azure**.
 
---
 
## 🗺️ Índice rápido — ¿dónde está cada cosa?
 
| Quiero... | Voy a... |
|---|---|
| Entender el proyecto desde cero | [📄 Contexto del proyecto](docs/CONTEXTO_PROYECTO.md) |
| Ver qué datos manejamos | [📋 Lista de ficheros Excel](docs/lista_todos_los_excel.md) |
| Ver o modificar el esquema de base de datos | [🗄️ Schema SQL](database/azure_sql_schema.sql) |
| Cargar datos en Azure SQL | [⬆️ Script de carga](database/load_to_azure_sql.py) |
| Ejecutar el pipeline ETL completo | [🔧 ml_pipeline/](ml_pipeline/) |
| Ver el plan de sprints y tareas | [📅 sprints/](sprints/) |
 
---
 
## 📁 Estructura del repositorio
 
```
conersys_predictivo_triatlon_elitemasculino/
│
├── 📂 database/                  # Base de datos Azure SQL
│   ├── azure_sql_schema.sql      # Esquema de tablas (atletas, pruebas, resultados)
│   └── load_to_azure_sql.py      # Script para cargar los datos limpios
│
├── 📂 docs/                      # Documentación del proyecto
│   ├── CONTEXTO_PROYECTO.md      # Descripción completa del problema y solución
│   └── lista_todos_los_excel.md  # Inventario de ficheros de datos del cliente
│
├── 📂 ml_pipeline/               # Pipeline de datos y modelo ML
│   ├── generate_normalized_datasets...  # Generación de datasets normalizados
│   ├── geocode_clubs.py          # Geocodificación de clubes
│   ├── importacion_y_limpieza.ipynb     # ETL principal (notebook)
│   └── prepare_azure_automl_data...     # Preparación datos para AutoML
│
├── 📂 sprints/                   # Planificación y documentación ágil
│   ├── sprint1.md                # ETL y datos
│   ├── sprint2.md                # Modelo ML
│   ├── sprint3.md                # API y Chatbot
│   ├── sprint4.md                # Dashboard y entrega
│   └── img/                     # Diagramas y esquemas visuales
│
└── README.md                     # Este archivo
```
 
---
 
## 🏗️ Arquitectura de la solución
 
La solución se divide en **4 capas** desplegadas en Azure:
 
```
┌─────────────────────────────────────────────────────────┐
│  CAPA 1 · DATOS                                         │
│  Blob Storage (raw) → Azure SQL Database → Redis Cache  │
├─────────────────────────────────────────────────────────┤
│  CAPA 2 · MACHINE LEARNING  (Azure ML)                  │
│  ML Notebooks → ML Model Registry → ML Online Endpoint  │
├─────────────────────────────────────────────────────────┤
│  CAPA 3 · BACKEND                                       │
│  Container Apps (FastAPI) + Azure OpenAI (GPT-4o)       │
├─────────────────────────────────────────────────────────┤
│  CAPA 4 · FRONTEND + CI/CD                              │
│  Static Web Apps (Blazor WASM) + GitHub Actions         │
└─────────────────────────────────────────────────────────┘
```
 
---
 
## 📅 Estado del proyecto por sprint
 
| Sprint | Qué hace | Fechas | Estado |
|---|---|---|---|
| [Sprint 1 →](sprints/sprint1.md) | ETL, limpieza y enriquecimiento de datos | 07/04 – 04/05 | 🟡 En curso |
| [Sprint 2 →](sprints/sprint2.md) | Entrenamiento del modelo predictivo (AutoML) | 04/05 – 18/05 | ⚪ Pendiente |
| [Sprint 3 →](sprints/sprint3.md) | API REST + Chatbot con Azure OpenAI | 18/05 – 01/06 | ⚪ Pendiente |
| [Sprint 4 →](sprints/sprint4.md) | Dashboard Blazor + integración final | 01/06 – 22/06 | ⚪ Pendiente |
 
> Actualiza los emojis de estado conforme avancéis: 🟡 En curso · ✅ Completado · 🔴 Bloqueado · ⚪ Pendiente
 
---
 
## ⚡ Cómo empezar a trabajar
 
### 1. Clonar el repositorio
```bash
git clone https://github.com/Mariioograciia/conersys_predictivo_triatlon_elitemasculino.git
cd conersys_predictivo_triatlon_elitemasculino
```
 
### 2. Instalar dependencias Python
```bash
pip install pandas numpy scikit-learn xgboost shap pyodbc azure-storage-blob python-dotenv
```
 
### 3. Configurar credenciales Azure
Crea un fichero `.env` en la raíz (nunca lo subas a GitHub — ya está en `.gitignore`):
```
AZURE_SQL_SERVER=tu-servidor.database.windows.net
AZURE_SQL_DATABASE=tu-base-de-datos
AZURE_SQL_USER=tu-usuario
AZURE_SQL_PASSWORD=tu-contraseña
AZURE_BLOB_CONNECTION_STRING=tu-cadena-de-conexion
```
 
### 4. Ejecutar el pipeline ETL
```bash
# Abrir en Jupyter o Azure ML Notebooks
ml_pipeline/importacion_y_limpieza.ipynb
```
 
---
 
## 🎯 Qué predice el modelo
 
Dado un **atleta** y una **prueba**, el sistema devuelve:
 
- ⏱️ **Tiempo final esperado** (ej: `1h 44m 32s`)
- 📊 **Intervalo de confianza al 90%**
- 🔍 **Top 3 factores más influyentes** (via SHAP):
  - *"Temperatura +8°C sobre su media habitual → +45s"*
  - *"Altitud elevada → +30s"*
  - *"Solo 3 días de descanso → +20s"*
- ⚠️ **Riesgo de descalificación** (si hay datos suficientes)
---
 
## 📊 Datos del proyecto
 
| Fuente | Contenido | Formato |
|---|---|---|
| Cliente Conersys | Rankings TRM históricos | Excel |
| Cliente Conersys | Resultados por campeonato | JSON |
| Open-Meteo API | Meteorología histórica por prueba | API REST |
| World Triathlon | Características de circuitos | Web scraping / manual |
 
Las variables originales de "nombre de carrera" se transforman en variables numéricas (altitud, temperatura, humedad, desnivel, tipo de agua) antes de entrar al modelo. Ver [Sprint 1](sprints/sprint1.md) para el detalle.
 
---
 
## 🛠️ Stack tecnológico
 
| Área | Tecnología |
|---|---|
| Lenguaje principal | Python 3.11 |
| ETL y análisis | pandas · numpy · Jupyter |
| Machine Learning | Azure AutoML · scikit-learn · XGBoost · SHAP |
| Base de datos | Azure SQL Database |
| Almacenamiento | Azure Blob Storage (LRS) |
| Modelo en producción | Azure ML Online Endpoint |
| API backend | FastAPI · Azure Container Apps |
| Chatbot | Azure OpenAI (GPT-4o) |
| Frontend | Blazor WebAssembly (.NET 8) |
| CI/CD | GitHub Actions |
| Secretos | Azure Key Vault |
 
---
 
## 👥 Equipo
 
| Rol | Persona |
|---|---|
| Desarrolladores | Mario García · Alejandro Benítez |
| Product Owner | Miguel Ángel Pablo Lope |
| Scrum Master | José Antonio Ureta Santacreu |
| Institución | Tajamar Tech · Máster IA 2025-26 |
