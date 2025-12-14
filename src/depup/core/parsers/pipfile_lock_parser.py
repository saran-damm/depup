from __future__ import annotations

import json
from pathlib import Path
from typing import List

from depup.core.models import DependencySpec


class PipfileLockParser:
    """Read-only parser for Pipfile.lock."""

    LOCKFILE_NAME = "Pipfile.lock"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.lockfile_path = project_root / self.LOCKFILE_NAME

    def exists(self) -> bool:
        return self.lockfile_path.exists()

    def parse(self) -> List[DependencySpec]:
        if not self.exists():
            return []

        with self.lockfile_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        deps: List[DependencySpec] = []

        for section in ("default", "develop"):
            packages = data.get(section, {})
            for name, meta in packages.items():
                version = meta.get("version")
                if not version:
                    continue

                deps.append(
                    DependencySpec(
                        name=name,
                        version=version,
                        source_file=self.lockfile_path,
                    )
                )

        return deps
