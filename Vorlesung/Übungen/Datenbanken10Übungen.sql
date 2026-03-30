-- ============================================================================
-- Transaktionen in MySQL – Vorlesungsbeispiele
-- Datenbanksysteme, DHBW Stuttgart
-- Karsten Keßler
-- ============================================================================
-- Voraussetzung: MySQL 8.4 mit InnoDB (Standard-Engine)
-- Am besten in VS Code mit 3 Terminals und separaten MySQL-Sessions ausführen
-- Verbindung: docker exec -it skeleton-mysql mysql -u root -p
-- ============================================================================


-- ============================================================================
-- 0. VORBEREITUNG: Testdatenbank und Tabellen anlegen
-- ============================================================================

DROP DATABASE IF EXISTS transaktionen_demo;
CREATE DATABASE transaktionen_demo;
USE transaktionen_demo;

-- Kontentabelle für Bankbeispiele
CREATE TABLE konten (
    konto_id    INT PRIMARY KEY,
    inhaber     VARCHAR(50) NOT NULL,
    kontostand  DECIMAL(10,2) NOT NULL,
    CONSTRAINT chk_positiv CHECK (kontostand >= 0)
);

INSERT INTO konten VALUES
    (1, 'Alice',  1000.00),
    (2, 'Bob',    2000.00),
    (3, 'Charlie', 500.00);

-- Produkttabelle für weitere Beispiele
CREATE TABLE produkte (
    produkt_id  INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    preis       DECIMAL(8,2) NOT NULL,
    bestand     INT NOT NULL DEFAULT 0
);

INSERT INTO produkte (name, preis, bestand) VALUES
    ('Laptop',    999.99, 10),
    ('Maus',       29.99, 50),
    ('Tastatur',   79.99, 30),
    ('Monitor',   349.99, 15);

SELECT * FROM konten;
SELECT * FROM produkte;


-- ============================================================================
-- 1. ACID DEMONSTRATION: Atomicity (Alles oder Nichts)
-- ============================================================================

-- Beispiel 1a: Erfolgreiche Überweisung (100 EUR von Alice an Bob)
-- ---------------------------------------------------------------

SELECT 'VORHER:' AS info;
SELECT * FROM konten WHERE konto_id IN (1, 2);

START TRANSACTION;

    UPDATE konten SET kontostand = kontostand - 100 WHERE konto_id = 1;  -- Alice
    UPDATE konten SET kontostand = kontostand + 100 WHERE konto_id = 2;  -- Bob

COMMIT;

SELECT 'NACHHER:' AS info;
SELECT * FROM konten WHERE konto_id IN (1, 2);
-- Ergebnis: Alice=900, Bob=2100 → beide Änderungen wurden übernommen


-- Beispiel 1b: Abgebrochene Überweisung mit ROLLBACK
-- ---------------------------------------------------

SELECT 'VORHER:' AS info;
SELECT * FROM konten WHERE konto_id IN (1, 2);

START TRANSACTION;

    UPDATE konten SET kontostand = kontostand - 500 WHERE konto_id = 1;  -- Alice
    UPDATE konten SET kontostand = kontostand + 500 WHERE konto_id = 2;  -- Bob

    -- Ups! Falsche Überweisung, wir machen alles rückgängig
ROLLBACK;

SELECT 'NACH ROLLBACK:' AS info;
SELECT * FROM konten WHERE konto_id IN (1, 2);
-- Ergebnis: Alice=900, Bob=2100 → keine Änderung, alles zurückgesetzt


-- Beispiel 1c: Consistency – CHECK-Constraint verhindert negativen Kontostand
-- ----------------------------------------------------------------------------

START TRANSACTION;

    -- Alice hat nur 900 EUR, wir versuchen 1000 abzubuchen
    UPDATE konten SET kontostand = kontostand - 1000 WHERE konto_id = 1;
    -- Dies führt zu einem CHECK-Constraint-Fehler (kontostand >= 0)

ROLLBACK;
-- Die Datenbank bleibt konsistent


-- Beispiel 1d: Atomicity – 10 Datensätze importieren (Alles oder Nichts)
-- -----------------------------------------------------------------------

