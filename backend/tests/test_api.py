from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.user import User
from src.domain.services.tax_engine import IVA_RATE


@pytest.fixture
def app():
    application = create_app()

    from src.api.routes.users import get_user_repo
    from src.api.routes.transactions import get_tx_repo as get_tx_repo_transactions
    from src.api.routes.taxes import get_tx_repo as get_tx_repo_taxes
    from tests.conftest import FakeTxRepo, FakeUserRepo

    user_repo = FakeUserRepo()
    tx_repo = FakeTxRepo()
    application.dependency_overrides[get_user_repo] = lambda: user_repo
    application.dependency_overrides[get_tx_repo_transactions] = lambda: tx_repo
    application.dependency_overrides[get_tx_repo_taxes] = lambda: tx_repo

    return application


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def client_with_user(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/users",
            params={
                "email": "exist@example.com",
                "business_name": "Existing S.A.",
                "business_type": "persona_juridica",
                "nit": "1234-567890-123-4",
                "regimen_fiscal": "general",
            },
        )
        user_id = resp.json()["data"]["user_id"]
        yield ac, user_id


@pytest_asyncio.fixture
async def client_with_tx(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/users",
            params={
                "email": "withtx@example.com",
                "business_name": "With Tx S.A.",
                "business_type": "persona_natural",
                "nit": "5678-123456-789-1",
                "regimen_fiscal": "simplificado",
            },
        )
        user_id = resp.json()["data"]["user_id"]

        for amount in [1000.00, 1000.00]:
            await ac.post(
                "/api/v1/transactions",
                params={
                    "user_id": user_id,
                    "type": "income",
                    "amount": amount,
                    "category": "ventas",
                },
            )
        await ac.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "expense",
                "amount": 500.00,
                "category": "servicios",
            },
        )
        yield ac, user_id


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_shape(self, client):
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_timestamp_is_iso(self, client):
        response = await client.get("/health")
        data = response.json()
        datetime.fromisoformat(data["timestamp"])


