# Architecture Notes

Running log of key decisions and lessons, day by day.

---

## Week 1 — Foundations & Setup

### Day 1 — Repo & Folder Skeleton
Set up the repo structure (backend/app/core, modules, db, tests) and .gitignore
from day one — secrets and venvs never enter git history.

### Day 2 — FastAPI Skeleton + Config
Used pydantic-settings for env-based config instead of hardcoding values —
avoids leaking secrets into source, and lets the same code run against
different environments just by swapping .env files.

### Day 3 — Dockerized Backend
Wrote Dockerfile + docker-compose.yml (backend + Postgres). Learned containers
reach each other by service name (e.g. db), not localhost — a distinction that
mattered a lot more later (Day 7).

### Day 4 — Async SQLAlchemy Setup
Used SQLAlchemy 2.0's async engine with asyncpg rather than sync SQLAlchemy.
FastAPI is async-first; a sync driver would block the event loop on every query.

### Day 5 — Alembic + First User Model
Chose Alembic over Base.metadata.create_all() — gives versioned migration
history and handles ALTER operations, not just initial table creation.

**Key lesson:** a native Windows Postgres install was independently listening
on port 5432, separate from Docker's Postgres — Alembic sometimes connected to
the wrong instance, causing confusing InvalidPasswordError issues. Fixed by
remapping Docker's Postgres to host port 5433. Also learned: POSTGRES_PASSWORD
belongs only in the root .env (used by Compose), not backend/.env; and Postgres
only applies POSTGRES_PASSWORD on first init of an empty volume — a stale
volume needs docker-compose down -v to reset.

---

## Week 2 — Auth Module

### Day 6 — Password Hashing
Extended User with hashed_password + is_active via a proper Alembic ALTER
migration. Chose bcrypt specifically — its tunable slowness resists brute-force
even if a hash leaks, unlike fast hashes (SHA-256) which are the wrong tool for
passwords.

### Day 7 — Registration Endpoint
Built POST /auth/register with router (HTTP concerns) separated from service
(business logic) — keeps logic testable and reusable outside HTTP. response_model
=UserResponse is what actually strips hashed_password from responses. Duplicate
email → 409 via a custom exception, not a raw 500.

**Key lesson:** several dependencies (sqlalchemy, asyncpg, greenlet,
email-validator) had only been installed locally, never pinned in
requirements.txt — invisible until a real Docker --build. Also hit a
passlib/bcrypt version incompatibility (bcrypt 5.0.0 broke passlib 1.7.4's
hashing) — fixed by pinning bcrypt==4.0.1. Dependency version mismatches are a
real, recurring bug category worth watching for.

### Day 8 — JWT Login
Built create_access_token() (python-jose) + POST /auth/login. JWT payload keeps
minimal claims (sub, exp) — a JWT is signed, not encrypted, so nothing sensitive
belongs in the payload. HS256 is sufficient for a single-backend setup. Access
tokens expire in 15 min, deliberately short, to limit damage from a leaked
token (this is why refresh tokens exist — Day 9). Both "user not found" and
"wrong password" return the same generic 401 — distinct messages would leak
which emails are registered (user enumeration).

**Key lesson:** hit a circular import — security.py accidentally imported from
itself (a line meant for service.py got pasted into the wrong file). Worth
double-checking which file an edit is meant to land in when juggling several
similarly-structured files.