DROP TABLE IF EXISTS auftraege;
CREATE TABLE auftraege (
    auftrag_id  INT PRIMARY KEY AUTO_INCREMENT,
    kunde       VARCHAR(50)   NOT NULL,
    betrag      DECIMAL(8,2)  NOT NULL CHECK (betrag > 0)
);

-- ── Versuch 1: Alle 10 Datensätze korrekt → COMMIT ───────────────────────────

START TRANSACTION;

    INSERT INTO auftraege (kunde, betrag) VALUES
        ('Alice',   150.00),
        ('Bob',     230.50),
        ('Charlie',  89.99),
        ('Diana',   412.00),
        ('Eve',      75.25),
        ('Frank',   310.80),
        ('Grace',   195.40),
        ('Heidi',   520.00),
        ('Ivan',     67.30),
        ('Judy',    289.75);

COMMIT;

SELECT COUNT(*) AS importiert, SUM(betrag) AS gesamtbetrag FROM auftraege;
-- Ergebnis: 10 Zeilen → alle dauerhaft gespeichert


-- ── Versuch 2: Ein Datensatz verletzt CHECK → ROLLBACK ───────────────────────
-- Atomicity: entweder ALLE neuen Zeilen oder KEINE

START TRANSACTION;

    INSERT INTO auftraege (kunde, betrag) VALUES
        ('Karl',    180.00),   -- korrekt
        ('Laura',   -50.00);   -- FEHLER: betrag <= 0 → CHECK-Constraint

ROLLBACK;  -- Karl wird NICHT gespeichert (Atomicity!)

SELECT COUNT(*) AS importiert FROM auftraege;
-- Ergebnis: weiterhin 10 → Karl und Laura wurden nicht gespeichert


-- ============================================================================
-- 2. SAVEPOINTS: Teilweises Zurücksetzen
-- ============================================================================

START TRANSACTION;

    UPDATE konten SET kontostand = kontostand + 100 WHERE konto_id = 1;  -- Alice +100
    SAVEPOINT nach_alice;

    UPDATE konten SET kontostand = kontostand + 200 WHERE konto_id = 2;  -- Bob +200
    SAVEPOINT nach_bob;

    UPDATE konten SET kontostand = kontostand + 300 WHERE konto_id = 3;  -- Charlie +300

    -- Oops, Charlie-Buchung war falsch → nur diese zurücksetzen
    ROLLBACK TO nach_bob;

    -- Alice und Bob behalten ihre Änderungen
COMMIT;

SELECT * FROM konten;
-- Alice=1000, Bob=2300, Charlie=500 (unverändert)


-- ============================================================================
-- 3. AUTOCOMMIT-Verhalten in MySQL
-- ============================================================================

-- MySQL hat standardmäßig autocommit=1
SHOW VARIABLES LIKE 'autocommit';

-- Das bedeutet: Jedes einzelne Statement ist automatisch eine eigene Transaktion!
-- Zum Testen:

SET autocommit = 0;

UPDATE konten SET kontostand = kontostand + 1 WHERE konto_id = 1;
-- Änderung ist noch NICHT dauerhaft gespeichert!
-- In einer anderen Session sieht man den alten Wert (je nach Isolation Level)

ROLLBACK;  -- Macht die Änderung rückgängig

SET autocommit = 1;  -- Zurücksetzen auf Standard


-- ============================================================================
-- 4. ISOLATION LEVELS demonstrieren
-- ============================================================================

-- Aktuelles Isolation Level anzeigen
SELECT @@transaction_isolation;
-- Standard in MySQL InnoDB: REPEATABLE-READ

-- Isolation Level ändern (für die aktuelle Session):
-- SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
-- SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;


-- ============================================================================
-- 4a. DIRTY READ demonstrieren
-- ============================================================================
-- Benötigt ZWEI separate MySQL-Sessions (Terminal 1 und Terminal 2)

-- === SESSION 1 (Terminal 1) ===
-- SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
-- START TRANSACTION;
-- SELECT kontostand FROM konten WHERE konto_id = 1;
--   → zeigt 1000

