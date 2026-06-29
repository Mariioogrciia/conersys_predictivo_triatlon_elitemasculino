# 🏊🚴🏃 Predictivo Triatlón Élite Masculino
**Conersys · TFM Máster IA · Tajamar Tech 2025-26**
Mario García · Alejandro Benítez

---

## 🟢 Estado del Proyecto — Finalizado

> **Entrega final: 26/06/2026**

Sistema de predicción de rendimiento para triatlón élite masculino basado en inteligencia artificial. Utiliza datos reales de la FETRI, un modelo XGBoost con 51 features + Azure AutoML, explicabilidad SHAP, chatbot con Azure OpenAI (GPT-4o) y un dashboard web interactivo.

---

## 🗺️ Índice rápido

| Quiero... | Voy a... |
|---|---|
| Entender el proyecto desde cero | [📄 Contexto del proyecto](docs/CONTEXTO_PROYECTO.md) |
| Ver qué ficheros de datos tenemos | [📋 Excels](docs/lista_todos_los_excel.md) |
| Ver el esquema de base de datos | [🗄️ Esquema SQL](database/azure_sql_schema.sql) |
| Cargar datos en Azure SQL | [⬆️ Carga a la BBDD](database/load_to_azure_sql.py) |
| Ejecutar el ETL | [🔧 Importación y limpieza](ml_pipeline/importacion_y_limpieza.ipynb) |
| Preparar datos para AutoML | [🤖 ML Pipeline](ml_pipeline/) |
| Ver la planificación completa | [📅 Sprints](sprints/) |
| Ver las métricas del modelo | Dashboard → [Métricas](frontend/app/dashboard/metrics/page.tsx) |
| Entender las variables SHAP | Dashboard → [Diccionario](frontend/app/dashboard/diccionario/page.tsx) |

---

## 📅 Todos los sprints

| Sprint | Qué hace | Fechas | Estado |
|---|---|---|---|
| [📁 Sprint 1](sprints/sprint1.md) | ETL, limpieza y enriquecimiento de datos | 07/04 – 04/05 | ✅ Completado |
| [📁 Sprint 2](sprints/sprint2.md) | Entrenamiento del modelo predictivo (AutoML) | 04/05 – 18/05 | ✅ Completado |
| [📁 Sprint 3](sprints/sprint3.md) | API REST + Chatbot con Azure OpenAI | 18/05 – 01/06 | ✅ Completado |
| [📁 Sprint 4](sprints/sprint4.md) | Dashboard Next.js + integración final | 01/06 – 26/06 | ✅ Completado |

---

## 🏗️ Arquitectura de la solución

```
┌──────────────────────────────────────────────────────────────┐
│  CAPA 1 · DATOS                                              │
│  CSV / Excel (raw/) ──► Azure SQL Database                   │
├──────────────────────────────────────────────────────────────┤
│  CAPA 2 · MACHINE LEARNING  (Azure ML)                       │
│  ML Notebooks ──► Azure AutoML ──► ML Online Endpoint        │
│  XGBoost local (51 features) + SHAP Explainer                │
├──────────────────────────────────────────────────────────────┤
│  CAPA 3 · BACKEND                                            │
│  FastAPI (Python)  +  Azure OpenAI (GPT-4o Chatbot)          │
├──────────────────────────────────────────────────────────────┤
│  CAPA 4 · FRONTEND                                           │
│  Next.js 16 (React 19 + TypeScript)                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Cómo trabajar con el proyecto

### Configurar el entorno por primera vez

**1. Clonar el repo**
```bash
git clone https://github.com/Mariioograciia/conersys_predictivo_triatlon_elitemasculino.git
cd conersys_predictivo_triatlon_elitemasculino
```

**2. Instalar dependencias del backend (Python)**
```bash
pip install pandas numpy scikit-learn xgboost shap pyodbc python-dotenv fastapi uvicorn openai joblib sqlalchemy
```

**3. Instalar dependencias del frontend (Node.js)**
```bash
cd frontend
npm install
cd ..
```

**4. Crear el fichero `.env`** en la raíz del proyecto (nunca se sube a GitHub, ya está en `.gitignore`)
Puedes basarte en el archivo `.env.example` incluido en el proyecto.
```env
AZURE_SERVER=predictivomas-db-server.database.windows.net
AZURE_DB=predictivomasc_database
AZURE_USER=conersysadmin
AZURE_PASSWORD=tu-password
AZURE_SUBSCRIPTION_ID=tu-subscription-id
AZURE_RESOURCE_GROUP=TFM-Conersys
AZURE_WORKSPACE_NAME=predictivo_triatlon
AZURE_MODEL_NAME=predictivo_triatlon
AZURE_MODEL_VERSION=1
AZURE_ML_ENDPOINT=https://predictivo-triatlon-endpoint.../score
AZURE_ML_KEY=tu-key-de-ml
AZURE_FOUNDRY_ENDPOINT=https://conersysmodel-resource.openai.azure.com/
AZURE_FOUNDRY_KEY=tu-key-de-openai
AZURE_FOUNDRY_API_VERSION=2024-02-15-preview
```
> Las credenciales reales están en el canal de Teams del proyecto.

---

### Ejecutar el proyecto en local

**1. Backend (FastAPI en puerto 5050)**
```bash
python -m uvicorn chatbot.chatbot_api:app --host 0.0.0.0 --port 5050 --reload
```

**2. Frontend (Next.js en puerto 3000)**
```bash
cd frontend
npm run dev
```

**3. Abrir en el navegador**
- Landing + Dashboard: `http://localhost:3000`
- API directa: `http://localhost:5050`

