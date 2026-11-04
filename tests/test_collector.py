from app.collector import collect
from app.commands import READ_COMMANDS
from app.inventory import Server
from app.rates import RateStore
from tests.fake_transport import FakeTransport
from tests.samples import command_outputs


def _server():
    return Server(
        id="abc123abc123abc123abc123abc123ab",
        display_name="Edge",
        host="203.0.113.20",
        ssh_port=22,
        ssh_user="monitor",
        password="unique-secret-password",
        key_path="/tmp/demo-key-do-not-render",
    )


def test_fixed_commands_do_not_include_form_input():
    server = _server()
    transport = FakeTransport()
    transport.queue(server.host, command_outputs())
    snapshot = collect(server, transport, RateStore(), lambda: 1000.0, 0)
    assert snapshot.ok is True
    assert transport.seen == list(READ_COMMANDS)
    for command in transport.seen:
        assert server.password not in command
        assert server.key_path not in command
        assert server.host not in command
        assert server.display_name not in command


def test_transport_errors_are_categories_without_cpu_numbers():
    server = _server()
    for category in ("timeout", "authentication", "unreachable"):
        transport = FakeTransport()
        transport.fail(server.host, category)
        snapshot = collect(server, transport, RateStore(), lambda: 1000.0, 0)
        assert snapshot.ok is False
        assert snapshot.category == category
        assert snapshot.cpu is None
        assert snapshot.memory is None
        assert snapshot.interfaces is None
        assert str(category) == category


def test_malformed_sample_has_no_partial_metrics():
    server = _server()
    transport = FakeTransport()
    transport.queue(server.host, ["not-a-sample"] * 6)
    snapshot = collect(server, transport, RateStore(), lambda: 1000.0, 0)
    assert snapshot.ok is False
    assert snapshot.category == "malformed"
    assert snapshot.cpu is None
    assert snapshot.memory is None
