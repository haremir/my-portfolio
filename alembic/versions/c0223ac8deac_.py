"""Create educationmodel and experiencemodel tables.

Revision ID: c0223ac8deac
Revises:
Create Date: 2026-05-16 19:05:14.151397

Notes
-----
This migration is written to be idempotent: it checks whether each table
exists before creating it.  This is necessary because rx.Model (deprecated
in Reflex 0.9.2) used to auto-create tables at import time, meaning the
tables can exist in the DB before Alembic has recorded any version.

If you encounter 'table already exists' on a fresh clone, run:
    alembic stamp head
to register the current revision without re-running the DDL.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c0223ac8deac"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    """Return True if *name* already exists in the database."""
    conn = op.get_bind()
    return sa.inspect(conn).has_table(name)


def upgrade() -> None:
    """Create tables only when they don't already exist (idempotent)."""
    if not _table_exists("educationmodel"):
        op.create_table(
            "educationmodel",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("okul_adi", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("bolum", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("baslangic_yili", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("mezuniyet_yili", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("detay", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("experiencemodel"):
        op.create_table(
            "experiencemodel",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("sirket_adi", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("pozisyon", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("sure", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("aciklama", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    """Drop tables (reverse of upgrade)."""
    op.drop_table("experiencemodel")
    op.drop_table("educationmodel")
