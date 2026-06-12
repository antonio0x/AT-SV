from decimal import Decimal

from src.api.bff.response import BFFResponse, ErrorDetail, ResponseMeta
from src.api.bff.schemas import TaxProjectionBFF, TransactionBFF, UserBFF


class TestBFFResponse:
    def test_ok_creates_success_response(self):
        response = BFFResponse.ok(data={"key": "value"})
        assert response.data == {"key": "value"}
        assert response.errors == []
        assert response.meta == ResponseMeta()

    def test_ok_with_custom_meta(self):
        meta = ResponseMeta(page=2, limit=10, total=100)
        response = BFFResponse.ok(data="test", meta=meta)
        assert response.data == "test"
        assert response.meta == meta

    def test_ok_with_list_data(self):
        response = BFFResponse.ok(data=[1, 2, 3])
        assert response.data == [1, 2, 3]
        assert response.errors == []

    def test_ok_with_none_data(self):
        response = BFFResponse.ok(data=None)
        assert response.data is None

    def test_error_creates_error_response(self):
        response = BFFResponse.error(code="NOT_FOUND", message="Resource not found")
        assert response.data is None
        assert len(response.errors) == 1
        assert response.errors[0] == ErrorDetail(
            code="NOT_FOUND", message="Resource not found"
        )

    def test_error_multiple_calls_isolated(self):
        err1 = BFFResponse.error(code="A", message="First")
        err2 = BFFResponse.error(code="B", message="Second")
        assert len(err1.errors) == 1
        assert len(err2.errors) == 1
        assert err1.errors[0].code == "A"
        assert err2.errors[0].code == "B"

    def test_default_meta_values(self):
        response = BFFResponse.ok(data="x")
        assert response.meta.page == 1
        assert response.meta.limit == 50
        assert response.meta.total == 0

    def test_default_errors_empty(self):
        response = BFFResponse.ok(data="x")
        assert response.errors == []

    def test_ok_with_pagination_meta(self):
        meta = ResponseMeta(page=1, limit=25, total=100)
        response = BFFResponse.ok(data=["a", "b", "c"], meta=meta)
        assert response.meta.page == 1
        assert response.meta.limit == 25
        assert response.meta.total == 100
        assert len(response.data) == 3

    def test_error_with_multiple_errors(self):
        response = BFFResponse.error(
            code="VALIDATION_ERROR",
            message="Multiple fields invalid",
        )
        second_error = ErrorDetail(code="FIELD_ERROR", message="email is invalid")
        response.errors.append(second_error)
        assert len(response.errors) == 2
        assert response.errors[0].code == "VALIDATION_ERROR"
        assert response.errors[1].code == "FIELD_ERROR"

    def test_error_replaces_data_with_none(self):
        response = BFFResponse.error(code="ERROR", message="Something failed")
        assert response.data is None


class TestUserBFF:
    def test_user_bff_creation(self):
        user = UserBFF(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            business_name="Test S.A. de C.V.",
            business_type="persona_juridica",
            regimen_fiscal="general",
        )
        assert user.user_id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email == "test@example.com"
        assert user.business_name == "Test S.A. de C.V."
        assert user.business_type == "persona_juridica"
        assert user.regimen_fiscal == "general"

    def test_user_bff_serialization(self):
        user = UserBFF(
            user_id="id-1",
            email="a@b.com",
            business_name="Co",
            business_type="persona_natural",
            regimen_fiscal="simplificado",
        )
        data = user.model_dump()
        assert data["user_id"] == "id-1"
        assert data["email"] == "a@b.com"
        assert data["business_type"] == "persona_natural"

    def test_user_bff_serialization_all_fields(self):
        user = UserBFF(
            user_id="abc-123-def",
            email="user@domain.com",
            business_name="Full Name S.A.",
            business_type="persona_juridica",
            regimen_fiscal="general",
        )
        data = user.model_dump()
        assert data["user_id"] == "abc-123-def"
        assert data["email"] == "user@domain.com"
        assert data["business_name"] == "Full Name S.A."
        assert data["business_type"] == "persona_juridica"
        assert data["regimen_fiscal"] == "general"
        assert len(data) == 5


