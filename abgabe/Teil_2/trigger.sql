-- =========================================================
-- 04_trigger.sql
-- Trigger zur Protokollierung von Änderungen an Produkten
-- =========================================================

USE productdb;

-- ---------------------------------------------------------
-- Audit-Tabelle
-- Speichert welches Produkt geändert wurde, alte & neue Werte
-- sowie den Zeitstempel und die Art der Aktion.
-- ---------------------------------------------------------
DROP TABLE IF EXISTS products_audit;

CREATE TABLE products_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    old_name VARCHAR(255),
    new_name VARCHAR(255),

    old_description TEXT,
    new_description TEXT,

    old_brand_id INT,
    new_brand_id INT,

    old_category_id INT,
    new_category_id INT,

    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),

    old_load_class VARCHAR(100),
    new_load_class VARCHAR(100),

    old_application VARCHAR(255),
    new_application VARCHAR(255),

    old_temperature_range VARCHAR(100),
    new_temperature_range VARCHAR(100)
);

-- ---------------------------------------------------------
-- Trigger: trg_products_audit_update
-- Protokolliert jede Änderung (UPDATE) an der products-Tabelle
-- ---------------------------------------------------------
DROP TRIGGER IF EXISTS trg_products_audit_update;

DELIMITER $$

CREATE TRIGGER trg_products_audit_update
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    INSERT INTO products_audit (
        product_id,
        action_type,
        changed_at,

        old_name, new_name,
        old_description, new_description,
        old_brand_id, new_brand_id,
        old_category_id, new_category_id,
        old_price, new_price,
        old_load_class, new_load_class,
        old_application, new_application,
        old_temperature_range, new_temperature_range
    )
    VALUES (
        OLD.id,
        'UPDATE',
        CURRENT_TIMESTAMP,

        OLD.name, NEW.name,
        OLD.description, NEW.description,
        OLD.brand_id, NEW.brand_id,
        OLD.category_id, NEW.category_id,
        OLD.price, NEW.price,
        OLD.load_class, NEW.load_class,
        OLD.application, NEW.application,
        OLD.temperature_range, NEW.temperature_range
    );
END$$

DELIMITER ;

-- ------------
/*
UPDATE products 
SET 
    price = price + 5.00, 
    load_class = 'Heavy Duty Test'
WHERE id = 1;
*/
-- ----------------
