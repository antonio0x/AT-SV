from datetime import date as _date, datetime
from decimal import Decimal

from src.domain.models.transaction import Transaction, TransactionType
from src.domain.interfaces.repository import TransactionRepository
from src.domain.services.tax_engine import calculate_iva


class RecordTransactionUseCase:
    def __init__(self, transaction_repo: TransactionRepository):
        self._transaction_repo = transaction_repo

    async def execute(
        self,
        user_id: str,
        type: TransactionType,
        amount: Decimal,
        category: str,
        description: str | None = None,
        tx_date: _date | None = None,
        iva_rate: Decimal | None = None,
    ) -> Transaction:
        iva = calculate_iva(amount, iva_rate or Decimal("0.13"))
        transaction = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=description,
            date=tx_date or _date.today(),
            iva_rate=iva_rate or Decimal("0.13"),
        )
        return await self._transaction_repo.create(transaction)
