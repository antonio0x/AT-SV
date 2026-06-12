# Design: Backend Core — Foundation Layer for AT-SV

## 1. Directory Tree (File-Level Detail)

```
backend/
├── pyproject.toml                       # FastAPI, boto3, pydantic v2, pytest, httpx, pytest-asyncio
├── Makefile                             # test, lint, dev, clean targets
├── .env.example                         # AWS env vars, table names, CORS origin
├── .env                                 # (gitignored)
├── src/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app factory, lifespan, CORS, exception handlers
│   ├── config.py                        # pydantic-settings BaseSettings → Settings singleton
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py              # DI wiring: get_repo, get_uow
│   │   ├── middleware.py                # Request ID, timing, error logging
│   │   ├── bff/
│   │   │   ├── __init__.py
│   │   │   ├── response.py             # BFFResponse[T], ResponseMeta, ErrorDetail, pagination helpers
│   │   │   └── schemas.py              # UserBFF, TransactionBFF, TaxProjectionBFF, create/update request schemas
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py               # GET /health
│   │       ├── users.py                # CRUD routes → /api/v1/users
│   │       ├── transactions.py         # CRUD + list routes → /api/v1/transactions
│   │       └── taxes.py                # Projection route → /api/v1/taxes/projection
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       ├── register_user.py        # RegisterUserUseCase: validate → repo.create
│   │       ├── record_transaction.py   # RecordTransactionUseCase: validate → engine → repo.create
│   │       └── get_tax_projection.py   # GetTaxProjectionUseCase: load → accumulate → project
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   ├── repository.py           # UserRepository(ABC), TransactionRepository(ABC)
│   │   │   └── unit_of_work.py         # UnitOfWork(ABC)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User, UserCreate, UserUpdate — pydantic v2 models
│   │   │   ├── transaction.py          # Transaction, TransactionCreate — pydantic v2 models
│   │   │   └── tax_declaration.py      # TaxDeclaration — pydantic v2 model
│   │   └── services/
│   │       ├── __init__.py
│   │       └── tax_engine.py           # Pure functions: calculate_iva, calculate_pago_cuenta, accumulate_*
│   │
│   └── infrastructure/
│       ├── __init__.py
│       ├── database.py                 # boto3 DynamoDB client factory, table resolution
│       └── repositories/
│           ├── __init__.py
│           ├── user_repo.py            # DynamoDBUserRepo(UserRepository)
│           └── transaction_repo.py     # DynamoDBTransactionRepo(TransactionRepository)
│
└── tests/
    ├── __init__.py
    ├── conftest.py                     # fixtures: dynamo mock, test repos, test client
    ├── unit/
    │   ├── __init__.py
    │   ├── test_tax_engine.py          # Exhaustive: IVA, Pago Cuenta, edge cases, rounding
    │   └── test_models.py             # Pydantic validation, Decimal constraints
    ├── integration/
    │   ├── __init__.py
    │   ├── conftest.py                 # moto/LocalStack DynamoDB fixtures
    │   ├── test_user_repo.py          # CRUD + GSI queries
    │   └── test_transaction_repo.py   # CRUD + paginated list
    └── e2e/
        ├── __init__.py
        ├── conftest.py                 # AsyncClient fixture with DB mocked
        ├── test_health.py             # /health smoke test
        ├── test_users_e2e.py          # Full user lifecycle via API
        ├── test_transactions_e2e.py   # Full transaction lifecycle via API
        └── test_taxes_e2e.py         # Projection endpoint smoke
```

### Key file responsibilities

