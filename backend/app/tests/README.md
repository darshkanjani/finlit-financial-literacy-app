# Tests README

This directory contains the backend test suite for the FinLit app.

This README explains:
- what is being tested
- how the test setup works
- how to run backend and frontend tests
- which files are active tests vs placeholders

## 1. High-level picture

The project has two separate test suites because the project itself has two separate runtimes:

1. Backend
- Python
- FastAPI
- SQLAlchemy
- tested with `pytest`

2. Frontend
- React + TypeScript
- Vite
- tested with `vitest`

They are separate because Python code cannot be tested with the frontend runner, and React UI code cannot be tested with `pytest`.

## 2. How tests work in simple terms

A test is just code that:

1. sets up some input
2. runs part of the app
3. checks the result with `assert`

Example:

```python
result = 2 + 3
assert result == 5
```

If the assertion is true, the test passes.
If not, the test fails.

## 3. Backend testing

### 3.1 Tool

Backend tests use `pytest`.

Run from the backend folder:

```bash
cd Code/backend
PYTHONPATH=. python -m pytest app/tests
```

If your virtual environment is activated, this uses the venv Python.

Why `PYTHONPATH=.` is needed:
- backend imports use `from app...`
- Python must treat `Code/backend` as the import root

### 3.2 What `collected 33 items` means

When `pytest` says:

```bash
collected 33 items
```

it means:
- it found 33 individual `test_*` functions to run

It does not mean:
- 33 files
- 33 lines
- full code coverage

### 3.3 Shared backend setup

File:
- [conftest.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/conftest.py)

This file provides shared setup for backend tests.

It does three important things:

1. Creates a dedicated SQLite test database
2. Drops and recreates all tables before each test
3. Provides reusable fixtures

Fixtures:

`db_session`
- gives a SQLAlchemy session connected to the test DB

`make_user`
- quickly inserts a test user row into the test DB

Why this matters:
- tests do not touch the real dev database
- every test starts from a clean state
- one test cannot accidentally break another

## 4. Active backend test files

These are the test files currently in the active passing suite.

### 4.1 Auth

File:
- [test_auth.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_auth.py)

What it tests:
- user registration
- duplicate email rejection
- login success
- login failure
- token-to-user lookup
- missing token rejection
- password change success/failure

Main code exercised:
- [auth_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/auth_service.py)
- [deps.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/api/deps.py)
- [jwt.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/core/jwt.py)

How:
- calls service functions directly
- builds a fake request object when testing token extraction

### 4.2 Profile

File:
- [test_profile.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_profile.py)

What it tests:
- profile save/update
- currency persistence
- manual literacy score handling
- quiz-derived literacy score handling
- retaining existing literacy score
- invalid input rejection

Main code exercised:
- [profile_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/profile_service.py)

### 4.3 Chat

File:
- [test_chat.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_chat.py)

What it tests:
- literacy score changes the system prompt rules
- chat history persists
- chat history can be cleared

Main code exercised:
- [chat_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/chat_service.py)

How:
- LLM calls are mocked
- RAG retrieval is mocked

Why mock them:
- no network
- no model dependency
- deterministic output

### 4.4 Advice

File:
- [test_advice.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_advice.py)

What it tests:
- literacy score changes advice prompt rules
- advice history persists
- advice history can be cleared

Main code exercised:
- [advice_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/advice_service.py)

### 4.5 Dashboard

File:
- [test_dashboard.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_dashboard.py)

What it tests:
- empty dashboard state for a fresh user
- populated dashboard state for a user with profile/goals/stress results

Main code exercised:
- [dashboard_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/dashboard_service.py)

Checks include:
- currency code
- profile income
- spending breakdown
- resilience summary
- goals

### 4.6 FX / currency

File:
- [test_fx.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_fx.py)

What it tests:
- live FX payload handling
- fallback FX payload handling

Main code exercised:
- [fx_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/fx_service.py)

How:
- provider fetches are mocked

### 4.7 CSV parsing

File:
- [test_csv.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_csv.py)

What it tests:
- CSV parsing
- transaction categorisation
- classification metadata (`suggested_category`, `confidence`, `method`)
- audit persistence
- missing header handling
- bad amount warning handling

Main code exercised:
- [csv_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/csv_service.py)

Important note:
- these tests found a real bug where `"Netflix"` was wrongly classified as transport because `"tfl"` was matched inside the word
- the categoriser was then fixed to use more careful matching

Current CSV parser output shape:
- `transactions`
- `category_totals`
- `warnings`
- `parsed_count`

The `transactions` list is a preview-only structure for the frontend import UI.
It is not stored as raw transaction history in the main financial profile.

Sample upload file for manual testing:
- [sample_bank_upload.csv](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/fixtures/sample_bank_upload.csv)

That sample file intentionally exercises several parser paths:
- merchant-map matches
- phrase-rule matches
- token-rule matches
- fallback classification

