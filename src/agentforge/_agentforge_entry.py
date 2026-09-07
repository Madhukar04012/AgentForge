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

"""AgentForge CLI entry point.

The new, user-facing primary command name is ``agentforge``. This module is
the thin wrapper that the package's console script (added by the release
process) calls when the user runs ``agentforge <subcommand>`` — it re-invokes
the same Click group that the legacy ``agentforge`` console script uses.

Both ``agentforge`` and ``agentforge`` resolve to the same ``main()`` function
in ``agentforge.main``; the only difference is the program name they
self-identify with in ``--help`` and ``--version`` output, which is derived
from ``sys.argv[0]``. The legacy command remains fully supported as a
compatibility alias while users transition.

This is a rename, not a rewrite: every command, flag, scaffold, extension,
skill, and security protection is unchanged.
"""

from __future__ import annotations

from agentforge.main import main as _main


def main() -> None:
    """Entry point for the ``agentforge`` console script.

    Delegates to the same Click group as ``agentforge``. The program name
    shown in --help/--version is taken from the script that was actually
    invoked (so `agentforge --version` reports `agentforge`, and
    `agentforge --version` reports `agentforge`).
    """
    _main()


if __name__ == "__main__":
    main()
