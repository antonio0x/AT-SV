from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.interfaces.repository import UserRepository
from src.domain.models.user import User
from src.infrastructure.database import get_dynamodb_resource, get_settings


_DYNAMO_SERIALIZABLE = (UUID, datetime, date)


class DynamoDBUserRepository(UserRepository):
    def __init__(self):
        self.table = get_dynamodb_resource().Table(get_settings().users_table)

    @staticmethod
    def _to_item(model: BaseModel) -> dict:
        item = model.model_dump()
        for k, v in item.items():
            if isinstance(v, _DYNAMO_SERIALIZABLE):
                item[k] = str(v)
        return item

    async def create(self, user: User) -> User:
        self.table.put_item(Item=self._to_item(user))
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item")
        return User(**item) if item else None

    async def get_by_email(self, email: str) -> User | None:
        response = self.table.query(
            IndexName="email_index",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": email},
        )
        items = response.get("Items", [])
        return User(**items[0]) if items else None

    async def update(self, user: User) -> User:
        self.table.put_item(Item=self._to_item(user))
        return user

    async def delete(self, user_id: str) -> bool:
        self.table.delete_item(Key={"user_id": user_id})
        return True
