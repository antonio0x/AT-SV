from decimal import Decimal, ROUND_HALF_UP

from src.domain.models.tax_declaration import F07Data, F14Data, F06Data
from src.domain.models.transaction import Transaction, TransactionType
from src.domain.models.employee import Employee

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


def calculate_f07(transactions: list[Transaction]) -> F07Data:
    iva_debito = Decimal("0")
    iva_credito = Decimal("0")
    for t in transactions:
        iva = calculate_iva(t.amount, t.iva_rate)
        if t.type == TransactionType.INCOME:
            iva_debito += iva
        else:
            iva_credito += iva
    iva_debito = iva_debito.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    iva_credito = iva_credito.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return F07Data(
        total_iva=iva_debito - iva_credito,
        iva_debito=iva_debito,
        iva_credito=iva_credito,
        iva_retenido=Decimal("0"),
    )


def calculate_f14(
    transactions: list[Transaction],
    saldo_anterior: Decimal = Decimal("0"),
) -> F14Data:
    ingresos_brutos = Decimal("0")
    total_pago = Decimal("0")
    tasa_sum = Decimal("0")
    count = 0
    for t in transactions:
        if t.type == TransactionType.INCOME:
            ingresos_brutos += t.amount
            rate = PAGO_CUENTA_RATES.get(t.category, Decimal("0.01"))
            total_pago += calculate_pago_cuenta(t.amount, rate)
            tasa_sum += rate
            count += 1

    ingresos_brutos = ingresos_brutos.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_pago = total_pago.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tasa_aplicada = (tasa_sum / Decimal(max(count, 1))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    saldo_anterior = saldo_anterior.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    pago_cuenta = max(total_pago - saldo_anterior, Decimal("0"))

    return F14Data(
        ingresos_brutos=ingresos_brutos,
        tasa_aplicada=tasa_aplicada,
        pago_cuenta_calculado=pago_cuenta,
        saldo_a_favor_anterior=saldo_anterior,
    )


def calculate_f06(employees: list[Employee]) -> F06Data:
    total_remuneraciones = Decimal("0")
    isr_retenido = Decimal("0")
    cotizaciones_iss = Decimal("0")
    cotizaciones_afp = Decimal("0")

    for e in employees:
        salario = e.salario
        total_remuneraciones += salario
        isr_retenido += (salario * e.isr_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cotizaciones_iss += (salario * e.iss_deduction).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cotizaciones_afp += (salario * e.afp_deduction).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    return F06Data(
        total_remuneraciones=total_remuneraciones.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
        total_empleados=len(employees),
        isr_retenido=isr_retenido.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        cotizaciones_iss=cotizaciones_iss.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
        cotizaciones_afp=cotizaciones_afp.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
    )
