import os
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import create_engine, text
from neo4j import GraphDatabase

MYSQL_URL = os.environ["MYSQL_URL"]  # im app-container gesetzt
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "admin123")

BATCH_SIZE = int(os.environ.get("NEO4J_BATCH_SIZE", "500"))

engine = create_engine(MYSQL_URL, pool_pre_ping=True)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def fetch_all(sql: str):
    """Liest Query-Ergebnis als Liste echter dicts (Neo4j-Driver-kompatibel)."""
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
        return [dict(r) for r in rows]


def chunked(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _neo4j_safe_value(v):
    """Konvertiert Werte in Neo4j/Packstream-kompatible Typen."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        # Neo4j kann Decimal nicht serialisieren
        return float(v)
    if isinstance(v, (datetime, date)):
        # sicherer als native neo4j temporal, wenn du es einfach halten willst
        return v.isoformat()
    return v


def _neo4j_safe_rows(rows):
    """Konvertiert eine Liste dicts auf Neo4j-sichere Werte."""
    out = []
    for r in rows:
        d = dict(r)

        # wichtige Felder konvertieren
        if "price" in d:
            d["price"] = _neo4j_safe_value(d["price"])

        # IDs optional normieren (robust, falls MySQL mal Decimal/str liefert)
        for k in ("id", "brand_id", "category_id", "product_id", "tag_id"):
            if k in d and d[k] is not None:
                try:
                    d[k] = int(d[k])
                except Exception:
                    # wenn es nicht sauber int ist, lass es so
                    pass

        # restliche Werte allgemein absichern (optional, aber robust)
        for k, v in list(d.items()):
            d[k] = _neo4j_safe_value(v)

        out.append(d)
    return out


def upsert_brands(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MERGE (b:Brand {id: r.id})
    SET b.name = r.name
    """
    tx.run(cypher, rows=rows)


def upsert_categories(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MERGE (c:Category {id: r.id})
    SET c.name = r.name
    """
    tx.run(cypher, rows=rows)


def upsert_tags(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MERGE (t:Tag {id: r.id})
    SET t.name = r.name
    """
    tx.run(cypher, rows=rows)


def upsert_products(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MERGE (p:Product {id: r.id})
    SET
      p.name = r.name,
      p.description = r.description,
      p.price = r.price,
      p.load_class = r.load_class,
      p.application = r.application,
      p.temperature_range = r.temperature_range,
      p.brand_id = r.brand_id,
      p.category_id = r.category_id
    """
    tx.run(cypher, rows=rows)


def link_product_brand(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MATCH (p:Product {id: r.product_id})
    MATCH (b:Brand {id: r.brand_id})
    MERGE (p)-[:HAS_BRAND]->(b)
    """
    tx.run(cypher, rows=rows)


def link_product_category(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MATCH (p:Product {id: r.product_id})
    MATCH (c:Category {id: r.category_id})
    MERGE (p)-[:IN_CATEGORY]->(c)
    """
    tx.run(cypher, rows=rows)


def link_product_tags(tx, rows):
    cypher = """
    UNWIND $rows AS r
    MATCH (p:Product {id: r.product_id})
    MATCH (t:Tag {id: r.tag_id})
    MERGE (p)-[:HAS_TAG]->(t)
    """
    tx.run(cypher, rows=rows)


def main():
    # 1) Dimensionstabellen
    brands = fetch_all("SELECT id, name FROM brands;")
    categories = fetch_all("SELECT id, name FROM categories;")
    tags = fetch_all("SELECT id, name FROM tags;")

    # 2) Produkte
    products = fetch_all("""
         SELECT id, name, description, brand_id, category_id, price,
             load_class, application, temperature_range
        FROM products;
    """)

    # 3) Relationsdaten
    product_brand = fetch_all("SELECT id AS product_id, brand_id FROM products WHERE brand_id IS NOT NULL;")
    product_category = fetch_all("SELECT id AS product_id, category_id FROM products WHERE category_id IS NOT NULL;")
    product_tags = fetch_all("SELECT product_id, tag_id FROM product_tags;")

    # Alles Neo4j-sicher machen (wichtig!)
    brands = _neo4j_safe_rows(brands)
    categories = _neo4j_safe_rows(categories)
    tags = _neo4j_safe_rows(tags)
    products = _neo4j_safe_rows(products)
    product_brand = _neo4j_safe_rows(product_brand)
    product_category = _neo4j_safe_rows(product_category)
    product_tags = _neo4j_safe_rows(product_tags)

    with driver.session() as session:
        # Upserts
        for batch in chunked(brands, BATCH_SIZE):
            session.execute_write(upsert_brands, batch)

        for batch in chunked(categories, BATCH_SIZE):
            session.execute_write(upsert_categories, batch)

        for batch in chunked(tags, BATCH_SIZE):
            session.execute_write(upsert_tags, batch)

        for batch in chunked(products, BATCH_SIZE):
            session.execute_write(upsert_products, batch)

        # Links
        for batch in chunked(product_brand, BATCH_SIZE):
            session.execute_write(link_product_brand, batch)

        for batch in chunked(product_category, BATCH_SIZE):
            session.execute_write(link_product_category, batch)

        for batch in chunked(product_tags, BATCH_SIZE):
            session.execute_write(link_product_tags, batch)

    print("✅ Sync fertig: MySQL → Neo4j")


if __name__ == "__main__":
    try:
        main()
    finally:
        driver.close()
