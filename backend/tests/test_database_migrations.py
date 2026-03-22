from sqlalchemy import create_engine

from app.core.database import run_schema_migrations


def test_run_schema_migrations_adds_milestone_2b_columns_and_backfills(tmp_path):
    db_path = tmp_path / "legacy.db"
    legacy_engine = create_engine(f"sqlite:///{db_path.as_posix()}")

    with legacy_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE inference_jobs (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                engine_id TEXT,
                model_id TEXT,
                status TEXT,
                input_path TEXT,
                original_filename TEXT,
                created_at TIMESTAMP
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO inference_jobs (
                id, user_id, engine_id, model_id, status, input_path, original_filename, created_at
            ) VALUES (
                'job-1', 1, 'rddc2020-cli', 'rddc2020-imsc-last95', NULL, '/tmp/input.jpg', 'input.jpg', NULL
            )
            """
        )

    run_schema_migrations(legacy_engine)
    run_schema_migrations(legacy_engine)

    with legacy_engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(inference_jobs)").fetchall()
        }
        assert "output_path" in columns
        assert "detections_json" in columns
        assert "duration_ms" in columns
        assert "error_code" in columns
        assert "error_message" in columns
        assert "started_at" in columns
        assert "finished_at" in columns

        row = connection.exec_driver_sql(
            """
            SELECT
                status,
                created_at,
                output_path,
                detections_json,
                duration_ms,
                error_code,
                error_message,
                started_at,
                finished_at
            FROM inference_jobs
            WHERE id='job-1'
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "queued"
    assert row[1] is not None
    assert row[2] is None
    assert row[3] is None
    assert row[4] is None
    assert row[5] is None
    assert row[6] is None
    assert row[7] is None
    assert row[8] is None

