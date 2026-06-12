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
