# JSON Output

depup supports structured JSON output for automation, CI pipelines,
and integrations with other tools.

---

## When to use JSON output

Use JSON output when:

- Integrating depup into CI/CD
- Parsing results programmatically
- Feeding results into dashboards or agents
- Writing custom policy checks

---

## Command

```bash
depup scan --latest --json
```

---

## JSON Structure

```json
{
  "dependencies": [
    {
      "name": "requests",
      "current": "==2.31.0",
      "latest": "2.32.5",
      "update_type": "minor",
      "source": "pyproject.toml"
    }
  ]
}
```

---

## Fields

| Field         | Description                       |
| ------------- | --------------------------------- |
| `name`        | Package name                      |
| `current`     | Declared or installed version     |
| `latest`      | Latest version on PyPI            |
| `update_type` | `none`, `patch`, `minor`, `major` |
| `source`      | Origin file or environment        |

---

## Exit codes with JSON

JSON output **does not change exit codes**.

Use `--check` for CI enforcement:

```bash
depup scan --latest --json --check
```