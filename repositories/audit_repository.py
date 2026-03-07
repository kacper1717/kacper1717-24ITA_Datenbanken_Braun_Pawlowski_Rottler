from abc import ABC, abstractmethod
from sqlalchemy import text
import db


class AuditRepository(ABC):
    @abstractmethod
    def get_log(self, page: int, page_size: int) -> dict:
        pass


class AuditRepositoryImpl(AuditRepository):
    def get_log(self, page: int, page_size: int) -> dict:
        raise NotImplementedError("TODO: implement audit log retrieval.")
