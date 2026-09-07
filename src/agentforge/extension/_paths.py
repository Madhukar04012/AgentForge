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

"""Filesystem locations for extension scopes and caches."""

from __future__ import annotations

import hashlib
import os
import re
import warnings
from collections.abc import Iterator
from pathlib import Path

from agentforge._project import find_project_root


def _user_config_dir_new() -> Path:
    # Roaming (APPDATA): config that should follow the user between machines.
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "agentforge"
        return Path.home() / "AppData" / "Roaming" / "agentforge"
    return Path.home() / ".config" / "agentforge"


def _user_config_dir_legacy() -> Path:
    # The pre-rename location; present if the user installed the old
    # distribution. We read from it as a fallback so existing extensions
    # keep loading after the rename.
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "agentforge"
        return Path.home() / "AppData" / "Roaming" / "agentforge"
    return Path.home() / ".config" / "agentforge"


def user_config_root() -> Path:
    """Return the user-scope config root.

    Prefers the new ``agentforge`` location. If it does not exist but the
    legacy ``agentforge`` location does, returns the legacy path and emits a
    one-time ``DeprecationWarning`` so users can move their data at leisure.
    """
    new = _user_config_dir_new()
    if new.exists():
        return new
    legacy = _user_config_dir_legacy()
    if legacy.exists():
        warnings.warn(
            f"User config root {legacy} is the pre-rename path. Move it to "
            f"{new} (or re-run `agentforge setup`) to silence this warning.",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy
    return new


def vendored_extensions_dir(scope_root: Path) -> Path:
    return scope_root / "extensions"


def scope_root(scope: str) -> Path | None:
    """Root for an install scope, or None for project scope outside a project.

    Returning None rather than raising leaves the wording of "you need a project"
    to the caller, since only the install commands can say what to do about it.
    """
    if scope == "user":
        return user_config_root()
    return find_project_root(Path.cwd())


def installed_scope_roots() -> Iterator[tuple[str, Path]]:
    """Yield (scope, root) for each resolvable scope, project before user.

    Skips project scope when not inside a project, so callers can iterate both
    scopes without repeating the "resolve root, skip if no project" boilerplate.
    """
    for scope in ("project", "user"):
        root = scope_root(scope)
        if root is not None:
            yield scope, root


def _git_cache_dir_new() -> Path:
    # Local (LOCALAPPDATA), not Roaming: re-clonable, and not worth syncing.
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        return root / "agentforge" / "git"
    return Path.home() / ".cache" / "agentforge" / "git"


def _git_cache_dir_legacy() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        return root / "agentforge" / "git"
    return Path.home() / ".cache" / "agentforge" / "git"


def git_cache_root() -> Path:
    """Return the shared git cache root directory.

    Same new-wins, legacy-OK rule as ``user_config_root``. The cache is
    re-clonable so falling back to the legacy path keeps existing extension
    installs working without a hidden copy step.
    """
    new = _git_cache_dir_new()
    if new.exists():
        return new
    legacy = _git_cache_dir_legacy()
    if legacy.exists():
        warnings.warn(
            f"Git cache root {legacy} is the pre-rename path. Move it to "
            f"{new} to silence this warning.",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy
    return new


def git_cache_dir_name(identity: str, url: str | None) -> str:
    """Return the cache directory name for a repo, as a single path component.

    ``identity`` is the readable ``org/repo``; ``url`` is the clone URL when the
    reference was given as one, and None for the github.com shorthand.

    A shorthand flattens to ``org__repo`` as it always has — the host is implied,
    so the name is unambiguous. A URL cannot do that: two hosts can serve the
    same ``org/repo``, and handing back one host's clone for the other's
    extension would run the wrong code. So a URL's name carries a digest of the
    URL, and the readable part is reduced to characters every filesystem accepts
    (a URL holds ``:`` and ``/``, and Windows rejects both).
    """
    if url is None:
        return identity.replace("/", "__")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", identity).strip("_") or "extension"
    return f"{slug}__{hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]}"
