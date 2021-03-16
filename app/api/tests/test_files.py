from fastapi.testclient import TestClient
import pytest

from api.main import app
from api.config import settings

client = TestClient(app)

def get_token():
    """ Returns a token. Most of the tests expect at least 5 calls quota to work """

    response = client.post("/auth", files={"user_id": (None, f"{settings.DEMO_USER_ID}"), "password":(None, f"{settings.DEMO_USER_PASSWORD}")})
    
    assert response.status_code == 200
    assert response.json()
    assert response.json().get("token")
    return response.json().get("token")

@pytest.fixture
def token():
    """ Returns a token. Most of the tests expect at least 5 calls quota to work """
    response = client.post("/auth", files={"user_id": (None, f"{settings.DEMO_USER_ID}"), "password":(None, f"{settings.DEMO_USER_PASSWORD}")})
    
    assert response.status_code == 200
    assert response.json()
    assert response.json().get("token")
    return response.json().get("token")

# Get files
def test_unauthorized_get_user_files():
    response = client.get("/me")
    
    assert response.status_code == 401
    assert response.json()

def test_authorized_get_user_files(token):
    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json() == {'files': [], 'user': settings.DEMO_USER_ID}

# Post files
def test_unauthorized_post_user_file():
    response = client.post("/me")
    
    assert response.status_code == 401
    assert response.json()

def test_authorized_post_user_file(token):
    # Non atomic test as it leaves a file for the user, this API doesn't have a delete method for files
    with open('./tests/house.jpg','rb') as file:
        files = {'file': ("house.jpg", file)}
        response = client.post("/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get("files")) == 1


def test_authorized_post_duplicated_user_file(token):
    """ This test checks that after uploading a file twice with the same name, the amount of files stays the same.
    That means that the file is overriten
    """

    # Non atomic test as it leaves a file for the user, this API doesn't have a delete method for files
    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    current_files = len(temporal_response.json().get("files"))

    with open('./tests/house.jpg','rb') as file:
        files = {'file': ("house1.jpg", file)}
        response = client.post("/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    with open('./tests/house.jpg','rb') as file:
        files = {'file': ("house1.jpg", file)}
        response = client.post("/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get("files")) == current_files + 1

def test_authorized_post_user_file_account_limit(token):
    """ This test checks that after uploading N+1 files, the amount of files stays at N.
    That means that the first file is overriten, following FIFO
    """

    # Non atomic test as it leaves a file for the user, this API doesn't have a delete method for files
    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    current_files = len(temporal_response.json().get("files"))

    # Upload missing files to reach the limit
    for i in range(settings.USER_MAX_FILES-current_files):
        token = get_token() # Get a new token on each request to ignore the quota limit
        with open('./tests/house.jpg','rb') as file:
            files = {'file': (f"house_multiple{i}.jpg", file)}
            response = client.post("/me", headers={"Authorization": f"Bearer {token}"}, files=files)
            assert response.status_code == 200
            assert response.json()
            assert response.json().get("url")

    # Check that the number of files is correct
    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get("files")) == settings.USER_MAX_FILES

    # Check that the number of files is correct, even after adding one extra file
    with open('./tests/house.jpg','rb') as file:
        files = {'file': ("house_final.jpg", file)}
        response = client.post("/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    temporal_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get("files")) == settings.USER_MAX_FILES

# Get file
def test_unauthorized_get_user_file():
    response = client.get("/f/test")
    
    assert response.status_code == 401
    assert response.json()

# Test download quota
# Test file integrity with checksum

# Share file
def test_unauthorized_get_user_file_share_link():
    response = client.get("/f/test/share")
    
    assert response.status_code == 401
    assert response.json()

# Get share file
def test_not_found_get_share_link_file():
    response = client.get("/s/test")
    
    assert response.status_code == 404
    assert response.json()
# Test non download quota