| File | Responsibility |
|------|---------------|
| `src/main.py` | FastAPI `lifespan`, app factory, register routers, CORS middleware, global exception handlers |
| `src/config.py` | `Settings(BaseSettings)` — loads from env/`.env`; AWS region, table names, CORS origins, app version |
| `src/api/dependencies.py` | FastAPI `Depends` callables: `get_user_repo`, `get_tx_repo`, `get_uow`, `get_current_user` (stub) |
| `src/api/bff/response.py` | `BFFResponse[T]`, `ResponseMeta`, `ErrorDetail`, `PaginationMeta`, `paginated_response()` builder |
| `src/api/bff/schemas.py` | BFF-optimized schemas + domain→BFF transformers (`UserBFF.from_domain(u)`) |
| `src/api/middleware.py` | `@app.middleware("http")` — request_id injection via uuid4 header, timing, structured error logging |
| `src/domain/interfaces/repository.py` | Pure ABCs with `@abstractmethod`, async signatures, no infrastructure imports |
| `src/domain/services/tax_engine.py` | Pure Decimal functions, zero imports outside `decimal` and `dataclasses` |
| `src/infrastructure/database.py` | `get_dynamodb_client()`, `get_table(name: str)` — cached client, resolves from Settings |
| `src/infrastructure/repositories/user_repo.py` | DynamoDB `PutItem`/`GetItem`/`UpdateItem`/`DeleteItem`, Decimal serialization |
| `tests/conftest.py` | Top-level fixtures: `settings_override`, `dynamodb_mock` (moto), `test_repos`, `async_client` |

## 2. Layer Dependency Diagram

```
┌══════════════════════════════════════════════════┐
│                   API / BFF                       │
│  src/api/ (routes, bff, middleware, deps)         │
│  Depends: application, domain (models only)       │
├──────────────────────────────────────────────────┤
│                  APPLICATION                      │
│  src/application/use_cases/                       │
│  Depends: domain (interfaces, models, services)   │
├──────────────┬───────────────────────────────────┤
│              │         DOMAIN                     │
│              │  src/domain/                       │
│              │  ● interfaces/ (ABCs)              │
│              │  ● models/ (pydantic)              │
│              │  ● services/ (pure functions)      │
│              │  IMPORTS: ZERO from other layers   │
│              │  stdlib only + pydantic            │
├──────────────┴───────────────────────────────────┤
│              INFRASTRUCTURE                       │
│  src/infrastructure/repositories/                 │
│  Depends: domain (interfaces), boto3              │
│                                                   │
│  Domain knows nothing about infra.                │
│  Infra implements Domain ABCs.                    │
│  Wiring: use_cases receive ABCs via DI.           │
│                                                   │
│  Flow:                                             │
│    Route Handler                                  │
│      → UseCase.__call__(deps...)                  │
│        → Domain Service (pure)                    │
│        → Repository ABC method                    │
│          → DynamoDB Impl (hidden behind ABC)      │
└═══════════════════════════════════════════════════┘

Dependency rule (enforced via imports):
  API        → Application, Domain
  Application → Domain (NOT API, NOT Infrastructure)
  Domain     → (nothing)
  Infrastructure → Domain (implements interfaces)

Everything depends on Domain. Domain depends on nothing.
```

## 3. Tax Engine Detailed Design

### `src/domain/services/tax_engine.py`

