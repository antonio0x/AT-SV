# SDD Spec — Backend Core

## Metadata

- **Change**: Backend Core — Foundation Layer for AT-SV
- **Status**: Spec
- **Previous**: Proposal (`sdd/backend-core/proposal`)
- **Next**: Design (`sdd-design`)
- **Version**: 0.1.0

---

## 1. Tax Engine Spec — `backend/domain/services/tax_engine.py`

### 1.1 Module Contract

Pure functions at module level. Zero imports from `application/`, `api/`, or `infrastructure/`. No I/O, no state, no randomness. Only uses `decimal.Decimal` and Python stdlib.

### 1.2 Constants

```python
IVA_RATE: Decimal = Decimal("0.13")
PAGO_CUENTA_RATES: dict[str, Decimal] = {
    "services_general": Decimal("0.10"),
    "capital_interest": Decimal("0.05"),
    "other": Decimal("0.01"),
}
```

### 1.3 Function: `calculate_iva`

| Item | Value |
|------|-------|
| Signature | `def calculate_iva(amount: Decimal, rate: Decimal = IVA_RATE) -> Decimal` |
| Logic | `(amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` |
| Rounding | 2 decimal places, HALF_UP |
| Rate precision | Accept arbitrary precision, but quantize after multiplication |

**Scenarios:**

| # | Input amount | rate | Expected | Notes |
|---|-------------|------|----------|-------|
| 1 | `Decimal("100.00")` | `Decimal("0.13")` | `Decimal("13.00")` | Standard |
| 2 | `Decimal("0.00")` | `Decimal("0.13")` | `Decimal("0.00")` | Zero amount |
| 3 | `Decimal("9999999999.99")` | `Decimal("0.13")` | `Decimal("1299999999.9987")` truncated to `1300000000.00` | Large — verify no overflow |
| 4 | `Decimal("0.01")` | `Decimal("0.13")` | `Decimal("0.00")` | Sub-cent rounding |
| 5 | `Decimal("10.555")` | `Decimal("0.13")` | `Decimal("1.37")` | Rounding (1.37215 → 1.37) |
| 6 | `Decimal("10.555")` | `Decimal("0.1300")` | `Decimal("1.37")` | Rate may have extra trailing zeros |
| 7 | `Decimal("100.00")` | `Decimal("0.01")` | `Decimal("1.00")` | Custom rate below IVA |
| 8 | `Decimal("-100.00")` | `Decimal("0.13")` | `ValueError` | Negative amount |
| 9 | `Decimal("100.00")` | `Decimal("-0.13")` | `ValueError` | Negative rate |

**Determinism proof**: Same `(amount, rate)` → same `Decimal` across all invocations. No random, no datetime, no external call.

### 1.4 Function: `calculate_pago_cuenta`

| Item | Value |
|------|-------|
| Signature | `def calculate_pago_cuenta(amount: Decimal, rate: Decimal) -> Decimal` |
| Logic | `(amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` |
| Rate | Must be one of `PAGO_CUENTA_RATES` values (validated upstream or inside function) |
| Rounding | 2 decimal places, HALF_UP |

**Scenarios:**

| # | Input amount | rate | Expected | Notes |
|---|-------------|------|----------|-------|
| 1 | `Decimal("1000.00")` | `Decimal("0.10")` | `Decimal("100.00")` | Services 10% |
| 2 | `Decimal("1000.00")` | `Decimal("0.05")` | `Decimal("50.00")` | Capital/Interest 5% |
| 3 | `Decimal("1000.00")` | `Decimal("0.01")` | `Decimal("10.00")` | Other 1% |
| 4 | `Decimal("0.00")` | `Decimal("0.10")` | `Decimal("0.00")` | Zero amount |
| 5 | `Decimal("-500.00")` | `Decimal("0.10")` | `ValueError` | Negative amount |

### 1.5 Edge Case Matrix (both functions)

| Condition | Behaviour |
|-----------|-----------|
| `amount` is not Decimal | `TypeError` at call site (or Pydantic validation upstream) |
| `rate` is not Decimal | Same |
| `amount` is `Decimal("NaN")` or `Decimal("Inf")` | `InvalidOperation` from Decimal — document as undefined behaviour |
| Rounding halfway | Always `ROUND_HALF_UP` (commercial rounding, SV tax standard) |
| Very large `amount` (10^12) | No Python overflow; test with `Decimal("1_000_000_000_000.00")` |
| Very small `amount` (< 0.01) | Quantizes to 0.00 |

