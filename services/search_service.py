"""
Search Service - Business Logic for Search Operations

Handles vector search, RAG (Retrieval-Augmented Generation), and graph enrichment.
"""
import logging
from typing import Optional, Iterable

from flask import current_app
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from repositories import QdrantRepository, Neo4jRepository

log = logging.getLogger(__name__)


class SearchService:
    """Service for search operations with vector DB, graph enrichment, and LLM"""

    def __init__(
        self,
        qdrant_repo: QdrantRepository,
        neo4j_repo: Optional[Neo4jRepository],
        embedding_model: Optional[SentenceTransformer] = None,
        llm_client: Optional[OpenAI] = None,
    ):
        """
        Initialize search service.

        Args:
            qdrant_repo: Qdrant repository for vector search
            neo4j_repo: Optional Neo4j repository for graph enrichment
            embedding_model: Optional pre-initialized embedding model
            llm_client: Optional pre-initialized OpenAI client
        """
        self.qdrant_repo = qdrant_repo
        self.neo4j_repo = neo4j_repo
        self._embedding_model = embedding_model
        self._llm_client = llm_client

    def _get_embedding_model(self) -> SentenceTransformer:
        """Lazy-load embedding model"""
        if self._embedding_model is None:
            import os
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            log.info(f"Loading embedding model: {model_name}")
            self._embedding_model = SentenceTransformer(model_name)
        return self._embedding_model

    def _get_llm_client(self) -> OpenAI:
        """Lazy-load OpenAI client"""
        raise NotImplementedError("TODO: implement LLM client loading.")

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
        embeddings = model.encode(texts)
        return embeddings.tolist()

    def vector_search(
        self, query: str, topk: int = 5, collection_name: Optional[str] = None
    ) -> list[dict]:
        """
        Perform vector search on product collection.

        Args:
            query: Search query
            topk: Number of results to return
            collection_name: Optional collection name (uses default if None)

        Returns:
            List of product dictionaries with scores
        """
        if not query:
            return []
            
        col = collection_name or "products"
        
        # 1. Embed query
        query_vector = self.embed_texts([query])[0]
        
        # 2. Search in Qdrant
        results = self.qdrant_repo.search(
            collection_name=col,
            query_vector=query_vector,
            limit=topk,
            with_payload=True
        )
        
        # 3. Format results
        formatted_results = []
        for r in results:
            payload = r.payload or {}
            formatted_results.append({
                "id": r.id,
                "score": r.score,
                "name": payload.get("name", "Unknown"),
                "brand": payload.get("brand", ""),
                "category": payload.get("category", ""),
                "price": payload.get("price", 0.0),
                "document": payload.get("document", "")
            })
            
        return formatted_results

    def rag_search(
        self, strategy: str, query: str, topk: int = 5, use_graph_enrichment: bool = True
    ) -> dict:
        """
        Perform RAG (Retrieval-Augmented Generation) search with graph enrichment.

        Args:
            strategy: Search strategy (not used currently, for compatibility)
            query: Search query
            topk: Number of results to retrieve
            use_graph_enrichment: Whether to enrich results with Neo4j data

        Returns:
            Dictionary with 'query', 'answer', 'hits'
        """
        raise NotImplementedError("TODO: implement RAG search.")

    def pdf_rag_search(
        self, query: str, topk: int = 5, pdf_collection: str = "pdf_skripte"
    ) -> Optional[dict]:
        """
        Search in PDF documents with RAG.

        Args:
            query: Search query
            topk: Number of chunks to retrieve
            pdf_collection: PDF collection name

        Returns:
            Dictionary with 'answer' and 'hits', or None on error
        """
        raise NotImplementedError("TODO: implement PDF RAG search.")

    def search_product_pdfs(
        self, query: str, topk: int = 3, pdf_products_collection: str = "pdf_produkte"
    ) -> list[dict]:
        """
        Search in product PDF documents.

        Args:
            query: Search query
            topk: Number of chunks to retrieve
            pdf_products_collection: Product PDF collection name

        Returns:
            List of hit dictionaries
        """
        raise NotImplementedError("TODO: implement product PDF search.")

    def execute_sql_search(self, query: str) -> list[dict]:
        """
        Keyword search via MySQL using parameterized queries.

        Args:
            query: Search term

        Returns:
            List of result dictionaries
        """
        if not query:
            return []
        try:
            from services import ServiceFactory
            product_service = ServiceFactory.get_product_service()
            results = product_service.search_products_by_keyword(keyword=query, limit=20)
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "brand": r.get("brand"),
                    "category": r.get("category"),
                    "price": r.get("price"),
                    "document": r.get("description", ""),
                }
                for r in results
            ]
        except Exception as e:
            log.error(f"Error in SQL search: {e}")
            return []

    def _generate_llm_answer(self, query: str, hits: list[dict]) -> str:
        """
        Generate LLM answer based on search hits.

        Args:
            query: User query
            hits: List of search hits

        Returns:
            LLM-generated answer string
        """
        raise NotImplementedError("TODO: implement LLM answer generation.")

    @staticmethod
    def _coerce_int(value) -> Optional[int]:
        raise NotImplementedError("TODO: implement int coercion.")

    @classmethod
    def _coerce_ints(cls, values: Iterable) -> list[int]:
        raise NotImplementedError("TODO: implement list int coercion.")
