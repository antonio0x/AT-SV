# SDD Tasks: Tax Declarations (F-07, F-14, F-06) + Dashboard + Employees

Two chained PRs:
- **PR#2a** — Backend (T1–T8, branch `feat/decl-backend` → `feat/declarations`)
- **PR#2b** — Frontend (T9–T15, branch `feat/decl-frontend` → `feat/decl-backend`)

---

## PR#2a — Backend (T1–T8)

### ✅ T1 — Create F07Data, F14Data, F06Data models and extend TaxDeclaration

**Files**: `backend/src/domain/models/tax_declaration.py`, `backend/src/domain/models/__init__.py`
**Effort**: S (20 min)
**Depends**: none
**Details**:
- Add inner Pydantic models:
  - `F07Data`: `total_iva`, `iva_debito`, `iva_credito`, `iva_retenido` (all `Decimal`)
  - `F14Data`: `ingresos_brutos`, `tasa_aplicada`, `pago_cuenta_calculado`, `saldo_a_favor_anterior` (all `Decimal`)
  - `F06Data`: `total_remuneraciones`, `total_empleados` (`int`), `isr_retenido`, `cotizaciones_iss`, `cotizaciones_afp` (all `Decimal`)
- Add optional fields `f07: F07Data | None`, `f14: F14Data | None`, `f06: F06Data | None` to `TaxDeclaration`
- Keep existing fields (`declaration_id`, `user_id`, `form_type`, `period`, `year`, `status`, `created_at`)
- Update `__init__.py` exports

### ✅ T2 — Create Employee domain model

**Files**: `backend/src/domain/models/employee.py`, `backend/src/domain/models/__init__.py`
**Effort**: XS (10 min)
**Depends**: none
**Details**:
- `Employee` model: `employee_id`, `user_id`, `nombre`, `salario` (`Decimal`), `isr_rate` (`Decimal`, default `0.10`), `iss_deduction` (`Decimal`, default `0.03`), `afp_deduction` (`Decimal`, default `0.0725`), `created_at`
- Add to `__init__.py` exports

### ✅ T3 — Add DeclarationRepository + EmployeeRepository interfaces + update UnitOfWork

**Files**: `backend/src/domain/interfaces/repository.py`, `backend/src/domain/interfaces/unit_of_work.py`
**Effort**: S (20 min)
**Depends**: T1, T2
**Details**:
- `DeclarationRepository`: `create`, `get_by_id`, `get_by_user_id` (paginated), `get_by_period` (user_id + form_type + year + period → `TaxDeclaration | None`), `update`, `delete`
- `EmployeeRepository`: `create`, `get_by_id`, `get_by_user_id`, `update`, `delete`
- `UnitOfWork`: add `declarations: DeclarationRepository` and `employees: EmployeeRepository` properties

### ✅ T4 — InMemoryDeclarationRepository + InMemoryEmployeeRepository

**Files**: `backend/src/infrastructure/repositories/in_memory.py`
**Effort**: S (15 min)
**Depends**: T3
**Details**:
- Follow existing `InMemoryTransactionRepository` pattern
- `InMemoryDeclarationRepository`: `_store: dict[str, TaxDeclaration]`, enforce period uniqueness on create (same form_type + year + period → raise)
- `InMemoryEmployeeRepository`: `_store: dict[str, Employee]`

### ✅ T5 — Extend tax engine with F-07, F-14, F-06 calculations

**Files**: `backend/src/domain/services/tax_engine.py`
**Effort**: M (45 min)
**Depends**: T1, T2
**Details**:
- `calculate_f07(transactions: list[Transaction]) -> F07Data`: sum IVA débito from income transactions, IVA crédito from expense transactions. `total_iva = debito - credito`. `iva_retenido = 0` (simplified).
- `calculate_f14(transactions: list[Transaction], category_rates: dict, saldo_anterior: Decimal = 0) -> F14Data`: compute pago a cuenta per income transaction by category rate (`PAGO_CUENTA_RATES`). Sum = `pago_cuenta_calculado`. Subtract `saldo_anterior`. Set `saldo_a_favor_anterior` from input.
- `calculate_f06(employees: list[Employee]) -> F06Data`: per employee, `isr = salario * isr_rate`, `iss = salario * iss_deduction`, `afp = salario * afp_deduction`. Aggregate totals — `total_remuneraciones`, `total_empleados`, `isr_retenido`, `cotizaciones_iss`, `cotizaciones_afp`.
- Reuse existing `PAGO_CUENTA_RATES` from `tax_engine.py`

### ✅ T6 — Create declaration use cases

