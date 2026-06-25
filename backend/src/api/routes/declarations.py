from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.auth.helpers import get_current_user
from src.api.bff.response import BFFResponse, ResponseMeta
from src.api.bff.schemas import (
    DeclarationBFF,
    DeclarationCalculateRequest,
    DeclarationCreateRequest,
)
from src.api.dependencies import (
    get_declaration_repo,
    get_employee_repo,
    get_tx_repo,
)
from src.application.use_cases.calculate_declaration import (
    CalculateDeclarationUseCase,
)
from src.application.use_cases.save_declaration import SaveDeclarationUseCase
from src.application.use_cases.submit_declaration import SubmitDeclarationUseCase
from src.application.use_cases.get_declaration import GetDeclarationUseCase
from src.application.use_cases.list_declarations import ListDeclarationsUseCase
from src.domain.exceptions import DomainError
from src.domain.models.tax_declaration import (
    TaxDeclaration,
    F07Data,
    F14Data,
    F06Data,
)
from src.domain.models.user import User

router = APIRouter(tags=["declarations"])

DOMAIN_ERROR_STATUS = {
    "DUPLICATE_PERIOD": 400,
    "NOT_FOUND": 404,
    "ALREADY_SUBMITTED": 400,
}


def _declaration_to_bff(d: TaxDeclaration) -> DeclarationBFF:
    f07 = d.f07
    f14 = d.f14
    f06 = d.f06
    return DeclarationBFF(
        declaration_id=d.declaration_id,
        user_id=d.user_id,
        form_type=d.form_type.value,
        period=d.period,
        year=d.year,
        status=d.status.value,
        total_iva=f07.total_iva if f07 else None,
        iva_debito=f07.iva_debito if f07 else None,
        iva_credito=f07.iva_credito if f07 else None,
        iva_retenido=f07.iva_retenido if f07 else None,
        ingresos_brutos=f14.ingresos_brutos if f14 else None,
        tasa_aplicada=f14.tasa_aplicada if f14 else None,
        pago_cuenta_calculado=f14.pago_cuenta_calculado if f14 else None,
        saldo_a_favor_anterior=f14.saldo_a_favor_anterior if f14 else None,
        total_remuneraciones=f06.total_remuneraciones if f06 else None,
        total_empleados=f06.total_empleados if f06 else None,
        isr_retenido=f06.isr_retenido if f06 else None,
        cotizaciones_iss=f06.cotizaciones_iss if f06 else None,
        cotizaciones_afp=f06.cotizaciones_afp if f06 else None,
        created_at=d.created_at.isoformat(),
    )


def _build_form_data(body: DeclarationCreateRequest):
    f07 = None
    f14 = None
    f06 = None
    if body.form_type == "F-07":
        f07 = F07Data(
            total_iva=body.total_iva or Decimal("0"),
            iva_debito=body.iva_debito or Decimal("0"),
            iva_credito=body.iva_credito or Decimal("0"),
            iva_retenido=body.iva_retenido or Decimal("0"),
        )
    elif body.form_type == "F-14":
        f14 = F14Data(
            ingresos_brutos=body.ingresos_brutos or Decimal("0"),
            tasa_aplicada=body.tasa_aplicada or Decimal("0"),
            pago_cuenta_calculado=body.pago_cuenta_calculado or Decimal("0"),
            saldo_a_favor_anterior=body.saldo_a_favor_anterior or Decimal("0"),
        )
    elif body.form_type == "F-06":
        f06 = F06Data(
            total_remuneraciones=body.total_remuneraciones or Decimal("0"),
            total_empleados=body.total_empleados or 0,
            isr_retenido=body.isr_retenido or Decimal("0"),
            cotizaciones_iss=body.cotizaciones_iss or Decimal("0"),
            cotizaciones_afp=body.cotizaciones_afp or Decimal("0"),
        )
    return f07, f14, f06


