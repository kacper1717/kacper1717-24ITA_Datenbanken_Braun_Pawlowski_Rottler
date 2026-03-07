from abc import ABC, abstractmethod
from sqlalchemy import text
import db


class ProductRepository(ABC):
    @abstractmethod
    def get_all(self, page: int, page_size: int) -> dict:
        pass


class ProductRepositoryImpl(ProductRepository):
    def get_all(self, page: int, page_size: int) -> dict:
        raise NotImplementedError("TODO: implement product repository listing.")
