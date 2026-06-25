from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app
from src.domain.interfaces.repository import (
    EmployeeRepository,
    UserRepository,
)
from src.domain.models.employee import Employee
from src.domain.models.user import User


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
    "email": "emptest@example.com",
    "password": "securePass123",
    "business_name": "Emp Test S.A. de C.V.",
    "business_type": "persona_juridica",
    "nit": "1234-567890-123-4",
    "nrc": "123456-7",
    "regimen_fiscal": "general",
}


@pytest.fixture
def app():
    application = create_app()

    from src.api.dependencies import get_user_repo, get_employee_repo

    user_repo = FakeUserRepo()
    emp_repo = FakeEmployeeRepo()

    application.dependency_overrides[get_user_repo] = lambda: user_repo
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


class TestCreateEmployee:
    @pytest.mark.asyncio
    async def test_create_employee_success(self, authed_client):
        resp = await authed_client.post(
            "/api/v1/employees",
            json={
                "nombre": "Juan Perez",
                "salario": "1500.00",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["nombre"] == "Juan Perez"
        assert data["salario"] == "1500.00"
        assert data["isr_rate"] == "0.10"
        assert data["employee_id"] is not None
        assert data["user_id"] is not None

    @pytest.mark.asyncio
    async def test_create_employee_with_custom_rates(self, authed_client):
        resp = await authed_client.post(
            "/api/v1/employees",
            json={
                "nombre": "Maria Lopez",
                "salario": "2000.00",
                "isr_rate": "0.15",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["isr_rate"] == "0.15"

    @pytest.mark.asyncio
    async def test_create_employee_returns_401_without_auth(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as fresh:
            resp = await fresh.post(
                "/api/v1/employees",
                json={"nombre": "X", "salario": "1000"},
            )
        assert resp.status_code == 401


class TestGetEmployee:
    @pytest.mark.asyncio
    async def test_get_employee_success(self, authed_client):
        create_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Ana", "salario": "1200.00"},
        )
        emp_id = create_resp.json()["data"]["employee_id"]

        resp = await authed_client.get(f"/api/v1/employees/{emp_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["employee_id"] == emp_id
        assert data["nombre"] == "Ana"

    @pytest.mark.asyncio
    async def test_get_employee_not_found(self, authed_client):
        resp = await authed_client.get(
            "/api/v1/employees/nonexistent-id"
        )
        assert resp.status_code == 404


class TestListEmployees:
    @pytest.mark.asyncio
    async def test_list_employees(self, authed_client):
        for name in ["A", "B", "C"]:
            await authed_client.post(
                "/api/v1/employees",
                json={"nombre": name, "salario": "1000.00"},
            )

        resp = await authed_client.get("/api/v1/employees")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 3


class TestUpdateEmployee:
    @pytest.mark.asyncio
    async def test_update_employee_success(self, authed_client):
        create_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Carlos", "salario": "1000.00"},
        )
        emp_id = create_resp.json()["data"]["employee_id"]

        resp = await authed_client.put(
            f"/api/v1/employees/{emp_id}",
            json={"nombre": "Carlos Updated", "salario": "1500.00"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["nombre"] == "Carlos Updated"
        assert data["salario"] == "1500.00"

    @pytest.mark.asyncio
    async def test_update_employee_partial(self, authed_client):
        create_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Diana", "salario": "1000.00"},
        )
        emp_id = create_resp.json()["data"]["employee_id"]

        resp = await authed_client.put(
            f"/api/v1/employees/{emp_id}",
            json={"isr_rate": "0.12"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["nombre"] == "Diana"
        assert data["isr_rate"] == "0.12"

    @pytest.mark.asyncio
    async def test_update_employee_not_owned_returns_404(
        self, authed_client, app
    ):
        create_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Elena", "salario": "1000.00"},
        )
        emp_id = create_resp.json()["data"]["employee_id"]

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
            resp = await other_client.put(
                f"/api/v1/employees/{emp_id}",
                json={"nombre": "Hacker"},
            )
        assert resp.status_code == 404


class TestDeleteEmployee:
    @pytest.mark.asyncio
    async def test_delete_employee_success(self, authed_client):
        create_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Delete Me", "salario": "1000.00"},
        )
        emp_id = create_resp.json()["data"]["employee_id"]

        resp = await authed_client.delete(
            f"/api/v1/employees/{emp_id}"
        )
        assert resp.status_code == 200

        get_resp = await authed_client.get(
            f"/api/v1/employees/{emp_id}"
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_employee_not_owned_returns_404(
        self, authed_client, app
    ):
        create_resp = await authed_client.post(
            "/api/v1/employees",
            json={"nombre": "Mine", "salario": "1000.00"},
        )
        emp_id = create_resp.json()["data"]["employee_id"]

        other_register = {
            **REGISTER_BODY,
            "email": "other2@example.com",
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as other_client:
            await other_client.post(
                "/api/v1/auth/register", json=other_register
            )
            resp = await other_client.delete(
                f"/api/v1/employees/{emp_id}"
            )
        assert resp.status_code == 404
