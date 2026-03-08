-- =============================================================================
-- SQL DDL Skript – Alle SQL-Statements aus der Vorlesung "Datenbanken 8 – SQL DDL"
-- Kurs: Informatik 24ITA, DHBW Stuttgart
-- Ziel-DBMS: MySQL 8.4
-- =============================================================================

-- =============================================================================
-- Datenbank-Setup (DB-Name entspricht dem Skriptnamen)
-- =============================================================================
DROP DATABASE IF EXISTS DDL_Skripte;
DROP DATABASE IF EXISTS DDL_Skripte;
CREATE DATABASE DDL_Skripte
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE DDL_Skripte;


-- =============================================================================
-- Anforderungen an eine Data Definition Language
-- =============================================================================

-- (1) Attribute definieren / (3) Relationenschemata anlegen
CREATE TABLE Student (
    Matrikelnummer INT PRIMARY KEY,
    Name VARCHAR(50),
    Geburtsdatum DATE
);

-- (2) Wertebereiche festlegen
ALTER TABLE Student ADD CHECK (Matrikelnummer > 0);

-- (4) Primär- und Fremdschlüssel festlegen
-- Hinweis: Setzt voraus, dass die Tabelle "Kurs" bereits existiert.
CREATE TABLE Kurs (
    KursID INT PRIMARY KEY,
    Bezeichnung VARCHAR(100)
);

