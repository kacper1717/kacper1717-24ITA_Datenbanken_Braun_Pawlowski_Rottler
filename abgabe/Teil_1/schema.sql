/*
Teil 1 - Datenmodell:

Anforderungen:
- vollständiges relationales Schema
- Primär- und Fremdschnlüssel
- referenzielle Integrität
- Normalisierung (mind. 4 NF)

Abgabe Teil 1 beinhaltet:
- ER-Modell.pdf
- import.sql
- schema.sql
*/


/*
schema.sql aufbauend auf ER-Modell implementiert die Tabellen mit entsprechenden PK, FK und relationen sowie kardinalitäten.
*/
DROP DATABASE IF EXISTS productdb;
CREATE DATABASE productdb;
USE productdb;

CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    brand_id INT NOT NULL,
    category_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    load_class VARCHAR(100),
    application VARCHAR(255),
    temperature_range VARCHAR(100),

    CONSTRAINT fk_products_brand
        FOREIGN KEY (brand_id)
        REFERENCES brands(id),

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id),

    CONSTRAINT chk_price
        CHECK (price >= 0),
    
    CONSTRAINT chk_name_not_empty
        CHECK (CHAR_LENGTH(name) > 0)
);

CREATE TABLE product_tags (
    product_id INT,
    tag_id INT,

    PRIMARY KEY (product_id, tag_id),

    FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE,

    FOREIGN KEY (tag_id)
        REFERENCES tags(id)
        ON DELETE CASCADE
);