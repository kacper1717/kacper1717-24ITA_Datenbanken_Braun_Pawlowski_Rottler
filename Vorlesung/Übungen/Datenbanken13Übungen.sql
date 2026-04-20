-- =====================================================================
--  Demo-Schema: kunden-Tabelle mit 1.000.000 Zeilen
--  Ziel: Indexe in Aktion demonstrieren (MySQL 8+)
-- =====================================================================

-- ANALYZE TABLE kunden; aktualisiert die Statistiken der Tabelle.
-- Diese nutzt der Optimizer für:
-- - Auswahl geeigneter Indizes
-- - Join-Reihenfolge
-- - Entscheidung zwischen Table Scan und Indexzugriff
-- Hinweis: Für diese Demo sind korrekte Statistiken wichtiger als ein leerer Cache.

-- Hinweis:
-- Der Datenimport wird über eine Stored Procedure gestartet.
-- Die eigentliche Befüllung erfolgt weiterhin über ein einzelnes
-- INSERT ... SELECT-Statement, das als atomare Anweisung ausgeführt wird.
-- Für diese Demo sind die Indexeffekte wichtiger als Transaktionssteuerung.

-- EXPLAIN zeigt den Plan. EXPLAIN ANALYZE zeigt die Realität.
-- EXPLAIN verstehen (ohne ANALYZE):
-- type
-- ALL → Full Table Scan
-- ref / range → Indexzugriff
-- rows
-- geschätzte Zeilen
-- filtered
-- wie viele Zeilen bleiben übrig
-- key
-- verwendeter Index

-- Auf der Windows Admin-Console evtl:
-- net stop MySQL80
-- net start MySQL80

-- InnoDB Besonderheit:
-- Der PRIMARY KEY bildet bei InnoDB den Clustered Index.
-- Die eigentlichen Tabellendaten sind dabei nach dem Primary Key organisiert.
-- Alle mit CREATE INDEX angelegten weiteren Indexe sind Secondary
-- bzw. Non-Clustered Indexe.
-- Diese speichern nicht den kompletten Datensatz, sondern den
-- Indexschlüssel plus den Primary Key als Verweis auf die eigentliche Zeile.
-- Bei SELECT * kann daher nach dem Treffer im Secondary Index
-- ein zusätzlicher Zugriff über den Clustered Index nötig sein
-- (oft als Double Lookup bezeichnet).

DROP DATABASE IF EXISTS index_demo;
CREATE DATABASE index_demo CHARACTER SET utf8mb4;
USE index_demo;

