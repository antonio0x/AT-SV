import re
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.domain.models.tax_declaration import (
    DeclarationStatus,
    FormType,
    TaxDeclaration,
)
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.user import User


class TestUserValidation:
    def test_valid_user_minimal(self):
        user = User(
            email="test@example.com",
            business_name="Test S.A. de C.V.",
            business_type="persona_natural",
            nit="1234-567890-123-4",
            regimen_fiscal="general",
        )
        assert user.email == "test@example.com"
        assert re.match(r"^\d{4}-\d{6}-\d{3}-\d$", user.nit)

    def test_valid_user_persona_juridica(self):
        user = User(
            email="empresa@example.com",
            business_name="Empresa S.A.",
            business_type="persona_juridica",
            nit="9876-543210-789-1",
            regimen_fiscal="general",
        )
        assert user.business_type == "persona_juridica"

    def test_valid_user_simplificado(self):
        user = User(
            email="simple@example.com",
            business_name="Simple",
            business_type="persona_natural",
            nit="4321-123456-789-5",
            regimen_fiscal="simplificado",
        )
        assert user.regimen_fiscal == "simplificado"

    def test_valid_user_with_nrc(self):
        user = User(
            email="withnrc@example.com",
            business_name="Con NRC",
            business_type="persona_natural",
            nit="1111-222222-333-4",
            nrc="123456-78",
            regimen_fiscal="general",
        )
        assert user.nrc == "123456-78"

    def test_invalid_nit_wrong_format_raises_error(self):
        with pytest.raises(ValidationError, match="nit"):
            User(
                email="test@example.com",
                business_name="Test",
                business_type="persona_natural",
                nit="1234-567890-1234",  # should be XXX-X not XXXX
                regimen_fiscal="general",
            )

    def test_invalid_nit_with_letters_raises_error(self):
        with pytest.raises(ValidationError, match="nit"):
            User(
                email="test@example.com",
                business_name="Test",
                business_type="persona_natural",
                nit="ABCD-EFGHIJ-KLM-N",
                regimen_fiscal="general",
            )

    def test_invalid_nit_too_short_raises_error(self):
        with pytest.raises(ValidationError, match="nit"):
            User(
                email="test@example.com",
                business_name="Test",
                business_type="persona_natural",
                nit="1234-567",
                regimen_fiscal="general",
            )

    def test_invalid_nit_no_hyphens_raises_error(self):
        with pytest.raises(ValidationError, match="nit"):
            User(
                email="test@example.com",
                business_name="Test",
                business_type="persona_natural",
                nit="12345678901234",
                regimen_fiscal="general",
            )

    def test_invalid_business_type_raises_error(self):
        with pytest.raises(ValidationError, match="business_type"):
            User(
                email="test@example.com",
                business_name="Test",
                business_type="cooperativa",
                nit="1234-567890-123-4",
                regimen_fiscal="general",
            )

    def test_invalid_regimen_fiscal_raises_error(self):
        with pytest.raises(ValidationError, match="regimen_fiscal"):
            User(
                email="test@example.com",
                business_name="Test",
                business_type="persona_natural",
                nit="1234-567890-123-4",
                regimen_fiscal="especial",
            )

    def test_invalid_email_raises_error(self):
        with pytest.raises(ValidationError):
            User(
                email="not-an-email",
                business_name="Test",
                business_type="persona_natural",
                nit="1234-567890-123-4",
                regimen_fiscal="general",
            )

    def test_user_auto_generates_uuid(self):
        user = User(
            email="auto@example.com",
            business_name="Auto UUID",
            business_type="persona_natural",
            nit="1234-567890-123-4",
            regimen_fiscal="general",
        )
        assert isinstance(user.user_id, UUID)

    def test_user_created_at_defaults(self):
        user = User(
            email="date@example.com",
            business_name="Date Test",
            business_type="persona_natural",
            nit="1234-567890-123-4",
            regimen_fiscal="general",
        )
        assert isinstance(user.created_at, datetime)


