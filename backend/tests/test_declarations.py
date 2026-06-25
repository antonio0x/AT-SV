from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app
from src.domain.interfaces.repository import (
    DeclarationRepository,
    EmployeeRepository,
    TransactionRepository,
    UserRepository,
)
from src.domain.models.employee import Employee
from src.domain.models.tax_declaration import (
    TaxDeclaration,
    FormType,
    DeclarationStatus,
    F07Data,
    F14Data,
    F06Data,
)
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.user import User
from src.domain.services.tax_engine import (
    calculate_f07,
    calculate_f14,
    calculate_f06,
    IVA_RATE,
)


class FakeUserRepo(UserRepository):
    def __init__(self):
        self._users: dict[str, User] = {}

    async def create(self, user: User) -> User:
        self._users[str(user.user_id)] = user
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        for u in self._users.values():
            if u.email == email:
                return u
        return None

    async def update(self, user: User) -> User:
        self._users[str(user.user_id)] = user
        return user

    async def delete(self, user_id: str) -> bool:
        self._users.pop(user_id, None)
        return True


class FakeTxRepo(TransactionRepository):
    def __init__(self):
        self._txs: dict[str, Transaction] = {}

    async def create(self, transaction: Transaction) -> Transaction:
        self._txs[str(transaction.transaction_id)] = transaction
        return transaction

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        return self._txs.get(transaction_id)

    async def get_by_user_id(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> list[Transaction]:
        user_txs = [
            tx for tx in self._txs.values() if str(tx.user_id) == user_id
        ]
        start = (page - 1) * limit
        return user_txs[start : start + limit]

    async def update(self, transaction: Transaction) -> Transaction:
        self._txs[str(transaction.transaction_id)] = transaction
        return transaction

    async def delete(self, transaction_id: str) -> bool:
        self._txs.pop(transaction_id, None)
        return True


class FakeDeclarationRepo(DeclarationRepository):
    def __init__(self):
        self._store: dict[str, TaxDeclaration] = {}

    async def create(self, declaration: TaxDeclaration) -> TaxDeclaration:
        existing = await self.get_by_period(
            declaration.user_id,
            declaration.form_type.value,
            declaration.year,
            declaration.period,
        )
        if existing:
            raise ValueError("period uniqueness")
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


class FakeEmployeeRepo(EmployeeRepository):
    def __init__(self):
        self._store: dict[str, Employee] = {}

    async def create(self, employee: Employee) -> Employee:
        self._store[employee.employee_id] = employee
        return employee

    async def get_by_id(self, employee_id: str) -> Employee | None:
        return self._store.get(employee_id)

    async def get_by_user_id(self, user_id: str) -> list[Employee]:
        return [e for e in self._store.values() if e.user_id == user_id]

    async def update(self, employee: Employee) -> Employee:
        self._store[employee.employee_id] = employee
        return employee

    async def delete(self, employee_id: str) -> None:
        self._store.pop(employee_id, None)


REGISTER_BODY = {
    "email": "decltest@example.com",
    "password": "securePass123",
    "business_name": "Decl Test S.A. de C.V.",
    "business_type": "persona_juridica",
    "nit": "1234-567890-123-4",
    "nrc": "123456-7",
    "regimen_fiscal": "general",
}


@pytest.fixture
def app():
    application = create_app()

    from src.api.dependencies import (
        get_user_repo,
        get_declaration_repo,
        get_employee_repo,
        get_tx_repo,
    )
    from src.api.routes.transactions import get_tx_repo as get_tx_repo_trx
    from src.api.routes.taxes import get_tx_repo as get_tx_repo_taxes

    user_repo = FakeUserRepo()
    tx_repo = FakeTxRepo()
    decl_repo = FakeDeclarationRepo()
    emp_repo = FakeEmployeeRepo()

    application.dependency_overrides[get_user_repo] = lambda: user_repo
    application.dependency_overrides[get_tx_repo] = lambda: tx_repo
    application.dependency_overrides[get_tx_repo_trx] = lambda: tx_repo
    application.dependency_overrides[get_tx_repo_taxes] = lambda: tx_repo
    application.dependency_overrides[get_declaration_repo] = lambda: decl_repo
    application.dependency_overrides[get_employee_repo] = lambda: emp_repo

    return application


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def authed_client(app, client):
    await client.post("/api/v1/auth/register", json=REGISTER_BODY)
    return client


@pytest_asyncio.fixture
async def user_id(authed_client):
    resp = await authed_client.get("/api/v1/users/me")
    return resp.json()["data"]["user_id"]


class TestCalculateDeclaration:
    @pytest.mark.asyncio
    async def test_calculate_f07_returns_iva(self, authed_client, user_id):
        from datetime import date
        today = date.today()
        period = f"{today.month:02d}"
        year = today.year

        await authed_client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "income",
                "amount": 1000,
                "category": "ventas",
            },
        )
        await authed_client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "expense",
                "amount": 300,
                "category": "servicios",
            },
        )

        resp = await authed_client.post(
            "/api/v1/declarations/calculate",
            json={"form_type": "F-07", "period": period, "year": year},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["form_type"] == "F-07"
        assert data["total_iva"] == "91.00"

    @pytest.mark.asyncio
    async def test_calculate_f14_returns_pago_cuenta(
        self, authed_client, user_id
    ):
        from datetime import date
        today = date.today()
        period = f"{today.month:02d}"
        year = today.year

        await authed_client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "income",
                "amount": 2000,
                "category": "servicios_profesionales",
            },
        )
        await authed_client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "income",
                "amount": 1000,
                "category": "ventas",
            },
        )

        resp = await authed_client.post(
            "/api/v1/declarations/calculate",
            json={"form_type": "F-14", "period": period, "year": year},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["form_type"] == "F-14"
        assert data["pago_cuenta_calculado"] is not None

    @pytest.mark.asyncio
    async def test_calculate_f06_returns_aggregation(
        self, authed_client, user_id
    ):
        emp_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Juan", "salario": "1000"},
        )
        assert emp_resp.status_code == 201

        resp = await authed_client.post(
            "/api/v1/declarations/calculate",
            json={"form_type": "F-06", "period": "06", "year": 2025},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["form_type"] == "F-06"
        assert data["total_empleados"] == 1
        assert data["total_remuneraciones"] == "1000.00"

    @pytest.mark.asyncio
    async def test_calculate_returns_401_without_auth(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            resp = await fresh.post(
                "/api/v1/declarations/calculate",
                json={"form_type": "F-07", "period": "06", "year": 2025},
            )
        assert resp.status_code == 401


class TestCreateDeclaration:
    @pytest.mark.asyncio
    async def test_create_draft_success(self, authed_client, user_id):
        resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "01",
                "year": 2025,
                "total_iva": "100.00",
                "iva_debito": "130.00",
                "iva_credito": "30.00",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["form_type"] == "F-07"
        assert data["status"] == "draft"
        assert data["total_iva"] == "100.00"
        assert data["iva_debito"] == "130.00"
        assert data["declaration_id"] is not None

    @pytest.mark.asyncio
    async def test_create_duplicate_period_returns_400(
        self, authed_client, user_id
    ):
        body = {
            "form_type": "F-07",
            "period": "03",
            "year": 2025,
            "total_iva": "50.00",
        }
        resp1 = await authed_client.post("/api/v1/declarations", json=body)
        assert resp1.status_code == 201

        resp2 = await authed_client.post("/api/v1/declarations", json=body)
        assert resp2.status_code == 400
        assert resp2.json()["errors"][0]["code"] == "DUPLICATE_PERIOD"

    @pytest.mark.asyncio
    async def test_create_returns_401_without_auth(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            resp = await fresh.post(
                "/api/v1/declarations",
                json={"form_type": "F-07", "period": "01", "year": 2025},
            )
        assert resp.status_code == 401


class TestGetDeclaration:
    @pytest.mark.asyncio
    async def test_get_declaration_success(self, authed_client, user_id):
        create_resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-14",
                "period": "02",
                "year": 2025,
                "ingresos_brutos": "5000",
                "pago_cuenta_calculado": "250.00",
            },
        )
        decl_id = create_resp.json()["data"]["declaration_id"]

        resp = await authed_client.get(
            f"/api/v1/declarations/{decl_id}"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["declaration_id"] == decl_id
        assert data["ingresos_brutos"] == "5000"

    @pytest.mark.asyncio
    async def test_get_declaration_not_found(self, authed_client):
        resp = await authed_client.get(
            "/api/v1/declarations/nonexistent-id"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_declaration_returns_401_without_auth(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            resp = await fresh.get(
                "/api/v1/declarations/some-id"
            )
        assert resp.status_code == 401


class TestListDeclarations:
    @pytest.mark.asyncio
    async def test_list_declarations(self, authed_client, user_id):
        for i in range(3):
            await authed_client.post(
                "/api/v1/declarations",
                json={
                    "form_type": "F-07",
                    "period": f"{i+4:02d}",
                    "year": 2025,
                    "total_iva": f"{i*10}.00",
                },
            )

        resp = await authed_client.get(
            "/api/v1/declarations", params={"page": 1, "limit": 10}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 3
        assert body["meta"]["total"] == 3

    @pytest.mark.asyncio
    async def test_list_with_filters(self, authed_client, user_id):
        await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "01",
                "year": 2025,
                "total_iva": "100.00",
            },
        )
        await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-14",
                "period": "01",
                "year": 2025,
                "ingresos_brutos": "5000",
            },
        )

        resp = await authed_client.get(
            "/api/v1/declarations",
            params={"form_type": "F-14"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1


class TestUpdateDeclaration:
    @pytest.mark.asyncio
    async def test_update_draft_success(self, authed_client, user_id):
        create_resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "05",
                "year": 2025,
                "total_iva": "50.00",
            },
        )
        decl_id = create_resp.json()["data"]["declaration_id"]

        resp = await authed_client.put(
            f"/api/v1/declarations/{decl_id}",
            json={
                "form_type": "F-07",
                "period": "05",
                "year": 2025,
                "total_iva": "75.00",
                "iva_debito": "100.00",
                "iva_credito": "25.00",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total_iva"] == "75.00"

    @pytest.mark.asyncio
    async def test_update_submitted_returns_400(self, authed_client, user_id):
        create_resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "07",
                "year": 2025,
                "total_iva": "50.00",
            },
        )
        decl_id = create_resp.json()["data"]["declaration_id"]
        await authed_client.post(
            f"/api/v1/declarations/{decl_id}/submit"
        )

        resp = await authed_client.put(
            f"/api/v1/declarations/{decl_id}",
            json={
                "form_type": "F-07",
                "period": "07",
                "year": 2025,
                "total_iva": "75.00",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["errors"][0]["code"] == "ALREADY_SUBMITTED"


class TestSubmitDeclaration:
    @pytest.mark.asyncio
    async def test_submit_draft_success(self, authed_client, user_id):
        create_resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "04",
                "year": 2025,
                "total_iva": "50.00",
            },
        )
        decl_id = create_resp.json()["data"]["declaration_id"]

        resp = await authed_client.post(
            f"/api/v1/declarations/{decl_id}/submit"
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_submit_submitted_returns_400(self, authed_client, user_id):
        create_resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "08",
                "year": 2025,
                "total_iva": "50.00",
            },
        )
        decl_id = create_resp.json()["data"]["declaration_id"]
        await authed_client.post(
            f"/api/v1/declarations/{decl_id}/submit"
        )

        resp = await authed_client.post(
            f"/api/v1/declarations/{decl_id}/submit"
        )
        assert resp.status_code == 400
        assert resp.json()["errors"][0]["code"] == "ALREADY_SUBMITTED"

    @pytest.mark.asyncio
    async def test_submit_not_owned_returns_404(
        self, authed_client, app, user_id
    ):
        create_resp = await authed_client.post(
            "/api/v1/declarations",
            json={
                "form_type": "F-07",
                "period": "09",
                "year": 2025,
                "total_iva": "50.00",
            },
        )
        decl_id = create_resp.json()["data"]["declaration_id"]

        other_register = {
            **REGISTER_BODY,
            "email": "other@example.com",
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as other_client:
            await other_client.post(
                "/api/v1/auth/register", json=other_register
            )
            resp = await other_client.post(
                f"/api/v1/declarations/{decl_id}/submit"
            )
        assert resp.status_code == 404


class TestTaxEngine:
    def test_calculate_f07_returns_correct_iva(self):
        income = Transaction(
            user_id="u1",
            type=TransactionType.INCOME,
            amount=Decimal("1000"),
            category="ventas",
            date=date(2025, 6, 1),
        )
        expense = Transaction(
            user_id="u1",
            type=TransactionType.EXPENSE,
            amount=Decimal("300"),
            category="servicios",
            date=date(2025, 6, 1),
        )
        result = calculate_f07([income, expense])
        assert result.iva_debito == Decimal("130.00")
        assert result.iva_credito == Decimal("39.00")
        assert result.total_iva == Decimal("91.00")

    def test_calculate_f14_without_carry_over(self):
        tx = Transaction(
            user_id="u1",
            type=TransactionType.INCOME,
            amount=Decimal("1000"),
            category="servicios_profesionales",
            date=date(2025, 6, 1),
        )
        result = calculate_f14([tx])
        assert result.ingresos_brutos == Decimal("1000.00")
        assert result.pago_cuenta_calculado == Decimal("100.00")
        assert result.saldo_a_favor_anterior == Decimal("0")

    def test_calculate_f14_with_carry_over(self):
        tx = Transaction(
            user_id="u1",
            type=TransactionType.INCOME,
            amount=Decimal("1000"),
            category="servicios_profesionales",
            date=date(2025, 6, 1),
        )
        result = calculate_f14([tx], saldo_anterior=Decimal("30.00"))
        assert result.pago_cuenta_calculado == Decimal("70.00")
        assert result.saldo_a_favor_anterior == Decimal("30.00")

    def test_calculate_f14_carry_over_does_not_go_below_zero(self):
        tx = Transaction(
            user_id="u1",
            type=TransactionType.INCOME,
            amount=Decimal("100"),
            category="servicios_profesionales",
            date=date(2025, 6, 1),
        )
        result = calculate_f14([tx], saldo_anterior=Decimal("50.00"))
        assert result.pago_cuenta_calculado == Decimal("0.00")

    def test_calculate_f06_aggregates_employees(self):
        emp1 = Employee(
            user_id="u1", nombre="A", salario=Decimal("1000")
        )
        emp2 = Employee(
            user_id="u1", nombre="B", salario=Decimal("2000")
        )
        result = calculate_f06([emp1, emp2])
        assert result.total_remuneraciones == Decimal("3000.00")
        assert result.total_empleados == 2
        assert result.isr_retenido == Decimal("300.00")
        assert result.cotizaciones_iss == Decimal("90.00")
        assert result.cotizaciones_afp == Decimal("217.50")
