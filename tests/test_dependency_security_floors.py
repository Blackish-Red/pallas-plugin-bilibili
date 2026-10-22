from __future__ import annotations

import importlib.metadata
import re
import tomllib
from pathlib import Path

# 传递依赖安全下限回归：旧解析结果会让本测试失败，升级到下限后通过。
SECURITY_FLOORS: dict[str, str] = {
    "multidict": "6.9.1",
}

# 必须进分发 metadata（project.dependencies）的运行时下限；仅 dev 使用的项不在此列。
RUNTIME_FLOORS: dict[str, str] = {
    "multidict": "6.9.1",
}


def parse_version(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in value.split("."):
        digits = ""
        for char in chunk:
            if not char.isdigit():
                break
            digits += char
        parts.append(int(digits or "0"))
    return tuple(parts)


def declared_floor(requirements: list[str], package: str) -> str | None:
    for requirement in requirements:
        name = re.split(r"[\[<>=!~; ]", requirement, maxsplit=1)[0].strip().lower().replace("_", "-")
        if name != package.replace("_", "-"):
            continue
        match = re.search(r">=\s*([0-9][0-9A-Za-z.*+!-]*)", requirement)
        return match.group(1) if match else None
    return None


def test_dependency_security_floors() -> None:
    for package, floor in SECURITY_FLOORS.items():
        installed = importlib.metadata.version(package)
        assert parse_version(installed) >= parse_version(floor), f"{package} {installed} < security floor {floor}"


def test_project_metadata_declares_runtime_floors() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as handle:
        requirements = tomllib.load(handle)["project"]["dependencies"]
    for package, floor in RUNTIME_FLOORS.items():
        declared = declared_floor(requirements, package)
        assert declared is not None, f"{package} 未在 project.dependencies 声明运行时安全下限"
        assert parse_version(declared) >= parse_version(floor), f"{package} 声明下限 {declared} < 安全下限 {floor}"
