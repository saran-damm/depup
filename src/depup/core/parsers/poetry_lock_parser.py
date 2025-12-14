from __future__ import annotations

from pathlib import Path
from typing import List

import tomllib

from depup.core.models import DependencySpec


class PoetryLockParser:
    """Parse poetry.lock in read-only mode."""

    LOCKFILE_NAME = "poetry.lock"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.lockfile_path = project_root / self.LOCKFILE_NAME

    def exists(self) -> bool:
        return self.lockfile_path.exists()

    def parse(self) -> List[DependencySpec]:
        if not self.exists():
            return []

        with self.lockfile_path.open("rb") as f:
            data = tomllib.load(f)

        packages = data.get("package", [])
        deps: List[DependencySpec] = []

        for pkg in packages:
            name = pkg.get("name")
            version = pkg.get("version")

            if not name or not version:
                continue

            deps.append(
                DependencySpec(
                    name=name,
                    version=f"=={version}",
                    source_file=self.lockfile_path,
                )
            )

        return deps
