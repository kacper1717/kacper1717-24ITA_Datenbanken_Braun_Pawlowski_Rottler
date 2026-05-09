"""
Index Service - Business Logic for Index Management

Handles building, truncating, and monitoring the Qdrant vector index.
"""
import logging
import time
from typing import Optional
from datetime import datetime

from flask import current_app
from sentence_transformers import SentenceTransformer

from repositories import QdrantRepository, MySQLRepository

log = logging.getLogger(__name__)


class IndexService:
    """Service for managing the product vector index"""

    def __init__(
        self,
        qdrant_repo: QdrantRepository,
        mysql_repo: MySQLRepository,
        embedding_model: Optional[SentenceTransformer] = None,
    ):
        """
        Initialize index service.

        Args:
            qdrant_repo: Qdrant repository for vector operations
            mysql_repo: MySQL repository for loading products
            embedding_model: Optional pre-initialized embedding model
        """
        self.qdrant_repo = qdrant_repo
        self.mysql_repo = mysql_repo
        self._embedding_model = embedding_model

    def _get_embedding_model(self) -> SentenceTransformer:
        """Lazy-load embedding model"""
        if self._embedding_model is None:
            model_name = current_app.config.get(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            )
            self._embedding_model = SentenceTransformer(model_name)
            log.info(f"✓ Embedding model loaded: {model_name}")
        return self._embedding_model

    def embed_texts(self, texts: list[str]) -> list:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (numpy arrays)
        """
        model = self._get_embedding_model()
        return model.encode(texts, normalize_embeddings=True)

    @staticmethod
    def product_to_document(product: dict) -> str:
        """
        Convert a product dictionary to a searchable document string.

        Args:
            product: Product dictionary with fields from MySQL

        Returns:
            Formatted document string
        """
        parts: list[str] = []
        if product.get("name"):  # MySQL column is 'name', not 'title'
            parts.append(product["name"])
        if product.get("description"):
            parts.append(product["description"])
        if product.get("brand"):
            parts.append(f"Marke: {product['brand']}")
        if product.get("category"):
            parts.append(f"Kategorie: {product['category']}")
        if product.get("tags"):
            parts.append("Tags: " + ", ".join(product["tags"]))
        if product.get("application"):
            parts.append(f"Anwendung: {product['application']}")
        if product.get("load_class"):
            parts.append(f"Belastung: {product['load_class']}")
        if product.get("temperature_range"):
            parts.append(f"Temperatur: {product['temperature_range']}")
        return "\n".join(parts).strip()

    def build_index(
        self, strategy: str = "A", limit: Optional[int] = None, batch_size: int = 64
    ) -> dict:
        """
        Build the product vector index.

        Strategy:
        - A: Append/Update existing index
        - B: Incremental update
        - C: Complete rebuild (delete and recreate)

        Args:
            strategy: Indexing strategy ('A', 'B', or 'C')
            limit: Optional limit on number of products to index
            batch_size: Batch size for upserting points

        Returns:
            Dictionary with indexing statistics
        """
        t0 = time.time()
        log.info(
            "action=index_service_build_start strategy=%s limit=%s batch_size=%s",
            strategy,
            limit,
            batch_size,
        )

        collection = self.qdrant_repo.default_collection
        vector_dim = current_app.config.get("EMBEDDING_DIM", 384)

        # Strategy C: Complete rebuild
        if (strategy or "").upper().strip() == "C":
            log.info("Strategy C: Complete rebuild - deleting collection")
            self.qdrant_repo.delete_collection(collection)

        # Ensure collection exists
        self.qdrant_repo.ensure_collection(
            collection_name=collection, vector_size=vector_dim, distance="COSINE"
        )

        # Load products from MySQL
        products = self.mysql_repo.load_products_for_index(limit=limit, include_tags=True)
        processed = len(products)

        if processed == 0:
            log.info("action=index_service_build_empty strategy=%s", strategy)
            return {
                "strategy": strategy,
                "processed": 0,
                "written": 0,
                "seconds": round(time.time() - t0, 3),
            }

        # Convert products to documents and generate embeddings
        docs = [self.product_to_document(p) for p in products]
        vectors = self.embed_texts(docs)

        log.info(f"Generated {len(vectors)} embeddings for {processed} products")

        # Upsert in batches
        written = 0
        for i in range(0, processed, batch_size):
            batch_products = products[i : i + batch_size]
            batch_docs = docs[i : i + batch_size]
            batch_vectors = vectors[i : i + batch_size]

            points: list[dict] = []
            for p, doc, vec in zip(batch_products, batch_docs, batch_vectors):
                payload = {
                    "mysql_id": p["id"],
                    ##"sku": p.get("sku"),
                    "name": p.get("name"),  # MySQL column is 'name'
                    "brand": p.get("brand"),
                    "category": p.get("category"),
                    "tags": p.get("tags", []),
                    "price": float(p["price"]) if p.get("price") is not None else None,
                    ## "doc_preview": doc[:300],
                    "document": doc,
                    "indexed_at": datetime.utcnow().isoformat(),
                }
                sku = p.get("sku")
                if sku:  # nur wenn nicht None/leer
                    payload["sku"] = sku
                points.append({"id": p["id"], "vector": vec.tolist(), "payload": payload})

            self.qdrant_repo.upsert_points(collection_name=collection, points=points)
            written += len(points)

            log.debug(f"Batch {i // batch_size + 1}: Upserted {len(points)} points")

        # Log to ETL run log
        try:
            self.mysql_repo.log_etl_run(
                strategy=strategy, products_processed=processed, products_written=written
            )
        except Exception as e:
            log.warning(f"Failed to log ETL run: {e}")

        elapsed = round(time.time() - t0, 3)
        log.info(
            "action=index_service_build_done strategy=%s processed=%s written=%s seconds=%s",
            strategy,
            processed,
            written,
            elapsed,
        )

        return {
            "strategy": strategy,
            "processed": processed,
            "written": written,
            "seconds": elapsed,
        }

    def get_index_status(self) -> dict:
        """
        Get current index status.

        Returns:
            Dictionary with index statistics
        """
        collection = self.qdrant_repo.default_collection
        count_indexed = 0
        last_indexed_at = None
        collection_info: dict = {}

        # Get count from Qdrant
        try:
            count_indexed = self.qdrant_repo.count(collection_name=collection, exact=True)
        except Exception as e:
            log.error(f"Failed to get Qdrant count: {e}")

        # Get collection info from Qdrant
        try:
            collection_info = self.qdrant_repo.get_collection_info(collection)
        except Exception as e:
            log.error(f"Failed to get collection info: {e}")

        # Get last indexed timestamp from MySQL
        try:
            dashboard_stats = self.mysql_repo.get_dashboard_stats()
            last_indexed_at = dashboard_stats.get("last_indexed_at")
        except Exception as e:
            log.error(f"Failed to get last indexed timestamp: {e}")

        return {
            "count_indexed": count_indexed,
            "last_indexed_at": last_indexed_at,
            "collection_info": collection_info,
            "embedding_model": current_app.config.get(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
        }

    def truncate_index(self, collection_name: Optional[str] = None) -> None:
        """
        Truncate (delete and recreate) the index.

        Args:
            collection_name: Optional collection name (uses default if None)
        """
        collection = collection_name or self.qdrant_repo.default_collection
        vector_dim = current_app.config.get("EMBEDDING_DIM", 384)
        log.info("action=index_service_truncate_start collection=%s", collection)

        # Delete collection
        self.qdrant_repo.delete_collection(collection)

        # Recreate empty collection
        self.qdrant_repo.ensure_collection(
            collection_name=collection, vector_size=vector_dim, distance="COSINE"
        )

        log.info("action=index_service_truncate_done collection=%s", collection)

    def get_collection_info(self, collection_name: Optional[str] = None) -> dict:
        """
        Get detailed information about a collection.

        Args:
            collection_name: Optional collection name (uses default if None)

        Returns:
            Dictionary with collection information
        """
        collection = collection_name or self.qdrant_repo.default_collection
        return self.qdrant_repo.get_collection_info(collection)
