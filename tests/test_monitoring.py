import re

from app.inventory import Server, load_inventory, save_inventory
from tests.samples import command_outputs


def _add(data_dir, **overrides):
    values = {
        "id": "abc123abc123abc123abc123abc123ab",
        "display_name": "Edge proxy",
        "host": "203.0.113.20",
        "ssh_port": 22,
        "ssh_user": "monitor",
        "password": "unique-secret-password",
        "key_path": "/tmp/demo-key-do-not-render",
    }
    values.update(overrides)
    server = Server(**values)
    save_inventory(data_dir, [server])
    return server


def test_one_success_and_one_failure_both_stay_visible(signed_in, data_dir, transport):
    good = Server(
        id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        display_name="Good host",
        host="good.example",
        ssh_port=22,
        ssh_user="monitor",
        password="unique-secret-password",
    )
    bad = Server(
        id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        display_name="Bad host",
        host="bad.example",
        ssh_port=22,
        ssh_user="monitor",
        password="unique-secret-password",
    )
    save_inventory(data_dir, [good, bad])
    transport.queue(good.host, command_outputs())
    transport.fail(bad.host, "authentication")
    body = signed_in.get("/").get_data(as_text=True)
    assert "Good host" in body
    assert "Bad host" in body
    assert "Reachable" in body
    assert "Authentication failed" in body
    assert "unique-secret-password" not in body


def test_detail_shows_snapshot_and_five_second_refresh(signed_in, data_dir, transport, clock):
    server = _add(data_dir)
    transport.queue(server.host, command_outputs())
    before = (data_dir / "inventory.json").read_text(encoding="utf-8")
    response = signed_in.get(f"/servers/{server.id}")
    body = response.get_data(as_text=True)
    assert "50.0%" in body
    assert "0.40" in body
    assert "2000 MiB" in body
    assert "1000 MiB" in body
    assert "No rate yet" in body
    assert "sshd" in body
    assert 'data-interval="5000"' in body
    assert "unique-secret-password" not in body
    assert "/tmp/demo-key-do-not-render" not in body
    assert "../../x" not in body
    assert (data_dir / "inventory.json").read_text(encoding="utf-8") == before
    ports = re.search(r'id="listening-ports".*?</table>', body, re.S).group(0)
    assert "<a " not in ports
    assert "<button" not in ports
    assert "—" in ports

    clock.value = 1002
    transport.queue(server.host, command_outputs(rx=3000, tx=6000))
    live = signed_in.get(f"/servers/{server.id}/live")
    live_body = live.get_data(as_text=True)
    assert "1000 B/s" in live_body
    assert "2000 B/s" in live_body
    assert "No rate yet" not in live_body
    assert "<form" not in live_body


def test_malformed_detail_hides_partial_numbers(signed_in, data_dir, transport):
    server = _add(data_dir)
    transport.queue(server.host, ["not-a-sample"] * 6)
    body = signed_in.get(f"/servers/{server.id}").get_data(as_text=True)
    assert "The host returned data that could not be read." in body
    assert "Utilization" not in body
    assert "2000 MiB" not in body


def test_host_text_is_escaped(signed_in, data_dir, transport):
    server = _add(
        data_dir,
        display_name='<img src=x onerror=alert(1)>',
    )
    transport.queue(server.host, command_outputs(process="<script>alert(1)</script>"))
    body = signed_in.get(f"/servers/{server.id}").get_data(as_text=True)
    assert "<img src=x onerror=alert(1)>" not in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body


def test_list_refresh_marker_is_present(signed_in, data_dir, transport):
    server = _add(data_dir)
    transport.fail(server.host, "timeout")
    body = signed_in.get("/").get_data(as_text=True)
    assert 'data-interval="5000"' in body
    assert 'data-url="/live"' in body
    assert 'data-mode="status"' in body
    live = signed_in.get("/live")
    payload = live.get_json()
    assert payload["servers"][0]["status"] == "Timed out"
    assert payload["servers"][0]["category"] == "timeout"
    encoded = live.get_data(as_text=True)
    assert "unique-secret-password" not in encoded
    assert "/tmp/demo-key-do-not-render" not in encoded


def test_detail_has_no_remote_actions_and_posts_are_csrf_only(signed_in, data_dir, transport, app):
    server = _add(data_dir)
    transport.queue(server.host, command_outputs())
    body = signed_in.get(f"/servers/{server.id}").get_data(as_text=True)
    assert "Restart" not in body
    assert "Kill" not in body
    assert "reboot" not in body.lower()
    assert 'name="command"' not in body
    actions = re.findall(r'<form[^>]*action="([^"]*)"', body)
    assert actions == ["/sign-out"]
    post_rules = sorted(rule.rule for rule in app.url_map.iter_rules() if "POST" in rule.methods)
    assert post_rules == ["/servers/<server_id>/remove", "/servers/new", "/sign-in", "/sign-out"]
    for rule in app.url_map.iter_rules():
        lowered = rule.rule.lower()
        assert "restart" not in lowered
        assert "kill" not in lowered
        assert "shell" not in lowered
        assert "exec" not in lowered
    rejected = signed_in.post(f"/servers/{server.id}/remove", data={})
    assert rejected.status_code == 400
    assert load_inventory(data_dir) == [server]


def test_templates_escape_html(app):
    rendered = app.jinja_env.from_string("{{ value }}").render(value="<b>")
    assert rendered == "&lt;b&gt;"
