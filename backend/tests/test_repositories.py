from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from moto import mock_aws

from src.infrastructure.database import get_settings
from src.infrastructure.repositories.user_repo import DynamoDBUserRepository
from src.infrastructure.repositories.transaction_repo import DynamoDBTransactionRepository
from src.domain.models.user import User
from src.domain.models.transaction import Transaction, TransactionType


SETTINGS = get_settings()


@pytest.fixture(autouse=True)
def dynamo_mock():
    with mock_aws():
        from src.infrastructure.database import get_dynamodb_resource

        client = get_dynamodb_resource().meta.client

        client.create_table(
            TableName=SETTINGS.users_table,
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
            TableName=SETTINGS.transactions_table,
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


class TestDynamoDBUserRepository:
    @pytest.fixture
    def repo(self):
        return DynamoDBUserRepository()

    @pytest.fixture
    def sample_user(self) -> User:
        return User(
            user_id=str(uuid4()),
            email="test@example.com",
            business_name="Test S.A. de C.V.",
            business_type="persona_juridica",
            nit="1234-567890-123-4",
            nrc="123456-7",
            regimen_fiscal="general",
            created_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_create_user(self, repo, sample_user):
        result = await repo.create(sample_user)
        assert result == sample_user

        stored = await repo.get_by_id(str(sample_user.user_id))
        assert stored is not None
        assert stored.email == sample_user.email

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self, repo):
        result = await repo.get_by_id("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, repo, sample_user):
        await repo.create(sample_user)

        result = await repo.get_by_email("test@example.com")
        assert result is not None
        assert result.user_id == sample_user.user_id

    @pytest.mark.asyncio
    async def test_get_by_email_returns_none_for_missing(self, repo):
        result = await repo.get_by_email("missing@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_user(self, repo, sample_user):
        await repo.create(sample_user)

        updated_user = sample_user.model_copy(update={"business_name": "Updated S.A."})
        result = await repo.update(updated_user)
        assert result.business_name == "Updated S.A."

        stored = await repo.get_by_id(str(sample_user.user_id))
        assert stored is not None
        assert stored.business_name == "Updated S.A."

    @pytest.mark.asyncio
    async def test_delete_user(self, repo, sample_user):
        await repo.create(sample_user)
        result = await repo.delete(str(sample_user.user_id))
        assert result is True

        stored = await repo.get_by_id(str(sample_user.user_id))
        assert stored is None


class TestDynamoDBTransactionRepository:
    @pytest.fixture
    def repo(self):
        return DynamoDBTransactionRepository()

    @pytest.fixture
    def sample_transaction(self) -> Transaction:
        return Transaction(
            transaction_id=str(uuid4()),
            user_id=str(uuid4()),
            type=TransactionType.INCOME,
            amount=Decimal("150.00"),
            category="ventas",
            description="Venta de productos",
            date=date.today(),
            iva_rate=Decimal("0.13"),
            created_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_create_transaction(self, repo, sample_transaction):
        result = await repo.create(sample_transaction)
        assert result == sample_transaction

        stored = await repo.get_by_id(str(sample_transaction.transaction_id))
        assert stored is not None
        assert stored.amount == sample_transaction.amount

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self, repo):
        result = await repo.get_by_id("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, repo, sample_transaction):
        await repo.create(sample_transaction)

        results = await repo.get_by_user_id(str(sample_transaction.user_id))
        assert len(results) == 1
        assert results[0].transaction_id == sample_transaction.transaction_id

    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_empty_for_missing(self, repo):
        results = await repo.get_by_user_id(str(uuid4()))
        assert results == []

    @pytest.mark.asyncio
    async def test_update_transaction(self, repo, sample_transaction):
        await repo.create(sample_transaction)

        updated = sample_transaction.model_copy(update={"description": "Updated description"})
        result = await repo.update(updated)
        assert result.description == "Updated description"

        stored = await repo.get_by_id(str(sample_transaction.transaction_id))
        assert stored is not None
        assert stored.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_transaction(self, repo, sample_transaction):
        await repo.create(sample_transaction)
        result = await repo.delete(str(sample_transaction.transaction_id))
        assert result is True

        stored = await repo.get_by_id(str(sample_transaction.transaction_id))
        assert stored is None