### 1.6 Test Requirements

- Module: `backend/tests/test_tax_engine.py`
- Minimum coverage: 100% of both functions (all paths, all edge cases)
- Parametrize all scenarios from tables above
- Add deterministic proof test: call same inputs 100x, assert same result

---

## 2. Domain Models Spec — `backend/domain/models/`

### 2.1 Conventions

- All models: Pydantic v2 `BaseModel`, `frozen=True` where immutable after creation
- All `Decimal` fields validated via `AfterValidator` to ensure no `NaN`/`Inf`
- All string fields trimmed via `strip()` validator
- UUID fields stored as `str` (UUID hex) for DynamoDB compatibility
- `created_at` always `datetime.now(timezone.utc)` unless explicitly set

### 2.2 User Model — `backend/domain/models/user.py`

**Fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | `str` (UUID4) | Yes | Auto-generated. Length 36 |
| `email` | `str` | Yes | Regex `.+\@.+\..+`, max 255, lowercase |
| `business_name` | `str` | Yes | Min 1, max 255 |
| `business_type` | `str` | Yes | One of: `persona_natural`, `persona_juridica`, `otro` |
| `nit` | `str` | Yes | 14-digit format: `XXXX-XXXXXX-XXX-X` (regex verified) |
| `nrc` | `str` | Yes | 8-digit format: `XXXXXX-XX` |
| `regimen_fiscal` | `str` | Yes | One of: `general`, `simplificado` |
| `created_at` | `datetime` | Yes | UTC, default `now` |

**NIT Format Validation:**
```
Pattern: ^(\d{4})-(\d{6})-(\d{3})-(\d{1})$
```
- Digits only in each group
- Length exactly 17 chars including hyphens
- Last digit is check digit (store as-is; verification is future scope)

**Validation Rules (via `@field_validator`):**
- `email`: lowercase and strip
- `nit`: strip whitespace, must match pattern
- `nrc`: strip whitespace, must match `^\d{6}-\d{2}$`
- All `min_length`/`max_length` enforced at Pydantic level

### 2.3 Transaction Model — `backend/domain/models/transaction.py`

**Fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | `str` (UUID4) | Yes | Auto-generated |
| `user_id` | `str` | Yes | Valid UUID |
| `type` | `str` | Yes | Enum: `income`, `expense` |
| `amount` | `Decimal` | Yes | Max digits 18, scale 2 |
| `category` | `str` | Yes | Enum below |
| `description` | `str` | No | Max 500 |
| `date` | `date` | Yes | `YYYY-MM-DD` |
| `iva_rate` | `Decimal` | Yes | Default `Decimal("0.13")` |
| `created_at` | `datetime` | Yes | UTC, default `now` |

**Category Enum:**
```
sales, services, purchases, salaries, rent, utilities, taxes,
professional_fees, supplies, equipment, other_income, other_expense
```

**Validation Rules:**
- `amount` must be > 0 (positive). Use `gt=0` on Pydantic field
- `type` must be exactly `income` or `expense`
- `category` must be one of pre-defined enum
- `date` cannot be in the future (warning vs error — spec says warn for > today, error for > 1 year from now)

### 2.4 TaxDeclaration Model — `backend/domain/models/tax_declaration.py`

**Fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | `str` (UUID4) | Yes | Auto-generated |
| `user_id` | `str` | Yes | Valid UUID |
| `form_type` | `str` | Yes | Enum: `F-07`, `F-14`, `F-06` |
| `period` | `int` | Yes | 1–12 (month) |
| `year` | `int` | Yes | 2020–2030 |
| `total_iva` | `Decimal` | Yes | Default 0.00, scale 2 |
| `total_renta` | `Decimal` | Yes | Default 0.00, scale 2 |
| `status` | `str` | Yes | Enum: `draft`, `submitted` |
| `created_at` | `datetime` | Yes | UTC, default `now` |

**Validation Rules:**
- `period` must be 1–12
- `year` must be 2020–2030
- `total_iva` >= 0
- `total_renta` >= 0

---

## 3. Repository Interfaces Spec — `backend/domain/interfaces/`

