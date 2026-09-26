import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

# Determine project base directory and load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_DB_PATH = BASE_DIR / "disaster_response.db"
raw_db_url = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# Standardize SQLite URL to project root absolute path if it is relative
if raw_db_url.startswith("sqlite:///") and not raw_db_url.startswith("sqlite:////"):
    rel_part = raw_db_url[len("sqlite:///"):]
    # If path starts with Windows drive like C:, keep it as-is
    if len(rel_part) > 1 and rel_part[1] == ":":
        DATABASE_URL = f"sqlite:///{rel_part}"
    else:
        abs_path = (BASE_DIR / rel_part).resolve().as_posix()
        DATABASE_URL = f"sqlite:///{abs_path}"
else:
    DATABASE_URL = raw_db_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@contextmanager
def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
