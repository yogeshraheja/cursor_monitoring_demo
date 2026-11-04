# Linux server monitoring demo

Local Flask app for live Linux server monitoring. Product scope is in [docs/requirements.md](docs/requirements.md).

GitHub Actions runs the unit tests. Start the app locally. This demo does not deploy anywhere.

## Setup

1. Create a virtual environment and install Flask, Paramiko, and the test runner:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create the local config and inventory on this machine:

```bash
cp config.example.json config.local.json
python -c "from werkzeug.security import generate_password_hash; import getpass; print(generate_password_hash(getpass.getpass('Admin password: ')))"
```

Put the printed hash in `config.local.json` as `admin_password_hash`. The file stores the hash only. Leave the real inventory at `data/inventory.json`. Copy `data/inventory.example.json` over it only when you want the fake sample host. Both local files stay on this machine and are gitignored.

3. Start Flask on localhost:

```bash
flask --app app run --host 127.0.0.1 --port 5000
```

4. Open http://127.0.0.1:5000/, sign in as `admin`, and add a Linux host.

`FLASK_SECRET_KEY` sets the Flask secret. When that variable is unset, the app uses a local-only fallback for this demo.

## Sign-in

Monitoring pages require the `admin` session. The username is `admin`. The password is checked against `admin_password_hash` in `config.local.json`. A failed sign-in stays on the sign-in page and shows `Sign-in failed.` Sign-out clears the session. The session cookie is `HttpOnly` and `SameSite=Lax`.

## Tests

Unit tests use a fixture hash and a fake SSH transport. They do not open a real SSH connection and they do not need the admin password.

```bash
python -m pytest
```

## Server list

After sign-in, the home page is the server list. An empty inventory shows **No servers yet** and a link to add a server. The list shows each server as reachable or as one of the collection errors below. Reachability refreshes every 5 seconds.

## Inventory

The real inventory file is `data/inventory.json`, under the project `data` directory. The app refuses a path outside that directory. Fields:

| Field | Rule |
| --- | --- |
| Display name | Required |
| Host name or IP | Required |
| SSH port | Optional, default 22, integer from 1 to 65535 |
| SSH user | Required |
| Password or private key path | One of the two is required |

SSH secrets are read from that file when collecting. They are not written to the page after save and they are not logged. Remove deletes the inventory record only. The host is not changed.

## Collection

Each refresh opens SSH with a 5-second timeout and runs a fixed set of read commands (`/proc/loadavg`, `/proc/stat`, `/proc/meminfo`, `/proc/net/dev`, and `ss`). Form input is not inserted into those commands. Agent and X11 forwarding are off. Tests call a fake transport instead of Paramiko.

A failed host shows one of three errors: **Timed out**, **Authentication failed**, or **Host unreachable**. The page does not include the raw SSH exception. Other servers still appear. If the command output cannot be parsed, the detail page shows a collection error and no partial numbers.

This local demo accepts a new SSH host key on first connect.

## Metrics

CPU shows utilization percent and the 1, 5, and 15 minute load averages. Memory shows total, used, available, and used percent.

Network shows per-interface receive and transmit counters. Bytes per second come from the previous successful sample in this process. The first refresh has no rate. Rates are not stored on disk.

Listening ports show address, port, protocol, and process name when the host provides one. Process names are text, with no link or action.

The detail page refreshes in place every 5 seconds. Refresh requests stay on this origin. Responses omit the SSH password and key path.

## Read-only

Monitoring pages are read-only. Add and remove are the only inventory writes, and those edits stay on this machine. No page sends a remote command, shell, restart, or process kill.
