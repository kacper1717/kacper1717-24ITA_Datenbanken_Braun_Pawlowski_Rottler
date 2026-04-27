"""Dashboard route - Main overview page"""
import logging
from flask import Blueprint, render_template

from services import ServiceFactory

log = logging.getLogger(__name__)
bp = Blueprint("dashboard", __name__)


@bp.get("/")
def dashboard():
    """Main dashboard with MySQL and Qdrant statistics"""
    product_service = ServiceFactory.get_product_service()
    data = product_service.get_dashboard_data()
    mysql_counts = data.get("mysql_counts", {})
    qdrant_counts = data.get("qdrant_counts", {})
    log.info(
        "action=dashboard_view products=%s brands=%s categories=%s indexed=%s",
        mysql_counts.get("products", 0),
        mysql_counts.get("brands", 0),
        mysql_counts.get("categories", 0),
        qdrant_counts.get("indexed", 0),
    )
    return render_template("dashboard.html", data=data)
