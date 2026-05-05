from abc import ABC, abstractmethod
from sqlalchemy import text
import db


class AuditRepository(ABC):
    @abstractmethod
    def get_log(self, page: int, page_size: int) -> dict:
        pass


class AuditRepositoryImpl(AuditRepository):
    def __init__(self, mysql_repo):
        self.mysql_repo = mysql_repo

    def get_log(self, page: int, page_size: int) -> dict:
        """Get paginated ETL audit log entries."""
        try:
            return self.mysql_repo.get_audit_entries(page=page, page_size=page_size)
        except Exception:
            return {"items": [], "total": 0}
