-- import.sql sorgt für das korrekte laden der CSV-Daten in die erzegten Tabellen aus schema.sql
USE productdb;

DELIMITER //

CREATE PROCEDURE import_all_data()
BEGIN
    -- Wenn irgendein Fehler passiert, mache ALLES rückgängig
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK;
        RESIGNAL; -- Gibt die Fehlermeldung nach außen weiter
    END;

    START TRANSACTION;

    LOAD DATA INFILE '/csv/brands.csv'
    INTO TABLE brands
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;

    LOAD DATA INFILE '/csv/categories.csv'
    INTO TABLE categories
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;
    (id, name);

    LOAD DATA INFILE '/csv/tags.csv'
    INTO TABLE tags
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;
    (id, name);
    
    -- Lade products_extended und products_500_new in gleiche Tabelle, da keine doppelten Einträge etc sind
    LOAD DATA INFILE '/csv/products_extended.csv'
    INTO TABLE products
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;
    (id, name, description, brand_id, category_id, price, load_class, application, temperature_range);

    LOAD DATA INFILE '/csv/products_500_new.csv'
    INTO TABLE products
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;
    (id, name, description, brand_id, category_id, price, load_class, application, temperature_range);

    LOAD DATA INFILE '/csv/product_tags.csv'
    INTO TABLE product_tags
    FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS;
    (product_id, tag_id);

    COMMIT;
END //

DELIMITER ;

-- Prozedur aufrufen, um die Daten zu importieren
CALL import_all_data();

-- Prozedur löschen, da sie nicht mehr benötigt wird
DROP PROCEDURE import_all_data;