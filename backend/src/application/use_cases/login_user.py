from src.application.auth import verify_password
from src.domain.exceptions import DomainError
from src.domain.interfaces.repository import UserRepository
from src.domain.models.user import User


class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(self, email: str, password: str) -> User:
        user = await self._user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            raise DomainError("INVALID_CREDENTIALS", "Credenciales inválidas")
        if not verify_password(password, user.hashed_password):
            raise DomainError("INVALID_CREDENTIALS", "Credenciales inválidas")
        return user
