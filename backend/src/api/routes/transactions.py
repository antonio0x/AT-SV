from datetime import date as _date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth.helpers import get_current_user
from src.api.bff.response import BFFResponse, ResponseMeta
from src.api.bff.schemas import (
    TransactionBFF,
    TransactionCreateRequest,
    TransactionUpdateRequest,
)
from src.api.dependencies import get_tx_repo
from src.application.use_cases.record_transaction import RecordTransactionUseCase
from src.domain.models.user import User

router = APIRouter(tags=["transactions"])


@router.post(
    "/transactions",
    response_model=BFFResponse[TransactionBFF],
    status_code=201,
)
async def create_transaction(
    body: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_tx_repo),
):
    use_case = RecordTransactionUseCase(repo)
    tx_date = _date.fromisoformat(body.date) if body.date else None
    tx = await use_case.execute(
        user_id=current_user.user_id,
        type=body.type,
        amount=body.amount,
        category=body.category,
        description=body.description,
        tx_date=tx_date,
        iva_rate=body.iva_rate,
    )
    return BFFResponse.ok(
        data=TransactionBFF(
            transaction_id=str(tx.transaction_id),
            type=tx.type.value,
            amount=tx.amount,
            category=tx.category,
            description=tx.description,
            date=tx.date.isoformat(),
            iva=tx.amount * tx.iva_rate,
            iva_rate=tx.iva_rate,
            created_at=tx.created_at.isoformat(),
        )
    )


@router.get(
    "/transactions", response_model=BFFResponse[list[TransactionBFF]]
)
async def list_transactions(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_tx_repo),
):
    txs = await repo.get_by_user_id(current_user.user_id, page=page, limit=limit)
    items = [
        TransactionBFF(
            transaction_id=str(tx.transaction_id),
            type=tx.type.value,
            amount=tx.amount,
            category=tx.category,
            description=tx.description,
            date=tx.date.isoformat(),
            iva=tx.amount * tx.iva_rate,
            iva_rate=tx.iva_rate,
            created_at=tx.created_at.isoformat(),
        )
        for tx in txs
    ]
    return BFFResponse.ok(
        data=items, meta=ResponseMeta(page=page, limit=limit, total=len(items))
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=BFFResponse[TransactionBFF],
)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_tx_repo),
):
    tx = await repo.get_by_id(transaction_id)
    if not tx or str(tx.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=404,
            detail={
                "errors": [
                    {
                        "code": "NOT_FOUND",
                        "message": "Transacción no encontrada",
                    }
                ]
            },
        )
    return BFFResponse.ok(
        data=TransactionBFF(
            transaction_id=str(tx.transaction_id),
            type=tx.type.value,
            amount=tx.amount,
            category=tx.category,
            description=tx.description,
            date=tx.date.isoformat(),
            iva=tx.amount * tx.iva_rate,
            iva_rate=tx.iva_rate,
            created_at=tx.created_at.isoformat(),
        )
    )


@router.put(
    "/transactions/{transaction_id}",
    response_model=BFFResponse[TransactionBFF],
)
async def update_transaction(
    transaction_id: str,
    body: TransactionUpdateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_tx_repo),
):
    tx = await repo.get_by_id(transaction_id)
    if not tx or str(tx.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=404,
            detail={
                "errors": [
                    {
                        "code": "NOT_FOUND",
                        "message": "Transacción no encontrada",
                    }
                ]
            },
        )
    update_data = body.model_dump(exclude_none=True)
    if "date" in update_data:
        update_data["date"] = _date.fromisoformat(body.date)
    tx = tx.model_copy(update=update_data)
    updated = await repo.update(tx)
    return BFFResponse.ok(
        data=TransactionBFF(
            transaction_id=str(updated.transaction_id),
            type=updated.type.value,
            amount=updated.amount,
            category=updated.category,
            description=updated.description,
            date=updated.date.isoformat(),
            iva=updated.amount * updated.iva_rate,
            iva_rate=updated.iva_rate,
            created_at=updated.created_at.isoformat(),
        )
    )


@router.delete(
    "/transactions/{transaction_id}",
    response_model=BFFResponse[dict],
)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_tx_repo),
):
    tx = await repo.get_by_id(transaction_id)
    if not tx or str(tx.user_id) != current_user.user_id:
        raise HTTPException(
            status_code=404,
            detail={
                "errors": [
                    {
                        "code": "NOT_FOUND",
                        "message": "Transacción no encontrada",
                    }
                ]
            },
        )
    await repo.delete(transaction_id)
    return BFFResponse.ok(data={"message": "Transacción eliminada"})
