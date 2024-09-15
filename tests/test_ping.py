from conftest import client


def test_ping():
    response = client.get("/api/v1/ping")
    assert response.json() == {"success": True}


def test_index():
    response = client.get("/api/v1/")
    assert response.json() == {"index": True}
