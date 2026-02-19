# smart_irrigation_system/server/db/session.py

from sqlmodel import create_engine, Session
from pathlib import Path
import os

# -----------------------------------------------------------------------------
# Database location
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "runtime" / "server" / "data" / "sis.db"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH}" # fallback to a local SQLite database if DATABASE_URL is not set (e.g., no Docker environment variable provided)
)

# -----------------------------------------------------------------------------
# Engine
# -----------------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

# -----------------------------------------------------------------------------
# Dependency
# -----------------------------------------------------------------------------

def get_session():
    with Session(engine) as session:
        yield session
