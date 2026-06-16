from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(BaseModel):
    transaction_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    type: TransactionType
    amount: Decimal = Field(gt=Decimal("0"))
    category: str
    description: str | None = None
    date: date
    iva_rate: Decimal = Field(default=Decimal("0.13"))
    created_at: datetime = Field(default_factory=datetime.now)