class TestTransactionBFF:
    def test_transaction_bff_creation(self):
        tx = TransactionBFF(
            transaction_id="tx-1",
            type="income",
            amount=Decimal("150.00"),
            category="ventas",
            description="Sale of products",
            date="2025-01-15",
            iva=Decimal("19.50"),
            iva_rate=Decimal("0.13"),
        )
        assert tx.transaction_id == "tx-1"
        assert tx.type == "income"
        assert tx.amount == Decimal("150.00")
        assert tx.category == "ventas"
        assert tx.description == "Sale of products"
        assert tx.date == "2025-01-15"
        assert tx.iva == Decimal("19.50")
        assert tx.iva_rate == Decimal("0.13")

    def test_transaction_bff_optional_description(self):
        tx = TransactionBFF(
            transaction_id="tx-2",
            type="expense",
            amount=Decimal("50.00"),
            category="servicios",
            description=None,
            date="2025-02-01",
            iva=Decimal("6.50"),
            iva_rate=Decimal("0.13"),
        )
        assert tx.description is None

    def test_transaction_bff_serialization(self):
        tx = TransactionBFF(
            transaction_id="tx-3",
            type="expense",
            amount=Decimal("100.00"),
            category="alquiler",
            description="Office rent",
            date="2025-03-01",
            iva=Decimal("13.00"),
            iva_rate=Decimal("0.13"),
        )
        data = tx.model_dump()
        assert data["type"] == "expense"
        assert data["iva"] == Decimal("13.00")

    def test_transaction_bff_with_decimal_amounts(self):
        tx = TransactionBFF(
            transaction_id="tx-decimal",
            type="income",
            amount=Decimal("999999.99"),
            category="ventas",
            description="Large amount",
            date="2025-06-01",
            iva=Decimal("129999.9987"),
            iva_rate=Decimal("0.13"),
        )
        assert tx.amount == Decimal("999999.99")
        assert tx.iva == Decimal("129999.9987")


class TestTaxProjectionBFF:
    def test_tax_projection_bff_creation(self):
        proj = TaxProjectionBFF(
            total_iva=Decimal("130.00"),
            total_pago_cuenta=Decimal("10.00"),
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("500.00"),
            period="monthly",
            year=2025,
            estimated_iva_due=Decimal("130.00"),
            estimated_pago_cuenta_due=Decimal("10.00"),
        )
        assert proj.total_iva == Decimal("130.00")
        assert proj.total_pago_cuenta == Decimal("10.00")
        assert proj.total_income == Decimal("1000.00")
        assert proj.total_expenses == Decimal("500.00")
        assert proj.period == "monthly"
        assert proj.year == 2025
        assert proj.estimated_iva_due == Decimal("130.00")
        assert proj.estimated_pago_cuenta_due == Decimal("10.00")

    def test_tax_projection_bff_zero_values(self):
        proj = TaxProjectionBFF(
            total_iva=Decimal("0"),
            total_pago_cuenta=Decimal("0"),
            total_income=Decimal("0"),
            total_expenses=Decimal("0"),
            period="yearly",
            year=2026,
            estimated_iva_due=Decimal("0"),
            estimated_pago_cuenta_due=Decimal("0"),
        )
        assert proj.total_iva == Decimal("0")
        assert proj.total_income == Decimal("0")

    def test_tax_projection_bff_serialization(self):
        proj = TaxProjectionBFF(
            total_iva=Decimal("26.00"),
            total_pago_cuenta=Decimal("2.00"),
            total_income=Decimal("200.00"),
            total_expenses=Decimal("100.00"),
            period="quarterly",
            year=2025,
            estimated_iva_due=Decimal("26.00"),
            estimated_pago_cuenta_due=Decimal("2.00"),
        )
        data = proj.model_dump()
        assert data["period"] == "quarterly"
        assert data["year"] == 2025
        assert data["estimated_iva_due"] == Decimal("26.00")

    def test_tax_projection_bff_zero_edge_cases(self):
        proj = TaxProjectionBFF(
            total_iva=Decimal("0.00"),
            total_pago_cuenta=Decimal("0.00"),
            total_income=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
            period="01",
            year=2025,
            estimated_iva_due=Decimal("0.00"),
            estimated_pago_cuenta_due=Decimal("0.00"),
        )
        assert proj.total_iva == Decimal("0.00")
        assert proj.estimated_iva_due == Decimal("0.00")