### 3.1 Location & Conventions

- Module: `backend/domain/interfaces/repository.py`, `backend/domain/interfaces/unit_of_work.py`
- All repositories are `ABC` with `@abstractmethod`
- All methods are `async`
- Domain models are used as input/output (not raw dicts)
- `None` returned when entity not found (no exceptions for not-found)
- `list` returns are `list[Model]` (empty list, not None)

### 3.2 UserRepository — `backend/domain/interfaces/repository.py`

```python
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user. Raises DuplicateEmailError if email exists."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        """Find by primary key."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Find by email via GSI."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Full replace. Raises NotFoundError if user_id missing."""
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """Delete by PK. No-op if not found."""
        ...
```

**Custom Exceptions** (defined in same file or `backend/domain/interfaces/exceptions.py`):

```python
class DuplicateEmailError(Exception):
    """Email already registered."""
    ...

class NotFoundError(Exception):
    """Entity not found."""
    ...
```

### 3.3 TransactionRepository — `backend/domain/interfaces/repository.py`

```python
class TransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        ...

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Transaction], int]:
        """Returns (items, total_count). Paginated by GSI on user_id+created_at."""
        ...

    @abstractmethod
    async def update(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def delete(self, transaction_id: str) -> None:
        ...
```

### 3.4 UnitOfWork Protocol — `backend/domain/interfaces/unit_of_work.py`

```python
class UnitOfWork(ABC):
    """Async context manager for transaction scope."""

    users: UserRepository
    transactions: TransactionRepository

    @abstractmethod
    async def __aenter__(self) -> Self:
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Rollback on exception, commit otherwise."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...
```

No DynamoDB-specific patterns leak into the interface. The UoW is a protocol — infrastructure implements it.

---

## 4. DynamoDB Infrastructure Spec — `backend/infrastructure/`

### 4.1 Database Setup — `backend/infrastructure/database.py`

```python
import boto3
from decimal import Decimal

dynamodb: boto3.resources.base.ServiceResource | None = None

def get_dynamodb() -> boto3.resources.base.ServiceResource:
    global dynamodb
    if dynamodb is None:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            # endpoint_url from env for LocalStack
            endpoint_url=os.getenv("DYNAMODB_ENDPOINT"),
        )
    return dynamodb

def get_table(table_name: str) -> boto3.resources.factory.dynamodb.Table:
    return get_dynamodb().Table(table_name)
```

**Environment Variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `AWS_REGION` | `us-east-1` | AWS region |
| `DYNAMODB_ENDPOINT` | `None` | LocalStack endpoint |
| `USERS_TABLE` | `users` | Users DynamoDB table name |
| `TRANSACTIONS_TABLE` | `transactions` | Transactions table name |
| `TAX_DECLARATIONS_TABLE` | `tax_declarations` | Tax declarations table name |

### 4.2 Table Schemas

#### Users Table

| Attribute | Key Type | Type | Notes |
|-----------|----------|------|-------|
| `user_id` | HASH (PK) | String | UUID4 |
| `email` | GSI HASH | String | GSI name: `email_index` |
| `business_name` | — | String | |
| `business_type` | — | String | Enum stored as string |
| `nit` | — | String | With hyphens |
| `nrc` | — | String | With hyphen |
| `regimen_fiscal` | — | String | Enum stored as string |
| `created_at` | — | String | ISO 8601 UTC |

**GSI: `email_index`**
- HASH: `email`
- Projection: ALL (keys + attributes)

#### Transactions Table

| Attribute | Key Type | Type | Notes |
|-----------|----------|------|-------|
| `transaction_id` | HASH (PK) | String | UUID4 |
| `user_id` | GSI HASH | String | GSI: `user_transactions` |
| `created_at` | GSI RANGE | String | ISO 8601 UTC (sort key for pagination) |
| `type` | — | String | `income`/`expense` |
| `amount` | — | Number | Stored as DynamoDB Number (Decimal via TypeSerializer) |
| `category` | — | String | Enum stored as string |
| `description` | — | String | Optional |
| `date` | — | String | ISO date `YYYY-MM-DD` |
| `iva_rate` | — | Number | Decimal stored as Number |

**GSI: `user_transactions`**
- HASH: `user_id`
- RANGE: `created_at`
- Projection: ALL

