from __future__ import annotations

import logging
from typing import List

from importlib import metadata

from depup.core.models import DependencySpec

logger = logging.getLogger(__name__)


class EnvironmentScanError(Exception):
    """Raised when environment package scanning fails."""


class EnvironmentScanner:
    """
    Scans the currently active Python environment for installed packages.

    Uses importlib.metadata to remain compatible with:
    - uv
    - poetry
    - venv
    - system Python
    """

    def scan(self) -> List[DependencySpec]:
        deps: List[DependencySpec] = []

        try:
            distributions = metadata.distributions()
        except Exception as exc:
            logger.error("Failed to read environment metadata: %s", exc)
            raise EnvironmentScanError(
                "Unable to inspect installed packages"
            ) from exc

        for dist in distributions:
            try:
                name = dist.metadata["Name"]
                version = dist.version
            except Exception:
                continue

            if not name:
                continue

            deps.append(
                DependencySpec(
                    name=name.lower(),
                    version=version,
                    source_file=None,  # environment has no source file
                )
            )

        return deps
