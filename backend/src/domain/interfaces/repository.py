from abc import ABC, abstractmethod
from uuid import UUID
from src.domain.models.user import User
from src.domain.models.transaction import Transaction


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        ...


class TransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[Transaction]:
        ...

    @abstractmethod
    async def update(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def delete(self, transaction_id: UUID) -> None:
        ...
