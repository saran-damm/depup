# poetry.lock Support

depup can **read** `poetry.lock` files.

---

## Purpose

- Detect exact locked versions
- Compare with PyPI latest versions
- Report update impact

---

## Important Notes

- poetry.lock is **read-only**
- depup does NOT modify lockfiles
- Use Poetry to regenerate locks

---

## Recommended workflow

```bash
depup scan --latest
poetry update
```