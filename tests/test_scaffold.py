"""Smoke tests for the package scaffold."""

from __future__ import annotations

import qmj_tsx
from qmj_tsx.config import load_config, repo_root


def test_package_imports():
    assert hasattr(qmj_tsx, "__version__")


def test_default_config_loads():
    cfg = load_config()
    assert cfg.get("sample", "start") is not None
    assert cfg.data_raw.exists()
    assert cfg.path is not None


def test_repo_root_has_pyproject():
    assert (repo_root() / "pyproject.toml").is_file()


def test_cli_help_runs():
    from click.testing import CliRunner

    from qmj_tsx.cli import main

    runner = CliRunner()
    res = runner.invoke(main, ["--help"])
    assert res.exit_code == 0
    assert "QMJ-TSX" in res.output
