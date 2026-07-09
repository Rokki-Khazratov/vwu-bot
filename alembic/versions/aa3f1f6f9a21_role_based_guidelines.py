"""role based guidelines

Revision ID: aa3f1f6f9a21
Revises: 819cea87c48d
Create Date: 2026-07-09 22:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "aa3f1f6f9a21"
down_revision: str | None = "819cea87c48d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "guidelines",
        sa.Column("default_role", sa.String(length=32), nullable=False, server_default="notes"),
    )
    op.create_table(
        "task_blueprint_guidelines",
        sa.Column("blueprint_id", sa.Uuid(), nullable=False),
        sa.Column("guideline_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("include_in_generation", sa.Boolean(), nullable=False),
        sa.Column("include_in_evaluation", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["blueprint_id"], ["task_blueprints.id"]),
        sa.ForeignKeyConstraint(["guideline_id"], ["guidelines.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("blueprint_id", "guideline_id", "role", name="uq_blueprint_guideline_role"),
    )
    op.create_index(
        op.f("ix_task_blueprint_guidelines_blueprint_id"),
        "task_blueprint_guidelines",
        ["blueprint_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_blueprint_guidelines_guideline_id"),
        "task_blueprint_guidelines",
        ["guideline_id"],
        unique=False,
    )
    op.create_table(
        "task_instance_guidelines",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("guideline_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("include_in_generation", sa.Boolean(), nullable=False),
        sa.Column("include_in_evaluation", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["guideline_id"], ["guidelines.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["task_instances.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "guideline_id", "role", name="uq_task_guideline_role"),
    )
    op.create_index(
        op.f("ix_task_instance_guidelines_guideline_id"),
        "task_instance_guidelines",
        ["guideline_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_instance_guidelines_task_id"),
        "task_instance_guidelines",
        ["task_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_instance_guidelines_task_id"), table_name="task_instance_guidelines")
    op.drop_index(
        op.f("ix_task_instance_guidelines_guideline_id"),
        table_name="task_instance_guidelines",
    )
    op.drop_table("task_instance_guidelines")
    op.drop_index(
        op.f("ix_task_blueprint_guidelines_guideline_id"),
        table_name="task_blueprint_guidelines",
    )
    op.drop_index(
        op.f("ix_task_blueprint_guidelines_blueprint_id"),
        table_name="task_blueprint_guidelines",
    )
    op.drop_table("task_blueprint_guidelines")
    op.drop_column("guidelines", "default_role")
