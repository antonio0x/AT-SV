from decimal import Decimal

from src.domain.exceptions import DomainError
from src.domain.interfaces.repository import DeclarationRepository
from src.domain.models.tax_declaration import (
    TaxDeclaration,
    FormType,
    F07Data,
    F14Data,
    F06Data,
)


class SaveDeclarationUseCase:
    def __init__(self, decl_repo: DeclarationRepository):
        self._decl_repo = decl_repo

    async def execute(
        self,
        user_id: str,
        form_type: str,
        period: str,
        year: int,
        declaration_id: str | None = None,
        f07: F07Data | None = None,
        f14: F14Data | None = None,
        f06: F06Data | None = None,
    ) -> TaxDeclaration:
        existing = await self._decl_repo.get_by_period(
            user_id, form_type, year, period
        )
        if existing and existing.declaration_id != declaration_id:
            raise DomainError(
                code="DUPLICATE_PERIOD",
                message=f"Declaration already exists for {form_type} {period}/{year}",
            )

        if declaration_id:
            stored = await self._decl_repo.get_by_id(declaration_id)
            if not stored or stored.user_id != user_id:
                raise DomainError(
                    code="NOT_FOUND", message="Declaration not found"
                )
            if stored.status.value == "submitted":
                raise DomainError(
                    code="ALREADY_SUBMITTED",
                    message="Cannot update a submitted declaration",
                )
            decl = stored.model_copy(
                update={
                    "form_type": FormType(form_type),
                    "period": period,
                    "year": year,
                    "f07": f07,
                    "f14": f14,
                    "f06": f06,
                }
            )
            if f07:
                decl.total_iva = f07.total_iva
            return await self._decl_repo.update(decl)

        decl = TaxDeclaration(
            user_id=user_id,
            form_type=FormType(form_type),
            period=period,
            year=year,
            f07=f07,
            f14=f14,
            f06=f06,
        )
        if f07:
            decl.total_iva = f07.total_iva
        return await self._decl_repo.create(decl)
