from pathlib import Path
import tempfile
from unittest.mock import patch

from depup.core.upgrade_executor import UpgradeExecutor, PlannedUpgrade
from depup.core.parser import DependencySpec


def test_update_pyproject_pep621_dependencies():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        py = root / "pyproject.toml"
        py.write_text(
            """
[project]
name = "example"
version = "0.1.0"
dependencies = [
  "requests>=2.30.0",
  "numpy==1.25.0",
]
"""
        )

        deps = [
            DependencySpec(name="requests", version=">=2.30.0", source_file=py),
            DependencySpec(name="numpy", version="==1.25.0", source_file=py),
        ]
        plan = PlannedUpgrade(
            name="requests",
            current_spec=">=2.30.0",
            target_version="2.31.0",
            source_file=py,
        )

        executor = UpgradeExecutor(project_root=root, dependencies=deps)

        with patch("depup.core.upgrade_executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            executor.execute([plan], dry_run=False)

        content = py.read_text()
        assert 'requests>=2.31.0' in content
        assert 'requests>=2.30.0' not in content


def test_update_pyproject_poetry_dependencies():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        py = root / "pyproject.toml"
        py.write_text(
            """
[tool.poetry]
name = "example"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.11"
requests = ">=2.30.0"
"""
        )

        deps = [
            DependencySpec(name="requests", version=">=2.30.0", source_file=py),
        ]
        plan = PlannedUpgrade(
            name="requests",
            current_spec=">=2.30.0",
            target_version="2.31.0",
            source_file=py,
        )

        executor = UpgradeExecutor(project_root=root, dependencies=deps)

        with patch("depup.core.upgrade_executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            executor.execute([plan], dry_run=False)

        content = py.read_text()
        assert 'requests = ">=2.31.0"' in content
        assert 'requests = ">=2.30.0"' not in content


def test_update_pipfile_packages_section():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pipfile = root / "Pipfile"
        pipfile.write_text(
            """
[packages]
requests = ">=2.30.0"
numpy = "*"

[dev-packages]
pytest = ">=7.0.0"
"""
        )

        deps = [
            DependencySpec(name="requests", version=">=2.30.0", source_file=pipfile),
            DependencySpec(name="pytest", version=">=7.0.0", source_file=pipfile),
        ]
        plan = PlannedUpgrade(
            name="requests",
            current_spec=">=2.30.0",
            target_version="2.31.0",
            source_file=pipfile,
        )

        executor = UpgradeExecutor(project_root=root, dependencies=deps)

        with patch("depup.core.upgrade_executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            executor.execute([plan], dry_run=False)

        content = pipfile.read_text()
        # requests version should be updated
        assert 'requests = ">=2.31.0"' in content
        assert 'requests = ">=2.30.0"' not in content
        # wildcard remains unchanged
        assert 'numpy = "*"' in content
