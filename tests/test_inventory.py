import json
from pathlib import Path

import pytest

from app.inventory import (
    InventoryPathError,
    Server,
    load_inventory,
    resolve_inventory_path,
    save_inventory,
)


def _server(**overrides):
    values = {
        "id": "abc123abc123abc123abc123abc123ab",
        "display_name": "Web",
        "host": "203.0.113.10",
        "ssh_port": 22,
        "ssh_user": "monitor",
        "password": "stored-secret",
        "key_path": "",
    }
    values.update(overrides)
    return Server(**values)


def test_save_and_load_round_trip(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    save_inventory(data_dir, [_server()])
    loaded = load_inventory(data_dir)
    assert loaded == [_server()]
    assert loaded[0].password == "stored-secret"


def test_missing_file_loads_as_empty(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    assert load_inventory(data_dir) == []


def test_omitted_port_defaults_to_22(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    path = data_dir / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "id": "abc123abc123abc123abc123abc123ab",
                        "display_name": "Web",
                        "host": "203.0.113.10",
                        "ssh_user": "monitor",
                        "password": "stored-secret",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    loaded = load_inventory(data_dir)
    assert loaded[0].ssh_port == 22


def test_inventory_path_must_stay_inside_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    outside = tmp_path / "secret.json"
    with pytest.raises(InventoryPathError):
        resolve_inventory_path(data_dir, outside)
    with pytest.raises(InventoryPathError):
        resolve_inventory_path(data_dir, Path("../secret.json"))


def test_saved_inventory_is_not_world_readable(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    path = save_inventory(data_dir, [_server()])
    assert path.stat().st_mode & 0o077 == 0


def test_gitignore_covers_real_inventory_and_local_config():
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert "data/inventory.json" in text
    assert "config.local.json" in text
