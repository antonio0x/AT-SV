from src.domain.interfaces.repository import (
    DeclarationRepository,
    EmployeeRepository,
)
from src.domain.models.tax_declaration import TaxDeclaration
from src.domain.models.employee import Employee


class InMemoryDeclarationRepository(DeclarationRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaxDeclaration] = {}

    async def create(self, declaration: TaxDeclaration) -> TaxDeclaration:
        existing = await self.get_by_period(
            declaration.user_id,
            declaration.form_type.value,
            declaration.year,
            declaration.period,
        )
        if existing:
            raise ValueError(
                f"Declaration already exists for period {declaration.period}/{declaration.year} form {declaration.form_type.value}"
            )
        self._store[declaration.declaration_id] = declaration
        return declaration

    async def get_by_id(self, declaration_id: str) -> TaxDeclaration | None:
        return self._store.get(declaration_id)

    async def get_by_user_id(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> list[TaxDeclaration]:
        all_decls = [
            d for d in self._store.values() if d.user_id == user_id
        ]
        all_decls.sort(key=lambda d: d.created_at, reverse=True)
        start = (page - 1) * limit
        return all_decls[start : start + limit]

    async def get_by_period(
        self, user_id: str, form_type: str, year: int, period: str
    ) -> TaxDeclaration | None:
        for d in self._store.values():
            if (
                d.user_id == user_id
                and d.form_type.value == form_type
                and d.year == year
                and d.period == period
            ):
                return d
        return None

    async def update(self, declaration: TaxDeclaration) -> TaxDeclaration:
        self._store[declaration.declaration_id] = declaration
        return declaration

    async def delete(self, declaration_id: str) -> None:
        self._store.pop(declaration_id, None)


class InMemoryEmployeeRepository(EmployeeRepository):
    def __init__(self) -> None:
        self._store: dict[str, Employee] = {}

    async def create(self, employee: Employee) -> Employee:
        self._store[employee.employee_id] = employee
        return employee

    async def get_by_id(self, employee_id: str) -> Employee | None:
        return self._store.get(employee_id)

    async def get_by_user_id(self, user_id: str) -> list[Employee]:
        return [
            e for e in self._store.values() if e.user_id == user_id
        ]

    async def update(self, employee: Employee) -> Employee:
        self._store[employee.employee_id] = employee
        return employee

    async def delete(self, employee_id: str) -> None:
        self._store.pop(employee_id, None)
