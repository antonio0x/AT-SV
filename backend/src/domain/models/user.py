from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr
from typing import Literal


class User(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    business_name: str
    business_type: Literal["persona_natural", "persona_juridica"]
    nit: str = Field(pattern=r"^\d{4}-\d{6}-\d{3}-\d$")
    nrc: str | None = None
    regimen_fiscal: Literal["general", "simplificado"]
    created_at: datetime = Field(default_factory=datetime.now)
