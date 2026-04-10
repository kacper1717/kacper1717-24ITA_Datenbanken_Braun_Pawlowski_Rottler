-- ============================================================
-- import.sql
-- Lädt die CSV-Daten in die durch schema.sql erstellten Tabellen.
-- Der gesamte Import läuft in einer Transaktion, sodass bei
-- einem Fehler keine inkonsistenten Daten entstehen.
-- ============================================================

USE productdb;

-- Transaktion starten: alle folgenden LOAD DATA Operationen werden
-- erst mit COMMIT dauerhaft geschrieben. Tritt ein Fehler auf, bevor
-- COMMIT erreicht wird, verwirft MySQL alle Änderungen automatisch,
-- sofern die Verbindung danach geschlossen wird (z.B. über Terminal).
START TRANSACTION;

LOAD DATA INFILE '/csv/brands.csv'
INTO TABLE brands
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name);

LOAD DATA INFILE '/csv/categories.csv'
INTO TABLE categories
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name);

LOAD DATA INFILE '/csv/tags.csv'
INTO TABLE tags
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name);

LOAD DATA INFILE '/csv/products_extended.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name, description, brand_id, category_id, price, load_class, application, temperature_range);

LOAD DATA INFILE '/csv/products_500_new.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name, description, brand_id, category_id, price, load_class, application, temperature_range);

LOAD DATA INFILE '/csv/product_tags.csv'
INTO TABLE product_tags
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, tag_id);

-- Alle Importe erfolgreich -> Transaktion abschließen
COMMIT;