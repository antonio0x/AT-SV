# Archive: Auth + Frontend-Backend Connection

**Change**: `auth-and-frontend-connection`
**Archived**: 2026-06-16
**PRs**: #1 (Backend Auth), #2 (Frontend Connection)
**SDD Cycle**: Complete — planned, implemented, verified, archived

---

## Summary

End-to-end authentication connecting the frontend to the real API. Users can register and login via the UI, receive a JWT in an httpOnly SameSite cookie (XSS-safe), and access protected routes. The auth state is managed by a Zustand store hydrated via `GET /users/me` on every mount.

---

## What Was Implemented

### PR #1 — Backend Auth

| Area | Details |
|------|---------|
| Domain | `hashed_password` on User model, `DomainError` exception class |
| Use cases | `RegisterUserUseCase` — bcrypt hashing + duplicate email check; `LoginUserUseCase` — email lookup + bcrypt verify |
| Auth helpers | JWT encode/decode (HS256), httpOnly cookie set/clear, `get_current_user` FastAPI dependency |
| Endpoints | `POST /api/v1/auth/register` (201), `POST /api/v1/auth/login` (200), `POST /api/v1/auth/logout` (200), `GET /api/v1/users/me` (200) |
| Config | JWT settings in Settings class (`jwt_secret_key`, `jwt_algorithm`, `jwt_expire_minutes`) |
| Dependencies | `python-jose[cryptography]>=3.3.0`, `passlib[bcrypt]>=1.7.4` |
| Removed | Old `POST /api/v1/users` (query-param, no password) |

### PR #2 — Frontend Connection

| Area | Details |
|------|---------|
| API client | Axios instance with `baseURL: '/api/v1'`, `withCredentials: true` |
| Auth store | Zustand — `hydrate()`, `login()`, `register()`, `logout()` |
| Auth UI | LoginPage with login/register toggle, registration fields (business info, NIT, regimen fiscal), client-side validation |
| Route guard | `ProtectedRoute` — shows spinner while loading, redirects to `/login` if unauthenticated |
| Auth-aware nav | Header shows "Iniciar sesión" when anonymous, `business_name` + "Cerrar sesión" when authenticated |
| Routing | `/documentos` wrapped in ProtectedRoute; `/login` redirects to `/` if already authenticated |
| Vite proxy | `/api` → `http://localhost:8000` (same-origin dev, no CORS) |
| New deps | `axios`, `zustand` |

---

## Test Results

### Backend: 72 tests passing

| Category | Tests |
|----------|-------|
| Auth API integration | Register → cookie → `/users/me`; Login → cookie → `/users/me`; duplicate email → 409; wrong password → 401; wrong email → 401; no cookie → 401; logout → cookie cleared; expired/tampered cookie → 401 |
| Use cases | Register with password hash, duplicate email, login valid/invalid |
| Removed endpoint | Old `POST /api/v1/users` → 404 |

### Frontend: 45 tests passing (5 test files)

| Test file | Scope |
|-----------|-------|
| `authStore.test.ts` | Login updates state, hydrate fetches user, logout clears state |
| `ProtectedRoute.test.tsx` | Renders Outlet when authenticated, Navigate when not |
| `LoginPage.test.tsx` | Toggle between modes, validation errors, submit calls store |
| `Header.test.tsx` | Login link when anonymous, business_name + logout when auth |
| (additional integration) | Full login/register flow with mocked API |

### TypeScript: 0 errors

### Verification Findings (all fixed)

| Finding | Status |
|---------|--------|
| Remove `Secure` flag on cookie when `settings.debug=True` for HTTP dev | Fixed |
| Add short-password test case (5 chars → 422 validation) | Fixed |
| Login redirect test: verify `Navigate` renders at `/` when already authenticated | Fixed |

### Spec-Scenario Coverage: 13/13 verified

| # | Scenario | Status |
|---|----------|--------|
| 1 | Register → 201 + cookie → `/users/me` returns user | ✅ |
| 2 | Login → 200 + cookie → `/users/me` returns user | ✅ |
| 3 | Duplicate email → 409 | ✅ |
| 4 | Wrong password → 401 (same error as wrong email) | ✅ |
| 5 | No cookie → `/users/me` → 401 | ✅ |
| 6 | Expired/tampered cookie → 401 | ✅ |
| 7 | Unauth → protected route → redirect `/login` | ✅ |
| 8 | Auth → `/login` → redirect `/` | ✅ |
| 9 | Logout → cookie cleared → `/users/me` → 401 | ✅ |
| 10 | Register with short password → 422 | ✅ |
| 11 | Old `POST /api/v1/users` → 404 | ✅ |
| 12 | NIT validation on frontend registration form | ✅ |
| 13 | Auth-aware header (anonymous vs authenticated) | ✅ |

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Token storage | httpOnly SameSite=Strict cookie | XSS-safe; no JS access to token |
| Dev API routing | Vite proxy (`/api` → `localhost:8000`) | Same-origin in dev avoids CORS entirely |
| Auth state | Zustand store, hydrated via `GET /users/me` | Cookie auto-sent on mount; store reflects real state |
| Password hashing | bcrypt via passlib, 12 rounds | Industry standard |
| JWT signing | HS256, `python-jose[cryptography]` | Simple, sufficient for v1 |
| Token expiry | Single access token, 24h | No refresh token complexity for v1 |
| Error uniqueness | Same `INVALID_CREDENTIALS` for wrong email OR password | Prevents user enumeration |
| Cookie Secure flag | Controlled by `settings.debug` | Development over HTTP needs Secure=false |
| Use case error signaling | `DomainError` exception | Clean Architecture: use case doesn't import FastAPI |
| Cookie path | `/api` — only sent to API routes | Limits cookie exposure |

---

## Artifacts

| Artifact | Path |
|----------|------|
| Proposal | `openspec/auth-and-frontend-connection/proposal.md` |
| Spec | `openspec/auth-and-frontend-connection/spec.md` |
| Design | `openspec/auth-and-frontend-connection/design.md` |
| Tasks | `openspec/auth-and-frontend-connection/tasks.md` |
| Archive report | `openspec/auth-and-frontend-connection/archive.md` |

---

## Remaining Work / Future Improvements

| Item | Priority | Notes |
|------|----------|-------|
| Password reset flow | Medium | Spec'd but not implemented; requires email integration |
| Google OAuth / social login | Low | Out of scope for v1 |
| Refresh tokens / token rotation | Low | Single 24h token sufficient for initial launch |
| Email verification | Low | Out of scope for v1 |
| Profile completion flow | Low | Out of scope for v1 |
| RBAC / admin roles | Low | Out of scope for v1 |
| DynamoDB conditional write for dup email | Low | TOCTOU race accepted for v1 |
| Frontend password strength indicator | Low | Enhancement for registration UX |
| Remember me / extended sessions | Low | Would require refresh token infrastructure |
