from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(BaseModel):
    transaction_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    type: TransactionType
    amount: Decimal = Field(gt=Decimal("0"))
    category: str
    description: str | None = None
    date: date
    iva_rate: Decimal = Field(default=Decimal("0.13"))
    created_at: datetime = Field(default_factory=datetime.now)
