# Contributing

Thanks for helping improve `docker-compose-health-dashboard`.

## Development Setup

```bash
uv sync --extra dev
uv run pytest
```

## Pull Requests

- Keep changes scoped and easy to review.
- Add or update tests for parser, risk-engine, or CLI behavior changes.
- Do not print secret values in test output, examples, or rendered reports.
- Update `README.md` when user-facing behavior changes.
- Ensure CI passes before requesting review.

## Design Principles

- Analyze static Compose files only.
- Keep parsing, risk detection, and rendering separated.
- Prefer clear, explainable checks over broad claims.
- Avoid adding live Docker inspection, credentials, databases, or cloud sync to
  the MVP.