-- === SESSION 2 (Terminal 2) ===
-- START TRANSACTION;
-- UPDATE konten SET kontostand = 9999 WHERE konto_id = 1;
-- (KEIN COMMIT!)

-- === SESSION 1 (Terminal 1) ===
-- SELECT kontostand FROM konten WHERE konto_id = 1;
--   → Bei READ UNCOMMITTED: zeigt 9999 (Dirty Read!)
--   → Bei READ COMMITTED oder höher: zeigt weiterhin 1000

-- === SESSION 2 (Terminal 2) ===
-- ROLLBACK;  -- Änderung wird zurückgenommen
--            -- Session 1 hat aber bereits den "dreckigen" Wert gelesen!


-- ============================================================================
-- 4b. NON-REPEATABLE READ demonstrieren
-- ============================================================================

-- === SESSION 1 (Terminal 1) ===
-- SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- START TRANSACTION;
-- SELECT kontostand FROM konten WHERE konto_id = 1;
--   → zeigt 1000

-- === SESSION 2 (Terminal 2) ===
-- UPDATE konten SET kontostand = 1500 WHERE konto_id = 1;
-- COMMIT;

-- === SESSION 1 (Terminal 1) ===
-- SELECT kontostand FROM konten WHERE konto_id = 1;
--   → Bei READ COMMITTED: zeigt 1500 (Non-Repeatable Read!)
--   → Bei REPEATABLE READ: zeigt weiterhin 1000 (konsistenter Snapshot)
-- COMMIT;


-- ============================================================================
-- 4c. PHANTOM READ demonstrieren
-- ============================================================================

-- === SESSION 1 (Terminal 1) ===
-- SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- START TRANSACTION;
-- SELECT COUNT(*) FROM konten;
--   → zeigt 3

-- === SESSION 2 (Terminal 2) ===
-- INSERT INTO konten VALUES (5, 'Eve', 100.00);
-- COMMIT;

-- === SESSION 1 (Terminal 1) ===
-- SELECT COUNT(*) FROM konten;
--   → Bei REPEATABLE READ (MySQL/InnoDB): zeigt weiterhin 3
--     (InnoDB verhindert Phantom Reads auch bei REPEATABLE READ durch Gap Locks!)
--   → Bei READ COMMITTED: könnte 4 zeigen (Phantom)
-- COMMIT;

-- Aufräumen:
-- DELETE FROM konten WHERE konto_id = 5;


-- ============================================================================
-- 5. LOCKING in der Praxis
-- ============================================================================

-- 5a. Shared Lock (FOR SHARE) – Lesesperre
-- -----------------------------------------
-- Mehrere Transaktionen können gleichzeitig lesen,
-- aber niemand kann schreiben, solange der Lock besteht.

START TRANSACTION;
    SELECT * FROM konten WHERE konto_id = 1 FOR SHARE;
    -- Andere Sessions können ebenfalls FOR SHARE lesen
    -- Aber UPDATE/DELETE auf diese Zeile wird blockiert
COMMIT;


-- 5b. Exclusive Lock (FOR UPDATE) – Schreibsperre
-- ------------------------------------------------
-- Nur eine Transaktion kann den Lock halten.

START TRANSACTION;
    SELECT * FROM konten WHERE konto_id = 1 FOR UPDATE;
    -- Nur diese Transaktion kann jetzt die Zeile ändern
    -- Andere Sessions werden bei jedem Zugriff blockiert
    UPDATE konten SET kontostand = kontostand - 50 WHERE konto_id = 1;
COMMIT;


-- 5c. Lock-Kompatibilitätsmatrix anzeigen
-- ----------------------------------------
-- Zur Veranschaulichung:
--
--                    | S-Lock angefordert | X-Lock angefordert
-- -------------------|--------------------|-----------------------
-- Kein Lock          |       OK           |        OK
-- S-Lock vorhanden   |       OK           |     BLOCKIERT
-- X-Lock vorhanden   |    BLOCKIERT       |     BLOCKIERT


-- ============================================================================
-- 6. LOST UPDATE demonstrieren (mit zwei Sessions)
-- ============================================================================

