from abc import ABC, abstractmethod
from typing import AsyncContextManager
from src.domain.interfaces.repository import UserRepository, TransactionRepository


class UnitOfWork(ABC, AsyncContextManager["UnitOfWork"]):
    users: UserRepository
    transactions: TransactionRepository

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, *args) -> None:
        ...
