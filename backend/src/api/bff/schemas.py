from decimal import Decimal

from pydantic import BaseModel, Field

from src.domain.models.transaction import TransactionType


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
    created_at: str


class TransactionCreateRequest(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=Decimal("0"))
    category: str
    description: str | None = None
    date: str | None = None
    iva_rate: Decimal | None = None


class TransactionUpdateRequest(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(None, gt=Decimal("0"))
    category: str | None = None
    description: str | None = None
    date: str | None = None
    iva_rate: Decimal | None = None


class TaxProjectionBFF(BaseModel):
    total_iva: Decimal
    total_pago_cuenta: Decimal
    total_income: Decimal
    total_expenses: Decimal
    period: str
    year: int
    estimated_iva_due: Decimal
    estimated_pago_cuenta_due: Decimal
