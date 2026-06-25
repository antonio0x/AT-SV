# SDD Spec: Transaction Management

## Backend Endpoints

All under `/api/v1/transactions`. All require `get_current_user` from JWT cookie (returns 401 `UNAUTHENTICATED` on missing/invalid token).

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| POST | `/transactions` | 201 | Create transaction (JSON body, user_id from JWT) |
| GET | `/transactions` | 200 | List with pagination (user_id from JWT) |
| GET | `/transactions/{id}` | 200 | Get by ID (ownership verified) |
| PUT | `/transactions/{id}` | 200 | Update (JSON body, ownership verified) |
| DELETE | `/transactions/{id}` | 200 | Delete (ownership verified) |

Error codes: 401 UNAUTHENTICATED, 404 NOT_FOUND, 422 Validation

## Request Schemas

```python
class TransactionCreateRequest(BaseModel):
    type: TransactionType  # income | expense
    amount: Decimal = Field(gt=Decimal("0"))
    category: str
    description: str | None = None
    date: str | None = None  # ISO format, defaults to today
    iva_rate: Decimal | None = None  # defaults to 0.13

class TransactionUpdateRequest(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(None, gt=Decimal("0"))
    category: str | None = None
    description: str | None = None
    date: str | None = None
    iva_rate: Decimal | None = None
```

## Frontend Components

- **UI Kit**: Button, Input, Select, Table, Badge, Card in `src/components/ui/`
- **TransaccionesPage**: table + pagination + filters + "Nueva transacción" button
- **TransactionForm**: modal for create/edit with all fields
- **transactionStore**: Zustand with CRUD actions + pagination state
- **Route**: `/transacciones` under ProtectedRoute
- **Header**: "Transacciones" link with Receipt icon
