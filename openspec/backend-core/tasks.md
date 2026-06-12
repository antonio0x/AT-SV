# SDD Tasks — Backend Core Foundation Layer

## Metadata

- **Change**: Backend Core — Foundation Layer for AT-SV
- **Phase**: Tasks
- **Previous**: Design (`sdd/backend-core/design`)
- **Next**: Apply (`sdd-apply`)
- **Version**: 0.1.0

---

## Architecture Decision: Package Structure

The design specifies `backend/src/` as the Python package root (configurable via `pythonpath = ["src"]` in pyproject.toml). The user's original task outline used `backend/domain/`, `backend/api/` etc., but those are relative to the package root. All source paths below are RELATIVE to `backend/`:

| Layer | Path (relative to `backend/`) |
|-------|-------------------------------|
| Source root | `src/` |
| API/BFF | `src/api/` |
| Application | `src/application/` |
| Domain | `src/domain/` |
| Infrastructure | `src/infrastructure/` |
| Tests | `tests/` (flat) |

This resolves the discrepancy between the user's flat-list structure and the design's `src/`-based layout. The `pythonpath = ["src"]` setting in pyproject.toml ensures all `from src.xxx` imports work in both production and tests.

---

## Task Dependency Graph

```
T1 (Scaffolding)
 ├── T2 (Domain Models)
 │    ├── T4 (Repository Interfaces)
 │    │    ├── T6 (DynamoDB Repos) ──┐
 │    │    └── T7 (Use Cases) ───────┤
 │    └── T8 (BFF Layer) ────────────┤
 │                                   ├── T9 (API Routes) ──┐
 ├── T3 (Tax Engine) ──── T7 ────────┘                     │
 │                                                          ├── T11 (Integ. Tests)
 └── T5 (DynamoDB Infra) ─── T6 ───────────────────────────┘

T10 (Unit Tests) ──── depends on T3, T2, T8 (parallel to T9-T11)
```

**Parallelizable groups**:
- Group A: T1 only (must go first)
- Group B: T2, T3, T5 (independent of each other, after T1)
- Group C: T4 (after T2), T8 (after T2)
- Group D: T6 (after T4+T5), T7 (after T3+T4)
- Group E: T9 (after T6+T7+T8)
- Group F: T10 (after T2+T3+T8), T11 (after T6+T9) — parallel

---

## Task Breakdown

### T1 — Project Scaffolding

**Files to create:**
- `backend/pyproject.toml` — project metadata, all dependencies (fastapi, uvicorn, pydantic, pydantic-settings, boto3, python-dotenv), optional dev deps (pytest, pytest-asyncio, httpx, moto[dynamodb], pytest-cov), tool config (pytest: asyncio_mode=auto, testpaths=tests, pythonpath=src; coverage: source=src)
- `backend/Makefile` — targets: install, test, test-unit, test-integration, test-e2e, dev, clean, lint, format (ruff)
- `backend/.env.example` — AWS_REGION, DYNAMODB_ENDPOINT, table names, CORS origins
- `backend/src/__init__.py` — empty
- `backend/src/config.py` — `Settings(BaseSettings)` with pydantic-settings: app_version, debug, cors_origins, aws_region, table names, dynamodb_endpoint_url. Singleton `settings = Settings()`.

**What to implement:**
- pyproject.toml with exact version pins from the design
- Makefile with ruff lint/format (ruff check, ruff format)
- Settings class with `model_config = {"env_file": ".env"}` and `.env.example` as reference
- All `__init__.py` files for the package tree: `src/`, `src/domain/`, `src/application/`, `src/infrastructure/`, `src/api/`, `src/api/bff/`, `src/api/routes/`, `tests/`

**Dependencies:** None (first task)

**Complexity:** S

**Effort:** ~80–100 lines

**Test strategy:** N/A (infrastructure). Verify: `pip install -e ".[dev]"` succeeds; `python -c "from src.config import settings; print(settings.app_version)"` works.

---

### T2 — Domain Models

**Files to create:**
- `backend/src/domain/models/__init__.py`
- `backend/src/domain/models/user.py` — User model
- `backend/src/domain/models/transaction.py` — Transaction model
- `backend/src/domain/models/tax_declaration.py` — TaxDeclaration model

