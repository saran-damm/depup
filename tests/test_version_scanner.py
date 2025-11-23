import subprocess
from unittest.mock import patch

from depup.core.version_scanner import VersionScanner, VersionInfo
from depup.core.parser import DependencySpec


def fake_pip_output(package: str):
    return {
        "requests": """requests (2.30.0)
Available versions: 2.30.0, 2.29.0, 2.28.2
""",
        "numpy": """numpy (2.0.0)
Available versions: 2.0.0, 1.26.0, 1.25.0
""",
    }[package]


@patch("subprocess.run")
def test_version_scanner_patch(mock_run):
    mock_run.return_value.stdout = fake_pip_output("requests")
    dep = DependencySpec("requests", "==2.29.0", None)

    scanner = VersionScanner()
    result = scanner.scan([dep])[0]

    assert result.latest == "2.30.0"
    assert result.update_type == "patch"


@patch("subprocess.run")
def test_version_scanner_major(mock_run):
    mock_run.return_value.stdout = fake_pip_output("numpy")
    dep = DependencySpec("numpy", "==1.26.0", None)

    scanner = VersionScanner()
    result = scanner.scan([dep])[0]

    assert result.latest == "2.0.0"
    assert result.update_type == "major"
