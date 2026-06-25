from src.domain.exceptions import DomainError
from src.domain.interfaces.repository import DeclarationRepository
from src.domain.models.tax_declaration import (
    TaxDeclaration,
    DeclarationStatus,
)


class SubmitDeclarationUseCase:
    def __init__(self, decl_repo: DeclarationRepository):
        self._decl_repo = decl_repo

    async def execute(
        self, user_id: str, declaration_id: str
    ) -> TaxDeclaration:
        decl = await self._decl_repo.get_by_id(declaration_id)
        if not decl or decl.user_id != user_id:
            raise DomainError(
                code="NOT_FOUND", message="Declaration not found"
            )
        if decl.status == DeclarationStatus.SUBMITTED:
            raise DomainError(
                code="ALREADY_SUBMITTED",
                message="Declaration is already submitted",
            )
        updated = decl.model_copy(
            update={"status": DeclarationStatus.SUBMITTED}
        )
        return await self._decl_repo.update(updated)
