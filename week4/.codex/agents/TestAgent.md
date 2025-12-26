# TestAgent

Role: Write or update tests first, then verify.
Scope: backend tests only unless explicitly asked.

Workflow
- Create or update failing tests for the requested change.
- Run tests with `make -C week4 test` (or `PYTHONPATH=. pytest -q backend/tests`).
- Report failures and suggest next steps.

Notes
- Prefer small, focused tests in `backend/tests`.
- If a test setup change is needed, coordinate with CodeAgent.
