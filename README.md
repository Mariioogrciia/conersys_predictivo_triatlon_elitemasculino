# 🏊🚴🏃 Predictivo Triatlón Élite Masculino
**Conersys · TFM Máster IA · Tajamar Tech 2025-26**
Mario García · Alejandro Benítez
 A
---
 
## 🟡 Sprint actual — Sprint 2: Modelo predictivo ML
 
> **25/05/2026 → 05/06/2026** · 2 semanas  
 
**Objetivo:** Entrenar el modelo que predice el tiempo final de cada atleta y dejarlo registrado en Azure ML listo para ser consumido por una API.
 
### ¿En qué estamos ahora mismo?
 
| Tarea | Responsable | Estado |
|---|---|---|
| 📖 Leer [sprint2.md](sprints/sprint2.md) | Mario | ⚪ Pendiente |
| <sub>Leer el plan completo del sprint antes de empezar — objetivos, features, modelos, riesgos y definition of done</sub> | | |
| 📖 Leer [sprint2.md](sprints/sprint2.md) | Alejandro | ✅ Hecho |
| <sub>Leer el plan completo del sprint antes de empezar — objetivos, features, modelos, riesgos y definition of done</sub> | | |
| **— PENDIENTES DE SPRINT 1 —** | | |
| Notebook EDA | Mario | ⚪ Pendiente |
| <sub>Explorar el dataset: distribuciones, % nulos por columna, outliers y correlaciones básicas</sub> | | |
| Identificar registros DSQ/DNF | Ambos | ⚪ Pendiente |
| <sub>Buscar si hay columna de resultado en el dataset y crear la variable `descalificado` (0/1) — condiciona el clasificador</sub> | | |
| **— INFRAESTRUCTURA —** | | |
| Crear Azure ML Workspace | Alejandro | ⚪ Pendiente |
| <sub>Azure Portal → Machine Learning → Create · crea automáticamente su Key Vault y App Insights</sub> | | |
| **— FEATURE ENGINEERING —** | | |
| Calcular variables de rendimiento del atleta | Alejandro | ⚪ Pendiente |
| <sub>Calcular: media últimas 5 pruebas, mejor marca personal, nº pruebas completadas en la temporada</sub> | | |
| Calcular variables de contexto de la prueba | Alejandro | ⚪ Pendiente |
| <sub>Unir altitud, temperatura, humedad, desnivel y tipo de agua (ya enriquecidos en Sprint 1) al dataset del modelo</sub> | | |
| Calcular variable de recuperación | Alejandro | ⚪ Pendiente |
| <sub>Calcular `dias_desde_ultima_prueba` por atleta para cada fila del dataset</sub> | | |
| Documentar todas las features | Alejandro | ⚪ Pendiente |
| <sub>Crear tabla en `docs/` con nombre, descripción, unidad, rango esperado y cómo se calcula cada variable</sub> | | |
| Verificar que no hay data leakage | ❓ Por asignar | ⚪ Pendiente |
| <sub>Comprobar que ninguna feature usa información posterior a la fecha de la prueba que se predice</sub> | | |
| **— MODELO —** | | |
| Preparar splits de entrenamiento y test | ❓ Por asignar | ⚪ Pendiente |
| <sub>Separar temporalmente: pruebas antiguas = train, pruebas recientes = test · nunca aleatorio</sub> | | |
| Entrenar Random Forest | ❓ Por asignar | ⚪ Pendiente |✅ Hecho
| <sub>Entrenar con k-fold temporal (k=5) y registrar RMSE, MAE y R² en Azure ML Experiments</sub> | | |
| Entrenar XGBoost | ❓ Por asignar | ⚪ Pendiente |
| <sub>Entrenar con los mismos splits y métricas que Random Forest para que la comparación sea justa</sub> | | |
| Comparar modelos y seleccionar el ganador | ❓ Por asignar | ⚪ Pendiente |
| <sub>Si diferencia de RMSE < 3% → Random Forest (más interpretable) · si no → XGBoost</sub> | | |
| Registrar modelo ganador en Azure ML Model Registry | ❓ Por asignar | ⚪ Pendiente |
| <sub>Subir el modelo con nombre, versión, métricas y fecha · objetivo: RMSE < 120s</sub> | | |
| Documentar métricas finales del modelo | ❓ Por asignar | ⚪ Pendiente |
| <sub>Añadir tabla de resultados (RMSE, MAE, R²) al `sprint2.md` y al `docs/`</sub> | | |
| **— EXPLICABILIDAD Y DSQ —** | | |
| Implementar módulo SHAP | ❓ Por asignar | ⚪ Pendiente |
| <sub>Para cada predicción devolver los 3 factores más influyentes con su efecto en segundos (+/-)</sub> | | |
| Probar SHAP con ejemplos reales | ❓ Por asignar | ⚪ Pendiente |
| <sub>Ejecutar SHAP sobre 5-10 atletas reales y verificar que la explicación tiene sentido deportivo</sub> | | |
| Clasificador / detector DSQ | ❓ Por asignar | ⚪ Pendiente |
| <sub>Si ≥30 casos DSQ → clasificador binario · si no → Isolation Forest · registrar en Azure ML Model Registry</sub> | | |
 
> **Estados:** ✅ Hecho · 🟡 En curso · ⚪ Pendiente · 🔴 AVISAR YA

📋 **Detalle completo del sprint → [sprints/sprint2.md](sprints/sprint2.md)**
 
---
 
## 🗺️ Índice rápido
 
| Quiero... | Voy a... |
|---|---|
| Entender el proyecto desde cero | [📄 Contexto del proyecto](docs/CONTEXTO_PROYECTO.md) |
| Ver qué ficheros de datos tenemos | [📋 Excels](docs/lista_todos_los_excel.md) |
| Ver o tocar el esquema de base de datos | [🗄️ Esquema de la BBDD](database/azure_sql_scalejandrobenitez1@lagomar.comhema.sql) |
| Cargar datos en Azure SQL | [⬆️ Carga a la BBDD](database/load_to_azure_sql.py) |
| Ejecutar el ETL | [🔧 Importación y limpieza](ml_pipeline/importacion_y_limpieza.ipynb) |
| Preparar datos para AutoML | [🤖 ML Pipeline](ml_pipeline/) |
| Ver la planificación completa | [📅 Sprints](sprints/) |
 
---
 
## 📅 Todos los sprints
 
| Sprint | Qué hace | Fechas | Estado |
|---|---|---|---|
| [📁 Sprint 1](sprints/sprint1.md) | ETL, limpieza y enriquecimiento de datos | 07/04 – 04/05 | ✅ Completado |
| [📁 Sprint 2](sprints/sprint2.md) | Entrenamiento del modelo predictivo (AutoML) | 04/05 – 18/05 | 🟡 En curso |
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
```⚪ Pendiente
Entrega final: 26/06/2026*
