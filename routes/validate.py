"""Validate route - MySQL schema validation"""
import logging
from flask import Blueprint, current_app, render_template
from sqlalchemy import create_engine

from validation import validate_mysql

log = logging.getLogger(__name__)
bp = Blueprint("validate", __name__)


@bp.post("/validate")
def validate():
    """Validate MySQL database schema and data integrity"""
    mysql_url = current_app.config.get("MYSQL_URL")
    engine = create_engine(mysql_url, pool_pre_ping=True, future=True)
    report = validate_mysql(engine)
    return render_template("validation_result.html", report=report)
