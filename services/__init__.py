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
        raise NotImplementedError("TODO: implement ServiceFactory.reset().")

    @classmethod
    def _get_embedding_model(cls) -> SentenceTransformer:
        """
        Get shared embedding model instance (expensive to load).

        Returns:
            SentenceTransformer instance
        """
        raise NotImplementedError("TODO: implement shared embedding model setup.")

    @classmethod
    def _get_llm_client(cls) -> Optional[OpenAI]:
        """
        Get shared OpenAI client instance.

        Returns:
            OpenAI client or None if API key not configured
        """
        raise NotImplementedError("TODO: implement shared LLM client setup.")

    @classmethod
    def get_search_service(cls) -> SearchService:
        """
        Get SearchService instance.

        Returns:
            SearchService instance with injected dependencies
        """
        raise NotImplementedError("TODO: implement SearchService creation.")

    @classmethod
    def get_index_service(cls) -> IndexService:
        """
        Get IndexService instance.

        Returns:
            IndexService instance with injected dependencies
        """
        raise NotImplementedError("TODO: implement IndexService creation.")

    @classmethod
    def get_pdf_service(cls) -> PDFService:
        """
        Get PDFService instance.

        Returns:
            PDFService instance with injected dependencies
        """
        raise NotImplementedError("TODO: implement PDFService creation.")

    @classmethod
    def get_product_service(cls) -> ProductService:
        """
        Get ProductService instance.

        Returns:
            ProductService instance with injected dependencies
        """
        raise NotImplementedError("TODO: implement ProductService creation.")


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
