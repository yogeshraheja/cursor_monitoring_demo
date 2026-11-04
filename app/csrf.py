import secrets

from flask import session

CSRF_FIELD = "csrf_token"


def ensure_csrf_token() -> str:
    token = session.get(CSRF_FIELD)
    if not isinstance(token, str) or not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_FIELD] = token
    return token


def csrf_tokens_match(submitted: str) -> bool:
    expected = session.get(CSRF_FIELD, "")
    if not isinstance(expected, str) or not expected or not submitted:
        return False
    return secrets.compare_digest(expected, submitted)


def rotate_session() -> None:
    from app.auth import ADMIN_USERNAME

    session.clear()
    session["user"] = ADMIN_USERNAME
    session[CSRF_FIELD] = secrets.token_urlsafe(32)
    session.modified = True
