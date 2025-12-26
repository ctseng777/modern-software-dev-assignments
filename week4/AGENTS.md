# AGENTS.md

## 1: Code navigation and entry points

- Run the app: `make run` (from `week4/`), then open `http://localhost:8000` and `http://localhost:8000/docs`.
- Routers live in `backend/app/routers`.
- Tests live in `backend/tests` and are run with `make test`.
- DB seed: `data/seed.sql` and `make seed` (runs `backend.app.db.apply_seed_if_needed`).

## 2: Style and safety guardrails

- Tooling expectations: format with `black .`, lint with `ruff check .`, and keep `pre-commit` green.
- Safe commands: `make run`, `make test`, `make lint`, `make format`, `make seed`, `pre-commit run --all-files`.
- Commands to avoid: destructive deletes (`rm -rf`), wiping `data/notes.db` without asking, or ad-hoc DB resets outside `make seed`.
- Lint/test gates: changes should pass `make lint` and `make test` before submission.

## 3: Workflow snippets

- When asked to add an endpoint, first write a failing test, then implement, then run `pre-commit run --all-files`.