**What to implement:**
- **User**: Pydantic v2 `BaseModel` with fields: id (UUID str), email (regex validated), business_name, business_type (enum: persona_natural, persona_juridica, otro), nit (regex `^\d{4}-\d{6}-\d{3}-\d{1}$`), nrc (regex `^\d{6}-\d{2}$`), regimen_fiscal (enum: general, simplificado), created_at (datetime UTC). Validators: email lowercase+strip, nit/nrc strip, business_type enum, regimen_fiscal enum.
- **Transaction**: Fields: id (UUID str), user_id (UUID str), type (enum: income, expense), amount (Decimal, gt=0, max_digits=18, decimal_places=2), category (enum with 12 values), description (optional, max 500), date (date), iva_rate (Decimal, default 0.13), created_at (datetime UTC). Validators: date not in future (warn), amount > 0 via `gt=0`.
- **TaxDeclaration**: Fields: id (UUID str), user_id (UUID str), form_type (enum: F-07, F-14, F-06), period (int 1-12), year (int 2020-2030), total_iva (Decimal >= 0), total_renta (Decimal >= 0), status (enum: draft, submitted), created_at (datetime UTC).

All models use `frozen=True`, Decimal fields validated for NaN/Inf via AfterValidator, string fields trimmed.

**Dependencies:** T1

**Complexity:** M

**Effort:** ~200–280 lines

**Test strategy:** Pydantic validation unit tests in T10. Verify: valid/invalid NIT, NRC, email formats, enum constraints, Decimal precision, field defaults.

---

### T3 — Tax Engine (Pure Functions)

**Files to create:**
- `backend/src/domain/services/__init__.py`
- `backend/src/domain/services/tax_engine.py`

**What to implement:**
- **Constants**: `IVA_RATE = Decimal("0.13")`, `PagoCuentaCategory` enum (SERVICIOS_PROFESIONALES, ARRENDAMIENTO, OTROS_SERVICIOS, COMPRA_BIENES), `PAGO_CUENTA_RATES` dict mapping enum→Decimal rates (0.10, 0.05, 0.01, 0.01)
- **`calculate_iva(amount: Decimal, rate: Decimal = IVA_RATE) -> Decimal`**: `(amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`, negative amount → `Decimal("0.00")` (clamped, per SV regulation)
- **`calculate_pago_cuenta(amount: Decimal, category: PagoCuentaCategory) -> Decimal`**: Look up rate from PAGO_CUENTA_RATES, multiply and quantize. Unknown category → 1% fallback. Negative amount → 0.00.
- **`calculate_iva_from_transactions(transactions: list[dict]) -> Decimal`**: Sum IVA across transaction dicts with `amount` and `iva_rate` keys.
- **`calculate_pago_cuenta_from_transactions(transactions: list[dict], category_key: str = "category") -> dict[PagoCuentaCategory, Decimal]`**: Group by category, sum pago cuenta per category.
- **`TaxProjection` dataclass**: total_iva, total_pago_cuenta, pago_cuenta_breakdown, period, year.

Zero imports from application/, api/, or infrastructure/. Pure Decimal + stdlib only.

**Dependencies:** T1

**Complexity:** S

**Effort:** ~80–120 lines

**Test strategy:** Exhaustive parametrized tests in T10. All edge case matrix entries, 100% branch coverage, determinism proof (same inputs 100x → same output).

---

### T4 — Repository Interfaces (ABCs)

**Files to create:**
- `backend/src/domain/interfaces/__init__.py`
- `backend/src/domain/interfaces/repository.py` — UserRepository, TransactionRepository, custom exceptions
- `backend/src/domain/interfaces/unit_of_work.py` — UnitOfWork ABC

**What to implement:**
- **UserRepository(ABC)**: `create(user: UserCreate) -> User`, `get_by_id(user_id: str) -> User | None`, `get_by_email(email: str) -> User | None`, `update(user_id: str, updates: UserUpdate) -> User | None`, `delete(user_id: str) -> bool`. All async.
- **TransactionRepository(ABC)**: `create(tx: TransactionCreate) -> Transaction`, `get_by_id(tx_id: str) -> Transaction | None`, `get_by_user(user_id: str, page: int = 1, limit: int = 20) -> tuple[list[Transaction], int]`, `update(tx_id: str, updates: dict) -> Transaction | None`, `delete(tx_id: str) -> bool`. All async.
- **Custom Exceptions** (same file): `DuplicateEmailError`, `NotFoundError`, `DomainError(code, message)`.
- **UnitOfWork(ABC)**: Properties `users: UserRepository`, `transactions: TransactionRepository`. Async context manager protocol with `commit()` and `rollback()`.

