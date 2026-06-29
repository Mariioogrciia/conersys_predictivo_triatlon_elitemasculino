# 📖 Contexto del Proyecto: Modelo Predictivo de Triatlón (FETRI)

Este documento sirve como **guía de contexto global** para que cualquier asistente de inteligencia artificial o copiloto de código entienda la arquitectura de datos, las fuentes de origen, el modelo de base de datos destino (**Azure SQL Database**) y los objetivos de ciencia de datos del proyecto.

---

## 1. Visión General del Proyecto

* **Objetivo principal:** Desarrollar un **modelo predictivo de triatlón** que estime la posición de llegada de los atletas en futuras competiciones, analice las probabilidades de victoria de cada participante y clasifique a los competidores según su nivel de habilidad esperado.
* **Dominio de negocio:** Datos oficiales de la **Federación Española de Triatlón (FETRI)**.
* **Tecnologías clave:** Python (Pandas, Scikit-Learn, XGBoost, SHAP), **Azure SQL Database** (base de datos relacional en la nube), **Azure Machine Learning** (AutoML + Online Endpoint), **Azure OpenAI** (GPT-4o para chatbot), **FastAPI** (backend), **Next.js** (frontend) y Jupyter Notebooks para experimentación.

---

## 2. Origen y Estructura de los Datos en Bruto

Los datos en el entorno local provienen de dos fuentes principales que se complementan entre sí:

### A. Los JSON de Campeonatos (`championships%3A[AÑO].json`)
Contienen el calendario histórico y los metadatos de todas las pruebas oficiales organizadas por año (de 2019 a 2026).
* **Campos clave en cada prueba:**
  * `Id` (ID único del campeonato).
  * `Name` (Nombre oficial del evento).
  * `Season` (Año/Temporada).
  * `StartDate` / `EndDate` (Fechas de competición).
  * `ChampionshipLevel` (Nivel del campeonato: indica la importancia/dificultad de la prueba).
  * `ChampionshipType` / `EspecialityType` (Tipos de disciplina).
  * `City` / `Province` / `Location` / `Lat` / `Lng` (Ubicación geográfica precisa de la carrera).
  * `Tags` (Etiquetas como `RK-IND-TRI` - *Ranking Individual Triatlón* que clasifican a qué ranking afecta).

### B. Los Excel de Rankings Activos (`fetri_ranking_lst_[MODALIDAD].json`)
Los archivos JSON de rankings actúan como un **índice de versiones** que contienen metadatos y enlaces de descarga de AWS S3. 
* **IMPORTANTE:** Debido a cambios en los servidores, los enlaces antiguos de la cubeta `conersys-data` están caídos. **Solo los enlaces del servidor activo (`fetri2025-media`) están operativos.** Estos corresponden a las versiones de rankings **Activos (los más recientes de 2025 y 2026)**.
* **Estructura Interna de los Excel Activos (Ej. `Ranking 2025`):**
  Cada archivo Excel es una **matriz acumulativa de la temporada completa**, no una foto estática. Contiene:
  * **Datos del Atleta (Filas):** Nombre (`NOMBRE`), Club (`CLUB`), Documento/Licencia (`DOCUMENTO`), Grupo de Edad (`GGEE`), Puesto General (`PUESTO`) y Puntos Totales (`PUNTOS`).
  * **Resultados por Carrera (Columnas):** Cada columna restante corresponde al nombre de una prueba específica celebrada esa temporada (coincidiendo con el `Name` en los JSON de campeonatos). La celda contiene los **puntos exactos obtenidos por ese atleta en esa carrera específica** (o `NaN` si no participó).

---

## 3. Arquitectura y Diseño de la Base de Datos: Azure SQL Database

El proyecto utiliza **Azure SQL Database**, un servicio gestionado de base de datos relacional en Microsoft Azure. El esquema está diseñado con un modelo estrella optimizado para consultas analíticas:

### Tabla 1: `ranking_types` (Catálogo)
Mapea los IDs numéricos a disciplinas (TRW, TRM, DUM, etc.).
```sql
CREATE TABLE dbo.ranking_types (
    id INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    siglas VARCHAR(10) NOT NULL
);
```

### Tabla 2: `clubes_geo` (Dimensión de Enriquecimiento)
Almacena las coordenadas geográficas de las sedes de los clubes para calcular distancias de viaje.
```sql
CREATE TABLE dbo.clubes_geo (
    club VARCHAR(255) PRIMARY KEY,
    ciudad_sede VARCHAR(255) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL
);
```

