# 📖 Contexto del Proyecto: Modelo Predictivo de Triatlón (FETRI)

Este documento sirve como **guía de contexto global** para que cualquier asistente de inteligencia artificial o copiloto de código entienda la arquitectura de datos, las fuentes de origen, el modelo de base de datos destino (**ClickHouse**) y los objetivos de ciencia de datos del proyecto.

---

## 1. Visión General del Proyecto

* **Objetivo principal:** Desarrollar un **modelo predictivo de triatlón** que estime el rendimiento de los atletas en futuras competiciones, determine las probabilidades de victoria de cada participante en una carrera dada y clasifique a los competidores según su nivel de habilidad esperado.
* **Dominio de negocio:** Datos oficiales de la **Federación Española de Triatlón (FETRI)**.
* **Tecnologías clave:** Python (Pandas, ClickHouse-connect, Scikit-Learn/XGBoost), **ClickHouse** (Base de datos analítica orientada a columnas) y Jupyter Notebooks para experimentación.

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

## 3. Arquitectura y Diseño de la Base de Datos: ClickHouse

Dado que ClickHouse es una base de datos columnar optimizada para analítica e inserciones rápidas, diseñamos un esquema denormalizado y optimizado con el motor **`MergeTree`**:

### Tabla 1: `ranking_types` (Catálogo)
Mapea los IDs numéricos a disciplinas (TRW, TRM, DUM, etc.).
```sql
CREATE TABLE IF NOT EXISTS fetri.ranking_types (
    id UInt8,
    nombre String,
    siglas String
) ENGINE = MergeTree()
ORDER BY id;
```

### Tabla 2: `deportistas` (Dimensión Mutable)
Almacena la información demográfica y de afiliación de los atletas.
```sql
CREATE TABLE IF NOT EXISTS fetri.deportistas (
    documento String,             -- DNI o Licencia (Clave Primaria)
    nombre String,
    club String,
    ggee String,                  -- Grupo de Edad
    fecha_actualizacion DateTime DEFAULT now() -- Para resolución de conflictos en ReplacingMergeTree
) ENGINE = ReplacingMergeTree(fecha_actualizacion)
ORDER BY documento;
```

### Tabla 3: `pruebas` (Dimensión Estática)
Almacena los metadatos del calendario e importancia de las carreras.
```sql
CREATE TABLE IF NOT EXISTS fetri.pruebas (
    id UInt32,                    -- ID de la prueba en el JSON
    season UInt16,                -- Temporada (Ej. 2025)
    nombre String,
    championship_level String,    -- Nivel competitivo (para ponderar la dificultad)
    fecha Date,                   -- Fecha de la competición
    ciudad String,
    provincia String,
    lat Float64,                  -- Para calcular fatiga de viaje (Haversine)
    lng Float64
) ENGINE = MergeTree()
ORDER BY (season, fecha, id);
```

### Tabla 4: `resultados` (Tabla de Hechos Central)
Almacena los resultados históricos individuales obtenidos por cada atleta en cada prueba.
```sql
CREATE TABLE IF NOT EXISTS fetri.resultados (
    season UInt16,
    ranking_type_id UInt8,        -- FK a ranking_types
    deportista_documento String,  -- FK a deportistas
    prueba_id UInt32,             -- FK a pruebas
    puntos Float32,               -- Variable objetivo principal
    puesto UInt16                 -- Variable objetivo secundaria (Target para Rank:NDCG)
) ENGINE = MergeTree()
ORDER BY (season, ranking_type_id, deportista_documento, prueba_id);
```

### Tabla 5: `clubes_geo` (Dimensión de Enriquecimiento)
Almacena las coordenadas geográficas de las sedes de los clubes para calcular distancias de viaje.
```sql
CREATE TABLE IF NOT EXISTS fetri.clubes_geo (
    club String,
    ciudad_sede String,
    lat Float64,
    lng Float64
) ENGINE = MergeTree()
ORDER BY club;
```

---

## 4. Estrategia para el Modelo Predictivo

Cualquier asistente de código encargado de desarrollar la lógica del modelo predictivo debe considerar las siguientes pautas de ciencia de datos:

### A. Preparación de Variables (*Feature Engineering*)
1. **Historial de Habilidad del Atleta:** Media móvil de puntos obtenidos por carrera, desviación estándar (consistencia) y número de pruebas finalizadas.
2. **Nivel del Evento:** El nivel de campeonato (`ChampionshipLevel`) influye en la cantidad de puntos que se reparten y en la dureza de la competencia.
3. **Efecto de Fatiga de Viaje:** Distancia geográfica (usando la fórmula de Haversine) entre la provincia del Club del atleta y las coordenadas (`Lat`, `Lng`) de la carrera.
4. **Grupo de Edad / Experiencia:** Agrupación y tendencias de rendimiento por edad (`GGEE`).

### B. Enfoques de Modelado Sugeridos
* **Modelo de Rating Multijugador (TrueSkill o Elo):** Generar una puntuación dinámica de habilidad para cada deportista que aumente cuando supera a rivales fuertes y disminuya cuando es superado por rivales con menor puntuación.
* **Modelo Bradley-Terry / Plackett-Luce:** Modelar probabilísticamente clasificaciones de carreras de múltiples competidores para obtener la probabilidad exacta de victoria de cada uno.
* **Regresión (XGBoost) + Simulación Monte Carlo:** 
  1. Entrenar un regresor para predecir los puntos esperados de un deportista en una prueba dada.
  2. Añadir un factor de variabilidad/error aleatorio basado en el histórico de cada atleta.
  3. Simular la carrera 10,000 veces para estimar la probabilidad final de victoria (porcentaje de veces que el atleta termina en 1ª posición).
