import os

from flask import Flask, render_template

# Used only when FLASK_SECRET_KEY is unset. This demo runs on localhost.
_LOCAL_DEMO_SECRET = "local-demo-only-not-for-shared-use"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", _LOCAL_DEMO_SECRET)

    @app.get("/")
    def home():
        return render_template("home.html")

    return app


app = create_app()
