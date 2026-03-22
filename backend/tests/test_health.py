def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert "meta" in payload
    assert "request_id" in payload["meta"]