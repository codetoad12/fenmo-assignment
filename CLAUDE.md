# Fenmo Assessment Context

We are preparing for a timed Fenmo SDE technical assessment. The final
submission must include:

- a public live application URL
- a public GitHub repository URL
- a README with setup, run, test, and deployment notes
- a screenshot of the repository commit history page

The assessment is evaluated on depth and production-readiness rather than
feature breadth. Prioritize a focused, working, deployable application over a
large unfinished feature set.

## Working Agreement

- Claude is expected to write the main application code.
- Codex focuses on planning, code review, style, tests, README polish, and
  production-readiness checks.
- Codex should break the problem into clear subtasks and hand those tasks to
  Claude with goals, expected files or modules, acceptance criteria, and
  constraints.
- Claude should ask clarifying questions when requirements, user flows, data
  models, or deployment expectations are ambiguous.
- Do not one-shot large parts of the solution unless there is a very high
  degree of confidence in the correct approach.
- Work through the app in small subtasks with short review loops owned by
  Codex.
- After each meaningful subtask, Claude should pause for Codex review before
  moving to broad new work unless the next step is obvious and low-risk.
- Before editing existing files, inspect the current workspace so changes from
  another assistant are preserved.
- Keep changes scoped to the assessment goal.

## Base Code Rules

- Keep every source line at or below 79 characters.
- Keep each function at or below 60 lines.
- Use single quotes for Python string literals unless double quotes avoid
  escaping or are required by a tool/framework.
- Prefer readable, explicit code over clever abstractions.
- Add comments only when they clarify non-obvious behavior.

## Likely Python Stack

Default to FastAPI for backend/API applications. Use Streamlit only if the
problem statement is primarily a dashboard, analytics, or data-entry app where
Streamlit gives a faster complete result.

For FastAPI apps, aim for:

- Pydantic request/response models
- clean route/service separation when useful
- SQLite or another simple persistence layer unless the prompt requires more
- health endpoint
- pytest coverage for core behavior
- Dockerfile or clear deploy instructions
- simple, polished UI if the prompt expects end-user interaction

## Time Strategy

1. Understand the problem statement and define the smallest complete product.
2. Build the core flow first.
3. Add persistence, validation, and errors.
4. Add tests for the highest-risk logic.
5. Polish the README and deployment settings.
6. Deploy, verify the live app, and prepare submission links.