#### Tax Declarations Table

| Attribute | Key Type | Type | Notes |
|-----------|----------|------|-------|
| `declaration_id` | HASH (PK) | String | UUID4 |
| `user_id` | GSI HASH | String | GSI: `user_declarations` |
| `period` | GSI RANGE | Number | 1–12 |
| `form_type` | — | String | `F-07`/`F-14`/`F-06` |
| `year` | — | Number | |
| `total_iva` | — | Number | Decimal → DynamoDB Number |
| `total_renta` | — | Number | Decimal → DynamoDB Number |
| `status` | — | String | `draft`/`submitted` |
| `created_at` | — | String | ISO 8601 UTC |

**GSI: `user_declarations`**
- HASH: `user_id`
- RANGE: `period`
- Projection: ALL

### 4.3 Decimal Serialization Strategy

**Problem**: DynamoDB's `Decimal` type doesn't handle Python `decimal.Decimal` natively via `TypeSerializer`. boto3 uses its own serialization: Python `Decimal` → DynamoDB `{"N": "string_value"}`. This works, but on deserialization, DynamoDB returns `Decimal` objects from boto3's `TypeDeserializer` — however they are boto3 `Decimal`s, not `decimal.Decimal`.

**Approach**: Custom `TypeSerializer` subclass that:
- Accepts Python `decimal.Decimal` as-is in `encode_number`
- On decode (via `TypeDeserializer`), converts boto3 Decimal → Python `decimal.Decimal`

```python
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

class DecimalTypeSerializer(TypeSerializer):
    def _is_number(self, value):
        return isinstance(value, (int, float, Decimal))

class DecimalTypeDeserializer(TypeDeserializer):
    def _deserialize_n(self, value):
        return Decimal(value)
```

These live in `backend/infrastructure/database.py` for easy import.

**Alternative (simpler)**: Use boto3's built-in serialization with `decimal.Decimal` but:
1. Before writing: call `int(amount * 100)` or store as string. **Rejected** — loses precision control.
2. Use DynamoDB's Number type directly with boto3 `TypeSerializer`. **Chosen** — simplest, boto3-native.

### 4.4 Repository Implementations

#### `DynamoDBUserRepo`

Located: `backend/infrastructure/repositories/user_repo.py`

- Receives table name via `__init__` (or uses env var default)
- `create`: `table.put_item(Item=item, ConditionExpression="attribute_not_exists(user_id)")`
- `get_by_id`: `table.get_item(Key={"user_id": user_id})` → deserialize to User
- `get_by_email`: `table.query(IndexName="email_index", KeyConditionExpression=Key("email").eq(email))`
- `update`: `table.put_item(Item=item)` (full replace)
- `delete`: `table.delete_item(Key={"user_id": user_id})`

`create` uses `ConditionExpression` to detect duplicates → catches `ConditionalCheckFailedException` and re-raises as `DuplicateEmailError`.

#### `DynamoDBTransactionRepo`

Located: `backend/infrastructure/repositories/transaction_repo.py`

- `create`: `table.put_item(Item=item)`
- `get_by_id`: `table.get_item(Key={"transaction_id": transaction_id})`
- `get_by_user_id`: `table.query(
    IndexName="user_transactions",
    KeyConditionExpression=Key("user_id").eq(user_id),
    Limit=limit,
    ExclusiveStartKey=last_evaluated_key from page calculation,
    ScanIndexForward=False
  )`
  - **Pagination**: DynamoDB does NOT support page number natively. Implementation must use `page` + `limit` to calculate offset by scanning forward. Strategy:
    1. For simple pagination: `ScanIndexForward=False` + `Limit=limit`, collect `LastEvaluatedKey`
    2. Compute offset: `skip = (page - 1) * limit`
    3. If `skip > 0`, query without limit, skip `skip` items, then re-query with limit.
    4. Alternative: use `start_key` URL parameter instead of page. **Spec chooses: page-based is simpler for frontend but has O(n) skip cost. Accept for now; document performance warning.**
  - Total count: use `Select="COUNT"` query (no items) with same key condition.
- `update`: `table.put_item(Item=item)`
- `delete`: `table.delete_item(Key={"transaction_id": transaction_id})`

---

## 5. API/BFF Spec — `backend/api/`

