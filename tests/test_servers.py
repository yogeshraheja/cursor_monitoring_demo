from app.inventory import Server, load_inventory, save_inventory
from tests.helpers import post_form


def _valid(**overrides):
    data = {
        "display_name": "Edge proxy",
        "host": "203.0.113.20",
        "ssh_user": "monitor",
        "password": "unique-secret-password",
    }
    data.update(overrides)
    return data


def test_empty_list_renders_for_signed_in_admin(signed_in):
    response = signed_in.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "No servers yet" in body
    assert "Add a server" in body
    assert 'href="/servers/new"' in body


def test_valid_save_shows_server_and_hides_password(signed_in, data_dir):
    response = post_form(signed_in, "/servers/new", _valid(), page_path="/servers/new")
    assert response.status_code == 302
    page = signed_in.get("/")
    body = page.get_data(as_text=True)
    assert "Edge proxy" in body
    assert "203.0.113.20" in body
    assert "unique-secret-password" not in body
    stored = load_inventory(data_dir)
    assert stored[0].password == "unique-secret-password"
    assert stored[0].ssh_port == 22


def test_each_missing_required_field(signed_in, data_dir):
    cases = [
        {"display_name": ""},
        {"host": ""},
        {"ssh_user": ""},
        {"password": ""},
    ]
    messages = [
        "Display name is required.",
        "Host is required.",
        "SSH user is required.",
        "Enter a password or a private key path.",
    ]
    for overrides, message in zip(cases, messages):
        response = post_form(signed_in, "/servers/new", _valid(**overrides))
        assert response.status_code == 200
        assert message in response.get_data(as_text=True)
        assert load_inventory(data_dir) == []


def test_invalid_port_is_rejected(signed_in, data_dir):
    response = post_form(signed_in, "/servers/new", _valid(ssh_port="70000"))
    assert response.status_code == 200
    assert "SSH port must be an integer from 1 to 65535." in response.get_data(as_text=True)
    assert load_inventory(data_dir) == []


def test_unexpected_field_is_rejected(signed_in, data_dir):
    response = post_form(signed_in, "/servers/new", _valid(reboot="now"))
    assert response.status_code == 200
    assert "Unexpected fields were submitted." in response.get_data(as_text=True)
    assert load_inventory(data_dir) == []


def test_confirm_remove_and_cancel(signed_in, data_dir, transport):
    server = Server(
        id="abc123abc123abc123abc123abc123ab",
        display_name="Edge proxy",
        host="203.0.113.20",
        ssh_port=22,
        ssh_user="monitor",
        password="unique-secret-password",
    )
    save_inventory(data_dir, [server])
    confirm = signed_in.get(f"/servers/{server.id}/remove")
    body = confirm.get_data(as_text=True)
    assert confirm.status_code == 200
    assert "The host is not changed." in body
    assert "unique-secret-password" not in body
    cancel = signed_in.get("/")
    assert "Edge proxy" in cancel.get_data(as_text=True)
    assert load_inventory(data_dir) == [server]
    transport.seen.clear()
    removed = post_form(signed_in, f"/servers/{server.id}/remove", {})
    assert removed.status_code == 302
    assert transport.seen == []
    assert load_inventory(data_dir) == []
    page = signed_in.get("/")
    assert "No servers yet" in page.get_data(as_text=True)
    assert "Edge proxy" not in page.get_data(as_text=True)
