from dataclasses import dataclass, field
from typing import Any, Dict, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


@dataclass
class ValidationItem:
    level: str          # "OK" | "WARN" | "ERROR"
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    ok: bool
    summary: Dict[str, int]
    items: List[ValidationItem]


def validate_mysql(engine) -> ValidationReport:
    items: List[ValidationItem] = []
    counts = {"OK": 0, "WARN": 0, "ERROR": 0}

    def add(level: str, code: str, message: str, **details: Any) -> None:
        items.append(ValidationItem(level=level, code=code, message=message, details=details))
        counts[level] += 1

    try:
        with engine.connect() as con:
            # 0) Verbindung / Version
            version = con.execute(text("SELECT VERSION()")).scalar()
            add("OK", "MYSQL_CONNECTED", "MySQL Verbindung OK.", version=version)

            # 1) Tabellen vorhanden?
            expected_tables = ["brands", "categories", "tags", "products", "product_tags"]
            existing = con.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
            """)).scalars().all()
            existing_set = set(existing)

            missing = [t for t in expected_tables if t not in existing_set]
            if not missing:
                add("OK", "MYSQL_TABLES_PRESENT", "Alle erwarteten Tabellen sind vorhanden.", tables=expected_tables)
            else:
                add("ERROR", "MYSQL_TABLES_MISSING", "Es fehlen erwartete Tabellen.", missing=missing, existing=sorted(existing_set))

            # 2) Row counts
            table_counts = {}
            for t in expected_tables:
                table_counts[t] = con.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() if t in existing_set else None
            add("OK", "MYSQL_COUNTS", "Tabellenanzahlen ermittelt.", counts=table_counts)

            # 3) Pflichtfelder / leere Namen
            for table in ["brands", "categories", "tags"]:
                if table in existing_set:
                    n = con.execute(text(f"""
                        SELECT COUNT(*)
                        FROM {table}
                        WHERE name IS NULL OR TRIM(name) = ''
                    """)).scalar()
                    if n == 0:
                        add("OK", f"MYSQL_{table.upper()}_NAME_NOT_EMPTY", f"{table}.name ist überall befüllt.")
                    else:
                        add("ERROR", f"MYSQL_{table.upper()}_NAME_EMPTY", f"{table} enthält leere name-Werte.", count=n)

            # 4) Pflichtfeld products.name
            if "products" in existing_set:
                n = con.execute(text("""
                    SELECT COUNT(*)
                    FROM products
                    WHERE name IS NULL OR TRIM(name) = ''
                """)).scalar()
                if n == 0:
                    add("OK", "MYSQL_PRODUCTS_NAME_NOT_EMPTY", "products.name ist überall befüllt.")
                else:
                    add("ERROR", "MYSQL_PRODUCTS_NAME_EMPTY", "products enthält Produkte ohne name.", count=n)

         ##   # 5) SKU: leere Strings (nicht NULL, aber leer) -> WARN
          ##  if "products" in existing_set:
         ###       n = con.execute(text("""
        #           SELECT COUNT(*)
        #            FROM products
       #             WHERE sku IS NOT NULL AND TRIM(sku) = ''
        #        """)).scalar()
        #        if n == 0:
        #            add("OK", "MYSQL_PRODUCTS_SKU_NO_EMPTY_STRINGS", "Keine leeren SKU-Strings gefunden.")
        #        else:
        #            add("WARN", "MYSQL_PRODUCTS_SKU_EMPTY_STRINGS", "Es gibt Produkte mit sku='' (leer).", count=n)

            # 6) SKU-Duplikate (sollte wegen UNIQUE nicht passieren)
       #     if "products" in existing_set:
         #       dups = con.execute(text("""
         #           SELECT sku, COUNT(*) AS c
         #           FROM products
         #           WHERE sku IS NOT NULL AND TRIM(sku) <> ''
        #           GROUP BY sku
         #           HAVING c > 1
         #           LIMIT 10
         #       """)).mappings().all()

         #       if len(dups) == 0:
         #           add("OK", "MYSQL_PRODUCTS_SKU_UNIQUE", "Keine doppelten SKU gefunden.")
         #       else:
         #           add("ERROR", "MYSQL_PRODUCTS_SKU_DUPLICATES", "Doppelte SKU gefunden (Top 10).",
         #               examples=[dict(r) for r in dups])

            # 7) FK-Checks (shouldn't happen, but good validation)
            if "products" in existing_set and "brands" in existing_set:
                orphan_brand = con.execute(text("""
                    SELECT COUNT(*)
                    FROM products p
                    LEFT JOIN brands b ON b.id = p.brand_id
                    WHERE p.brand_id IS NOT NULL AND b.id IS NULL
                """)).scalar()
                add("OK", "MYSQL_PRODUCTS_BRAND_FK_OK", "Alle products.brand_id sind gültig.") if orphan_brand == 0 \
                    else add("ERROR", "MYSQL_PRODUCTS_BRAND_FK_BROKEN", "Ungültige brand_id in products gefunden.", count=orphan_brand)

            if "products" in existing_set and "categories" in existing_set:
                orphan_cat = con.execute(text("""
                    SELECT COUNT(*)
                    FROM products p
                    LEFT JOIN categories c ON c.id = p.category_id
                    WHERE p.category_id IS NOT NULL AND c.id IS NULL
                """)).scalar()
                add("OK", "MYSQL_PRODUCTS_CATEGORY_FK_OK", "Alle products.category_id sind gültig.") if orphan_cat == 0 \
                    else add("ERROR", "MYSQL_PRODUCTS_CATEGORY_FK_BROKEN", "Ungültige category_id in products gefunden.", count=orphan_cat)

            if "product_tags" in existing_set and "products" in existing_set and "tags" in existing_set:
                orphan_pt_prod = con.execute(text("""
                    SELECT COUNT(*)
                    FROM product_tags pt
                    LEFT JOIN products p ON p.id = pt.product_id
                    WHERE p.id IS NULL
                """)).scalar()
                orphan_pt_tag = con.execute(text("""
                    SELECT COUNT(*)
                    FROM product_tags pt
                    LEFT JOIN tags t ON t.id = pt.tag_id
                    WHERE t.id IS NULL
                """)).scalar()

                if orphan_pt_prod == 0 and orphan_pt_tag == 0:
                    add("OK", "MYSQL_PRODUCT_TAGS_FK_OK", "Alle product_tags Referenzen sind gültig.")
                else:
                    add("ERROR", "MYSQL_PRODUCT_TAGS_FK_BROKEN", "product_tags enthält ungültige Referenzen.",
                        orphan_product_id=orphan_pt_prod, orphan_tag_id=orphan_pt_tag)

                # Duplikate wären durch PK verhindert; check trotzdem.
                dup_pt = con.execute(text("""
                    SELECT product_id, tag_id, COUNT(*) AS c
                    FROM product_tags
                    GROUP BY product_id, tag_id
                    HAVING c > 1
                    LIMIT 10
                """)).mappings().all()

                if len(dup_pt) == 0:
                    add("OK", "MYSQL_PRODUCT_TAGS_PK_OK", "Keine doppelten (product_id, tag_id) Kombinationen.")
                else:
                    add("ERROR", "MYSQL_PRODUCT_TAGS_DUPLICATES", "Doppelte (product_id, tag_id) Kombinationen gefunden (Top 10).",
                        examples=[dict(r) for r in dup_pt])

            # 8) Warnungen für leere Tabellen
            if table_counts.get("products") == 0:
                add("WARN", "MYSQL_PRODUCTS_EMPTY", "products ist leer – Import/Seed fehlt?")
            if table_counts.get("brands") == 0:
                add("WARN", "MYSQL_BRANDS_EMPTY", "brands ist leer – ggf. ok, aber oft unerwartet.")
            if table_counts.get("categories") == 0:
                add("WARN", "MYSQL_CATEGORIES_EMPTY", "categories ist leer – ggf. ok, aber oft unerwartet.")
            if table_counts.get("tags") == 0:
                add("WARN", "MYSQL_TAGS_EMPTY", "tags ist leer – ggf. ok, aber oft unerwartet.")

    except SQLAlchemyError as e:
        add("ERROR", "MYSQL_VALIDATION_FAILED", "Validierung fehlgeschlagen (DB-Fehler).", error=str(e))
    except Exception as e:
        add("ERROR", "MYSQL_VALIDATION_FAILED_UNKNOWN", "Validierung fehlgeschlagen (unerwarteter Fehler).", error=str(e))

    ok = counts["ERROR"] == 0
    return ValidationReport(ok=ok, summary=counts, items=items)
