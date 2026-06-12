from decimal import Decimal, ROUND_HALF_UP

IVA_RATE = Decimal("0.13")

PAGO_CUENTA_RATES: dict[str, Decimal] = {
    "servicios_profesionales": Decimal("0.10"),
    "servicios_no_profesionales": Decimal("0.05"),
    "alquileres": Decimal("0.05"),
    "otros": Decimal("0.01"),
}


def calculate_iva(amount: Decimal, rate: Decimal = IVA_RATE) -> Decimal:
    if amount < Decimal("0"):
        raise ValueError("Amount cannot be negative")
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_pago_cuenta(amount: Decimal, rate: Decimal) -> Decimal:
    if amount < Decimal("0"):
        raise ValueError("Amount cannot be negative")
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total_iva_from_transactions(transactions: list[dict]) -> Decimal:
    total = Decimal("0")
    for t in transactions:
        total += calculate_iva(t["amount"], t.get("iva_rate", IVA_RATE))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