**Files**: `backend/src/application/use_cases/calculate_declaration.py`, `save_declaration.py`, `submit_declaration.py`, `get_declaration.py`, `list_declarations.py`
**Effort**: L (90 min)
**Depends**: T3, T4, T5
**Details**:
- `CalculateDeclarationUseCase`: reads transactions for the period (via `TransactionRepository`), employees for F-06 (via `EmployeeRepository`), calls tax engine, returns `TaxDeclaration` (NOT persisted). Injects both `declaration_repo` and `employee_repo`.
- `SaveDeclarationUseCase`: validates period uniqueness (query `get_by_period` — raise `400` on duplicate), creates or updates declaration, persists via repo.
- `SubmitDeclarationUseCase`: loads declaration by id, verifies ownership, validates status is `"draft"`, sets `status = "submitted"`, persists.
- `GetDeclarationUseCase`: loads by id, verifies ownership (user_id matches current user).
- `ListDeclarationsUseCase`: loads by user_id with pagination (page, limit) + optional filters (form_type, year, period, status).

### ✅ T7 — Create BFF schemas + API routes + update dependencies

**Files**: `backend/src/api/bff/schemas.py`, `backend/src/api/routes/declarations.py`, `backend/src/api/routes/employees.py`, `backend/src/api/dependencies.py`, `backend/src/api/main.py`
**Effort**: M (60 min)
**Depends**: T6
**Details**:
- Add to `schemas.py`:
  - `DeclarationBFF`: `declaration_id`, `user_id`, `form_type`, `period`, `year`, `status`, all form-type fields as optional, `created_at`
  - `DeclarationCreateRequest`: `declaration_id` (optional for update), `form_type`, `period`, `year`, form-type fields (only matching type required)
  - `DeclarationCalculateRequest`: `form_type`, `period`, `year`
  - `EmployeeBFF`: `employee_id`, `user_id`, `nombre`, `salario`, `isr_rate`, `iss_deduction`, `afp_deduction`, `created_at`
  - `EmployeeCreateRequest`: `nombre`, `salario`, and optional rate fields
  - `EmployeeUpdateRequest`: all optional
- Create `routes/declarations.py`:
  - `POST /declarations/calculate` → `200` (CalculateDeclarationUseCase)
  - `POST /declarations` → `201` (SaveDeclarationUseCase)
  - `GET /declarations` → `200` (ListDeclarationsUseCase)
  - `GET /declarations/{id}` → `200` (GetDeclarationUseCase)
  - `PUT /declarations/{id}` → `200` (SaveDeclarationUseCase with existing id)
  - `POST /declarations/{id}/submit` → `200` (SubmitDeclarationUseCase)
- Create `routes/employees.py`:
  - `POST /employees` → `201`
  - `GET /employees` → `200`
  - `GET /employees/{id}` → `200`
  - `PUT /employees/{id}` → `200`
  - `DELETE /employees/{id}` → `200`
- Add `get_declaration_repo()`, `get_employee_repo()` to `dependencies.py` (follows `get_tx_repo` pattern with `use_fake_repos`)
- Register both routers in `main.py` under `/api/v1`

### ✅ T8 — Write backend tests

**Files**: `backend/tests/test_declarations.py`, `backend/tests/test_employees.py`
**Effort**: L (90 min)
**Depends**: T7
**Details**:
- Test declaration CRUD: calculate (per type), create (draft), get, list, update, submit
- Test error cases: duplicate period (same form_type + year + month), submit already-submitted declaration, 404 for non-owned declaration
- Test employee CRUD: create, get, list, update, delete
- Test auth: all endpoints return 401 without JWT cookie
- Test tax engine: F-07 IVA sum, F-14 with and without carry-over, F-06 aggregation from employees
- Use fixture for authenticated user with cookie (same pattern as `test_transactions`)

---

## PR#2b — Frontend (T9–T15)

### ✅ T9 — declarationStore + employeeStore (Zustand)

**Files**: `frontend/src/store/declarationStore.ts`, `frontend/src/store/employeeStore.ts`
**Effort**: M (30 min)
**Depends**: none
**Details**:
- `declarationStore`: `declarations`, `isLoading`, `error`, `page`, `limit`, `total`, `filters` (`form_type`, `year`, `period`, `status`), actions: `fetch`, `create`, `update`, `submit`, `calculate`, `setPage`, `setFilters`
- `employeeStore`: `employees`, `isLoading`, `error`, actions: `fetch`, `create`, `update`, `delete`
- Follow `transactionStore.ts` pattern with `api.ts` for HTTP calls

### ✅ T10 — DashboardPage

