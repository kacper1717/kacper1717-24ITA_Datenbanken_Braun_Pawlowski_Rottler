"""Search route - Unified search interface"""
import logging
from flask import Blueprint, flash, render_template, request

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("search", __name__)


@bp.route("/search", methods=["GET", "POST"])
def search():
    """Unified search: vector, RAG, graph, PDF, SQL"""
    raise NotImplementedError("TODO: implement unified search.")
