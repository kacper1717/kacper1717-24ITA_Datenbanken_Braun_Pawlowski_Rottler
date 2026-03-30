-- ============================================================================
-- ÜBUNG: DATENINTEGRITÄT
-- Themen:
-- 1. Referenzielle Integrität (FOREIGN KEY)
-- 2. ON DELETE / ON UPDATE
-- 3. CHECK-Constraints
-- 4. Trigger
-- ============================================================================



-- ============================================================================
-- 1. REFERENZIELLE INTEGRITÄT – SET NULL
-- ============================================================================
-- Wenn ein Datensatz in der Eltern-Tabelle gelöscht wird,
-- werden die Fremdschlüssel im Kind auf NULL gesetzt.

DROP DATABASE IF EXISTS integritaet;
create database integritaet;
use integritaet;

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS rolle;

CREATE TABLE rolle(
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(10)
);

CREATE TABLE user(
    id VARCHAR(3),
    name VARCHAR(10),
    FOREIGN KEY(id) REFERENCES rolle(id)
    ON DELETE SET NULL
);

INSERT INTO rolle VALUES
('A', 'Admin'),
('L', 'Local'),
('G', 'Global'),
('D','DAU');

INSERT INTO user VALUES
('A', 'Anette'),
('L', 'Ludwig'),
('L', 'Lisa'),
('G','Gerd'),
('D','Dieter');

SELECT * FROM rolle;
SELECT * FROM user;

-- Löschen in Eltern-Tabelle
DELETE FROM rolle WHERE id = 'D';

-- Ergebnis:
-- → id in user wird NULL
SELECT * FROM user;



-- ============================================================================
-- 2. ON DELETE / ON UPDATE CASCADE
-- ============================================================================
-- Änderungen/Löschungen werden automatisch weitergegeben

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS rolle;

CREATE TABLE rolle(
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(10)
);

CREATE TABLE user(
    id VARCHAR(3),
    name VARCHAR(10),
    FOREIGN KEY(id) REFERENCES rolle(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

INSERT INTO rolle VALUES
('A', 'Admin'),
('D','DAU');

INSERT INTO user VALUES
('A', 'Anette'),
('D','Dieter');

-- UPDATE im Parent
UPDATE rolle SET id = 'DD' WHERE id = 'D';

-- Ergebnis:
SELECT * FROM user;
-- → Fremdschlüssel wurde automatisch angepasst

-- DELETE im Parent
DELETE FROM rolle WHERE id = 'DD';

-- Ergebnis:
SELECT * FROM user;
-- → Datensätze wurden gelöscht



-- ============================================================================
-- 3. ON DELETE RESTRICT
-- ============================================================================
-- Löschen wird verhindert, wenn abhängige Daten existieren

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS rolle;

CREATE TABLE rolle(
    id VARCHAR(3) PRIMARY KEY,
    name VARCHAR(10)
);

CREATE TABLE user(
    id VARCHAR(3),
    name VARCHAR(10),
    FOREIGN KEY(id) REFERENCES rolle(id)
    ON DELETE RESTRICT
);

INSERT INTO rolle VALUES ('D','DAU');
INSERT INTO user VALUES ('D','Dieter');

-- Versuch zu löschen:
DELETE FROM rolle WHERE id = 'D';

-- Ergebnis:
-- → Fehler! Referenzielle Integrität verletzt



-- ============================================================================
-- 4. CHECK-CONSTRAINT
-- ============================================================================
-- Lokale Integritätsbedingung (Wertebereich)

DROP TABLE IF EXISTS user;

CREATE TABLE user(
    name VARCHAR(10),
    note NUMERIC(2,1) CHECK (note BETWEEN 1.0 AND 4.0)
);

INSERT INTO user VALUES ('Max', 2.0);

-- Ungültiger Wert:
INSERT INTO user VALUES ('Tom', 5.0);

-- Ergebnis:
-- → Fehler (CHECK verletzt)



-- ============================================================================
-- 5. TRIGGER
-- ============================================================================
-- Ereignisgesteuerte Integrität (dynamisch)

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS logger;

CREATE TABLE user(
    id VARCHAR(3),
    name VARCHAR(10),
    birthday DATE
);

CREATE TABLE logger (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255)
);

-- Trigger: nach INSERT
DELIMITER $$
CREATE TRIGGER after_user_insert
AFTER INSERT ON user
FOR EACH ROW
BEGIN
    IF NEW.birthday IS NULL THEN
        INSERT INTO logger(message)
        VALUES (CONCAT('Bitte Geburtstag für ', NEW.name, ' ergänzen.'));
    END IF;
END$$
DELIMITER ;

-- Test
INSERT INTO user VALUES ('A', 'Anna', NULL);

SELECT * FROM logger;



-- ============================================================================
-- 6. BONUS: MASSENDATEN (NICHT Teil Integrität)
-- ============================================================================
-- Nur für Performance / Tests

DROP TABLE IF EXISTS SPEED;

CREATE TABLE SPEED (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    FIELD1 VARCHAR(32),
    FIELD2 VARCHAR(32),
    FIELD3 VARCHAR(32),
    FIELD4 VARCHAR(32),
    FIELD5 VARCHAR(32)
);

DELIMITER $$
CREATE PROCEDURE Speed()
BEGIN
    DECLARE i INT DEFAULT 0;

    START TRANSACTION;

    WHILE i < 10000 DO
        INSERT INTO SPEED(FIELD1, FIELD2, FIELD3, FIELD4, FIELD5)
        VALUES (MD5(RAND()), MD5(RAND()), MD5(RAND()), MD5(RAND()), MD5(RAND()));
        SET i = i + 1;
    END WHILE;

    COMMIT;
END$$
DELIMITER ;

-- CALL Speed();