```python
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

IVA_RATE = Decimal("0.13")

# F-14 withholding rates by service type (Art. 156 LISR)
# Rates: Profesionales independientes → 10%, Arrendamiento → 5%, Otros → 1%
class PagoCuentaCategory(str, Enum):
    SERVICIOS_PROFESIONALES = "servicios_profesionales"
    ARRENDAMIENTO = "arrendamiento"
    OTROS_SERVICIOS = "otros_servicios"
    COMPRA_BIENES = "compra_bienes"

PAGO_CUENTA_RATES: dict[PagoCuentaCategory, Decimal] = {
    PagoCuentaCategory.SERVICIOS_PROFESIONALES: Decimal("0.10"),
    PagoCuentaCategory.ARRENDAMIENTO: Decimal("0.05"),
    PagoCuentaCategory.OTROS_SERVICIOS: Decimal("0.01"),
    PagoCuentaCategory.COMPRA_BIENES: Decimal("0.01"),
}

IVA_EXEMPT_AMOUNT = Decimal("0.00")  # No IVA exemption threshold in SV (all consumption taxed)


def calculate_iva(amount: Decimal, rate: Decimal = IVA_RATE) -> Decimal:
    """Calculate IVA (F-07): amount × rate, rounded to 2 decimals.

    Edge cases:
    - amount = 0 → Decimal('0.00')
    - amount negative → clamped to 0 (no negative IVA)
    - rate = 0 → Decimal('0.00')
    - Extreme precision: inputs like 0.1 + 0.2 produce exact Decimal('0.03') × rate
    """
    if amount <= Decimal("0"):
        return Decimal("0.00")
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_pago_cuenta(amount: Decimal, category: PagoCuentaCategory) -> Decimal:
    """Calculate Pago a Cuenta / Retención (F-14): amount × category rate, rounded to 2 decimals.

    Edge cases:
    - Unrecognized category → falls back to 1%
    - amount = 0 → Decimal('0.00')
    - amount negative → clamped to 0
    - Decimal rounding: standard ROUND_HALF_UP
    """
    if amount <= Decimal("0"):
        return Decimal("0.00")
    rate = PAGO_CUENTA_RATES.get(category, PAGO_CUENTA_RATES[PagoCuentaCategory.OTROS_SERVICIOS])
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_iva_from_transactions(transactions: list[dict]) -> Decimal:
    """Accumulate IVA from a list of transaction dicts with 'amount' and 'iva_rate'.

    Each transaction may have a different IVA rate (e.g., 0%, 13% for different goods).
    Returns sum of individual IVAs, rounded total to 2 decimals.
    """
    total = sum(
        calculate_iva(tx["amount"], Decimal(str(tx.get("iva_rate", IVA_RATE))))
        for tx in transactions
    )
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_pago_cuenta_from_transactions(
    transactions: list[dict],
    category_key: str = "category",
) -> dict[PagoCuentaCategory, Decimal]:
    """Group transactions by category and calculate Pago a Cuenta per category.

    Returns dict keyed by category with subtotals.
    """
    result: dict[PagoCuentaCategory, Decimal] = {}
    for cat in PagoCuentaCategory:
        cat_txs = [tx for tx in transactions if tx.get(category_key) == cat.value]
        if cat_txs:
            total = sum(
                calculate_pago_cuenta(tx["amount"], cat)
                for tx in cat_txs
            )
            result[cat] = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return result


class TaxProjection:
    """Result object for tax projection calculations."""

    def __init__(
        self,
        total_iva: Decimal,
        total_pago_cuenta: Decimal,
        pago_cuenta_breakdown: dict[PagoCuentaCategory, Decimal],
        period: str,
        year: int,
    ):
        self.total_iva = total_iva
        self.total_pago_cuenta = total_pago_cuenta
        self.pago_cuenta_breakdown = pago_cuenta_breakdown
        self.period = period
        self.year = year
```

### Edge case matrix

| Input | Function | Expected |
|-------|----------|----------|
| `Decimal("100.00")` × 0.13 | `calculate_iva` | `Decimal("13.00")` |
| `Decimal("0.00")` × 0.13 | `calculate_iva` | `Decimal("0.00")` |
| `Decimal("-50.00")` × 0.13 | `calculate_iva` | `Decimal("0.00")` |
| `Decimal("99.99")` × 0.13 | `calculate_iva` | `Decimal("13.00")` (12.9987 → 13.00) |
| `Decimal("99.99")` × 0.10 | `calculate_pago_cuenta` | `Decimal("10.00")` |
| `Decimal("0.001")` × 0.13 | `calculate_iva` | `Decimal("0.00")` |
| `Decimal("0.005")` × 0.13 | `calculate_iva` | `Decimal("0.00")` (0.00065 → 0.00) |
| `Decimal("0.01")` × 0.13 | `calculate_iva` | `Decimal("0.00")` (0.0013 → 0.00) |
| Unknown category | `calculate_pago_cuenta` | 1% fallback |
| Empty transaction list | `calculate_iva_from_transactions` | `Decimal("0.00")` |

