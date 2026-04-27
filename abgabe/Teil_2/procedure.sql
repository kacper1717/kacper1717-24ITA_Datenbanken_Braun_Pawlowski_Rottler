-- =========================================================
-- 05_procedure.sql
-- Stored Procedure für den sauberen Import von Produkten
-- =========================================================

USE productdb;

DROP PROCEDURE IF EXISTS import_product;

-- sorgt dafür dass komplettes skript auf einmal ausgeführt wird
DELIMITER $$

CREATE PROCEDURE import_product(
    IN p_name VARCHAR(255),
    IN p_description TEXT,
    IN p_brand_name VARCHAR(255),
    IN p_category_name VARCHAR(255),
    IN p_price DECIMAL(10,2),
    IN p_load_class VARCHAR(100),
    IN p_application VARCHAR(255),
    IN p_temperature_range VARCHAR(100)
)
BEGIN
    DECLARE v_brand_id INT DEFAULT NULL;
    DECLARE v_category_id INT DEFAULT NULL;
    DECLARE v_existing_product_id INT DEFAULT NULL;

    -- =========================
    -- 1. Pflichtfelder prüfen
    -- =========================
    IF p_name IS NULL OR TRIM(p_name) = '' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Pflichtfeld fehlt: Produktname';
    END IF;

    IF p_brand_name IS NULL OR TRIM(p_brand_name) = '' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Pflichtfeld fehlt: Marke (Brand)';
    END IF;

    IF p_category_name IS NULL OR TRIM(p_category_name) = '' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Pflichtfeld fehlt: Kategorie (Category)';
    END IF;

    IF p_price IS NULL OR p_price < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ungueltiger Preis: Darf nicht NULL oder negativ sein';
    END IF;

    -- =========================
    -- 2. Marke suchen / anlegen
    -- =========================
    SELECT id INTO v_brand_id 
    FROM brands 
    WHERE name = TRIM(p_brand_name) 
    LIMIT 1;

    IF v_brand_id IS NULL THEN
        INSERT INTO brands (name) VALUES (TRIM(p_brand_name));
        SET v_brand_id = LAST_INSERT_ID();
    END IF;

    -- =============================
    -- 3. Kategorie suchen / anlegen
    -- =============================
    SELECT id INTO v_category_id 
    FROM categories 
    WHERE name = TRIM(p_category_name) 
    LIMIT 1;

    IF v_category_id IS NULL THEN
        INSERT INTO categories (name) VALUES (TRIM(p_category_name));
        SET v_category_id = LAST_INSERT_ID();
    END IF;

    -- =========================
    -- 4. Dubletten prüfen
    -- Ein Produkt gilt als Dublette, wenn der Name und die Marke identisch sind
    -- =========================
    SELECT id INTO v_existing_product_id 
    FROM products 
    WHERE name = TRIM(p_name) 
      AND brand_id = v_brand_id 
    LIMIT 1;

    IF v_existing_product_id IS NOT NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Fehler: Dieses Produkt existiert bereits (Dublette)';
    END IF;

    -- =========================
    -- 5. Produkt einfügen
    -- =========================
    INSERT INTO products(
        name,
        description,
        brand_id,
        category_id,
        price,
        load_class,
        application,
        temperature_range
    )
    VALUES (
        TRIM(p_name),
        p_description,
        v_brand_id,
        v_category_id,
        p_price,
        TRIM(p_load_class),
        TRIM(p_application),
        TRIM(p_temperature_range)
    );

END$$

DELIMITER ;


--
/*
CALL import_product(
       'Test Produkt A', 'Beschreibung', 'Neue Test Marke', 'Neue Test Kategorie', 
       19.99, 'Medium', 'Indoor', '0-50 C'
   );

-- Test mit leerem Namen
   CALL import_product(
       '   ', 'Beschreibung', 'Neue Test Marke', 'Neue Test Kategorie', 
       19.99, 'Medium', 'Indoor', '0-50 C'
   );


*/
--