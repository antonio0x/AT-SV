from decimal import Decimal
from dataclasses import dataclass

from src.domain.interfaces.repository import TransactionRepository
from src.domain.services.tax_engine import calculate_iva, calculate_pago_cuenta


@dataclass
class TaxProjection:
    total_iva: Decimal
    total_pago_cuenta: Decimal
    total_income: Decimal
    total_expenses: Decimal
    period: str
    year: int


class GetTaxProjectionUseCase:
    def __init__(self, transaction_repo: TransactionRepository):
        self._transaction_repo = transaction_repo

    async def execute(
        self, user_id: str, year: int, period: str
    ) -> TaxProjection:
        transactions = await self._transaction_repo.get_by_user_id(user_id)
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        for tx in transactions:
            if tx.date.year != year:
                continue
            if tx.type.value == "income":
                total_income += tx.amount
            else:
                total_expenses += tx.amount
        total_iva = calculate_iva(total_income)
        total_pago_cuenta = calculate_pago_cuenta(total_income, Decimal("0.01"))
        return TaxProjection(
            total_iva=total_iva,
            total_pago_cuenta=total_pago_cuenta,
            total_income=total_income,
            total_expenses=total_expenses,
            period=period,
            year=year,
        )
