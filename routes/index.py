"""Index route - Build and manage Qdrant vector index"""
import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import ServiceFactory
from utils import _get_int, _get_optional_int

log = logging.getLogger(__name__)
bp = Blueprint("index", __name__)


def _get_index_service_safe():
    """Return index service or None and log detailed failure context."""
    try:
        service = ServiceFactory.get_index_service()
    except Exception:
        log.exception("action=index_service_init_error")
        return None

    if service is None:
        log.error("action=index_service_none")
        return None

    return service


def _empty_index_status() -> dict:
    """Safe default status for template rendering when service is unavailable."""
    return {
        "indexed_products": 0,
        "last_indexed_at": None,
        "embedding_model": None,
        "collection_info": {},
    }


@bp.route("/index", methods=["GET", "POST"])
def index():
    """Index management page - build, truncate, view status"""
    index_service = _get_index_service_safe()

    if index_service is None:
        flash("Index-Service ist aktuell nicht verfuegbar.", "warning")
        log.warning("action=index_service_unavailable method=%s", request.method)
        if request.method == "POST":
            return redirect(url_for("index.index"))
        return render_template("index.html", status=_empty_index_status())

    if request.method == "POST":
        strategy = (request.form.get("strategy") or "C").strip()
        batch_size = _get_int(request.form.get("batch_size"), 64, min_value=1, max_value=10_000)

        limit_raw = request.form.get("limit")
        limit_int = _get_optional_int(limit_raw)
        if limit_raw is not None and str(limit_raw).strip() and limit_int is None:
            log.warning("action=index_build_invalid_limit limit_raw=%r", limit_raw)
            flash("Limit muss eine Zahl sein.", "warning")
            return redirect(url_for("index.index"))

        try:
            log.info(
                "action=index_build_start strategy=%s batch_size=%s limit=%s",
                strategy,
                batch_size,
                limit_int,
            )
            summary = index_service.build_index(
                strategy=strategy, limit=limit_int, batch_size=batch_size
            )
            log.info(
                "action=index_build_done strategy=%s processed=%s written=%s seconds=%s",
                summary.get("strategy"),
                summary.get("processed"),
                summary.get("written"),
                summary.get("seconds"),
            )
            flash(f"Indexlauf erfolgreich: {summary}", "success")
        except Exception:
            log.exception("Indexlauf fehlgeschlagen.")
            flash("Indexlauf fehlgeschlagen. Details siehe Log.", "danger")

        return redirect(url_for("index.index"))

    status = index_service.get_index_status()
    return render_template("index.html", status=status)


@bp.post("/truncate-index")
def truncate_index():
    """Truncate (delete and recreate) the Qdrant index"""
    index_service = _get_index_service_safe()
    if index_service is None:
        flash("Index-Service ist aktuell nicht verfuegbar.", "warning")
        log.warning("action=index_truncate_aborted reason=service_unavailable")
        return redirect(url_for("index.index"))

    log.info("action=index_truncate_start")
    index_service.truncate_index()
    log.info("action=index_truncate_done")
    flash("Qdrant-Index wurde geleert.", "success")
    return redirect(url_for("index.index"))