-- Ausgangslage: Alice hat 1000 EUR
-- Szenario: Zwei Transaktionen wollen gleichzeitig den Kontostand ändern

-- === SESSION 1 (Terminal 1): Abbuchung ===
-- START TRANSACTION;
-- SELECT kontostand FROM konten WHERE konto_id = 1;
--   → liest 1000
-- (Hier kurz warten, damit Session 2 ebenfalls lesen kann)

-- === SESSION 2 (Terminal 2): Zinsgutschrift ===
-- START TRANSACTION;
-- SELECT kontostand FROM konten WHERE konto_id = 1;
--   → liest ebenfalls 1000
-- UPDATE konten SET kontostand = 1000 * 1.03 WHERE konto_id = 1;
--   → schreibt 1030
-- COMMIT;

-- === SESSION 1 (Terminal 1) ===
-- UPDATE konten SET kontostand = 1000 - 100 WHERE konto_id = 1;
--   → schreibt 900 → Zinsgutschrift von Session 2 ist verloren!
-- COMMIT;

-- LÖSUNG: SELECT ... FOR UPDATE verwenden!
-- === SESSION 1 (korrigiert) ===
-- START TRANSACTION;
-- SELECT kontostand FROM konten WHERE konto_id = 1 FOR UPDATE;
--   → setzt einen exklusiven Lock auf die Zeile
--   → Session 2 muss warten bis Session 1 fertig ist


-- ============================================================================
-- 7. MVCC (Multi-Version Concurrency Control) demonstrieren
-- ============================================================================

-- MVCC-Testdaten
drop database if exists mvcc;
create database mvcc;
USE mvcc;
DROP TABLE IF EXISTS mvcc_demo;
CREATE TABLE mvcc_demo (
    id   INT PRIMARY KEY,
    wert INT
);
INSERT INTO mvcc_demo VALUES (1, 100), (2, 200), (3, 300);
select * from mvcc_demo;

-- === SESSION 1 (Terminal 1) ===
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT * FROM mvcc_demo;
-- → zeigt: 100, 200, 300
-- → Snapshot wird beim ersten SELECT erstellt

-- === SESSION 2 (Terminal 2) ===
START TRANSACTION;
UPDATE mvcc_demo SET wert = 999 WHERE id = 2;
COMMIT;
-- → Daten werden geändert (id=2 → 999)

-- === SESSION 1 (Terminal 1) ===
SELECT * FROM mvcc_demo;
--   → zeigt IMMER NOCH: 100, 200, 300
--   → liest aus dem Snapshot!

COMMIT;

-- === SESSION 1 (Terminal 1) ===
SELECT * FROM mvcc_demo;
--   → JETZT zeigt es: 100, 999, 300
--   → neuer Snapshot nach COMMIT

-- → MVCC ermöglicht konsistentes Lesen, ohne dass Leser und Schreiber sich blockieren.


-- ============================================================================
-- 8. DEADLOCK demonstrieren
-- ============================================================================

-- === SESSION 1 (Terminal 1) ===
-- START TRANSACTION;
-- UPDATE konten SET kontostand = kontostand - 10 WHERE konto_id = 1;
--   → X-Lock auf Konto 1

-- === SESSION 2 (Terminal 2) ===
-- START TRANSACTION;
-- UPDATE konten SET kontostand = kontostand - 10 WHERE konto_id = 2;
--   → X-Lock auf Konto 2

-- === SESSION 1 (Terminal 1) ===
-- UPDATE konten SET kontostand = kontostand + 10 WHERE konto_id = 2;
--   → will X-Lock auf Konto 2 → BLOCKIERT (Session 2 hält Lock)

-- === SESSION 2 (Terminal 2) ===
-- UPDATE konten SET kontostand = kontostand + 10 WHERE konto_id = 1;
--   → will X-Lock auf Konto 1 → DEADLOCK!
--   → MySQL erkennt dies automatisch und bricht eine Transaktion ab:
--   → ERROR 1213 (40001): Deadlock found when trying to get lock;
--     try restarting transaction

