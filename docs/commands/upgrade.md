# depup upgrade

Upgrade outdated dependencies safely.

---

## What it does

- Detects outdated dependencies
- Applies upgrades selectively
- Updates dependency files
- Supports dry-run mode

---

## Command syntax

```bash
depup upgrade [PATH] [PACKAGES...] [OPTIONS]
```

---

## Options

| Option         | Description                  |
| -------------- | ---------------------------- |
| `--only-patch` | Upgrade patch versions only  |
| `--only-minor` | Upgrade minor versions only  |
| `--only-major` | Upgrade major versions only  |
| `--dry-run`    | Show planned upgrades only   |
| `--yes`        | Skip confirmation            |
| `--env`        | Upgrade environment packages |

---

## Examples

```bash
depup upgrade --dry-run
depup upgrade requests rich
depup upgrade --env --only-patch
```