"""Products route - List products with pagination"""
import logging
from flask import Blueprint, render_template, request

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("products", __name__)


@bp.get("/products")
def products():
    """List products with brand, category, and tags"""
    raise NotImplementedError("TODO: implement products listing.")
