from rich.console import Console
from rich.table import Table
from depup.core.models import UpdateType

console = Console()

def _render_latest_file_table(deps, infos):
    info_by_name = {i.name.lower(): i for i in infos}

    table = Table(title="Declared Dependencies (with latest versions)")
    table.add_column("Package", style="cyan")
    table.add_column("Declared Spec", style="green")
    table.add_column("Latest Version", style="yellow")
    table.add_column("Update Type", style="red")
    table.add_column("Source File", style="magenta")

    for dep in deps:
        info = info_by_name.get(dep.name.lower())
        table.add_row(
            dep.name,
            dep.version or "",
            info.latest if info else "",
            info.update_type if info else UpdateType.NONE,
            dep.source_file.name,
        )

    console.print(table)


def _render_declared_file_table(deps):
    table = Table(title="Declared Dependencies")
    table.add_column("Package", style="cyan")
    table.add_column("Version Spec", style="green")
    table.add_column("Source File", style="magenta")

    for dep in deps:
        table.add_row(dep.name, dep.version or "", dep.source_file.name)

    console.print(table)


def _render_env_table(deps):
    table = Table(title="Environment Packages")
    table.add_column("Package", style="cyan")
    table.add_column("Installed Version", style="green")

    for dep in deps:
        table.add_row(dep.name, dep.version or "")

    console.print(table)


def _render_latest_env_table(deps, infos):
    info_by_name = {i.name.lower(): i for i in infos}

    table = Table(title="Environment Packages (Latest Versions)")
    table.add_column("Package", style="cyan")
    table.add_column("Installed", style="green")
    table.add_column("Latest", style="yellow")
    table.add_column("Update Type", style="red")

    for dep in deps:
        info = info_by_name.get(dep.name.lower())
        table.add_row(
            dep.name,
            dep.version or "",
            info.latest if info else "",
            info.update_type if info else UpdateType.NONE,
        )

    console.print(table)

__all__ = [
    "_render_latest_file_table",
    "_render_declared_file_table",
    "_render_env_table",
    "_render_latest_env_table",
]