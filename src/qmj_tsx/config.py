"""Config loader. Reads YAML and resolves repo-root-relative paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    """Locate the repo root (the directory containing pyproject.toml)."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError("Could not locate repo root (no pyproject.toml found).")


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any] = field(default_factory=dict)
    path: Path | None = None

    @property
    def root(self) -> Path:
        return repo_root()

    def resolve(self, rel: str) -> Path:
        return self.root / rel

    @property
    def data_raw(self) -> Path:
        return self.resolve(self.raw["paths"]["data_raw"])

    @property
    def data_interim(self) -> Path:
        return self.resolve(self.raw["paths"]["data_interim"])

    @property
    def data_processed(self) -> Path:
        return self.resolve(self.raw["paths"]["data_processed"])

    def get(self, *keys: str, default: Any = None) -> Any:
        cur: Any = self.raw
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur


def load_config(path: str | Path | None = None) -> Config:
    """Load YAML config; defaults to configs/default.yaml at the repo root."""
    if path is None:
        path = repo_root() / "configs" / "default.yaml"
    path = Path(path)
    with path.open() as f:
        raw = yaml.safe_load(f) or {}
    return Config(raw=raw, path=path)
