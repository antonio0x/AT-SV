from decimal import Decimal

from src.domain.interfaces.repository import (
    TransactionRepository,
    DeclarationRepository,
    EmployeeRepository,
)
from src.domain.models.tax_declaration import (
    TaxDeclaration,
    FormType,
)
from src.domain.services.tax_engine import calculate_f07, calculate_f14, calculate_f06


class CalculateDeclarationUseCase:
    def __init__(
        self,
        tx_repo: TransactionRepository,
        decl_repo: DeclarationRepository,
        emp_repo: EmployeeRepository,
    ):
        self._tx_repo = tx_repo
        self._decl_repo = decl_repo
        self._emp_repo = emp_repo

    async def execute(
        self,
        user_id: str,
        form_type: str,
        year: int,
        period: str,
    ) -> TaxDeclaration:
        all_txs = await self._tx_repo.get_by_user_id(user_id, page=1, limit=9999)
        period_txs = [
            t
            for t in all_txs
            if t.date.year == year and t.date.month == int(period)
        ]

        form = FormType(form_type)
        decl = TaxDeclaration(
            user_id=user_id,
            form_type=form,
            period=period,
            year=year,
        )

        if form == FormType.F07:
            decl.f07 = calculate_f07(period_txs)
            decl.total_iva = decl.f07.total_iva
        elif form == FormType.F14:
            previous_period = f"{int(period) - 1:02d}" if int(period) > 1 else "12"
            previous_year = year if int(period) > 1 else year - 1
            prev = await self._decl_repo.get_by_period(
                user_id, form_type, previous_year, previous_period
            )
            saldo_anterior = Decimal("0")
            if prev and prev.f14:
                saldo_anterior = prev.f14.saldo_a_favor_anterior
            decl.f14 = calculate_f14(period_txs, saldo_anterior)
        elif form == FormType.F06:
            employees = await self._emp_repo.get_by_user_id(user_id)
            decl.f06 = calculate_f06(employees)

        return decl
