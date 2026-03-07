"""RAG route - Retrieval-Augmented Generation with graph enrichment"""
import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("rag", __name__)


@bp.route("/rag", methods=["GET", "POST"])
def rag():
    """RAG search with Neo4j graph enrichment"""
    raise NotImplementedError("TODO: implement RAG route.")


@bp.route("/graph-rag", methods=["GET", "POST"])
def graph_rag():
    """Graph-RAG with PDF upload support"""
    raise NotImplementedError("TODO: implement graph RAG route.")
