"""
Neo4j Repository - Data Access Layer for Neo4j Graph Database
Handles all Neo4j-specific graph operations.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging

from neo4j import GraphDatabase

log = logging.getLogger(__name__)


class Neo4jRepository(ABC):
    """Abstract base class for Neo4j graph database operations"""

    @abstractmethod
    def get_product_relationships(self, mysql_ids: list[int]) -> dict[int, dict]:
        """Get product relationships and enrichment data from Neo4j"""
        pass

    @abstractmethod
    def execute_cypher(self, query: str, parameters: Optional[dict] = None) -> list:
        """Execute a raw Cypher query"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the Neo4j driver connection"""
        pass


class NoOpNeo4jRepository(Neo4jRepository):
    """No-op repository used when Neo4j is not configured."""

    def get_product_relationships(self, mysql_ids: list[int]) -> dict[int, dict]:
        return {}

    def execute_cypher(self, query: str, parameters: Optional[dict] = None) -> list:
        return []

    def close(self) -> None:
        return None

    def get_product_by_mysql_id(self, mysql_id: int) -> Optional[dict]:
        return None

    def get_products_by_category(self, category_name: str, limit: int = 10) -> list[dict]:
        return []

    def get_products_by_brand(self, brand_name: str, limit: int = 10) -> list[dict]:
        return []

    def get_related_products(self, mysql_id: int, limit: int = 5) -> list[dict]:
        return []

    def count_products(self) -> int:
        return 0

    def count_products_by_category(self) -> dict[str, int]:
        return {}

    def count_products_by_brand(self) -> dict[str, int]:
        return {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None


class Neo4jRepositoryImpl(Neo4jRepository):
    """Concrete implementation of Neo4j repository"""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j repository.

        Args:
            uri: Neo4j URI (e.g., 'bolt://localhost:7687')
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password))


    def get_product_relationships(self, mysql_ids: list[int]) -> dict[int, dict]:
        """
        Get product relationships and enrichment data from Neo4j.

        Loads additional product data from the graph database based on MySQL IDs.
        Adapts to the graph schema: uses relationships if available, falls back to properties.

        Args:
            mysql_ids: List of MySQL product IDs

        Returns:
            Dictionary mapping mysql_id to enrichment data (title, brand, category, tags)

        Example:
            {
                123: {
                    "title": "Product Name",
                    "brand": "Brand Name",
                    "category": "Category Name",
                    "tags": ["tag1", "tag2"]
                },
                ...
            }
        """
        if not mysql_ids:
            return {}

        query = """
        MATCH (p:Product)
        WHERE coalesce(p.mysql_id, p.id) IN $mysql_ids
        OPTIONAL MATCH (p)-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]->(brand)
        OPTIONAL MATCH (p)-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]->(category)
        OPTIONAL MATCH (p)-[:HAS_TAG|TAGGED_WITH|IN_TAG|TAG]->(tag)
        WITH p, brand, category, collect(DISTINCT tag.name) AS tag_names
        RETURN
            coalesce(p.mysql_id, p.id) AS mysql_id,
            coalesce(p.title, p.name, p.product_name, '') AS title,
            coalesce(brand.name, p.brand, p.brand_name, '') AS brand,
            coalesce(category.name, p.category, p.category_name, '') AS category,
            [tag_name IN tag_names WHERE tag_name IS NOT NULL AND trim(tag_name) <> '' | tag_name] AS tags
        ORDER BY mysql_id
        """

        rows = self.execute_cypher(query, {"mysql_ids": mysql_ids})
        enrichment: dict[int, dict] = {}
        for row in rows:
            mysql_id = row.get("mysql_id")
            if mysql_id is None:
                continue
            tags = row.get("tags") or []
            enrichment[int(mysql_id)] = {
                "title": row.get("title") or "",
                "brand": row.get("brand") or "",
                "category": row.get("category") or "",
                "tags": [tag for tag in tags if tag],
            }
        return enrichment

    def execute_cypher(self, query: str, parameters: Optional[dict] = None) -> list:
        """
        Execute a raw Cypher query.

        Args:
            query: Cypher query string
            parameters: Optional query parameters

        Returns:
            List of result records

        Raises:
            Exception: On query execution errors
        """
        params = parameters or {}
        with self.driver.session() as session:
            result = session.run(query, params)
            return [record.data() for record in result]

    def close(self) -> None:
        """Close the Neo4j driver connection"""
        if getattr(self, "driver", None) is not None:
            self.driver.close()

    # ======================
    # High-level operations
    # ======================

    def get_product_by_mysql_id(self, mysql_id: int) -> Optional[dict]:
        """
        Get a single product from Neo4j by MySQL ID.

        Args:
            mysql_id: MySQL product ID

        Returns:
            Product dictionary or None if not found
        """
        rows = self.get_product_relationships([mysql_id])
        return rows.get(mysql_id)

    def get_products_by_category(self, category_name: str, limit: int = 10) -> list[dict]:
        """
        Get products in a specific category.

        Args:
            category_name: Category name
            limit: Maximum number of results

        Returns:
            List of product dictionaries
        """
        query = """
        MATCH (p:Product)-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]->(category)
        WHERE toLower(coalesce(category.name, category.title, '')) = toLower($category_name)
        OPTIONAL MATCH (p)-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]->(brand)
        OPTIONAL MATCH (p)-[:HAS_TAG|TAGGED_WITH|IN_TAG|TAG]->(tag)
        WITH p, brand, category, collect(DISTINCT tag.name) AS tag_names
        RETURN
            coalesce(p.mysql_id, p.id) AS mysql_id,
            coalesce(p.title, p.name, p.product_name, '') AS title,
            coalesce(brand.name, p.brand, p.brand_name, '') AS brand,
            coalesce(category.name, category.title, p.category, p.category_name, '') AS category,
            [tag_name IN tag_names WHERE tag_name IS NOT NULL AND trim(tag_name) <> '' | tag_name] AS tags
        ORDER BY title
        LIMIT $limit
        """
        rows = self.execute_cypher(query, {"category_name": category_name, "limit": limit})
        return [
            {
                "id": row.get("mysql_id"),
                "title": row.get("title") or "",
                "brand": row.get("brand") or "",
                "category": row.get("category") or "",
                "tags": row.get("tags") or [],
            }
            for row in rows
        ]

    def get_products_by_brand(self, brand_name: str, limit: int = 10) -> list[dict]:
        """
        Get products from a specific brand.

        Args:
            brand_name: Brand name
            limit: Maximum number of results

        Returns:
            List of product dictionaries
        """
        query = """
        MATCH (p:Product)-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]->(brand)
        WHERE toLower(coalesce(brand.name, brand.title, '')) = toLower($brand_name)
        OPTIONAL MATCH (p)-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]->(category)
        OPTIONAL MATCH (p)-[:HAS_TAG|TAGGED_WITH|IN_TAG|TAG]->(tag)
        WITH p, brand, category, collect(DISTINCT tag.name) AS tag_names
        RETURN
            coalesce(p.mysql_id, p.id) AS mysql_id,
            coalesce(p.title, p.name, p.product_name, '') AS title,
            coalesce(brand.name, brand.title, p.brand, p.brand_name, '') AS brand,
            coalesce(category.name, category.title, p.category, p.category_name, '') AS category,
            [tag_name IN tag_names WHERE tag_name IS NOT NULL AND trim(tag_name) <> '' | tag_name] AS tags
        ORDER BY title
        LIMIT $limit
        """
        rows = self.execute_cypher(query, {"brand_name": brand_name, "limit": limit})
        return [
            {
                "id": row.get("mysql_id"),
                "title": row.get("title") or "",
                "brand": row.get("brand") or "",
                "category": row.get("category") or "",
                "tags": row.get("tags") or [],
            }
            for row in rows
        ]

    def get_related_products(self, mysql_id: int, limit: int = 5) -> list[dict]:
        """
        Get products related to a given product (same category or brand).

        Args:
            mysql_id: MySQL product ID
            limit: Maximum number of results

        Returns:
            List of related product dictionaries
        """
        query = """
        MATCH (source:Product)
        WHERE coalesce(source.mysql_id, source.id) = $mysql_id
        OPTIONAL MATCH (source)-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]->(brand)<-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]-(related:Product)
        OPTIONAL MATCH (source)-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]->(category)<-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]-(related)
        OPTIONAL MATCH (related)-[:HAS_TAG|TAGGED_WITH|IN_TAG|TAG]->(tag)
        WITH DISTINCT related, brand, category, collect(DISTINCT tag.name) AS tag_names
        WHERE related IS NOT NULL AND coalesce(related.mysql_id, related.id) <> $mysql_id
        RETURN
            coalesce(related.mysql_id, related.id) AS mysql_id,
            coalesce(related.title, related.name, related.product_name, '') AS title,
            coalesce(brand.name, related.brand, related.brand_name, '') AS brand,
            coalesce(category.name, category.title, related.category, related.category_name, '') AS category,
            [tag_name IN tag_names WHERE tag_name IS NOT NULL AND trim(tag_name) <> '' | tag_name] AS tags
        ORDER BY title
        LIMIT $limit
        """
        rows = self.execute_cypher(query, {"mysql_id": mysql_id, "limit": limit})
        return [
            {
                "id": row.get("mysql_id"),
                "title": row.get("title") or "",
                "brand": row.get("brand") or "",
                "category": row.get("category") or "",
                "tags": row.get("tags") or [],
            }
            for row in rows
        ]

    def count_products(self) -> int:
        """
        Count total number of products in Neo4j.

        Returns:
            Total product count
        """
        rows = self.execute_cypher(
            """
            MATCH (p:Product)
            RETURN count(DISTINCT coalesce(p.mysql_id, p.id)) AS count
            """
        )
        return int(rows[0].get("count", 0)) if rows else 0

    def count_products_by_category(self) -> dict[str, int]:
        """
        Count products grouped by category.

        Returns:
            Dictionary mapping category names to counts
        """
        rows = self.execute_cypher(
            """
            MATCH (p:Product)-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]->(category)
            RETURN coalesce(category.name, category.title, 'Unbekannt') AS name,
                   count(DISTINCT coalesce(p.mysql_id, p.id)) AS count
            ORDER BY name
            """
        )
        return {row.get("name", "Unbekannt"): int(row.get("count", 0)) for row in rows}

    def count_products_by_brand(self) -> dict[str, int]:
        """
        Count products grouped by brand.

        Returns:
            Dictionary mapping brand names to counts
        """
        rows = self.execute_cypher(
            """
            MATCH (p:Product)-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]->(brand)
            RETURN coalesce(brand.name, brand.title, 'Unbekannt') AS name,
                   count(DISTINCT coalesce(p.mysql_id, p.id)) AS count
            ORDER BY name
            """
        )
        return {row.get("name", "Unbekannt"): int(row.get("count", 0)) for row in rows}

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes connection"""
        self.close()
