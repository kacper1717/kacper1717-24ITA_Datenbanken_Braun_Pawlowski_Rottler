-- ============================================================
-- transaction.sql
-- A2 Transaktionen - fachliche Datenbankoperationen
--
-- Enthaltene Fälle:
-- 1) ROLLBACK-DEMO: Rollback bei fachlichem Fehler (Doppel-Eintrag)
-- 2) UPDATE: Produkt konsistent aktualisieren (inkl. Tags, Marke, Kategorie)
-- 3) DELETE: Produkt löschen mit referenzieller Integrität
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

-- N:M-Verknüpfungen zu Tags
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
--    (Technisch ist products.name nicht UNIQUE, daher prüfen wir
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

-- Fehlerfall: zweiter Datensatz mit gleichem fachlichen Schlüssel
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


-- ------------------------------------------------------------
-- 3) UPDATE: Produkt konsistent aktualisieren
--    - Produktstammdaten ändern
--    - Marke/Kategorie umhängen
--    - Tag-Verknüpfungen konsistent ersetzen
-- ------------------------------------------------------------

-- Ausgangsdaten für Update/Delete-Demo sicherstellen
START TRANSACTION;

INSERT INTO brands (name)
VALUES ('TX_UPDATE_BRAND_OLD')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_brand_old_id := LAST_INSERT_ID();

INSERT INTO categories (name)
VALUES ('TX_UPDATE_CATEGORY_OLD')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_category_old_id := LAST_INSERT_ID();

INSERT INTO tags (name)
VALUES ('tx-update-tag-old')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_tag_old_id := LAST_INSERT_ID();

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
    'TX_UPDATE_DELETE_PRODUCT',
    'Ausgangsprodukt fuer Update/Delete-Demo',
    @upd_brand_old_id,
    @upd_category_old_id,
    79.90,
    'M',
    'Service',
    '0..70 C'
);
SET @upd_product_id := LAST_INSERT_ID();

INSERT IGNORE INTO product_tags (product_id, tag_id)
VALUES (@upd_product_id, @upd_tag_old_id);

COMMIT;

-- Zielwerte für konsistentes Update vorbereiten
INSERT INTO brands (name)
VALUES ('TX_UPDATE_BRAND_NEW')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_brand_new_id := LAST_INSERT_ID();

INSERT INTO categories (name)
VALUES ('TX_UPDATE_CATEGORY_NEW')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_category_new_id := LAST_INSERT_ID();

INSERT INTO tags (name)
VALUES ('tx-update-tag-new-a')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_tag_new_a_id := LAST_INSERT_ID();

INSERT INTO tags (name)
VALUES ('tx-update-tag-new-b')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @upd_tag_new_b_id := LAST_INSERT_ID();

START TRANSACTION;

UPDATE products
SET
    description = 'Konsistent aktualisiert (inkl. Abhängigkeiten)',
    brand_id = @upd_brand_new_id,
    category_id = @upd_category_new_id,
    price = 89.90,
    load_class = 'H',
    application = 'Produktion',
    temperature_range = '-20..120 C'
WHERE id = @upd_product_id;

-- Abhängige N:M-Daten konsistent anpassen
DELETE FROM product_tags
WHERE product_id = @upd_product_id;

INSERT INTO product_tags (product_id, tag_id)
VALUES
    (@upd_product_id, @upd_tag_new_a_id),
    (@upd_product_id, @upd_tag_new_b_id);

COMMIT;

SELECT
    'UPDATE committed' AS tx_status,
    p.id,
    p.name,
    p.price,
    b.name AS brand,
    c.name AS category,
    GROUP_CONCAT(t.name ORDER BY t.name SEPARATOR ', ') AS tags
FROM products p
JOIN brands b ON b.id = p.brand_id
JOIN categories c ON c.id = p.category_id
LEFT JOIN product_tags pt ON pt.product_id = p.id
LEFT JOIN tags t ON t.id = pt.tag_id
WHERE p.id = @upd_product_id
GROUP BY p.id, p.name, p.price, b.name, c.name;


-- ------------------------------------------------------------
-- 4) DELETE: Produkt löschen mit referenzieller Integritaet
--    - Produkt wird gelöscht
--    - keine verwaisten product_tags-Einträge bleiben bestehen
-- ------------------------------------------------------------

SET @pt_before_delete := (
    SELECT COUNT(*)
    FROM product_tags
    WHERE product_id = @upd_product_id
);

START TRANSACTION;

DELETE FROM products
WHERE id = @upd_product_id;

SET @product_after_delete := (
    SELECT COUNT(*)
    FROM products
    WHERE id = @upd_product_id
);

SET @pt_after_delete := (
    SELECT COUNT(*)
    FROM product_tags
    WHERE product_id = @upd_product_id
);

SET @delete_decision := IF(
    @product_after_delete = 0 AND @pt_after_delete = 0,
    'COMMIT',
    'ROLLBACK'
);

PREPARE tx_delete_stmt FROM @delete_decision;
EXECUTE tx_delete_stmt;
DEALLOCATE PREPARE tx_delete_stmt;

SELECT
    'DELETE tx result' AS tx_status,
    @pt_before_delete AS product_tags_before,
    @product_after_delete AS product_after,
    @pt_after_delete AS product_tags_after,
    IF(
        @product_after_delete = 0 AND @pt_after_delete = 0,
        'COMMIT OK - referenzielle Integrität gewahrt',
        'ROLLBACK - Integrität verletzt'
    ) AS validation;
