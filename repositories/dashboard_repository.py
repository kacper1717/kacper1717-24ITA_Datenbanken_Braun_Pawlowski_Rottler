from abc import ABC, abstractmethod
from sqlalchemy import text
import db


class DashboardRepository(ABC):
    @abstractmethod
    def get_mysql_counts(self) -> dict:
        pass

    @abstractmethod
    def get_last_indexed_at(self):
        pass

    @abstractmethod
    def get_last_runs(self, limit: int = 10) -> list[dict]:
        pass


class DashboardRepositoryImpl(DashboardRepository):
    def __init__(self, mysql_repo):
        self.mysql_repo = mysql_repo

    def get_mysql_counts(self) -> dict:
        """Get counts of products, brands, categories, tags from MySQL."""
        try:
            return self.mysql_repo.get_dashboard_stats().get("mysql_counts", {})
        except Exception:
            return {"products": 0, "brands": 0, "categories": 0, "tags": 0}

    def get_last_indexed_at(self):
        """Get timestamp of last index run."""
        try:
            runs = self.mysql_repo.get_last_runs(limit=1)
            if runs:
                return runs[0].get("run_timestamp")
        except Exception:
            pass
        return None

    def get_last_runs(self, limit: int = 10) -> list[dict]:
        """Get last N ETL run log entries."""
        try:
            return self.mysql_repo.get_last_runs(limit=limit)
        except Exception:
            return []