> El frontend proxy todas las rutas `/api/*` al backend automáticamente (configurado en `next.config.mjs`).

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
sprint2/feature-engineering
sprint3/chatbot-azure-openai
sprint4/dashboard-nextjs
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
├── 📂 chatbot/                       # Backend FastAPI + Chatbot IA
│   ├── chatbot_api.py                # Servidor principal (FastAPI)
│   ├── ai_foundry.py                 # Integración con Azure OpenAI (GPT-4o)
│   ├── chat_logic.py                 # Motor de conversación (fallback local)
│   ├── shap_explainer.py             # Explainer SHAP + predicción XGBoost/Azure ML
│   ├── race_lookup.py                # Búsqueda de carreras por nombre/ciudad
│   ├── database_service.py           # Conexión y consultas a Azure SQL
│   └── db_check.py                   # Healthcheck de la BBDD
│
├── 📂 database/
│   ├── azure_sql_schema.sql          # Esquema de tablas SQL
│   └── load_to_azure_sql.py          # Carga los datos procesados a Azure SQL
│
├── 📂 docs/
│   ├── CONTEXTO_PROYECTO.md          # Descripción del problema y decisiones clave
│   ├── Diccionario_Variables.docx    # Diccionario de variables del modelo
│   └── lista_todos_los_excel.md      # Inventario de ficheros del cliente
│
├── 📂 frontend/                      # Dashboard Next.js 16
│   ├── app/
│   │   ├── page.tsx                  # Landing page (estilo FETRI)
│   │   ├── GlobalLayout.tsx          # Layout global + chat widget
│   │   ├── dashboard/page.tsx        # Simulador predictivo
│   │   ├── dashboard/metrics/        # Métricas del modelo + SHAP global
│   │   ├── dashboard/diccionario/    # Diccionario de variables
│   │   ├── dashboard/athlete/        # Ficha individual de atleta
│   │   ├── clubes/                   # Directorio de clubes
│   │   ├── atletas/                  # Directorio de atletas
│   │   └── competiciones/            # Directorio de competiciones
│   └── public/images/                # Gráficos SHAP (beeswarm, bar, dependence)
│
├── 📂 ml_pipeline/                   # Pipeline completo de ML
│   ├── importacion_y_limpieza.ipynb  # ETL principal
│   ├── build_dataset.py              # Construcción del dataset de 51 features
│   ├── prepare_azure_automl_dataset  # Prepara datos para Azure AutoML
│   ├── generate_normalized_datasets  # Genera datasets normalizados
│   ├── geocode_clubs.py              # Geocodificación de clubes
│   ├── deploy_azure_endpoint.py      # Despliegue del modelo en Azure ML
│   └── shap_explainer.py             # Generación de gráficos SHAP globales
│
├── 📂 models/                        # Modelos entrenados (.pkl)
├── 📂 data/                          # Datos raw y procesados
├── 📂 sprints/                       # Planificación de sprints
│
├── .env.example                      # Plantilla de variables de entorno
├── .gitignore                        # Exclusiones de git
├── train_xgboost_51_features.py      # Entrenamiento del modelo local XGBoost
└── README.md                         # Este archivo
```

---

## 📊 Métricas del Modelo

| Métrica | Valor |
|---|---|
| MAE (Error Absoluto Medio) | 13.21 posiciones |
| RMSE (Error Cuadrático) | 17.82 posiciones |
| R² (Varianza Explicada) | 0.678 |
| Correlación Spearman | 0.784 |

> Ver análisis detallado en el Dashboard → Métricas
