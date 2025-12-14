from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class UpdateType(str, Enum):
    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclass(frozen=True)
class DependencySpec:
    """
    Represents a declared or locked dependency.
    """
    name: str
    version: Optional[str]
    source_file: Optional[Path]


@dataclass(frozen=True)
class VersionInfo:
    """
    Represents version resolution information for a dependency.
    """
    name: str
    current: Optional[str]
    latest: Optional[str]
    update_type: UpdateType
