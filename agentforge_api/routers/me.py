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

"""``GET /api/v1/me`` — current user.

Returns the user attached to the request by :func:`get_current_user`,
or 401 if no valid session is present. Phase 1 only authenticates
demo sessions; full login lands in Phase 13.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..models.workspace import User
from ..schemas import UserOut

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserOut)
def read_me(
    user: Annotated[User, Depends(get_current_user)],
) -> UserOut:
    """Return the authenticated user."""
    return UserOut.model_validate(user)
