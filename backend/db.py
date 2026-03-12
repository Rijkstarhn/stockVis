from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLITE_URL = "sqlite:///./stockvis.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    # Import models before create_all so SQLAlchemy sees table metadata.
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
