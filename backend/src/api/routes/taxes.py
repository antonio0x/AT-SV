from fastapi import APIRouter, Depends

from src.api.auth.helpers import get_current_user
from src.api.bff.response import BFFResponse
from src.api.bff.schemas import TaxProjectionBFF
from src.api.dependencies import get_tx_repo
from src.application.use_cases.get_tax_projection import (
    GetTaxProjectionUseCase,
)
from src.domain.models.user import User

router = APIRouter(tags=["taxes"])


@router.get("/taxes/projection", response_model=BFFResponse[TaxProjectionBFF])
async def tax_projection(
    year: int,
    period: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_tx_repo),
):
    use_case = GetTaxProjectionUseCase(repo)
    projection = await use_case.execute(
        user_id=current_user.user_id, year=year, period=period
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
