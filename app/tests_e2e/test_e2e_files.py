import pytest
import shutil
import os
import requests
from api.config import settings
import hashlib


def get_token():
    """ Returns a token. Most of the tests expect at least 5 calls quota to work """

    response = requests.post("http://localhost/auth", files={"user_id": (
        None, f"{settings.DEMO_USER_ID}"), "password": (None, f"{settings.DEMO_USER_PASSWORD}")})

    assert response.status_code == 200
    assert response.json()
    assert response.json().get("token")
    return response.json().get("token")


@pytest.fixture
def token():
    """ Returns a token. Most of the tests expect at least 5 calls quota to work """
    response = requests.post("http://localhost/auth", files={"user_id": (
        None, f"{settings.DEMO_USER_ID}"), "password": (None, f"{settings.DEMO_USER_PASSWORD}")})

    assert response.status_code == 200
    assert response.json()
    assert response.json().get("token")
    return response.json().get("token")

# Get files


def test_unauthorized_get_user_files():
    response = requests.get("http://localhost/me")

    assert response.status_code == 401
    assert response.json()


def test_authorized_get_user_files(token):
    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json() == {
        'files': [], 'user': settings.DEMO_USER_ID}

# Post files


def test_unauthorized_post_user_file():
    response = requests.post("http://localhost/me")

    assert response.status_code == 401
    assert response.json()


def test_authorized_post_user_file(token):
    # Non atomic test as it leaves a file for the user, this API doesn't have a delete method for files
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get("files")) == 1


def test_authorized_post_duplicated_user_file(token):
    """ This test checks that after uploading a file twice with the same name, the amount of files stays the same.
    That means that the file is overriten
    """

    # Non atomic test as it leaves a file for the user, this API doesn't have a delete method for files
    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    current_files = len(temporal_response.json().get("files"))

    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house1.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house1.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get("files")) == current_files + 1


def test_authorized_post_user_file_account_limit(token):
    """ This test checks that after uploading N+1 files, the amount of files stays at N.
    That means that the first file is overriten, following FIFO
    """

    # Non atomic test as it leaves a file for the user, this API doesn't have a delete method for files
    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    current_files = len(temporal_response.json().get("files"))

    # Upload missing files to reach the limit
    for i in range(settings.USER_MAX_FILES-current_files):
        token = get_token()  # Get a new token on each request to ignore the quota limit
        with open('./tests_e2e/house.jpg', 'rb') as file:
            files = {'file': (f"house_multiple{i}.jpg", file)}
            response = requests.post(
                "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
            assert response.status_code == 200
            assert response.json()
            assert response.json().get("url")

    # Check that the number of files is correct
    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get(
        "files")) == settings.USER_MAX_FILES

    # Check that the number of files is correct, even after adding one extra file
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house_final.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")

    temporal_response = requests.get(
        "http://localhost/me", headers={"Authorization": f"Bearer {token}"})
    assert temporal_response.status_code == 200
    assert temporal_response.json()
    assert len(temporal_response.json().get(
        "files")) == settings.USER_MAX_FILES

# Get file
# As the API doesn't have any kind of support for information of user quotas, we need to calculate them manually


class db:
    downloaded_bytes = 0


def test_unauthorized_get_user_file():
    response = requests.get("http://localhost/f/test")

    assert response.status_code == 401
    assert response.json()