-- Deadlock-Informationen anzeigen:
SHOW ENGINE INNODB STATUS;
-- Im Abschnitt "LATEST DETECTED DEADLOCK" stehen die Details


-- ============================================================================
-- 8b. DEADLOCK mit WARTEGRAPH (3 Transaktionen)
-- ============================================================================
-- Benötigt DREI separate Sessions (Terminal 1, Terminal 2, Terminal 3)
-- Verbindung in DREI Terminals: docker exec -it skeleton-mysql mysql -u root -p
-- Entspricht dem Wartegraph-Beispiel: T1 → T2 → T3 → T1

-- Vorbereitung (in einer beliebigen Session):
show databases;
drop database if exists transaktion_demo;
create database transaktion_demo;
USE transaktion_demo;
DROP TABLE IF EXISTS ressourcen;
CREATE TABLE ressourcen (
    res_id   CHAR(1) PRIMARY KEY,
    wert     INT NOT NULL
);
INSERT INTO ressourcen VALUES ('A', 10), ('B', 20), ('C', 30), ('D', 40);
select * from ressourcen;

-- Ablauf:
--
--         t1     t2     t3     t4     t5     t6     t7     t8
--   T1    S(A)   S(D)                        S(B)
--   T2                  X(B)                        X(C)
--   T3                         S(D)   S(C)                 X(A)

-- Wartegraph:
--   t6: T1 will S(B) → T2 hält X(B) → T1 wartet auf T2  (T1→T2)
--   t7: T2 will X(C) → T3 hält S(C) → T2 wartet auf T3  (T2→T3)
--   t8: T3 will X(A) → T1 hält S(A) → T3 wartet auf T1  (T3→T1)
--   → Zyklus: T1 → T2 → T3 → T1 = DEADLOCK!

-- SCHRITT 1: Alle drei Sessions starten ihre Transaktionen
-- und holen sich die ersten Locks (t1–t3)

-- === SESSION 1 (Terminal 1) ===
-- select connection_id();
USE transaktion_demo;
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'A' FOR SHARE;    -- t1: S(A)
SELECT * FROM ressourcen WHERE res_id = 'D' FOR SHARE;    -- t2: S(D)

-- === SESSION 2 (Terminal 2) ===
-- select connection_id();
USE transaktion_demo;
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'B' FOR UPDATE;   -- t3: X(B)

-- === SESSION 3 (Terminal 3) ===
-- select connection_id();
USE transaktion_demo;
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'D' FOR SHARE;    -- t4: S(D) → OK, S+S verträglich
SELECT * FROM ressourcen WHERE res_id = 'C' FOR SHARE;    -- t5: S(C)

-- SCHRITT 2: Jetzt die Konflikte auslösen

-- === SESSION 1 (Terminal 1) ===
SELECT * FROM ressourcen WHERE res_id = 'B' FOR SHARE;
--   → t6: T1 will S(B), aber T2 hält X(B) → T1 BLOCKIERT (wartet auf T2)

-- === SESSION 2 (Terminal 2) ===
UPDATE ressourcen SET wert = 99 WHERE res_id = 'C';
--   → t7: T2 will X(C), aber T3 hält S(C) → T2 BLOCKIERT (wartet auf T3)

-- === SESSION 3 (Terminal 3) ===
UPDATE ressourcen SET wert = 99 WHERE res_id = 'A';
--   → t8: T3 will X(A), aber T1 hält S(A) → DEADLOCK erkannt!
--   → MySQL bricht eine der drei Transaktionen ab (diejenige mit geringstem Aufwand)
--   → ERROR 1213 (40001): Deadlock found when trying to get lock

-- SCHRITT 3: Deadlock analysieren
 SHOW ENGINE INNODB STATUS\G
--   → Unter "LATEST DETECTED DEADLOCK" sieht man den Zyklus
--   → MySQL zeigt welche Transaktion abgebrochen wurde ("WE ROLL BACK TRANSACTION ...")

-- Die anderen beiden Transaktionen können jetzt weiterlaufen:
-- (in den nicht-abgebrochenen Sessions)
COMMIT;

