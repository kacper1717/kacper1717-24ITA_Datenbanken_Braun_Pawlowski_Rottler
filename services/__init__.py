"""
Service Layer - Business Logic Factory

Provides centralized access to all services with dependency injection.
"""
import logging
from typing import Optional

from flask import current_app
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from repositories import RepositoryFactory

# Import all services
from .search_service import SearchService
from .index_service import IndexService
from .pdf_service import PDFService
from .product_service import ProductService

log = logging.getLogger(__name__)


class ServiceFactory:
    """
    Factory for creating and managing service instances.

    Uses singleton pattern to reuse instances and shared resources (embedding models, LLM clients).
    Supports dependency injection for testing.
    """

    _instances = {}
    _shared_resources = {}

    @classmethod
    def reset(cls):
        """Reset all cached instances (useful for testing)"""
        cls._instances.clear()
        cls._shared_resources.clear()
        RepositoryFactory.reset()
        log.debug("Service factory instances cleared")

    @classmethod
    def _get_embedding_model(cls) -> SentenceTransformer:
        """
        Get shared embedding model instance (expensive to load).

        Returns:
            SentenceTransformer instance
        """
        if "embedding_model" not in cls._shared_resources:
            model_name = current_app.config.get(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            )
            cls._shared_resources["embedding_model"] = SentenceTransformer(model_name)
            log.info(f"✓ Shared embedding model loaded: {model_name}")
        return cls._shared_resources["embedding_model"]

    @classmethod
    def _get_llm_client(cls) -> Optional[OpenAI]:
        """
        Get shared OpenAI client instance.

        Returns:
            OpenAI client or None if API key not configured
        """
        if "llm_client" not in cls._shared_resources:
            api_key = current_app.config.get("OPENAI_API_KEY")
            if not api_key:
                log.warning("OPENAI_API_KEY not configured - LLM features disabled")
                cls._shared_resources["llm_client"] = None
            else:
                cls._shared_resources["llm_client"] = OpenAI(api_key=api_key)
                log.info("✓ Shared OpenAI client initialized")
        return cls._shared_resources["llm_client"]

    @classmethod
    def get_search_service(cls) -> SearchService:
        """
        Get SearchService instance.

        Returns:
            SearchService instance with injected dependencies
        """
        if "search" not in cls._instances:
            qdrant_repo = RepositoryFactory.get_qdrant_repository()
            neo4j_repo = RepositoryFactory.get_neo4j_repository()
            embedding_model = cls._get_embedding_model()
            llm_client = cls._get_llm_client()

            cls._instances["search"] = SearchService(
                qdrant_repo=qdrant_repo,
                neo4j_repo=neo4j_repo,
                embedding_model=embedding_model,
                llm_client=llm_client,
            )
            log.debug("SearchService instance created")
        return cls._instances["search"]

    @classmethod
    def get_index_service(cls) -> IndexService:
        """
        Get IndexService instance.

        Returns:
            IndexService instance with injected dependencies
        """
        if "index" not in cls._instances:
            qdrant_repo = RepositoryFactory.get_qdrant_repository()
            mysql_repo = RepositoryFactory.get_mysql_repository()
            embedding_model = cls._get_embedding_model()

            cls._instances["index"] = IndexService(
                qdrant_repo=qdrant_repo,
                mysql_repo=mysql_repo,
                embedding_model=embedding_model,
            )
            log.debug("IndexService instance created")
        return cls._instances["index"]

    @classmethod
    def get_pdf_service(cls) -> PDFService:
        """
        Get PDFService instance.

        Returns:
            PDFService instance with injected dependencies
        """
        if "pdf" not in cls._instances:
            qdrant_repo = RepositoryFactory.get_qdrant_repository()
            embedding_model = cls._get_embedding_model()

            cls._instances["pdf"] = PDFService(
                qdrant_repo=qdrant_repo,
                embedding_model=embedding_model,
            )
            log.debug("PDFService instance created")
        return cls._instances["pdf"]

    @classmethod
    def get_product_service(cls) -> ProductService:
        """
        Get ProductService instance.

        Returns:
            ProductService instance with injected dependencies
        """
        if "product" not in cls._instances:
            mysql_repo = RepositoryFactory.get_mysql_repository()
            qdrant_repo = RepositoryFactory.get_qdrant_repository()

            cls._instances["product"] = ProductService(
                mysql_repo=mysql_repo,
                qdrant_repo=qdrant_repo,
            )
            log.debug("ProductService instance created")
        return cls._instances["product"]


# Export all service classes and factory
__all__ = [
    # Service classes
    "SearchService",
    "IndexService",
    "PDFService",
    "ProductService",
    # Factory
    "ServiceFactory",
]
