"""
MySQL Repository - Data Access Layer for MySQL Database
Handles all MySQL-specific database operations.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging
import re

from sqlalchemy import text
import db

log = logging.getLogger(__name__)


class MySQLRepository(ABC):
    """Abstract base class for MySQL data access operations"""

    @abstractmethod
    def get_products_with_joins(self, page: int, page_size: int) -> dict:
        """Get paginated products with brand, category, and tags"""
        pass

    @abstractmethod
    def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics (counts, last runs, etc.)"""
        pass

    @abstractmethod
    def get_audit_entries(self, page: int, page_size: int) -> dict:
        """Get paginated audit log entries"""
        pass

    @abstractmethod
    def execute_raw_query(self, query: str) -> list[dict]:
        """Execute a raw SELECT query (read-only)"""
        pass

    @abstractmethod
    def get_last_runs(self, limit: int = 10) -> list[dict]:
        """Get last N ETL run log entries"""
        pass

    @abstractmethod
    def has_column(self, table: str, column: str) -> bool:
        """Check if a table has a specific column"""
        pass


class MySQLRepositoryImpl(MySQLRepository):
    """Concrete implementation of MySQL repository"""

    def __init__(self, session_factory=None):
        """
        Initialize MySQL repository.

        Args:
            session_factory: Optional SQLAlchemy session factory.
                           If None, uses db.mysql_session_factory
        """
        self.session_factory = session_factory or db.mysql_session_factory
        if self.session_factory is None:
            raise RuntimeError("MySQL SessionFactory nicht initialisiert.")

    def _get_session(self):
        """Get MySQL session from factory"""
        return self.session_factory()

    @staticmethod
    def _table_exists(session, table_name: str) -> bool:
        """Return True if table exists in the current schema."""
        return (
            session.execute(
                text(
                    """
                SELECT 1
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table_name
                LIMIT 1
                """
                ),
                {"table_name": table_name},
            ).scalar()
            is not None
        )

    def get_products_with_joins(self, page: int, page_size: int) -> dict:
        """
        Get paginated products with brand, category, and tags joined.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            dict with 'items' (list of products) and 'total' (total count)
        """
        page_int = int(page)
        page_size_int = int(page_size)
        offset = max(page_int - 1, 0) * page_size_int

        try:
            with self._get_session() as s:
                if not self._table_exists(s, "products"):
                    log.warning("products table fehlt - liefere leere Produktliste")
                    return {"items": [], "total": 0}

                total = s.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0

                # Skeleton-Query: lauffaehig ohne JOINs.
                # TODO:
                # 1) brand/category
                # 2) tags_csv
                # 3) falls GROUP_CONCAT genutzt wird: passendes GROUP BY ergaenzen
                sql = text(
                    """
                    SELECT p.id AS product_id,
                           p.name AS name,
                           p.price AS price,
                           b.name AS brand,
                           c.name AS category,
                           GROUP_CONCAT(t.name) AS tags_csv
                    FROM products p
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN product_tags pt ON p.id = pt.product_id
                    LEFT JOIN tags t ON pt.tag_id = t.id
                    GROUP BY p.id, p.name, p.price, b.name, c.name
                    ORDER BY p.id
                    LIMIT :limit OFFSET :offset
                    """
                )

                rows = (
                    s.execute(sql, {"limit": page_size_int, "offset": offset})
                    .mappings()
                    .all()
                )

                items: list[dict] = []
                for r in rows:
                    it = dict(r)
                    it["currency"] = "EUR"
                    tags_csv = it.pop("tags_csv", "") or ""
                    it["tags"] = [x for x in tags_csv.split(",") if x]
                    it["tags_str"] = ", ".join(it["tags"])
                    items.append(it)

            return {"items": items, "total": int(total)}
        except Exception:
            log.exception("Produktliste konnte nicht geladen werden - liefere leere Liste")
            return {"items": [], "total": 0}

    def get_dashboard_stats(self) -> dict:
        """
        Get dashboard statistics including MySQL counts, Qdrant status, and last runs.

        Note: This method only returns MySQL-related stats. Qdrant stats should be
        retrieved from QdrantRepository.

        Returns:
            dict with 'mysql_counts' and 'last_runs'
        """
        try:
            with self._get_session() as s:
                products_count = s.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
                brands_count = s.execute(text("SELECT COUNT(*) FROM brands")).scalar() or 0
                categories_count = s.execute(text("SELECT COUNT(*) FROM categories")).scalar() or 0
                
            last_runs = self.get_last_runs(limit=5)
            
            return {
                "mysql_counts": {
                    "products": products_count,
                    "brands": brands_count,
                    "categories": categories_count
                },
                "last_runs": last_runs
            }
        except Exception as e:
            log.error(f"Error getting dashboard stats: {e}")
            return {
                "mysql_counts": {"products": 0, "brands": 0, "categories": 0},
                "last_runs": []
            }

    def get_audit_entries(self, page: int, page_size: int) -> dict:
        """
        Get paginated audit log entries from etl_run_log.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            dict with 'items' (list of audit entries) and 'total' (total count)
        """
        page_int = int(page)
        page_size_int = int(page_size)
        offset = max(page_int - 1, 0) * page_size_int
        
        try:
            with self._get_session() as s:
                if not self._table_exists(s, "products_audit"):
                    return {"items": [], "total": 0}
                    
                total = s.execute(text("SELECT COUNT(*) FROM products_audit")).scalar() or 0
                rows = s.execute(text("SELECT * FROM products_audit ORDER BY changed_at DESC LIMIT :limit OFFSET :offset"), 
                                {"limit": page_size_int, "offset": offset}).mappings().all()
                return {"items": [dict(r) for r in rows], "total": int(total)}
        except Exception as e:
            log.error(f"Error getting audit entries: {e}")
            return {"items": [], "total": 0}

    def get_last_runs(self, limit: int = 10) -> list[dict]:
        """
        Get last N ETL run log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of run log dictionaries
        """
        try:
            with self._get_session() as s:
                if not self._table_exists(s, "etl_run_log"):
                    return []
                rows = s.execute(text("SELECT * FROM etl_run_log ORDER BY run_timestamp DESC LIMIT :limit"), {"limit": limit}).mappings().all()
                return [dict(r) for r in rows]
        except Exception as e:
            log.error(f"Error getting last runs: {e}")
            return []

    def execute_raw_query(self, query: str) -> list[dict]:
        """
        Execute a raw SQL SELECT query on MySQL database.

        Security: Only SELECT queries are allowed. Forbidden keywords are blocked.

        Args:
            query: SQL query string (must be SELECT)

        Returns:
            List of result dictionaries

        Raises:
            ValueError: If query is not SELECT or contains forbidden keywords
            Exception: On SQL execution errors
        """
        query_upper = self._strip_string_literals(query).upper()
        if not query_upper.strip().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
            
        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "GRANT", "REVOKE"]
        for word in forbidden:
            if re.search(r'' + word + r'', query_upper):
                raise ValueError(f"Forbidden keyword '{word}' detected.")
                
        try:
            with self._get_session() as s:
                rows = s.execute(text(query)).mappings().all()
                return [dict(r) for r in rows]
        except Exception as e:
            log.error(f"Raw query failed: {e}")
            raise e

    @staticmethod
    def _strip_string_literals(query: str) -> str:
        # Remove anything in single quotes or double quotes
        q = re.sub(r"'[^']*'", "''", query)
        q = re.sub(r'"[^"]*"', '""', q)
        return q

    @staticmethod
    def _extract_table_names(query: str) -> list[str]:
        q = MySQLRepositoryImpl._strip_string_literals(query).upper()
        # Find all words after FROM or JOIN
        tables = []
        parts = q.split()
        for i, p in enumerate(parts):
            if p in ("FROM", "JOIN") and i + 1 < len(parts):
                # Next word might be table name
                t = re.sub(r'[^A-Z0-9_]', '', parts[i+1])
                if t: tables.append(t)
        return tables

    def has_column(self, table: str, column: str) -> bool:
        """
        Check if a table has a specific column in current database.

        Args:
            table: Table name
            column: Column name

        Returns:
            True if column exists, False otherwise
        """
        try:
            with self._get_session() as s:
                result = s.execute(text("""
                    SELECT 1 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                      AND TABLE_NAME = :table 
                      AND COLUMN_NAME = :column
                """), {"table": table, "column": column}).scalar()
                return result is not None
        except Exception as e:
            log.error(f"Error checking column: {e}")
            return False

    def load_products_for_index(
        self, limit: Optional[int] = None, include_tags: bool = True
    ) -> list[dict]:
        """
        Load products from MySQL for indexing purposes.

        Args:
            limit: Optional limit on number of products
            include_tags: Whether to load tags for each product

        Returns:
            List of product dictionaries with all fields
        """
        try:
            with self._get_session() as s:
                query = """
                    SELECT p.*, b.name as brand, c.name as category
                    FROM products p
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                """
                if limit:
                    query += " LIMIT :limit"
                
                rows = s.execute(text(query), {"limit": limit} if limit else {}).mappings().all()
                products = [dict(r) for r in rows]
                
                if include_tags:
                    for p in products:
                        tags = s.execute(text("""
                            SELECT t.name 
                            FROM tags t
                            JOIN product_tags pt ON t.id = pt.tag_id
                            WHERE pt.product_id = :pid
                        """), {"pid": p["id"]}).scalars().all()
                        p["tags"] = list(tags)
                return products
        except Exception as e:
            log.error(f"Error loading products for index: {e}")
            return []

    def log_etl_run(
        self, strategy: str, products_processed: int, products_written: int
    ) -> None:
        """
        Log an ETL run to etl_run_log table.

        Args:
            strategy: ETL strategy used (e.g., 'A', 'B', 'C')
            products_processed: Number of products processed
            products_written: Number of products written to index
        """
        try:
            with self._get_session() as s:
                if not self._table_exists(s, "etl_run_log"):
                    s.execute(text("""
                        CREATE TABLE etl_run_log (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            strategy VARCHAR(50),
                            products_processed INT,
                            products_written INT,
                            run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                s.execute(text("""
                    INSERT INTO etl_run_log (strategy, products_processed, products_written)
                    VALUES (:strategy, :processed, :written)
                """), {"strategy": strategy, "processed": products_processed, "written": products_written})
                s.commit()
        except Exception as e:
            log.error(f"Error logging ETL run: {e}")
