from src.domain.interfaces.repository import DeclarationRepository
from src.domain.models.tax_declaration import TaxDeclaration


class ListDeclarationsUseCase:
    def __init__(self, decl_repo: DeclarationRepository):
        self._decl_repo = decl_repo

    async def execute(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50,
        form_type: str | None = None,
        year: int | None = None,
        period: str | None = None,
        status: str | None = None,
    ) -> list[TaxDeclaration]:
        all_decls = await self._decl_repo.get_by_user_id(
            user_id, page=page, limit=limit
        )
        result = []
        for d in all_decls:
            if form_type and d.form_type.value != form_type:
                continue
            if year is not None and d.year != year:
                continue
            if period and d.period != period:
                continue
            if status and d.status.value != status:
                continue
            result.append(d)
        return result
