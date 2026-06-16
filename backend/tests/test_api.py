from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from src.api.main import create_app
from src.domain.interfaces.repository import (
    TransactionRepository,
    UserRepository,
)
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.user import User
from src.infrastructure.database import get_settings


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


REGISTER_BODY = {
    "email": "user@example.com",
    "password": "securePass123",
    "business_name": "Test S.A. de C.V.",
    "business_type": "persona_juridica",
    "nit": "1234-567890-123-4",
    "nrc": "123456-7",
    "regimen_fiscal": "general",
}


@pytest.fixture
def app():
    application = create_app()

    from src.api.dependencies import get_user_repo
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
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_shape(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_timestamp_is_iso(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        from datetime import datetime

        datetime.fromisoformat(data["timestamp"])


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        response = await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        assert response.status_code == 201
        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert "HttpOnly" in set_cookie
        assert "access_token" in set_cookie
        body = response.json()
        assert body["errors"] == []
        assert body["data"]["email"] == "user@example.com"
        assert body["data"]["business_name"] == "Test S.A. de C.V."
        assert body["data"]["business_type"] == "persona_juridica"
        assert body["data"]["regimen_fiscal"] == "general"
        assert "user_id" in body["data"]

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        body = {**REGISTER_BODY, "password": "123"}
        response = await client.post("/api/v1/auth/register", json=body)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        assert response.status_code == 409
        body = response.json()
        assert body["errors"][0]["code"] == "EMAIL_EXISTS"

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": REGISTER_BODY["email"], "password": REGISTER_BODY["password"]},
        )
        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert "HttpOnly" in set_cookie
        assert "access_token" in set_cookie
        body = response.json()
        assert body["errors"] == []
        assert body["data"]["email"] == REGISTER_BODY["email"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": REGISTER_BODY["email"], "password": "wrongPassword1"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["errors"][0]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_email(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "somePass123"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["errors"][0]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_users_me_with_cookie(self, app, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["email"] == REGISTER_BODY["email"]
        assert body["data"]["business_name"] == REGISTER_BODY["business_name"]

    @pytest.mark.asyncio
    async def test_users_me_no_cookie(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            response = await fresh.get("/api/v1/users/me")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["errors"][0]["code"] == "UNAUTHENTICATED"

    @pytest.mark.asyncio
    async def test_logout(self, app, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None
        assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()
        assert "access_token=" in set_cookie
        me = await client.get("/api/v1/users/me")
        assert me.status_code == 401
        me_body = me.json()
        assert me_body["detail"]["errors"][0]["code"] == "UNAUTHENTICATED"

    @pytest.mark.asyncio
    async def test_old_users_endpoint_gone(self, client):
        response = await client.post("/api/v1/users")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_expired_token(self, app):
        settings = get_settings()
        expired_payload = {
            "sub": "nonexistent-id",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            fresh.cookies.set("access_token", token)
            response = await fresh.get("/api/v1/users/me")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["errors"][0]["code"] == "UNAUTHENTICATED"


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
        assert "/api/v1/health" in routes
        assert "/api/v1/users/me" in routes or "/api/v1/users/{user_id}" in routes

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
