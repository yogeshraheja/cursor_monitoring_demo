import re

from tests.constants import PASSWORD


def csrf_from(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, html
    return match.group(1)


def post_form(client, path, data, page_path=None):
    page = client.get(page_path or path)
    assert page.status_code == 200
    payload = dict(data)
    payload["csrf_token"] = csrf_from(page.get_data(as_text=True))
    return client.post(path, data=payload)


def sign_in(client, username="admin", password=PASSWORD):
    return post_form(client, "/sign-in", {"username": username, "password": password})
