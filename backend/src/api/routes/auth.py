from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from src.api.auth.helpers import clear_auth_cookie, get_current_user, set_auth_cookie
from src.api.bff.response import BFFResponse
from src.api.bff.schemas import UserBFF
from src.api.dependencies import get_user_repo
from src.application.use_cases.login_user import LoginUserUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.exceptions import DomainError
from src.domain.models.user import User

router = APIRouter(tags=["auth"])

DOMAIN_ERROR_STATUS = {
    "EMAIL_EXISTS": 409,
    "INVALID_CREDENTIALS": 401,
    "VALIDATION_ERROR": 422,
}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    business_type: str
    nit: str
    nrc: str | None = None
    regimen_fiscal: str = "simplificado"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/auth/register", response_model=BFFResponse[UserBFF], status_code=201)
async def register(body: RegisterRequest, response: Response, repo=Depends(get_user_repo)):
    use_case = RegisterUserUseCase(repo)
    try:
        user = await use_case.execute(
            email=body.email,
            password=body.password,
            business_name=body.business_name,
            business_type=body.business_type,
            nit=body.nit,
            nrc=body.nrc,
            regimen_fiscal=body.regimen_fiscal,
        )
    except DomainError as e:
        status = DOMAIN_ERROR_STATUS.get(e.code, 400)
        return JSONResponse(
            status_code=status,
            content=BFFResponse.error(code=e.code, message=e.message).model_dump(),
        )
    set_auth_cookie(response, user)
    return BFFResponse.ok(
        data=UserBFF(
            user_id=user.user_id,
            email=user.email,
            business_name=user.business_name,
            business_type=user.business_type,
            regimen_fiscal=user.regimen_fiscal,
        )
    )


@router.post("/auth/login", response_model=BFFResponse[UserBFF])
async def login(body: LoginRequest, response: Response, repo=Depends(get_user_repo)):
    use_case = LoginUserUseCase(repo)
    try:
        user = await use_case.execute(email=body.email, password=body.password)
    except DomainError as e:
        status = DOMAIN_ERROR_STATUS.get(e.code, 400)
        return JSONResponse(
            status_code=status,
            content=BFFResponse.error(code=e.code, message=e.message).model_dump(),
        )
    set_auth_cookie(response, user)
    return BFFResponse.ok(
        data=UserBFF(
            user_id=user.user_id,
            email=user.email,
            business_name=user.business_name,
            business_type=user.business_type,
            regimen_fiscal=user.regimen_fiscal,
        )
    )


@router.post("/auth/logout", response_model=BFFResponse)
async def logout(response: Response):
    clear_auth_cookie(response)
    return BFFResponse.ok(data=None)
