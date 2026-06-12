from decimal import Decimal, ROUND_HALF_UP
import pytest
from src.domain.services.tax_engine import (
    calculate_iva,
    calculate_pago_cuenta,
    calculate_total_iva_from_transactions,
    IVA_RATE,
    PAGO_CUENTA_RATES,
)


class TestCalculateIVA:
    def test_normal_calculation(self):
        result = calculate_iva(Decimal("100"), IVA_RATE)
        assert result == Decimal("13.00")

    def test_zero_amount(self):
        result = calculate_iva(Decimal("0"), IVA_RATE)
        assert result == Decimal("0.00")

    def test_negative_amount_raises_value_error(self):
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            calculate_iva(Decimal("-1"), IVA_RATE)

    def test_rounding_one_unit(self):
        result = calculate_iva(Decimal("1.00"), IVA_RATE)
        assert result == Decimal("0.13")

    def test_rounding_one_unit_no_decimals(self):
        result = calculate_iva(Decimal("1"), IVA_RATE)
        assert result == Decimal("0.13")

    def test_rounding_high_precision(self):
        result = calculate_iva(Decimal("0.001"), IVA_RATE)
        assert result == Decimal("0.00")

    def test_determinism(self, decimal_amounts):
        for amount in decimal_amounts:
            first = calculate_iva(amount, IVA_RATE)
            for _ in range(100):
                assert calculate_iva(amount, IVA_RATE) == first

    def test_default_rate(self):
        result = calculate_iva(Decimal("200"))
        assert result == Decimal("26.00")

    def test_custom_rate(self):
        result = calculate_iva(Decimal("100"), Decimal("0.10"))
        assert result == Decimal("10.00")

    def test_large_amount(self):
        result = calculate_iva(Decimal("9999999999.99"), IVA_RATE)
        expected = (Decimal("9999999999.99") * IVA_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        assert result == expected

    def test_high_precision_input(self):
        result = calculate_iva(Decimal("0.123456789"), IVA_RATE)
        assert isinstance(result, Decimal)
        assert result == Decimal("0.02")

    def test_rounding_half_up_005(self):
        result = calculate_iva(Decimal("0.005"), IVA_RATE)
        assert result == Decimal("0.00")

    def test_sequential_calls_no_state_leakage(self):
        results = []
        for i in range(100):
            r = calculate_iva(Decimal(f"{i}.00"), IVA_RATE)
            results.append(r)
        for i, r in enumerate(results):
            expected = (Decimal(f"{i}.00") * IVA_RATE).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            assert r == expected, f"State leakage at iteration {i}"

    def test_determinism_all_functions(self, decimal_amounts):
        for amount in decimal_amounts:
            first_iva = calculate_iva(amount, IVA_RATE)
            first_pc = calculate_pago_cuenta(amount, PAGO_CUENTA_RATES["otros"])
            for _ in range(100):
                assert calculate_iva(amount, IVA_RATE) == first_iva
                assert (
                    calculate_pago_cuenta(amount, PAGO_CUENTA_RATES["otros"])
                    == first_pc
                )


class TestCalculatePagoCuenta:
    def test_servicios_profesionales(self):
        result = calculate_pago_cuenta(
            Decimal("1000"), PAGO_CUENTA_RATES["servicios_profesionales"]
        )
        assert result == Decimal("100.00")

    def test_servicios_no_profesionales(self):
        result = calculate_pago_cuenta(
            Decimal("1000"), PAGO_CUENTA_RATES["servicios_no_profesionales"]
        )
        assert result == Decimal("50.00")

    def test_alquileres(self):
        result = calculate_pago_cuenta(
            Decimal("1000"), PAGO_CUENTA_RATES["alquileres"]
        )
        assert result == Decimal("50.00")

    def test_otros(self):
        result = calculate_pago_cuenta(
            Decimal("1000"), PAGO_CUENTA_RATES["otros"]
        )
        assert result == Decimal("10.00")

    def test_zero_amount(self):
        result = calculate_pago_cuenta(
            Decimal("0"), PAGO_CUENTA_RATES["servicios_profesionales"]
        )
        assert result == Decimal("0.00")

    def test_negative_amount_raises_value_error(self):
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            calculate_pago_cuenta(Decimal("-50"), Decimal("0.10"))

    def test_custom_rate_not_in_predefined_dict(self):
        result = calculate_pago_cuenta(Decimal("1000"), Decimal("0.07"))
        assert result == Decimal("70.00")


class TestCalculateTotalIVAFromTransactions:
    def test_empty_list(self):
        result = calculate_total_iva_from_transactions([])
        assert result == Decimal("0.00")

    def test_single_transaction(self):
        transactions = [{"amount": Decimal("100"), "iva_rate": IVA_RATE}]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("13.00")

    def test_multiple_transactions(self):
        transactions = [
            {"amount": Decimal("100"), "iva_rate": Decimal("0.13")},
            {"amount": Decimal("200"), "iva_rate": Decimal("0.13")},
            {"amount": Decimal("50"), "iva_rate": Decimal("0.13")},
        ]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("45.50")

    def test_mixed_rates(self):
        transactions = [
            {"amount": Decimal("100"), "iva_rate": Decimal("0.13")},
            {"amount": Decimal("200"), "iva_rate": Decimal("0.00")},
        ]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("13.00")

    def test_default_rate_when_missing(self):
        transactions = [{"amount": Decimal("100")}]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("13.00")

    def test_rounded_total(self):
        transactions = [
            {"amount": Decimal("0.01"), "iva_rate": IVA_RATE},
            {"amount": Decimal("0.02"), "iva_rate": IVA_RATE},
        ]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("0.00")

    def test_single_item_with_rate(self):
        transactions = [{"amount": Decimal("500.00"), "iva_rate": Decimal("0.13")}]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("65.00")

    def test_mixed_rates_multiple_items(self):
        transactions = [
            {"amount": Decimal("100.00"), "iva_rate": Decimal("0.13")},
            {"amount": Decimal("200.00"), "iva_rate": Decimal("0.05")},
            {"amount": Decimal("300.00"), "iva_rate": Decimal("0.00")},
        ]
        result = calculate_total_iva_from_transactions(transactions)
        assert result == Decimal("23.00")
