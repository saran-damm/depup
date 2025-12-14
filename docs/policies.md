# Dependency Policies

depup enables teams to enforce dependency policies consistently.

---

## What is a dependency policy?

A dependency policy defines:
- When upgrades are allowed
- Which update types are acceptable
- How strictly CI enforces updates

---

## Common policies

### Allow only patch updates
```bash
depup upgrade --only-patch
```

### Fail CI on any outdated dependency

```bash
depup scan --latest --check
```

### Monitor without enforcing

```bash
depup scan --latest
```

---

## Recommended policy progression

| Stage           | Policy              |
| --------------- | ------------------- |
| Early project   | Monitor only        |
| Growing project | Enforce patch/minor |
| Mature project  | Strict enforcement  |

---

## Why depup helps

depup separates:

* **Detection** from **execution**
* **Policy** from **mechanics**

This makes dependency management safer and auditable.

