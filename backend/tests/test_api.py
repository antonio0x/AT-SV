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

    from src.api.dependencies import get_user_repo, get_tx_repo

    user_repo = FakeUserRepo()
    tx_repo = FakeTxRepo()
    application.dependency_overrides[get_user_repo] = lambda: user_repo
    application.dependency_overrides[get_tx_repo] = lambda: tx_repo

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
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.post(
            "/api/v1/transactions",
            json={
                "type": "income",
                "amount": "250.00",
                "category": "ventas",
                "description": "Product sale",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["errors"] == []
        assert body["data"]["type"] == "income"
        from decimal import Decimal
        assert Decimal(body["data"]["amount"]) == Decimal("250")
        assert body["data"]["category"] == "ventas"
        assert body["data"]["description"] == "Product sale"
        assert "transaction_id" in body["data"]
        assert "date" in body["data"]
        assert "created_at" in body["data"]

    @pytest.mark.asyncio
    async def test_create_expense_transaction(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.post(
            "/api/v1/transactions",
            json={
                "type": "expense",
                "amount": "100.00",
                "category": "servicios",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["type"] == "expense"
        from decimal import Decimal
        assert Decimal(body["data"]["amount"]) == Decimal("100")

    @pytest.mark.asyncio
    async def test_list_transactions(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        for i in range(3):
            await client.post(
                "/api/v1/transactions",
                json={
                    "type": "income",
                    "amount": "100.0",
                    "category": "ventas",
                },
            )

        response = await client.get("/api/v1/transactions")
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 3
        assert body["meta"]["page"] == 1
        assert body["meta"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_list_transactions_pagination(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        for i in range(5):
            await client.post(
                "/api/v1/transactions",
                json={
                    "type": "income",
                    "amount": "100.0",
                    "category": "ventas",
                },
            )

        response = await client.get(
            "/api/v1/transactions",
            params={"page": 1, "limit": 2},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_transaction_by_id(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        create_resp = await client.post(
            "/api/v1/transactions",
            json={"type": "income", "amount": "100.0", "category": "ventas"},
        )
        tx_id = create_resp.json()["data"]["transaction_id"]
        response = await client.get(f"/api/v1/transactions/{tx_id}")
        assert response.status_code == 200
        assert response.json()["data"]["transaction_id"] == tx_id

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.get("/api/v1/transactions/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_transaction_not_owned(self, app, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        create_resp = await client.post(
            "/api/v1/transactions",
            json={"type": "income", "amount": "100.0", "category": "ventas"},
        )
        tx_id = create_resp.json()["data"]["transaction_id"]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client_b:
            await client_b.post(
                "/api/v1/auth/register",
                json={**REGISTER_BODY, "email": "user2@example.com"},
            )
            response = await client_b.get(f"/api/v1/transactions/{tx_id}")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_transaction(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        create_resp = await client.post(
            "/api/v1/transactions",
            json={"type": "income", "amount": "100.0", "category": "ventas"},
        )
        tx_id = create_resp.json()["data"]["transaction_id"]

        response = await client.put(
            f"/api/v1/transactions/{tx_id}",
            json={"amount": "200.0", "category": "servicios"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["amount"] == "200.0"
        assert data["category"] == "servicios"

    @pytest.mark.asyncio
    async def test_delete_transaction(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        create_resp = await client.post(
            "/api/v1/transactions",
            json={"type": "income", "amount": "100.0", "category": "ventas"},
        )
        tx_id = create_resp.json()["data"]["transaction_id"]

        response = await client.delete(f"/api/v1/transactions/{tx_id}")
        assert response.status_code == 200
        assert response.json()["data"]["message"] == "Transacción eliminada"

    @pytest.mark.asyncio
    async def test_transactions_unauthenticated(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            response = await fresh.post(
                "/api/v1/transactions",
                json={"type": "income", "amount": "100.0", "category": "ventas"},
            )
            assert response.status_code == 401
            body = response.json()
            assert body["detail"]["errors"][0]["code"] == "UNAUTHENTICATED"


class TestTaxesAPI:
    @pytest.mark.asyncio
    async def test_tax_projection_with_year_filter(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        await client.post(
            "/api/v1/transactions",
            json={
                "type": "income",
                "amount": "1000.00",
                "category": "ventas",
                "date": "2026-01-01",
            },
        )
        await client.post(
            "/api/v1/transactions",
            json={
                "type": "expense",
                "amount": "300.00",
                "category": "servicios",
                "date": "2025-01-01",
            },
        )

        response = await client.get(
            "/api/v1/taxes/projection",
            params={"year": 2026, "period": "monthly"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["errors"] == []
        data = body["data"]
        from decimal import Decimal
        assert Decimal(data["total_income"]) == Decimal("1000")
        assert Decimal(data["total_expenses"]) == Decimal("0")
        assert data["total_iva"] == "130.00"
        assert data["total_pago_cuenta"] == "10.00"
        assert data["period"] == "monthly"
        assert data["year"] == 2026
        assert data["estimated_iva_due"] == "130.00"
        assert data["estimated_pago_cuenta_due"] == "10.00"

    @pytest.mark.asyncio
    async def test_tax_projection_no_transactions(self, client):
        await client.post("/api/v1/auth/register", json=REGISTER_BODY)
        response = await client.get(
            "/api/v1/taxes/projection",
            params={"year": 2025, "period": "yearly"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_income"] == "0"
        assert data["total_expenses"] == "0"
        assert data["total_iva"] == "0.00"

    @pytest.mark.asyncio
    async def test_tax_projection_unauthenticated(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as fresh:
            response = await fresh.get(
                "/api/v1/taxes/projection",
                params={"year": 2025, "period": "yearly"},
            )
            assert response.status_code == 401
            body = response.json()
            assert body["detail"]["errors"][0]["code"] == "UNAUTHENTICATED"


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
        route_paths = set()
        for r in app.routes:
            if hasattr(r, "path"):
                route_paths.add(r.path)
            elif hasattr(r, "original_router"):
                for sr in r.original_router.routes:
                    route_paths.add(f"{r.include_context.prefix}{sr.path}")
        assert "/api/v1/health" in route_paths
        assert "/api/v1/auth/register" in route_paths

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
