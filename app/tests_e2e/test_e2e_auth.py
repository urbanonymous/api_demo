from app.api.config import settings

def test_get_access_token():
    r = client.post(f"http://localhost:8000/auth")

    assert r.json()
    assert r.status_code == 200
