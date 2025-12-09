from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DependencySpec:
    """
    Represents a declared dependency in a project's dependency file.
    """
    name: str
    version: Optional[str]
    source_file: Optional[Path]

@dataclass
class VersionInfo:
    name: str
    current: str
    latest: str
    update_type: str