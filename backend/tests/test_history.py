import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.inference_job import InferenceJob


def _register_and_auth(client, email: str | None = None) -> dict[str, str]:
    user_email = email or f"history-{uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": user_email, "password": "Password1"},
    )
    payload = response.json()["data"]
    return {"Authorization": f"Bearer {payload['access_token']}"}


def _create_job(client, headers: dict[str, str], model_id: str = "rddc2020-imsc-last95") -> str:
    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": model_id},
        files={"image": ("road.jpg", b"fake-image-data", "image/jpeg")},
    )
    assert response.status_code == 202
    return response.json()["data"]["job_id"]


def test_history_requires_authentication(client):
    response = client.get("/history")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_TOKEN_INVALID"


def test_history_is_user_scoped_and_supports_pagination_and_model_filter(client, db_session):
    owner_headers = _register_and_auth(client, email=f"owner-history-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"other-history-{uuid4()}@example.com")

    owner_job_ids = [
        _create_job(client, owner_headers, model_id="rddc2020-imsc-last95"),
        _create_job(client, owner_headers, model_id="rddc2020-imsc-ensemble-test1"),
        _create_job(client, owner_headers, model_id="rddc2020-imsc-last95"),
    ]
    other_job_id = _create_job(client, other_headers, model_id="rddc2020-imsc-last95")

    now = datetime.now(UTC)
    for index, job_id in enumerate(owner_job_ids):
        job = db_session.query(InferenceJob).filter(InferenceJob.id == job_id).first()
        assert job is not None
        job.created_at = now + timedelta(seconds=index)
        db_session.add(job)

    other_job = db_session.query(InferenceJob).filter(InferenceJob.id == other_job_id).first()
    assert other_job is not None
    other_job.created_at = now + timedelta(minutes=5)
    db_session.add(other_job)
    db_session.commit()

    page_one = client.get("/history?page=1&page_size=2", headers=owner_headers)
    assert page_one.status_code == 200
    page_one_data = page_one.json()["data"]
    assert page_one_data["page"] == 1
    assert page_one_data["page_size"] == 2
    assert page_one_data["total"] == 3
    assert len(page_one_data["items"]) == 2

    page_two = client.get("/history?page=2&page_size=2", headers=owner_headers)
    assert page_two.status_code == 200
    page_two_data = page_two.json()["data"]
    assert page_two_data["page"] == 2
    assert page_two_data["page_size"] == 2
    assert page_two_data["total"] == 3
    assert len(page_two_data["items"]) == 1

    owner_returned_job_ids = {item["job_id"] for item in page_one_data["items"] + page_two_data["items"]}
    assert other_job_id not in owner_returned_job_ids
    assert owner_returned_job_ids == set(owner_job_ids)

    filtered = client.get("/history?model_id=rddc2020-imsc-last95", headers=owner_headers)
    assert filtered.status_code == 200
    filtered_data = filtered.json()["data"]
    assert filtered_data["total"] == 2
    assert all(item["model_id"] == "rddc2020-imsc-last95" for item in filtered_data["items"])


def test_history_computes_stats_and_handles_malformed_detection_json(client, db_session):
    headers = _register_and_auth(client, email=f"stats-history-{uuid4()}@example.com")

    good_job_id = _create_job(client, headers)
    legacy_job_id = _create_job(client, headers)
    malformed_job_id = _create_job(client, headers)

    good_job = db_session.query(InferenceJob).filter(InferenceJob.id == good_job_id).first()
    legacy_job = db_session.query(InferenceJob).filter(InferenceJob.id == legacy_job_id).first()
    malformed_job = db_session.query(InferenceJob).filter(InferenceJob.id == malformed_job_id).first()
    assert good_job is not None
    assert legacy_job is not None
    assert malformed_job is not None

    good_job.status = "succeeded"
    good_job.detections_json = json.dumps(
        [
            {"label": "D00", "confidence": 0.6, "bbox": {"x1": 1, "y1": 1, "x2": 2, "y2": 2}},
            {"label": "D10", "confidence": None, "bbox": {"x1": 3, "y1": 3, "x2": 4, "y2": 4}},
            {"label": "D20", "bbox": {"x1": 5, "y1": 5, "x2": 6, "y2": 6}},
        ]
    )

    legacy_job.status = "succeeded"
    legacy_job.detections_json = json.dumps(
        [
            {"label": "D40", "bbox": {"x1": 7, "y1": 7, "x2": 8, "y2": 8}},
        ]
    )

    malformed_job.status = "succeeded"
    malformed_job.detections_json = "{this-is-not-json"

    db_session.add(good_job)
    db_session.add(legacy_job)
    db_session.add(malformed_job)
    db_session.commit()

    response = client.get("/history", headers=headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    item_by_id = {item["job_id"]: item for item in items}

    good_item = item_by_id[good_job_id]
    assert good_item["defect_count"] == 3
    assert good_item["max_confidence"] == 0.6

    legacy_item = item_by_id[legacy_job_id]
    assert legacy_item["defect_count"] == 1
    assert "max_confidence" not in legacy_item

    malformed_item = item_by_id[malformed_job_id]
    assert "defect_count" not in malformed_item
    assert "max_confidence" not in malformed_item

def test_history_delete_endpoints_require_authentication(client):
    clear_response = client.delete("/history")
    assert clear_response.status_code == 401
    assert clear_response.json()["error"]["code"] == "AUTH_TOKEN_INVALID"

    delete_one_response = client.delete(f"/history/{uuid4()}")
    assert delete_one_response.status_code == 401
    assert delete_one_response.json()["error"]["code"] == "AUTH_TOKEN_INVALID"


def test_delete_history_item_is_owner_scoped_and_not_found_style(client, db_session):
    owner_headers = _register_and_auth(client, email=f"del-owner-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"del-other-{uuid4()}@example.com")

    owner_job_id = _create_job(client, owner_headers)
    other_job_id = _create_job(client, other_headers)

    non_owner_delete = client.delete(f"/history/{owner_job_id}", headers=other_headers)
    assert non_owner_delete.status_code == 404
    assert non_owner_delete.json()["error"]["code"] == "NOT_FOUND"

    missing_delete = client.delete(f"/history/{uuid4()}", headers=owner_headers)
    assert missing_delete.status_code == 404
    assert missing_delete.json()["error"]["code"] == "NOT_FOUND"

    owner_delete = client.delete(f"/history/{owner_job_id}", headers=owner_headers)
    assert owner_delete.status_code == 200
    owner_payload = owner_delete.json()["data"]
    assert owner_payload["job_id"] == owner_job_id
    assert owner_payload["message"] == "History item deleted."

    owner_job = db_session.query(InferenceJob).filter(InferenceJob.id == owner_job_id).first()
    other_job = db_session.query(InferenceJob).filter(InferenceJob.id == other_job_id).first()
    assert owner_job is None
    assert other_job is not None


def test_clear_history_only_removes_callers_jobs(client, db_session):
    owner_headers = _register_and_auth(client, email=f"clear-owner-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"clear-other-{uuid4()}@example.com")

    owner_job_ids = [_create_job(client, owner_headers), _create_job(client, owner_headers)]
    other_job_id = _create_job(client, other_headers)

    clear_response = client.delete("/history", headers=owner_headers)
    assert clear_response.status_code == 200
    payload = clear_response.json()["data"]
    assert payload["message"] == "History cleared."
    assert payload["deleted_count"] == 2

    for owner_job_id in owner_job_ids:
        owner_job = db_session.query(InferenceJob).filter(InferenceJob.id == owner_job_id).first()
        assert owner_job is None

    other_job = db_session.query(InferenceJob).filter(InferenceJob.id == other_job_id).first()
    assert other_job is not None

    owner_history = client.get("/history", headers=owner_headers)
    assert owner_history.status_code == 200
    assert owner_history.json()["data"]["total"] == 0

    other_history = client.get("/history", headers=other_headers)
    assert other_history.status_code == 200
    assert other_history.json()["data"]["total"] == 1