## 4. Repository Interface Design

### `src/domain/interfaces/repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional

from domain.models.user import User, UserCreate, UserUpdate
from domain.models.transaction import Transaction, TransactionCreate


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: UserCreate) -> User:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Returns None if not found — no exceptions for missing entities."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Lookup via email GSI. Returns None if not found."""
        ...

    @abstractmethod
    async def update(self, user_id: str, updates: UserUpdate) -> Optional[User]:
        """Partial update. Returns updated User or None if not found."""
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Returns True if deleted, False if not found."""
        ...


class TransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction: TransactionCreate) -> Transaction:
        ...

    @abstractmethod
    async def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        ...

    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Transaction], int]:
        """Returns (items, total_count). Paginated via last_evaluated_key cursor.

        Internally maps page/limit to DynamoDB Query with ExclusiveStartKey.
        Total count is estimated (DynamoDB ScannedCount or pre-computed).
        """
        ...

    @abstractmethod
    async def update(self, transaction_id: str, updates: dict) -> Optional[Transaction]:
        ...

    @abstractmethod
    async def delete(self, transaction_id: str) -> bool:
        ...
```

### `src/domain/interfaces/unit_of_work.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncContextManager


class UnitOfWork(ABC):
    """Async context manager wrapping DynamoDB transactions.

    DynamoDB does not support multi-table transactions natively (only TransactWriteItems
    with up to 25 items). This UoW provides a logical transaction boundary:
    - On commit: flush queued write operations
    - On rollback: discard queue (no-op, since DynamoDB has no rollback)
    - On exit without commit: auto-rollback

    For future: can be extended to use DynamoDB transactions API when needed.
    """

    @abstractmethod
    async def commit(self) -> None:
        """Flush all pending writes. Raises on conflict."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Discard pending writes. Always succeeds."""
        ...

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
```

## 5. DynamoDB Table Design

### `users` table

| Attribute | Type | Key | Notes |
|-----------|------|-----|-------|
| `user_id` | String (UUID) | **HASH** (PK) | |
| `email` | String | **GSI PK** | email_index |
| `business_name` | String | | |
| `business_type` | String | | enum: persona_natural, persona_juridica |
| `nit` | String | | Unique, validated format |
| `nrc` | String | | Registro de Contribuyente |
| `regimen_fiscal` | String | | general, simplificado |
| `created_at` | String (ISO8601) | | |
| `updated_at` | String (ISO8601) | | |

```
Table: users
  PK: user_id (String)
  Billing: PAY_PER_REQUEST (on-demand)

GSI: email_index
  PK: email (String)
  Projection: ALL
```

### `transactions` table

| Attribute | Type | Key | Notes |
|-----------|------|-----|-------|
| `transaction_id` | String (UUID) | **HASH** (PK) | |
| `user_id` | String | **GSI PK** | user_transactions |
| `created_at` | String (ISO8601) | **GSI SK** | user_transactions (sort key) |
| `type` | String | | income, expense |
| `amount` | Number | | Decimal stored as Number |
| `category` | String | | enum: servicios_profesionales, arrendamiento, ... |
| `description` | String | | |
| `date` | String (ISO8601) | | Transaction date (may differ from created_at) |
| `iva_rate` | Number | | 0.13, 0.00, etc. |
| `updated_at` | String (ISO8601) | | |

```
Table: transactions
  PK: transaction_id (String)
  Billing: PAY_PER_REQUEST (on-demand)

GSI: user_transactions
  PK: user_id (String)
  SK: created_at (String) — enables time-ordered queries per user
  Projection: ALL
