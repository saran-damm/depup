from __future__ import annotations

from pathlib import Path
from typing import List

from depup.core.models import VersionInfo
from depup.core.parsers.declaration_parser import DependencySpec
from depup.core.upgrade_executor import PlannedUpgrade


def build_upgrade_plans(
    infos: List[VersionInfo],
    deps: List[DependencySpec],
    project_root: Path,
) -> List[PlannedUpgrade]:
    plans: List[PlannedUpgrade] = []

    for info in infos:
        dep_spec = next(
            (d for d in deps if d.name.lower() == info.name.lower()),
            None,
        )

        source_file = (
            dep_spec.source_file if dep_spec else project_root / "requirements.txt"
        )

        plans.append(
            PlannedUpgrade(
                name=info.name,
                current_spec=info.current,
                target_version=info.latest,
                source_file=source_file,
            )
        )

    return plans
