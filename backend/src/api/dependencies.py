from src.infrastructure.database import get_settings


def get_user_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.fake_repos import fake_user_repo
        return fake_user_repo
    from src.infrastructure.repositories.user_repo import DynamoDBUserRepository
    return DynamoDBUserRepository()


def get_tx_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.fake_repos import fake_transaction_repo
        return fake_transaction_repo
    from src.infrastructure.repositories.transaction_repo import DynamoDBTransactionRepository
    return DynamoDBTransactionRepository()


def get_declaration_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.repositories.in_memory import InMemoryDeclarationRepository
        return InMemoryDeclarationRepository()
    raise NotImplementedError("DynamoDB DeclarationRepository not yet implemented")


def get_employee_repo():
    settings = get_settings()
    if settings.use_fake_repos:
        from src.infrastructure.repositories.in_memory import InMemoryEmployeeRepository
        return InMemoryEmployeeRepository()
    raise NotImplementedError("DynamoDB EmployeeRepository not yet implemented")