```

### `tax_declarations` table

| Attribute | Type | Key | Notes |
|-----------|------|-----|-------|
| `declaration_id` | String (UUID) | **HASH** (PK) | |
| `user_id` | String | **GSI PK** | user_declarations |
| `period` | String | **GSI SK** | user_declarations, format: YYYY-MM |
| `form_type` | String | | F-07, F-14, F-06 |
| `year` | Number | | |
| `total_iva` | Number | | |
| `total_renta` | Number | | |
| `status` | String | | draft, submitted |
| `created_at` | String (ISO8601) | | |
| `updated_at` | String (ISO8601) | | |

```
Table: tax_declarations
  PK: declaration_id (String)
  Billing: PAY_PER_REQUEST (on-demand)

GSI: user_declarations
  PK: user_id (String)
  SK: period (String) — enables period-range queries per user
  Projection: ALL
```

### Decimal serialization

DynamoDB Number type handles Decimal natively via `boto3.dynamodb.types.TypeSerializer`.
All `amount` fields use Python `Decimal` with `quantize(Decimal("0.01"))`.

```python
# src/infrastructure/database.py
from decimal import Decimal
import boto3
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from functools import lru_cache

serializer = TypeSerializer()
deserializer = TypeDeserializer()

@lru_cache
def get_dynamodb_client() -> "boto3.client":
    return boto3.client("dynamodb", region_name=settings.aws_region)

def get_table(table_name: str) -> "boto3.resource.Table":
    resource = boto3.resource("dynamodb", region_name=settings.aws_region)
    return resource.Table(table_name)

def item_to_dict(item: dict) -> dict:
    """Convert DynamoDB raw item to plain dict with Decimal numbers."""
    return {k: deserializer.deserialize(v) for k, v in item.items()}
```

## 6. BFF Response Schema Design

### `src/api/bff/response.py`

```python
from __future__ import annotations
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from decimal import Decimal

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    has_next: bool

class ResponseMeta(BaseModel):
    request_id: str
    version: str
    pagination: Optional[PaginationMeta] = None

class BFFResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    meta: ResponseMeta
    errors: list[ErrorDetail] = []

    @classmethod
    def success(cls, data: T, meta: ResponseMeta) -> "BFFResponse[T]":
        return cls(data=data, meta=meta, errors=[])

    @classmethod
    def error(cls, meta: ResponseMeta, errors: list[ErrorDetail]) -> "BFFResponse":
        return cls(data=None, meta=meta, errors=errors)
```

### `src/api/bff/schemas.py`

```python
from pydantic import BaseModel, EmailStr
from decimal import Decimal
from typing import Optional
from datetime import datetime

# ─── Request Schemas ───────────────────────────────────

class UserCreateRequest(BaseModel):
    email: str
    business_name: str
    business_type: str  # persona_natural, persona_juridica
    nit: str
    nrc: str
    regimen_fiscal: str  # general, simplificado

class UserUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    email: Optional[str] = None
    regimen_fiscal: Optional[str] = None

class TransactionCreateRequest(BaseModel):
    user_id: str
    type: str  # income, expense
    amount: Decimal
    category: str
    description: str
    date: str  # ISO8601
    iva_rate: Decimal = Decimal("0.13")

# ─── Response Schemas ──────────────────────────────────

class UserBFF(BaseModel):
    id: str
    email: str
    business_name: str
    business_type: str
    nit: str
    nrc: str
    regimen_fiscal: str
    created_at: str

class TransactionBFF(BaseModel):
    id: str
    user_id: str
    type: str
    amount: Decimal
    category: str
    description: str
    date: str
    iva_rate: Decimal
    iva_calculated: Decimal
    created_at: str

class PagoCuentaBreakdownBFF(BaseModel):
    servicios_profesionales: Optional[Decimal] = None
    arrendamiento: Optional[Decimal] = None
    otros_servicios: Optional[Decimal] = None
    compra_bienes: Optional[Decimal] = None

class TaxProjectionBFF(BaseModel):
    total_iva: Decimal
    total_pago_cuenta: Decimal
    pago_cuenta_breakdown: PagoCuentaBreakdownBFF
    period: str
    year: int

