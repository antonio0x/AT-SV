# Design: Auth + Frontend-Backend Connection

## Technical Approach

Add `hashed_password` to the User domain model. Move password hashing + duplicate checking into `RegisterUserUseCase`. Create `LoginUserUseCase` for credential verification. Introduce a `/api/v1/auth/` router with register/login/logout endpoints, all setting httpOnly SameSite cookies. Add `GET /api/v1/users/me` via a `get_current_user` FastAPI dependency that reads the JWT from cookie. On the frontend: Zustand store hydrated on mount via `/users/me`, protected routes, auth-aware header, and a login/register toggle page. Wire everything through Vite proxy so cookies stay same-origin in dev.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| Auth helpers location | `backend/src/api/auth/helpers.py` | In `dependencies.py`, in route file | Keeps JWT encode/decode + cookie set/clear colocated; routes stay thin; dependencies.py only has DI wiring |
| Error signaling from use cases | `DomainError` exception | Return-tuple, `HTTPException` in use case | Clean Architecture: use case doesn't import FastAPI; route catches and maps to HTTP status |
| Password hashing location | In `RegisterUserUseCase` (application layer) | Domain service, dedicated hasher class | Use case already orchestrates; no need for extra abstraction at this scale |
| Duplicate email detection | `repo.get_by_email()` then `repo.create()` | Conditional DynamoDB put + catch | Accepts TOCTOU race for v1; DynamoDB conditional write can be added later |
| auth/register response | 201 with cookie | 200 with cookie | REST: 201 Created for resource creation; matches spec |
| Cookie Secure flag | Controlled by `settings.debug` | Always on, always off | Development over HTTP needs Secure=false; production HTTPS needs Secure=true |
| Error status codes | Real HTTP codes (401, 409) | Always 200 with body errors | Auth requires proper status codes for browser/frontend interop; existing pattern stays for other endpoints |

## Data Flow

```
Registration:
  POST /api/v1/auth/register { email, password, business_name, ... }
    → auth.py route
      → RegisterUserUseCase.execute(email, password, ...)
        → repo.get_by_email(email) → raise DomainError if exists
        → hash password (passlib bcrypt)
        → User(hashed_password=hash, ...)
        → repo.create(user)
      ← User
    → helpers.set_auth_cookie(response, user)  # Set-Cookie: access_token=<jwt>
    → BFFResponse(UserBFF(...))

Login:
  POST /api/v1/auth/login { email, password }
    → auth.py route
      → LoginUserUseCase.execute(email, password)
        → repo.get_by_email(email) → None → raise DomainError(INVALID_CREDENTIALS)
        → passlib.verify(password, user.hashed_password) → fail → raise DomainError(INVALID_CREDENTIALS)
      ← User
    → helpers.set_auth_cookie(response, user)
    → BFFResponse(UserBFF(...))

Authenticated request (e.g. GET /api/v1/users/me):
  Cookie: access_token=<jwt>
    → get_current_user(request, repo)
      → jwt_decode(cookie_value) → payload
      → repo.get_by_id(payload["sub"]) → None → raise HTTPException(401)
      ← User
    → route handler uses user

ProtectedRoute:
  App mounts → authStore.hydrate()
    → GET /api/v1/users/me (cookie auto-sent)
    → 200 → store.user = data, isAuthenticated = true
    → 401 → store.user = null, isAuthenticated = false
  Route render:
    isLoading → <Spinner />
    !isAuthenticated → <Navigate to="/login" />
    authenticated → <Outlet />
```

## File Changes

### New Files

