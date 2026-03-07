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
    def get_mysql_counts(self) -> dict:
        raise NotImplementedError("TODO: implement MySQL counts.")

    def get_last_indexed_at(self):
        raise NotImplementedError("TODO: implement last indexed timestamp.")

    def get_last_runs(self, limit: int = 10) -> list[dict]:
        raise NotImplementedError("TODO: implement last runs.")
