"""PDF route - PDF upload and management"""
import logging
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from services import ServiceFactory

log = logging.getLogger(__name__)
bp = Blueprint("pdf", __name__)


@bp.route("/pdf-upload", methods=["GET", "POST"])
def pdf_upload():
    """PDF upload page (GET) or upload handler (POST via forms)"""
    raise NotImplementedError("TODO: implement PDF upload page.")


@bp.post("/upload-teaching-pdf")
def upload_teaching_pdf():
    """Upload a teaching PDF to Qdrant"""
    raise NotImplementedError("TODO: implement teaching PDF upload.")


@bp.post("/upload-product-pdf")
def upload_product_pdf():
    """Upload a product PDF to Qdrant"""
    raise NotImplementedError("TODO: implement product PDF upload.")


@bp.route("/api/pdf-stats")
def get_pdf_stats():
    """API endpoint: Get PDF statistics for admin page"""
    raise NotImplementedError("TODO: implement PDF stats endpoint.")
