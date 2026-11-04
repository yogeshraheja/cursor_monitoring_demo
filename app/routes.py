import re
import uuid

from flask import abort, current_app, redirect, render_template, request, session, url_for

from app.auth import ADMIN_USERNAME, SIGN_IN_FAILED, authenticate
from app.collector import collect, status_text
from app.csrf import csrf_tokens_match, ensure_csrf_token, rotate_session
from app.inventory import InventoryReadError, Server, load_inventory, save_inventory
from app.present import present_snapshot

PUBLIC_ENDPOINTS = {"sign_in", "static"}
ID_RE = re.compile(r"^[0-9a-f]{32}$")
ADD_FIELDS = {"csrf_token", "display_name", "host", "ssh_port", "ssh_user", "password", "key_path"}
USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,32}$")


def register_routes(app):
    @app.before_request
    def guard():
        if request.method == "POST":
            submitted = request.form.get("csrf_token", "")
            if not csrf_tokens_match(submitted):
                abort(400)
        else:
            ensure_csrf_token()
        if request.endpoint in PUBLIC_ENDPOINTS or request.endpoint is None:
            return None
        if session.get("user") != ADMIN_USERNAME:
            return redirect(url_for("sign_in"))
        return None

    @app.context_processor
    def inject_template_context():
        return {
            "csrf_token": session.get("csrf_token", ""),
            "signed_in": session.get("user") == ADMIN_USERNAME,
        }

    @app.errorhandler(InventoryReadError)
    def inventory_failed(_exc):
        return render_template("error.html", message="The inventory file could not be read."), 500

    @app.errorhandler(400)
    def bad_request(_exc):
        return render_template("error.html", message="The form could not be submitted."), 400

    @app.errorhandler(404)
    def not_found(_exc):
        if session.get("user") != ADMIN_USERNAME:
            return redirect(url_for("sign_in"))
        return render_template("error.html", message="That page is not available."), 404

    @app.route("/sign-in", methods=["GET", "POST"])
    def sign_in():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            if authenticate(current_app.config["CONFIG_PATH"], username, password):
                rotate_session()
                return redirect(url_for("home"))
            error = SIGN_IN_FAILED
        return render_template("sign_in.html", error=error)

    @app.post("/sign-out")
    def sign_out():
        session.clear()
        return redirect(url_for("sign_in"))

    @app.get("/")
    def home():
        return render_template("list.html", rows=_rows())

    @app.get("/live")
    def list_live():
        return {
            "servers": [
                {"id": row["server"]["id"], "status": row["status"], "category": row["category"]}
                for row in _rows()
            ]
        }

    @app.route("/servers/new", methods=["GET", "POST"])
    def server_add():
        form = _blank_form()
        errors = []
        if request.method == "POST":
            form, errors, server = _parse_add_form()
            if not errors and server is not None:
                servers = load_inventory(current_app.config["DATA_DIR"])
                save_inventory(current_app.config["DATA_DIR"], servers + [server])
                return redirect(url_for("home"))
        return render_template("add_server.html", form=form, errors=errors)

    @app.get("/servers/<server_id>")
    def server_detail(server_id):
        server = _find(server_id)
        if server is None:
            abort(404)
        metrics = present_snapshot(_snapshot(server))
        return render_template("detail.html", server=_public(server), metrics=metrics)

    @app.get("/servers/<server_id>/live")
    def server_live(server_id):
        server = _find(server_id)
        if server is None:
            abort(404)
        return render_template("_metrics.html", metrics=present_snapshot(_snapshot(server)))

    @app.route("/servers/<server_id>/remove", methods=["GET", "POST"])
    def server_remove(server_id):
        server = _find(server_id)
        if server is None:
            abort(404)
        if request.method == "POST":
            remaining = [item for item in load_inventory(current_app.config["DATA_DIR"]) if item.id != server.id]
            save_inventory(current_app.config["DATA_DIR"], remaining)
            current_app.extensions["rate_store"].drop(server.id)
            return redirect(url_for("home"))
        return render_template("remove.html", server=_public(server))


def _rows():
    rows = []
    for server in load_inventory(current_app.config["DATA_DIR"]):
        snapshot = _snapshot(server)
        rows.append(
            {
                "server": _public(server),
                "status": status_text(snapshot),
                "category": "ok" if snapshot.ok else (snapshot.category or "unreachable"),
            }
        )
    return rows


def _snapshot(server):
    return collect(
        server,
        current_app.config["TRANSPORT"],
        current_app.extensions["rate_store"],
        current_app.config["CLOCK"],
        current_app.config["SAMPLE_GAP"],
    )


def _find(server_id):
    if not ID_RE.fullmatch(server_id or ""):
        return None
    for server in load_inventory(current_app.config["DATA_DIR"]):
        if server.id == server_id:
            return server
    return None


def _public(server: Server) -> dict:
    return {
        "id": server.id,
        "display_name": server.display_name,
        "host": server.host,
        "ssh_port": server.ssh_port,
        "ssh_user": server.ssh_user,
    }


def _blank_form():
    return {"display_name": "", "host": "", "ssh_port": "", "ssh_user": "", "key_path": ""}


def _parse_add_form():
    unexpected = set(request.form) - ADD_FIELDS
    form = {
        "display_name": request.form.get("display_name", ""),
        "host": request.form.get("host", ""),
        "ssh_port": request.form.get("ssh_port", ""),
        "ssh_user": request.form.get("ssh_user", ""),
        "key_path": request.form.get("key_path", ""),
    }
    errors = []
    if unexpected:
        errors.append("Unexpected fields were submitted.")
    display_name = _clean_text(form["display_name"], 80)
    host = _clean_host(form["host"])
    ssh_user = form["ssh_user"].strip()
    port = _clean_port(form["ssh_port"])
    password = request.form.get("password", "")
    key_path = _clean_key_path(form["key_path"])
    if display_name is None:
        errors.append("Display name is required.")
    if host is None:
        errors.append("Host is required.")
    if not ssh_user:
        errors.append("SSH user is required.")
    elif not USER_RE.fullmatch(ssh_user):
        errors.append("SSH user is invalid.")
    if port is None:
        errors.append("SSH port must be an integer from 1 to 65535.")
    if key_path is None:
        errors.append("Key path is invalid.")
        key_path = ""
    if not str(password).strip() and not key_path:
        errors.append("Enter a password or a private key path.")
    if len(password) > 1024:
        errors.append("Password is too long.")
    if errors:
        return form, errors, None
    server = Server(
        id=uuid.uuid4().hex,
        display_name=display_name,
        host=host,
        ssh_port=port,
        ssh_user=ssh_user,
        password=password if password.strip() else "",
        key_path=key_path,
    )
    return form, [], server


def _clean_text(value: str, limit: int):
    text = value.strip()
    if not text or len(text) > limit or any(ord(char) < 32 for char in text):
        return None
    return text


def _clean_host(value: str):
    host = value.strip()
    if not host or len(host) > 253 or any(char.isspace() or ord(char) < 32 for char in host):
        return None
    return host


def _clean_port(value: str):
    text = value.strip()
    if text == "":
        return 22
    if not text.isdigit():
        return None
    port = int(text)
    if 1 <= port <= 65535:
        return port
    return None


def _clean_key_path(value: str):
    text = value.strip()
    if not text:
        return ""
    if len(text) > 4096 or any(ord(char) < 32 for char in text):
        return None
    return text
