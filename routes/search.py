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
                    "category": r.get("category", ""),
                    "price": r.get("price", 0),
                    "score": r.get("score"),
                    "doc_preview": r.get("document", ""),
                    "tags": r.get("tags", []),
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

        elif search_type == "pdf":
            try:
                # Mehr Ergebnisse anfordern, um die Deduplizierung auszugleichen
                pdf_result = search_service.pdf_rag_search(query, topk=topk * 2)
                raw_hits = pdf_result.get("hits", []) if pdf_result else []
                
                # Nach (Quelle, Seite) deduplizieren - nur eindeutige PDF-Seiten behalten
                seen = set()
                results = []
                for r in raw_hits:
                    source = r.get("source", "")
                    page = r.get("page", "")
                    key = (source, page)
                    if key not in seen:
                        seen.add(key)
                        results.append({
                            "source": source,
                            "page": page,
                            "score": r.get("score", 0),
                            "text": r.get("text", ""),
                        })
                    # Sobald genug Ergebnisse vorhanden sind, abbrechen
                    if len(results) >= topk:
                        break
                answer = pdf_result.get("answer") if pdf_result else None
            except Exception as e:
                log.exception("PDF search error")
                flash(str(e), "danger")

        elif search_type in {"rag", "graph"}:
            try:
                rag_result = search_service.rag_search(
                    strategy=search_type,
                    query=query,
                    topk=topk,
                    use_graph_enrichment=search_type == "graph",
                )
                raw_hits = rag_result.get("hits", [])
                # Konsistent mit der Vektorsuche formatieren
                results = [
                    {
                        "title": r.get("name", ""),
                        "brand": r.get("brand", ""),
                        "category": r.get("category", ""),
                        "price": r.get("price", 0),
                        "score": r.get("score"),
                        "doc_preview": r.get("document", ""),
                        "tags": r.get("tags", []),
                        "graph_source": r.get("graph_source"),
                    }
                    for r in raw_hits
                ]
                answer = rag_result.get("answer")
            except Exception as e:
                log.exception("RAG search error")
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