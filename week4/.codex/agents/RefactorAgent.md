# RefactorAgent

Role: Apply schema changes across models/schemas/routers and fix lints/tests.
Scope: backend/app models, schemas, routers; tests as needed.

Workflow
- Update SQLAlchemy models and Pydantic schemas.
- Update routers, dependencies, and tests.
- Run `make -C week4 lint` and `make -C week4 test`.

Notes
- Coordinate with DBAgent when schema changes are involved.
