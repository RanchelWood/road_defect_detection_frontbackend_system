from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

if settings.database_url.startswith("sqlite:///"):
    sqlite_file = Path(settings.database_url.replace("sqlite:///", "", 1))
    sqlite_file.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_schema_migrations(target_engine: Engine) -> None:
    if target_engine.dialect.name != "sqlite":
        return

    with target_engine.begin() as connection:
        table_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='inference_jobs'"
        ).fetchone()
        if table_exists is None:
            return

        rows = connection.exec_driver_sql("PRAGMA table_info(inference_jobs)").fetchall()
        existing_columns = {row[1] for row in rows}

        missing_columns = {
            "output_path": "TEXT",
            "detections_json": "TEXT",
            "duration_ms": "INTEGER",
            "error_code": "TEXT",
            "error_message": "TEXT",
            "started_at": "TIMESTAMP",
            "finished_at": "TIMESTAMP",
        }

        for column_name, sql_type in missing_columns.items():
            if column_name not in existing_columns:
                connection.exec_driver_sql(f"ALTER TABLE inference_jobs ADD COLUMN {column_name} {sql_type}")

        if "status" in existing_columns:
            connection.exec_driver_sql(
                "UPDATE inference_jobs SET status='queued' WHERE status IS NULL OR TRIM(status)=''"
            )

        if "created_at" in existing_columns:
            connection.exec_driver_sql(
                "UPDATE inference_jobs SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL"
            )


def init_db() -> None:
    from app.models.base import Base
    from app.models.inference_job import InferenceJob
    from app.models.refresh_token import RefreshToken
    from app.models.user import User

    _ = (User, RefreshToken, InferenceJob)
    Base.metadata.create_all(bind=engine)
    run_schema_migrations(engine)
