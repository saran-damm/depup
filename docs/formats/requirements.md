# requirements.txt Support

depup supports classic `requirements.txt` files.

---

## Supported formats

```text
requests==2.31.0
numpy>=1.25
pandas~=1.5
```

---

## Behavior

* Ignores comments and blank lines
* Preserves version operators
* Rewrites versions during upgrade

---

## Limitations

* Editable installs (`-e`) are ignored
* Complex flags are skipped
