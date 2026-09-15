# Scalable E-Commerce Platform

![Backend Tests](https://github.com/vedantgonbare/ecommerce-platform/actions/workflows/backend-tests.yml/badge.svg)
![Frontend Tests](https://github.com/vedantgonbare/ecommerce-platform/actions/workflows/frontend-tests.yml/badge.svg)

A full-stack e-commerce platform built as a structured, hands-on learning project — a modular
monolith backend (FastAPI, PostgreSQL, Redis, Celery, Stripe) paired with a React frontend
(Vite, Tailwind, TanStack Query, React Router).

## Status

✅ Core build complete (40/40 planned days) — backend and frontend fully wired end-to-end,
covered by automated tests and CI on every push.

See [`docs/architecture.md`](docs/architecture.md) for the full day-by-day build log and
the reasoning behind major decisions.

## Features

- **Auth** — registration, login, httpOnly-cookie-based JWT access + refresh tokens, logout,
  server-side refresh token revocation via Redis
- **Product catalog** — hierarchical categories (with cycle detection), full CRUD, Postgres
  full-text search, pagination and filtering
- **Cart** — persistent per-user cart, bump-not-duplicate items
- **Redis caching** — cache-aside pattern on product listings, pattern-based invalidation on writes
- **Orders** — cart-to-order conversion with row-level stock locking, order history, self-cancel
- **Payments** — Stripe Checkout Sessions, webhook-driven order status updates, success/cancel pages
- **Background jobs** — Celery tasks for order and payment confirmation
- **Reviews** — verified-purchase-only reviews, one review per user per product, full CRUD
- **Frontend** — full React UI for every module above: auth, product browsing, cart, checkout,
  order history, and reviews

## Tech Stack

**Backend:** Python 3.13, FastAPI, PostgreSQL 16, SQLAlchemy 2.0 (async, asyncpg), Alembic,
Pydantic v2, Redis, Celery, Stripe SDK, Docker & Docker Compose

**Frontend:** React (Vite), Tailwind CSS v4, React Router, TanStack Query

**Testing:** pytest + pytest-asyncio + httpx (backend), Vitest + React Testing Library (frontend)

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

```
ecommerce-platform/
├── backend/          # FastAPI app — app/modules/<domain>/ per feature
├── frontend/         # React (Vite) app
├── docs/
│   └── architecture.md   # Full build log and design decisions
└── .github/workflows/    # CI pipelines
```