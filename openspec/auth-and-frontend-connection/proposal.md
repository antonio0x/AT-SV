# Proposal: Auth + Frontend-Backend Connection

## Intent
Connect the frontend to the real API with end-to-end authentication (register + login with JWT in httpOnly cookies), protected routes, and auth-aware UI.

## Scope

### In Scope
- **Backend**: `hashed_password` on User model; `POST /auth/register` hashes password; `POST /auth/login` verifies credentials, issues JWT via httpOnly SameSite cookie; `get_current_user` FastAPI dependency reads cookie; `GET /users/me` protected endpoint
- **Frontend**: Axios client with `credentials: 'include'`; Zustand auth store (reads `/users/me` on mount); LoginPage refactored with login/register toggle; ProtectedRoute component; Header auth-aware nav (login link vs username+logout); Vite proxy `/api` → `localhost:8000`
- **Config**: JWT settings in Settings class; `python-jose` + `passlib[bcrypt]` deps; `axios` + `zustand` frontend deps

### Out of Scope
- Google OAuth or social login
- Refresh tokens / token rotation
- Email verification / password reset
- Profile completion
- RBAC / admin roles

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Token storage | httpOnly SameSite cookie | XSS-safe from day 1; backend sets cookie; no JS access needed |
| Dev API routing | Vite proxy (`/api` → `localhost:8000`) | Same-origin in dev avoids CORS entirely; same as prod |
| Auth state | Zustand store, hydrated via `GET /users/me` | Cookie auto-sent on mount; store reflects real auth state |
| Password storage | On User model (`hashed_password` field) | Simpler than separate auth table |
| Token type | Single access token, 24h expiry | No refresh token complexity for v1 |
| Auth endpoints | POST JSON body (not query params) | Proper semantics for credentials |

## Auth Flow

```
Registration:
  POST /api/v1/auth/register { email, password, business_name, business_type, nit, ... }
  → Backend hashes password with bcrypt, creates User, sets httpOnly cookie with JWT
  → Response 201 with user data

Login:
  POST /api/v1/auth/login { email, password }
  → Backend verifies bcrypt hash, issues JWT in Set-Cookie header
  → Response 200 with user data

Authenticated request:
  Browser auto-sends cookie → Backend reads cookie → get_current_user resolves user
  → GET /api/v1/users/me returns user profile

Frontend auth state hydration:
  App mounts → zustand store calls GET /api/v1/users/me
  → If 200: user is authenticated, store populated
  → If 401: user is anonymous, redirect to /login
```

## Success Criteria
- [ ] User registers via frontend → receives httpOnly cookie → is authenticated
- [ ] User logs in → receives httpOnly cookie → is authenticated
- [ ] JavaScript cannot read the JWT token (XSS-safe)
- [ ] Protected routes redirect unauthenticated users to `/login`
- [ ] Public pages (Home, Calculator) are accessible without auth
- [ ] Header shows login/register when anonymous, username+logout when authenticated
- [ ] Login/register toggle switches seamlessly on the same page
