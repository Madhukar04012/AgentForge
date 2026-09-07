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

"""agentforge scaffold command group."""

import click

from agentforge._click import LazyGroup


@click.group("scaffold", cls=LazyGroup)
def scaffold_group():
    """Scaffold, enhance, and upgrade agent projects.

    \b
    Subcommands:
      create   Create a new agent project
      enhance  Add deployment target or CI/CD to an existing project
      upgrade  Upgrade project to a newer agentforge version
    """


scaffold_group.add_lazy_command(
    "create",
    "agentforge.scaffold.commands.create:create",
    "Create GCP-based AI agent projects from templates.",
)
scaffold_group.add_lazy_command(
    "enhance",
    "agentforge.scaffold.commands.enhance:enhance",
    "Enhance your existing project with deployment, CI/CD, or RAG scaffolding.",
)
scaffold_group.add_lazy_command(
    "upgrade",
    "agentforge.scaffold.commands.upgrade:upgrade",
    "Upgrade project to a newer agentforge version.",
)
