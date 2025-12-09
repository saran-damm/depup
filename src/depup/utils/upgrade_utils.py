from typing import List
from depup.core.models import VersionInfo
from rich.console import Console

console = Console()

def _perform_env_upgrades(infos: List[VersionInfo], dry_run: bool = False):
    import subprocess

    for info in infos:
        pkg = info.name
        target = info.latest

        if dry_run:
            console.print(f"[cyan]Would upgrade {pkg} → {target}[/cyan]")
            continue

        console.print(f"[blue]Upgrading {pkg} → {target}...[/blue]")

        try:
            subprocess.run(
                ["pip", "install", "-U", f"{pkg}=={target}"],
                check=True,
            )
            console.print(f"[green]✓ {pkg} upgraded successfully[/green]")
        except subprocess.CalledProcessError as exc:
            console.print(f"[red]✗ Failed to upgrade {pkg}: {exc}[/red]")