-- import.sql sorgt für das korrekte Laden der CSV-Daten in die erzeugten Tabellen aus schema.sql
USE productdb;

-- Transaktion starten
START TRANSACTION;

-- Lade Brands
LOAD DATA INFILE '/csv/brands.csv'
INTO TABLE brands
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name);

-- Lade Categories
LOAD DATA INFILE '/csv/categories.csv'
INTO TABLE categories
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name);

-- Lade Tags
LOAD DATA INFILE '/csv/tags.csv'
INTO TABLE tags
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name);

-- Lade products_extended in die products-Tabelle
LOAD DATA INFILE '/csv/products_extended.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name, description, brand_id, category_id, price, load_class, application, temperature_range);

-- Lade products_500_new in die products-Tabelle (keine doppelten Einträge)
LOAD DATA INFILE '/csv/products_500_new.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(id, name, description, brand_id, category_id, price, load_class, application, temperature_range);

-- Lade Product-Tags Zuordnungen
LOAD DATA INFILE '/csv/product_tags.csv'
INTO TABLE product_tags
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, tag_id);

-- Commit bei Erfolg
COMMIT;

-- Bei Fehler manuell ausführen:
-- ROLLBACK;