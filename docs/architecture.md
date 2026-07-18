## Week 2, Day 8 — JWT Login

### What was built
- POST /auth/login — verifies email/password, returns a signed JWT access token
- create_access_token() in security.py using python-jose

### Key decisions
- JWT payload: `sub` (user id) + `exp` (expiry) — minimal claims, no sensitive data
- HS256 algorithm — symmetric signing, appropriate for a single backend
- 15-minute access token expiry — deliberately short to limit damage from a leaked token
- Both "user not found" and "wrong password" return the same generic 401
  ("Incorrect email or password") — prevents user enumeration

### Bugs hit today
- Circular import: security.py accidentally imported from itself
  (a snippet meant for service.py got pasted into security.py instead)
- Missing `verify_password` in service.py's import line after adding
  authenticate_user() — a reminder to double check imports whenever
  new function names get used across files