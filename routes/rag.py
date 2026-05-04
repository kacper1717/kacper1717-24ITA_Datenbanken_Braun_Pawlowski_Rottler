"""RAG route - Retrieval-Augmented Generation with graph enrichment"""
import logging
from flask import Blueprint, flash, render_template, request

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("rag", __name__)


@bp.route("/rag", methods=["GET", "POST"])
def rag():
    """RAG search with Neo4j graph enrichment"""
    search_service = ServiceFactory.get_search_service()
    query = request.form.get("query", request.args.get("q", ""))
    topk = _get_int(request.form.get("topk", "5"), 5)

    results = []
    answer = None

    if query and request.method == "POST":
        try:
            rag_result = search_service.rag_search(
                strategy="rag",
                query=query,
                topk=topk,
                use_graph_enrichment=False,
            )
            results = rag_result.get("hits", [])
            answer = rag_result.get("answer")
        except Exception as e:
            log.exception("RAG route error")
            flash(str(e), "danger")

    return render_template(
        "search_unified.html",
        query=query,
        search_type="rag",
        results=results,
        answer=answer,
        vector_results=[],
        sql_results=[],
    )


@bp.route("/graph-rag", methods=["GET", "POST"])
def graph_rag():
    """Graph-RAG with PDF upload support"""
    search_service = ServiceFactory.get_search_service()
    query = request.form.get("query", request.args.get("q", ""))
    topk = _get_int(request.form.get("topk", "5"), 5)

    results = []
    answer = None

    if query and request.method == "POST":
        try:
            rag_result = search_service.rag_search(
                strategy="graph",
                query=query,
                topk=topk,
                use_graph_enrichment=True,
            )
            results = rag_result.get("hits", [])
            answer = rag_result.get("answer")
        except Exception as e:
            log.exception("Graph-RAG route error")
            flash(str(e), "danger")

    return render_template(
        "search_unified.html",
        query=query,
        search_type="graph",
        results=results,
        answer=answer,
        vector_results=[],
        sql_results=[],
    )
