# Publishing ARIA

ARIA is packaged for public Python distribution as `aria-agent`.
The installed command remains `aria`.

## Local Install

```bash
uv tool install . --reinstall
aria --help
aria config set openai-api-key
aria brain check
aria demo
```

## PyPI Build

```bash
uv build
```

This creates release artifacts under `dist/`.

## PyPI Publish

```bash
uv publish
```

Use a PyPI token from your local environment or uv credential store. Do not put publish tokens or API keys in the repository.

## Install After Publish

Run without a persistent install:

```bash
uvx aria-agent
```

Install as a CLI tool:

```bash
pipx install aria-agent
aria --help
```

## Command Usage

```bash
aria config set openai-api-key
aria brain check
aria demo
aria run "Research browser-use"
```

## Release Checklist

```bash
uv run pytest -q
uv run aria --help
uv run aria config show
uv run aria brain check
uv run aria demo
uv build
uv tool install . --reinstall
aria doctor
aria demo
```

## Safety Notes

- Never commit `.env`.
- Never print API keys in CLI output.
- Keep generated `.aria/`, `reports/`, and build artifacts out of version control.
- Verify `pyproject.toml` exposes `aria = "aria.cli.main:app"`.
