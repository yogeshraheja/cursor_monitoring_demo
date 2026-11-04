import json
from pathlib import Path

from werkzeug.security import check_password_hash

ADMIN_USERNAME = "admin"
SIGN_IN_FAILED = "Sign-in failed."

# Used when the username does not match or the config has no hash, so those
# failures still pay the password-hash cost. Not a password for any account.
_DUMMY_HASH = (
    "scrypt:32768:8:1$mULcyVtKdk80Ne1U$"
    "e8c44ac74a8c9d355af21cc7be79206c58f28f67b83573e88cd375f9bea86fcb"
    "965782018306d67f426485abe18eaaf385c430e845fdd5560de454f3d993a9e7"
)


def load_admin_password_hash(config_path: Path) -> str | None:
    path = Path(config_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("admin_password_hash")
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def authenticate(config_path: Path, username: str, password: str) -> bool:
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if len(username) > 64 or len(password) > 256:
        return False
    stored = load_admin_password_hash(config_path)
    username_matches = username == ADMIN_USERNAME
    candidate = stored if stored and username_matches else _DUMMY_HASH
    try:
        password_matches = check_password_hash(candidate, password)
    except (TypeError, ValueError):
        password_matches = False
    return bool(stored and username_matches and password_matches)
