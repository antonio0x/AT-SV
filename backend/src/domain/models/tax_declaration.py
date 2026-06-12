from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class FormType(str, Enum):
    F07 = "F-07"
    F14 = "F-14"
    F06 = "F-06"


class DeclarationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class TaxDeclaration(BaseModel):
    declaration_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    form_type: FormType
    period: str = Field(pattern=r"^(0[1-9]|1[0-2])$")
    year: int
    total_iva: Decimal | None = None
    total_renta: Decimal | None = None
    status: DeclarationStatus = DeclarationStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
