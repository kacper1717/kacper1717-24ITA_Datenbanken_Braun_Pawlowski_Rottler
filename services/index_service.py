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
            import os
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            log.info(f"Loading embedding model: {model_name}")
            self._embedding_model = SentenceTransformer(model_name)
        return self._embedding_model

    def embed_texts(self, texts: list[str]) -> list:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (numpy arrays)
        """
        if not texts:
            return []
        model = self._get_embedding_model()
        # encode returns a numpy array, convert to list of floats for Qdrant
        embeddings = model.encode(texts)
        return embeddings.tolist()

    @staticmethod
    def product_to_document(product: dict) -> str:
        """
        Convert a product dictionary to a searchable document string.

        Args:
            product: Product dictionary with fields

        Returns:
            Formatted document string
        """
        # Combine all relevant fields into a rich text document for better semantic search
        parts = []
        parts.append(f"Produkt: {product.get('name', '')}")
        
        brand = product.get('brand')
        if brand: parts.append(f"Marke: {brand}")
        
        category = product.get('category')
        if category: parts.append(f"Kategorie: {category}")
        
        desc = product.get('description')
        if desc: parts.append(f"Beschreibung: {desc}")
        
        tags = product.get('tags', [])
        if tags: parts.append(f"Tags: {', '.join(tags)}")
        
        return " | ".join(parts)

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
        log.info(f"Starting index build with strategy={strategy}, limit={limit}")
        
        # 1. Fetch products from MySQL
        products = self.mysql_repo.load_products_for_index(limit=limit, include_tags=True)
        if not products:
            log.warning("No products found in MySQL to index.")
            return {"status": "error", "message": "No products found"}

        # 2. Ensure Qdrant collection exists (default vector size for MiniLM is 384)
        import os
        vector_size = int(os.getenv("EMBEDDING_DIM", "384"))
        collection = "products"
        self.qdrant_repo.ensure_collection(collection_name=collection, vector_size=vector_size)

        # 3. Process in batches
        total_processed = 0
        total_written = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            # Prepare documents
            texts = [self.product_to_document(p) for p in batch]
            
            # Generate embeddings
            embeddings = self.embed_texts(texts)
            
            # Prepare points for Qdrant
            points = []
            for p, emb, txt in zip(batch, embeddings, texts):
                points.append({
                    "id": p["id"],
                    "vector": emb,
                    "payload": {
                        "name": p.get("name"),
                        "brand": p.get("brand"),
                        "category": p.get("category"),
                        "price": float(p.get("price", 0.0)),
                        "document": txt
                    }
                })
            
            # Upsert to Qdrant
            self.qdrant_repo.upsert_points(collection_name=collection, points=points)
            
            total_processed += len(batch)
            total_written += len(points)
            log.info(f"Indexed batch: {total_written}/{len(products)}")

        # 4. Log the run in MySQL
        self.mysql_repo.log_etl_run(
            strategy=strategy,
            products_processed=total_processed,
            products_written=total_written
        )

        return {
            "status": "success",
            "products_processed": total_processed,
            "products_written": total_written
        }

    def get_index_status(self) -> dict:
        """
        Get current index status.

        Returns:
            Dictionary with index statistics
        """
        import os
        count = self.qdrant_repo.count(collection_name="products")
        collection_info = self.get_collection_info()

        last_indexed_at = None
        runs = self.mysql_repo.get_last_runs(limit=1)
        if runs:
            last_indexed_at = runs[0].get("run_timestamp")

        return {
            "indexed_products": count,
            "count_indexed": count,
            "status": "online" if count > 0 else "empty",
            "last_indexed_at": last_indexed_at,
            "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            "collection_info": collection_info,
        }

    def truncate_index(self, collection_name: Optional[str] = None) -> None:
        """
        Truncate (delete and recreate) the index.

        Args:
            collection_name: Optional collection name (uses default if None)
        """
        self.qdrant_repo.truncate_index(collection_name=collection_name)

    def get_collection_info(self, collection_name: Optional[str] = None) -> dict:
        """
        Get detailed information about a collection.

        Args:
            collection_name: Optional collection name (uses default if None)

        Returns:
            Dictionary with collection information
        """
        col = collection_name or "products"
        return self.qdrant_repo.get_collection_info(collection_name=col)
