-- -----------------------------------------------
-- - Szenario: DDL
-- -----------------------------------------------
-- =============================================================================
-- SQL DDL Skript – Zusätzliche SQL-Statements aus der Vorlesung "Datenbanken 8 – SQL DDL"
-- Kurs: Informatik 24ITA, DHBW Stuttgart
-- Ziel-DBMS: MySQL 8.4
-- =============================================================================


-- -----------------------------------------------
-- Datenbank-Setup (DB-Name entspricht dem Skriptnamen)
-- -----------------------------------------------
DROP DATABASE IF EXISTS Datenbanken8;
CREATE DATABASE Datenbanken8
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE Datenbanken8;

-- Systemkatalog
CREATE SCHEMA IF NOT EXISTS vorlesungen;

CREATE TABLE IF NOT EXISTS vorlesungen.person (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS KLAUSUR (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  PRIMARY KEY (id)
);

SELECT 'Datenbanken im Server' AS DBServer;
SHOW DATABASES;

SELECT 'Tabellen in aktueller DB' AS TabDB;
SHOW TABLES;

SELECT 'Indizes: vorlesungen.person' AS Indizes;
SHOW INDEX FROM vorlesungen.person;

SELECT 'DDL: CREATE TABLE KLAUSUR' AS CREATETAB;
SHOW CREATE TABLE KLAUSUR;

SELECT 'Server-Statusinformationen' AS Status;
SHOW STATUS; -- Listet Statusinformationen auf

SELECT 'Schemas (information_schema.schemata)' AS Schemata;
SELECT schema_name AS SchemaName FROM information_schema.schemata ORDER BY schema_name;

SELECT 'Tabellen in aktueller DB (information_schema.tables)' AS Akteuertabellen;
SELECT table_name AS Tabelle, table_type AS Typ, table_rows AS Zeilen
FROM information_schema.tables
WHERE table_schema = DATABASE();

SELECT 'Spalten in Tabelle STUDENT (information_schema.columns)' AS SpaltenSTUDENT;
SELECT column_name AS Spalte, ordinal_position AS Position, column_default AS DefaultWert,
       is_nullable AS Nullable, data_type AS Typ
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name = 'STUDENT';

-- SELECT 'Tabellen- und Indexspeicher gesamt (aktuelle DB)' AS TabellenIndexSpeicher;
SELECT ROUND(SUM(data_length)/1024/1024) AS TableSpaceMB,
       ROUND(SUM(index_length)/1024/1024) AS IndexSpaceMB
FROM information_schema.tables
WHERE table_schema = DATABASE();

-- -------------------------------------------------------------------------------
DROP TABLE IF EXISTS DDL_TEST;

CREATE TABLE DDL_TEST (NR NUMERIC(7) NOT NULL,
NAME VARCHAR(20) NOT NULL,
BIRTHDAY DATE NOT NULL,
RESULTAT DECIMAL(3,1) NOT NULL);

INSERT INTO DDL_TEST (NR,NAME,BIRTHDAY,RESULTAT)
VALUES 
(1000,'Meyer','1998-07-30', 4.0),
(1001,'Müller','1999-12-12', 2.5);

-- SELECT 'Inhalt: DDL_TEST (ohne AUTO_INCREMENT)' AS Inhalt;
SELECT * FROM DDL_TEST;

-- -------------------------------------------

DROP TABLE IF EXISTS DDL_TEST;

CREATE TABLE DDL_TEST (ID INT NOT NULL AUTO_INCREMENT, NR NUMERIC(7) NOT NULL,
NAME VARCHAR(20) NOT NULL,
BIRTHDAY DATE NOT NULL,
RESULTAT DECIMAL(3,1) NOT NULL,
PRIMARY KEY (ID));

INSERT INTO DDL_TEST (NR,NAME,BIRTHDAY,RESULTAT)
VALUES (1000,'Meyer','1998-07-30', 4.0),
(1001,'Müller','1999-12-12', 2.5);
 
-- SELECT 'Inhalt: DDL_TEST (mit AUTO_INCREMENT)' AS Inhalt;
SELECT * FROM DDL_TEST;

-- -------------------------------------------
-- MySQL unterstützt CREATE DOMAIN nicht
    DROP TABLE IF EXISTS example;
    CREATE TABLE example (
    	ID		INTEGER PRIMARY KEY,
    	VALUE	INTEGER CHECK (VALUE >= 100)
    );

    INSERT INTO example (ID, VALUE) VALUES (1, 101);
    -- Die nächste Zeile provoziert in MySQL 8.4 einen PK-Fehler (ID=1 doppelt)
    -- INSERT INTO example (ID, VALUE) VALUES (1, 100);
 
-- -------------------------------------------
 
 DROP TEMPORARY TABLE IF EXISTS DDL_MEMORY_TEST;
 CREATE TEMPORARY TABLE DDL_MEMORY_TEST (NR NUMERIC(7) NOT NULL,
NAME VARCHAR(20) NOT NULL,
BIRTHDAY DATE NOT NULL,
RESULTAT DECIMAL(3,1) NOT NULL) ENGINE = MEMORY;
INSERT INTO DDL_MEMORY_TEST (NR,NAME,BIRTHDAY,RESULTAT)
VALUES 
(1000,'Meyer','1998-07-30', 4.0),
(1001,'Müller','1999-12-12', 2.5);

-- SELECT 'Inhalt: DDL_MEMORY_TEST (ENGINE=MEMORY)' AS Abschnitt;
SELECT * FROM DDL_MEMORY_TEST;

 
 -- -------------------------------------------
/*
SELECT @@SESSION.sql_mode;

SET SESSION sql_mode = 'STRICT_ALL_TABLES';
 
DROP TABLE IF EXISTS DDL_TEST;

CREATE TABLE DDL_TEST (NR NUMERIC(7) NOT NULL,
NAME VARCHAR(20) NOT NULL,
BIRTHDAY DATE NOT NULL,
RESULTAT DECIMAL(3,1) NOT NULL, CONSTRAINT CHECK (RESULTAT < 0));

INSERT INTO DDL_TEST (NR,NAME,BIRTHDAY,RESULTAT)
VALUES 
(1000,'Meyer','1998-07-30', 4.0),
(1001,'Müller','1999-12-12', 2.5);

SELECT * FROM DDL_TEST;
*/


-- -------------------------------------------
-- Abschlussmeldung
SELECT
  'Datenbanken8.sql erfolgreich durchgelaufen.' AS status,
  NOW() AS executed_at;
 
