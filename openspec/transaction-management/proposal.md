# Proposal: Transaction Management

## Intent

Full CRUD for income/expense transactions with JWT auth, proper JSON endpoints, and a transaction management UI. This is the data foundation for declarations (next PR).

## Scope

### In Scope
- **Backend**: Fix POST /transactions to JSON body + user_id from JWT; add PUT, DELETE, GET by id; fix projection period filtering; category-specific Pago a Cuenta rates
- **Frontend**: TransaccionesPage (table + pagination), TransactionForm (modal), transactionStore (Zustand)
- **Shared UI**: Button, Input, Select, Table, Badge, Card in `src/components/ui/`
- **Nav**: "Transacciones" link in Header (protected)
- **Tests**: Backend endpoint tests + frontend component/store tests

### Out of Scope
- Declarations / F-07 / F-14 / F-06 (next PR)
- Dashboard page (next PR)
- Transaction import/export
- Categories CRUD (use existing hardcoded categories)

## Capabilities

### New Capabilities
- `transaction-management`: full CRUD for income/expense transactions with auth, paginated list, and modal-based create/edit

### Modified Capabilities
None

## Approach

Two chained PRs:
1. **Backend**: refactor POST to JSON body + JWT user_id; add GET/{id}, PUT/{id}, DELETE/{id}; fix projection filtering; category-specific Pago a Cuenta
2. **Frontend + UI kit**: build shared components (Button, Input, Select, Table, Badge, Card), transactionStore, TransaccionesPage, TransactionForm modal, nav link

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/src/api/routes/transactions.py` | Modified | JSON body, JWT user_id, add PUT/DELETE/GET-by-id |
| `backend/src/application/use_cases/` | New | Update/Delete/GetTransaction use cases |
| `frontend/src/components/ui/` | New | Button, Input, Select, Table, Badge, Card |
| `frontend/src/pages/TransaccionesPage.tsx` | New | List with table, filters, pagination |
| `frontend/src/store/transactionStore.ts` | New | Zustand CRUD store |
| `frontend/src/App.tsx` | Modified | Add route + ProtectedRoute wrapper |
| `frontend/src/components/layout/Header.tsx` | Modified | Add "Transacciones" nav link |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| POST /transactions breaking change (query params → JSON) | High | Update all tests first; coordinate with any callers |
| No shared UI components exist yet | Medium | Build minimal kit as first frontend task |
| Transaction type/category enums need UI surface | Low | Select with hardcoded options from existing constants |

## Rollback Plan

Revert the frontend changes (remove route, store, page, components). For backend, revert transactions.py to restore query-param behavior. Both slices independently revertible.

## Dependencies

- JWT auth fully working (shipped in auth-and-frontend-connection)
- No external dependencies

## Success Criteria

- [ ] Authenticated user can create, list, view, edit, delete transactions via UI
- [ ] POST/PUT /transactions accept JSON body, reject query params
- [ ] user_id extracted from JWT cookie, not request params
- [ ] All transaction endpoints return 401 for unauthenticated requests
- [ ] Shared UI components render correctly in isolation
- [ ] Transaction list shows paginated results with filters
