Add POST /expenses

Request body includes amount, category, description, date
Response includes id, amount, category, description, date, created_at
Validate amount is positive
Validate category and description are not empty
Use ISO date format, e.g. 2026-04-22
Make retries safe with an Idempotency-Key header
Same key + same body should return the same expense
Same key + different body should return 409 Conflict

Add GET /expenses

Returns all expenses
Supports optional category filter
Supports sorting by date
Suggested query params:
category
sort=date
order=asc|desc
Default order can be newest first
Data model minimum fields:

id
amount
category
description
date
created_at
Recommended implementation:

Use SQLite via Python standard sqlite3
Initialize tables on app startup
Keep DB path configurable with env var, e.g. EXPENSE_DB_PATH
Add /health if it is not already present
Keep dependencies minimal for Render
Acceptance criteria:

POST /expenses creates an expense and returns complete data
Repeating the same POST with the same Idempotency-Key does not create duplicates
Reusing an idempotency key with a different body returns 409
GET /expenses?category=food filters correctly
GET /expenses?sort=date&order=asc sorts by date ascending
Invalid payloads return useful 422 errors
Tests cover create, retry behavior, conflict behavior, filtering, and sorting
Constraints from repo docs:

Keep source lines under 79 chars
Keep functions under 60 lines
Use single quotes in Python where possible
Avoid unrelated refactors
Keep implementation boring and maintainable