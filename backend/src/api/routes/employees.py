from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.auth.helpers import get_current_user
from src.api.bff.response import BFFResponse
from src.api.bff.schemas import (
    EmployeeBFF,
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
)
from src.api.dependencies import get_employee_repo
from src.domain.exceptions import DomainError
from src.domain.models.employee import Employee
from src.domain.models.user import User

router = APIRouter(tags=["employees"])

DOMAIN_ERROR_STATUS = {
    "NOT_FOUND": 404,
}


def _employee_to_bff(e: Employee) -> EmployeeBFF:
    return EmployeeBFF(
        employee_id=e.employee_id,
        user_id=e.user_id,
        nombre=e.nombre,
        salario=e.salario,
        isr_rate=e.isr_rate,
        iss_deduction=e.iss_deduction,
        afp_deduction=e.afp_deduction,
        created_at=e.created_at.isoformat(),
    )


@router.post("/employees", status_code=201)
async def create_employee(
    body: EmployeeCreateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_employee_repo),
):
    emp = Employee(
        user_id=current_user.user_id,
        nombre=body.nombre,
        salario=body.salario,
        isr_rate=body.isr_rate or Decimal("0.10"),
        iss_deduction=body.iss_deduction or Decimal("0.03"),
        afp_deduction=body.afp_deduction or Decimal("0.0725"),
    )
    created = await repo.create(emp)
    return BFFResponse.ok(data=_employee_to_bff(created))


@router.get("/employees")
async def list_employees(
    current_user: User = Depends(get_current_user),
    repo=Depends(get_employee_repo),
):
    employees = await repo.get_by_user_id(current_user.user_id)
    items = [_employee_to_bff(e) for e in employees]
    return BFFResponse.ok(data=items)


@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_employee_repo),
):
    emp = await repo.get_by_id(employee_id)
    if not emp or emp.user_id != current_user.user_id:
        return JSONResponse(
            status_code=404,
            content=BFFResponse.error(
                code="NOT_FOUND", message="Employee not found"
            ).model_dump(),
        )
    return BFFResponse.ok(data=_employee_to_bff(emp))


@router.put("/employees/{employee_id}")
async def update_employee(
    employee_id: str,
    body: EmployeeUpdateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_employee_repo),
):
    emp = await repo.get_by_id(employee_id)
    if not emp or emp.user_id != current_user.user_id:
        return JSONResponse(
            status_code=404,
            content=BFFResponse.error(
                code="NOT_FOUND", message="Employee not found"
            ).model_dump(),
        )
    updates = {}
    if body.nombre is not None:
        updates["nombre"] = body.nombre
    if body.salario is not None:
        updates["salario"] = body.salario
    if body.isr_rate is not None:
        updates["isr_rate"] = body.isr_rate
    if body.iss_deduction is not None:
        updates["iss_deduction"] = body.iss_deduction
    if body.afp_deduction is not None:
        updates["afp_deduction"] = body.afp_deduction
    updated = emp.model_copy(update=updates)
    result = await repo.update(updated)
    return BFFResponse.ok(data=_employee_to_bff(result))


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_employee_repo),
):
    emp = await repo.get_by_id(employee_id)
    if not emp or emp.user_id != current_user.user_id:
        return JSONResponse(
            status_code=404,
            content=BFFResponse.error(
                code="NOT_FOUND", message="Employee not found"
            ).model_dump(),
        )
    await repo.delete(employee_id)
    return BFFResponse.ok(data=None)