| File | Responsibility |
|------|---------------|
| `backend/src/api/auth/__init__.py` | Package init |
| `backend/src/api/auth/helpers.py` | `jwt_encode()`, `jwt_decode()`, `set_auth_cookie()`, `clear_auth_cookie()`, `get_current_user()` dependency |
| `backend/src/api/routes/auth.py` | Router with `POST /register`, `POST /login`, `POST /logout` |
| `backend/src/application/use_cases/login_user.py` | `LoginUserUseCase` — email lookup → bcrypt verify → return User or DomainError |
| `backend/src/domain/exceptions.py` | `DomainError` base exception with code + message |
| `backend/src/api/dependencies.py` | Shared `get_user_repo()` for both users.py and auth.py |
| `frontend/src/lib/api.ts` | Axios instance with `baseURL: '/api/v1'`, `withCredentials: true` |
| `frontend/src/store/authStore.ts` | Zustand store: hydrate, login, register, logout |
| `frontend/src/components/auth/ProtectedRoute.tsx` | Route guard with loading state |

### Modified Files

| File | Changes |
|------|---------|
| `backend/src/domain/models/user.py` | Add `hashed_password: str \| None = None` |
| `backend/src/application/use_cases/register_user.py` | Accept `password` param, hash with passlib, check duplicate email via `repo.get_by_email()`, return User or raise DomainError |
| `backend/src/infrastructure/database.py` | Add `jwt_secret_key`, `jwt_algorithm`, `jwt_expire_minutes` to Settings |
| `backend/src/api/main.py` | Import + include `auth.router`, remove old `users` POST route coverage |
| `backend/src/api/routes/users.py` | Remove `POST /users` (query-param), add `GET /users/me` using `get_current_user`, move `get_user_repo` to `dependencies.py` |
| `backend/tests/test_api.py` | Remove old user creation tests, add auth endpoint tests (register, login, logout, duplicate email, wrong password, /users/me with/without cookie, expired/tampered token) |
| `backend/pyproject.toml` | Add `python-jose[cryptography]>=3.3.0`, `passlib[bcrypt]>=1.7.4` to dependencies |
| `frontend/src/pages/LoginPage.tsx` | Add login/register toggle mode, registration fields, API calls via store, error display from BFFResponse |
| `frontend/src/App.tsx` | Wrap `/documentos` route with `<ProtectedRoute>`, add `/login` redirect-if-authenticated logic, call `authStore.hydrate()` on mount |
| `frontend/src/components/layout/Header.tsx` | Show `business_name` (truncated 20 chars) + "Cerrar sesión" when authenticated; "Iniciar sesión" link when anonymous |
| `frontend/vite.config.js` | Add `server.proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } }` |
| `frontend/package.json` | Add `axios`, `zustand` to dependencies |

## Interfaces / Contracts

### DomainError
```python
class DomainError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")
```

### LoginUserUseCase
```python
class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository): ...
    async def execute(self, email: str, password: str) -> User: ...
    # Raises DomainError(INVALID_CREDENTIALS) for wrong email OR wrong password
```

### Updated RegisterUserUseCase
```python
class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository): ...
    async def execute(
        self, email: str, password: str, business_name: str,
        business_type: str, nit: str, nrc: str | None = None,
        regimen_fiscal: str = "simplificado",
    ) -> User: ...
    # Raises DomainError(EMAIL_EXISTS) on duplicate email
```

### Auth Helpers
```python
def jwt_encode(payload: dict) -> str: ...
def jwt_decode(token: str) -> dict: ...  # raises on expired/bad signature
def set_auth_cookie(response: Response, user: User) -> None: ...
def clear_auth_cookie(response: Response) -> None: ...
async def get_current_user(request: Request, repo=Depends(get_user_repo)) -> User: ...
```

### Auth Router Endpoints
| Method | Path | Status | Returns |
|--------|------|--------|---------|
| POST | `/api/v1/auth/register` | 201 | `BFFResponse[UserBFF]` + Set-Cookie |
| POST | `/api/v1/auth/login` | 200 | `BFFResponse[UserBFF]` + Set-Cookie |
| POST | `/api/v1/auth/logout` | 200 | `BFFResponse[None]` + Clear-Cookie |

### GET /api/v1/users/me
```python
@router.get("/users/me", response_model=BFFResponse[UserBFF])
async def get_current_user_info(current_user: User = Depends(get_current_user)): ...
```

