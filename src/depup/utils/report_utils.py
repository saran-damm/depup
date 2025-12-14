from __future__ import annotations

from pathlib import Path
from typing import List

from depup.core.models import DependencySpec, VersionInfo, UpdateType


def generate_markdown_report(
    output_path: Path,
    deps: List[DependencySpec],
    infos: List[VersionInfo],
    title: str = "Dependency Report",
) -> None:
    """
    Generate a Markdown dependency report.
    """

    info_by_name = {i.name.lower(): i for i in infos}

    lines: list[str] = []
    lines.append(f"# {title}\n")
    lines.append("| Package | Current | Latest | Update Type | Source |")
    lines.append("|--------|---------|--------|-------------|--------|")

    for dep in deps:
        info = info_by_name.get(dep.name.lower())

        current = dep.version or ""
        latest = info.latest if info else ""
        update_type = info.update_type if info else UpdateType.NONE
        source = dep.source_file.name

        lines.append(
            f"| {dep.name} | {current} | {latest} | {update_type} | {source} |"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")
