-- Wenn ein Kunde gelöscht wird → kundenid in bestellung wird NULL
DROP DATABASE IF EXISTS integritaet2;
create database integritaet2;
use integritaet2;

DROP TABLE IF EXISTS kunde;
DROP TABLE IF EXISTS bestellung;
DROP TABLE IF EXISTS artikel;
DROP TABLE IF EXISTS pruefung;
DROP TABLE IF EXISTS logger;
DROP TABLE IF EXISTS SPEED;

CREATE TABLE kunde (
    kundenid INT PRIMARY KEY,
    name VARCHAR(50), email VARCHAR(100)
);

CREATE TABLE bestellung (
    bestellnr INT PRIMARY KEY,
    datum DATE, kundenid INT,
    FOREIGN KEY (kundenid) REFERENCES kunde(kundenid)
    ON DELETE SET NULL
);

INSERT INTO kunde VALUES (101,'Müller','mueller@mail.de'),
  (102,'Schmidt','schmidt@mail.de'), (103,'Weber','weber@mail.de'),
  (104,'Fischer','fischer@mail.de');
INSERT INTO bestellung VALUES (5001,'2025-01-10',101),
  (5002,'2025-01-12',102), (5003,'2025-01-15',102),
  (5004,'2025-02-01',103), (5005,'2025-02-05',104);

DELETE FROM kunde WHERE kundenid = 104;
-- → kundenid in Bestellung 5005 wird NULL
-- Änderungen/Löschungen werden automatisch weitergegeben

DROP TABLE IF EXISTS bestellung;
DROP TABLE IF EXISTS kunde;

CREATE TABLE kunde (
    kundenid INT PRIMARY KEY,
    name VARCHAR(50), email VARCHAR(100)
);

CREATE TABLE bestellung (
    bestellnr INT PRIMARY KEY,
    datum DATE, kundenid INT,
    FOREIGN KEY (kundenid) REFERENCES kunde(kundenid)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);


INSERT INTO kunde VALUES (101,'Müller','mueller@mail.de'),
  (102,'Schmidt','schmidt@mail.de');
INSERT INTO bestellung VALUES (5001,'2025-01-10',101),
  (5002,'2025-01-12',102), (5003,'2025-01-15',102);

UPDATE kunde SET kundenid = 201 WHERE kundenid = 101;
-- → FK automatisch angepasst (101 → 201)

DELETE FROM kunde WHERE kundenid = 201;
-- → Bestellung 5001 automatisch gelöscht

-- Löschen wird verhindert, wenn abhängige Daten existieren

DROP TABLE IF EXISTS bestellung;
DROP TABLE IF EXISTS kunde;

CREATE TABLE kunde (
    kundenid INT PRIMARY KEY,
    name VARCHAR(50), email VARCHAR(100)
);

CREATE TABLE bestellung (
    bestellnr INT PRIMARY KEY,
    datum DATE, kundenid INT,
    FOREIGN KEY (kundenid) REFERENCES kunde(kundenid)
    ON DELETE RESTRICT
);

INSERT INTO kunde VALUES (101,'Müller','mueller@mail.de');
INSERT INTO bestellung VALUES (5001,'2025-01-10',101);

-- Versuch zu löschen:
DELETE FROM kunde WHERE kundenid = 101;

-- → Fehler! Referenzielle Integrität verletzt
-- → Kunde 101 hat noch Bestellungen

-- Lokale Integritätsbedingung (Wertebereich)

CREATE TABLE artikel (
    artikelnr INT PRIMARY KEY,
    bezeichnung VARCHAR(50),
    preis NUMERIC(8,2) CHECK (preis > 0)
);

-- Gültiger Wert:
INSERT INTO artikel VALUES (1,'Laptop',999.99);

-- Ungültiger Wert:
INSERT INTO artikel VALUES (2,'Geschenk',-5.00);

-- → Fehler (CHECK verletzt: preis muss > 0 sein)


-- Weiteres Beispiel mit BETWEEN:
CREATE TABLE pruefung (
    matrikelnr INT,
    fach VARCHAR(50),
    note NUMERIC(2,1)
      CHECK (note BETWEEN 1.0 AND 5.0)
);

INSERT INTO pruefung VALUES (12345,'DB',1.3);
INSERT INTO pruefung VALUES (12345,'DB',6.0);
-- → Fehler (note nicht zwischen 1.0 und 5.0)

-- Ereignisgesteuerte Integrität (dynamisch)

DROP TABLE IF EXISTS bestellung;
DROP TABLE IF EXISTS kunde;
DROP TABLE IF EXISTS logger;

CREATE TABLE kunde (
    kundenid INT PRIMARY KEY,
    name VARCHAR(50), email VARCHAR(100)
);
CREATE TABLE bestellung (
    bestellnr INT PRIMARY KEY,
    datum DATE, kundenid INT,
    FOREIGN KEY (kundenid) REFERENCES kunde(kundenid)
);
CREATE TABLE logger (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zeitpunkt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    meldung VARCHAR(255)
);

DELIMITER $$
CREATE TRIGGER after_bestellung_insert
AFTER INSERT ON bestellung
FOR EACH ROW
BEGIN
    INSERT INTO logger(meldung)
    VALUES (CONCAT('Neue Bestellung ',
      NEW.bestellnr,' für Kunde ',
      NEW.kundenid,' am ',NEW.datum));
END$$
DELIMITER ;

INSERT INTO kunde VALUES (101,'Müller','m@mail.de');
SELECT * FROM logger;
INSERT INTO bestellung VALUES (5001,'2025-03-15',101);
SELECT * FROM logger;
-- → Eintrag im Logger

-- Nicht Teil Integrität – nur für Tests
drop table if exists SPEED;
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
        INSERT INTO SPEED
          (FIELD1,FIELD2,FIELD3,FIELD4,FIELD5)
        VALUES (MD5(RAND()),MD5(RAND()),
          MD5(RAND()),MD5(RAND()),MD5(RAND()));
        SET i = i + 1;
    END WHILE;
    COMMIT;
END$$
DELIMITER ;

CALL Speed();
-- → Erzeugt 10.000 Testdatensätze