### Tabla 3: `deportistas` (Dimensión de Atletas)
Almacena la información demográfica y de afiliación de los atletas.
```sql
CREATE TABLE dbo.deportistas (
    documento VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    club VARCHAR(255) NULL,
    ggee VARCHAR(50) NULL,
    fecha_actualizacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_deportistas_club FOREIGN KEY (club) REFERENCES dbo.clubes_geo(club)
);
```

### Tabla 4: `pruebas` (Dimensión de Campeonatos)
Almacena los metadatos del calendario, ubicación y condiciones meteorológicas de las carreras.
```sql
CREATE TABLE dbo.pruebas (
    id INT PRIMARY KEY,
    season INT NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    championship_level VARCHAR(10) NOT NULL,
    fecha DATE NOT NULL,
    ciudad VARCHAR(255) NOT NULL,
    provincia VARCHAR(255) NOT NULL,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    altitud FLOAT NULL,
    temperatura_max FLOAT NULL,
    humedad_media FLOAT NULL,
    precipitacion FLOAT NULL,
    viento_max FLOAT NULL
);
```

### Tabla 5: `resultados` (Tabla de Hechos Central)
Almacena los resultados históricos individuales obtenidos por cada atleta en cada prueba.
```sql
CREATE TABLE dbo.resultados (
    id INT IDENTITY(1,1) PRIMARY KEY,
    season INT NOT NULL,
    ranking_type_id INT NOT NULL,
    deportista_documento VARCHAR(50) NOT NULL,
    prueba_id INT NOT NULL,
    puntos REAL NOT NULL,
    puesto INT NOT NULL,
    CONSTRAINT FK_resultados_ranking FOREIGN KEY (ranking_type_id) REFERENCES dbo.ranking_types(id),
    CONSTRAINT FK_resultados_deportista FOREIGN KEY (deportista_documento) REFERENCES dbo.deportistas(documento),
    CONSTRAINT FK_resultados_prueba FOREIGN KEY (prueba_id) REFERENCES dbo.pruebas(id)
);
```

---

## 4. Estrategia para el Modelo Predictivo

### A. Modelo Implementado: XGBoost con 51 Features + Azure AutoML

El modelo final utiliza **XGBoost Regressor** entrenado con un dataset de **51 variables de ingeniería** que cubren:

1. **Perfil del atleta:** Edad, federación, ranking FETRI, ID World Triathlon.
2. **Historial de rendimiento:** Posición media en últimas 3/5 carreras, mejor marca histórica y de temporada, tasas de victoria/podio/top10/DNF.
3. **Momentum y forma:** Momentum de ranking, tendencia (subiendo/estable/bajando), racha de podios y top10, puntuación de forma.
4. **Rendimiento por segmentos:** Rankings medios de natación, ciclismo y carrera a pie.
5. **Adaptabilidad ambiental:** Sesgos de rendimiento en altitud, costa y calor. Posición media en condiciones extremas.
6. **Contexto de la carrera:** Ciudad, temperatura, humedad, altitud, latitud/longitud, tipo de carrera, mes, día de la semana.
7. **Contexto competitivo:** Número de participantes, ranking medio de rivales, porcentaje de rivales con mejor ranking.
8. **Experiencia en la ciudad:** Carreras previas y victorias en la misma ciudad.

### B. Explicabilidad: SHAP (SHapley Additive exPlanations)

Para cada predicción, el sistema calcula los **valores SHAP** que explican qué factores empujan la posición del atleta hacia arriba (peor) o hacia abajo (mejor). Esto permite:
- **Explicaciones individuales:** Los 5 factores más influyentes para cada atleta.
- **Explicaciones globales:** Gráficos beeswarm, bar plots y dependence plots que revelan las variables más importantes del modelo a nivel agregado.

### C. Métricas de Evaluación

| Métrica | Valor |
|---|---|
| MAE (Error Absoluto Medio) | 13.21 posiciones |
| RMSE (Error Cuadrático Medio) | 17.82 posiciones |
| R² (Varianza Explicada) | 0.678 |
| Correlación Spearman | 0.784 |

### D. Detección de Anomalías

El sistema detecta predicciones atípicas comparando la posición predicha con el historial real del atleta mediante z-scores. Si la predicción se desvía más de 1.5 desviaciones estándar de su media histórica, se marca como anomalía con una explicación.
