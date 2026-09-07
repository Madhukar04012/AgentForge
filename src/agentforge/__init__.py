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

"""AgentForge — AI Agent Development, Evaluation & Deployment Platform."""

import importlib.metadata

# Reported when the CLI runs from a source checkout rather than an installed
# distribution. Version checks treat it as "unknown, don't block".
DEV_VERSION = "0.0.0-dev"

try:
    __version__ = importlib.metadata.version("agentforge")
except importlib.metadata.PackageNotFoundError:
    # Fall back to the legacy distribution name so a checkout installed under
    # the old name (e.g. an in-place install of the pre-rename tree) still
    # reports a useful version instead of dev.
    try:
        __version__ = importlib.metadata.version("google-agents-cli")
    except importlib.metadata.PackageNotFoundError:
        __version__ = DEV_VERSION
