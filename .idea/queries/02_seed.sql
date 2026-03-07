INSERT INTO brands (name) VALUES ('SKF'), ('FAG'), ('Schaeffler')
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO categories (name) VALUES ('Wälzlager'), ('Dichtungen')
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO tags (name) VALUES ('Industrie'), ('Automotive'), ('Premium')
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO products (sku, title, description, brand_id, category_id)
VALUES
('SKU-1001', 'Rillenkugellager 6204', 'Standardlager für hohe Drehzahlen', 1, 1),
('SKU-1002', 'Wellendichtring 35x52x7', 'NBR-Dichtung für Standardanwendungen', 2, 2);

INSERT INTO product_tags (product_id, tag_id)
VALUES (1,1),(1,3),(2,2);
