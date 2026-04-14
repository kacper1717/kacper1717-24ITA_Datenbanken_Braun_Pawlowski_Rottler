-- --------------------------------------------------------------
-- Szenario: Rechte, Rollen und Sichten
-- angepasst an Schema `25_26_2`
-- --------------------------------------------------------------

USE mysql;

-- --------------------------------------------------------------
-- 1) Benutzer anlegen
-- --------------------------------------------------------------
CREATE USER IF NOT EXISTS 'admin1'@'localhost' IDENTIFIED BY 'admin1pass';
CREATE USER IF NOT EXISTS 'dozent1'@'localhost' IDENTIFIED BY 'dozent1pass';
CREATE USER IF NOT EXISTS 'student1'@'localhost' IDENTIFIED BY 'student1pass';
CREATE USER IF NOT EXISTS 'dau1'@'localhost' IDENTIFIED BY 'dau1pass';

-- --------------------------------------------------------------
-- 2) Rollen anlegen
-- --------------------------------------------------------------
CREATE ROLE IF NOT EXISTS 'adminrolle';
CREATE ROLE IF NOT EXISTS 'dozentrolle';
CREATE ROLE IF NOT EXISTS 'studentrolle';
CREATE ROLE IF NOT EXISTS 'daurolle';

-- --------------------------------------------------------------
-- 3) Rechte an Rollen vergeben
-- --------------------------------------------------------------

-- Admin: volle Sicht auf alles + Änderungsrechte auf Basistabellen
GRANT SELECT ON `25_26_2`.* TO 'adminrolle';
GRANT INSERT, UPDATE, DELETE ON `25_26_2`.student TO 'adminrolle';
GRANT INSERT, UPDATE, DELETE ON `25_26_2`.klausur TO 'adminrolle';
GRANT INSERT, UPDATE, DELETE ON `25_26_2`.kurs TO 'adminrolle';
GRANT INSERT, UPDATE, DELETE ON `25_26_2`.dozent TO 'adminrolle';
GRANT INSERT, UPDATE, DELETE ON `25_26_2`.fachbereich TO 'adminrolle';
GRANT INSERT, UPDATE, DELETE ON `25_26_2`.thema TO 'adminrolle';

-- Dozent: typische Leserechte auf ausgewählte Views
GRANT SELECT ON `25_26_2`.allstudents TO 'dozentrolle';
GRANT SELECT ON `25_26_2`.allmathestudentswith TO 'dozentrolle';
GRANT SELECT ON `25_26_2`.kursview TO 'dozentrolle';
GRANT SELECT ON `25_26_2`.kursthemaview TO 'dozentrolle';

-- Student: eingeschränkte Leserechte auf ausgewählte Views
GRANT SELECT ON `25_26_2`.allstudentswithbirthday TO 'studentrolle';
GRANT SELECT ON `25_26_2`.allstudentswithbirthdaywithcheckoption TO 'studentrolle';

-- DAU: nur sehr eingeschränkte Sicht
GRANT SELECT ON `25_26_2`.allstudentsavgbymatnr TO 'daurolle';

-- --------------------------------------------------------------
-- 4) Rollen an Benutzer vergeben
-- --------------------------------------------------------------
GRANT 'adminrolle' TO 'admin1'@'localhost';
GRANT 'dozentrolle' TO 'dozent1'@'localhost';
GRANT 'studentrolle' TO 'student1'@'localhost';
GRANT 'daurolle' TO 'dau1'@'localhost';

-- --------------------------------------------------------------
-- 5) Default-Rollen setzen
-- --------------------------------------------------------------
SET DEFAULT ROLE 'adminrolle' TO 'admin1'@'localhost';
SET DEFAULT ROLE 'dozentrolle' TO 'dozent1'@'localhost';
SET DEFAULT ROLE 'studentrolle' TO 'student1'@'localhost';
SET DEFAULT ROLE 'daurolle' TO 'dau1'@'localhost';

-- --------------------------------------------------------------
-- 6) Kontrolle
-- --------------------------------------------------------------
SHOW GRANTS FOR 'admin1'@'localhost';
SHOW GRANTS FOR 'dozent1'@'localhost';
SHOW GRANTS FOR 'student1'@'localhost';
SHOW GRANTS FOR 'dau1'@'localhost';

SHOW GRANTS FOR 'adminrolle';
SHOW GRANTS FOR 'dozentrolle';
SHOW GRANTS FOR 'studentrolle';
SHOW GRANTS FOR 'daurolle';

-- --------------------------------------------------------------
-- 7) Ins Übungsschema wechseln
-- --------------------------------------------------------------
USE `25_26_2`;