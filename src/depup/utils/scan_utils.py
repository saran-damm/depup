from depup.core.models import UpdateType

def _convert_to_jsonable(deps, infos):
    info_by_name = {i.name.lower(): i for i in infos}

    items = []
    for dep in deps:
        info = info_by_name.get(dep.name.lower())

        items.append({
            "name": dep.name,
            "declared": dep.version,
            "current": dep.version,  # for env mode declared=None
            "latest": info.latest if info else None,
            "update_type": info.update_type if info else UpdateType.NONE,
            "source": dep.source_file.name if dep.source_file else None,
        })
    return items

def _has_outdated(infos: list) -> bool:
    return any(i.update_type != UpdateType.NONE for i in infos)

__all__ = [
    "_convert_to_jsonable",
    "_has_outdated",
]