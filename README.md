# E-Commerce Platform

![Backend Tests](https://github.com/vedantgonbare/ecommerce-platform/actions/workflows/backend-tests.yml/badge.svg)
![Frontend Tests](https://github.com/vedantgonbare/ecommerce-platform/actions/workflows/frontend-tests.yml/badge.svg)

A full-stack e-commerce platform built as a structured, hands-on learning project — a modular
monolith backend (FastAPI, PostgreSQL, Redis, Celery, Stripe) paired with a React frontend
(Vite, Tailwind, TanStack Query, React Router).

## Status

Core build complete and functional end-to-end — auth, catalog, cart, orders, payments, and
reviews all wired from backend to frontend, covered by automated tests, and running on CI for
every push. The project went through a post-launch hardening pass (admin-only write access,
stock restoration on cancel, idempotent payment webhooks, deadlock prevention) and a design
pass (full UI restyle, numbered pagination, category filtering) after the initial build.

See [`docs/architecture.md`](docs/architecture.md) for the full day-by-day build log and
the reasoning behind major decisions.

## Features

- **Auth** — registration, login, httpOnly-cookie-based JWT access + refresh tokens, logout,
  server-side refresh token revocation via Redis
- **Admin role** — `is_admin` flag with a `require_admin` dependency gating product and
  category writes; all reads stay public
- **Product catalog** — hierarchical categories (with cycle detection), full CRUD, Postgres
  full-text search backed by a GIN index, pagination and category filtering
- **Cart** — persistent per-user cart, bump-not-duplicate items
- **Redis caching** — cache-aside pattern on product listings, pattern-based invalidation on writes
- **Orders** — cart-to-order conversion with row-level stock locking (deadlock-safe, sorted lock
  order), order history, self-cancel with automatic stock restoration
- **Payments** — Stripe Checkout Sessions, idempotent webhook-driven order status updates,
  success/cancel pages
- **Background jobs** — Celery tasks for order and payment confirmation. These **simulate**
  email (a short delay plus a log line) rather than sending real messages — no email provider
  is wired up, by design, to keep the focus on the task-queue mechanics
- **Reviews** — verified-purchase-only reviews, one review per user per product, full CRUD
- **Frontend** — full React UI for every module above: auth with session persistence, product
  browsing with category filters and pagination, cart, checkout, order history, and reviews,
  styled with a consistent design system

## Tech Stack

**Backend:** Python 3.13, FastAPI, PostgreSQL 16, SQLAlchemy 2.0 (async, asyncpg), Alembic,
Pydantic v2, Redis, Celery, Stripe SDK, Docker & Docker Compose

**Frontend:** React (Vite), Tailwind CSS v4, React Router, TanStack Query

**Testing:** pytest + pytest-asyncio + httpx (72 backend tests), Vitest + React Testing Library
(frontend)

**CI:** GitHub Actions — backend and frontend test suites run independently on every push/PR

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js (for the frontend)
- Python 3.13 (for running backend tests/Alembic outside Docker)

### Backend

```bash
# from the repo root
docker compose up -d

# from backend/
cd backend
alembic upgrade head
```

The API will be available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

### Running tests

```bash
# backend (from backend/, with Docker's db/redis running)
python -m pytest -v

# frontend (from frontend/)
npm test -- --run
```

## Project Structure

ecommerce-platform/
├── backend/ # FastAPI app — app/modules/<domain>/ per feature
├── frontend/ # React (Vite) app
├── docs/
│ └── architecture.md # Full build log and design decisions
└── .github/workflows/ # CI pipelines


## Known Limitations

These are documented, deliberate scope decisions made while building this as a learning
project — not oversights:

- **Refresh tokens are revoked on logout but not rotated** — each login issues one refresh
  token that's reused until it expires or is revoked, rather than being replaced on every use
- **The duplicate-review race condition is unresolved by design** — review creation uses a
  query-then-insert check rather than a database-level constraint, so two near-simultaneous
  requests could both pass the check (acceptable at this project's scale)
- **No concurrency/load testing** — row-level locks on stock and order status are correct by
  code review and consistent lock ordering, but haven't been proven under genuine concurrent
  load
- **Redis cache has no automated test coverage** — correctness verified manually
- **No admin UI** — the admin role is enforced on the backend, but promoting a user to admin
  is a direct database update, not a dashboard action
- **Order status stops at `cancelled`/`paid`** — `shipped`/`delivered` transitions aren't
  implemented, since they'd need an admin interface to trigger them
- **Stripe SDK calls are synchronous** inside async route handlers (the SDK isn't async-native)
- **Cart quantity updates have no debounce** — each keystroke in the quantity field fires a
  request