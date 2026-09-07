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

"""agents + agent_versions + executions + execution_events — Phase 2

Revision ID: 0002_agents_executions
Revises: 0001_init
Create Date: 2026-09-07

Adds the four tables required for the real agent runtime vertical
slice:

  * ``agents`` — logical, named agent within a workspace.
  * ``agent_versions`` — **immutable** config snapshot. The runtime
    always executes against a specific version, never against the
    mutable ``agents.current_version_id``.
  * ``executions`` — a single attempt to run a specific
    ``agent_version_id`` with a user input.
  * ``execution_events`` — append-only event log for an execution,
    ordered by ``sequence``.

The deferred FK on ``agents.current_version_id`` →
``agent_versions.id`` is created via ``use_alter`` on the model, and
mirrored here with two passes (create the column without the FK,
then ``alter_column`` to add it). SQLite has historically required
this dance for self-referential circular FKs.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_agents_executions"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_EXECUTION_STATUS_VALUES = (
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
)


def upgrade() -> None:
    # --- agents ---------------------------------------------------------
    op.create_table(
        "agents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            sa.ForeignKey("workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # current_version_id is added below with a deferred FK so
        # the agents ↔ agent_versions chicken-and-egg resolves.
        sa.Column("current_version_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "name", name="agents_workspace_name_uniq"),
    )
    op.create_index("ix_agents_workspace_id", "agents", ["workspace_id"])

    # --- agent_versions -------------------------------------------------
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "agent_id",
            sa.String(length=36),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "agent_id", "version_number", name="agent_versions_agent_version_uniq"
        ),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])

    # Now wire agents.current_version_id -> agent_versions.id. SQLite
    # requires batch mode for this; Postgres handles it inline.
    with op.batch_alter_table("agents") as batch_op:
        batch_op.create_foreign_key(
            "agents_current_version_id_fkey",
            "agent_versions",
            ["current_version_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # --- executions -----------------------------------------------------
    op.create_table(
        "executions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            sa.ForeignKey("workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            sa.String(length=36),
            sa.ForeignKey("agents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_version_id",
            sa.String(length=36),
            sa.ForeignKey("agent_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(*_EXECUTION_STATUS_VALUES, name="execution_status"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "triggered_by_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_executions_workspace_id", "executions", ["workspace_id"])
    op.create_index("ix_executions_agent_version_id", "executions", ["agent_version_id"])
    op.create_index("ix_executions_status", "executions", ["status"])
    op.create_index("ix_executions_queued_at", "executions", ["queued_at"])

    # --- execution_events ----------------------------------------------
    op.create_table(
        "execution_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "execution_id",
            sa.String(length=36),
            sa.ForeignKey("executions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_execution_events_execution_id", "execution_events", ["execution_id"]
    )
    op.create_index(
        "ix_execution_events_exec_seq",
        "execution_events",
        ["execution_id", "sequence"],
    )


def downgrade() -> None:
    op.drop_index("ix_execution_events_exec_seq", table_name="execution_events")
    op.drop_index("ix_execution_events_execution_id", table_name="execution_events")
    op.drop_table("execution_events")

    op.drop_index("ix_executions_queued_at", table_name="executions")
    op.drop_index("ix_executions_status", table_name="executions")
    op.drop_index("ix_executions_agent_version_id", table_name="executions")
    op.drop_index("ix_executions_workspace_id", table_name="executions")
    op.drop_table("executions")
    sa.Enum(name="execution_status").drop(op.get_bind(), checkfirst=True)

    # Drop the deferred FK on agents.current_version_id before
    # removing the agent_versions table.
    with op.batch_alter_table("agents") as batch_op:
        batch_op.drop_constraint("agents_current_version_id_fkey", type_="foreignkey")

    op.drop_index("ix_agent_versions_agent_id", table_name="agent_versions")
    op.drop_table("agent_versions")

    op.drop_index("ix_agents_workspace_id", table_name="agents")
    op.drop_table("agents")
