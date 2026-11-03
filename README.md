# Linux server monitoring demo

Local Flask app for live Linux server monitoring. Product scope is in [docs/requirements.md](docs/requirements.md).

## Setup

1. Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start Flask on localhost:

```bash
flask --app app run --host 127.0.0.1 --port 5000
```

Open http://127.0.0.1:5000/.

`FLASK_SECRET_KEY` sets the Flask secret. When that variable is unset, the app uses a local-only fallback for this demo.
