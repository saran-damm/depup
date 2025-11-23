import tempfile
from pathlib import Path

from depup.core.parser import DependencyParser, DependencySpec
from depup.core.exceptions import InvalidDependencyFileError


def write(path: Path, content: str):
    path.write_text(content)


def test_parse_requirements():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        req = root / "requirements.txt"
        write(req, "requests==2.31.0\nnumpy>=1.20\n")

        parser = DependencyParser(root)
        deps = parser.parse_all()

        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[1].version == ">=1.20"


def test_parse_pyproject_pep621():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        file = root / "pyproject.toml"
        write(
            file,
            """
[project]
dependencies = [
    "requests>=2.0",
    "numpy"
]
""",
        )
        parser = DependencyParser(root)
        deps = parser.parse_all()

        assert len(deps) == 2
        assert deps[0].name == "requests"
        assert deps[0].version == ">=2.0"


def test_parse_pipfile():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pipfile = root / "Pipfile"
        write(
            pipfile,
            """
[packages]
flask = "2.2.5"
[dev-packages]
pytest = "*"
""",
        )
        parser = DependencyParser(root)
        deps = parser.parse_all()

        names = {d.name for d in deps}
        assert "flask" in names
        assert "pytest" in names


def test_unsupported_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        badfile = root / "weird.txt"
        write(badfile, "???")

        parser = DependencyParser(root)
        parser.SUPPORTED_FILES.append("weird.txt")

        # Expecting failure during parsing
        try:
            parser.parse_all()
            assert False, "Expected exception not raised"
        except InvalidDependencyFileError:
            pass
