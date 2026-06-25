from decimal import Decimal

from fastapi import APIRouter, Depends

from src.api.bff.response import BFFResponse, ResponseMeta
from src.api.bff.schemas import TransactionBFF
from src.application.use_cases.record_transaction import RecordTransactionUseCase
from src.domain.models.transaction import TransactionType
from src.infrastructure.database import get_settings

router = APIRouter(tags=["transactions"])


def get_tx_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.fake_repos import fake_transaction_repo
        return fake_transaction_repo
    from src.infrastructure.repositories.transaction_repo import DynamoDBTransactionRepository
    return DynamoDBTransactionRepository()


@router.post("/transactions", response_model=BFFResponse[TransactionBFF])
async def create_transaction(
    user_id: str,
    type: TransactionType,
    amount: Decimal,
    category: str,
    description: str | None = None,
    iva_rate: Decimal | None = None,
    repo=Depends(get_tx_repo),
):
    use_case = RecordTransactionUseCase(repo)
    tx = await use_case.execute(
        user_id=user_id,
        type=type,
        amount=amount,
        category=category,
        description=description,
        iva_rate=iva_rate,
    )
    return BFFResponse.ok(
        data=TransactionBFF(
            transaction_id=str(tx.transaction_id),
            type=tx.type.value,
            amount=tx.amount,
            category=tx.category,
            description=tx.description,
            date=tx.date.isoformat(),
            iva=tx.amount * (iva_rate or Decimal("0.13")),
            iva_rate=tx.iva_rate,
        )
    )


@router.get(
    "/transactions", response_model=BFFResponse[list[TransactionBFF]]
)
async def list_transactions(
    user_id: str,
    page: int = 1,
    limit: int = 50,
    repo=Depends(get_tx_repo),
):
    txs = await repo.get_by_user_id(user_id, page=page, limit=limit)
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
        )
        for tx in txs
    ]
    return BFFResponse.ok(
        data=items, meta=ResponseMeta(page=page, limit=limit, total=len(items))
    )
