"""
storage.py
--------------
Standalone script that reads all data/embedded/*.json files and stores
(upserts) them into PostgreSQL.

Intended to run on any machine that has:
  - access to the data/embedded/ directory
  - network access to the PostgreSQL instance
  - DATABASE_URL set in .env (or the environment)

Usage:
    python data_processing/storage/storage.py
    python data_processing/storage/storage.py --dir /path/to/embedded
    python data_processing/storage/storage.py --dir /path/to/embedded --create-tables
"""

import argparse
import os
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
# ==================== Load configurations ====================
MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(REPO_ROOT / "data_processing" / ".env")
with open(MODULE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)
# ==================== Configure ====================
DATA_ROOT_DIR = REPO_ROOT / "data"
DATA_EMBEDDED_DIR = DATA_ROOT_DIR / "embedded"  # output: data/embedded/<year>/<issue>/<doc>.json

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# ---------------------------------------------------------------------------
# DB setup  (mirrors api/database.py but fully self-contained)
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

from api.services.importer import import_all
# ---------------------------------------------------------------------------
# Optional table creation (CREATE TABLE IF NOT EXISTS via SQLAlchemy metadata)
# ---------------------------------------------------------------------------

def _get_current_embedding_dim() -> int:
    """Read the configured embedding dimension from data_processing/config.yaml."""
    return int(_cfg["selected_model"]["embedding"]["embedding_dim"])


def _drop_embeddings_table_if_dim_mismatch() -> None:
    """Drop document_embeddings if the stored vector dimension doesn't match config."""
    from sqlalchemy import text, inspect
    expected_dim = _get_current_embedding_dim()

    insp = inspect(engine)
    if "document_embeddings" not in insp.get_table_names():
        return  # table doesn't exist yet, nothing to do

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT atttypmod FROM pg_attribute "
            "JOIN pg_class ON pg_class.oid = pg_attribute.attrelid "
            "WHERE pg_class.relname = 'document_embeddings' "
            "AND pg_attribute.attname = 'embedding'"
        )).fetchone()

    if row is None:
        return

    stored_dim = row[0]  # pgvector stores dimension in atttypmod
    if stored_dim != expected_dim:
        print(f"  ⚠ Embedding dimension mismatch: DB has {stored_dim}, config expects {expected_dim}.")
        print("  Dropping document_embeddings table to recreate with correct dimension …")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS document_embeddings CASCADE"))
            conn.commit()
        print("  ✓ Dropped document_embeddings")


def _create_tables() -> None:
    # Import all models so their metadata is registered on Base
    from api.database import Base
    import api.models.db  # noqa: F401 – registers all ORM classes

    # pgvector extension must exist before vector columns can be created
    with engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    _drop_embeddings_table_if_dim_mismatch()

    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables created (or already exist)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import data/embedded JSON files into PostgreSQL."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Override the embedded data directory (default: <repo>/data/embedded)",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Run CREATE TABLE IF NOT EXISTS before importing (requires pgvector extension).",
    )
    args = parser.parse_args()

    if not DATA_EMBEDDED_DIR.exists():
        print(f"ERROR: directory not found: {DATA_EMBEDDED_DIR}")
        sys.exit(1)

    print(f"Database : {DATABASE_URL.split('@')[-1]}")   # hide credentials
    print(f"Source   : {DATA_EMBEDDED_DIR}")
    print()

    if args.create_tables:
        print("Creating tables …")
        _create_tables()
        print()

    db = SessionLocal()
    try:
        print("Importing …")
        result = import_all(db, embedded_dir=DATA_EMBEDDED_DIR)
    finally:
        db.close()

    print(f"\n  ✓ Processed : {result.processed}")
    if result.errors:
        print(f"  ✗ Errors    : {len(result.errors)}")
        for err in result.errors:
            print(f"      {err}")
        sys.exit(1)
    else:
        print("  Done – no errors.")


if __name__ == "__main__":
    main()
