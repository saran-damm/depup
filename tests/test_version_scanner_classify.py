from depup.core.models import UpdateType
from depup.core.version_scanner import VersionScanner


def test_classify_equal_versions_none():
    vs = VersionScanner()
    assert vs._classify("==1.2.3", "1.2.3") == UpdateType.NONE


def test_classify_major_minor_patch():
    vs = VersionScanner()
    assert vs._classify("==1.2.3", "2.0.0") == UpdateType.MAJOR
    assert vs._classify("==1.2.3", "1.3.0") == UpdateType.MINOR
    assert vs._classify("==1.2.3", "1.2.4") == UpdateType.PATCH


def test_classify_invalid_versions_unknown():
    vs = VersionScanner()
    assert vs._classify("==2004d", "1.0.0") == UpdateType.NONE
