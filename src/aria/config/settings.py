from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def user_env_path() -> Path:
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "aria" / ".env"


def project_env_path(workspace: Path | None = None) -> Path:
    return (workspace or Path.cwd()) / ".env"


def default_write_env_path(workspace: Path | None = None) -> Path:
    root = workspace or Path.cwd()
    if (root / "pyproject.toml").exists() and (root / "src" / "aria").exists():
        return root / ".env"
    return user_env_path()


def write_env_value(path: Path, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    updated = False
    output: list[str] = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            output.append(f"{key}={value}")
            updated = True
        else:
            output.append(line)
    if not updated:
        output.append(f"{key}={value}")
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def _parse_toml_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    import tomllib

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    aria = data.get("aria", data)
    if not isinstance(aria, dict):
        return {}

    mapping = {
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "model": "ARIA_MODEL",
        "memory_backend": "ARIA_MEMORY_BACKEND",
        "data_dir": "ARIA_DATA_DIR",
        "headless": "ARIA_HEADLESS",
        "max_steps": "ARIA_MAX_STEPS",
        "max_failures": "ARIA_MAX_FAILURES",
    }
    values: dict[str, str] = {}
    for key, env_key in mapping.items():
        value = aria.get(key)
        if value is not None:
            values[env_key] = str(value)
    return values


def _pick(values: dict[str, str], key: str, default: str | None = None) -> str | None:
    return os.getenv(key) or values.get(key) or default


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no", "off"}


def _int(value: str | None, default: int) -> int:
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    workspace: Path = Path.cwd()
    reports_dir: Path = Path("reports")
    data_dir: Path = Path(".aria")
    memory_dir: Path = Path(".aria/memory")
    screenshots_dir: Path = Path(".aria/screenshots")
    max_steps: int = 8
    max_failures: int = 3
    headless: bool = True
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    model: str = os.getenv("ARIA_MODEL", "gpt-5-mini")
    memory_backend: str = os.getenv("ARIA_MEMORY_BACKEND", "json")
    vision_model: str = os.getenv("ARIA_VISION_MODEL", "claude-sonnet-4-20250514")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls.load()

    @classmethod
    def load(cls, workspace: Path | None = None) -> "Settings":
        root = workspace or Path.cwd()
        values: dict[str, str] = {}
        values.update(_parse_env_file(user_env_path()))
        values.update(_parse_toml_config(root / "aria.toml"))
        values.update(_parse_env_file(root / ".env"))

        data_dir = Path(_pick(values, "ARIA_DATA_DIR", ".aria") or ".aria")
        return cls(
            workspace=root,
            reports_dir=Path("reports"),
            data_dir=data_dir,
            memory_dir=data_dir / "memory",
            screenshots_dir=data_dir / "screenshots",
            max_steps=_int(_pick(values, "ARIA_MAX_STEPS"), 8),
            max_failures=_int(_pick(values, "ARIA_MAX_FAILURES"), 3),
            headless=_bool(_pick(values, "ARIA_HEADLESS"), True),
            openai_api_key=_pick(values, "OPENAI_API_KEY"),
            anthropic_api_key=_pick(values, "ANTHROPIC_API_KEY"),
            model=_pick(values, "ARIA_MODEL", "gpt-5-mini") or "gpt-5-mini",
            memory_backend=(_pick(values, "ARIA_MEMORY_BACKEND", "json") or "json").lower(),
            vision_model=_pick(values, "ARIA_VISION_MODEL", "claude-sonnet-4-20250514")
            or "claude-sonnet-4-20250514",
        )

    def redacted(self) -> dict[str, Any]:
        return {
            "OPENAI_API_KEY": "set" if self.openai_api_key else "missing",
            "ANTHROPIC_API_KEY": "set" if self.anthropic_api_key else "missing optional",
            "ARIA_MODEL": self.model,
            "ARIA_MEMORY_BACKEND": self.memory_backend,
            "ARIA_DATA_DIR": str(self.data_dir),
            "reports_dir": str(self.reports_dir),
            "headless": self.headless,
        }
