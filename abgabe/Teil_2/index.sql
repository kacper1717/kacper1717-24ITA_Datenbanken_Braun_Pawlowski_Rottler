-- =========================================================
-- 06_index.sql
-- Aufgabe A5: Indizes und B-Baum-Bezug
-- =========================================================

USE productdb;

-- ---------------------------------------------------------
-- 1) Gezielte Indizes
-- ---------------------------------------------------------
-- Fuer die Aufgabe legen wir explizit die geforderten Indizes
-- auf Produktname, Marke und Kategorie an.

DROP INDEX IF EXISTS idx_products_name ON products;
DROP INDEX IF EXISTS idx_products_brand_id ON products;
DROP INDEX IF EXISTS idx_products_category_id ON products;

CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_category_id ON products(category_id);

-- Optionaler Zusatzindex fuer Bereichsabfragen und Sortierung nach Preis.
DROP INDEX IF EXISTS idx_products_price ON products;
CREATE INDEX idx_products_price ON products(price);


-- ---------------------------------------------------------
-- 2) Warum verwendet MySQL hier B-Baeume?
-- ---------------------------------------------------------
/*
InnoDB nutzt standardmaessig B+-Tree-Indizes. Das ist hier sinnvoll, weil:

1. Suche mit O(log n):
   Exakte Suchen (z. B. WHERE name = '...') bleiben auch bei vielen
   Datensaetzen schnell.

2. Bereichsabfragen und Sortierung:
   Durch die sortierte Blattstruktur funktionieren BETWEEN, >, < und
   ORDER BY effizient.

3. Stabilitaet durch Balancierung:
   Der Baum bleibt ausgeglichen. Dadurch bleiben Antwortzeiten planbar,
   auch wenn Daten laufend eingefuegt/geaendert werden.

4. Praefix-Suche:
   LIKE 'abc%' kann den B+-Tree nutzen. LIKE '%abc%' kann den Index
   dagegen in der Regel nicht verwenden.
*/


-- ---------------------------------------------------------
-- 3) EXPLAIN-Analyse der Abfragen
-- ---------------------------------------------------------
-- Nach dem Indexbau Statistiken aktualisieren.
ANALYZE TABLE products;

-- 3.1 Produktname: Erwartet key = idx_products_name, type meist ref.
EXPLAIN SELECT id, name, price
FROM products
WHERE name = 'Crank Brothers Candy 1';

-- 3.2 Marke: Erwartet key = idx_products_brand_id auf products.
EXPLAIN SELECT p.id, p.name, b.name AS brand
FROM products p
JOIN brands b ON b.id = p.brand_id
WHERE p.brand_id = 1;

-- 3.3 Kategorie: Erwartet key = idx_products_category_id auf products.
EXPLAIN SELECT p.id, p.name, c.name AS category
FROM products p
JOIN categories c ON c.id = p.category_id
WHERE p.category_id = 2;

-- 3.4 Preisbereich: Erwartet key = idx_products_price, type meist range.
EXPLAIN SELECT id, name, price
FROM products
WHERE price BETWEEN 50.00 AND 150.00
ORDER BY price;

-- 3.5 Gegenbeispiel: Fuehrendes Wildcard verhindert normalerweise Indexnutzung.
EXPLAIN SELECT id, name, price
FROM products
WHERE description LIKE '%racing%';


-- ---------------------------------------------------------
-- 4) Kontrolle der vorhandenen Indizes
-- ---------------------------------------------------------
SHOW INDEX FROM products;