-- --------------------------------------------------------------
-- - Szenario: Views
-- --------------------------------------------------------------

-- GRANT SELECT ON kessler_test_kessler.allstudents TO foo1@localhost;
-- GRANT SELECT ON kessler_test_kessler.allstudentswithbirthday TO foo1@localhost;

-- REVOKE SELECT ON kessler_test_kessler.allstudentswithbirthday FROM foo1@localhost;

DROP VIEW IF EXISTS allStudents;
DROP VIEW IF EXISTS allStudentsWithBirthday;
DROP VIEW IF EXISTS allStudentsWithBirthdayWithCheckOption;
DROP VIEW IF EXISTS allMatheStudentsWith;
DROP VIEW IF EXISTS allStudentsAvgByMatnr;
DROP VIEW IF EXISTS kursView;
DROP VIEW IF EXISTS kursThemaView;

-- Damit das Skript mehrfach ausführbar bleibt
DELETE FROM STUDENT WHERE MATNR IN (2000, 2001);
UPDATE STUDENT
SET BIRTHDAY = '2003-03-21'
WHERE MATNR = 1000;

-- --------------------------------------------------------------
-- 1) Einfache View
-- --------------------------------------------------------------
CREATE VIEW allStudents AS
SELECT *
FROM STUDENT;

SELECT NAME, VORNAME
FROM STUDENT
WHERE NAME LIKE 'a%' AND VORNAME LIKE 'a%';

SELECT *
FROM allStudents
WHERE NAME LIKE 'a%' AND VORNAME LIKE 'a%';

-- --------------------------------------------------------------
-- 2) Selektionssicht
-- --------------------------------------------------------------
CREATE VIEW allStudentsWithBirthday AS
SELECT NAME, VORNAME
FROM STUDENT
WHERE BIRTHDAY >= '2000-01-01'
WITH CHECK OPTION;

SELECT *
FROM allStudentsWithBirthday
WHERE NAME LIKE 'a%' AND VORNAME LIKE 'a%';

-- --------------------------------------------------------------
-- 3) Selektionssicht mit CHECK OPTION
-- --------------------------------------------------------------
CREATE VIEW allStudentsWithBirthdayWithCheckOption AS
SELECT *
FROM STUDENT
WHERE BIRTHDAY >= '2000-01-01'
WITH CHECK OPTION;

-- DELETE FROM allStudents WHERE MATNR = 2000;

INSERT INTO allStudents (MATNR, NAME, VORNAME, FB, EMAIL, BIRTHDAY)
VALUES (2000, 'Kessler', 'Karsten', 1, 'Karsten.Kessler@fooschule.de', '1967-03-21');
-- --> geht, da allStudents alle Tupel aus STUDENT enthält

INSERT INTO allStudentsWithBirthdayWithCheckOption (MATNR, NAME, VORNAME, FB, EMAIL, BIRTHDAY)
VALUES (2001, 'Kessler1', 'Karsten1', 1, 'Karsten1.Kessler1@fooschule.de', '1967-03-21');
-- --> geht nicht, da die Bedingung BIRTHDAY >= '2000-01-01' verletzt wird

UPDATE allStudentsWithBirthdayWithCheckOption
SET BIRTHDAY = '2010-03-21'
WHERE MATNR = 1000;
-- --> geht, da der Datensatz danach weiterhin in der View enthalten ist

UPDATE allStudentsWithBirthdayWithCheckOption
SET BIRTHDAY = '1967-03-21'
WHERE MATNR = 1000;
-- --> geht nicht, da WITH CHECK OPTION verletzt wird

UPDATE allStudents
SET BIRTHDAY = '1967-03-22'
WHERE MATNR = 1000;
-- --> geht, da auf allStudents keine CHECK OPTION wirkt

-- --------------------------------------------------------------
-- 4) Join-View
-- --------------------------------------------------------------
CREATE VIEW allMatheStudentsWith AS
SELECT s.NAME AS SNAME,
       fb.NAME AS FBNAME
FROM STUDENT s
INNER JOIN FACHBEREICH fb
    ON s.FB = fb.FB
WHERE fb.FB = 1;

SELECT *
FROM allMatheStudentsWith;

-- Achtung:
-- Änderungen auf Join-Views sind problematisch und DBMS-abhängig.
-- Daher hier nur lesen, kein UPDATE testen.
-- UPDATE allMatheStudentsWith
-- SET SNAME = 'Edith2'
-- WHERE SNAME = 'Edith';

-- --------------------------------------------------------------
-- 5) Aggregationssicht
-- --------------------------------------------------------------
CREATE VIEW allStudentsAvgByMatnr (MATNR, Durchschnittsnote) AS
SELECT MATNR, AVG(RESULTAT)
FROM KLAUSUR
GROUP BY MATNR;

SELECT *
FROM allStudentsAvgByMatnr
WHERE MATNR = 1000;

UPDATE allStudentsAvgByMatnr
SET Durchschnittsnote = 1.0
WHERE MATNR = 1000;
-- --> geht nicht, da Aggregationssichten nicht updatable sind

-- --------------------------------------------------------------
-- 6) Weitere View mit mehreren Tabellen
-- --------------------------------------------------------------
CREATE VIEW kursView AS
SELECT TNR, VORNAME
FROM KURS, DOZENT;

SELECT *
FROM kursView;

-- Kein INSERT auf diese View:
-- Die View basiert auf mehreren Tabellen und ist nicht sinnvoll änderbar.
-- INSERT INTO kursView VALUES (1, 'Test');

-- --------------------------------------------------------------
-- 7) View mit Unteranfrage
-- --------------------------------------------------------------
CREATE VIEW kursThemaView AS
SELECT *
FROM THEMA t
WHERE t.TNR IN (SELECT TNR FROM kursView);

SELECT NAME
FROM kursThemaView;

-- ------------------------------------------------------------