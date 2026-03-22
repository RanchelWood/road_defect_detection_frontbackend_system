import json
from uuid import uuid4

from app.models.inference_job import InferenceJob


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


def test_models_returns_rddc2020_presets(client):
    headers = _register_and_auth(client)

    response = client.get("/models", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    items = payload["data"]["items"]
    assert len(items) == 3
    assert any(item["model_id"] == "rddc2020-imsc-last95" for item in items)
    assert all(item["engine_id"] == "rddc2020-cli" for item in items)
    assert all("status" in item for item in items)
    assert all("performance_notes" in item for item in items)


def test_create_inference_job_returns_queued_job(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-ensemble-test1"},
        files={"image": ("road.jpg", b"fake-image-data", "image/jpeg")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["engine_id"] == "rddc2020-cli"


def test_create_inference_job_validates_model_id(client):
    headers = _register_and_auth(client)

    response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "unknown-model"},
        files={"image": ("road.jpg", b"fake-image-data", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MODEL"


def test_user_can_fetch_own_job_only(client):
    owner_headers = _register_and_auth(client, email=f"owner-{uuid4()}@example.com")
    other_headers = _register_and_auth(client, email=f"other-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=owner_headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", b"fake-image-data", "image/png")},
    )
    job_id = create_response.json()["data"]["job_id"]

    owner_response = client.get(f"/inference/jobs/{job_id}", headers=owner_headers)
    assert owner_response.status_code == 200
    assert owner_response.json()["data"]["job_id"] == job_id
    assert owner_response.json()["data"]["result"] is None

    other_response = client.get(f"/inference/jobs/{job_id}", headers=other_headers)
    assert other_response.status_code == 404
    assert other_response.json()["error"]["code"] == "NOT_FOUND"


def test_job_detail_result_payload_matches_contract_shape(client, db_session):
    headers = _register_and_auth(client, email=f"contract-{uuid4()}@example.com")

    create_response = client.post(
        "/inference/jobs",
        headers=headers,
        data={"model_id": "rddc2020-imsc-last95"},
        files={"image": ("road.png", b"fake-image-data", "image/png")},
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
