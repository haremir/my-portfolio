"""
Alembic migration environment for harun_site.

Key fixes vs. the original generated file
------------------------------------------
1. target_metadata now points at SQLModel.metadata so that
   'alembic revision --autogenerate' sees the actual tables.

2. The database URL is read from rxconfig.py at runtime so that
   Alembic always connects to the same database as the app.
   The placeholder URL in alembic.ini ('driver://...') is never used.

3. render_as_batch=True is set for both offline and online modes.
   SQLite does NOT support ALTER TABLE natively; batch mode rewrites
   tables transparently so column additions / renames work correctly.

4. EducationModel and ExperienceModel are imported explicitly so their
   table definitions are registered with SQLModel.metadata before
   autogenerate introspects the schema.

Usage
-----
    # First-time setup (applies existing migration, creates tables):
    alembic upgrade head

    # After adding a new model field:
    alembic revision --autogenerate -m "add <field> to <model>"
    alembic upgrade head

    # Roll back one migration:
    alembic downgrade -1
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
from alembic import context

# ── Project root on sys.path so 'from harun_site...' imports work ────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Import models so their tables are registered with SQLModel.metadata ───────
# This MUST happen before target_metadata is assigned below.
from harun_site.models import EducationModel, ExperienceModel  # noqa: F401, E402

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Wire target_metadata ──────────────────────────────────────────────────────
# Without this, 'alembic revision --autogenerate' produces empty migrations.
target_metadata = SQLModel.metadata


# ── Override the DB URL from rxconfig so Alembic talks to the real DB ─────────
def _get_db_url() -> str:
    """Return the database URL from rxconfig, falling back to the ini value."""
    try:
        from rxconfig import config as rx_config  # type: ignore[import]
        return str(rx_config.db_url)
    except Exception:
        fallback = config.get_main_option("sqlalchemy.url", "sqlite:///reflex.db")
        return fallback


config.set_main_option("sqlalchemy.url", _get_db_url())


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection ('offline' mode).

    Generates SQL DDL that can be inspected or piped to a DB tool.
    render_as_batch=True is required for SQLite ALTER TABLE emulation.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations against a live DB connection ('online' mode — the default).

    render_as_batch=True is required for SQLite ALTER TABLE emulation.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
