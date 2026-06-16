from fastapi import APIRouter, Depends

from src.api.bff.response import BFFResponse
from src.api.bff.schemas import TaxProjectionBFF
from src.application.use_cases.get_tax_projection import (
    GetTaxProjectionUseCase,
)
from src.infrastructure.database import get_settings

router = APIRouter(tags=["taxes"])


def get_tx_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.fake_repos import fake_transaction_repo
        return fake_transaction_repo
    from src.infrastructure.repositories.transaction_repo import DynamoDBTransactionRepository
    return DynamoDBTransactionRepository()


@router.get("/taxes/projection", response_model=BFFResponse[TaxProjectionBFF])
async def tax_projection(
    user_id: str,
    year: int,
    period: str,
    repo=Depends(get_tx_repo),
):
    use_case = GetTaxProjectionUseCase(repo)
    projection = await use_case.execute(
        user_id=user_id, year=year, period=period
    )
    return BFFResponse.ok(
        data=TaxProjectionBFF(
            total_iva=projection.total_iva,
            total_pago_cuenta=projection.total_pago_cuenta,
            total_income=projection.total_income,
            total_expenses=projection.total_expenses,
            period=projection.period,
            year=projection.year,
            estimated_iva_due=projection.total_iva,
            estimated_pago_cuenta_due=projection.total_pago_cuenta,
        )
    )
