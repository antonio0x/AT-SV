from fastapi import APIRouter, Depends

from src.api.bff.response import BFFResponse
from src.api.bff.schemas import UserBFF
from src.application.use_cases.register_user import RegisterUserUseCase
from src.infrastructure.repositories.user_repo import DynamoDBUserRepository

router = APIRouter(tags=["users"])


def get_user_repo():
    return DynamoDBUserRepository()


@router.post("/users", response_model=BFFResponse[UserBFF])
async def create_user(
    email: str,
    business_name: str,
    business_type: str,
    nit: str,
    nrc: str | None = None,
    regimen_fiscal: str = "simplificado",
    repo=Depends(get_user_repo),
):
    use_case = RegisterUserUseCase(repo)
    user = await use_case.execute(
        email=email,
        business_name=business_name,
        business_type=business_type,
        nit=nit,
        nrc=nrc,
        regimen_fiscal=regimen_fiscal,
    )
    return BFFResponse.ok(
        data=UserBFF(
            user_id=str(user.user_id),
            email=user.email,
            business_name=user.business_name,
            business_type=user.business_type,
            regimen_fiscal=user.regimen_fiscal,
        )
    )


@router.get("/users/{user_id}", response_model=BFFResponse[UserBFF])
async def get_user(user_id: str, repo=Depends(get_user_repo)):
    user = await repo.get_by_id(user_id)
    if not user:
        return BFFResponse.error(code="NOT_FOUND", message="User not found")
    return BFFResponse.ok(
        data=UserBFF(
            user_id=str(user.user_id),
            email=user.email,
            business_name=user.business_name,
            business_type=user.business_type,
            regimen_fiscal=user.regimen_fiscal,
        )
    )
