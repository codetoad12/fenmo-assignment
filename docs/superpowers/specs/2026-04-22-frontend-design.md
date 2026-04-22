# Frontend Design

**Date:** 2026-04-22
**Topic:** Minimal browser UI for expense tracker

## Scope

Serve a vanilla HTML/JS/CSS UI from the existing FastAPI app. No framework,
no CDN dependencies, no build step. Same service, same Render deployment.

## Architecture

Three new files added to `app/`:

- `app/templates/index.html` — HTML shell: form, table, controls
- `app/static/app.js` — all JS behavior
- `app/static/styles.css` — minimal responsive styles

`app/main.py` changes:
- Mount `StaticFiles` at `/static` from `app/static/`
- Change `GET /` to return `FileResponse('app/templates/index.html')`

No new Python dependencies. `StaticFiles` and `FileResponse` are in FastAPI.

## UI Layout

Single page. Top: expense creation form. Below: filter/sort controls + total.
Below that: expense list/table.

Form fields: amount (number), category (text), description (text), date (date
input, defaults to today).

List columns: amount, category, description, date, created time.

Controls: category text input (filter), sort-by-date toggle (asc/desc).

Total: sum of `amount` across the currently displayed list.

## Behavior

### Load
1. `GET /expenses` → render list → calculate total from response array.

### Create
1. Generate `crypto.randomUUID()` as idempotency key on form edit / page load.
2. Disable submit button while request is in-flight.
3. `POST /expenses` with `Idempotency-Key` header.
4. On 201 or 200: refresh list via `GET /expenses`, generate new key.
5. On 409: show "Conflict" error message.
6. On 422: show validation error from `detail` field.
7. On network failure: keep same key, show retry button.

### Filter / Sort
- Category filter: `GET /expenses?category=<value>` on input change.
- Sort: `GET /expenses?sort=date&order=asc|desc` on toggle.
- Both params combined when both are active.
- Total recalculates from each response.

### States
- Loading: show spinner / "Loading..." in list area.
- Empty: show "No expenses yet." message.
- Error: show readable message, do not crash.

## Idempotency Key Lifecycle

- Generated: on page load and after each successful create.
- Reused: when retrying after network failure (same form values).
- Regenerated: on any form field edit or after success.

## Render Compatibility

- Static asset links are root-relative: `/static/styles.css`, `/static/app.js`.
- All API calls use relative paths: `fetch('/expenses')`.
- No `localhost` or `127.0.0.1` in frontend code.

## Acceptance Criteria

- `/` loads the UI on local dev and Render
- User can create an expense from the browser
- Successful creation refreshes the list
- Duplicate clicks do not create duplicate expenses
- Retry after network failure reuses the same idempotency key
- Category filter works
- Date sort asc/desc works
- Total updates with filter, not with sort-only change
- Loading, empty, and error states are visible
- Layout is readable on mobile and desktop
