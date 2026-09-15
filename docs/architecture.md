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


---

## Week 4 — Cart + Redis Caching

### Day 16 — Cart Model
Built Cart + CartItem as two related tables rather than a single CartItem-with-user_id
table — gives the cart itself a natural home for future metadata (status, abandoned-cart
logic) without restructuring later. Two unique constraints do real work here: Cart.user_id
is unique at the DB level, so "does this user already have a cart" can never race into a
duplicate; CartItem's composite unique constraint on (cart_id, product_id) is what makes
bump-not-duplicate structurally enforced rather than just a matter of careful service-layer
code. cascade="all, delete-orphan" on the relationship means a deleted cart takes its items
with it automatically.

### Day 17 — Cart Endpoints
Service layer keys off product_id, not cart_item.id, for update/remove — the frontend
already has product_id from wherever "add to cart" was clicked, and never needs to know an
internal cart_item id exists. CartItemResponse can't be populated by from_attributes alone
since product_name/product_price live on Product, not CartItem — the service explicitly
joins CartItem against Product to build each response. Every endpoint requires
Depends(get_current_user), the first module built that's auth-protected end-to-end from day
one. DELETE /cart/items/{product_id} deliberately returns 200 with the updated cart, not 204
— unlike deleting a product, removing a cart item leaves something meaningful (the rest of
the cart) worth returning immediately.

### Day 18 — Redis Cache-Aside Pattern
Added Redis as a Docker service (redis:7-alpine, mapped to host port 6380 to avoid the same
kind of port collision Postgres had on Day 5) and wired a redis.asyncio client as shared
infrastructure in app/core/redis.py, same pattern as the DB session.

Cached GET /products/ using cache-aside: check Redis first, on a miss query Postgres and
write the result back into Redis with a 60s TTL, on a hit skip the DB entirely. Cache keys
encode limit/offset/category_id explicitly (e.g. products:list:limit=20:offset=0:category_id=none)
since different query combinations return genuinely different data — a single flat key would
have every distinct query stomping on the same cached entry.

Measured, not assumed: a cold request took ~4.5s, the cached hit took ~50ms.