### 5.1 BFF Response Wrapper — `backend/api/bff/response.py`

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")
ErrorT = TypeVar("ErrorT")

class BFFMeta(BaseModel):
    page: int | None = None
    total: int | None = None
    limit: int | None = None

class BFFResponse(BaseModel, Generic[T]):
    data: T
    meta: BFFMeta = BFFMeta()
    errors: list[str] = []
```

**Error response** (non-generic):
```python
class BFFErrorResponse(BaseModel):
    data: None = None
    meta: BFFMeta = BFFMeta()
    errors: list[str]
```

### 5.2 BFF Schemas — `backend/api/bff/schemas.py`

#### UserBFF

```python
class UserBFF(BaseModel):
    id: str
    email: str
    business_name: str
    business_type: str
    nit: str
    nrc: str
    regimen_fiscal: str
    created_at: str  # ISO 8601
```

#### UserCreate

```python
class UserCreate(BaseModel):
    email: str
    business_name: str
    business_type: str
    nit: str
    nrc: str
    regimen_fiscal: str
```

#### TransactionBFF

```python
class TransactionBFF(BaseModel):
    id: str
    user_id: str
    type: str
    amount: str  # Decimal as string for frontend
    category: str
    description: str | None
    date: str  # YYYY-MM-DD
    iva_rate: str
    iva_amount: str  # Computed by tax engine
    created_at: str
```

#### TransactionCreate

```python
class TransactionCreate(BaseModel):
    user_id: str
    type: str
    amount: Decimal
    category: str
    description: str | None = None
    date: date
    iva_rate: Decimal | None = Decimal("0.13")
```

#### TaxProjectionBFF

```python
class TaxPeriodSummary(BaseModel):
    period: int
    total_income: str
    total_expenses: str
    net_iva: str  # IVA debit - IVA credit
    iva_debit: str   # Sum of IVA on income
    iva_credit: str  # Sum of IVA on expenses

class TaxProjectionBFF(BaseModel):
    user_id: str
    year: int
    periods: list[TaxPeriodSummary]
    annual_summary: TaxPeriodSummary  # Aggregated totals
    pago_cuenta_total: str  # Sum of all pagos a cuenta
```

> **Note**: All `Decimal` values in BFF responses are serialized as `str` to avoid JavaScript float precision loss.

### 5.3 Routes

#### GET `/health`

**Handler**: `backend/api/routes/health.py`

**Response**:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-06-11T22:00:00Z"
}
```

#### POST `/api/v1/users`

**Handler**: `RegisterUser` use case → `BFFResponse<UserBFF>`

**Request Body**: `UserCreate`

**Responses**:
- 201: `BFFResponse<UserBFF>` — user created
- 409: `BFFErrorResponse` — duplicate email
- 422: `BFFErrorResponse` — validation error

#### GET `/api/v1/users/{user_id}`

**Handler**: Get user by ID

**Responses**:
- 200: `BFFResponse<UserBFF>`
- 404: `BFFErrorResponse`

#### GET `/api/v1/users/email/{email}`

**Handler**: Get user by email

**Responses**:
- 200: `BFFResponse<UserBFF>`
- 404: `BFFErrorResponse`

#### POST `/api/v1/transactions`

**Handler**: `RecordTransaction` use case → `BFFResponse<TransactionBFF>`

**Request Body**: `TransactionCreate`

**Responses**:
- 201: `BFFResponse<TransactionBFF>`
- 422: `BFFErrorResponse`

#### GET `/api/v1/transactions/{transaction_id}`

**Responses**:
- 200: `BFFResponse<TransactionBFF>`
- 404: `BFFErrorResponse`

#### GET `/api/v1/transactions`

**Query Parameters**:
- `user_id` (required, str)
- `page` (optional, int, default 1)
- `limit` (optional, int, default 50, max 100)

**Responses**:
- 200: `BFFResponse<list<TransactionBFF>>` with `meta.page`, `meta.total`, `meta.limit`
- 422: `BFFErrorResponse`

#### GET `/api/v1/taxes/projection`

**Query Parameters**:
- `user_id` (required, str)
- `year` (required, int)
- `period` (optional, int, 1–12, if provided returns single period + annual summary)

