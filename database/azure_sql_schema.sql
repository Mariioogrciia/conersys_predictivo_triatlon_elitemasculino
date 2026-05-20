-- ============================================================================
-- SCRIPT DE CREACIÓN DE TABLAS - PROYECTO TFM TRIATLÓN (FETRI)
-- Base de datos: Azure SQL Database / Microsoft SQL Server
-- ============================================================================

-- Nota: En Azure SQL Database, la base de datos se crea a nivel de recurso.
-- Ejecuta este script conectado a la base de datos de tu TFM.

-- 1. Tabla de Modalidades / Tipos de Ranking (Catálogo)
IF OBJECT_ID('dbo.resultados', 'U') IS NOT NULL DROP TABLE dbo.resultados;
IF OBJECT_ID('dbo.deportistas', 'U') IS NOT NULL DROP TABLE dbo.deportistas;
IF OBJECT_ID('dbo.clubes_geo', 'U') IS NOT NULL DROP TABLE dbo.clubes_geo;
IF OBJECT_ID('dbo.pruebas', 'U') IS NOT NULL DROP TABLE dbo.pruebas;
IF OBJECT_ID('dbo.ranking_types', 'U') IS NOT NULL DROP TABLE dbo.ranking_types;

CREATE TABLE dbo.ranking_types (
    id INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    siglas VARCHAR(10) NOT NULL
);

-- 2. Tabla de Coordenadas de Clubes (Dimensión de Enriquecimiento)
CREATE TABLE dbo.clubes_geo (
    club VARCHAR(255) PRIMARY KEY,
    ciudad_sede VARCHAR(255) NOT NULL,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL
);

-- 3. Tabla de Deportistas (Dimensión de Atletas)
CREATE TABLE dbo.deportistas (
    documento VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    club VARCHAR(255) NULL,
    ggee VARCHAR(50) NULL,
    fecha_actualizacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_deportistas_club FOREIGN KEY (club) REFERENCES dbo.clubes_geo(club) ON DELETE SET NULL
);

-- 4. Tabla de Pruebas (Dimensión de Campeonatos)
CREATE TABLE dbo.pruebas (
    id INT PRIMARY KEY,
    season INT NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    championship_level VARCHAR(10) NOT NULL,
    fecha DATE NOT NULL,
    ciudad VARCHAR(255) NOT NULL,
    provincia VARCHAR(255) NOT NULL,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL
);

-- 5. Tabla de Resultados (Tabla de Hechos Central / Relación N:M)
CREATE TABLE dbo.resultados (
    id INT IDENTITY(1,1) PRIMARY KEY, -- Clave primaria física para control interno en Azure SQL
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

-- ============================================================================
-- Poblado Inicial de la Tabla Catálogo (Tipos de Ranking)
-- ============================================================================
INSERT INTO dbo.ranking_types (id, nombre, siglas) VALUES 
(1, 'Triatlón Femenino', 'TRW'),
(2, 'Triatlón Femenino (Hist)', 'TRW1'),
(3, 'Duatlón Femenino', 'DUW'),
(4, 'Media y Larga Distancia Femenino', 'MDLDW'),
(5, 'Junior Femenino', 'JUW'),
(6, 'Triatlón Masculino', 'TRM'),
(7, 'Duatlón Masculino', 'DUM'),
(8, 'Media y Larga Distancia Masculino', 'MDLDM'),
(9, 'Junior Masculino', 'JUM');
