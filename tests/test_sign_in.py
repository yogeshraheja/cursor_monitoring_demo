import json

import pytest

from app import create_app
from app.auth import SIGN_IN_FAILED
from tests.fake_transport import FakeTransport
from tests.helpers import post_form, sign_in


def test_sign_in_success_starts_session(client):
    response = sign_in(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session_data:
        assert session_data["user"] == "admin"
    page = client.get("/")
    assert page.status_code == 200


@pytest.mark.parametrize(
    "username,password",
    [
        ("admin", "wrong-password"),
        ("someone-else", "test-password"),
    ],
)
def test_sign_in_failure_stays_on_page(client, username, password):
    response = sign_in(client, username=username, password=password)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert SIGN_IN_FAILED in body
    assert "wrong password" not in body.lower()
    assert "unknown user" not in body.lower()
    with client.session_transaction() as session_data:
        assert session_data.get("user") != "admin"


def test_missing_config_hash(tmp_path, data_dir, transport, clock):
    config_path = tmp_path / "missing.json"
    config_path.write_text("{}", encoding="utf-8")
    application = create_app(
        config_path=config_path,
        data_dir=data_dir,
        transport=transport,
        sample_gap=0,
        clock=clock,
    )
    local_client = application.test_client()
    response = sign_in(local_client)
    assert response.status_code == 200
    assert SIGN_IN_FAILED in response.get_data(as_text=True)


def test_missing_config_file(tmp_path, data_dir, transport, clock):
    application = create_app(
        config_path=tmp_path / "absent.json",
        data_dir=data_dir,
        transport=FakeTransport(),
        sample_gap=0,
        clock=clock,
    )
    local_client = application.test_client()
    response = sign_in(local_client)
    assert response.status_code == 200
    assert SIGN_IN_FAILED in response.get_data(as_text=True)


def test_session_cookie_is_http_only_and_same_site(client):
    response = client.get("/sign-in")
    cookie = " ".join(response.headers.getlist("Set-Cookie"))
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_sign_in_and_sign_out_require_csrf(client, signed_in):
    rejected = client.post("/sign-in", data={"username": "admin", "password": "test-password"})
    assert rejected.status_code == 400
    rejected_out = signed_in.post("/sign-out", data={})
    assert rejected_out.status_code == 400


def test_example_config_has_hash_only():
    data = json.loads(open("config.example.json", encoding="utf-8").read())
    assert "password" not in data
    assert data["admin_password_hash"].startswith("scrypt:")
