# Backend Scaffold

Planned backend stack for implementation:

- FastAPI
- SQLAlchemy + Alembic
- Pydantic schemas
- JWT auth and bcrypt password hashing
- Ultralytics YOLO inference service

Expected source shape during implementation:

- `app/main.py` app factory and router inclusion
- `app/api/` endpoint modules
- `app/services/` auth, inference, model registry, storage
- `app/repositories/` persistence logic
- `app/models/` ORM entities
- `app/schemas/` request/response schemas
- `tests/` unit and integration tests

This directory is intentionally scaffold-only at this stage.