from abc import ABC, abstractmethod
from sqlalchemy import text
import db


class ProductRepository(ABC):
    @abstractmethod
    def get_all(self, page: int, page_size: int) -> dict:
        pass


class ProductRepositoryImpl(ProductRepository):
    def __init__(self, mysql_repo):
        self.mysql_repo = mysql_repo

    def get_all(self, page: int, page_size: int) -> dict:
        """Get paginated list of all products with brand, category, and tags."""
        try:
            return self.mysql_repo.get_products_with_joins(page=page, page_size=page_size)
        except Exception:
            return {"items": [], "total": 0}
