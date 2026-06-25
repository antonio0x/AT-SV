from abc import ABC, abstractmethod

from src.domain.models.transaction import Transaction
from src.domain.models.user import User
from src.domain.models.tax_declaration import TaxDeclaration
from src.domain.models.employee import Employee


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        ...


class TransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        ...

    @abstractmethod
    async def get_by_user_id(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> list[Transaction]:
        ...

    @abstractmethod
    async def update(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def delete(self, transaction_id: str) -> None:
        ...


class DeclarationRepository(ABC):
    @abstractmethod
    async def create(self, declaration: TaxDeclaration) -> TaxDeclaration:
        ...

    @abstractmethod
    async def get_by_id(self, declaration_id: str) -> TaxDeclaration | None:
        ...

    @abstractmethod
    async def get_by_user_id(
        self, user_id: str, page: int = 1, limit: int = 50
    ) -> list[TaxDeclaration]:
        ...

    @abstractmethod
    async def get_by_period(
        self, user_id: str, form_type: str, year: int, period: str
    ) -> TaxDeclaration | None:
        ...

    @abstractmethod
    async def update(self, declaration: TaxDeclaration) -> TaxDeclaration:
        ...

    @abstractmethod
    async def delete(self, declaration_id: str) -> None:
        ...


class EmployeeRepository(ABC):
    @abstractmethod
    async def create(self, employee: Employee) -> Employee:
        ...

    @abstractmethod
    async def get_by_id(self, employee_id: str) -> Employee | None:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> list[Employee]:
        ...

    @abstractmethod
    async def update(self, employee: Employee) -> Employee:
        ...

    @abstractmethod
    async def delete(self, employee_id: str) -> None:
        ...
