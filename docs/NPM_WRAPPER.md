# Future npm Wrapper Plan

ARIA is a Python CLI distributed as `aria-agent` on PyPI. A future npm package can make installation feel native for Node.js users:

```bash
npm install -g aria-agent
aria --help
```

## Scope

The npm package should be a thin wrapper only. It should not reimplement ARIA.

Recommended behavior:

1. Check whether Python and `uvx` are available.
2. Invoke the Python CLI through:

   ```bash
   uvx aria-agent "$@"
   ```

3. Forward stdout, stderr, and exit codes unchanged.
4. Print a clear setup error if Python or uv is missing.

## Package Shape

```text
npm-package/
  package.json
  bin/
    aria.js
  README.md
```

The `aria.js` file should spawn `uvx aria-agent` with the current process arguments.

## Do Not Do

- Do not duplicate Python business logic.
- Do not bundle API keys.
- Do not write secrets into npm package files.
- Do not publish until the PyPI package name and CLI behavior are stable.
