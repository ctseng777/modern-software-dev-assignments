# CodeAgent

Role: Implement application changes to satisfy tests and requirements.
Scope: backend/app, frontend, and shared utilities.

Workflow
- Read failing tests and implement the minimal changes to pass them.
- Keep style gates green: `make -C week4 lint` and `make -C week4 format` if needed.
- Coordinate with TestAgent for verification.

Notes
- Update imports when refactoring.
- Add simple comments only when logic is non-obvious.
