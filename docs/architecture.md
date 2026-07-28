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

### Day 9 — Refresh Tokens + Protected Routes
Built create_refresh_token() (7-day expiry) and get_current_user() as a reusable
FastAPI dependency — decodes the JWT from the Authorization header via
OAuth2PasswordBearer, validates signature/expiry/type, fetches the user from
the DB. Every future protected route just adds Depends(get_current_user)
instead of reimplementing auth logic.

Both access and refresh tokens carry a "type" claim (access/refresh) — without
it, a leaked refresh token could be used directly on protected routes instead
of being restricted to /auth/refresh.

POST /auth/refresh reuses the same refresh token rather than rotating it
(stateless design) — simpler, but means a stolen refresh token can't be
revoked before it expires. Flagged as a Week 8 stretch goal once refresh
tokens are stored server-side.

Key lesson: hit the same missing-import pattern twice today (RefreshRequest,
then create_refresh_token) — worth building the habit of adding an import
the moment a new name is used, not after hitting a NameError.

### Day 10 — Testing + Week 2 Recap

**Testing setup:** Chose a separate test database (`ecommerce_test`) over
reusing the dev DB — avoids polluting real data and lets tests run repeatedly
without duplicate-email conflicts. `conftest.py` handles the whole lifecycle:
[explain in your own words — env var override before app import, session-scoped
table create/drop fixture, async test client via httpx + ASGITransport,
get_db dependency override].

**Event loop gotcha:** Hit an asyncpg InterfaceError because pytest-asyncio
was creating a new event loop per test, but the DB engine was tied to the
loop from the session-scoped fixture. Fixed via pytest.ini setting
asyncio_default_fixture_loop_scope = session — [explain why in your own words].

**First automated tests written:** test_register_success, 
test_register_duplicate_email, test_login_success — covering the two main
happy/failure paths in the auth flow for the first time with actual test
code instead of manual Postman checks.

**Week 2 recap (bcrypt + JWT):** [your reasoning on bcrypt's tunable slowness,
access vs refresh token tradeoffs, and the stateless-refresh-token limitation
we've flagged as a Week 8 stretch goal]

---

## Week 3 — Product Catalog

### Day 11 — Category Model
Built a self-referencing Category model (nullable parent_id) to support
hierarchical categories (e.g. Electronics > Laptops) without a separate
join table — a single FK pointing back to the same table. Slugs are
auto-generated from the name at creation time and enforced unique at the
DB level, since URLs and lookups should use human-readable identifiers
rather than raw UUIDs.

Known deferred gap: no cycle-detection on parent_id (a category could in
theory be set as its own ancestor). Acceptable for now since categories are
admin-created, not user-generated, but flagged as a real gap if this were
production-facing.

### Day 12–13 — Product CRUD
Product's category_id is a required FK, not nullable — every product must
belong to a category, there's no "uncategorized" state to handle downstream.
price uses Numeric(10,2) / Decimal rather than float — floats introduce
rounding errors in monetary values (0.1 + 0.2 != 0.3 territory), which is
unacceptable once real money is involved. Deliberately left out a SKU field
for now — not every catalog needs one, and adding it later is a straightforward
migration versus overengineering a field with no current use.

Full CRUD follows the same router/service split as auth: routers translate
service-layer exceptions (CategoryNotFoundError, ProductNotFoundError) into
HTTP status codes, services hold the actual logic.

### Day 14 — Full-Text Search
Built GET /products/search using Postgres's to_tsvector/plainto_tsquery rather
than a plain ILIKE '%query%'. The win over ILIKE is language-awareness —
stemming (e.g. "running" matches "run") and stopword handling — plus ts_rank
for relevance ordering, not raw speed.

Two deliberate scope calls, both documented tradeoffs rather than oversights:
- Search scope is name-only, not name + description. Simpler, and matches the
  most common real-world search intent for a catalog this size.
- The tsvector is computed on-the-fly per query, not stored as a generated
  column with a GIN index. This means no index-backed speed advantage over
  ILIKE at scale — for a learning project's data volume this is a non-issue,
  but at real scale this is the first thing I'd revisit (stored tsvector
  column + GIN index removes the per-query computation cost entirely).

Route ordering lesson (re-learned, first hit back in an earlier week too):
/search must be registered before /{product_id} in router.py — FastAPI
matches routes in registration order, so a dynamic path registered first
will try to parse the literal string "search" as a UUID and 422 instead of
ever reaching the search handler.

### Day 15 — Pagination, Filtering, pytest Suite

**Pagination + filtering:** GET /products/ now accepts limit/offset and an
optional category_id filter, wrapped in a ProductListResponse
({total, limit, offset, items}). The count and the paginated results are
built from the same base query (count via
select(func.count()).select_from(base_query.subquery())) rather than two
independently-constructed queries — this guarantees the total can never
drift out of sync with what filters were actually applied.

**Bug found:** auth_router was imported in main.py but never passed to
app.include_router() — the entire /auth prefix was silently 404ing. A good
reminder that "imported" and "wired up" are two different things FastAPI
won't warn you about.

**pytest suite for products (11 tests):** covers create (success + 400 on a
nonexistent category), get (200 + 404), update (partial-field correctness,
and specifically a zero-value case — price/stock set to 0 — since exclude_unset
logic can silently break on falsy-but-valid values if it's ever written as a
truthiness check instead of a key-presence check), delete (204 then 404),
search (with results + empty), and pagination/filtering. Each test creates
its own isolated category rather than asserting against the DB's grand total,
since the test DB's tables are created once per test session (not wiped per
test) — assertions have to be scoped to data the test itself created.

**Dev workflow addition:** Docker Compose now bind-mounts ./backend:/app and
uvicorn runs with --reload, so plain code changes take effect on save without
a full docker-compose up --build. --build is still required when
requirements.txt or the Dockerfile itself changes. This is a deliberate
dev-only convenience — production builds intentionally skip bind mounts,
since they undermine image immutability (a running container should reflect
exactly what was baked into the image, not whatever happens to be on disk).