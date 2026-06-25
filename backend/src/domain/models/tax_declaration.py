from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field


class FormType(str, Enum):
    F07 = "F-07"
    F14 = "F-14"
    F06 = "F-06"


class DeclarationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class F07Data(BaseModel):
    total_iva: Decimal = Decimal("0")
    iva_debito: Decimal = Decimal("0")
    iva_credito: Decimal = Decimal("0")
    iva_retenido: Decimal = Decimal("0")


class F14Data(BaseModel):
    ingresos_brutos: Decimal = Decimal("0")
    tasa_aplicada: Decimal = Decimal("0")
    pago_cuenta_calculado: Decimal = Decimal("0")
    saldo_a_favor_anterior: Decimal = Decimal("0")


class F06Data(BaseModel):
    total_remuneraciones: Decimal = Decimal("0")
    total_empleados: int = 0
    isr_retenido: Decimal = Decimal("0")
    cotizaciones_iss: Decimal = Decimal("0")
    cotizaciones_afp: Decimal = Decimal("0")


class TaxDeclaration(BaseModel):
    declaration_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    form_type: FormType
    period: str = Field(pattern=r"^(0[1-9]|1[0-2])$")
    year: int
    total_iva: Decimal | None = None
    total_renta: Decimal | None = None
    status: DeclarationStatus = DeclarationStatus.DRAFT
    f07: F07Data | None = None
    f14: F14Data | None = None
    f06: F06Data | None = None
    created_at: datetime = Field(default_factory=datetime.now)
