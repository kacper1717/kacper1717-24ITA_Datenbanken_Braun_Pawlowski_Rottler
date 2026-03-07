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
    raise NotImplementedError("TODO: implement audit view.")
