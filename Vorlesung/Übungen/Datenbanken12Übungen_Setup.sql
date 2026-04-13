-- ------------------------------------------------------------
-- Basis-Setup für das Übungs-SQL zu Views
-- MySQL-kompatibel
-- ------------------------------------------------------------

-- Falls bereits vorhanden: zuerst abhängige Tabellen löschen
DROP TABLE IF EXISTS KLAUSUR;
DROP TABLE IF EXISTS THEMA;
DROP TABLE IF EXISTS STUDENT;
DROP TABLE IF EXISTS FACHBEREICH;
DROP TABLE IF EXISTS KURS;
DROP TABLE IF EXISTS DOZENT;

-- ------------------------------------------------------------
-- Tabellen
-- ------------------------------------------------------------

CREATE TABLE FACHBEREICH (
    FB INT PRIMARY KEY,
    NAME VARCHAR(100) NOT NULL
);

CREATE TABLE STUDENT (
    MATNR INT PRIMARY KEY,
    NAME VARCHAR(100) NOT NULL,
    VORNAME VARCHAR(100) NOT NULL,
    FB INT NOT NULL,
    EMAIL VARCHAR(200),
    BIRTHDAY DATE,
    CONSTRAINT FK_STUDENT_FACHBEREICH
        FOREIGN KEY (FB) REFERENCES FACHBEREICH(FB)
);

CREATE TABLE KLAUSUR (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    MATNR INT NOT NULL,
    RESULTAT DECIMAL(3,1) NOT NULL,
    CONSTRAINT FK_KLAUSUR_STUDENT
        FOREIGN KEY (MATNR) REFERENCES STUDENT(MATNR)
);

CREATE TABLE KURS (
    TNR INT PRIMARY KEY
);

CREATE TABLE DOZENT (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    VORNAME VARCHAR(100) NOT NULL
);

CREATE TABLE THEMA (
    TNR INT NOT NULL,
    NAME VARCHAR(100) NOT NULL
);

-- ------------------------------------------------------------
-- Testdaten
-- ------------------------------------------------------------

INSERT INTO FACHBEREICH (FB, NAME) VALUES
(1, 'Mathematik'),
(2, 'Informatik'),
(3, 'Wirtschaft');

INSERT INTO STUDENT (MATNR, NAME, VORNAME, FB, EMAIL, BIRTHDAY) VALUES
(1000, 'Alpha',    'Anna',    1, 'anna.alpha@fooschule.de',    '2003-03-21'),
(1001, 'Adams',    'Anton',   1, 'anton.adams@fooschule.de',   '2001-02-10'),
(1002, 'Edith',    'Eva',     1, 'eva.edith@fooschule.de',     '1999-07-15'),
(1003, 'Braun',    'Berta',   2, 'berta.braun@fooschule.de',   '2004-11-05'),
(1004, 'Zuse',     'Konrad',  2, 'konrad.zuse@fooschule.de',   '1998-06-22'),
(1005, 'Albrecht', 'Anja',    1, 'anja.albrecht@fooschule.de', '2002-01-08');

INSERT INTO KLAUSUR (MATNR, RESULTAT) VALUES
(1000, 1.7),
(1000, 2.0),
(1000, 1.3),
(1001, 2.3),
(1001, 2.0),
(1002, 1.3),
(1002, 1.7),
(1003, 3.0),
(1003, 2.7),
(1004, 2.0),
(1005, 1.0),
(1005, 1.3);

INSERT INTO KURS (TNR) VALUES
(1),
(2),
(3);

INSERT INTO DOZENT (VORNAME) VALUES
('Meyer'),
('Schmidt'),
('TestDozent');

INSERT INTO THEMA (TNR, NAME) VALUES
(1, 'SQL-Grundlagen'),
(2, 'Sichten'),
(3, 'Rechte in SQL'),
(4, 'Nicht zugeordnetes Thema');

-- ------------------------------------------------------------
-- Kontrollabfragen
-- ------------------------------------------------------------

SELECT * FROM FACHBEREICH;
SELECT * FROM STUDENT;
SELECT * FROM KLAUSUR;
SELECT * FROM KURS;
SELECT * FROM DOZENT;
SELECT * FROM THEMA;