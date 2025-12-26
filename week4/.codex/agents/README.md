# Week 4 Codex Subagents

These agent prompts are stored in `week4/.codex/agents/`.

Suggested flows
- TestAgent -> CodeAgent -> TestAgent (tests first, then implement, then verify)
- CodeAgent -> DocsAgent (implement route, then regenerate docs)
- DBAgent -> RefactorAgent (schema change, then code updates + lint/test)

Usage
- Load one agent prompt at a time in Codex when switching roles.
- Keep scopes tight to reduce cross-contamination.
