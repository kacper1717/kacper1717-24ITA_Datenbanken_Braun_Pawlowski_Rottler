"""Index route - Build and manage Qdrant vector index"""
import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import ServiceFactory
from utils import _get_int, _get_optional_int

log = logging.getLogger(__name__)
bp = Blueprint("index", __name__)


@bp.route("/index", methods=["GET", "POST"])
def index():
    """Index management page - build, truncate, view status"""
    raise NotImplementedError("TODO: implement index page (build/truncate/status).")


@bp.post("/truncate-index")
def truncate_index():
    """Truncate (delete and recreate) the Qdrant index"""
    raise NotImplementedError("TODO: implement index truncation.")