-- Aufräumen:
DROP TABLE IF EXISTS ressourcen;


-- ============================================================================
-- 8c. WAIT-DIE UND WOUND-WAIT (Deadlock-Prävention mit Zeitstempeln)
-- ============================================================================
-- Beide Strategien VERHINDERN Deadlocks proaktiv.
-- Grundidee: Jede Transaktion erhält beim Start einen Zeitstempel.
--            Konflikte werden anhand des Alters (alt = früher gestartet) aufgelöst.
--
-- WICHTIG:
-- MySQL implementiert Wait-Die und Wound-Wait NICHT nativ.
-- Die folgenden Abläufe zeigen nur reale Sperrkonflikte in MySQL.
-- Die Entscheidung "warten" oder "abbrechen" wird anschließend
-- THEORETISCH nach den Regeln interpretiert.

-- ============================================================================
-- WAIT-DIE ("Wait if older – Die if younger")
-- ============================================================================
-- Regel:
--   • Ältere T fordert Sperre an  → darf warten
--   • Jüngere T fordert Sperre an → wird abgebrochen
--
-- Merksatz:
--   Alt wartet, jung stirbt.

-- === SESSION 1 (Terminal 1) – Ältere Transaktion (Zeitstempel t=10) ===
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'A' FOR UPDATE;
--  → T1 hält X-Lock auf Ressource A
SELECT SLEEP(60);
--   → simuliert lange Verarbeitung

-- === SESSION 2 (Terminal 2) – Jüngere Transaktion (Zeitstempel t=20) ===
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'A' FOR UPDATE;
-- MySQL: T2 wartet auf den Lock von T1.
-- Theorie (Wait-Die): Da T2 jünger ist als T1, würde T2 sofort abgebrochen.
ROLLBACK;
-- Nach der MySQL-Demo manuell zurücksetzen;
-- in der Theorie von Wait-Die wäre T2 bereits vorher abgebrochen worden.

-- === SESSION 1 (Terminal 1) ===
COMMIT;  -- T1 beendet regulär


-- ============================================================================
-- WOUND-WAIT ("Wound if older – Wait if younger")
-- ============================================================================
-- Regel:
--   • Ältere T fordert Sperre an  → jüngere wird abgebrochen
--   • Jüngere T fordert Sperre an → muss warten
--
-- Merksatz:
--   Alt verwundet, jung wartet.

-- === SESSION 2 (Terminal 2) – Jüngere Transaktion (Zeitstempel t=20) ===
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'A' FOR UPDATE;
-- → T2 hält X-Lock auf A
 SELECT SLEEP(60);
--   → simuliert lange Verarbeitung

-- === SESSION 1 (Terminal 1) – Ältere Transaktion (Zeitstempel t=10) ===
START TRANSACTION;
SELECT * FROM ressourcen WHERE res_id = 'A' FOR UPDATE;
-- MySQL: T1 wartet auf den Lock von T2.
-- Theorie (Wound-Wait): T1 ist älter → würde T2 abbrechen
-- und den Lock sofort bekommen.

-- === SESSION 2 ===
ROLLBACK;
-- Aufräumen nach der Demo

-- === SESSION 1 ===
COMMIT;


-- ── Vergleich ────────────────────────────────────────────────────────────────
-- Strategie    │ Ältere T fordert an  │ Jüngere T fordert an
-- ─────────────┼──────────────────────┼──────────────────────
-- Wait-Die     │ Darf warten          │ Wird abgebrochen
-- Wound-Wait   │ Bricht jüngere ab    │ Muss warten
--
-- Beide Strategien sind verklemmungsfrei:
-- Zeitstempel sind eindeutig → kein Zyklus im Wartegraph möglich.


-- ============================================================================
-- 9. PRAXISBEISPIEL: Sichere Bestellung mit Bestandsprüfung
-- ============================================================================

DELIMITER //