### Day 19 — Cache Invalidation
The write side of the cache: create_product, update_product, and delete_product now all
invalidate every cached list variation after their commit succeeds (invalidation happens
after the write is durable, not before — a failed commit shouldn't wipe a still-valid cache).

Since cache keys are parameterized by limit/offset/category_id, there's no way to know in
advance every combination a write might affect — the fix is a SCAN-based invalidate_pattern()
helper that deletes every key matching products:list:*, rather than trying to enumerate
exact keys. Used Redis's SCAN instead of KEYS deliberately: KEYS blocks the entire server
while it runs, which is a real bad habit to build even at small scale — SCAN iterates in
small non-blocking steps instead.

Verified end-to-end, not just "no errors": populated the cache, created a new product,
immediately confirmed the cache key was gone, then confirmed the next GET returned fresh
data including the new product rather than the stale cached list.

### Day 20 — Cart Tests + Week 4 Recap
Wrote a 9-test pytest suite for the cart module, reusing the same isolation principles as
the Week 3 products suite (every test creates its own category/product, nothing depends on
another test's leftover data). Added a shared auth_headers fixture in conftest.py — registers
a throwaway user, logs in, returns a Bearer token header — since cart is the first module
where every single test needs real authentication, not just some of them.

The bump-quantity test is the one that actually matters here: it proves two separate POSTs
to add the same product result in one row at quantity 5, not two rows at quantity 2 and 3 —
the same thing verified manually in Postman on Day 16, now automated and no longer dependent
on remembering to check it by hand. test_cart_requires_auth is the other easy one to skip
by accident — it's the only test with no auth_headers at all, proving the 401 path fires
correctly rather than only ever testing the authenticated happy path.

Full suite (auth + products + cart) passes together: 22 tests.

## Week 5 — Orders + Celery

**Day 21 — Order & OrderItem models:** Two related tables, structurally different from Cart/CartItem in the ways that matter. No per-user uniqueness on Order (a user can have many orders, unlike one cart per user). OrderItem deliberately snapshots `product_name` and `unit_price` at creation time instead of joining live against Product — the one place denormalization is correct rather than a shortcut, since an order is a historical record and must not change if a product's price changes later. Postgres `order_status` enum (`pending`/`paid`/`shipped`/`delivered`/`cancelled`) chosen over a plain string column for DB-level enforcement, consistent with the project's general preference for making invalid states structurally impossible. Re-hit and fixed the "new model must be imported in alembic/env.py" gotcha from Day 16.

**Day 22 — Order creation from cart:** The most complex service function in the project. `create_order_from_cart` uses `SELECT ... FOR UPDATE` row-level locking on each product before checking/decrementing stock, closing the classic check-then-act race condition where two concurrent requests could both see stock as available and both succeed, oversell­ing the same unit. Everything — stock decrements, order creation, cart clearing — happens inside a single transaction; if anything raises before commit, none of it persists. `InsufficientStockError` maps to 409 (not 400): the request itself is valid, it just conflicts with current state — same reasoning as the existing 409 usage for duplicate-email registration. Diagnosed and fixed a real async-SQLAlchemy `MissingGreenlet` bug: relationships can't be lazily loaded after commit in an async session; fixed via `db.refresh(order, attribute_names=["items"])`.

**Day 23 — Order listing, detail, and self-cancel:** `GET /orders/` reuses the products pagination pattern (`{total, limit, offset, items}`, one shared base query for count + results). `GET /orders/{id}` folds the ownership check directly into the query's WHERE clause rather than fetching then checking in Python — this makes "wrong owner" and "doesn't exist" produce the identical result (404), so there's no way to leak an order's existence to someone who doesn't own it. Hit the same async lazy-load problem again, this time on a list of orders rather than a single one just-committed — solved more generally with `selectinload(Order.items)` at query time instead of `refresh()` after commit, since these paths don't have a fresh single object to refresh. Order status transitions deliberately scoped to customer self-cancel only this week (`pending`/`paid` → `cancelled`); `paid`→`shipped`→`delivered` explicitly deferred until Stripe (Week 6, for `paid`) and an admin role (not yet built, for `shipped`/`delivered`) exist — a documented scope decision, not an oversight.

**Day 24 — Celery background tasks:** Added Celery as a genuinely new kind of infrastructure — a second, independent process (`celery-worker`, its own Docker Compose service, same codebase and Dockerfile as `backend`, different command) that listens to Redis for queued jobs rather than running inline in the API's request/response cycle. First task: a simulated `send_order_confirmation` (log + sleep, no real email), triggered via `.delay()` after successful order commit — `.delay()` matters specifically because calling the task function directly would block the API request for the task's full duration, defeating the purpose. Learned that `autodiscover_tasks` is lazy and doesn't reliably register tasks outside of a running worker context; switched to an explicit task-module import in `celery_app.py` for predictable registration in every context (worker, scripts, tests). Verified with real worker logs cross-referenced against the order ID returned by the API — not just a fast response, actual proof the task executed with the correct data.

**Day 25 — Orders test suite + recap:** 11-test pytest suite for orders (auth requirement, create success/empty-cart/insufficient-stock, stock-decrement-and-cart-clear correctness, list, get-by-id, get-not-found, get-wrong-owner, cancel success, cancel-already-cancelled). The wrong-owner test is the one that actually proves the ownership-filtered query works, by registering a second real user and confirming they get 404 rather than the first user's order. Celery tested via **eager mode** (`task_always_eager=True`, `task_eager_propagates=True`, set in `conftest.py`): `.delay()` runs the task synchronously in-process during tests, so the suite needs no live Redis worker and doesn't pay real task latency, while `task_eager_propagates` ensures a broken task fails the test loudly instead of being silently swallowed (the opposite of real production behavior, deliberately, for test visibility). Moved the `test_product` fixture from `test_cart.py` into shared `conftest.py` since orders needed it too — avoiding duplication ahead of Reviews (Week 7), which will need it again. Full suite: 33 tests passing (auth 3, products 11, cart 8, orders 11).


**Test coverage snapshot:** Auth 3, Products 11, Cart 8, Orders 11 — 33 total, all passing together.

---

## Week 6 — Payments (Stripe) + Notifications

**Day 26 — Checkout session creation:** Used Stripe Checkout (hosted page) over Payment Intents — less frontend work needed before Week 7's React build. No separate `Payment` table — `stripe_checkout_session_id` just lives on `Order`. `metadata={"order_id": ...}` on the session is the bridge the webhook later uses to identify the order. Prices sent in cents, not floats, for the same rounding reasons `Decimal` was chosen back in Week 3.

**Day 27 — Webhook handler:** Reads the raw request body (not a parsed schema) since Stripe's signature is computed over exact bytes. `mark_order_paid` is a separate, trusted lookup by ID only — no ownership check, since there's no user session on a webhook call. **Bug:** direct `session["metadata"]["order_id"]` access crashed on Stripe's synthetic test events, which omit metadata. Fixed with `.get()` and a guard — now the standing rule for any field from an external payload.

**Day 28 — Success/cancel pages:** No auth on these two endpoints — Stripe's redirect has no Authorization header, so the unguessable `session_id` in the URL is the proof instead. Order is looked up by `stripe_checkout_session_id`, not `order_id`, since that's all Stripe's redirect provides. **Bug:** `orders_router` was registered before `payments_router` in `main.py`, so `/orders/success` got matched by `/orders/{order_id}` first and 401'd. Fixed by reordering. Same bug class as Day 14's `/search` issue — route-ordering problems keep resurfacing at different scopes, worth checking first whenever a route 401s/404s unexpectedly.

**Day 29 — Payment confirmation task:** Extended the Day 24 Celery pattern directly — new task, explicit import into `celery_app.py`, triggered with `.delay()` after commit. Kept as a separate task from `send_order_confirmation` rather than reusing it, since "order placed" and "payment received" are genuinely different events. Verified via real worker logs.

**Day 30 — Payments tests + this recap:** First module needing to mock an external system. Used `unittest.mock.patch` to fake `stripe.checkout.Session.create` and `stripe.Webhook.construct_event` — only that one line is mocked per test, everything else runs for real against the test DB. 6 new tests: checkout success/not-found, webhook success/invalid-signature, success-page found/not-found. Full suite: 39 tests passing, no regressions.

**Test coverage snapshot:** Auth 3, Products 11, Cart 8, Orders 11, Payments 6 — 39 total, all passing together.

---

**Known gaps carried forward:**
- Order transitions beyond self-cancel/webhook-paid (`shipped`/`delivered`) need an admin role — deferred
- Refresh tokens still stateless — deferred
- Redis cache still has no automated tests
- Pydantic v1-style `class Config` still used across schemas — harmless warnings, not cleaned up
- Stripe SDK calls are sync/blocking inside async routes — acceptable at this scale


## Week 7 — Reviews Module (Days 31–32)

**Day 31 — Review model:** Design decided up front: multiple reviews per user
per product are allowed (not one-per-product — that gap wasn't closed until
Day 36), and a review requires a verified purchase. "Verified" is enforced
against order `status == PAID` (or `SHIPPED`/`DELIVERED`, though those states
don't exist yet without an admin role) rather than strictly `DELIVERED` —
requiring `DELIVERED` would make reviews impossible in practice given that
transition doesn't exist yet.

`Review` model: `product_id`/`user_id` FKs, `rating` (Integer), `comment`
(nullable), `created_at`. New pattern for this project: a DB-level
`CheckConstraint("rating BETWEEN 1 AND 5")` in `__table_args__`, making an
invalid rating structurally impossible at the database layer, not just
Pydantic-validated — the same "make invalid states impossible" philosophy
as the `order_status` Postgres enum from Week 5.

**Day 32 — Endpoints, testing, and three real bugs:** `has_verified_purchase()`
is a new query shape for this project — joins `Order` to `OrderItem` to check
for any matching paid order containing the product. `UnverifiedPurchaseError`
maps to **403**, not 404 or 409 — a genuinely new status-code case: the user
and product both exist, they just haven't earned the right to review yet
(an authorization failure, not a not-found or a conflict). `get_review_or_404`
reuses the ownership-in-WHERE-clause pattern from Orders (Week 5) — wrong
owner and nonexistent review both produce the identical 404.

Router has no single `prefix=` — a first for this project — since review
routes genuinely span two different path families (`/products/{id}/reviews`
for create/list, `/reviews/{id}` for update/delete).

Three real bugs chased down during manual testing, each instructive: (1) a
review attempt correctly 403'd on an order that *looked* paid but the Stripe
Pay button was never actually clicked — a correct rejection initially
mistaken for a bug; (2) the Stripe CLI webhook listener was off, so a real
payment never flipped the order to `paid` — a reminder that the listener
doesn't persist across sessions and needs restarting each time; (3) a stale
Postman environment variable (`{{product_id}}` still holding an old order ID
from an earlier test run) caused a 403 even against a genuinely paid order —
not a logic bug at all, just stale test data.

Reviews pytest suite deliberately deferred to Week 8 (Day 36) rather than
rushed after a long debugging session.


## Week 7 (cont.) — httpOnly Cookie Auth Conversion (Day 33)

**What changed:** Auth switched from returning JWT access + refresh tokens in the
JSON response body (client stores them itself, sends via `Authorization: Bearer`)
to the server setting both tokens as httpOnly cookies. The browser now handles
storage and attachment automatically; JavaScript never touches the tokens at all.

**Why:** An httpOnly cookie cannot be read by `document.cookie` or any client-side
JS. Even a successful XSS attack that got arbitrary JS running on the page still
couldn't exfiltrate the token — this is the main advantage over `localStorage`,
which is trivially readable by any script running on the page, malicious or not.

**New endpoint — `POST /auth/logout`:** didn't exist before, because there was
never anything for the server to do on logout under the Bearer-token model — the
frontend just discarded the token from wherever it stored it. With httpOnly
cookies, the frontend *can't* discard them (it can't see them), so the server has
to explicitly tell the browser to forget them via `delete_cookie()`.

**Cookie flags used:** `httponly=True` (JS-inaccessible), `secure=False` for local
dev over plain HTTP (flips to `True` in production, since `secure` cookies are
silently refused by browsers over non-HTTPS), `samesite="lax"` (cookie rides along
on same-site requests and top-level navigation, but not on cross-site subrequests
— a reasonable default that blocks most CSRF vectors without breaking normal use).

**Tradeoffs carried forward, unchanged from the original design:**
- Still no server-side token revocation/blacklisting. Logout clears the *browser's*
  copy of the cookie, but a raw token captured before logout (e.g. via a network
  intercept) remains cryptographically valid until its natural expiry. This was
  already true under the Bearer-token model — cookies don't make it worse, but
  they don't fix it either. Flagged as a future improvement, same as before.

**New tradeoff introduced by this change:**
- Cookies are sent automatically by the browser on every matching-origin request,
  which is exactly the mechanism CSRF attacks exploit (a malicious site could
  trigger a request to our API and have the browser attach our cookies without
  the user's intent). `SameSite=Lax` mitigates most practical CSRF risk for this
  project's scope by blocking the cookie on cross-site subrequests, though a
  dedicated CSRF token would be the fuller fix for a production-grade app.

**CORS became mandatory, not optional:** `CORSMiddleware` added with
`allow_credentials=True` and an explicit frontend origin (`allow_origins=["*"]`
is rejected by browsers once credentials are involved — origins must be named
explicitly). Without this, the future React frontend would never have been able
to send or receive the auth cookies cross-origin (`localhost:8000` vs
`localhost:5173` count as different origins despite both being "localhost").

**Testing implications:** `httpx.AsyncClient` maintains its own cookie jar across
requests, just like a real browser tab — so `conftest.py`'s `auth_headers` fixture
no longer needs to manually build and pass an `Authorization` header; it just logs
the shared `client` in once, and every subsequent request on that same client
carries the session automatically. Any test that manually parsed a token out of
the login response body to build a second identity's headers needed rewriting to
just log that second user in on the same client instead (caught two such cases in
`test_orders.py` and `test_reviews.py`'s wrong-owner tests).

**Process note:** done on a dedicated `feature/httponly-cookie-auth` branch,
committed at each verified sub-step (login → get_current_user → refresh → logout
→ CORS → tests → Postman), merged to `main` only after full regression (49/49
pytest, full Postman collection) passed. `main` was never in a broken state at
any point during the conversion.


## Week 7 — React Frontend Build (Days 33 cont.–35)

**Stack decisions (confirmed before writing code):** Vite + React, JavaScript
not TypeScript (deliberate — keep focus on React/Vite/Tailwind concepts
without adding a type system on day one), Tailwind CSS v4 (`@tailwindcss/vite`
plugin — the entire config is one `@import "tailwindcss";` line, a real
departure from v3's `tailwind.config.js`/PostCSS pipeline), React Router
(`BrowserRouter`), TanStack Query for all server-state fetching rather than
plain `fetch`/local state — more concepts, better caching and loading-state
patterns, worth the investment.

**Centralized API client (`src/api/client.js`):** every request sets
`credentials: 'include'` unconditionally — the one line that makes the
httpOnly-cookie auth actually work cross-origin, since `localhost:5173` and
`localhost:8000` are different origins despite both being "localhost."
Unwraps the backend's `{"detail": "..."}` error shape into a real JS `Error`
with a readable `.message`, matching every `HTTPException` across the whole
backend. No components ever call raw `fetch()` — everything routes through
this client.

**Session persistence (`AuthContext.jsx`):** a single `useQuery(['currentUser'],
() => api.get('/auth/me'), { retry: false })` run once on app load, exposed via
a `useAuth()` hook. `retry: false` is deliberate here specifically — a 401
means "not logged in," an expected outcome, not a failure to retry past.
`logout()` calls the backend, then manually clears the cached user via
`queryClient.setQueryData(['currentUser'], null)`, since nothing else would
trigger a re-fetch after the server-side cookie is cleared.

**Response shapes are not uniform across the backend, confirmed the hard
way:** products and orders return `{total, limit, offset, items}`; cart and
reviews return bare shapes (cart: `{id, user_id, items, subtotal}`; reviews:
a plain array). Every new page needed the actual shape confirmed before
writing `.map()` calls — assuming consistency across endpoints would have
been a real, silent bug source.

**Two legitimate strategies for updating the query cache after a mutation,
chosen by response shape, not preference:** `queryClient.setQueryData(key, data)`
when the mutation's response already *is* the full fresh resource (cart
mutations, order cancel — the endpoint returns the whole updated object);
`queryClient.invalidateQueries({ queryKey: key })` when the response is only
a *piece* of what the query needs (creating one review, but the query holds
the whole list).

**Checkout flow uses a real full-page navigation, not client-side routing:**
`window.location.href = session.checkout_url` — Stripe's checkout page lives
on a different domain entirely, so `useNavigate()`/`<Link>` (in-app routing
only) can't reach it.

**`useParams()` vs `useSearchParams()`, used deliberately for different URL
shapes:** path segments (`/products/:id`) use `useParams()`; Stripe's redirect
query string (`?session_id=...`) uses `useSearchParams()` — genuinely
different hooks for genuinely different URL structures.

**UI state derived from the query cache directly, not duplicated into local
state:** e.g. `canCancel = order.status === 'pending' || order.status === 'paid'`
computed fresh on every render from the cached order data, rather than
tracked as separate `useState` that would need manual syncing after a
successful cancel mutation.

**Leave-a-review form is always shown**, with eligibility enforced entirely
by the backend's 403 — the frontend just surfaces whatever error comes back,
the same "backend is the source of truth" approach used for add-to-cart.

Full flow verified end-to-end with real browser/DevTools evidence at every
step (session persistence surviving a refresh, a genuine Stripe test-mode
payment flipping an order to `paid` via the real webhook listener, edit/delete
on a review working and the list correctly falling back to "No reviews yet."
after deletion) — no step taken on faith.

**Known gaps, carried forward as deliberate scope decisions:** no automated
frontend tests yet (closed in Week 8, Day 40); no pagination UI controls
anywhere (`limit`/`offset` hardcoded, only page 1 ever shown); the cart
quantity input fires a mutation on every keystroke with no debounce.




## Week 8 — Test Coverage & Real Bug Fixes (Days 36–38b)

**Day 36 — Reviews pytest suite, and a real gap found by writing tests:**
Reviewing the Reviews module's own code while writing tests surfaced something
the manual Postman testing never caught: nothing prevented a user with
multiple paid orders for the same product from leaving unlimited reviews.
Fixed with `UniqueConstraint('user_id', 'product_id')` on `Review` and a new
`DuplicateReviewError` → 409, checked query-first (consistent with the
existing `has_verified_purchase` style) rather than caught via
`IntegrityError`. Real process bug alongside the code bug: the Alembic
migration file for this constraint was initially committed *separately* from
the model change that required it — a fresh clone in between those two
commits would have had model/DB drift. 12 tests written; diagnosed a
`ModuleNotFoundError: No module named 'app'` down to running bare `pytest`
instead of `python -m pytest` — the bare console script doesn't add the
current directory to `sys.path`.

**Day 37 — Redis cache pytest coverage:** Confirmed the cache-aside logic
actually lives in `products/router.py`, not `service.py` as first assumed —
worth checking before writing tests against an assumed location. Found and
fixed a real test-isolation gap: cache tests had no cleanup and were sharing
the dev Redis instance with no reset between runs, fixed via a module-scoped
`autouse` fixture calling `invalidate_pattern()` before and after each test
in that file specifically (not globally, to avoid unrelated blast radius).
The most important test here doesn't just check the response is correct —
it proves the cache is actually being *used*: `unittest.mock.patch` on the
real DB-query function with `side_effect` set to the real implementation,
then asserting `call_count == 1` across two identical requests. A response
could look correct even with completely broken caching if the assertion only
checked the data, not how many times the DB was actually hit.

Caught a subtle Python trap mid-session: a duplicate test function
definition silently shadowed an earlier, broken draft — Python allows
redefining a function with no error or warning, so the broken version was
never actually the code path running, despite appearing to be tested.

**Day 38a — Category cycle detection:** Live-reproduced the actual
vulnerability before writing any fix — built a real 3-level category chain
via curl, then set the top category's parent to its own descendant, which
succeeded with a `200 OK` and created a genuine infinite loop in the live
database. `would_create_cycle()` walks the ancestor chain from a proposed new
parent; if it ever reaches the category being updated, the reparent is
rejected with a new `CategoryCycleError` → 400. Scope extended mid-session,
deliberately, to also validate that a given `parent_id` actually exists
(previously failed silently until a raw `IntegrityError`/500 at commit).
Real bug during the fix itself: a new exception was imported from the wrong
module in `router.py`, crash-looping the whole backend container on every
reload — diagnosed via `docker compose logs backend` after curl requests
mysteriously hung with no output at all (the hang meant no server was
running, not a client-side issue).

**Day 38b — Refresh token revocation:** Design chosen and explained before
coding: a Redis-backed denylist keyed by each token's unique `jti` claim,
with the Redis key's TTL set to the token's *actual remaining lifetime*
(computed from its real `exp`), so denylist entries expire themselves with
no cleanup job needed — chosen specifically over a DB table, which would need
manual/background pruning of now-irrelevant expired rows. `/refresh` checks
the denylist via `.get("jti")`, not `["jti"]`, so pre-existing tokens issued
before this fix (which have no `jti` at all) don't crash, they just skip the
check and remain unrevocable until they naturally expire — an accepted,
temporary gap. `/logout` now decodes the refresh cookie *before* deleting it
and revokes it, wrapped in try/except so an already-invalid token never
breaks logout itself. Real bug: `/logout` used `datetime.fromtimestamp(...)`
with `datetime`/`timezone` never imported in that file, causing a `500` on
every logout attempt — only visible via `docker compose logs backend`, not
the API response. Full scenario live-proved via curl with a cookie jar file:
login → logout → refresh with the same cookies → correctly rejected `401`
(previously would have succeeded); negative control confirmed login → refresh
without logout still works normally.

**Test suite status after Days 36–38b:** 64 tests passing (Week 7 baseline 51
+ reviews 12 net + cache 6 + category hierarchy 4 + token revocation 3 = 76
gross written, 64 net after the reviews dedup noted in known gaps below).



## Week 8 — CI Pipelines (Days 39–40)

**Day 39 — GitHub Actions CI (backend):** Built incrementally, each step
proven before adding the next, rather than writing the full config at once:
a trivial one-step workflow first, to confirm the push/PR trigger actually
fires and to learn to read a run's logs in GitHub's UI; then Postgres and
Redis added as **service containers** — genuinely different from
`docker-compose.yml` syntax, but the same underlying idea (GitHub starts them
before the job's steps run, reachable at `localhost:<port>`), with
`--health-cmd pg_isready` / `redis-cli ping` health checks so the job's steps
don't race against a container that's technically "started" but not yet
actually accepting connections; then real `pip install` + `alembic upgrade
head` against the CI Postgres, proving the entire migration history (Day 5's
first `User` table through Day 38's fixes) builds a correct schema from
nothing; then the full pytest suite.

**Real bug found and fixed via CI, not local testing:** `conftest.py`
unconditionally overwrote `DATABASE_URL` with the local machine's hardcoded
port (`5433`, the Windows-Postgres-conflict workaround) and password — this
silently broke on any environment but the original dev machine, since CI's
Postgres runs on the standard `5432` with different credentials entirely.
Every one of the 64 tests failed identically with a connection error to the
wrong port — a single root cause producing 64 apparent failures, not 64
separate bugs. Fixed with `os.environ.setdefault(...)` instead of a direct
assignment — respects an already-set environment variable (as CI provides)
and only falls back to the local default when nothing else set it first. A
genuine, permanent improvement to the test suite's portability, not a
CI-only hack.

Both `backend-tests.yml` and (once it existed) `frontend-tests.yml` were
scoped with `paths:` filters (`backend/**` / `frontend/**` respectively)
after noticing, live, that an unscoped backend workflow was needlessly
re-running the entire 64-test suite on every frontend-only commit.

**Day 40 — Vitest + React Testing Library (frontend):** Chose `jsdom` +
plain `vi.mock()` over MSW for mocking API calls — simpler to reason about
while learning the framework for the first time, at the cost of being a less
realistic simulation of real network behavior. Built a shared
`renderWithProviders()` test utility wrapping every rendered component in
both `QueryClientProvider` (a **fresh** `QueryClient` per render, with
`retry: false` — retry delays would make tests slow for no benefit since the
API is mocked anyway) and `BrowserRouter`, after deliberately seeing the raw
`useNavigate() may be used only in the context of a <Router> component` crash
once, unwrapped, to understand why the wrapper is necessary rather than
treating it as boilerplate copied from a tutorial.

Three real tests written: Login submits the correct credentials to the
correct endpoint; Register submits and redirects to `/login` specifically
(not auto-login, matching the Day 33 design decision — a test that would
catch someone later "fixing" the redirect to `/` by mistake); Cart's checkout
mutation chains two `api.post` calls in the correct order with the correct
arguments (`mockResolvedValueOnce().mockResolvedValueOnce()`, since the same
mock function returns two different values across two calls) and sets
`window.location.href` to the real session URL — `window.location` itself
had to be deleted and replaced with a plain mutable object, since jsdom
doesn't implement real navigation and the built-in property is normally
read-only.

**Real infrastructure bug found and fixed along the way:** a stray
`node_modules/` folder appeared at the *repo root* (not `frontend/`) after a
command was accidentally run from the wrong directory — and `.gitignore` had
no `node_modules/` entry at all, since it had only ever been written from the
backend/Python side of the project. Fixed both the immediate folder (deleted)
and the actual gap (`node_modules/` and `dist/` added to `.gitignore`,
unscoped so the pattern matches at any depth, not just `frontend/`) — a
narrower fix that only ignored `frontend/node_modules/` would have left the
same class of accident possible anywhere else in the repo.

**CI status:** two independent GitHub Actions workflows, each triggered only
by changes to their respective half of the codebase — `backend-tests.yml`
(64 pytest tests against real Postgres + Redis service containers) and
`frontend-tests.yml` (5 Vitest tests, no service containers needed since
every API call is mocked at the module level).


---

## Project Status

40/40 planned days complete. Backend (auth, catalog, cart, orders, payments,
reviews) and frontend (full React UI across every module) are both built,
tested, and covered by independent CI pipelines that run on every push and
PR. See [`README.md`](../README.md) for setup instructions and a feature
summary; this document remains the place for *why* things are built the way
they are, not just *what* exists.