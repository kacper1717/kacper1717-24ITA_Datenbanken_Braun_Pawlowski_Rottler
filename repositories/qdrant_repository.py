"""
Qdrant Repository - Data Access Layer for Qdrant Vector Database
Handles all Qdrant-specific vector operations.
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging
from datetime import datetime
import uuid
from io import BytesIO

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, HnswConfigDiff, PointStruct
import pdfplumber

log = logging.getLogger(__name__)


class QdrantRepository(ABC):
    """Abstract base class for Qdrant vector database operations"""

    @abstractmethod
    def ensure_collection(
        self, collection_name: str, vector_size: int, distance: str = "COSINE"
    ) -> None:
        """Ensure a collection exists, create if not"""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection"""
        pass

    @abstractmethod
    def count(self, collection_name: str, exact: bool = True) -> int:
        """Count points in a collection"""
        pass

    @abstractmethod
    def upsert_points(
        self, collection_name: str, points: list[dict]
    ) -> None:
        """Upsert points into a collection"""
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        with_payload: bool = True,
    ) -> list:
        """Search for similar vectors"""
        pass

    @abstractmethod
    def scroll(
        self, collection_name: str, limit: int = 100, with_payload: bool = True
    ) -> tuple[list, Optional[str]]:
        """Scroll through all points in a collection"""
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        """Get information about a collection"""
        pass