@router.post("/declarations/calculate")
async def calculate_declaration(
    body: DeclarationCalculateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_declaration_repo),
    tx_repo=Depends(get_tx_repo),
    emp_repo=Depends(get_employee_repo),
):
    use_case = CalculateDeclarationUseCase(tx_repo, repo, emp_repo)
    decl = await use_case.execute(
        user_id=current_user.user_id,
        form_type=body.form_type,
        year=body.year,
        period=body.period,
    )
    return BFFResponse.ok(data=_declaration_to_bff(decl))


@router.post("/declarations", status_code=201)
async def create_declaration(
    body: DeclarationCreateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_declaration_repo),
):
    use_case = SaveDeclarationUseCase(repo)
    f07, f14, f06 = _build_form_data(body)
    try:
        decl = await use_case.execute(
            user_id=current_user.user_id,
            form_type=body.form_type,
            period=body.period,
            year=body.year,
            declaration_id=body.declaration_id,
            f07=f07,
            f14=f14,
            f06=f06,
        )
    except DomainError as e:
        status = DOMAIN_ERROR_STATUS.get(e.code, 400)
        return JSONResponse(
            status_code=status,
            content=BFFResponse.error(
                code=e.code, message=e.message
            ).model_dump(),
        )
    return BFFResponse.ok(data=_declaration_to_bff(decl))


@router.get("/declarations")
async def list_declarations(
    page: int = 1,
    limit: int = 50,
    form_type: str | None = None,
    year: int | None = None,
    period: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_declaration_repo),
):
    use_case = ListDeclarationsUseCase(repo)
    decls = await use_case.execute(
        user_id=current_user.user_id,
        page=page,
        limit=limit,
        form_type=form_type,
        year=year,
        period=period,
        status=status,
    )
    items = [_declaration_to_bff(d) for d in decls]
    return BFFResponse.ok(
        data=items, meta=ResponseMeta(page=page, limit=limit, total=len(items))
    )


@router.get("/declarations/{declaration_id}")
async def get_declaration(
    declaration_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_declaration_repo),
):
    use_case = GetDeclarationUseCase(repo)
    try:
        decl = await use_case.execute(
            user_id=current_user.user_id,
            declaration_id=declaration_id,
        )
    except DomainError as e:
        return JSONResponse(
            status_code=404,
            content=BFFResponse.error(
                code=e.code, message=e.message
            ).model_dump(),
        )
    return BFFResponse.ok(data=_declaration_to_bff(decl))


@router.put("/declarations/{declaration_id}")
async def update_declaration(
    declaration_id: str,
    body: DeclarationCreateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_declaration_repo),
):
    use_case = SaveDeclarationUseCase(repo)
    f07, f14, f06 = _build_form_data(body)
    try:
        decl = await use_case.execute(
            user_id=current_user.user_id,
            form_type=body.form_type,
            period=body.period,
            year=body.year,
            declaration_id=declaration_id,
            f07=f07,
            f14=f14,
            f06=f06,
        )
    except DomainError as e:
        status = DOMAIN_ERROR_STATUS.get(e.code, 400)
        return JSONResponse(
            status_code=status,
            content=BFFResponse.error(
                code=e.code, message=e.message
            ).model_dump(),
        )
    return BFFResponse.ok(data=_declaration_to_bff(decl))


@router.post("/declarations/{declaration_id}/submit")
async def submit_declaration(
    declaration_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_declaration_repo),
):
    use_case = SubmitDeclarationUseCase(repo)
    try:
        decl = await use_case.execute(
            user_id=current_user.user_id,
            declaration_id=declaration_id,
        )
    except DomainError as e:
        status = DOMAIN_ERROR_STATUS.get(e.code, 400)
        return JSONResponse(
            status_code=status,
            content=BFFResponse.error(
                code=e.code, message=e.message
            ).model_dump(),
        )
    return BFFResponse.ok(data=_declaration_to_bff(decl))
