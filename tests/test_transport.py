import pytest

from app.commands import ALLOWED_COMMANDS
from app.inventory import Server
from app.transport import (
    ParamikoTransport,
    SSH_TIMEOUT_SECONDS,
    TransportFailure,
    classify_exception,
    connect_kwargs,
    open_paramiko,
)


def _server():
    return Server(
        id="abc123abc123abc123abc123abc123ab",
        display_name="Edge",
        host="203.0.113.20",
        ssh_port=22,
        ssh_user="monitor",
        password="unique-secret-password",
        key_path="",
    )


class _Channel:
    def __init__(self, status):
        self._status = status
        self.calls = []

    def recv_exit_status(self):
        return self._status

    def request_x11(self):
        self.calls.append("request_x11")

    def request_agent(self):
        self.calls.append("request_agent")


class _Buffer:
    def __init__(self, payload, channel):
        self._payload = payload
        self.channel = channel

    def read(self):
        return self._payload


class _Client:
    def __init__(self, status=0, stderr=b"private key /home/demo/.ssh/id_rsa"):
        self.calls = []
        self.channel = _Channel(status)
        self.stderr_payload = stderr

    def set_missing_host_key_policy(self, _policy):
        self.calls.append("policy")

    def load_system_host_keys(self):
        self.calls.append("host_keys")

    def connect(self, **_kwargs):
        self.calls.append("connect")

    def exec_command(self, command, timeout=None):
        self.calls.append(("exec", command, timeout))
        stdout = _Buffer(b"ok\n", self.channel)
        stderr = _Buffer(self.stderr_payload, self.channel)
        return None, stdout, stderr

    def close(self):
        self.calls.append("close")


def test_connect_disables_agent_and_uses_the_timeout():
    kwargs = connect_kwargs(_server(), SSH_TIMEOUT_SECONDS)
    assert kwargs["allow_agent"] is False
    assert kwargs["look_for_keys"] is False
    assert kwargs["timeout"] == 5
    assert kwargs["auth_timeout"] == 5
    assert kwargs["banner_timeout"] == 5
    assert kwargs["password"] == "unique-secret-password"
    assert "key_filename" not in kwargs


def test_open_does_not_request_forwarding(caplog):
    client = _Client()
    text = open_paramiko(_server(), "cat /proc/loadavg", 5, lambda: client)
    assert text == "ok\n"
    assert client.channel.calls == []
    assert "request_x11" not in client.calls
    assert "request_agent" not in client.calls
    assert "id_rsa" not in text
    assert "id_rsa" not in caplog.text
    assert ("exec", "cat /proc/loadavg", 5) in client.calls


def test_failed_command_hides_paths():
    client = _Client(status=2, stderr=b"failed reading /home/demo/.ssh/id_rsa")
    with pytest.raises(TransportFailure) as caught:
        open_paramiko(_server(), "cat /proc/loadavg", 5, lambda: client)
    assert caught.value.category == "malformed"
    assert "id_rsa" not in str(caught.value)


def test_unknown_command_does_not_connect():
    def factory():
        raise AssertionError("connected")

    transport = ParamikoTransport(client_factory=factory)
    with pytest.raises(TransportFailure) as caught:
        transport.run(_server(), "rm -rf /")
    assert caught.value.category == "unreachable"


def test_classify_discards_exception_text():
    category = classify_exception(TimeoutError("timed out reading /home/demo/.ssh/id_rsa"))
    assert category == "timeout"
    failure = TransportFailure(category)
    assert str(failure) == "timeout"
    assert "id_rsa" not in str(failure)
    assert "reboot" not in " ".join(ALLOWED_COMMANDS)
