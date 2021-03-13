from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

def test_unauthorized_get_user_files():
    response = client.get("/me")
    
    assert response.status_code == 401
    assert response.json()


def test_unauthorized_post_user_file():
    response = client.post("/me")
    
    assert response.status_code == 401
    assert response.json()


def test_unauthorized_get_user_file():
    response = client.get("/f/test")
    
    assert response.status_code == 401
    assert response.json()

def test_unauthorized_get_user_file_share_link():
    response = client.get("/f/test/share")
    
    assert response.status_code == 401
    assert response.json()

def test_not_found_get_share_link_file():
    response = client.get("/s/test")
    
    assert response.status_code == 404
    assert response.json()
