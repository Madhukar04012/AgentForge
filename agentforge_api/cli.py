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

"""``python -m agentforge_api`` entrypoint.

Launches a uvicorn server with the application from
:mod:`agentforge_api.app`. The host and port come from
``Settings.api_host`` / ``Settings.api_port``; both are overridable via
environment variables (``AGENTFORGE_API_HOST``, ``AGENTFORGE_API_PORT``).
"""

from __future__ import annotations

import uvicorn

from .config import get_settings


def main() -> None:
    """Run the API server using uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "agentforge_api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
