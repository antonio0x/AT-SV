from unittest.mock import patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app
from src.domain.interfaces.repository import (
    TransactionRepository,
    UserRepository,
)
from src.domain.models.transaction import Transaction, TransactionType
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
            tx
            for tx in self._txs.values()
            if str(tx.user_id) == user_id
        ]
        start = (page - 1) * limit
        return user_txs[start : start + limit]

    async def update(self, transaction: Transaction) -> Transaction:
        self._txs[str(transaction.transaction_id)] = transaction
        return transaction

    async def delete(self, transaction_id: str) -> bool:
        self._txs.pop(transaction_id, None)
        return True


@pytest.fixture
def app():
    application = create_app()

    from src.api.routes.users import get_user_repo
    from src.api.routes.transactions import get_tx_repo as get_tx_repo_transactions
    from src.api.routes.taxes import get_tx_repo as get_tx_repo_taxes

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
        from datetime import datetime

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
        response = await client.get(
            "/api/v1/users/nonexistent-user-id"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"] is None
        assert len(body["errors"]) == 1
        assert body["errors"][0]["code"] == "NOT_FOUND"


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


class TestAppFactory:
    def test_create_app_with_middleware(self):
        app = create_app()
        assert app.title == "AT-SV Backend"
        assert app.version == "0.1.0"
        middleware_classes = [
            m.cls.__name__ for m in app.user_middleware
        ]
        assert "CORSMiddleware" in middleware_classes

    def test_create_app_routes_registered(self):
        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/health" in routes
        assert "/api/v1/users" in routes or "/api/v1/users/{user_id}" in routes

    def test_custom_settings(self):
        with patch(
            "src.infrastructure.database.get_settings"
        ) as mock_settings:
            settings = mock_settings.return_value
            settings.cors_origins = "https://example.com"
            settings.title = "Custom App"
            settings.version = "2.0.0"

            app = create_app()
            assert app.title == "AT-SV Backend"