class QdrantRepositoryImpl(QdrantRepository):
    """Concrete implementation of Qdrant repository"""

    def __init__(self, qdrant_url: str, default_collection: str = "products"):
        """
        Initialize Qdrant repository.

        Args:
            qdrant_url: Qdrant server URL
            default_collection: Default collection name for products
        """
        # NOTE (Skeleton): Für viele Aufgaben (z.B. /products) wird Qdrant nicht benötigt.
        # Trotzdem wird der ProductService über die Factory immer mit einem Qdrant-Repo
        # instanziiert. Damit /products nicht an einem Stub scheitert, initialisiert man
        # hier den Client minimal.
        self.qdrant_url = qdrant_url
        self.default_collection = default_collection
        self.client = QdrantClient(url=qdrant_url)
        log.info("✓ Qdrant client initialized url=%s default_collection=%s", qdrant_url, default_collection)

    def ensure_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "COSINE",
        hnsw_m: int = 16,
        hnsw_ef_construct: int = 128,
    ) -> None:
        """
        Ensure a collection exists, create if not.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of the embeddings
            distance: Distance metric (COSINE, DOT, EUCLID)
            hnsw_m: HNSW m parameter (connections per point)
            hnsw_ef_construct: HNSW ef_construct parameter (search width during build)
        """
        try:
            if not self.client.collection_exists(collection_name=collection_name):
                # distance param is string, map to Qdrant Distance enum
                dist_map = {
                    "COSINE": Distance.COSINE,
                    "DOT": Distance.DOT,
                    "EUCLID": Distance.EUCLID
                }
                d = dist_map.get(distance.upper(), Distance.COSINE)
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=d),
                    hnsw_config=HnswConfigDiff(m=hnsw_m, ef_construct=hnsw_ef_construct)
                )
                log.info(f"Created Qdrant collection: {collection_name}")
        except Exception as e:
            log.error(f"Error ensuring collection {collection_name}: {e}")

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete
        """
        try:
            if self.client.collection_exists(collection_name=collection_name):
                self.client.delete_collection(collection_name=collection_name)
                log.info(f"Deleted Qdrant collection: {collection_name}")
        except Exception as e:
            log.error(f"Error deleting collection {collection_name}: {e}")

    def count(self, collection_name: str, exact: bool = True) -> int:
        """
        Count points in a collection.

        Args:
            collection_name: Name of the collection
            exact: Whether to use exact count (slower but accurate)

        Returns:
            Number of points in collection
        """
        try:
            if not self.client.collection_exists(collection_name=collection_name):
                return 0
            response = self.client.count(collection_name=collection_name, exact=exact)
            return response.count
        except Exception as e:
            log.error(f"Error counting in {collection_name}: {e}")
            return 0

    def upsert_points(self, collection_name: str, points: list[dict]) -> None:
        """
        Upsert points into a collection.

        Args:
            collection_name: Name of the collection
            points: List of point dictionaries with 'id', 'vector', 'payload'
        """
        if not points:
            return
        try:
            qdrant_points = [
                PointStruct(
                    id=p.get('id'),
                    vector=p.get('vector'),
                    payload=p.get('payload', {})
                ) for p in points
            ]
            self.client.upsert(collection_name=collection_name, points=qdrant_points)
        except Exception as e:
            log.error(f"Error upserting points to {collection_name}: {e}")

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        with_payload: bool = True,
        hnsw_ef: int = 64,
    ) -> list:
        """
        Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            limit: Maximum number of results
            with_payload: Whether to include payload
            hnsw_ef: HNSW ef parameter (higher = more accurate but slower)

        Returns:
            List of search results (points)
        """
        try:
            from qdrant_client.http.models import SearchParams
            response = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                with_payload=with_payload,
                search_params=SearchParams(hnsw_ef=hnsw_ef)
            )
            return response.points
        except Exception as e:
            log.error(f"Error searching {collection_name}: {e}")
            return []

    def scroll(
        self,
        collection_name: str,
        limit: int = 100,
        with_payload: bool = True,
        offset: Optional[str] = None,
    ) -> tuple[list, Optional[str]]:
        """
        Scroll through all points in a collection.

        Args:
            collection_name: Name of the collection
            limit: Number of points to retrieve
            with_payload: Whether to include payload
            offset: Offset for pagination

        Returns:
            Tuple of (points, next_offset)
        """
        try:
            records, next_page_offset = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=with_payload,
                offset=offset
            )
            return records, next_page_offset
        except Exception as e:
            log.error(f"Error scrolling {collection_name}: {e}")
            return [], None

    def get_collection_info(self, collection_name: str) -> dict:
        """
        Get information about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection info
        """
        try:
            if not self.client.collection_exists(collection_name=collection_name):
                return {"status": "not_found"}
            info = self.client.get_collection(collection_name=collection_name)
            vectors_config = info.config.params.vectors
            hnsw_config = info.config.hnsw_config
            return {
                "name": collection_name,
                "status": str(info.status),
                "points_count": info.points_count,
                "vector_size": vectors_config.size if vectors_config else None,
                "distance": vectors_config.distance.name if vectors_config and vectors_config.distance else None,
                "hnsw_m": hnsw_config.m if hnsw_config else None,
                "hnsw_ef_construct": hnsw_config.ef_construct if hnsw_config else None,
            }
        except Exception as e:
            log.error(f"Error getting info for {collection_name}: {e}")
            return {"status": "error"}

    # ======================
    # High-level operations
    # ======================

    def truncate_index(self, collection_name: Optional[str] = None) -> None:
        """
        Truncate (delete and recreate) a collection.

        Args:
            collection_name: Name of the collection (uses default if None)
        """
        col = collection_name or self.default_collection
        try:
            if self.client.collection_exists(collection_name=col):
                info = self.client.get_collection(collection_name=col)
                size = info.config.params.vectors.size
                distance = info.config.params.vectors.distance
                self.client.delete_collection(collection_name=col)
                
                self.client.create_collection(
                    collection_name=col,
                    vectors_config=VectorParams(size=size, distance=distance)
                )
                log.info(f"Truncated collection {col}")
        except Exception as e:
            log.error(f"Error truncating collection {col}: {e}")

    def get_unique_sources(self, collection_name: str) -> set[str]:
        """
        Get unique source filenames from a collection.

        Useful for PDF collections to count unique uploaded files.

        Args:
            collection_name: Name of the collection

        Returns:
            Set of unique source filenames
        """
        raise NotImplementedError("TODO: implement unique source listing.")

    # ======================
    # PDF-specific operations
    # ======================

    def upload_pdf_chunks(
        self,
        collection_name: str,
        chunks: list[dict],
        embeddings: list,
        source_filename: str,
    ) -> int:
        """
        Upload PDF chunks with embeddings to Qdrant.

        Args:
            collection_name: Name of the collection
            chunks: List of chunk dictionaries with 'text' and 'page'
            embeddings: List of embedding vectors
            source_filename: Source PDF filename

        Returns:
            Number of chunks uploaded
        """
        raise NotImplementedError("TODO: implement PDF chunk upload.")

    @staticmethod
    def extract_pdf_chunks(pdf_file, chunk_size: int = 300) -> list[dict]:
        """
        Extract text chunks from a PDF file.

        Args:
            pdf_file: File object or BytesIO
            chunk_size: Size of each text chunk in characters

        Returns:
            List of chunk dictionaries with 'text' and 'page'
        """
        raise NotImplementedError("TODO: implement PDF text extraction.")

    def get_pdf_counts(
        self, pdf_collection: str, pdf_products_collection: str
    ) -> dict:
        """
        Get count of unique PDF files in both collections.

        Args:
            pdf_collection: Name of the teaching PDF collection
            pdf_products_collection: Name of the product PDF collection

        Returns:
            Dictionary with counts for each collection and total
        """
        raise NotImplementedError("TODO: implement PDF counts.")

    def list_uploaded_pdfs(self, collection_name: str) -> list[str]:
        """
        List all uploaded PDF filenames in a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Sorted list of unique PDF filenames
        """
        raise NotImplementedError("TODO: implement PDF list.")
