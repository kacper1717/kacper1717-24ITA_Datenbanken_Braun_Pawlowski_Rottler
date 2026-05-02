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
    index_service = ServiceFactory.get_index_service()
    
    if request.method == "POST":
        strategy = request.form.get("strategy", "C")
        limit = _get_optional_int(request.form.get("limit"))
        batch_size = _get_int(request.form.get("batch_size"), 64)
        
        try:
            res = index_service.build_index(strategy=strategy, limit=limit, batch_size=batch_size)
            if res.get("status") == "success":
                flash(f"Indexierung erfolgreich! {res.get('products_written')} Produkte verarbeitet.", "success")
            else:
                flash(f"Fehler: {res.get('message')}", "danger")
        except Exception as e:
            log.exception("Index build error")
            flash(f"Fehler bei der Indexierung: {e}", "danger")
            
        return redirect(url_for("index.index"))

    status = index_service.get_index_status()
    info = index_service.get_collection_info()
    return render_template("index.html", status=status, info=info)


@bp.post("/truncate-index")
def truncate_index():
    """Truncate (delete and recreate) the Qdrant index"""
    index_service = ServiceFactory.get_index_service()
    try:
        index_service.truncate_index()
        flash("Index wurde erfolgreich geleert.", "success")
    except Exception as e:
        log.error(f"Error truncating index: {e}")
        flash(f"Fehler beim Leeren des Index: {e}", "danger")
    return redirect(url_for("index.index"))
