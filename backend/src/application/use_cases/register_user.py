from src.application.auth import hash_password
from src.domain.exceptions import DomainError
from src.domain.models.user import User
from src.domain.interfaces.repository import UserRepository


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(
        self,
        email: str,
        password: str,
        business_name: str,
        business_type: str,
        nit: str,
        nrc: str | None = None,
        regimen_fiscal: str = "simplificado",
    ) -> User:
        if len(password) < 8:
            raise DomainError("VALIDATION_ERROR", "La contraseña debe tener al menos 8 caracteres")

        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise DomainError("EMAIL_EXISTS", "El correo ya está registrado")

        hashed = hash_password(password)
        user = User(
            email=email,
            business_name=business_name,
            business_type=business_type,
            nit=nit,
            nrc=nrc,
            regimen_fiscal=regimen_fiscal,
            hashed_password=hashed,
        )
        return await self._user_repo.create(user)
