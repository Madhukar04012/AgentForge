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

"""Locate the bundled AgentForge skills.

The canonical skills live in ``data/`` next to this file
(``src/google/agents/cli/skills/data/``). Because that directory is inside the
package, it's automatically bundled in the wheel - so ``agentforge setup`` can
install skills with no ``git`` and no network.

This module is just a small helper to locate the skills dir based on a relative
path from this module.
"""

from __future__ import annotations

from pathlib import Path

# Skill directories are recognised under both the new ``agentforge-*`` prefix
# (the user-facing brand going forward) and the legacy ``google-agents-cli-*``
# prefix (preserved so previously installed skills keep being detected after
# the rename — renaming a directory on disk would orphan everyone's install).
_SKILL_PREFIXES: tuple[str, ...] = ("agentforge-", "google-agents-cli-")

SKILL_BUNDLE_DIR = Path(__file__).resolve().parent / "data"


def is_skill_dir(path: Path) -> bool:
    """Return True if ``path`` is a bundled skill directory.

    A skill is a directory whose name starts with one of the recognised
    prefixes (``agentforge-*`` or the legacy ``google-agents-cli-*``) and
    contains a ``SKILL.md`` spec.
    """
    if not path.is_dir() or not (path / "SKILL.md").is_file():
        return False
    return any(path.name.startswith(prefix) for prefix in _SKILL_PREFIXES)


def get_bundled_skills_dir() -> Path | None:
    """
    Run a sanity check on whether the skill bundle is actually present and contains skills.
    If yes, return path to it. Return None otherwise.
    """
    if not SKILL_BUNDLE_DIR.is_dir():
        return None
    return (
        SKILL_BUNDLE_DIR
        if any(is_skill_dir(d) for d in SKILL_BUNDLE_DIR.iterdir())
        else None
    )
