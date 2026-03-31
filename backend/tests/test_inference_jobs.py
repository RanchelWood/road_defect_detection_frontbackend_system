import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.inference_job import InferenceJob

VALID_IMAGE_BYTES = bytes.fromhex(
    "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE0000000A49444154789C6360000000020001E527D4A20000000049454E44AE426082"
)


def _register_and_auth(client, email: str | None = None) -> dict[str, str]:
    user_email = email or f"user-{uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": user_email, "password": "Password1"},
    )
    payload = response.json()["data"]
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_models_requires_authentication(client):
    response = client.get("/models")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_TOKEN_INVALID"


def test_models_returns_rddc2020_orddc2024_and_shiyu_presets(client):
    headers = _register_and_auth(client)

    response = client.get("/models", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    items = payload["data"]["items"]

    model_ids = {item["model_id"] for item in items}
    assert "rddc2020-imsc-last95" in model_ids
    assert "orddc2024-phase1-ensemble" in model_ids
    assert "orddc2024-phase2-ensemble" in model_ids
    assert "shiyu-cpu-ensemble-default" in model_ids
    assert "shiyu-yolov7x-640" in model_ids
    assert "shiyu-y7x640-faster-swin-w7" in model_ids

    engine_ids = {item["engine_id"] for item in items}
    assert "rddc2020-cli" in engine_ids
    assert "orddc2024-cli" in engine_ids
    assert "shiyu-grddc2022-cli" in engine_ids

    assert all("status" in item for item in items)
    assert all("performance_notes" in item for item in items)


def test_create_inference_job_returns_queued_job(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-ensemble-test1"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["engine_id"] == "rddc2020-cli"

def test_create_inference_job_returns_queued_job_for_orddc2024_model(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "orddc2024-phase1-ensemble"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["engine_id"] == "orddc2024-cli"




def test_create_inference_job_returns_queued_job_for_shiyu_model(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "shiyu-yolov7x-640"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["engine_id"] == "shiyu-grddc2022-cli"

def test_create_inference_job_rejects_invalid_image_content(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.jpg", b"this-is-not-an-image", "image/jpeg")},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "INVALID_IMAGE_CONTENT"
    assert payload["error"]["details"]["field"] == "image"

def test_create_inference_job_validates_model_id(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "unknown-model"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MODEL"


def test_owner_can_cancel_queued_job(client, db_session):
    headers = _register_and_auth(client, email=f"cancel-owner-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    cancel_response = client.post(f"/inference/jobs/{job_id}/cancel", headers=headers)

    assert cancel_response.status_code == 200
    cancel_payload = cancel_response.json()["data"]
    assert cancel_payload["job_id"] == job_id
    assert cancel_payload["status"] == "cancelled"

    job = db_session.query(InferenceJob).filter(InferenceJob.id == job_id).first()
    assert job is not None
    assert job.status == "cancelled"
    assert job.error_code == "JOB_CANCELLED"


def test_non_owner_cannot_cancel_job(client):
    owner_headers = _register_and_auth(client, email=f"cancel-owner-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"cancel-other-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=owner_headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    cancel_response = client.post(f"/inference/jobs/{job_id}/cancel", headers=other_headers)

    assert cancel_response.status_code == 404
    assert cancel_response.json()["error"]["code"] == "NOT_FOUND"


def test_cancel_running_job_requests_cancellation(client, db_session):
    headers = _register_and_auth(client, email=f"cancel-running-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    job = db_session.query(InferenceJob).filter(InferenceJob.id == job_id).first()
    assert job is not None
    job.status = "running"
    job.started_at = datetime.now(UTC)
    db_session.add(job)
    db_session.commit()

    cancel_response = client.post(f"/inference/jobs/{job_id}/cancel", headers=headers)

    assert cancel_response.status_code == 200
    payload = cancel_response.json()["data"]
    assert payload["status"] == "running"
    assert payload["message"] == "Cancellation requested."

    db_session.expire_all()
    refreshed = db_session.query(InferenceJob).filter(InferenceJob.id == job_id).first()
    assert refreshed is not None
    assert refreshed.status == "running"
    assert refreshed.error_code == "CANCEL_REQUESTED"


def test_user_can_fetch_own_job_only(client):
    owner_headers = _register_and_auth(client, email=f"owner-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"other-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=owner_headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    owner_response = client.get(f"/inference/jobs/{job_id}", headers=owner_headers)
    assert owner_response.status_code == 200
    assert owner_response.json()["data"]["job_id"] == job_id
    assert owner_response.json()["data"]["result"] is None

    other_response = client.get(f"/inference/jobs/{job_id}", headers=other_headers)
    assert other_response.status_code == 404
    assert other_response.json()["error"]["code"] == "NOT_FOUND"


def test_job_detail_timestamps_include_utc_timezone_suffix(client):
    headers = _register_and_auth(client, email=f"tz-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    response = client.get(f"/inference/jobs/{job_id}", headers=headers)
    assert response.status_code == 200

    payload = response.json()["data"]
    assert isinstance(payload["created_at"], str)
    assert payload["created_at"].endswith("Z")

    for key in ("started_at", "finished_at"):
        value = payload[key]
        if value is not None:
            assert value.endswith("Z")


def test_job_detail_result_payload_matches_contract_shape(client, db_session):
    headers = _register_and_auth(client, email=f"contract-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    job = db_session.query(InferenceJob).filter(InferenceJob.id == job_id).first()
    assert job is not None

    job.status = "succeeded"
    job.output_path = "D:/tmp/annotated.png"
    job.duration_ms = 88
    job.detections_json = json.dumps(
        [
            {
                "label": "D00",
                "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
            }
        ]
    )
    db_session.add(job)
    db_session.commit()

    response = client.get(f"/inference/jobs/{job_id}", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    result = payload["result"]
    assert result is not None
    assert result["model_id"] == "rddc2020-imsc-last95"
    assert result["engine_id"] == "rddc2020-cli"
    assert result["duration_ms"] == 88

    detection = result["detections"][0]
    assert detection["label"] == "D00"
    assert "confidence" in detection
    assert detection["confidence"] is None
    assert detection["bbox"] == {"x1": 1.0, "y1": 2.0, "x2": 3.0, "y2": 4.0}

    image_refs = result["image_refs"]
    assert any(item["kind"] == "original" for item in image_refs)
    assert any(item["kind"] == "annotated" for item in image_refs)


def test_owner_can_fetch_original_and_annotated_images_when_available(client, db_session):
    headers = _register_and_auth(client, email=f"img-owner-{uuid4()}@example.com")

    original_bytes = VALID_IMAGE_BYTES
    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", original_bytes, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    job = db_session.query(InferenceJob).filter(InferenceJob.id == job_id).first()
    assert job is not None

    annotated_path = Path(job.input_path).with_name("annotated.png")
    annotated_bytes = b"annotated-image-bytes"
    annotated_path.write_bytes(annotated_bytes)

    job.status = "succeeded"
    job.output_path = str(annotated_path)
    db_session.add(job)
    db_session.commit()

    original_response = client.get(f"/inference/jobs/{job_id}/image/original", headers=headers)
    assert original_response.status_code == 200
    assert original_response.content == original_bytes

    annotated_response = client.get(f"/inference/jobs/{job_id}/image/annotated", headers=headers)
    assert annotated_response.status_code == 200
    assert annotated_response.content == annotated_bytes


def test_non_owner_is_denied_job_image_access(client):
    owner_headers = _register_and_auth(client, email=f"img-owner-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"img-other-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=owner_headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    response = client.get(f"/inference/jobs/{job_id}/image/original", headers=other_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_missing_annotated_image_returns_clean_not_found(client):
    headers = _register_and_auth(client, email=f"img-missing-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    response = client.get(f"/inference/jobs/{job_id}/image/annotated", headers=headers)

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "IMAGE_NOT_FOUND"
    assert "annotated" in payload["error"]["message"].lower()


def test_unsupported_image_kind_returns_clear_error(client):
    headers = _register_and_auth(client, email=f"img-kind-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", VALID_IMAGE_BYTES, "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    response = client.get(f"/inference/jobs/{job_id}/image/preview", headers=headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMAGE_KIND"

