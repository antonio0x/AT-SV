from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from pydantic import BaseModel, Field


class Employee(BaseModel):
    employee_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    nombre: str
    salario: Decimal
    isr_rate: Decimal = Field(default=Decimal("0.10"))
    iss_deduction: Decimal = Field(default=Decimal("0.03"))
    afp_deduction: Decimal = Field(default=Decimal("0.0725"))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
