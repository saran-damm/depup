# Using depup in GitHub Actions

depup is designed to integrate cleanly into CI pipelines.

---

## Why use depup in CI?

- Prevent outdated dependencies from silently accumulating
- Enforce dependency hygiene before merge
- Fail builds when upgrades are required

---

## Basic CI Example

```yaml
name: Dependency Check

on:
  pull_request:
  push:
    branches: [main]

jobs:
  depup-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install depup
        run: pip install depup

      - name: Run dependency check
        run: depup scan --latest --check
```

---

## Behavior

* Exit code `0` → dependencies OK
* Exit code `1` → outdated dependencies detected
* Exit code `2` → invalid usage

---

## JSON-based enforcement

```yaml
- name: Scan dependencies (JSON)
  run: depup scan --latest --json --check
```

Use JSON output if you plan to parse results later.

---

## Recommended practice

* Use `scan --latest --check` on PRs
* Use `upgrade --dry-run` on release branches