# SDD Spec: Auth + Frontend-Backend Connection

**Change**: `auth-and-frontend-connection`
**Project**: AsistenteTributarioSV (tax assistant for El Salvador)

---

## 1. Functional Requirements

### 1.1 Registration

- `POST /api/v1/auth/register` — JSON body
- Required: `email`, `password`, `business_name`, `business_type`, `nit`, `regimen_fiscal`
- Optional: `nrc`
- Password ≥ 8 chars (backend validation)
- Email unique → duplicate returns **409 EMAIL_EXISTS**
- Backend hashes password with bcrypt (12 rounds), stores `hashed_password` on User
- On success: creates user, generates JWT, **sets httpOnly cookie**, returns **201** with `BFFResponse<UserBFF>`
- Registration auto-logs in the user (cookie is set)

### 1.2 Login

- `POST /api/v1/auth/login` — JSON body
- Required: `email`, `password`
- Lookup by email via `repo.get_by_email()`
- Verify password with bcrypt
- **Same error for wrong email vs wrong password**: `INVALID_CREDENTIALS` — **401**
- On success: generate JWT, set httpOnly cookie, return **200** with `BFFResponse<UserBFF>`

### 1.3 Logout

- `POST /api/v1/auth/logout` — no body
- Sets `Set-Cookie: access_token=; HttpOnly; Path=/api; Max-Age=0; SameSite=Strict`
- Returns **200** with empty `BFFResponse`

### 1.4 Get Current User

- `GET /api/v1/users/me` — protected
- Reads `access_token` cookie, validates JWT, extracts `sub` (user_id), fetches user
- Cookie missing or invalid → **401 UNAUTHENTICATED**
- Success → **200** with `BFFResponse<UserBFF>`

### 1.5 Protected Routes (Frontend)

- `ProtectedRoute` wraps routes that require auth
- Checks Zustand store `isAuthenticated`
- Not authenticated → redirect to `/login`
- Authenticated → render `<Outlet />`

### 1.6 Public Routes

- `/` (Home), `/calculadora` (Calculator), `/contacto` (Contact) always accessible
- `/login` accessible, but if already authenticated → redirect to `/`

### 1.7 Auth-Aware Navigation

- Anonymous: Header shows "Iniciar sesión" link → `/login`
- Authenticated: Header shows `business_name` (truncated ~20 chars) + "Cerrar sesión" button
- "Cerrar sesión" calls `POST /api/v1/auth/logout`, clears store, redirects `/`

---

## 2. Endpoint Specifications

