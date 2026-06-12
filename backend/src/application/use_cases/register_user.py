from src.domain.models.user import User
from src.domain.interfaces.repository import UserRepository


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(
        self,
        email: str,
        business_name: str,
        business_type: str,
        nit: str,
        nrc: str | None = None,
        regimen_fiscal: str = "simplificado",
    ) -> User:
        user = User(
            email=email,
            business_name=business_name,
            business_type=business_type,
            nit=nit,
            nrc=nrc,
            regimen_fiscal=regimen_fiscal,
        )
        return await self._user_repo.create(user)
