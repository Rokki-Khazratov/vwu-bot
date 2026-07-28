"""simplified subject tasks

Revision ID: c3f2a1b4d8e9
Revises: aa3f1f6f9a21
Create Date: 2026-07-09 23:45:00.000000
"""

from collections.abc import Sequence
from datetime import UTC, datetime
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "c3f2a1b4d8e9"
down_revision: str | None = "aa3f1f6f9a21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subject_tasks",
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("answer_format", sa.String(length=32), nullable=False),
        sa.Column("default_evaluator_code", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_id", "code", name="uq_subject_task_code"),
    )
    op.create_index(op.f("ix_subject_tasks_code"), "subject_tasks", ["code"], unique=False)
    op.create_index(
        op.f("ix_subject_tasks_subject_id"), "subject_tasks", ["subject_id"], unique=False
    )

    op.add_column("task_blueprints", sa.Column("subject_task_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_task_blueprints_subject_task_id"),
        "task_blueprints",
        ["subject_task_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_task_blueprints_subject_task_id_subject_tasks",
        "task_blueprints",
        "subject_tasks",
        ["subject_task_id"],
        ["id"],
    )
    op.alter_column("task_blueprints", "task_family_id", nullable=True)

    op.add_column("guidelines", sa.Column("subject_task_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_guidelines_subject_task_id_subject_tasks",
        "guidelines",
        "subject_tasks",
        ["subject_task_id"],
        ["id"],
    )

    op.add_column("rubrics", sa.Column("subject_task_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_rubrics_subject_task_id_subject_tasks",
        "rubrics",
        "subject_tasks",
        ["subject_task_id"],
        ["id"],
    )

    op.add_column("evaluation_profiles", sa.Column("subject_task_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_evaluation_profiles_subject_task_id_subject_tasks",
        "evaluation_profiles",
        "subject_tasks",
        ["subject_task_id"],
        ["id"],
    )

    op.add_column("training_sessions", sa.Column("subject_task_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_training_sessions_subject_task_id_subject_tasks",
        "training_sessions",
        "subject_tasks",
        ["subject_task_id"],
        ["id"],
    )
    op.alter_column("training_sessions", "exam_profile_id", nullable=True)

    op.add_column(
        "task_instances",
        sa.Column("source", sa.String(length=16), nullable=False, server_default="generated"),
    )
    op.create_index(op.f("ix_task_instances_source"), "task_instances", ["source"], unique=False)

    bind = op.get_bind()
    existing = {
        (str(row.subject_id), row.code)
        for row in bind.execute(sa.text("SELECT subject_id, code FROM subject_tasks"))
    }
    rows = bind.execute(
        sa.text(
            """
            SELECT
                ep.subject_id AS subject_id,
                s.code AS code,
                s.name AS name,
                s.position AS position,
                tf.answer_format AS answer_format,
                tf.default_evaluator_code AS default_evaluator_code,
                s.description AS description,
                s.is_active AS is_active
            FROM skills s
            JOIN exam_profiles ep ON ep.id = s.exam_profile_id
            JOIN task_families tf ON tf.skill_id = s.id
            """
        )
    )
    for row in rows:
        key = (str(row.subject_id), row.code)
        if key in existing:
            continue
        now = datetime.now(UTC)
        bind.execute(
            sa.text(
                """
                INSERT INTO subject_tasks (
                    id, subject_id, code, name, position, answer_format,
                    default_evaluator_code, description, is_active, created_at, updated_at
                )
                VALUES (
                    :id, :subject_id, :code, :name, :position, :answer_format,
                    :default_evaluator_code, :description, :is_active, :created_at, :updated_at
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "subject_id": row.subject_id,
                "code": row.code,
                "name": row.name,
                "position": row.position,
                "answer_format": row.answer_format,
                "default_evaluator_code": row.default_evaluator_code,
                "description": row.description,
                "is_active": row.is_active,
                "created_at": now,
                "updated_at": now,
            },
        )
        existing.add(key)
    op.execute(
        """
        UPDATE task_blueprints bp
        SET subject_task_id = st.id
        FROM task_families tf
        JOIN skills s ON s.id = tf.skill_id
        JOIN exam_profiles ep ON ep.id = s.exam_profile_id
        JOIN subject_tasks st ON st.subject_id = ep.subject_id AND st.code = s.code
        WHERE bp.task_family_id = tf.id
        """
    )
    op.execute(
        """
        UPDATE rubrics r
        SET subject_task_id = st.id
        FROM task_families tf
        JOIN skills s ON s.id = tf.skill_id
        JOIN exam_profiles ep ON ep.id = s.exam_profile_id
        JOIN subject_tasks st ON st.subject_id = ep.subject_id AND st.code = s.code
        WHERE r.task_family_id = tf.id
        """
    )
    op.execute(
        """
        UPDATE evaluation_profiles p
        SET subject_task_id = st.id
        FROM task_families tf
        JOIN skills s ON s.id = tf.skill_id
        JOIN exam_profiles ep ON ep.id = s.exam_profile_id
        JOIN subject_tasks st ON st.subject_id = ep.subject_id AND st.code = s.code
        WHERE p.task_family_id = tf.id
        """
    )
    op.execute(
        """
        UPDATE training_sessions ts
        SET subject_task_id = st.id
        FROM task_families tf
        JOIN skills s ON s.id = tf.skill_id
        JOIN exam_profiles ep ON ep.id = s.exam_profile_id
        JOIN subject_tasks st ON st.subject_id = ep.subject_id AND st.code = s.code
        WHERE ts.task_family_id = tf.id
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_instances_source"), table_name="task_instances")
    op.drop_column("task_instances", "source")
    op.drop_constraint(
        "fk_training_sessions_subject_task_id_subject_tasks",
        "training_sessions",
        type_="foreignkey",
    )
    op.alter_column("training_sessions", "exam_profile_id", nullable=False)
    op.drop_column("training_sessions", "subject_task_id")
    op.drop_constraint(
        "fk_evaluation_profiles_subject_task_id_subject_tasks",
        "evaluation_profiles",
        type_="foreignkey",
    )
    op.drop_column("evaluation_profiles", "subject_task_id")
    op.drop_constraint("fk_rubrics_subject_task_id_subject_tasks", "rubrics", type_="foreignkey")
    op.drop_column("rubrics", "subject_task_id")
    op.drop_constraint(
        "fk_guidelines_subject_task_id_subject_tasks", "guidelines", type_="foreignkey"
    )
    op.drop_column("guidelines", "subject_task_id")
    op.drop_constraint(
        "fk_task_blueprints_subject_task_id_subject_tasks",
        "task_blueprints",
        type_="foreignkey",
    )
    op.alter_column("task_blueprints", "task_family_id", nullable=False)
    op.drop_index(op.f("ix_task_blueprints_subject_task_id"), table_name="task_blueprints")
    op.drop_column("task_blueprints", "subject_task_id")
    op.drop_index(op.f("ix_subject_tasks_subject_id"), table_name="subject_tasks")
    op.drop_index(op.f("ix_subject_tasks_code"), table_name="subject_tasks")
    op.drop_table("subject_tasks")
