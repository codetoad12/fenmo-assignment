# Codex Collaboration Guide

## Role

Codex supports the timed Fenmo technical assessment by focusing on:

- planning and scope control
- code review and architecture review
- code style and production-readiness checks
- test strategy and deployment-readiness review
- README and submission polish

Claude may write the main implementation. Codex should inspect the current
workspace before editing and avoid overwriting work from another assistant.

## Collaboration Flow

- Ask clarifying questions when the problem statement, expected behavior, data
  model, or deployment target is ambiguous.
- Do not one-shot large parts of the solution unless there is a very high
  degree of confidence in the approach.
- Break the problem into small, reviewable subtasks before implementation.
- Codex owns task decomposition and should turn the prompt into clear
  implementation tasks for Claude.
- Each task should include the goal, expected files or modules, acceptance
  criteria, and any constraints that matter.
- Prefer short feedback loops: Claude implements one subtask, Codex reviews
  the result, then the team moves to the next highest-value subtask.
- Codex owns review loops and should check correctness, scope, style,
  tests, and production-readiness before marking a subtask complete.

## Base Code Rules

- Keep every source line at or below 79 characters.
- Keep each function at or below 60 lines.
- Prefer small, explicit functions over large procedural blocks.
- Use single quotes for Python string literals unless double quotes avoid
  escaping or are required by a tool/framework.
- Use clear names for variables, functions, classes, and modules.
- Avoid unrelated refactors during the timed assessment.
- Prefer boring, maintainable implementation over clever abstractions.

## Python Standards

- Prefer FastAPI for backend/API-focused prompts.
- Prefer Streamlit only when the prompt is mainly a dashboard or data app.
- Use type hints for public functions, API handlers, and service boundaries.
- Validate inputs with Pydantic models where applicable.
- Keep business logic outside route handlers when the app grows beyond a
  trivial endpoint.
- Add focused tests for core behavior and risky edge cases.
- Include a health endpoint for deployable web services.

## Render Free-Tier Review

Treat Render Free as the default deployment target unless the prompt clearly
requires paid infrastructure. During planning and review, Codex should check
that the implementation fits these constraints:

- minimal dependency set and no unnecessary heavyweight packages
- fast startup with no long migrations, scraping, model loading, or batch work
- no important data stored only on the local filesystem
- bounded memory usage, request sizes, result sets, and uploaded files
- no reliance on background workers, cron jobs, SSH access, or persistent disks
- graceful behavior after restarts or cold starts
- `/health` endpoint and Render start command are documented
- deployment is attempted early enough to absorb a 3-6 minute build cycle

Codex should recommend upgrading Render only when the real prompt needs
always-on availability, persistent disk, higher memory, or an evaluator demo
where free-tier cold starts are likely to hurt the submission.

## Review Checklist

- Does the app solve the exact prompt with a complete user flow?
- Is the smallest useful version deployed and working?
- Are errors handled clearly?
- Is data validation present where user input enters the system?
- Are tests meaningful, fast, and easy to run?
- Is the README enough for an evaluator to run and understand the app?
- Are secrets excluded from git?
- Is the deployment path documented?
