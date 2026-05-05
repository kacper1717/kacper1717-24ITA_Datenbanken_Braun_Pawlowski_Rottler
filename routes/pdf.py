"""PDF route - PDF upload and management"""
import logging
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from services import ServiceFactory

log = logging.getLogger(__name__)
bp = Blueprint("pdf", __name__)


@bp.route("/pdf-upload", methods=["GET", "POST"])
def pdf_upload():
    """PDF upload page (GET) or upload handler (POST via forms)"""
    pdf_service = ServiceFactory.get_pdf_service()
    stats = pdf_service.get_pdf_counts()
    teaching_pdfs = pdf_service.list_teaching_pdfs()
    product_pdfs = pdf_service.list_product_pdfs()
    return render_template(
        "pdf_upload.html",
        stats=stats,
        teaching_pdfs=teaching_pdfs,
        product_pdfs=product_pdfs,
    )


@bp.post("/upload-teaching-pdf")
def upload_teaching_pdf():
    """Upload a teaching PDF to Qdrant"""
    pdf_service = ServiceFactory.get_pdf_service()
    pdf_file = request.files.get("pdf_file")
    if not pdf_file:
        flash("Bitte eine PDF-Datei auswählen.", "danger")
        return redirect(url_for("pdf.pdf_upload"))

    try:
        message = pdf_service.upload_pdf_to_qdrant(pdf_file)
        flash(message, "success")
    except Exception as e:
        log.exception("Teaching PDF upload failed")
        flash(f"Fehler beim PDF-Upload: {e}", "danger")
    return redirect(url_for("pdf.pdf_upload"))


@bp.post("/upload-product-pdf")
def upload_product_pdf():
    """Upload a product PDF to Qdrant"""
    pdf_service = ServiceFactory.get_pdf_service()
    pdf_file = request.files.get("pdf_file")
    if not pdf_file:
        flash("Bitte eine Produktkatalog-PDF auswählen.", "danger")
        return redirect(url_for("pdf.pdf_upload"))

    try:
        message = pdf_service.upload_product_pdf(pdf_file)
        flash(message, "success")
    except Exception as e:
        log.exception("Product PDF upload failed")
        flash(f"Fehler beim Produktkatalog-Upload: {e}", "danger")
    return redirect(url_for("pdf.pdf_upload"))


@bp.route("/api/pdf-stats")
def get_pdf_stats():
    """API endpoint: Get PDF statistics for admin page"""
    pdf_service = ServiceFactory.get_pdf_service()
    return jsonify(pdf_service.get_pdf_counts())
