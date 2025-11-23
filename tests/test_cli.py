from pathlib import Path
import tempfile
from unittest.mock import patch

from typer.testing import CliRunner

from depup.cli.main import app
from depup.core.version_scanner import VersionInfo

runner = CliRunner()


def write(path: Path, content: str) -> None:
    path.write_text(content)


def test_scan_lists_dependencies():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "requirements.txt", "requests==2.31.0\n")

        result = runner.invoke(app, ["scan", str(root)])

        assert result.exit_code == 0
        assert "requests" in result.stdout
        assert "2.31.0" in result.stdout


@patch("depup.cli.main.VersionScanner")
def test_scan_with_latest_uses_version_scanner(mock_version_scanner) -> None:
    # Arrange fake VersionScanner.scan result
    instance = mock_version_scanner.return_value
    instance.scan.return_value = [
        VersionInfo(
            name="requests",
            current="==2.30.0",
            latest="2.31.0",
            update_type="patch",
        )
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "requirements.txt", "requests==2.30.0\n")

        result = runner.invoke(app, ["scan", "--latest", str(root)])

    assert result.exit_code == 0
    # Should show latest version and update type
    assert "requests" in result.stdout
    assert "2.31.0" in result.stdout
    assert "patch" in result.stdout
