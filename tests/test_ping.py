from conftest import client


def test_ping():
    response = client.get("/ping")
    assert response.json() == {"success": True}
