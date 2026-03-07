"""
Repository Layer - Data Access Factory

Provides centralized access to all repositories with dependency injection.
"""
import os
import logging
from typing import Optional

from flask import current_app

from .mysql_repository import MySQLRepository, MySQLRepositoryImpl
from .qdrant_repository import QdrantRepository, QdrantRepositoryImpl
from .neo4j_repository import Neo4jRepository, Neo4jRepositoryImpl, NoOpNeo4jRepository
from .product_repository import ProductRepository, ProductRepositoryImpl
from .dashboard_repository import DashboardRepository, DashboardRepositoryImpl
from .audit_repository import AuditRepository, AuditRepositoryImpl

log = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Factory for creating and managing repository instances.

    Uses singleton pattern to reuse instances across the application.
    Supports dependency injection for testing.
    """

    _instances = {}

    @classmethod
    def reset(cls):
        """Reset all cached instances (useful for testing)"""
        raise NotImplementedError("TODO: implement RepositoryFactory.reset().")

    @classmethod
    def get_mysql_repository(cls, session_factory=None) -> MySQLRepository:
        """
        Get MySQL repository instance.

        Args:
            session_factory: Optional SQLAlchemy session factory for testing

        Returns:
            MySQLRepository instance
        """
        raise NotImplementedError("TODO: implement MySQL repository creation.")

    @classmethod
    def get_qdrant_repository(cls, qdrant_url: Optional[str] = None) -> QdrantRepository:
        """
        Get Qdrant repository instance.

        Args:
            qdrant_url: Optional Qdrant URL (uses config if None)

        Returns:
            QdrantRepository instance
        """
        raise NotImplementedError("TODO: implement Qdrant repository creation.")

    @classmethod
    def get_neo4j_repository(
        cls, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None
    ) -> Neo4jRepository:
        """
        Get Neo4j repository instance.

        Args:
            uri: Optional Neo4j URI (uses config if None)
            user: Optional Neo4j user (uses config if None)
            password: Optional Neo4j password (uses config if None)

        Returns:
            Neo4jRepository instance
        """
        raise NotImplementedError("TODO: implement Neo4j repository creation.")

    @classmethod
    def get_product_repository(cls) -> ProductRepository:
        """
        Get Product repository instance (legacy).

        Returns:
            ProductRepository instance
        """
        raise NotImplementedError("TODO: implement Product repository creation.")

    @classmethod
    def get_dashboard_repository(cls) -> DashboardRepository:
        """
        Get Dashboard repository instance (legacy).

        Returns:
            DashboardRepository instance
        """
        raise NotImplementedError("TODO: implement Dashboard repository creation.")

    @classmethod
    def get_audit_repository(cls) -> AuditRepository:
        """
        Get Audit repository instance (legacy).

        Returns:
            AuditRepository instance
        """
        raise NotImplementedError("TODO: implement Audit repository creation.")


# Export all repository classes and factory
__all__ = [
    # Abstract base classes
    "MySQLRepository",
    "QdrantRepository",
    "Neo4jRepository",
    "ProductRepository",
    "DashboardRepository",
    "AuditRepository",
    # Concrete implementations
    "MySQLRepositoryImpl",
    "QdrantRepositoryImpl",
    "Neo4jRepositoryImpl",
    "NoOpNeo4jRepository",
    "ProductRepositoryImpl",
    "DashboardRepositoryImpl",
    "AuditRepositoryImpl",
    # Factory
    "RepositoryFactory",
]
