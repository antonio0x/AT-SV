from decimal import Decimal

from pydantic import BaseModel


class UserBFF(BaseModel):
    user_id: str
    email: str
    business_name: str
    business_type: str
    regimen_fiscal: str


class TransactionBFF(BaseModel):
    transaction_id: str
    type: str
    amount: Decimal
    category: str
    description: str | None
    date: str
    iva: Decimal
    iva_rate: Decimal


class TaxProjectionBFF(BaseModel):
    total_iva: Decimal
    total_pago_cuenta: Decimal
    total_income: Decimal
    total_expenses: Decimal
    period: str
    year: int
    estimated_iva_due: Decimal
    estimated_pago_cuenta_due: Decimal


class DeclarationBFF(BaseModel):
    declaration_id: str
    user_id: str
    form_type: str
    period: str
    year: int
    status: str
    total_iva: Decimal | None = None
    iva_debito: Decimal | None = None
    iva_credito: Decimal | None = None
    iva_retenido: Decimal | None = None
    ingresos_brutos: Decimal | None = None
    tasa_aplicada: Decimal | None = None
    pago_cuenta_calculado: Decimal | None = None
    saldo_a_favor_anterior: Decimal | None = None
    total_remuneraciones: Decimal | None = None
    total_empleados: int | None = None
    isr_retenido: Decimal | None = None
    cotizaciones_iss: Decimal | None = None
    cotizaciones_afp: Decimal | None = None
    created_at: str


class DeclarationCalculateRequest(BaseModel):
    form_type: str
    period: str
    year: int


class DeclarationCreateRequest(BaseModel):
    declaration_id: str | None = None
    form_type: str
    period: str
    year: int
    total_iva: Decimal | None = None
    iva_debito: Decimal | None = None
    iva_credito: Decimal | None = None
    iva_retenido: Decimal | None = None
    ingresos_brutos: Decimal | None = None
    tasa_aplicada: Decimal | None = None
    pago_cuenta_calculado: Decimal | None = None
    saldo_a_favor_anterior: Decimal | None = None
    total_remuneraciones: Decimal | None = None
    total_empleados: int | None = None
    isr_retenido: Decimal | None = None
    cotizaciones_iss: Decimal | None = None
    cotizaciones_afp: Decimal | None = None


class EmployeeBFF(BaseModel):
    employee_id: str
    user_id: str
    nombre: str
    salario: Decimal
    isr_rate: Decimal
    iss_deduction: Decimal
    afp_deduction: Decimal
    created_at: str


class EmployeeCreateRequest(BaseModel):
    nombre: str
    salario: Decimal
    isr_rate: Decimal | None = None
    iss_deduction: Decimal | None = None
    afp_deduction: Decimal | None = None


class EmployeeUpdateRequest(BaseModel):
    nombre: str | None = None
    salario: Decimal | None = None
    isr_rate: Decimal | None = None
    iss_deduction: Decimal | None = None
    afp_deduction: Decimal | None = None