class TestTransactionValidation:
    def test_valid_transaction_income(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category="ventas",
            date="2025-01-15",
        )
        assert tx.type == TransactionType.INCOME
        assert tx.amount == Decimal("100.00")

    def test_valid_transaction_expense(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            category="servicios",
            description="Office rent",
            date="2025-02-01",
        )
        assert tx.type == TransactionType.EXPENSE
        assert tx.description == "Office rent"

    def test_zero_amount_raises_error(self):
        with pytest.raises(ValidationError, match="amount"):
            Transaction(
                user_id=uuid4(),
                type=TransactionType.INCOME,
                amount=Decimal("0"),
                category="ventas",
                date="2025-01-15",
            )

    def test_negative_amount_raises_error(self):
        with pytest.raises(ValidationError, match="amount"):
            Transaction(
                user_id=uuid4(),
                type=TransactionType.INCOME,
                amount=Decimal("-50.00"),
                category="ventas",
                date="2025-01-15",
            )

    def test_default_iva_rate(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category="ventas",
            date="2025-01-15",
        )
        assert tx.iva_rate == Decimal("0.13")

    def test_custom_iva_rate(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category="ventas",
            date="2025-01-15",
            iva_rate=Decimal("0.00"),
        )
        assert tx.iva_rate == Decimal("0.00")

    def test_transaction_auto_generates_uuid(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category="ventas",
            date="2025-01-15",
        )
        assert isinstance(tx.transaction_id, UUID)

    def test_transaction_created_at_defaults(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category="ventas",
            date="2025-01-15",
        )
        assert isinstance(tx.created_at, datetime)

    def test_description_optional(self):
        tx = Transaction(
            user_id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category="ventas",
            date="2025-01-15",
        )
        assert tx.description is None


class TestTaxDeclarationValidation:
    def test_valid_tax_declaration_f07(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F07,
            period="01",
            year=2025,
        )
        assert decl.form_type == FormType.F07
        assert decl.period == "01"

    def test_valid_tax_declaration_f14(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F14,
            period="06",
            year=2025,
        )
        assert decl.form_type == FormType.F14

    def test_valid_tax_declaration_f06(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F06,
            period="12",
            year=2025,
        )
        assert decl.form_type == FormType.F06

    def test_valid_period_range_01_to_12(self):
        for p in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
            decl = TaxDeclaration(
                user_id=uuid4(),
                form_type=FormType.F07,
                period=p,
                year=2025,
            )
            assert decl.period == p

    def test_invalid_period_00_raises_error(self):
        with pytest.raises(ValidationError, match="period"):
            TaxDeclaration(
                user_id=uuid4(),
                form_type=FormType.F07,
                period="00",
                year=2025,
            )

    def test_invalid_period_13_raises_error(self):
        with pytest.raises(ValidationError, match="period"):
            TaxDeclaration(
                user_id=uuid4(),
                form_type=FormType.F07,
                period="13",
                year=2025,
            )

    def test_invalid_period_with_letters_raises_error(self):
        with pytest.raises(ValidationError, match="period"):
            TaxDeclaration(
                user_id=uuid4(),
                form_type=FormType.F07,
                period="ab",
                year=2025,
            )

    def test_invalid_form_type_raises_error(self):
        with pytest.raises(ValidationError):
            TaxDeclaration(
                user_id=uuid4(),
                form_type="F-99",
                period="01",
                year=2025,
            )

    def test_default_status_is_draft(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F07,
            period="01",
            year=2025,
        )
        assert decl.status == DeclarationStatus.DRAFT

    def test_submitted_status(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F07,
            period="01",
            year=2025,
            status=DeclarationStatus.SUBMITTED,
        )
        assert decl.status == DeclarationStatus.SUBMITTED

    def test_declaration_auto_generates_uuid(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F07,
            period="01",
            year=2025,
        )
        assert isinstance(decl.declaration_id, UUID)

    def test_declaration_created_at_defaults(self):
        decl = TaxDeclaration(
            user_id=uuid4(),
            form_type=FormType.F07,
            period="01",
            year=2025,
        )
        assert isinstance(decl.created_at, datetime)
