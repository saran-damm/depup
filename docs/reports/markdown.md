# Markdown Reports

depup can generate Markdown reports suitable for:

- Pull request comments
- Release audits
- Dependency reviews
- Human-readable records

---

## Command

```bash
depup scan --latest --report deps.md
````

---

## What the report contains

* Scan timestamp
* Dependency table
* Update classification
* Source files

---

## Example use cases

### GitHub Pull Requests

Attach dependency reports to PRs for review.

### Release Audits

Track dependency status at release time.

### Documentation

Publish dependency state alongside project docs.

---

## Notes

* Markdown reports are **read-only**
* They do not affect exit codes
* They are deterministic and reproducible