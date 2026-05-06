# AGENTS.md

Operational notes for Codex and other coding agents working in this repository.

## Shell Search On This Windows Workspace

Prefer `rg` for repository searches when it works.

In this Codex Desktop Windows environment, `rg.exe` may fail with:

```text
Access is denied
```

When that happens, do not keep retrying `rg`. Use PowerShell-native search instead:

```powershell
Get-ChildItem -Recurse | Select-String -Pattern "text-to-search"
```

For targeted searches, pass explicit files or directories to keep the output readable:

```powershell
Get-ChildItem README.md,docs,.github | Select-String -Pattern "mkdocs","docs/.*\.md"
```

This is only a local tooling fallback. It does not indicate a repository problem.

## Development Checks

Run the fast Python test suite with `uv`:

```powershell
uv run pytest -q
```

Use Docker-based checks only when the change needs the API, Redis, Celery worker,
or runtime container image.
