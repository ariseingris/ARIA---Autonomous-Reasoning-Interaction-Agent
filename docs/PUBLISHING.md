# Publishing ARIA

## Local Install

Install the CLI from the repository:

```bash
uv tool install . --reinstall
aria --help
aria demo
```

## Configuration

Use `.env.example` as the template:

```bash
cp .env.example .env
aria config check
```

Supported settings:

- `OPENAI_API_KEY`: enables the OpenAI Responses brain provider.
- `ANTHROPIC_API_KEY`: optional, enables Claude Vision.
- `ARIA_MODEL`: OpenAI model name, default `gpt-5-mini`.
- `ARIA_MEMORY_BACKEND`: `json` by default, `chroma` optional.
- `ARIA_DATA_DIR`: runtime data directory, default `.aria`.

Never publish `.env`, `.aria/`, generated reports, or real API keys.

## Release Checklist

```bash
uv run pytest -q
uv run aria --help
uv run aria demo
uv run aria config check
uv tool install . --reinstall
aria --help
```

## Console Script

`pyproject.toml` exposes:

```toml
aria = "aria.cli.main:app"
```
