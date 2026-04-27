"""Products route - List products with pagination"""
import logging
from flask import Blueprint, render_template, request

from services import ServiceFactory
from utils import _get_int

log = logging.getLogger(__name__)
bp = Blueprint("products", __name__)


@bp.get("/products")
def products():
    """List products with brand, category, and tags"""
    product_service = ServiceFactory.get_product_service()

    page = _get_int(request.args.get("page"), 1, min_value=1, max_value=100_000)
    page_size = _get_int(request.args.get("page_size"), 20, min_value=1, max_value=200)
    log.info("action=products_list_start page=%s page_size=%s", page, page_size)

    result = product_service.list_products_joined(page=page, page_size=page_size)

    total = result["total"]
    total_pages = (total + page_size - 1) // page_size
    log.info(
        "action=products_list_done page=%s page_size=%s items=%s total=%s total_pages=%s",
        page,
        page_size,
        len(result.get("items", [])),
        total,
        total_pages,
    )

    return render_template(
        "products.html",
        result=result,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
