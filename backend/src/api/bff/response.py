from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseMeta(BaseModel):
    page: int = 1
    limit: int = 50
    total: int = 0


class ErrorDetail(BaseModel):
    code: str
    message: str


class BFFResponse(BaseModel, Generic[T]):
    data: T | None = None
    meta: ResponseMeta = ResponseMeta()
    errors: list[ErrorDetail] = []

    @classmethod
    def ok(
        cls, data: T, meta: ResponseMeta | None = None
    ) -> "BFFResponse[T]":
        return cls(data=data, meta=meta or ResponseMeta())

    @classmethod
    def error(cls, code: str, message: str) -> "BFFResponse[T]":
        return cls(errors=[ErrorDetail(code=code, message=message)])
