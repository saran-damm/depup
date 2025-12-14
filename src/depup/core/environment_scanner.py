from __future__ import annotations

import logging
from importlib import metadata
from typing import List

from depup.core.models import DependencySpec

logger = logging.getLogger(__name__)


class EnvironmentScanError(Exception):
    """Raised when environment package scanning fails."""


class EnvironmentScanner:
    """
    Scans installed packages from the currently running Python environment.

    Uses importlib.metadata so this works with:
      - uv venv (pip may be absent)
      - venv
      - poetry
      - system python
    """

    def scan(self) -> List[DependencySpec]:
        try:
            dists = metadata.distributions()
        except Exception as exc:
            logger.error("Failed to read installed distributions: %s", exc)
            raise EnvironmentScanError(
                "Unable to inspect installed packages. "
                "If this is a minimal environment, ensure site-packages metadata is available."
            ) from exc

        deps: List[DependencySpec] = []
        for dist in dists:
            try:
                name = dist.metadata.get("Name") or ""
                version = dist.version
            except Exception:
                continue

            if not name:
                continue

            deps.append(
                DependencySpec(
                    name=name.lower(),
                    version=version,
                    source_file=None,
                )
            )

        return deps
