from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response
from jose import JWTError, jwt

from src.api.dependencies import get_user_repo
from src.infrastructure.database import get_settings


def jwt_encode(payload: dict) -> str:
    settings = get_settings()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def jwt_decode(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"errors": [{"code": "UNAUTHENTICATED", "message": "No autenticado"}]},
        )


def set_auth_cookie(response: Response, user) -> None:
    token = jwt_encode({"sub": user.user_id, "email": user.email})
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="strict",
        path="/api",
        max_age=settings.jwt_expire_minutes * 60,
        secure=not settings.debug if hasattr(settings, "debug") else False,
    )


def clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        samesite="strict",
        path="/api",
        max_age=0,
        secure=not settings.debug if hasattr(settings, "debug") else False,
    )


async def get_current_user(request: Request, repo=Depends(get_user_repo)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"errors": [{"code": "UNAUTHENTICATED", "message": "No autenticado"}]},
        )
    payload = jwt_decode(token)
    user = await repo.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"errors": [{"code": "UNAUTHENTICATED", "message": "No autenticado"}]},
        )
    return user
