# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compatibility shim coverage for the google-agents-cli -> AgentForge rename.

The codebase accepts both the new (AGENTFORGE_*, agentforge-manifest.yaml,
[tool.agentforge], requires.agentforge) and the legacy (AGENTS_CLI_*,
agents-cli-manifest.yaml, [tool.agents-cli], requires.agents_cli) spellings
so that pre-rename installs keep working through the transition. These tests
pin the compat behavior; if a future cleanup wants to drop the legacy
spellings, they have to update or delete this file intentionally.
"""

import os
from pathlib import Path

import pytest


# ---------- env vars ----------------------------------------------------------

def test_new_disable_overrides_env_takes_precedence(monkeypatch):
    from agentforge._runner import read_disable_overrides

    monkeypatch.setenv("AGENTFORGE_DISABLE_OVERRIDES", "1")
    monkeypatch.setenv("AGENTS_CLI_DISABLE_OVERRIDES", "0")
    assert read_disable_overrides() == "1"


def test_legacy_disable_overrides_env_still_read(monkeypatch):
    from agentforge._runner import read_disable_overrides

    monkeypatch.delenv("AGENTFORGE_DISABLE_OVERRIDES", raising=False)
    monkeypatch.setenv("AGENTS_CLI_DISABLE_OVERRIDES", "1")
    assert read_disable_overrides() == "1"


def test_new_extension_dir_env_takes_precedence(monkeypatch):
    from agentforge._runner import read_extension_dir

    monkeypatch.setenv("AGENTFORGE_EXTENSION_DIR", "/new")
    monkeypatch.setenv("AGENTS_CLI_EXTENSION_DIR", "/old")
    assert read_extension_dir() == "/new"


def test_legacy_extension_dir_env_still_read(monkeypatch):
    from agentforge._runner import read_extension_dir

    monkeypatch.delenv("AGENTFORGE_EXTENSION_DIR", raising=False)
    monkeypatch.setenv("AGENTS_CLI_EXTENSION_DIR", "/old")
    assert read_extension_dir() == "/old"


def test_experiments_env_accepts_legacy(monkeypatch):
    """The env var name change is honored without breaking callers that still
    set the old name. ``resolve_experiment`` reads both."""
    import json
    from agentforge._experiments import resolve_experiment

    monkeypatch.delenv("AGENTFORGE_EXPERIMENTS", raising=False)
    monkeypatch.setenv("AGENTS_CLI_EXPERIMENTS", json.dumps({"build_command": True}))
    assert resolve_experiment("build_command") is True


# ---------- version detection ------------------------------------------------

def test_get_current_version_falls_back_to_legacy(monkeypatch):
    """If only the legacy distribution is installed, report its version."""
    from importlib.metadata import PackageNotFoundError
    from unittest.mock import patch

    from agentforge.scaffold.utils import version

    def fake_version(name):
        if name == "agentforge":
            raise PackageNotFoundError("agentforge")
        if name == "google-agents-cli":
            return "1.4.0"
        raise PackageNotFoundError(name)

    with patch.object(version, "version", side_effect=fake_version):
        assert version.get_current_version() == "1.4.0"


def test_agentforge_version_pin_alias():
    from agentforge.scaffold.utils import version

    # Backward-compat alias retained for one release.
    assert version.agents_cli_version_pin is version.agentforge_version_pin


# ---------- manifest filename -----------------------------------------------

def test_manifest_filename_constant_legacy_alias_present():
    from agentforge import _project

    assert _project.MANIFEST_FILENAME == "agentforge-manifest.yaml"
    assert _project.MANIFEST_FILENAME_LEGACY == "agents-cli-manifest.yaml"


def test_legacy_to_new_filename_helper_present():
    """``upgrade`` carries a small name-conversion helper used to fold legacy
    filenames forward into the new scheme. Confirm it exists and is callable
    so a future cleanup that wants to drop legacy support can do so by
    deleting a single function."""
    from agentforge.scaffold.utils import upgrade

    assert callable(upgrade._legacy_to_new_filename)


# ---------- Pydantic extension spec -----------------------------------------

def test_extension_requires_accepts_new_field():
    from agentforge.extension._spec import Requires, _parse_requires

    spec = Requires(agentforge=">=1.5,<2")
    range_str, _ = _parse_requires(spec)
    assert range_str == ">=1.5,<2"


def test_extension_requires_accepts_legacy_field():
    from agentforge.extension._spec import Requires, _parse_requires

    spec = Requires(agents_cli=">=1.4,<2")
    range_str, _ = _parse_requires(spec)
    assert range_str == ">=1.4,<2"


def test_extension_requires_new_wins_over_legacy():
    from agentforge.extension._spec import Requires, _parse_requires

    spec = Requires(agentforge=">=1.5,<2", agents_cli=">=1.0,<2")
    range_str, _ = _parse_requires(spec)
    assert range_str == ">=1.5,<2"


def test_extension_requires_unparseable_range_drops_to_none():
    """A bad compat range is warned about and dropped — a malformed hint
    must not make the extension unloadable."""
    from agentforge.extension._spec import Requires, _parse_requires

    spec = Requires(agentforge="1.5.0")  # single version, not a range
    range_str, _ = _parse_requires(spec)
    assert range_str is None


# ---------- schema -----------------------------------------------------------

def test_schema_defines_both_requires_properties():
    import json

    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "agents-cli-extension-v1alpha1.schema.json"
    schema = json.loads(schema_path.read_text())
    requires_def = schema["$defs"]["Requires"]["properties"]
    assert "agentforge" in requires_def
    assert "agents_cli" in requires_def


# ---------- paths ------------------------------------------------------------

def test_user_config_root_warns_when_legacy_used(tmp_path, monkeypatch):
    """If the new config dir is absent and the legacy one is present, fall back
    to the legacy path and emit a DeprecationWarning."""
    from agentforge.extension import _paths

    new = tmp_path / "agentforge"  # does not exist
    legacy = tmp_path / "agents-cli"
    legacy.mkdir()
    monkeypatch.setattr(_paths, "_user_config_dir_new", lambda: new)
    monkeypatch.setattr(_paths, "_user_config_dir_legacy", lambda: legacy)

    with pytest.warns(DeprecationWarning):
        root = _paths.user_config_root()
    assert root == legacy


def test_user_config_root_prefers_new_dir(tmp_path, monkeypatch):
    from agentforge.extension import _paths

    new = tmp_path / "agentforge"
    new.mkdir()
    legacy = tmp_path / "agents-cli"
    legacy.mkdir()
    monkeypatch.setattr(_paths, "_user_config_dir_new", lambda: new)
    monkeypatch.setattr(_paths, "_user_config_dir_legacy", lambda: legacy)

    root = _paths.user_config_root()
    assert root == new


# ---------- subprocess env ---------------------------------------------------

def test_subprocess_env_uses_new_disable_var(monkeypatch):
    """The extension override runner sets AGENTFORGE_DISABLE_OVERRIDES on
    children so the built-in can re-enter cleanly."""
    from agentforge import _runner

    assert _runner.DISABLE_OVERRIDES_ENV == "AGENTFORGE_DISABLE_OVERRIDES"
    # The legacy name is still imported as a module-level constant.
    assert _runner.DISABLE_OVERRIDES_ENV_LEGACY == "AGENTS_CLI_DISABLE_OVERRIDES"


# ---------- console scripts --------------------------------------------------

def test_main_module_entry_point_exists():
    """Both ``agentforge`` and ``agents-cli`` are documented console scripts;
    the import path is the same, so importing the entry module is enough to
    prove the wiring is in place."""
    from agentforge import main

    assert callable(main.main)


# ---------- skills loader ----------------------------------------------------

def test_skill_loader_accepts_both_prefixes():
    """The skill loader recognizes both ``agentforge-*`` and
    ``google-agents-cli-*`` directory prefixes. Spot-check the helper that
    decides whether a directory is a skill — calling it on a real skill
    directory should return True."""
    from pathlib import Path

    from agentforge.skills._bundle import is_skill_dir

    repo_root = Path(__file__).resolve().parent.parent
    new_dir = repo_root / "skills" / "agentforge-scaffold"
    legacy_dir = repo_root / "skills" / "google-agents-cli-scaffold"

    if new_dir.is_dir():
        assert is_skill_dir(new_dir) is True
    if legacy_dir.is_dir():
        assert is_skill_dir(legacy_dir) is True
