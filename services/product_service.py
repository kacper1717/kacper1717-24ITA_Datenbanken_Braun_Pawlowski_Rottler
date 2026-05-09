"""
Product Service - Business Logic for Product Operations

Handles product listing, dashboard data, validation, and SQL queries.
"""
import logging

from flask import current_app

from repositories import MySQLRepository, QdrantRepository, DashboardRepository
from validation import validate_mysql as _validate_mysql
from validation import ValidationItem, ValidationReport

log = logging.getLogger(__name__)


class ProductService:
    """Service for product-related operations"""

    def __init__(self, mysql_repo: MySQLRepository, qdrant_repo: QdrantRepository, dashboard_repo: DashboardRepository):
        """
        Initialize product service.

        Args:
            mysql_repo: MySQL repository for database operations
            qdrant_repo: Qdrant repository for vector index stats
            dashboard_repo: Dashboard repository for aggregated dashboard data
        """
        self.mysql_repo = mysql_repo
        self.qdrant_repo = qdrant_repo
        self.dashboard_repo = dashboard_repo

    def list_products_joined(self, page: int = 1, page_size: int = 20) -> dict:
        """
        Get paginated products with brand, category, and tags.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Dictionary with 'items' (list of products) and 'total' (total count)
        """
        result = self.mysql_repo.get_products_with_joins(page=page, page_size=page_size)
        log.info(f"Listed {len(result['items'])} products (page {page}, size {page_size})")
        return result

    def get_dashboard_data(self) -> dict:
        """
        Get dashboard statistics.

        Combines MySQL counts, Qdrant index stats, and recent ETL runs.

        Returns:
            Dictionary with 'mysql_counts', 'qdrant_counts', 'last_runs'
        """
        mysql_counts = {
            "products": 0, "brands": 0, "categories": 0
        }
        last_runs = []
        try:
            stats = self.mysql_repo.get_dashboard_stats()
            if stats:
                mysql_counts = stats.get("mysql_counts", mysql_counts)
                last_runs = stats.get("last_runs", [])
        except Exception as e:
            log.error(f"Error getting MySQL stats: {e}")

        qdrant_counts = {
            "indexed": 0, "status": "unknown", "last_indexed_at": None, "embedding_model": None
        }
        try:
            from services import ServiceFactory
            index_service = ServiceFactory.get_index_service()
            q_stats = index_service.get_index_status()
            qdrant_counts["indexed"] = q_stats.get("indexed_products", 0)
            qdrant_counts["status"] = q_stats.get("status", "unknown")
            qdrant_counts["last_indexed_at"] = q_stats.get("last_indexed_at")
            qdrant_counts["embedding_model"] = q_stats.get("embedding_model")
        except Exception as e:
            log.error(f"Error getting Qdrant stats: {e}")

        return {
            "mysql_counts": mysql_counts,
            "qdrant_counts": qdrant_counts,
            "last_runs": last_runs
        }

    def get_audit_log(self, page: int = 1, page_size: int = 10) -> dict:
        """
        Get paginated audit log entries.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Dictionary with 'items' (list of audit entries) and 'total' (total count)
        """
        return self.mysql_repo.get_audit_entries(page=page, page_size=page_size)

    def get_last_runs(self, limit: int = 10) -> list[dict]:
        """
        Get last N ETL run log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of run log dictionaries
        """
        return self.mysql_repo.get_last_runs(limit=limit)

    def execute_sql_query(self, query: str) -> list[dict]:
        """
        Execute a raw SQL SELECT query.

        Security: Only SELECT queries are allowed.

        Args:
            query: SQL query string (must be SELECT)

        Returns:
            List of result dictionaries

        Raises:
            ValueError: If query is not SELECT or contains forbidden keywords
            Exception: On SQL execution errors
        """
        return self.mysql_repo.execute_raw_query(query)

    def search_products_by_keyword(self, keyword: str, limit: int = 20) -> list[dict]:
        """
        Keyword search delegated to MySQL repository.

        Args:
            keyword: Search term
            limit: Maximum number of results

        Returns:
            List of product dictionaries
        """
        return self.mysql_repo.search_products_by_keyword(keyword=keyword, limit=limit)

    def validate_mysql(self) -> dict:
        """
        Validate MySQL database schema and data integrity.

        Returns:
            Validation report dictionary
        """
        required_tables = ["products", "brands", "categories", "tags", "product_tags", "etl_run_log"]
        missing_tables = []
        for table in required_tables:
            if not self.mysql_repo.has_column(table, "id"):
                missing_tables.append(table)
        
        return {
            "status": "valid" if not missing_tables else "invalid",
            "missing_tables": missing_tables,
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }

    def get_product_count(self) -> int:
        """
        Get total number of products in MySQL.

        Returns:
            Total product count
        """
        try:
            counts = self.dashboard_repo.get_mysql_counts()
            return counts.get("products", 0)
        except Exception as e:
            log.error(f"Error getting product count: {e}")
            return 0

    def get_brand_count(self) -> int:
        """
        Get total number of brands in MySQL.

        Returns:
            Total brand count
        """
        try:
            counts = self.dashboard_repo.get_mysql_counts()
            return counts.get("brands", 0)
        except Exception as e:
            log.error(f"Error getting brand count: {e}")
            return 0

    def get_category_count(self) -> int:
        """
        Get total number of categories in MySQL.

        Returns:
            Total category count
        """
        try:
            counts = self.dashboard_repo.get_mysql_counts()
            return counts.get("categories", 0)
        except Exception as e:
            log.error(f"Error getting category count: {e}")
            return 0

    def get_summary_stats(self) -> dict:
        """
        Get summary statistics for products, brands, categories, and index.

        Returns:
            Dictionary with summary statistics
        """
        try:
            mysql_counts = self.dashboard_repo.get_mysql_counts()
            last_runs = self.dashboard_repo.get_last_runs(limit=5)
            last_indexed_at = self.dashboard_repo.get_last_indexed_at()
            
            return {
                "products": mysql_counts.get("products", 0),
                "brands": mysql_counts.get("brands", 0),
                "categories": mysql_counts.get("categories", 0),
                "tags": mysql_counts.get("tags", 0),
                "last_runs": last_runs,
                "last_indexed_at": last_indexed_at
            }
        except Exception as e:
            log.error(f"Error getting summary stats: {e}")
            return {
                "products": 0,
                "brands": 0,
                "categories": 0,
                "tags": 0,
                "last_runs": [],
                "last_indexed_at": None
            }