-- ---------------------------------------------------------------------
-- Tabellendefinition
-- ---------------------------------------------------------------------
CREATE TABLE kunden (
    id          INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    name        VARCHAR(50)    NOT NULL,
    email       VARCHAR(100)   NOT NULL,
    registriert DATE           NOT NULL,
    status      CHAR(1)        NOT NULL,   -- 'G' gold, 'S' silber, 'B' bronze
    land        CHAR(2)        NOT NULL,   -- 'DE', 'AT', 'CH', ...
    umsatz      DECIMAL(10,2)  NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Stored Procedure: Zufallsdaten generieren (rekursiv, MySQL 8+)
-- ---------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE fill_kunden(IN p_rows INT)
BEGIN
    SET SESSION cte_max_recursion_depth = p_rows;

    INSERT INTO kunden (name, email, registriert, status, land, umsatz)
    WITH RECURSIVE seq(n) AS (
        SELECT 1
        UNION ALL
        SELECT n + 1
        FROM seq
        WHERE n < p_rows
    )
    SELECT
        CONCAT('Kunde_', n)                                        AS name,
        CONCAT('kunde', n, '@example.com')                         AS email,
        DATE_ADD('2015-01-01', INTERVAL FLOOR(RAND() * 3650) DAY)  AS registriert,
        ELT(1 + FLOOR(RAND() * 3), 'G', 'S', 'B')                  AS status,
        ELT(1 + FLOOR(RAND() * 5), 'DE','AT','CH','FR','IT')       AS land,
        ROUND(RAND() * 10000, 2)                                   AS umsatz
    FROM seq;

    ANALYZE TABLE kunden;
END $$

DELIMITER ;

-- ---------------------------------------------------------------------
-- Daten befüllen
-- ---------------------------------------------------------------------
CALL fill_kunden(1000);
-- CALL fill_kunden(1000000);

-- Prüfen
SELECT COUNT(*) AS zeilen FROM kunden;
SELECT * FROM kunden LIMIT 5;

-- Hinweis zur CTE-Variante:
-- Kann je nach System langsam sein.
-- Alternative unten nutzt Cross Join und ist oft deutlich schneller.

-- Alternative: Cross-Join-Methode (schneller, oft für sehr große Mengen besser)
-- INSERT INTO kunden (name, email, registriert, status, land, umsatz)
-- SELECT
--   CONCAT('Kunde_', @rn := @rn + 1),
--   CONCAT('kunde', @rn, '@example.com'),
--   DATE_ADD('2015-01-01', INTERVAL FLOOR(RAND() * 3650) DAY),
--   ELT(1 + FLOOR(RAND() * 3), 'G', 'S', 'B'),
--   ELT(1 + FLOOR(RAND() * 5), 'DE','AT','CH','FR','IT'),
--   ROUND(RAND() * 10000, 2)
-- FROM
--   (SELECT 0 FROM information_schema.columns LIMIT 1000) a,
--   (SELECT 0 FROM information_schema.columns LIMIT 1000) b,
--   (SELECT @rn := 0) init;

-- Demo-Skript (zum Live-Vorführen)
-- Tipp: Für die Bewertung immer EXPLAIN ANALYZE nutzen,
-- nicht nur Laufzeit, sondern auch gelesene Zeilen betrachten.

USE index_demo;

-- =====================================================================
-- DEMO 1: Gleichheit — B+-Baum
-- =====================================================================

-- Schritt 1: Ohne Index
EXPLAIN
-- EXPLAIN ANALYZE
SELECT * FROM kunden WHERE name = 'Kunde_4711';
-- Erwartung: Full Table Scan (alle Zeilen werden geprüft).
-- Hinweis: Laufzeit kann je nach Cache variieren, wichtig ist die Zugriffsmethode.

-- Schritt 2: Index anlegen
CREATE INDEX idx_name ON kunden (name);
ANALYZE TABLE kunden;

-- Schritt 3: Nochmal ausführen
EXPLAIN ANALYZE
SELECT * FROM kunden WHERE name = 'Kunde_4711';
-- Erwartung: Index Lookup über idx_name.
-- Deutlich weniger gelesene Zeilen als beim Full Scan.

-- =====================================================================
-- DEMO 2: Range-Scan — B+-Baum
-- =====================================================================

EXPLAIN ANALYZE
SELECT COUNT(*) FROM kunden
WHERE registriert BETWEEN '2020-01-01' AND '2020-12-31';
-- Erwartung: Full Table Scan (keine geeignete Zugriffstruktur vorhanden).

CREATE INDEX idx_reg ON kunden (registriert);
ANALYZE TABLE kunden;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM kunden
WHERE registriert BETWEEN '2020-01-01' AND '2020-12-31';
-- Erwartung: Index Range Scan über idx_reg.
-- Es werden nur relevante Bereiche des Index durchsucht.

-- =====================================================================
-- DEMO 3: AND-Kombination — Index Merge (statt Bitmap)
-- =====================================================================

-- Index Merge ist KEIN eigener Index.
-- Es ist eine Zugriffsstrategie des Optimizers.
-- MySQL nutzt hier zwei getrennte Single-Column-Indizes
-- und kombiniert zur Laufzeit deren Trefferlisten.
-- Bei einer AND-Bedingung bildet MySQL die Schnittmenge
-- der gefundenen Zeilen.
-- Das ist oft besser als ein Full Table Scan, aber meist
-- schlechter als ein passender Composite Index.

-- Ohne Indexe: Full Scan
EXPLAIN ANALYZE
SELECT COUNT(*) FROM kunden
WHERE status = 'G' AND land = 'AT';
-- Erwartung: Full Table Scan, da keine passenden Indexe vorhanden sind.

-- Zwei getrennte Single-Column-Indexe
CREATE INDEX idx_status ON kunden (status);
CREATE INDEX idx_land   ON kunden (land);
ANALYZE TABLE kunden;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM kunden
WHERE status = 'G' AND land = 'AT';
-- Erwartung: Index Merge (Intersection) aus idx_status und idx_land.
-- MySQL kombiniert beide Indexe, anstatt einen Full Scan durchzuführen.

-- =====================================================================
-- BONUS: Composite Index schlägt Index Merge
-- =====================================================================

-- Composite Index / zusammengesetzter Index:
-- Ein einzelner Index enthält mehrere Spalten in fester Reihenfolge,
-- hier (status, land).
-- Dadurch kann MySQL direkt nach Kombinationen wie
-- (status = 'G' AND land = 'AT') suchen,
-- statt zwei getrennte Trefferlisten zusammenzuführen.
-- In der Regel ist das effizienter als Index Merge.

-- Linkspräfix-Regel:
-- Ein Composite Index (status, land) kann gut genutzt werden für:
--   WHERE status = 'G'
--   WHERE status = 'G' AND land = 'AT'
-- Aber nicht gut für:
--   WHERE land = 'AT'
-- Denn der Index ist nach der Reihenfolge (status, land) aufgebaut.

CREATE INDEX idx_status_land ON kunden (status, land);
ANALYZE TABLE kunden;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM kunden
WHERE status = 'G' AND land = 'AT';
-- Erwartung: Zugriff über zusammengesetzten Index (status, land).
-- In der Regel effizienter als Index Merge, da ein direkter Lookup möglich ist.

-- =====================================================================
-- BONUS 2: LIKE mit führendem Prozent
-- =====================================================================

EXPLAIN ANALYZE
SELECT * FROM kunden
WHERE name LIKE '%4711';
-- Ein B+-Baum funktioniert nur, wenn der linke Teil des Suchbegriffs bekannt ist.
-- Da der Suchbegriff mit % beginnt, ist der Anfang unbekannt.
-- Deshalb kann MySQL hier in der Regel nicht gezielt im Index einsteigen
-- und muss viele oder alle Einträge prüfen.

-- =====================================================================
-- Aufräumen (falls Demo wiederholt werden soll)
-- =====================================================================
-- DROP INDEX idx_name         ON kunden;
-- DROP INDEX idx_reg          ON kunden;
-- DROP INDEX idx_status       ON kunden;
-- DROP INDEX idx_land         ON kunden;
-- DROP INDEX idx_status_land  ON kunden;

SELECT
    table_name,
    ROUND(SUM(data_length) / 1024 / 1024, 2)  AS TableSpaceMB,
    ROUND(SUM(index_length) / 1024 / 1024, 2) AS IndexSpaceMB
FROM information_schema.tables
WHERE table_schema = 'index_demo'
GROUP BY table_name;