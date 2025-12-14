from __future__ import annotations

from typing import Any, Dict, List

from depup.core.models import DependencySpec, UpdateType, VersionInfo


def _has_outdated(infos: List[VersionInfo]) -> bool:
    return any(i.update_type in {UpdateType.PATCH, UpdateType.MINOR, UpdateType.MAJOR, UpdateType.NONE} for i in infos)


def _convert_to_jsonable(deps: List[DependencySpec], infos: List[VersionInfo]) -> Dict[str, Any]:
    info_by = {i.name.lower(): i for i in infos}
    items = []
    for d in deps:
        vi = info_by.get(d.name.lower())
        items.append(
            {
                "name": d.name,
                "declared": d.version,
                "latest": vi.latest if vi else None,
                "update_type": (vi.update_type.value if vi else UpdateType.NONE.value),
                "source_file": (d.source_file.name if d.source_file else None),
            }
        )
    return {"dependencies": items}
