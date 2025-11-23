from typer.testing import CliRunner
from pathlib import Path
import tempfile

from depup.cli.main import app

runner = CliRunner()


def write(path: Path, content: str):
    path.write_text(content)


def test_scan_lists_dependencies():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "requirements.txt", "requests==2.31.0\n")

        result = runner.invoke(app, ["scan", str(root)])

        assert result.exit_code == 0
        assert "requests" in result.stdout
        assert "2.31.0" in result.stdout