CREATE PROCEDURE bestelle_produkt(
    IN p_produkt_id INT,
    IN p_menge INT,
    OUT p_status VARCHAR(100)
)
BEGIN
    DECLARE v_bestand INT;

    -- Fehlerbehandlung: Bei Fehler automatisch ROLLBACK
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'FEHLER: Transaktion wurde zurückgesetzt';
    END;

    START TRANSACTION;

        -- Exklusiver Lock auf die Zeile (FOR UPDATE)
        SELECT bestand INTO v_bestand
        FROM produkte
        WHERE produkt_id = p_produkt_id
        FOR UPDATE;

        -- Bestandsprüfung
        IF v_bestand >= p_menge THEN
            UPDATE produkte
            SET bestand = bestand - p_menge
            WHERE produkt_id = p_produkt_id;

            SET p_status = CONCAT('OK: ', p_menge, ' Stück bestellt. Restbestand: ', v_bestand - p_menge);
            COMMIT;
        ELSE
            SET p_status = CONCAT('ABGELEHNT: Nur ', v_bestand, ' auf Lager, ', p_menge, ' angefordert.');
            ROLLBACK;
        END IF;
END //

DELIMITER ;

-- Test: Bestellung aufgeben
CALL bestelle_produkt(1, 3, @status);
SELECT @status;
SELECT * FROM produkte WHERE produkt_id = 1;

-- Test: Zu viel bestellen
CALL bestelle_produkt(3, 100, @status);
SELECT @status;
SELECT * FROM produkte WHERE produkt_id = 3;


-- ============================================================================
-- 10. PRAXISBEISPIEL: Überweisung als Stored Procedure
-- ============================================================================

DELIMITER //

CREATE PROCEDURE ueberweise(
    IN p_von INT,
    IN p_nach INT,
    IN p_betrag DECIMAL(10,2),
    OUT p_status VARCHAR(200)
)
BEGIN
    DECLARE v_saldo DECIMAL(10,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'FEHLER: Transaktion wurde zurückgesetzt';
    END;

    START TRANSACTION;

        -- Beide Konten sperren (immer in gleicher Reihenfolge → verhindert Deadlocks!)
        SELECT kontostand INTO v_saldo
        FROM konten
        WHERE konto_id = p_von
        FOR UPDATE;

        SELECT kontostand FROM konten
        WHERE konto_id = p_nach
        FOR UPDATE;

        -- Saldo prüfen
        IF v_saldo >= p_betrag THEN
            UPDATE konten SET kontostand = kontostand - p_betrag WHERE konto_id = p_von;
            UPDATE konten SET kontostand = kontostand + p_betrag WHERE konto_id = p_nach;

            SET p_status = CONCAT('OK: ', p_betrag, ' EUR von Konto ', p_von, ' an Konto ', p_nach);
            COMMIT;
        ELSE
            SET p_status = CONCAT('ABGELEHNT: Konto ', p_von, ' hat nur ', v_saldo, ' EUR');
            ROLLBACK;
        END IF;
END //

DELIMITER ;

-- Test: Erfolgreiche Überweisung
SELECT * FROM konten;
CALL ueberweise(2, 3, 300, @status);
SELECT @status;
SELECT * FROM konten;

-- Test: Überweisung abgelehnt (zu wenig Guthaben)
CALL ueberweise(3, 1, 9999, @status);
SELECT @status;


-- ============================================================================
-- 11. NÜTZLICHE DIAGNOSE-BEFEHLE
-- ============================================================================

-- Aktuelle Storage Engine und Transaktionsunterstützung
SHOW ENGINES;

-- Aktuelles Isolation Level
SELECT @@transaction_isolation;
SELECT @@global.transaction_isolation;

-- Autocommit-Status
SELECT @@autocommit;

-- InnoDB-spezifische Einstellung für Durability
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';

-- Aktive Locks anzeigen (bei laufenden Transaktionen)
SELECT * FROM performance_schema.data_locks;

-- Wartende Lock-Anfragen anzeigen
SELECT * FROM performance_schema.data_lock_waits;

-- Laufende Transaktionen anzeigen
SELECT * FROM information_schema.innodb_trx;

-- Letzten Deadlock anzeigen
SHOW ENGINE INNODB STATUS;


-- ============================================================================
-- AUFRÄUMEN
-- ============================================================================

-- DROP DATABASE transaktionen_demo;
