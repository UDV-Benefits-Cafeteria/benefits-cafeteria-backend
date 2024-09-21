# tests/test_ping.py


def test_ping(client):
    response = client.get("/api/v1/ping")
    assert response.json() == {"success": True}


def test_index(client):
    response = client.get("/api/v1/")
    assert response.json() == {"index": True}
