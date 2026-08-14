from __future__ import annotations

import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"gradio": "6.17.3", "smrt": "1.5.1"}


def _version_from_requirement(requirement: str, package: str) -> str:
    match = re.fullmatch(rf"{re.escape(package)}==([^\s#]+)", requirement.strip())
    assert match, f"{package} must be pinned with an exact == requirement"
    return match.group(1)


def test_requirements_and_project_pin_runtime_dependencies():
    requirement_lines = {
        line.strip()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_requirements = set(project["project"]["dependencies"])

    for package, version in EXPECTED.items():
        requirement = next(
            (line for line in requirement_lines if line.startswith(f"{package}==")),
            None,
        )
        assert requirement is not None
        assert _version_from_requirement(requirement, package) == version
        assert f"{package}=={version}" in project_requirements


def test_uv_lock_resolves_the_same_runtime_versions():
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked_versions = {
        package["name"]: package["version"] for package in lock["package"]
    }

    for package, version in EXPECTED.items():
        assert locked_versions[package] == version
