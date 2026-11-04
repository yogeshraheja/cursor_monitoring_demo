import json

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from tests.constants import PASSWORD
from tests.fake_transport import FakeTransport
from tests.helpers import sign_in

PASSWORD_HASH = generate_password_hash(PASSWORD)


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value


@pytest.fixture
def transport():
    return FakeTransport()


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def data_dir(tmp_path):
    path = tmp_path / "data"
    path.mkdir()
    return path


@pytest.fixture
def app(tmp_path, data_dir, transport, clock):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"admin_password_hash": PASSWORD_HASH}), encoding="utf-8")
    application = create_app(
        config_path=config_path,
        data_dir=data_dir,
        transport=transport,
        sample_gap=0,
        clock=clock,
    )
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def signed_in(client):
    response = sign_in(client)
    assert response.status_code == 302
    return client
