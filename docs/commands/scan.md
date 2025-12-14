# depup scan

Scan dependencies and detect outdated packages.

---

## What it does

- Reads dependency declarations and lockfiles
- Optionally checks latest versions on PyPI
- Produces human-readable or machine-readable output

---

## Command syntax

```bash
depup scan [PATH] [OPTIONS]
```

---

## Options

| Option            | Description                          |
| ----------------- | ------------------------------------ |
| `--latest`        | Fetch latest versions from PyPI      |
| `--env`           | Scan installed environment           |
| `--json`          | Output JSON                          |
| `--report <file>` | Write Markdown report                |
| `--check`         | Exit non-zero if outdated deps found |

---

## Examples

```bash
depup scan --latest
depup scan --env --latest
depup scan --latest --check
```

---

## Exit Codes

| Code | Meaning                            |
| ---- | ---------------------------------- |
| 0    | Success / no outdated dependencies |
| 1    | Outdated dependencies found        |
| 2    | Invalid flag combination           |
