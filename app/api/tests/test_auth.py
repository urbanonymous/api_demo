from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_valid_auth():
    response = client.post("/auth", files={"user_id": (None, "username"), "password":(None, "password")})
    
    assert response.status_code == 200
    assert response.json()
    assert response.json().get("token")

def test_invalid_auth():
    response = client.post("/auth", files={"user_id": (None, "username1"), "password":(None, "password")})
    
    assert response.status_code == 400
    assert response.json()
    assert response.json().get("token") == None
