from unittest.mock import patch, Mock

from depup.core.models import DependencySpec, UpdateType
from depup.core.version_scanner import VersionScanner


def mock_pypi(version: str):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {"info": {"version": version}}
    return resp


@patch("depup.core.version_scanner.requests.get")
def test_version_scanner_minor(mock_get):
    mock_get.return_value = mock_pypi("2.30.0")

    dep = DependencySpec("requests", "==2.29.0", None)
    result = VersionScanner().scan([dep])[0]

    assert result.latest == "2.30.0"
    assert result.update_type == UpdateType.MINOR


@patch("depup.core.version_scanner.requests.get")
def test_version_scanner_patch(mock_get):
    mock_get.return_value = mock_pypi("1.5.3")

    dep = DependencySpec("pandas", "==1.5.2", None)
    result = VersionScanner().scan([dep])[0]

    assert result.update_type == UpdateType.PATCH


@patch("depup.core.version_scanner.requests.get")
def test_version_scanner_major(mock_get):
    mock_get.return_value = mock_pypi("2.0.0")

    dep = DependencySpec("numpy", "==1.26.0", None)
    result = VersionScanner().scan([dep])[0]

    assert result.update_type == UpdateType.MAJOR
