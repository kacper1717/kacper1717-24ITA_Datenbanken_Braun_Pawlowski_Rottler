"""Search route - Unified search interface"""
import logging
from flask import Blueprint, flash, render_template, request

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("search", __name__)


@bp.route("/search", methods=["GET", "POST"])
def search():
    """Unified search: vector, SQL, RAG, graph, PDF"""
    search_service = ServiceFactory.get_search_service()

    search_type = request.args.get("type", request.form.get("type", "sql"))
    query = request.form.get("query", request.args.get("q", ""))
    topk = _get_int(request.form.get("topk", "5"), 5)

    results = []
    answer = None

    if query and request.method == "POST":
        if search_type == "vector":
            raw = search_service.vector_search(query, topk=topk)
            results = [
                {
                    "title": r.get("name", ""),
                    "brand": r.get("brand", ""),
                    "price": r.get("price", 0),
                    "score": r.get("score"),
                    "doc_preview": r.get("document", ""),
                    "graph_source": None,
                }
                for r in raw
            ]

        elif search_type == "sql":
            try:
                product_service = ServiceFactory.get_product_service()
                results = product_service.execute_sql_query(query)
            except Exception as e:
                log.error(f"SQL search error: {e}")
                flash(str(e), "danger")

    return render_template(
        "search_unified.html",
        query=query,
        search_type=search_type,
        results=results,
        answer=answer,
        vector_results=[],
        sql_results=[],
    )
