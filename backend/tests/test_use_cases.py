from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.use_cases.get_tax_projection import (
    GetTaxProjectionUseCase,
    TaxProjection,
)
from src.application.use_cases.record_transaction import RecordTransactionUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.interfaces.repository import (
    TransactionRepository,
    UserRepository,
)
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.user import User
from src.domain.services.tax_engine import calculate_iva


class TestRegisterUserUseCase:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock(spec=UserRepository)
        repo.create = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_register_user_creates_and_returns_user(self, mock_repo):
        use_case = RegisterUserUseCase(mock_repo)
        expected_user = User(
            email="test@example.com",
            business_name="Test S.A.",
            business_type="persona_juridica",
            nit="1234-567890-123-4",
            regimen_fiscal="general",
        )
        mock_repo.create.return_value = expected_user

        result = await use_case.execute(
            email="test@example.com",
            business_name="Test S.A.",
            business_type="persona_juridica",
            nit="1234-567890-123-4",
            regimen_fiscal="general",
        )

        assert result.email == "test@example.com"
        assert result.business_name == "Test S.A."
        mock_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_user_with_nrc(self, mock_repo):
        use_case = RegisterUserUseCase(mock_repo)
        expected_user = User(
            email="nrc@example.com",
            business_name="NRC Test",
            business_type="persona_natural",
            nit="1234-567890-123-4",
            nrc="123456-78",
            regimen_fiscal="simplificado",
        )
        mock_repo.create.return_value = expected_user

        result = await use_case.execute(
            email="nrc@example.com",
            business_name="NRC Test",
            business_type="persona_natural",
            nit="1234-567890-123-4",
            nrc="123456-78",
            regimen_fiscal="simplificado",
        )

        assert result.nrc == "123456-78"

    @pytest.mark.asyncio
    async def test_register_user_passes_correct_args_to_repo(self, mock_repo):
        use_case = RegisterUserUseCase(mock_repo)

        await use_case.execute(
            email="exact@example.com",
            business_name="Exact Match",
            business_type="persona_natural",
            nit="5678-123456-789-1",
        )

        mock_repo.create.assert_awaited_once()
        created_user = mock_repo.create.await_args.args[0]
        assert created_user.email == "exact@example.com"
        assert created_user.business_name == "Exact Match"


class TestRecordTransactionUseCase:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock(spec=TransactionRepository)
        repo.create = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_record_transaction_income_creates_and_returns(self, mock_repo):
        use_case = RecordTransactionUseCase(mock_repo)
        user_id = str(uuid4())
        expected_tx = Transaction(
            user_id=user_id,
            type=TransactionType.INCOME,
            amount=Decimal("250.00"),
            category="ventas",
            description="Product sale",
            date=date.today(),
        )
        mock_repo.create.return_value = expected_tx

        result = await use_case.execute(
            user_id=user_id,
            type=TransactionType.INCOME,
            amount=Decimal("250.00"),
            category="ventas",
            description="Product sale",
        )

        assert result.type == TransactionType.INCOME
        assert result.amount == Decimal("250.00")
        mock_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_record_transaction_expense_creates_and_returns(self, mock_repo):
        use_case = RecordTransactionUseCase(mock_repo)
        user_id = str(uuid4())
        expected_tx = Transaction(
            user_id=user_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            category="servicios",
            description="Office supplies",
            date=date.today(),
        )
        mock_repo.create.return_value = expected_tx

        result = await use_case.execute(
            user_id=user_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            category="servicios",
            description="Office supplies",
        )

        assert result.type == TransactionType.EXPENSE
        assert result.amount == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_record_transaction_with_custom_iva_rate(self, mock_repo):
        use_case = RecordTransactionUseCase(mock_repo)
        user_id = str(uuid4())

        await use_case.execute(
            user_id=user_id,
            type=TransactionType.INCOME,
            amount=Decimal("200.00"),
            category="ventas",
            iva_rate=Decimal("0.10"),
        )

        created_tx = mock_repo.create.await_args.args[0]
        assert created_tx.iva_rate == Decimal("0.10")

    @pytest.mark.asyncio
    async def test_record_transaction_passes_correct_args_to_repo(self, mock_repo):
        use_case = RecordTransactionUseCase(mock_repo)
        user_id = str(uuid4())
        tx_date = date(2025, 6, 1)

        await use_case.execute(
            user_id=user_id,
            type=TransactionType.INCOME,
            amount=Decimal("500.00"),
            category="ventas",
            description="June sales",
            tx_date=tx_date,
            iva_rate=Decimal("0.13"),
        )

        mock_repo.create.assert_awaited_once()
        created = mock_repo.create.await_args.args[0]
        assert created.amount == Decimal("500.00")
        assert created.category == "ventas"
        assert created.description == "June sales"
        assert created.date == tx_date


class TestGetTaxProjectionUseCase:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock(spec=TransactionRepository)
        repo.get_by_user_id = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_returns_projection_with_income_and_expenses(self, mock_repo):
        user_id = str(uuid4())
        mock_repo.get_by_user_id.return_value = [
            Transaction(
                user_id=user_id,
                type=TransactionType.INCOME,
                amount=Decimal("1000.00"),
                category="ventas",
                date=date(2025, 1, 15),
            ),
            Transaction(
                user_id=user_id,
                type=TransactionType.EXPENSE,
                amount=Decimal("300.00"),
                category="servicios",
                date=date(2025, 1, 20),
            ),
        ]

        use_case = GetTaxProjectionUseCase(mock_repo)
        result = await use_case.execute(user_id=user_id, year=2025, period="monthly")

        assert isinstance(result, TaxProjection)
        assert result.total_income == Decimal("1000.00")
        assert result.total_expenses == Decimal("300.00")

    @pytest.mark.asyncio
    async def test_returns_projection_with_correct_iva(self, mock_repo):
        user_id = str(uuid4())
        mock_repo.get_by_user_id.return_value = [
            Transaction(
                user_id=user_id,
                type=TransactionType.INCOME,
                amount=Decimal("1000.00"),
                category="ventas",
                date=date(2025, 1, 15),
            ),
        ]

        use_case = GetTaxProjectionUseCase(mock_repo)
        result = await use_case.execute(user_id=user_id, year=2025, period="monthly")

        expected_iva = calculate_iva(Decimal("1000.00"))
        assert result.total_iva == expected_iva

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_transactions(self, mock_repo):
        user_id = str(uuid4())
        mock_repo.get_by_user_id.return_value = []

        use_case = GetTaxProjectionUseCase(mock_repo)
        result = await use_case.execute(user_id=user_id, year=2025, period="monthly")

        assert result.total_income == Decimal("0")
        assert result.total_expenses == Decimal("0")
        assert result.total_iva == Decimal("0.00")
        assert result.total_pago_cuenta == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_correct_period_and_year_in_output(self, mock_repo):
        user_id = str(uuid4())
        mock_repo.get_by_user_id.return_value = []

        use_case = GetTaxProjectionUseCase(mock_repo)
        result = await use_case.execute(user_id=user_id, year=2025, period="01")

        assert result.period == "01"
        assert result.year == 2025
