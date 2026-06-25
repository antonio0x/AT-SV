# SDD Tasks: Auth + Frontend-Backend Connection

## Delivery Assessment

**Estimated total**: ~980 lines
**Review budget**: 400 lines
**Decision**: CHAINED PRs — stacked-to-main

**PR #1 — Backend Auth** (T1–T11): ~340 lines
**PR #2 — Frontend Connection** (T12–T19): ~610 lines

## Dependency Graph

```
T1 ──→ T3 ──→ T4 ──→ T5 ──→ T6 ──→ T7 ──→ T8 ──→ T9 ──→ T10 ──→ T11
 │     │      │                       │      │
 │     │      └───────────────────────┘      │
 │     │                                     │
 └─→ T2                                      │
                                             │
T12 ─→ T13 ─→ T14 ─→ T15 ──┬──→ T17
              │             │
              └──→ T16 ─────┘
                    T18
                    T19
```

## Task Groups

### PR #1 — Backend Auth

| Task | Description | Files | Est. |
|------|-------------|-------|------|
| T1 | DomainError + hashed_password on User model | `exceptions.py` (new), `user.py` (mod) | S |
| T2 | Add python-jose + passlib to pyproject.toml | `pyproject.toml` (mod) | S |
| T3 | JWT settings in Settings class | `database.py` (mod) | S |
| T4 | Shared DI: move get_user_repo to dependencies.py | `dependencies.py` (new), `users.py` (mod) | S |
| T5 | Update RegisterUserUseCase with password hashing + dup check | `register_user.py` (mod) | M |
| T6 | LoginUserUseCase | `login_user.py` (new) | M |
| T7 | Auth helpers: JWT encode/decode, cookie utils, get_current_user | `auth/__init__.py`, `auth/helpers.py` (new) | M |
| T8 | Auth routes: register, login, logout | `auth.py` (new) | M |
| T9 | Update users route: remove POST, add GET /users/me | `users.py` (mod) | S |
| T10 | Update main.py: wire auth router | `main.py` (mod) | S |
| T11 | Backend integration tests rewrite | `test_api.py` (mod) | L |

### PR #2 — Frontend Connection

| Task | Description | Files | Est. |
|------|-------------|-------|------|
| T12 | Add axios + zustand deps, Vite proxy | `package.json`, `vite.config.js` (mod) | S |
| T13 | Axios instance with withCredentials | `lib/api.ts` (new) | S |
| T14 | Zustand auth store (hydrate/login/register/logout) | `store/authStore.ts` (new) | M |
| T15 | ProtectedRoute component | `components/auth/ProtectedRoute.tsx` (new) | S |
| T16 | LoginPage refactor with toggle | `pages/LoginPage.tsx` (mod) | L |
| T17 | App.tsx wire routes + hydrate | `App.tsx` (mod) | M |
| T18 | Header auth-aware nav | `components/layout/Header.tsx` (mod) | M |
| T19 | Frontend component tests | new test files | L |
