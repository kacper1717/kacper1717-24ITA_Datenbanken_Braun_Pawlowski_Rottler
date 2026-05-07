"""Audit route - View ETL run log"""
import logging
from flask import Blueprint, render_template, request

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("audit", __name__)


@bp.get("/audit")
def audit():
    """View audit log with pagination"""
    page = _get_int(request.args.get("page"), 1)
    page_size = _get_int(request.args.get("page_size"), 50)
    product_service = ServiceFactory.get_product_service()

    try:
        result = product_service.get_audit_log(page=page, page_size=page_size)
    except Exception as e:
        log.error(f"Error loading audit log: {e}")
        result = {"items": [], "total": 0}

    return render_template("audit.html", result=result, page=page, page_size=page_size)