### 4.8 Goals

File:
- [test_goals.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_goals.py)

What it tests:
- create goal
- update goal
- delete goal
- forecast without profile
- forecast with profile
- missing goal rejection

Main code exercised:
- [goals_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/goals_service.py)

### 4.9 Stress engine and stress service

File:
- [test_stress.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_stress.py)

What it tests:
- stress engine returns the expected result shape
- stress service saves results
- ML cutback path is used when available
- resilience summary uses latest scenario results
- stress tests require a profile

Main code exercised:
- [stress_engine.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/ml/stress_engine.py)
- [stress_service.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/services/stress_service.py)

## 5. Backend files that are still placeholders / incomplete

These files exist in this directory but are not currently part of the real active coverage because they only contain notes or partial stubs:

- [test_categoriser.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_categoriser.py)
- [test_rag.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_rag.py)
- [test_security_jwt.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_security_jwt.py)
- [test_spending.py](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/backend/app/tests/test_spending.py)

These should be treated as TODOs, not as complete tests.

## 6. Why backend tests mostly hit services, not HTTP endpoints

The most useful thing to test is the core logic:
- auth rules
- profile validation
- dashboard aggregation
- FX fallback logic
- stress simulation

This suite is intentionally service-heavy because:
- it is faster
- it is more deterministic
- it avoids flaky HTTP-layer issues in the local test environment

The tests still exercise the real application logic, just one layer lower than full API-request tests.

## 7. Frontend testing

The frontend suite lives outside this folder, mainly under:
- `Code/frontend/src/**/*.test.ts`
- `Code/frontend/src/**/*.test.tsx`

Frontend tests use Vitest.

Run from the frontend folder:

```bash
cd Code/frontend
bun run test
```

Configuration files:
- [package.json](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/package.json)
- [vite.config.ts](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/vite.config.ts)
- [setup.ts](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/src/test/setup.ts)

### 7.1 Active frontend test files

#### Currency utilities
- [currency.test.ts](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/src/lib/currency.test.ts)

Tests:
- currency normalization
- conversion
- formatting

#### Onboarding
- [onboarding.test.tsx](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/src/pages/onboarding/onboarding.test.tsx)

Tests:
- manual literacy score payload
- quiz literacy answers payload

#### Summary
- [summary.test.tsx](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/src/pages/dashboard/summary.test.tsx)

Tests:
- FX fallback status rendering

#### Goals page
- [goals.test.tsx](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/src/pages/dashboard/goals.test.tsx)

Tests:
- rendering amounts in the selected currency
- adding a goal through the form

#### Stress page
- [stress.test.tsx](/home/darshkaws/Documents/emtech/emtech3/emerging-tec-fintec/Code/frontend/src/pages/dashboard/stress.test.tsx)

Tests:
- score explanation UI
- scenario breakdown UI

## 8. How frontend tests work

Frontend tests render components in a fake browser-like environment (`jsdom`) and inspect the rendered output.

Typical pattern:

1. render the component
2. mock API responses
3. simulate user interaction
4. check what appears on screen or what payload was sent

Example mental model:
- backend test asks: "did the function return the right data?"
- frontend test asks: "did the user see the right UI / did the component send the right payload?"

## 9. Mocks

Tests often replace external dependencies with fake ones.

Examples:
- fake LLM response
- fake FX provider response
- fake API client response
- fake RAG retrieval

Why mocks are used:
- tests stay fast
- tests stay deterministic
- tests do not depend on internet or external services

## 10. Current passing totals

At the time this README was written:

Backend:
- `33 passed`

Frontend:
- `9 passed`

These numbers will change as more tests are added.

## 11. Useful commands

### Run all backend tests

```bash
cd Code/backend
PYTHONPATH=. python -m pytest app/tests
```

### Run one backend file

```bash
cd Code/backend
PYTHONPATH=. python -m pytest app/tests/test_chat.py
```

### Show which backend tests pytest collects

```bash
cd Code/backend
PYTHONPATH=. python -m pytest app/tests --collect-only
```

### Run all frontend tests

```bash
cd Code/frontend
bun run test
```

### Run frontend tests in watch mode

```bash
cd Code/frontend
bun run test:watch
```

## 12. What still needs testing

The suite is now a good baseline, but it is not complete.

Still worth adding:
- forgot/reset password flow
- admin endpoints
- RAG retriever tests
- security/JWT utility tests
- spending breakdown tests
- endpoint-level CSV upload tests
- assistant page frontend tests
- reset-password frontend tests
- browser end-to-end flows (Playwright or similar)

## 13. Practical rule for contributors

When adding a feature:

1. add or update backend tests if business logic changes
2. add or update frontend tests if UI behavior changes
3. prefer deterministic tests over tests that depend on real external services
4. if a bug is found, add a regression test for it

That last rule matters:
- the CSV `"Netflix" -> transport` bug is a good example
- once fixed, a test now guards it from coming back