def test_authorized_get_user_file(token):
    # Upload a file and download it again
    file_id = None
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("new_house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

    with requests.get(f"http://localhost/f/{file_id}", headers={"Authorization": f"Bearer {token}"}, stream=True) as response:
        assert response.status_code == 200
        db.downloaded_bytes += sum(len(chunk)
                                   for chunk in response.iter_content(8196))
        with open('./tests_e2e/new_house.jpg', 'wb') as file:
            shutil.copyfileobj(response.raw, file)

    assert os.path.isfile("./tests_e2e/new_house.jpg")


def test_authorized_get_user_file_checksum(token):
    # Upload a file and download it again
    file_id = None
    sent_file_checksum = None
    response_file_checksum = None

    with open('./tests_e2e/house.jpg', 'rb') as file:
        sent_file = file.read()  # pylint: disable=unused-variable # This first read is necessary to get a valid checksum

        files = {'file': ("new_house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)

        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

        sent_file_checksum = hashlib.md5(file.read()).hexdigest()
        assert sent_file_checksum

    with requests.get(f"http://localhost/f/{file_id}", headers={"Authorization": f"Bearer {token}"}, stream=True) as response:
        assert response.status_code == 200
        db.downloaded_bytes += sum(len(chunk)
                                   for chunk in response.iter_content(8196))
        with open('./tests_e2e/new_house.jpg', 'wb+') as file:
            shutil.copyfileobj(response.raw, file)

    with open('./tests_e2e/new_house.jpg', 'rb') as file:
        response_file_checksum = hashlib.md5(file.read()).hexdigest()
        assert response_file_checksum

    assert os.path.isfile("./tests_e2e/new_house.jpg")

    # Check that checksums are the same
    assert sent_file_checksum == response_file_checksum


def test_authorized_get_user_file_quota_limit(token):
    # Upload a file and download it multiple times until reaching the quota limit

    file_id = None
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

    total_downloaded_bytes = db.downloaded_bytes
    while not total_downloaded_bytes >= settings.DOWNLOAD_QUOTA_TRAFFIC:
        token = get_token()  # Get a new token on each request to ignore the quota limit
        response = requests.get(
            f"http://localhost/f/{file_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        total_downloaded_bytes += len(response.content)
    db.downloaded_bytes = total_downloaded_bytes

    # As the total_downloaded_bytes is >= than the settings.DOWNLOAD_QUOTA_TRAFFIC, the next request will fail
    response = requests.get(
        f"http://localhost/f/{file_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 429


# TODO: test settings.DOWNLOAD_QUOTA_MINUTES

# Generate share file
def test_unauthorized_generate_user_file_share_link():
    response = requests.get("http://localhost/f/test/share")

    assert response.status_code == 401
    assert response.json()


def test_authorized_generate_user_file_share_link(token):
    # Upload a file and generate a share link

    file_id = None
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

    response = requests.get(f"http://localhost/f/{file_id}/share",
                            headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json().get("share_url")

# Download share file


def test_not_found_get_share_link_file():
    response = requests.get("http://localhost/s/test")

    assert response.status_code == 404
    assert response.json()


def test_download_share_link_file_authenticated(token):
    # Upload a file, generate a share link and download it with token

    file_id = None
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

    response = requests.get(f"http://localhost/f/{file_id}/share",
                            headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json().get("share_url")
    share_url = response.json().get("share_url")

    # This test also checks that the user is able to download shared files even without quota
    response = requests.get(f"http://localhost{share_url}", headers={
        "Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_download_share_link_file_not_authenticated(token):
    # Upload a file, generate a share link and download it without token

    file_id = None
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

    response = requests.get(f"http://localhost/f/{file_id}/share",
                            headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json().get("share_url")
    share_url = response.json().get("share_url")

    response = requests.get(f"http://localhost{share_url}")
    assert response.status_code == 200


def test_download_share_link_file_not_authenticated_multiple(token):
    # Upload a file, generate a share link and download it without token two times

    file_id = None
    with open('./tests_e2e/house.jpg', 'rb') as file:
        files = {'file': ("house.jpg", file)}
        response = requests.post(
            "http://localhost/me", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 200
        assert response.json()
        assert response.json().get("url")
        # Based on current API response, /f/<file_id>
        file_id = response.json().get("url").split('/')[2]
        assert file_id

    response = requests.get(f"http://localhost/f/{file_id}/share",
                            headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json().get("share_url")
    share_url = response.json().get("share_url")

    response = requests.get(f"http://localhost{share_url}")
    assert response.status_code == 200

    # The second time it MUST fail
    response = requests.get(f"http://localhost{share_url}")
    assert response.status_code == 404
