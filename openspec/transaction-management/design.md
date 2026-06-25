# SDD Design: Transaction Management

## Architecture Decisions

1. **JWT-driven ownership**: Every transaction endpoint uses `get_current_user` → `current_user.user_id` as sole owner identifier
2. **Use cases vs inline**: Create/update use existing `RecordTransactionUseCase` pattern; GET/DELETE call repos directly
3. **`get_tx_repo` extracted to `dependencies.py`**: Shared repo factory, inject via `Depends`
4. **Repository interface fix**: Add `page: int = 1, limit: int = 50` to abstract ABC signature
5. **Tax projection fix**: Filter in-memory by `tx.date.year == year`
6. **Modal without library**: Fixed div overlay + backdrop, Zustand state in page component
7. **UI Kit wraps Tailwind**: Typed React interfaces over existing utility CSS

## Data Flow

```
Browser → ProtectedRoute → TransaccionesPage → transactionStore (Zustand)
       → api.ts (withCredentials=true → JWT cookie)
       → FastAPI /api/v1/transactions*
       → get_current_user → repo → TransactionBFF response
```

## Implementation Order

| Step | Tasks | Dependencies |
|------|-------|-------------|
| 1 | T1 + T2: Schemas + dependencies refactor | — |
| 2 | T3 + T4 + T5: Routes refactor + new endpoints + tax fix | T1, T2 |
| 3 | T6: Backend tests | T3, T4, T5 |
| 4 | T7 + T8: UI Kit components | — |
| 5 | T9 + T10: transactionStore + TransactionForm | T7 |
| 6 | T11 + T12: TransaccionesPage + routes/nav | T9, T10 |
| 7 | T13: Frontend tests | T11, T12 |
