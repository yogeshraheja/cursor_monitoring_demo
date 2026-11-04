import logging
import os
import time
from pathlib import Path

from flask import Flask

from app.rates import RateStore
from app.transport import ParamikoTransport

ROOT = Path(__file__).resolve().parent.parent
_LOCAL_DEMO_SECRET = "local-demo-only-not-for-shared-use"


def create_app(config_path=None, data_dir=None, transport=None, sample_gap=0.25, clock=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", _LOCAL_DEMO_SECRET)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
    app.config["CONFIG_PATH"] = Path(config_path) if config_path else ROOT / "config.local.json"
    app.config["DATA_DIR"] = Path(data_dir) if data_dir else ROOT / "data"
    app.config["SAMPLE_GAP"] = sample_gap
    app.config["CLOCK"] = clock or time.monotonic
    app.config["TRANSPORT"] = transport or ParamikoTransport()
    app.extensions["rate_store"] = RateStore()
    logging.getLogger("paramiko").setLevel(logging.WARNING)

    from app.routes import register_routes

    register_routes(app)
    return app


app = create_app()
