# Pipfile.lock Support

depup supports read-only analysis of `Pipfile.lock`.

---

## What depup reads

- Locked package versions
- Dependency names

---

## What depup does NOT do

- Modify Pipfile.lock
- Re-lock dependencies

---

## Recommended workflow

```bash
depup scan --latest
pipenv update
```