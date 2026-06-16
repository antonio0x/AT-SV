from fastapi import APIRouter, Depends

from src.api.auth.helpers import get_current_user
from src.api.bff.response import BFFResponse
from src.api.bff.schemas import UserBFF
from src.api.dependencies import get_user_repo
from src.domain.models.user import User

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=BFFResponse[UserBFF])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return BFFResponse.ok(
        data=UserBFF(
            user_id=current_user.user_id,
            email=current_user.email,
            business_name=current_user.business_name,
            business_type=current_user.business_type,
            regimen_fiscal=current_user.regimen_fiscal,
        )
    )


@router.get("/users/{user_id}", response_model=BFFResponse[UserBFF])
async def get_user(user_id: str, repo=Depends(get_user_repo)):
    user = await repo.get_by_id(user_id)
    if not user:
        return BFFResponse.error(code="NOT_FOUND", message="User not found")
    return BFFResponse.ok(
        data=UserBFF(
            user_id=user.user_id,
            email=user.email,
            business_name=user.business_name,
            business_type=user.business_type,
            regimen_fiscal=user.regimen_fiscal,
        )
    )
