# Exit Codes

depup uses consistent exit codes for CI automation.

---

## Scan command

| Code | Meaning |
|----|--------|
| 0 | Success / no outdated dependencies |
| 1 | Outdated dependencies detected |
| 2 | Invalid command usage |

---

## Upgrade command

| Code | Meaning |
|----|--------|
| 0 | Upgrade succeeded |
| 1 | Upgrade failed |