class TestUsersAPI:
    @pytest.mark.asyncio
    async def test_create_user(self, client):
        response = await client.post(
            "/api/v1/users",
            params={
                "email": "user@example.com",
                "business_name": "Test S.A. de C.V.",
                "business_type": "persona_juridica",
                "nit": "1234-567890-123-4",
                "nrc": "123456-7",
                "regimen_fiscal": "general",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["errors"] == []
        assert body["data"]["email"] == "user@example.com"
        assert body["data"]["business_name"] == "Test S.A. de C.V."
        assert body["data"]["business_type"] == "persona_juridica"
        assert body["data"]["regimen_fiscal"] == "general"
        assert "user_id" in body["data"]

    @pytest.mark.asyncio
    async def test_create_user_with_default_regimen(self, client):
        response = await client.post(
            "/api/v1/users",
            params={
                "email": "user2@example.com",
                "business_name": "Default S.A.",
                "business_type": "persona_natural",
                "nit": "5678-123456-789-1",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["regimen_fiscal"] == "simplificado"

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client):
        create_resp = await client.post(
            "/api/v1/users",
            params={
                "email": "get@example.com",
                "business_name": "Get Test S.A.",
                "business_type": "persona_juridica",
                "nit": "1111-222333-444-5",
            },
        )
        user_id = create_resp.json()["data"]["user_id"]

        response = await client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["email"] == "get@example.com"
        assert body["data"]["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client):
        response = await client.get("/api/v1/users/nonexistent-user-id")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] is None
        assert len(body["errors"]) == 1
        assert body["errors"][0]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_full_user_registration_flow(self, client):
        resp = await client.post(
            "/api/v1/users",
            params={
                "email": "fullflow@example.com",
                "business_name": "Full Flow S.A.",
                "business_type": "persona_juridica",
                "nit": "9999-888888-777-6",
                "nrc": "123456-78",
                "regimen_fiscal": "general",
            },
        )
        assert resp.status_code == 200
        user_id = resp.json()["data"]["user_id"]
        assert user_id is not None

        get_resp = await client.get(f"/api/v1/users/{user_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()["data"]
        assert data["email"] == "fullflow@example.com"
        assert data["user_id"] == user_id
        assert data["regimen_fiscal"] == "general"

    @pytest.mark.asyncio
    async def test_missing_user_returns_proper_error(self, client):
        response = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] is None
        assert any(e["code"] == "NOT_FOUND" for e in body["errors"])


class TestTransactionsAPI:
    @pytest.mark.asyncio
    async def test_create_transaction(self, client):
        user_id = str(uuid4())
        response = await client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "income",
                "amount": 250.00,
                "category": "ventas",
                "description": "Product sale",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["errors"] == []
        assert body["data"]["type"] == "income"
        assert body["data"]["amount"] == "250.0"
        assert body["data"]["category"] == "ventas"
        assert body["data"]["description"] == "Product sale"
        assert "transaction_id" in body["data"]
        assert "date" in body["data"]

    @pytest.mark.asyncio
    async def test_create_expense_transaction(self, client):
        user_id = str(uuid4())
        response = await client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "expense",
                "amount": 100.00,
                "category": "servicios",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["type"] == "expense"
        assert body["data"]["amount"] == "100.0"

    @pytest.mark.asyncio
    async def test_list_transactions(self, client):
        user_id = str(uuid4())
        for i in range(3):
            await client.post(
                "/api/v1/transactions",
                params={
                    "user_id": user_id,
                    "type": "income",
                    "amount": 100.0 * (i + 1),
                    "category": "ventas",
                },
            )

        response = await client.get(
            "/api/v1/transactions",
            params={"user_id": user_id},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 3
        assert body["meta"]["page"] == 1
        assert body["meta"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_list_transactions_pagination(self, client):
        user_id = str(uuid4())
        for i in range(5):
            await client.post(
                "/api/v1/transactions",
                params={
                    "user_id": user_id,
                    "type": "income",
                    "amount": 100.0,
                    "category": "ventas",
                },
            )

        response = await client.get(
            "/api/v1/transactions",
            params={"user_id": user_id, "page": 1, "limit": 2},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2

    @pytest.mark.asyncio
    async def test_transaction_after_user_exists(self, client_with_user):
        ac, user_id = client_with_user
        resp = await ac.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "income",
                "amount": 750.00,
                "category": "ventas",
                "description": "Post-registration sale",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["type"] == "income"
        assert body["data"]["amount"] == "750.0"
        assert body["data"]["category"] == "ventas"


class TestTaxesAPI:
    @pytest.mark.asyncio
    async def test_tax_projection(self, client):
        user_id = str(uuid4())
        await client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "income",
                "amount": 1000.00,
                "category": "ventas",
            },
        )
        await client.post(
            "/api/v1/transactions",
            params={
                "user_id": user_id,
                "type": "expense",
                "amount": 300.00,
                "category": "servicios",
            },
        )

        response = await client.get(
            "/api/v1/taxes/projection",
            params={"user_id": user_id, "year": 2025, "period": "monthly"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["errors"] == []
        data = body["data"]
        assert data["total_income"] == "1000.0"
        assert data["total_expenses"] == "300.0"
        assert data["total_iva"] == "130.00"
        assert data["total_pago_cuenta"] == "10.00"
        assert data["period"] == "monthly"
        assert data["year"] == 2025
        assert data["estimated_iva_due"] == "130.00"
        assert data["estimated_pago_cuenta_due"] == "10.00"

    @pytest.mark.asyncio
    async def test_tax_projection_no_transactions(self, client):
        user_id = str(uuid4())
        response = await client.get(
            "/api/v1/taxes/projection",
            params={"user_id": user_id, "year": 2025, "period": "yearly"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_income"] == "0"
        assert data["total_expenses"] == "0"
        assert data["total_iva"] == "0.00"

    @pytest.mark.asyncio
    async def test_tax_projection_with_known_transactions(self, client_with_tx):
        ac, user_id = client_with_tx
        resp = await ac.get(
            "/api/v1/taxes/projection",
            params={"user_id": user_id, "year": date.today().year, "period": "monthly"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert Decimal(data["total_income"]) == Decimal("2000.00")
        assert Decimal(data["total_expenses"]) == Decimal("500.00")
        iva_on_income = (Decimal("2000.00") * IVA_RATE).quantize(Decimal("0.01"))
        assert Decimal(data["total_iva"]) == iva_on_income


class TestAppFactory:
    def test_create_app_with_middleware(self):
        app = create_app()
        assert app.title == "AT-SV Backend"
        assert app.version == "0.1.0"
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_create_app_routes_registered(self):
        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/health" in routes
        assert "/api/v1/users" in routes or "/api/v1/users/{user_id}" in routes

    @pytest.mark.asyncio
    async def test_cors_headers_present_in_response(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/health",
                headers={"Origin": "http://localhost:5173"},
            )
            assert "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_cors_headers_on_api_endpoints(self, client):
        resp = await client.options(
            "/api/v1/users",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" in resp.headers
