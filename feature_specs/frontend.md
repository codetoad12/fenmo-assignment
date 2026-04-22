# Minimal Frontend Spec

## Goal

Build a simple browser UI for the expense tracker that works locally and on
Render without a separate frontend deployment.

The UI should let users create expenses, view expenses, filter by category,
sort by date, and see the total amount for the current filtered result set.

## Recommended Repo Structure

```text
app/
  __init__.py
  main.py
  expenses.py
  static/
    app.js
    styles.css
  templates/
    index.html
tests/
  test_expenses.py
```

Serve the UI from FastAPI and mount static assets from the same application.
Use relative API URLs such as `/expenses`, not localhost URLs.

## Routes

- `GET /` serves the expense tracker UI
- `GET /health` returns backend health
- `POST /expenses` creates an expense
- `GET /expenses` returns expenses

## UI Requirements

The first screen should be the usable expense tracker, not a marketing page.

Include:

- expense creation form
- expense list or table
- category filter control
- date sort control
- current total amount
- loading state
- empty state
- readable error state

Expense form fields:

- amount
- category
- description
- date

Expense list fields:

- amount
- category
- description
- date
- created time

## Filtering, Sorting, and Total

The total amount should be calculated for the currently filtered expenses.

Expected behavior:

- with no filter, show the total of all expenses
- with a category filter, show the total of matching expenses
- changing sort order should not change the total
- changing the category filter may change the total

Preferred API response shape:

```json
{
  "items": [
    {
      "id": "7879a84c-b174-45dd-bcd1-e6cd91620893",
      "amount": 1,
      "category": "test",
      "description": "upi",
      "date": "2026-04-22",
      "created_at": "2026-04-22T14:29:33.505745Z"
    }
  ],
  "total_amount": 1
}
```

If the backend returns a plain list instead, the frontend may calculate the
total from the displayed list.

## Reliability Requirements

Expense creation must be safe under slow networks, timeouts, duplicate clicks,
browser retries, and client-side retry buttons.

Frontend behavior:

- generate one idempotency key for each form submission attempt
- send the key as the `Idempotency-Key` header on `POST /expenses`
- disable the submit button while the request is in flight
- keep the same key when retrying the same request after a network failure
- generate a new key only after success or after the user edits the form
- refresh expenses from the backend after successful creation
- avoid optimistic inserts unless reconciled with the backend response

Backend behavior expected by the UI:

- same key and same body returns the original expense
- same key and different body returns `409 Conflict`
- validation errors do not create expenses or idempotency records

## Render Requirements

The UI and API should be served by the same FastAPI service.

Use:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Static asset links should be root-relative:

```html
<link rel="stylesheet" href="/static/styles.css">
<script src="/static/app.js" defer></script>
```

JavaScript API calls should also be relative:

```javascript
fetch('/expenses');
```

Do not call `http://127.0.0.1:8000` or `localhost` from frontend code.

## Acceptance Criteria

- `/` loads the expense tracker UI on local dev and Render
- user can create an expense from the browser
- successful creation refreshes the expense list
- duplicate clicks do not create duplicate expenses
- retrying after a network failure uses the same idempotency key
- user can filter expenses by category
- user can sort expenses by date ascending or descending
- total amount updates with filtering
- total amount does not change when only the sort order changes
- UI shows loading, empty, and error states
- layout is readable on mobile and desktop