CREATE TABLE Einschreibung (
    StudentID INT,
    KursID INT,
    PRIMARY KEY (StudentID, KursID),
    FOREIGN KEY (StudentID) REFERENCES Student(Matrikelnummer)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (KursID) REFERENCES Kurs(KursID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Beispiel: Wirkung von ON DELETE/ON UPDATE CASCADE
INSERT INTO Student (Matrikelnummer, Name, Geburtsdatum)
VALUES (1, 'Max', '2000-01-01');

INSERT INTO Kurs (KursID, Bezeichnung)
VALUES (10, 'Datenbanken');

INSERT INTO Einschreibung (StudentID, KursID)
VALUES (1, 10);

-- ON DELETE CASCADE: Löscht Einschreibung automatisch
DELETE FROM Student WHERE Matrikelnummer = 1;

-- Wieder anlegen für Update-Beispiel
INSERT INTO Student (Matrikelnummer, Name, Geburtsdatum)
VALUES (1, 'Max', '2000-01-01');
INSERT INTO Einschreibung (StudentID, KursID)
VALUES (1, 10);

-- ON UPDATE CASCADE: Aktualisiert FK-Werte automatisch
UPDATE Student SET Matrikelnummer = 2 WHERE Matrikelnummer = 1;

-- Kontrolle
SELECT * FROM Einschreibung As Einschreibungen
   INNER JOIN Student As Studenten ON Einschreibungen.StudentID = Studenten.Matrikelnummer
   INNER JOIN Kurs As Kurse ON Einschreibungen.KursID = Kurse.KursID;;


-- =============================================================================
-- SQL Konzepte in drei Schichten / Ebenen
-- =============================================================================

-- Konzeptuelle Ebene
-- CREATE TABLE <TabellenName> (<attrib-name> <Wertebereich>, ...)
-- DROP TABLE <TabellenName>
-- ALTER TABLE <TabellenName> [...]

-- Externe Ebene
-- CREATE VIEW <Sichtname> [<Schemadeklaration>] AS <SQL-Anfrage>
-- DROP VIEW <Sichtname>

-- Interne Ebene
-- CREATE INDEX <IndexName> ON <TabellenName> (<indexcol> ...)
-- DROP INDEX <IndexName>
-- ALTER INDEX <IndexName> [...]


-- =============================================================================
-- Tabellen – CREATE TABLE Grundsyntax
-- =============================================================================

-- Allgemeine Syntax:
-- CREATE TABLE <Relationenname>
--     (<Spaltenname_1> <Wertebereich_1> [NOT NULL],
--      ...
--      <Spaltenname_n> <Wertebereich_n> [NOT NULL])

-- Wertebereiche (SQL-Standard vs. MySQL 8.4):
--   integer / INT              -> INT (4 Byte)
--   smallint                   -> SMALLINT (2 Byte)
--   float(p) / float           -> FLOAT / DOUBLE
--   decimal(p,q)               -> DECIMAL(p,q)
--   character(n) / char(n)     -> CHAR(n)
--   character varying(n)       -> VARCHAR(n)
--   bit(n) / bit varying(n)    -> BIT(n) (MySQL: kein BIT VARYING)
--   date, time, timestamp      -> DATE, TIME, TIMESTAMP / DATETIME


-- =============================================================================
-- Tabellen – Details und Beispiele mit CREATE DOMAIN
-- =============================================================================

-- ACHTUNG: CREATE DOMAIN existiert NICHT in MySQL 8.4!
-- Die folgenden Statements sind SQL-Standard und dienen nur der Illustration.

-- SQL-Standard (NICHT MySQL-kompatibel):
-- CREATE DOMAIN Gebiete varchar(20) DEFAULT 'Informatik';
-- CREATE DOMAIN Gebiete varchar(20) DEFAULT 'Informatik'
--     CHECK (VALUE IN ('Informatik', 'Mathematik', 'Elektrotechnik', 'Linguistik'));

-- ---- MySQL 8.4 Äquivalent (Variante 1: mit ENUM) ----
CREATE TABLE Vorlesungen_v1 (
    V_Bezeichnung VARCHAR(80) NOT NULL PRIMARY KEY,
    SWS SMALLINT CHECK (SWS > 0),
    Semester SMALLINT CHECK (Semester BETWEEN 1 AND 9),
    Studiengang ENUM('Informatik', 'Mathematik', 'Elektrotechnik', 'Linguistik')
        DEFAULT 'Informatik'
);

-- ---- MySQL 8.4 Äquivalent (Variante 2: mit CHECK) ----
CREATE TABLE Vorlesungen_v2 (
    V_Bezeichnung VARCHAR(80) NOT NULL PRIMARY KEY,
    SWS SMALLINT CHECK (SWS > 0),
    Semester SMALLINT CHECK (Semester BETWEEN 1 AND 9),
    Studiengang VARCHAR(20) DEFAULT 'Informatik'
        CHECK (Studiengang IN ('Informatik', 'Mathematik', 'Elektrotechnik', 'Linguistik'))
);


-- =============================================================================
-- Tabellen – Beispiele (2)
-- =============================================================================

-- Voraussetzung: Tabelle Bücher muss existieren
CREATE TABLE Buecher (
    ISBN CHAR(10) NOT NULL PRIMARY KEY
);

CREATE TABLE Buch_Versionen (
    ISBN CHAR(10) NOT NULL,
    Auflage SMALLINT CHECK (Auflage > 0),
    Jahr INT CHECK (Jahr BETWEEN 1800 AND 2030),       -- aktualisiert (war: 2020)
    Seiten INT CHECK (Seiten > 0),
    Preis DECIMAL(8,2) CHECK (Preis <= 250),
    PRIMARY KEY (ISBN, Auflage),
    FOREIGN KEY (ISBN) REFERENCES Buecher(ISBN)
);

-- ACHTUNG: Der folgende CHECK-Constraint aus dem Skript ist in MySQL 8.4
-- NICHT möglich, da Subqueries in CHECK-Constraints nicht unterstützt werden:
--
--   CHECK ((SELECT SUM(Preis) FROM Buch_Versionen) <
--          (SELECT SUM(Budget) FROM Lehrstuehle))
--
-- Alternative in MySQL 8.4: Über einen TRIGGER lösen.


-- =============================================================================
-- Ändern und Löschen einer Tabelle
-- =============================================================================

-- Spalte hinzufügen
ALTER TABLE Buch_Versionen
    ADD Sprache VARCHAR(30) DEFAULT 'Deutsch'
    CHECK (Sprache IN ('Deutsch', 'Englisch', 'Französisch'));

-- Default-Wert ändern
ALTER TABLE Buch_Versionen
    ALTER COLUMN Sprache SET DEFAULT 'Englisch';

-- Spalte entfernen
-- HINWEIS: RESTRICT und CASCADE werden von MySQL 8.4 geparst, aber ignoriert!
ALTER TABLE Buch_Versionen
    DROP COLUMN Sprache;

-- Tabelle löschen
-- HINWEIS: RESTRICT und CASCADE werden von MySQL 8.4 geparst, aber ignoriert!
-- MySQL löscht NICHT automatisch abhängige Fremdschlüssel-Tabellen.
-- DROP TABLE Buch_Versionen RESTRICT;
-- DROP TABLE Buch_Versionen CASCADE;
DROP TABLE Buch_Versionen;


-- =============================================================================
-- Index anlegen
-- =============================================================================

-- Allgemeine Syntax:
-- CREATE [UNIQUE] INDEX <IndexName>
--     ON <RelationenName> (<Spaltenname_1> <ordnung_1>, ...)

-- Beispiel:
CREATE INDEX idx_vorlesung_semester
    ON Vorlesungen_v1 (Semester ASC);

CREATE UNIQUE INDEX idx_vorlesung_bezeichnung
    ON Vorlesungen_v1 (V_Bezeichnung ASC);

-- Index löschen (MySQL-Syntax):
-- DROP INDEX idx_vorlesung_semester ON Vorlesungen_v1;

-- =============================================================================
-- Beispiele: UNIQUE-Constraint und AUTO_INCREMENT
-- =============================================================================

CREATE TABLE Mitarbeiter (
    ID INT PRIMARY KEY,
    Email VARCHAR(100) UNIQUE,
    Name VARCHAR(50) NOT NULL
);

CREATE TABLE Kurs_auto (
    KursID INT AUTO_INCREMENT PRIMARY KEY,
    Bezeichnung VARCHAR(80) NOT NULL
);


-- =============================================================================
-- MySQL-spezifische Syntax (korrigiert für MySQL 8.4)
-- =============================================================================

-- Datenbank ist bereits angelegt (siehe Kopfbereich).

-- Tabelle erstellen mit MySQL-8.4-Optionen
CREATE TABLE beispiel_tabelle (
    id INT NOT NULL AUTO_INCREMENT,
    bezeichnung VARCHAR(100) NOT NULL,
    beschreibung TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_bezeichnung (bezeichnung)
) ENGINE = InnoDB;                          -- korrigiert (war: TYPE=INNODB)

-- Hinweis zu verfügbaren Engines in MySQL 8.4:
--   InnoDB  (Standard, transaktionssicher, Fremdschlüssel)
--   MyISAM  (kein Transaktionssupport, kein FK)
--   MEMORY  (korrigiert: war HEAP, in-memory, temporär)
--   CSV, ARCHIVE, BLACKHOLE, ...
-- ISAM existiert seit MySQL 5.0 nicht mehr.

-- Fremdschlüssel mit referentiellen Aktionen
CREATE TABLE beispiel_detail (
    detail_id INT NOT NULL AUTO_INCREMENT,
    beispiel_id INT NOT NULL,
    wert DECIMAL(10,2),
    PRIMARY KEY (detail_id),
    FOREIGN KEY (beispiel_id) REFERENCES beispiel_tabelle(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- =============================================================================
-- INSERT und LOAD DATA (Nachtrag zu DML)
-- =============================================================================

-- INSERT-Varianten
INSERT INTO Vorlesungen_v1 (V_Bezeichnung, SWS, Semester, Studiengang)
    VALUES ('Datenbanksysteme', 4, 3, 'Informatik');

INSERT INTO Vorlesungen_v1 (V_Bezeichnung, SWS, Semester, Studiengang)
    VALUES ('Algorithmen', 4, 2, 'Informatik'),
           ('Lineare Algebra', 4, 1, 'Mathematik');

-- INSERT ... SET (MySQL-spezifisch)
INSERT INTO Vorlesungen_v1
    SET V_Bezeichnung = 'Compilerbau',
        SWS = 2,
        Semester = 5,
        Studiengang = 'Informatik';

-- INSERT ... SELECT
-- INSERT INTO Vorlesungen_v1 (V_Bezeichnung, SWS, Semester, Studiengang)
--     SELECT ... FROM andere_tabelle WHERE ...;

-- LOAD DATA INFILE
-- HINWEIS: In MySQL 8.4 ist local_infile standardmäßig deaktiviert!
-- Vorher ausführen: SET GLOBAL local_infile = 1;
-- Alternativ: MySQL-Server mit --local-infile=1 starten.
--
-- LOAD DATA INFILE '/pfad/zur/datei.csv'
--     INTO TABLE Vorlesungen_v1
--     FIELDS TERMINATED BY '\t'
--     ENCLOSED BY ''
--     ESCAPED BY '\\'
--     LINES TERMINATED BY '\n'
--     IGNORE 1 LINES
--     (V_Bezeichnung, SWS, Semester, Studiengang);


-- =============================================================================
-- Aufräumen (optional, zum Zurücksetzen)
-- =============================================================================

-- DROP TABLE IF EXISTS beispiel_detail;
-- DROP TABLE IF EXISTS beispiel_tabelle;
-- DROP TABLE IF EXISTS Buch_Versionen;
-- DROP TABLE IF EXISTS Buecher;
-- DROP TABLE IF EXISTS Einschreibung;
-- DROP TABLE IF EXISTS Kurs;
-- DROP TABLE IF EXISTS Student;
-- DROP TABLE IF EXISTS Vorlesungen_v1;
-- DROP TABLE IF EXISTS Vorlesungen_v2;
-- DROP DATABASE IF EXISTS DDL_Skripte;

-- Abschlussmeldung
SELECT
  'DDL_Skripte.sql erfolgreich durchgelaufen.' AS status,
  NOW() AS executed_at;
