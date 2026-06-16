from src.domain.interfaces.repository import TransactionRepository
from src.infrastructure.database import get_settings
from src.infrastructure.repositories.in_memory import InMemoryTransactionRepository


def get_user_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.fake_repos import fake_user_repo
        return fake_user_repo
    from src.infrastructure.repositories.user_repo import DynamoDBUserRepository
    return DynamoDBUserRepository()


def get_tx_repo() -> TransactionRepository:
    return InMemoryTransactionRepository()