**Files**: `frontend/src/pages/DashboardPage.tsx`
**Effort**: M (45 min)
**Depends**: T9
**Details**:
- Post-login landing page, route `/dashboard`
- Cards showing IVA projection, Pago a Cuenta projection, declarations status for current period
- Fetch projection from `/taxes/projection`, declarations from store
- Quick action buttons: "Nueva declaración IVA", "Nueva declaración Pago a Cuenta", "Ver transacciones"
- Uses `Card`, `Badge`, `Button` from UI kit
- Redirect to `/login` if not authenticated (handled by `ProtectedRoute`)

### ✅ T11 — DeclaracionesPage (list)

**Files**: `frontend/src/pages/DeclaracionesPage.tsx`
**Effort**: M (45 min)
**Depends**: T9
**Details**:
- Table: Formulario, Período, Año, Estado (`Badge`), Creado, Acciones (ver/editar/submit)
- Pagination + filters: `form_type` (Select), `year` (Input), `period` (Select), `status` (Select)
- "Nueva declaración" button → redirect to `/declaraciones/nueva`
- Uses `Table`, `Badge`, `Button`, `Card`, `Select`, `Input` from UI kit

### ✅ T12 — DeclarationCreatePage (wizard)

**Files**: `frontend/src/pages/DeclarationCreatePage.tsx`
**Effort**: L (60 min)
**Depends**: T9
**Details**:
- Step 1: select `form_type` (Select with F-07, F-14, F-06), year (Input), period/month (Select 01–12)
- Step 2: call `POST /declarations/calculate`, show calculated values in read-only form (field labels depend on form type)
- Step 3: confirm → call `POST /declarations` to save as draft, redirect to `/declaraciones/:id`
- Optional: allow user to adjust calculated values before save
- Uses `Button`, `Input`, `Select`, `Card` from UI kit

### ✅ T13 — DeclarationDetailPage

**Files**: `frontend/src/pages/DeclarationDetailPage.tsx`
**Effort**: M (45 min)
**Depends**: T9
**Details**:
- Show full declaration data based on `form_type`:
  - F-07: `total_iva`, `iva_debito`, `iva_credito`, `iva_retenido`
  - F-14: `ingresos_brutos`, `tasa_aplicada`, `pago_cuenta_calculado`, `saldo_a_favor_anterior`
  - F-06: `total_remuneraciones`, `total_empleados`, `isr_retenido`, `cotizaciones_iss`, `cotizaciones_afp`
- Status badge (draft/submitted)
- If draft: "Submit" button → calls `POST /declarations/{id}/submit`
- If submitted: show "Ya fue presentada" message, no actions

### ✅ T14 — EmployeesPage (CRUD)

**Files**: `frontend/src/pages/EmployeesPage.tsx`
**Effort**: M (45 min)
**Depends**: T9
**Details**:
- Table: Nombre, Salario, ISR Rate, ISS, AFP, Acciones (editar/eliminar)
- Modal form for create/edit (inline `EmployeeForm` component with inputs for nombre, salario, and all rates)
- Delete with confirmation dialog
- Uses `Table`, `Button`, `Input`, `Card` from UI kit

### ✅ T15 — Wire routes + nav + frontend tests

**Files**: `frontend/src/App.tsx`, `frontend/src/components/layout/Header.tsx`, plus test files
**Effort**: M (60 min)
**Depends**: T10, T11, T12, T13, T14
**Details**:
- `App.tsx`: add routes wrapped in `ProtectedRoute`:
  - `/dashboard` → `DashboardPage`
  - `/declaraciones` → `DeclaracionesPage`
  - `/declaraciones/nueva` → `DeclarationCreatePage`
  - `/declaraciones/:id` → `DeclarationDetailPage`
  - `/empleados` → `EmployeesPage`
- `Header.tsx`: add nav links — Dashboard (`LayoutDashboard` icon), Declaraciones (`FileText` icon), Empleados (`Users` icon)
- Frontend tests:
  - Store tests: declarationStore (fetch, calculate, create, submit, pagination, filters), employeeStore (CRUD)
  - Page smoke tests: each page renders without crashing
  - Navigation tests: links render in header

---

## Dependency Graph

```
T1  T2
|   |
T3  |
|   |
T4  |
 \  |
  T5
  |
  T6
  |
  T7
  |
  T8

T9
├──┬──┬──┬──┐
T10 T11 T12 T13 T14
 \   |   |   |  /
  \  |   |   | /
   T15 + tests
```

## Review Workload Forecast

- **Estimated changed lines**: ~2500+ (backend ~1200, frontend ~1300)
- **400-line budget risk**: HIGH
- **Chained PRs recommended**: YES (2 PRs as planned)
- **Decision needed before apply**: NO (already decided: 2 chained PRs, feature-branch-chain)