**Responses**:
- 200: `BFFResponse<TaxProjectionBFF>`
- 404: `BFFErrorResponse` — no transactions found
- 422: `BFFErrorResponse`

### 5.4 Error Handling Strategy

- **422 Validation Errors**: FastAPI's default `RequestValidationError` → custom handler that transforms to `BFFErrorResponse`
- **404 Not Found**: Repository returns `None` → route handler converts to `BFFErrorResponse`
- **409 Duplicate**: Repository raises `DuplicateEmailError` → route handler catches, returns 409
- **500 Internal**: Global exception handler → logs trace, returns 500 with `BFFErrorResponse`
- **BFF Layer Only**: All error responses use `BFFErrorResponse` shape

---

## 6. Use Cases Spec — `backend/application/use_cases/`

### 6.1 Conventions

- Each use case is a callable class (or standalone function with `async def __call__`)
- Receives repositories via DI (constructor injection)
- Returns BFF response schemas (already transformed to frontend-optimized shape)
- Handles validation + business logic + transformation
- Exceptions propagate to API layer for error handling

### 6.2 RegisterUser — `backend/application/use_cases/register_user.py`

**Input**: `UserCreate` (BFF schema)

**Flow**:
1. Validate `UserCreate` using Pydantic (FastAPI does this automatically)
2. Construct domain `User` model (generate `id` via uuid4)
3. Call `self.repo.create(user)` → catches `DuplicateEmailError`
4. Transform `User` → `UserBFF` (dates to ISO string, model_dump)
5. Return `BFFResponse<UserBFF>`

**Edge Cases**:
- Email already exists → let `DuplicateEmailError` propagate (handled by API layer)
- NIT/NRC format → validated at domain model level

### 6.3 RecordTransaction — `backend/application/use_cases/record_transaction.py`

**Input**: `TransactionCreate` (BFF schema)

**Flow**:
1. Validate `TransactionCreate`
2. Verify `user_id` exists via `self.user_repo.get_by_id(user_id)` → `NotFoundError` if missing
3. Call `tax_engine.calculate_iva(amount, iva_rate)` → get `iva_amount`
4. If transaction type is income AND category requires pago a cuenta (configurable): call `tax_engine.calculate_pago_cuenta(amount, rate)`
5. Construct domain `Transaction` model with computed IVA
6. Call `self.tx_repo.create(transaction)`
7. Transform `Transaction` → `TransactionBFF` (Decimal serialized as str)
8. Return `BFFResponse<TransactionBFF>`

**Tax Engine Invocation Detail**:
```python
iva_amount = calculate_iva(transaction.amount, transaction.iva_rate)
```

### 6.4 GetTaxProjection — `backend/application/use_cases/get_tax_projection.py`

**Input**: `user_id: str, year: int, period: int | None`

**Flow**:
1. Verify user exists via `user_repo.get_by_id(user_id)` → raise `NotFoundError` if None
2. Load all transactions for user + year:
   - Call `tx_repo.get_by_user_id(user_id, limit=1000)` (or paginate internally)
   - Filter by year (use `date` field range, or rely on GSI)

3. **Accumulation Logic** (pure function in use case or domain service):

```python
per_period: dict[int, dict] = {}
for tx in transactions:
    p = tx.date.month
    if period is not None and p != period:
        continue
    if p not in per_period:
        per_period[p] = {"income": ZERO, "expenses": ZERO, "iva_debit": ZERO, "iva_credit": ZERO}

    if tx.type == "income":
        per_period[p]["income"] += tx.amount
        per_period[p]["iva_debit"] += (tx.amount * tx.iva_rate).quantize(...)
    elif tx.type == "expense":
        per_period[p]["expenses"] += tx.amount
        per_period[p]["iva_credit"] += (tx.amount * tx.iva_rate).quantize(...)
```

4. Compute `net_iva = iva_debit - iva_credit` per period
5. Compute pago a cuenta per income transaction (using `PAGO_CUENTA_RATES`)
6. Build `TaxPeriodSummary` per period, plus annual aggregation
7. Return `BFFResponse<TaxProjectionBFF>`

**Performance Warning**: Without a proper year-range query on the GSI, this loads ALL user transactions and filters in-memory. Spec requires a composite SK on GSI that enables `created_at BETWEEN` or date-range filtering. If `date` is different from `created_at`, the GSI must change. **Decision**: Use `created_at` year extraction as first pass; explicitly document that year-based filtering is done in-memory for v1, and a date-range GSI should be added in v2.