Note: Repository methods accept domain Create/Update schemas (not raw dicts). Domain models used as return types.

**Dependencies:** T2 (domain model types in signatures)

**Complexity:** S

**Effort:** ~80–100 lines

**Test strategy:** N/A (pure ABCs, no runtime behavior). Verify: abstract methods raise `TypeError` on instantiation, all signatures match spec.

---

### T5 — DynamoDB Infrastructure

**Files to create:**
- `backend/src/infrastructure/__init__.py`
- `backend/src/infrastructure/database.py`

**What to implement:**
- **`get_dynamodb_client()`**: Cached (lru_cache) boto3.client("dynamodb") with region from Settings, optional endpoint_url from DYNAMODB_ENDPOINT env var.
- **`get_table(table_name: str)`**: boto3.resource("dynamodb").Table(name) — per-call (resource is lightweight, but could cache at client level).
- **`item_to_dict(item: dict) -> dict`**: Convert DynamoDB raw item (AttributeValue format) to plain dict using boto3's TypeDeserializer. Decimal values become Python `decimal.Decimal`.
- **`DecimalTypeSerializer` and `DecimalTypeDeserializer`**: Custom subclasses for consistent Decimal handling (boto3's TypeSerializer accepts Python Decimal as Number type; TypeDeserializer returns boto3 Decimal → converted back to Python Decimal).

**Dependencies:** T1 (config/Settings imports)

**Complexity:** S

**Effort:** ~50–70 lines

**Test strategy:** Integration tests in T11 with moto mock. Verify: table creation, basic put/get with Decimal round-trip.

---

### T6 — DynamoDB Repository Implementations

**Files to create:**
- `backend/src/infrastructure/repositories/__init__.py`
- `backend/src/infrastructure/repositories/user_repo.py` — DynamoDBUserRepo
- `backend/src/infrastructure/repositories/transaction_repo.py` — DynamoDBTransactionRepo

**What to implement:**
- **DynamoDBUserRepo**: Constructor takes `table: dynamodb.Table`. Methods:
  - `create`: `put_item` with `ConditionExpression="attribute_not_exists(user_id)"` → catches `ConditionalCheckFailedException` → re-raises as `DuplicateEmailError`
  - `get_by_id`: `get_item` → deserialize to User (unwrap `Item` key, handle missing)
  - `get_by_email`: `query(IndexName="email_index", ...)` → return first or None
  - `update`: `put_item` with full replace (User → dict, includes all fields)
  - `delete`: `delete_item` → return True if item existed (check response attributes)
- **DynamoDBTransactionRepo**: Same pattern. Methods:
  - `get_by_user`: `query(IndexName="user_transactions")` with page/limit → page-based pagination using skip-then-query (O(n) skip, documented performance warning). Total count via `Select="COUNT"` query.
  - All CRUD follow same pattern as User repo
  - Decimal fields serialize via `quantize(Decimal("0.01"))` before write
  - ISO 8601 string conversion for datetime fields

**Dependencies:** T4 (interfaces to implement), T5 (DynamoDB client/table factory)

**Complexity:** M

**Effort:** ~200–300 lines

**Test strategy:** Integration tests in T11 with moto mock. Verify: CRUD round-trips, GSI queries, pagination, decimal precision preservation, duplicate email detection.

---

### T7 — Use Cases

**Files to create:**
- `backend/src/application/__init__.py`
- `backend/src/application/use_cases/__init__.py`
- `backend/src/application/use_cases/register_user.py` — RegisterUserUseCase
- `backend/src/application/use_cases/record_transaction.py` — RecordTransactionUseCase
- `backend/src/application/use_cases/get_tax_projection.py` — GetTaxProjectionUseCase

**What to implement:**
- **RegisterUserUseCase**: Constructor receives `UserRepository`. `__call__(data: UserCreate) -> User`: check email uniqueness via repo.get_by_email → raise DomainError if exists, else build User domain model with uuid4 id and UTC created_at, call repo.create, return User.
- **RecordTransactionUseCase**: Constructor receives `TransactionRepository`, `UserRepository`. `__call__(data: TransactionCreate) -> Transaction`: verify user exists (get_by_id → NotFoundError if None), calculate IVA via tax_engine.calculate_iva, optionally calculate pago_cuenta for income with applicable category, build Transaction domain model with uuid4 id and UTC created_at, call repo.create, return Transaction.
- **GetTaxProjectionUseCase**: Constructor receives `TransactionRepository`, `UserRepository`. `__call__(user_id, year, period=None) -> TaxProjection`: verify user exists, load transactions via repo.get_by_user (limit=9999), filter by year (in-memory, documented v1 limitation), accumulate per-period: income sum, expense sum, IVA debit/credit via calculate_iva, pago_cuenta_total. Build TaxProjection with per-period breakdown and annual summary.

All use cases are callable classes (async `__call__`). Constructor injection for dependencies.

**Dependencies:** T3 (tax engine for RecordTransaction, GetTaxProjection), T4 (repository interfaces)

**Complexity:** M

**Effort:** ~150–200 lines

**Test strategy:** Unit tests with mocked repos (via E2E tests in T11, or standalone with unittest.mock). Verify: happy path, user-not-found (404), duplicate email (409), empty projection (zero amounts).

---

### T8 — BFF Response Layer

**Files to create:**
- `backend/src/api/bff/__init__.py`
- `backend/src/api/bff/response.py` — BFFResponse, ResponseMeta, ErrorDetail, PaginationMeta
- `backend/src/api/bff/schemas.py` — BFF request/response schemas and domain→BFF transformers

**What to implement:**
- **response.py**:
  - `ErrorDetail(BaseModel)`: code (str), message (str), field (Optional[str])
  - `PaginationMeta(BaseModel)`: page, limit, total, has_next (bool)
  - `ResponseMeta(BaseModel)`: request_id (str), version (str), pagination (Optional[PaginationMeta])
  - `BFFResponse(BaseModel, Generic[T])`: data (Optional[T]), meta (ResponseMeta), errors (list[ErrorDetail])
  - `BFFResponse.success(data, meta)` and `BFFResponse.error(meta, errors)` classmethods

- **schemas.py**:
  - **Request schemas**: UserCreateRequest, UserUpdateRequest, TransactionCreateRequest (all Pydantic)
  - **Response schemas**: UserBFF (id, email, business_name, nit, nrc, regimen_fiscal, created_at as str), TransactionBFF (id, user_id, type, amount as Decimal, category, description, date as str, iva_rate, iva_calculated, created_at as str), PagoCuentaBreakdownBFF, TaxProjectionBFF
  - **Transformers**: UserBFFTransformer.from_domain(user), TransactionBFFTransformer.from_domain(tx) — static methods converting domain models to BFF schemas

Note: All Decimal values in BFF responses will be serialized as JSON strings via custom FastAPI JSON encoder (handled in T9).

**Dependencies:** T2 (domain models for transformers)

**Complexity:** M

**Effort:** ~150–250 lines

**Test strategy:** Unit tests in T10. Verify: response wrapping, error formatting, schema transformations (domain→BFF field mapping, date/datetime→ISO string).

---

### T9 — API Routes, Middleware, and App Factory

**Files to create:**
- `backend/src/api/__init__.py`
- `backend/src/api/dependencies.py` — FastAPI DI wiring
- `backend/src/api/middleware.py` — request_id, timing middleware
- `backend/src/api/routes/__init__.py`
- `backend/src/api/routes/health.py` — GET /health
- `backend/src/api/routes/users.py` — POST /api/v1/users, GET /api/v1/users/{user_id}, GET /api/v1/users/email/{email}
- `backend/src/api/routes/transactions.py` — POST /api/v1/transactions, GET /api/v1/transactions/{tx_id}, GET /api/v1/transactions
- `backend/src/api/routes/taxes.py` — GET /api/v1/taxes/projection
- `backend/src/main.py` — FastAPI app factory with lifespan, CORS, exception handlers

**What to implement:**
- **dependencies.py**: `get_user_repo() -> UserRepository` (wired to DynamoDBUserRepo), `get_transaction_repo() -> TransactionRepository`, `get_register_user_use_case()`, `get_record_transaction_use_case()`, `get_tax_projection_use_case()`. All use FastAPI `Depends` for DI. Overridable in tests via `app.dependency_overrides`.
- **middleware.py**: `request_id_middleware` — injects X-Request-ID header (uuid4), X-Response-Time-Ms (ms float), sets `request.state.request_id`.
- **health.py**: `GET /health` → `{"status": "ok", "version": settings.app_version, "timestamp": utc_now_iso}`. No auth, no DB check.
- **users.py**: POST endpoint validates body via UserCreateRequest, calls RegisterUserUseCase → returns 201 with BFFResponse<UserBFF>. GET by id/email → calls repo directly or via use case, returns 200 with BFFResponse or 404. Duplicate email → 409.
- **transactions.py**: POST → RecordTransactionUseCase → 201. GET by id → 200/404. GET list with query params (user_id, page, limit) → 200 with BFFResponse<list<TransactionBFF>> and PaginationMeta.
- **taxes.py**: GET projection with query params (user_id, year, period) → GetTaxProjectionUseCase → 200 with BFFResponse<TaxProjectionBFF>.
- **main.py**: `create_app()` factory function. Registers CORS middleware (origins from Settings). Registers routers with prefixes. Global exception handlers: RequestValidationError → 422 BFFErrorResponse, HTTPException → 422/404/409, generic Exception → 500 BFFErrorResponse. Lifespan context manager (startup/shutdown hooks).

**Exception handling matrix:**
| Exception | Status | BFFErrorResponse |
|-----------|--------|------------------|
| RequestValidationError | 422 | errors w/ field-level detail |
| DuplicateEmailError | 409 | code: "DUPLICATE_EMAIL" |
| NotFoundError | 404 | code: "NOT_FOUND" |
| DomainError | 400 | code: "DOMAIN_ERROR" |
| Exception (generic) | 500 | code: "INTERNAL_ERROR" |

**Dependencies:** T6 (DynamoDB repos for DI wiring), T7 (use cases), T8 (BFF response/schemas)

**Complexity:** L

**Effort:** ~300–450 lines

**Test strategy:** E2E tests in T11 via httpx.AsyncClient. Verify: all 8 endpoints, all HTTP status codes, error response shapes, CORS headers, request-id header.

---

### T10 — Unit Tests (Tax Engine + BFF + Models)

**Files to create:**
- `backend/tests/__init__.py`
- `backend/tests/test_tax_engine.py`
- `backend/tests/test_bff.py`
- `backend/tests/test_models.py`

**What to implement:**
- **test_tax_engine.py**: Parametrized pytest tests covering ALL scenarios from spec edge case matrix:
  - `test_iva_standard`, `test_iva_zero`, `test_iva_negative_clamped`, `test_iva_rounding_half_up`, `test_iva_custom_rate`, `test_iva_zero_rate`, `test_iva_large_amount` (10^12), `test_iva_sub_cent`
  - `test_pago_cuenta_all_rates` (4 categories), `test_pago_cuenta_unknown_fallback`, `test_pago_cuenta_zero`, `test_pago_cuenta_negative`
  - `test_accumulate_iva_multiple`, `test_accumulate_pago_cuenta_grouped`, `test_empty_list`, `test_mixed_rates`
  - `test_determinism`: call same inputs 100x, assert identical Decimal
  - 100% branch coverage enforced
  - Coverage target: 100%

- **test_bff.py**: Tests for:
  - `BFFResponse.success()` and `.error()` classmethods
  - `ResponseMeta` with/without pagination
  - `UserBFFTransformer.from_domain()` — field mapping, date→ISO string, NIT format preservation
  - `TransactionBFFTransformer.from_domain()` — iva_calculated computed field, Decimal→str
  - ErrorDetail field-level error formatting
  - Coverage target: 95%

- **test_models.py**: Pydantic validation tests:
  - Valid User creation, invalid NIT (wrong format, wrong length, letters), invalid NRC, invalid email, invalid enum values
  - Valid Transaction creation, amount <= 0 rejected, future date (warn), too-long description
  - Valid TaxDeclaration, period out of range (1-12), year outside 2020-2030, negative totals
  - Coverage target: 100%

**Dependencies:** T3 (tax engine), T2 (models), T8 (BFF)

**Complexity:** M

**Effort:** ~250–350 lines

**Test strategy:** These ARE the tests. Run via `pytest tests/ -v --cov=src`.

---

### T11 — Integration + E2E Tests

**Files to create:**
- `backend/tests/conftest.py` — shared fixtures
- `backend/tests/test_api.py` — E2E tests via httpx.AsyncClient

**What to implement:**
- **conftest.py**:
  - `settings_override` fixture: patch Settings with test table names, test AWS region
  - `dynamodb_mock` fixture (scope=function): use `moto.mock_aws` to create users and transactions tables with GSIs matching production schema, yield, then teardown
  - `test_repos` fixture: instantiate DynamoDBUserRepo and DynamoDBTransactionRepo with mocked tables
  - `app` fixture: create FastAPI app via `create_app()`, override DI dependencies to use test repos
  - `async_client` fixture: `httpx.AsyncClient(app=app, base_url="http://test")`

- **test_api.py** (E2E via httpx):
  - `test_health`: GET /health → 200, verify body shape
  - `test_create_user`: POST /api/v1/users with valid body → 201, verify UserBFF response shape, verify UUID id and ISO created_at
  - `test_create_user_duplicate_email`: same email twice → 409, verify BFFErrorResponse
  - `test_create_user_invalid_data`: wrong NIT format → 422, verify field-level errors
  - `test_get_user_by_id`: create → GET by id → 200, verify fields match
  - `test_get_user_by_email`: create → GET by email → 200
  - `test_get_user_not_found`: GET nonexistent UUID → 404
  - `test_create_transaction`: POST /api/v1/transactions with valid body → 201, verify TransactionBFF with iva_calculated
  - `test_get_transaction_by_id`: create → GET by id → 200
  - `test_list_transactions`: create 3 transactions → GET list → verify pagination
  - `test_list_transactions_pagination`: create 25 transactions → GET page=1 limit=10 → 10 items, meta.total=25, meta.has_next=true → GET page=3 → 5 items
  - `test_tax_projection`: create 2 income ($1000) + 1 expense ($500) in same month → GET projection → verify calculated amounts
  - `test_tax_projection_empty`: GET projection for user with no transactions → 200 with zero amounts
  - `test_cors_headers`: verify Access-Control-Allow-Origin header present
  - Coverage targets: api/routes 90%, application 90%, infrastructure 85%

**Dependencies:** T6 (DynamoDB repos), T9 (API routes + app)

**Complexity:** L

**Effort:** ~300–450 lines

**Test strategy:** These ARE the tests. Run via `pytest tests/ -v --cov=src`.

---

## Summary Statistics

| Task | Files | Dependencies | Complexity | Est. Lines |
|------|-------|-------------|-----------|-----------|
| T1 — Scaffolding | ~15 | None | S | 80–100 |
| T2 — Domain Models | 5 | T1 | M | 200–280 |
| T3 — Tax Engine | 2 | T1 | S | 80–120 |
| T4 — Repository Interfaces | 3 | T2 | S | 80–100 |
| T5 — DynamoDB Infrastructure | 2 | T1 | S | 50–70 |
| T6 — DynamoDB Repos | 3 | T4, T5 | M | 200–300 |
| T7 — Use Cases | 5 | T3, T4 | M | 150–200 |
| T8 — BFF Response Layer | 3 | T2 | M | 150–250 |
| T9 — API Routes + App | 9 | T6, T7, T8 | L | 300–450 |
| T10 — Unit Tests | 4 | T2, T3, T8 | M | 250–350 |
| T11 — Integration + E2E | 2 | T6, T9 | L | 300–450 |
| **Total** | **~53** | | | **~1,840–2,670** |

---

## Success Criteria

1. `make install` installs all dependencies without error
2. `make test` runs all tests with ≥85% overall coverage
3. `make lint` passes with zero ruff violations
4. All 8 API endpoints respond with correct HTTP status codes and BFFResponse shapes
5. Tax engine produces mathematically correct results matching SV tax regulations (13% IVA, 10%/5%/1% Pago a Cuenta)
6. DynamoDB repositories handle CRUD + GSI queries + pagination correctly under moto mock
7. Decimal precision is preserved throughout the entire chain (API → use case → tax engine → DynamoDB → response)