### 2.1 `POST /api/v1/auth/register`

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "securePass123",
  "business_name": "Mi Empresa S.A. de C.V.",
  "business_type": "persona_juridica",
  "nit": "0614-290798-101-1",
  "nrc": "12345",
  "regimen_fiscal": "general"
}
```

| Status | Body | Cookies |
|--------|------|---------|
| **201** | `BFFResponse<UserBFF>` | `Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/api; Max-Age=86400` |
| **409** | `BFFResponse` — `errors: [{code: "EMAIL_EXISTS", message: "El correo ya está registrado"}]` | — |
| **422** | FastAPI validation errors | — |

### 2.2 `POST /api/v1/auth/login`

**Request body:**
```json
{"email": "user@example.com", "password": "securePass123"}
```

| Status | Body | Cookies |
|--------|------|---------|
| **200** | `BFFResponse<UserBFF>` | `Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/api; Max-Age=86400` |
| **401** | `BFFResponse` — `errors: [{code: "INVALID_CREDENTIALS", message: "Credenciales inválidas"}]` | — |

### 2.3 `POST /api/v1/auth/logout`

| Status | Body | Cookies |
|--------|------|---------|
| **200** | `BFFResponse(data=None)` | `Set-Cookie: access_token=; HttpOnly; Path=/api; Max-Age=0; SameSite=Strict` |

### 2.4 `GET /api/v1/users/me`

**Request:** Cookie: `access_token=<jwt>`

| Status | Body |
|--------|------|
| **200** | `BFFResponse<UserBFF>` |
| **401** | `BFFResponse` — `errors: [{code: "UNAUTHENTICATED", message: "No autenticado"}]` |

---

## 3. Data Model Changes

### 3.1 User Model

Add field:
```python
hashed_password: str | None = None
```

### 3.2 JWT Claims

```json
{"sub": "<user_id>", "email": "<email>", "exp": <unix_timestamp + 86400>}
```

---

## 4. Security Requirements

| Requirement | Implementation |
|-------------|---------------|
| Token storage | httpOnly + SameSite=Strict cookie only. No JS access |
| No user enumeration | Same `INVALID_CREDENTIALS` for wrong email OR wrong password |
| Password hashing | bcrypt via `passlib`, 12 rounds |
| JWT signing | `python-jose[cryptography]` with HS256, secret key from Settings |
| JWT validation | On every protected request via FastAPI `get_current_user` dependency |
| Cookie path | `/api` — only sent to API routes |

---

## 5. Frontend Component Specifications

### 5.1 Zustand Auth Store

```typescript
interface AuthState {
  user: UserBFF | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hydrate: () => Promise<void>;   // GET /users/me on mount
  login: (email, password) => Promise<void>;
  register: (data) => Promise<void>;
  logout: () => Promise<void>;
}
```

### 5.2 Axios Client

```typescript
const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});
```

### 5.3 LoginPage (Refactored)

- Two modes: `login` | `register`, controlled by toggle
- Toggle: "¿No tenés cuenta? Registrate" / "¿Ya tenés cuenta? Iniciá sesión"
- Register mode adds fields: business_name, business_type (select), nit, nrc (opt), regimen_fiscal (select)
- Client-side validation: email, password ≥ 8, NIT pattern, required fields
- Success → redirect `/`, error → display API error

### 5.4 ProtectedRoute

```tsx
function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuthStore();
  if (isLoading) return <Spinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}
```

### 5.5 Routes

```tsx
<Route path="/" element={<HomePage />} />
<Route path="/calculadora" element={<CalculatorPage />} />
<Route path="/contacto" element={<ContactPage />} />
<Route path="/login" element={<LoginPage />} />
<Route element={<ProtectedRoute />}>
  <Route path="/documentos" element={<DocumentosPage />} />
</Route>
```

### 5.6 Header

- Anonymous → "Iniciar sesión" link
- Authenticated → `business_name` + "Cerrar sesión"
- "Cerrar sesión" → `authStore.logout()`

---

## 6. Configuration

### 6.1 Backend Settings

Add to `Settings`:
```python
jwt_secret_key: str = "dev-secret-change-in-prod"
jwt_algorithm: str = "HS256"
jwt_expire_minutes: int = 1440  # 24h
```

### 6.2 Vite Proxy

```js
server: { proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } }
```

### 6.3 Dependencies

**Backend**: `python-jose[cryptography]>=3.3.0`, `passlib[bcrypt]>=1.7.4`
**Frontend**: `axios`, `zustand`

---

## 7. Cookie Details

| Property | Value |
|----------|-------|
| Name | `access_token` |
| httpOnly | `true` |
| SameSite | `Strict` |
| Secure | `true` (prod), configurable for dev |
| Path | `/api` |
| Max-Age | `86400` (24h) |

---

## 8. Removed Endpoints

- `POST /api/v1/users` (old query-param based, no password) — removed in favor of `POST /api/v1/auth/register`
- All existing fake repos and DynamoDB repos remain unchanged (password field is additive)

## 9. Test Scenarios

- Register → 201 + cookie → `/users/me` returns user
- Login → 200 + cookie → `/users/me` returns user
- Duplicate email → 409
- Wrong password → 401 (same error as wrong email)
- No cookie → `/users/me` → 401
- Expired/tampered cookie → 401
- Unauth → protected route → redirect `/login`
- Auth → `/login` → redirect `/`
- Logout → cookie cleared → `/users/me` → 401
