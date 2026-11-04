import json
import os
from dataclasses import dataclass
from pathlib import Path


class InventoryPathError(Exception):
    """The inventory path escaped the data directory."""


class InventoryReadError(Exception):
    """The inventory file could not be read. The message stays generic."""


@dataclass(frozen=True)
class Server:
    id: str
    display_name: str
    host: str
    ssh_port: int
    ssh_user: str
    password: str = ""
    key_path: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "host": self.host,
            "ssh_port": self.ssh_port,
            "ssh_user": self.ssh_user,
            "password": self.password,
            "key_path": self.key_path,
        }


def resolve_inventory_path(data_dir: Path, configured: Path | None = None) -> Path:
    root = Path(data_dir).resolve()
    if configured is None:
        candidate = root / "inventory.json"
    else:
        raw = Path(configured)
        candidate = raw if raw.is_absolute() else root / raw
    candidate = candidate.resolve()
    if candidate == root or root not in candidate.parents:
        raise InventoryPathError("Inventory path must stay inside the data directory")
    return candidate


def load_inventory(data_dir: Path, configured: Path | None = None) -> list[Server]:
    path = resolve_inventory_path(data_dir, configured)
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        raise InventoryReadError from None
    if not text.strip():
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise InventoryReadError from None
    if not isinstance(data, dict) or not isinstance(data.get("servers", []), list):
        raise InventoryReadError
    servers = []
    for entry in data.get("servers", []):
        servers.append(_server_from_entry(entry))
    return servers


def save_inventory(data_dir: Path, servers: list[Server], configured: Path | None = None) -> Path:
    path = resolve_inventory_path(data_dir, configured)
    path.parent.mkdir(mode=0o700, exist_ok=True)
    payload = json.dumps({"servers": [server.to_dict() for server in servers]}, indent=2) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    os.replace(temporary, path)
    os.chmod(path, 0o600)
    return path


def _server_from_entry(entry: object) -> Server:
    if not isinstance(entry, dict):
        raise InventoryReadError
    server_id = entry.get("id")
    display_name = entry.get("display_name")
    host = entry.get("host")
    ssh_user = entry.get("ssh_user")
    if not all(isinstance(value, str) and value for value in (server_id, display_name, host, ssh_user)):
        raise InventoryReadError
    password = entry.get("password", "")
    key_path = entry.get("key_path", "")
    if not isinstance(password, str) or not isinstance(key_path, str):
        raise InventoryReadError
    return Server(
        id=server_id,
        display_name=display_name,
        host=host,
        ssh_port=_port_from_entry(entry),
        ssh_user=ssh_user,
        password=password,
        key_path=key_path,
    )


def _port_from_entry(entry: dict) -> int:
    if "ssh_port" not in entry or entry["ssh_port"] is None:
        return 22
    port = entry["ssh_port"]
    if isinstance(port, str) and port.isdigit():
        port = int(port)
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise InventoryReadError
    return port
