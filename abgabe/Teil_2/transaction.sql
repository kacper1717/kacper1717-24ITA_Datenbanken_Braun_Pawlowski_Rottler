-- ============================================================
-- transaction.sql
-- A2 Transaktionen - fachliche Datenbankoperationen
--
-- Enthaltene Fälle:
-- 1) Produkt anlegen inkl. Marke, Kategorie und Tags
-- 2) Rollback-Demo bei fachlichem Fehlerfall (Doppel-Eintrag)
--
-- Voraussetzungen:
-- - Teil-1-Schema und Import sind bereits eingespielt
-- - Datenbank: productdb
-- ============================================================

USE productdb;

-- ------------------------------------------------------------
-- 1) CREATE: Produkt anlegen inkl. Marke, Kategorie und Tags
-- ------------------------------------------------------------
START TRANSACTION;

-- Marke und Kategorie anlegen (oder vorhandene IDs wiederverwenden)
INSERT INTO brands (name)
VALUES ('TX_DEMO_BRAND')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @brand_id := LAST_INSERT_ID();

INSERT INTO categories (name)
VALUES ('TX_DEMO_CATEGORY')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @category_id := LAST_INSERT_ID();

-- Tags anlegen (oder wiederverwenden)
INSERT INTO tags (name)
VALUES ('tx-demo-tag-a')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @tag_a_id := LAST_INSERT_ID();

INSERT INTO tags (name)
VALUES ('tx-demo-tag-b')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @tag_b_id := LAST_INSERT_ID();

-- Produkt anlegen
INSERT INTO products (
    name,
    description,
    brand_id,
    category_id,
    price,
    load_class,
    application,
    temperature_range
) VALUES (
    'TX_DEMO_PRODUCT_A2',
    'Demo fuer A2: Produktanlage in einer Transaktion',
    @brand_id,
    @category_id,
    99.90,
    'L',
    'Montage',
    '-10..80 C'
);
SET @product_id := LAST_INSERT_ID();

-- N:M-Verknuepfungen zu Tags
INSERT INTO product_tags (product_id, tag_id)
VALUES
    (@product_id, @tag_a_id),
    (@product_id, @tag_b_id);

COMMIT;

SELECT
    'CREATE committed' AS tx_status,
    p.id,
    p.name,
    b.name AS brand,
    c.name AS category,
    GROUP_CONCAT(t.name ORDER BY t.name SEPARATOR ', ') AS tags
FROM products p
JOIN brands b ON b.id = p.brand_id
JOIN categories c ON c.id = p.category_id
LEFT JOIN product_tags pt ON pt.product_id = p.id
LEFT JOIN tags t ON t.id = pt.tag_id
WHERE p.id = @product_id
GROUP BY p.id, p.name, b.name, c.name;


-- ------------------------------------------------------------
-- 2) ROLLBACK-DEMO: Fehlerfall "doppelter Eintrag"
--    Business-Regel: Produktname soll eindeutig bleiben.
--    (Technisch ist products.name nicht UNIQUE, daher pruefen wir
--     den fachlichen Fehler selbst und rollen explizit zurueck.)
-- ------------------------------------------------------------

-- Vorbereitung: definierter Ausgangszustand (genau 1 Datensatz)
START TRANSACTION;
DELETE FROM products
WHERE name = 'TX_ROLLBACK_DUPLICATE_PRODUCT';
COMMIT;

START TRANSACTION;
INSERT INTO products (
    name,
    description,
    brand_id,
    category_id,
    price,
    load_class,
    application,
    temperature_range
) VALUES (
    'TX_ROLLBACK_DUPLICATE_PRODUCT',
    'Ausgangsdatensatz fuer Rollback-Demo',
    @brand_id,
    @category_id,
    49.90,
    'M',
    'Demo',
    '-5..60 C'
);
COMMIT;

SET @before_cnt := (
    SELECT COUNT(*)
    FROM products
    WHERE name = 'TX_ROLLBACK_DUPLICATE_PRODUCT'
);

-- Fehlerfall: zweiter Datensatz mit gleichem fachlichen Schluessel
START TRANSACTION;

INSERT INTO products (
    name,
    description,
    brand_id,
    category_id,
    price,
    load_class,
    application,
    temperature_range
) VALUES (
    'TX_ROLLBACK_DUPLICATE_PRODUCT',
    'Soll als fachlicher Fehler erkannt werden',
    @brand_id,
    @category_id,
    59.90,
    'M',
    'Demo',
    '-5..60 C'
);

SET @dup_cnt := (
    SELECT COUNT(*)
    FROM products
    WHERE name = 'TX_ROLLBACK_DUPLICATE_PRODUCT'
);

SET @dup_decision := IF(@dup_cnt > 1, 'ROLLBACK', 'COMMIT');
PREPARE tx_dup_stmt FROM @dup_decision;
EXECUTE tx_dup_stmt;
DEALLOCATE PREPARE tx_dup_stmt;

SET @after_cnt := (
    SELECT COUNT(*)
    FROM products
    WHERE name = 'TX_ROLLBACK_DUPLICATE_PRODUCT'
);

SELECT
    'ROLLBACK demo' AS tx_status,
    @before_cnt AS count_before,
    @dup_cnt AS count_inside_tx,
    @after_cnt AS count_after,
    IF(@after_cnt = @before_cnt, 'ROLLBACK OK', 'CHECK FAILED') AS validation;