### Frontend Store
```typescript
interface AuthState {
  user: UserBFF | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hydrated: boolean;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit (use cases) | `LoginUserUseCase` — valid login, wrong email, wrong password, user not found, password hash failure | Direct instantiation with FakeUserRepo; assert return User or `pytest.raises(DomainError)` |
| Unit (use cases) | `RegisterUserUseCase` — valid register with password hash, duplicate email | Same; verify `hashed_password` field set, verify EMAIL_EXISTS raised |
| Integration (API) | Register → 201 + Set-Cookie → `/users/me` returns user | `httpx.AsyncClient` with `ASGITransport`; verify cookie in response headers; follow-up request auto-sends cookie |
| Integration (API) | Login → 200 + Set-Cookie → `/users/me` returns user | Same |
| Integration (API) | Duplicate email → 409 EMAIL_EXISTS | Post twice, check status |
| Integration (API) | Wrong password → 401 INVALID_CREDENTIALS | Register, login with wrong password |
| Integration (API) | Wrong email → 401 INVALID_CREDENTIALS | Login with non-existent email, check same error code |
| Integration (API) | No cookie → `/users/me` → 401 | Call without cookie |
| Integration (API) | Logout → cookie cleared → `/users/me` → 401 | Register, logout, try /users/me |
| Integration (API) | Expired/tampered cookie → 401 | Manually craft expired JWT, call /users/me |
| Integration (API) | `POST /api/v1/users` (old) removed → 404 | Call old endpoint, confirm 404 |
| Frontend (vitest) | `authStore` — login updates state, hydrate fetches user, logout clears state | Mock `api` module, test store actions |
| Frontend (vitest) | `ProtectedRoute` — renders Outlet when authenticated, Navigate when not | Render with mock store states |
| Frontend (vitest) | `LoginPage` — toggle between modes, validation errors, submit calls store | Render, fill fields, submit, assert store called |
| Frontend (vitest) | `Header` — shows login link when anonymous, business_name + logout when auth | Render with different store states |

Cookie testing note: `httpx.AsyncClient` in ASGI mode handles `Set-Cookie` headers transparently — follow-up requests on the same client instance auto-include stored cookies. No manual cookie jar management needed.

## Migration / Rollout

No migration required. `hashed_password` is optional (`None` by default) so existing test fixtures and fake repos don't break. Old `POST /api/v1/users` endpoint removed — frontend never used it (was query-param based with no password). Deployed backend needs `.env` to include `JWT_SECRET_KEY` or use the dev default.

## Implementation Order

1. **Domain**: `hashed_password` on User model, `DomainError` exception class
2. **Dependencies**: `python-jose` + `passlib[bcrypt]` in pyproject.toml
3. **Use cases**: Update `RegisterUserUseCase` (password hashing, dup check), create `LoginUserUseCase`
4. **Auth helpers**: `backend/src/api/auth/helpers.py` — JWT encode/decode, cookie utilities, `get_current_user`
5. **Shared DI**: `backend/src/api/dependencies.py` — move `get_user_repo` here
6. **Auth routes**: `backend/src/api/routes/auth.py` — register, login, logout
7. **Update users route**: Remove POST, add GET /users/me
8. **Update main.py**: Wire auth router, remove old users POST reference
9. **Update settings**: Add JWT fields to Settings
10. **Backend tests**: Rewrite user tests, add full auth scenario tests
11. **Frontend deps**: `axios`, `zustand` in package.json; Vite proxy
12. **Frontend lib/api.ts**: Axios instance
13. **Frontend authStore**: Zustand store with hydrate/login/register/logout
14. **Frontend ProtectedRoute**: Route guard component
15. **Frontend LoginPage**: Refactor with toggle, registration fields, store calls
16. **Frontend App.tsx**: Wire ProtectedRoute, hydrate on mount
17. **Frontend Header**: Auth-aware nav
18. **Frontend tests**: Auth store, protected route, login page, header

Steps 1–10 can be validated independently from frontend (httpx test suite). Steps 11–18 are frontend only.
