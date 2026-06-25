"""In-memory fake repositories for local development.

These are module-level singletons so data persists across requests.
Replace DynamoDB repos when USE_FAKE_REPOS=true in Settings.
"""

from datetime import date
from uuid import uuid4

from src.domain.interfaces.repository import (
    UserRepository,
    TransactionRepository,
)
from src.domain.models.user import User
from src.domain.models.transaction import Transaction, TransactionType


class _FakeUserRepository(UserRepository):
    """In-memory user store. Singleton instance via module var."""

    def __init__(self) -> None:
        self._store: dict[str, User] = {}
        self._email_index: dict[str, str] = {}

    async def create(self, user: User) -> User:
        self._store[user.user_id] = user
        self._email_index[user.email] = user.user_id
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        uid = self._email_index.get(email)
        if uid is None:
            return None
        return self._store.get(uid)

    async def update(self, user: User) -> User:
        self._store[user.user_id] = user
        self._email_index[user.email] = user.user_id
        return user

    async def delete(self, user_id: str) -> None:
        user = self._store.pop(user_id, None)
        if user:
            self._email_index.pop(user.email, None)


class _FakeTransactionRepository(TransactionRepository):
    """In-memory transaction store. Singleton instance via module var."""

    def __init__(self) -> None:
        self._store: dict[str, Transaction] = {}

    async def create(self, transaction: Transaction) -> Transaction:
        self._store[transaction.transaction_id] = transaction
        return transaction

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        return self._store.get(transaction_id)

    async def get_by_user_id(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> list[Transaction]:
        all_txs = [
            t for t in self._store.values() if t.user_id == user_id
        ]
        all_txs.sort(key=lambda t: t.date, reverse=True)
        start = (page - 1) * limit
        return all_txs[start : start + limit]

    async def update(self, transaction: Transaction) -> Transaction:
        self._store[transaction.transaction_id] = transaction
        return transaction

    async def delete(self, transaction_id: str) -> None:
        self._store.pop(transaction_id, None)


# Module-level singletons — same instance across all requests
fake_user_repo: UserRepository = _FakeUserRepository()
fake_transaction_repo: TransactionRepository = _FakeTransactionRepository()

def get_user_repo() -> UserRepository:
    return fake_user_repo

def get_transaction_repo() -> TransactionRepository:
    return fake_transaction_repo
