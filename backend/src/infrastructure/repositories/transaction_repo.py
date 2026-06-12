from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.interfaces.repository import TransactionRepository
from src.domain.models.transaction import Transaction
from src.infrastructure.database import get_dynamodb_resource, get_settings


_DYNAMO_SERIALIZABLE = (UUID, datetime, date)


class DynamoDBTransactionRepository(TransactionRepository):
    def __init__(self):
        self.table = get_dynamodb_resource().Table(get_settings().transactions_table)

    @staticmethod
    def _to_item(model: BaseModel) -> dict:
        item = model.model_dump()
        for k, v in item.items():
            if isinstance(v, _DYNAMO_SERIALIZABLE):
                item[k] = str(v)
        return item

    async def create(self, transaction: Transaction) -> Transaction:
        self.table.put_item(Item=self._to_item(transaction))
        return transaction

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        response = self.table.get_item(Key={"transaction_id": transaction_id})
        item = response.get("Item")
        return Transaction(**item) if item else None

    async def get_by_user_id(self, user_id: str, page: int = 1, limit: int = 50) -> list[Transaction]:
        response = self.table.query(
            IndexName="user_transactions",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id},
            Limit=limit,
        )
        return [Transaction(**item) for item in response.get("Items", [])]

    async def update(self, transaction: Transaction) -> Transaction:
        self.table.put_item(Item=self._to_item(transaction))
        return transaction

    async def delete(self, transaction_id: str) -> bool:
        self.table.delete_item(Key={"transaction_id": transaction_id})
        return True