# ─── Domain → BFF transformers ─────────────────────────

class UserBFFTransformer:
    @staticmethod
    def from_domain(user: "User") -> UserBFF:
        return UserBFF(
            id=user.user_id,
            email=user.email,
            business_name=user.business_name,
            business_type=user.business_type,
            nit=user.nit,
            nrc=user.nrc,
            regimen_fiscal=user.regimen_fiscal,
            created_at=user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at),
        )

class TransactionBFFTransformer:
    @staticmethod
    def from_domain(tx: "Transaction") -> TransactionBFF:
        return TransactionBFF(
            id=tx.transaction_id,
            user_id=tx.user_id,
            type=tx.type,
            amount=tx.amount,
            category=tx.category,
            description=tx.description,
            date=tx.date.isoformat() if hasattr(tx.date, "isoformat") else str(tx.date),
            iva_rate=tx.iva_rate,
            iva_calculated=tx.amount * tx.iva_rate,
            created_at=tx.created_at.isoformat() if hasattr(tx.created_at, "isoformat") else str(tx.created_at),
        )
```

## 7. FastAPI App Structure

### `src/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from api.routes import health, users, transactions, taxes
from api.middleware import request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate DynamoDB connectivity (optional ping)
    yield
    # Shutdown: close connections (boto3 client cleanup)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AT-SV Copiloto Fiscal API",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS — allow frontend origin only in production; permissive in dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # e.g., ["http://localhost:5173"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.middleware("http")(request_id_middleware)

    # Global exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "data": None,
                "meta": {"request_id": request.state.request_id, "version": settings.app_version},
                "errors": [{"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}],
            },
        )

    # Register routers
    app.include_router(health.router, tags=["health"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
    app.include_router(taxes.router, prefix="/api/v1/taxes", tags=["taxes"])

    return app


app = create_app()
```

### Middleware

```python
# src/api/middleware.py
import uuid
import time
from fastapi import Request, Response


async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(round(elapsed * 1000, 1))
    return response
```

### Exception handlers (per-route)

```python
from fastapi import HTTPException
from api.bff.response import BFFResponse, ResponseMeta, ErrorDetail


async def http_exception_handler(request: Request, exc: HTTPException):
    meta = ResponseMeta(request_id=request.state.request_id, version=settings.app_version)
    return JSONResponse(
        status_code=exc.status_code,
        content=BFFResponse.error(
            meta=meta,
            errors=[ErrorDetail(code="HTTP_ERROR", message=exc.detail)],
        ).model_dump(mode="json"),
    )
```

## 8. Dependency Injection Strategy

**Approach**: FastAPI `Depends` — simplest, most idiomatic, no framework overhead.

```python
# src/api/dependencies.py
from fastapi import Depends
from domain.interfaces.repository import UserRepository, TransactionRepository
from domain.interfaces.unit_of_work import UnitOfWork
from infrastructure.repositories.user_repo import DynamoDBUserRepo
from infrastructure.repositories.transaction_repo import DynamoDBTransactionRepo
from infrastructure.database import get_table


async def get_user_repo() -> UserRepository:
    """Factory: returns UserRepository wired to DynamoDB.

    In tests, override this dependency via `app.dependency_overrides[get_user_repo]`.
    """
    table = get_table(settings.users_table_name)
    return DynamoDBUserRepo(table)


async def get_transaction_repo() -> TransactionRepository:
    table = get_table(settings.transactions_table_name)
    return DynamoDBTransactionRepo(table)


# Unit of Work — per-request managed
from infrastructure.repositories.unit_of_work import DynamoDBUnitOfWork


async def get_uow() -> UnitOfWork:
    """Returns a UoW bound to the current request's DynamoDB client."""
    return DynamoDBUnitOfWork(client=get_dynamodb_client())


# Use-case wiring (example)
from application.use_cases.register_user import RegisterUserUseCase


async def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo=user_repo)
```

### Override in tests

```python
# tests/conftest.py
from api.dependencies import get_user_repo
from infrastructure.repositories.user_repo import InMemoryUserRepo  # test double


@pytest.fixture
def override_deps(app, in_memory_repo):
    app.dependency_overrides[get_user_repo] = lambda: in_memory_repo
    yield
    app.dependency_overrides.clear()
```

## 9. Test Strategy

### Testing Pyramid

```
         ╱╲
        ╱ E2E ╲           ← 3-5 smoke tests (httpx.AsyncClient + mocked DB)
       ╱────────╲
      ╱ Integration ╲     ← ~10 tests (moto/LocalStack + real DynamoDB queries)
     ╱──────────────╲
    ╱    Unit         ╲    ← ~30+ tests (pure tax engine + model validation)
   ╱──────────────────╲
```

### Unit Tests (`tests/unit/test_tax_engine.py`)

```python
import pytest
from decimal import Decimal
from domain.services.tax_engine import (
    calculate_iva,
    calculate_pago_cuenta,
    calculate_iva_from_transactions,
    calculate_pago_cuenta_from_transactions,
    IVA_RATE,
    PagoCuentaCategory,
)
```

**Test cases**:

| Test | What it verifies |
|------|-----------------|
| `test_iva_standard_rate` | 100 × 0.13 = 13.00 |
| `test_iva_zero_amount` | 0 → 0.00 |
| `test_iva_negative_amount` | negative → 0.00 (clamped) |
| `test_iva_rounding_half_up` | 99.99 × 0.13 = 12.9987 → 13.00 |
| `test_iva_custom_rate` | 200 × 0.10 = 20.00 |
| `test_iva_zero_rate` | 100 × 0.00 = 0.00 |
| `test_pago_cuenta_profesional` | 1000 × 0.10 = 100.00 |
| `test_pago_cuenta_arrendamiento` | 1000 × 0.05 = 50.00 |
| `test_pago_cuenta_otros` | 1000 × 0.01 = 10.00 |
| `test_pago_cuenta_unknown_category` | unknown → 1% fallback |
| `test_pago_cuenta_negative` | negative → 0.00 |
| `test_accumulate_iva_multiple` | 3 transactions sum correctly |
| `test_accumulate_pago_cuenta_by_category` | grouped correctly |
| `test_empty_list` | empty list → 0.00 |
| `test_mixed_rates_in_accumulation` | different IVA rates per tx |

### Integration Tests (`tests/integration/`)

- `test_user_repo.py`: create → get_by_id → get_by_email → update → delete (with moto mock)
- `test_transaction_repo.py`: create → get_by_id → get_by_user with pagination → update → delete
- `test_pagination_cursor`: verify page/limit returns correct subset

Fixtures (moto):

```python
# tests/integration/conftest.py
import pytest
import boto3
from moto import mock_aws
from infrastructure.database import get_table


@pytest.fixture(scope="function")
def dynamodb_mock():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        # Create tables matching production schema
        client.create_table(
            TableName="users",
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "email_index",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # ... create transactions and tax_declarations tables similarly
        yield
```

### E2E Tests (`tests/e2e/`)

- `test_health.py`: GET /health → 200 + expected body shape
- `test_users_e2e.py`: POST user → GET user → GET by email → 404 for missing
- `test_transactions_e2e.py`: POST tx → GET tx → list by user → pagination
- `test_taxes_e2e.py`: seed transactions → GET /projection → verify calculated amounts

Fixtures:

```python
# tests/e2e/conftest.py
@pytest.fixture
async def async_client(app, override_deps):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### Coverage targets

| Layer | Target |
|-------|--------|
| `domain/services/tax_engine.py` | 100% — every branch, edge case, Decimal rounding |
| `domain/models/*` | 100% — pydantic validation (valid/invalid inputs) |
| `api/bff/*` | 95% — schema transformations, response builder |
| `application/use_cases/*` | 90% — happy path, validation errors |
| `infrastructure/repositories/*` | 85% — CRUD operations, pagination, edge cases |
| `api/routes/*` | 90% — via E2E tests |
| `api/middleware.py` | 100% — request_id injection, timing header |
| Overall | ≥85% |

### What NOT to test

- boto3 client initialization (trust AWS SDK behavior)
- Python stdlib Decimal rounding functions (trust CPython)
- FastAPI/CORS middleware internals (trust framework)
- Pydantic BaseSettings loading (trust pydantic-settings)
- DynamoDB eventual consistency quirks (note in test docstring)

## 10. Use Case Detail

### `RegisterUserUseCase`

```python
class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def __call__(self, data: UserCreate) -> User:
        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise DomainError("EMAIL_ALREADY_EXISTS", f"User with email {data.email} already exists")
        return await self._user_repo.create(data)
```

### `RecordTransactionUseCase`

```python
class RecordTransactionUseCase:
    def __init__(self, tx_repo: TransactionRepository):
        self._tx_repo = tx_repo

    async def __call__(self, data: TransactionCreate) -> Transaction:
        iva = calculate_iva(data.amount, data.iva_rate)
        return await self._tx_repo.create(data)
```

### `GetTaxProjectionUseCase`

```python
class GetTaxProjectionUseCase:
    def __init__(self, tx_repo: TransactionRepository):
        self._tx_repo = tx_repo

    async def __call__(self, user_id: str, year: int, period: str) -> TaxProjection:
        transactions, _ = await self._tx_repo.get_by_user(user_id, limit=9999)
        # Filter by year/period
        filtered = [tx for tx in transactions if tx.date.startswith(f"{year}-{period}")]
        iva = calculate_iva_from_transactions(filtered)
        pc = calculate_pago_cuenta_from_transactions(filtered)
        total_pc = sum(pc.values(), Decimal("0.00"))
        return TaxProjection(
            total_iva=iva,
            total_pago_cuenta=total_pc,
            pago_cuenta_breakdown=pc,
            period=period,
            year=year,
        )
```

## 11. Configuration

### `src/config.py`

```python
from pydantic_settings import BaseSettings
from typing import list


class Settings(BaseSettings):
    # App
    app_version: str = "0.1.0"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None  # falls back to env/boto chain
    aws_secret_access_key: str | None = None

    # DynamoDB
    users_table_name: str = "at-sv-users"
    transactions_table_name: str = "at-sv-transactions"
    tax_declarations_table_name: str = "at-sv-tax-declarations"

    # DynamoDB endpoint (for local dev / LocalStack)
    dynamodb_endpoint_url: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

## 12. Project Files

### `pyproject.toml`

```toml
[project]
name = "at-sv-backend"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "boto3>=1.36.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
    "moto[dynamodb]>=5.0.0",
    "pytest-cov>=6.0.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.coverage.run]
source = ["src"]
```

### `Makefile`

```makefile
.PHONY: test test-unit test-integration test-e2e dev clean

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v --cov=src/domain --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v --cov=src/infrastructure --cov-report=term-missing

test-e2e:
	pytest tests/e2e/ -v --cov=src/api --cov=src/application --cov-report=term-missing

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .coverage htmlcov

install:
	pip install -e ".[dev]"
```

## 13. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| DynamoDB `TransactWriteItems` not used for UoW → no atomic multi-table writes | Medium | Documented in UoW ABC. Use-case-level consistency with idempotency keys. |
| Decimal → float coercion in JSON serialization | High | FastAPI custom JSON encoder: `json.dumps(cls=DecimalEncoder)` for all Decimal → string |
| moto doesn't 100% replicate DynamoDB behavior | Low | Flag "tested with moto" in CI; document moto limitations; add optional LocalStack integration test profile |
| No auth → any endpoint is open | High | Explicitly marked OOS. Add informational `Security` scheme in OpenAPI docs. |
