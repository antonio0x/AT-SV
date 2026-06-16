# SDD Tasks: Transaction Management

## T1 — Add request schemas + fix TransactionBFF + fix repository interface

**Files**: `backend/src/api/bff/schemas.py`, `backend/src/domain/interfaces/repository.py`
**Effort**: S (15 min)
**Depends**: none
**Details**: Add `TransactionCreateRequest`, `TransactionUpdateRequest` Pydantic models; add `created_at: str` to `TransactionBFF`; add `page/limit` to abstract `get_by_user_id`

## T2 — Extract `get_tx_repo` to `dependencies.py`

**Files**: `backend/src/api/dependencies.py`, `backend/src/api/routes/transactions.py`, `backend/src/api/routes/taxes.py`
**Effort**: XS (5 min)
**Depends**: none

## T3 — Refactor POST + GET /transactions to JWT auth + JSON body

**Files**: `backend/src/api/routes/transactions.py`
**Effort**: M (45 min)
**Depends**: T1, T2

## T4 — Add GET / PUT / DELETE /transactions/{id} with JWT auth

**Files**: `backend/src/api/routes/transactions.py`
**Effort**: M (45 min)
**Depends**: T1, T2

## T5 — Fix tax projection filtering + JWT auth

**Files**: `backend/src/api/routes/taxes.py`, `backend/src/application/use_cases/get_tax_projection.py`
**Effort**: S (20 min)
**Depends**: T2, T3

## T6 — Update backend tests for all changes

**Files**: `backend/tests/test_api.py`
**Effort**: L (90 min)
**Depends**: T3, T4, T5

## T7 — UI Kit: Button, Input, Select, Badge, Card

**Files**: `frontend/src/components/ui/Button.tsx`, `Input.tsx`, `Select.tsx`, `Badge.tsx`, `Card.tsx`
**Effort**: M (60 min)
**Depends**: none

## T8 — UI Kit: Table component

**Files**: `frontend/src/components/ui/Table.tsx`
**Effort**: S (20 min)
**Depends**: none

## T9 — transactionStore (Zustand)

**Files**: `frontend/src/store/transactionStore.ts`
**Effort**: M (30 min)
**Depends**: none (only api.ts)

## T10 — TransactionForm modal

**Files**: `frontend/src/components/TransactionForm.tsx`
**Effort**: M (45 min)
**Depends**: T7

## T11 — TransaccionesPage

**Files**: `frontend/src/pages/TransaccionesPage.tsx`
**Effort**: L (90 min)
**Depends**: T7, T9, T10

## T12 — Wire routes + nav

**Files**: `frontend/src/App.tsx`, `frontend/src/components/layout/Header.tsx`
**Effort**: XS (10 min)
**Depends**: T11

## T13 — Frontend component/store tests

**Files**: frontend test files
**Effort**: M (60 min)
**Depends**: T7, T9, T10, T11

## Dependency Graph

```
T1  T2
  \  /
   T3  T4  T5
    \ |  /
     T6
     
T7  T8
 |   |
 T9  |
 | \ |
 T10 T11
  \  /
   T12 T13
```
