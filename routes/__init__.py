"""
Routes Package - Blueprint Registry

Exports all Flask blueprints for registration in app.py
"""

from .dashboard import bp as dashboard_bp
from .products import bp as products_bp
from .index import bp as index_bp
from .audit import bp as audit_bp
from .search import bp as search_bp
from .rag import bp as rag_bp
from .validate import bp as validate_bp
from .pdf import bp as pdf_bp

__all__ = [
    "dashboard_bp",
    "products_bp",
    "index_bp",
    "audit_bp",
    "search_bp",
    "rag_bp",
    "validate_bp",
    "pdf_bp",
]
