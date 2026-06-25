from src.domain.interfaces.repository import TransactionRepository
from src.domain.models.transaction import Transaction


class InMemoryTransactionRepository(TransactionRepository):
    def __init__(self):
        self._store: dict[str, Transaction] = {}

    async def create(self, transaction: Transaction) -> Transaction:
        self._store[transaction.transaction_id] = transaction
        return transaction

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        return self._store.get(transaction_id)

    async def get_by_user_id(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> list[Transaction]:
        user_txs = [
            tx for tx in self._store.values() if tx.user_id == user_id
        ]
        user_txs.sort(key=lambda t: t.date, reverse=True)
        start = (page - 1) * limit
        return user_txs[start : start + limit]

    async def update(self, transaction: Transaction) -> Transaction:
        self._store[transaction.transaction_id] = transaction
        return transaction

    async def delete(self, transaction_id: str) -> None:
        self._store.pop(transaction_id, None)
