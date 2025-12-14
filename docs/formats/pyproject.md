# pyproject.toml Support

depup supports both modern PEP 621 and Poetry-style projects.

---

## PEP 621

```toml
[project]
dependencies = [
  "requests>=2.31.0",
  "rich"
]
```

---

## Poetry-style

```toml
[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31"
```

---

## Behavior

* Only version parts are rewritten
* Operators are preserved
* Python version entries are ignored