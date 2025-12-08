from __future__ import annotations

import json
import subprocess
from typing import List

from depup.core.models import DependencySpec


class EnvironmentScanner:
    """
    Fallback scanner that reads currently installed packages
    using `pip list --format=json`.
    """

    def scan(self) -> List[DependencySpec]:
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to read environment packages: {exc.stderr}") from exc

        try:
            packages = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Failed to parse pip output as JSON") from exc

        deps: List[DependencySpec] = []
        for pkg in packages:
            deps.append(
                DependencySpec(
                    name=pkg["name"],
                    version=pkg["version"],  # exact pinned version
                    source_file=None,  # environment has no file
                )
            )

        return deps
