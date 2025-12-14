# Quick Start

This guide shows the most common depup workflows.

---

## Scan project dependencies

```bash
depup scan
```

Shows all declared dependencies and where they are defined.

---

## Check for latest versions

```bash
depup scan --latest
```

Adds latest available versions from PyPI and update type.

---

## Scan installed environment

```bash
depup scan --env --latest
```

Checks packages installed in the current Python environment.

---

## CI-friendly check

```bash
depup scan --latest --check
```

* Exit code `0`: all dependencies up to date
* Exit code `1`: outdated dependencies found

---

## Generate reports

```bash
depup scan --latest --json
depup scan --latest --report deps.md
```

---

## Upgrade dependencies (preview)

```bash
depup upgrade --dry-run
```