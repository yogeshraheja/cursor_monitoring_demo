from pathlib import Path


def test_workflow_is_least_privilege_and_has_no_secrets():
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "contents: read" in lowered
    assert "password" not in lowered
    assert "secret" not in lowered
    assert "deploy" not in lowered
    assert "ssh" not in lowered
    assert "actions/checkout@" in text
    assert "actions/setup-python@" in text
    assert "@v" not in text.split("uses: ", 1)[1]


def test_readme_covers_local_setup_and_tests():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "127.0.0.1" in text
    assert "python -m pytest" in text
    assert "admin_password_hash" in text
    assert "data/inventory.json" in text
    assert "GitHub Actions" in text
    assert "5 seconds" in text
    assert "read-only" in text
