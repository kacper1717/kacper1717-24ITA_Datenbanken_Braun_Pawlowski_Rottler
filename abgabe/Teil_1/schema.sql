-- ============================================================
-- schema.sql
-- Erstellt die Datenbankstruktur für den Produktkatalog.
-- Aufbauend auf dem ER-Modell mit PK, FK, Constraints
-- und referenzieller Integrität.
-- ============================================================

DROP DATABASE IF EXISTS productdb;
CREATE DATABASE productdb;
USE productdb;

CREATE TABLE brands (
    id   INT          AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE categories (
    id   INT          AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE tags (
    id   INT          AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE products (
    id                INT           AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(255)  NOT NULL,
    description       TEXT,
    brand_id          INT           NOT NULL,
    category_id       INT           NOT NULL,
    price             DECIMAL(10,2) NOT NULL,
    load_class        VARCHAR(100),
    application       VARCHAR(255),
    temperature_range VARCHAR(100),

    CONSTRAINT fk_products_brand
        FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    -- Preis darf nicht negativ sein
    CONSTRAINT chk_price
        CHECK (price >= 0),
        
    -- Produktname darf nicht leer sein
    CONSTRAINT chk_name_not_empty
        CHECK (CHAR_LENGTH(name) > 0)
);

CREATE TABLE product_tags (
    product_id INT NOT NULL,
    tag_id     INT NOT NULL,

    PRIMARY KEY (product_id, tag_id),

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (tag_id)
        REFERENCES tags(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);