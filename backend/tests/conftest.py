from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

from src.domain.interfaces.repository import (
    TransactionRepository,
    UserRepository,
)
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.user import User
from src.domain.services.tax_engine import IVA_RATE


@pytest.fixture
def decimal_amounts() -> list[Decimal]:
    return [Decimal("100"), Decimal("0"), Decimal("1"), Decimal("0.001")]


# ─── Integration Test Fixtures ─────────────────────────────────


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
def fake_user_repo():
    return FakeUserRepo()


@pytest.fixture
def fake_tx_repo():
    return FakeTxRepo()


@pytest.fixture
def sample_user() -> User:
    return User(
        user_id=uuid4(),
        email="seed@example.com",
        business_name="Seed User S.A.",
        business_type="persona_juridica",
        nit="1234-567890-123-4",
        regimen_fiscal="general",
    )


@pytest.fixture
def sample_transaction(sample_user) -> Transaction:
    return Transaction(
        user_id=sample_user.user_id,
        type=TransactionType.INCOME,
        amount=Decimal("500.00"),
        category="ventas",
        description="Seed transaction",
        date=date.today(),
        iva_rate=IVA_RATE,
    )


@pytest.fixture
def app_with_fake_repos(fake_user_repo, fake_tx_repo):
    from src.api.main import create_app

    application = create_app()
    from src.api.routes.users import get_user_repo
    from src.api.routes.transactions import get_tx_repo as get_tx_repo_transactions
    from src.api.routes.taxes import get_tx_repo as get_tx_repo_taxes

    application.dependency_overrides[get_user_repo] = lambda: fake_user_repo
    application.dependency_overrides[get_tx_repo_transactions] = lambda: fake_tx_repo
    application.dependency_overrides[get_tx_repo_taxes] = lambda: fake_tx_repo
    return application


@pytest_asyncio.fixture
async def async_client(app_with_fake_repos):
    transport = ASGITransport(app=app_with_fake_repos)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── DynamoDB Mock Fixtures ────────────────────────────────────


@pytest.fixture(autouse=False)
def dynamo_mock():
    with mock_aws():
        from src.infrastructure.database import get_dynamodb_resource, get_settings

        settings = get_settings()
        client = get_dynamodb_resource().meta.client

        client.create_table(
            TableName=settings.users_table,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "email_index",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        client.create_table(
            TableName=settings.transactions_table,
            KeySchema=[{"AttributeName": "transaction_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "transaction_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user_transactions",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield
