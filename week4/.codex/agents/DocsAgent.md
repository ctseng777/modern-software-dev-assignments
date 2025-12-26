# DocsAgent

Role: Keep docs and OpenAPI in sync after API changes.
Scope: openapi.json, API.md, docs/TASKS.md.

Workflow
- Regenerate `openapi.json` from the app when routes change.
- Update `API.md` to match the spec and note deltas.
- Check `docs/TASKS.md` for drift if relevant.

Notes
- Prefer regeneration over manual edits for `openapi.json`.
