from __future__ import annotations

import concurrent.futures
from typing import List, Optional

import requests
from packaging.version import InvalidVersion, Version, parse as parse_version

from depup.core.models import DependencySpec, UpdateType, VersionInfo


class VersionScannerError(Exception):
    """Raised when version scanning fails."""


class VersionScanner:
    PYPI_URL = "https://pypi.org/pypi/{package}/json"
    TIMEOUT = 8
    MAX_WORKERS = 12

    IGNORE = {
        "pip",
        "setuptools",
        "wheel",
        "pkginfo",
        "distlib",
        "virtualenv",
        "pip-tools",
    }

    def scan(self, deps: List[DependencySpec]) -> List[VersionInfo]:
        filtered = [d for d in deps if d.name.lower() not in self.IGNORE]

        results: List[VersionInfo] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_map = {executor.submit(self._fetch_version_info, dep): dep for dep in filtered}

            for future in concurrent.futures.as_completed(future_map):
                dep = future_map[future]
                try:
                    info = future.result()
                except Exception as exc:
                    raise VersionScannerError(f"Failed to scan {dep.name}: {exc}") from exc
                if info:
                    results.append(info)

        return results

    def _fetch_version_info(self, dep: DependencySpec) -> VersionInfo:
        pkg = dep.name
        declared = dep.version or ""

        try:
            response = requests.get(self.PYPI_URL.format(package=pkg), timeout=self.TIMEOUT)
        except Exception as exc:
            raise RuntimeError(f"Network error fetching {pkg}: {exc}") from exc

        if response.status_code != 200:
            # Can't resolve latest -> treat as UNKNOWN
            return VersionInfo(
                name=pkg,
                current=declared,
                latest="",
                update_type=UpdateType.NONE,
            )

        data = response.json()
        latest = (data.get("info") or {}).get("version", "") or ""

        update_type = self._classify(declared, latest)

        return VersionInfo(
            name=pkg,
            current=declared,
            latest=latest,
            update_type=update_type,
        )

    def _normalize_declared(self, spec: str) -> Optional[str]:
        spec = (spec or "").strip()
        if not spec:
            return None

        for op in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if spec.startswith(op):
                return spec[len(op):].strip()

        # Unhandled forms (e.g., "requests[security]>=2.0") should be treated carefully elsewhere
        return spec.strip()

    def _safe_version(self, s: str) -> Optional[Version]:
        try:
            v = parse_version(s)
            if isinstance(v, Version):
                return v
            return None
        except InvalidVersion:
            return None

    def _classify(self, current_spec: str, latest: str) -> UpdateType:
        current_norm = self._normalize_declared(current_spec)
        latest_norm = (latest or "").strip()

        if not latest_norm:
            return UpdateType.NONE

        # If we don't know what the user declared, we can’t reliably classify.
        if not current_norm:
            return UpdateType.NONE
        c = self._safe_version(current_norm)
        l = self._safe_version(latest_norm)

        if c is None or l is None:
            return UpdateType.NONE

        if l == c:
            return UpdateType.NONE

        if l < c:
            return UpdateType.NONE

        if l.major > c.major:
            return UpdateType.MAJOR
        if l.minor > c.minor:
            return UpdateType.MINOR
        return UpdateType.PATCH
