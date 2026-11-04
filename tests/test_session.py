from tests.helpers import post_form


def test_unsigned_visitor_is_redirected(client):
    for path in ("/", "/servers/new", "/live"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/sign-in")


def test_sign_in_page_is_available_without_a_session(client):
    response = client.get("/sign-in")
    assert response.status_code == 200
    assert "Username" in response.get_data(as_text=True)


def test_signed_in_user_can_open_the_app(signed_in):
    response = signed_in.get("/")
    assert response.status_code == 200
    assert "No servers yet" in response.get_data(as_text=True)


def test_sign_out_clears_the_session(signed_in):
    response = post_form(signed_in, "/sign-out", {}, page_path="/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/sign-in")
    with signed_in.session_transaction() as session_data:
        assert "user" not in session_data
    follow = signed_in.get("/")
    assert follow.status_code == 302
    assert follow.headers["Location"].endswith("/sign-in")