---

## Scenarios & Acceptance

### Scenario 1: Register User Flow
1. Send POST `/api/v1/users` with valid `UserCreate` body
2. Response: 201 with `BFFResponse<UserBFF>`, includes `id` and ISO `created_at`
3. Send same POST again → 409 with `BFFErrorResponse`
4. Invalidate NIT (wrong format) → 422 with `BFFErrorResponse`

### Scenario 2: Record Transaction with IVA
1. Send POST `/api/v1/transactions` with `TransactionCreate` (amount: 100.00, type: income)
2. Response: 201 with `TransactionBFF`, `iva_amount: "13.00"`
3. Query GET `/api/v1/transactions/{id}` → same data returned

### Scenario 3: Tax Projection Aggregation
1. Record 2 income transactions ($1000 each, IVA 13%) for January
2. Record 1 expense transaction ($500, IVA 13%) for January
3. GET `/api/v1/taxes/projection?user_id=X&year=2026`
4. Response: January period: income=2000.00, expenses=500.00, iva_debit=260.00, iva_credit=65.00, net_iva=195.00

### Scenario 4: Pagination
1. Record 25 transactions for same user
2. GET `/api/v1/transactions?user_id=X&page=1&limit=10` → 10 items, meta.total=25
3. GET `/api/v1/transactions?user_id=X&page=2&limit=10` → 10 items (items 11–20)
4. GET `/api/v1/transactions?user_id=X&page=3&limit=10` → 5 items

### Scenario 5: Error Propagation
1. GET `/api/v1/users/nonexistent-uuid` → 404 with `BFFErrorResponse`
2. POST `/api/v1/transactions` without body → 422 with `BFFErrorResponse`
3. GET `/api/v1/taxes/projection` without `user_id` → 422 with `BFFErrorResponse`

### Scenario 6: Health Check
1. GET `/health` → `{status: "ok", version: "0.1.0", timestamp: "..."}`
2. Status code 200

---

## Implementation Notes

- `pyproject.toml` uses `src/` layout: NO. Project root is `backend/`, tests at `backend/tests/`.
- FastAPI app created in `backend/api/app.py`, include routers from `backend/api/routes/`.
- Middleware: CORS enabled for development (frontend on localhost:5173).
- Startup: `@app.on_event("startup")` initializes DynamoDB connection.
- `.env.example` includes all env vars with sane defaults for LocalStack.

## .env.example

```bash
AWS_REGION=us-east-1
DYNAMODB_ENDPOINT=http://localhost:4566
USERS_TABLE=users
TRANSACTIONS_TABLE=transactions
TAX_DECLARATIONS_TABLE=tax_declarations
```

## Makefile Targets

```makefile
install:
	pip install -e ".[dev]"

test:
	pytest --cov=domain --cov=api --cov=application --cov-report=term-missing

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .

localstack:
	docker compose up -d localstack
```

## pyproject.toml dependencies

```toml
[project]
name = "at-sv-backend"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "fastapi>=0.115.0,<1.0.0",
    "uvicorn[standard]>=0.34.0,<1.0.0",
    "pydantic>=2.10.0,<3.0.0",
    "pydantic-settings>=2.0.0,<3.0.0",
    "boto3>=1.36.0,<2.0.0",
    "python-dotenv>=1.0.0,<2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3,<9.0",
    "pytest-asyncio>=0.25,<1.0",
    "pytest-cov>=6.0,<7.0",
    "httpx>=0.28,<1.0",
    "ruff>=0.9.0,<1.0.0",
]
```

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DynamoDB page-based pagination is O(n) skip | High | Medium | Document performance warning; accept for v1; consider `start_key`-based in v2 |
| Year filtering on transactions loads all data | Medium | Medium | Document as v1 limitation; add date-range GSI in v2 |
| Decimal serialization mismatch (boto3 vs Python) | Medium | High | Custom TypeSerializer; integration test with LocalStack |
| No auth on endpoints | High | High | Explicitly documented; Pydantic validation as first gate; auth is next change |
| FastAPI 422 vs domain validation collision | Low | Low | Custom exception handler coalesces both into BFFErrorResponse |
