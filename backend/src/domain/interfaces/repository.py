from abc import ABC, abstractmethod

from src.domain.models.transaction import Transaction
from src.domain.models.user import User


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        ...


class TransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str, page: int = 1, limit: int = 50) -> list[Transaction]:
        ...

    @abstractmethod
    async def update(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def delete(self, transaction_id: str) -> None:
        ...
