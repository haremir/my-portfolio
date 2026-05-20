"""
models.py — SQLModel table definitions for harun_site.

Design notes
------------
* rx.Model was deprecated in Reflex 0.9.2 and is removed in 1.0.0.
  These models extend sqlmodel.SQLModel directly so the deprecation
  warning is gone and we own the full engine/session lifecycle.

* ensure_tables() must be called once at startup (harun_site.py does
  this after rx.App() is created).  It uses CREATE TABLE IF NOT EXISTS
  semantics — safe to re-run on every startup; data is never touched.

* get_engine() returns a module-level cached SQLAlchemy engine so that
  every state method that calls Session(get_engine()) reuses the same
  connection pool rather than spawning a new one every time.
"""

from __future__ import annotations

import sys
from typing import Optional

from sqlalchemy import create_engine as _sa_create_engine
from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

class EducationModel(SQLModel, table=True):
    """Education entry persisted in SQLite (reflex.db → educationmodel)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    okul_adi: str = Field(default="")
    bolum: str = Field(default="")
    baslangic_yili: str = Field(default="")
    mezuniyet_yili: str = Field(default="")
    detay: str = Field(default="")


class ExperienceModel(SQLModel, table=True):
    """Work-experience entry persisted in SQLite (reflex.db → experiencemodel)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    sirket_adi: str = Field(default="")
    pozisyon: str = Field(default="")
    sure: str = Field(default="")
    aciklama: str = Field(default="")


# ---------------------------------------------------------------------------
# Engine helpers
# ---------------------------------------------------------------------------

_engine = None  # module-level singleton — created once by get_engine()


def _db_url() -> str:
    """Read db_url from rxconfig with a hard fallback to sqlite:///reflex.db."""
    try:
        from rxconfig import config  # type: ignore[import]
        return str(config.db_url)
    except Exception:
        return "sqlite:///reflex.db"


def get_engine():
    """
    Return the module-level cached SQLAlchemy engine.

    Creates the engine on first call using the URL from rxconfig.
    Subsequent calls return the same object (connection-pool reuse).
    Safe to call from any thread because check_same_thread=False is
    set for SQLite connections.
    """
    global _engine
    if _engine is None:
        url = _db_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = _sa_create_engine(url, connect_args=connect_args)
    return _engine


# ---------------------------------------------------------------------------
# Startup helper
# ---------------------------------------------------------------------------

def ensure_tables() -> None:
    """
    Create every SQLModel table that does not yet exist.

    Behaviour
    ---------
    * Uses SQLAlchemy's CREATE TABLE IF NOT EXISTS — completely idempotent.
    * Existing tables and all stored data are left untouched.
    * Uses our own engine (not rx.Model / rx.session) because rx.Model is
      deprecated in Reflex 0.9.2.

    When to call
    ------------
    Call ONCE in harun_site.py after rx.App() is constructed so that
    Reflex's own configuration is fully loaded before we build the engine.

    For schema changes (column additions, renames) prefer Alembic:
        alembic revision --autogenerate -m "describe change"
        alembic upgrade head
    """
    try:
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        print(
            "[DB] ensure_tables: OK — educationmodel + experiencemodel verified.",
            file=sys.stderr,
        )
    except Exception as exc:
        print(
            f"[DB] ensure_tables FAILED — {type(exc).__name__}: {exc}\n"
            "  Tables will be missing at runtime.  Fix options:\n"
            "    1. Run:  alembic upgrade head\n"
            "    2. Or check db_url in rxconfig.py",
            file=sys.stderr,
        )
