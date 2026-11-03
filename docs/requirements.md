# Demo Server Monitoring — Requirements

**Product:** Local demo for live Linux server monitoring  
**Status:** Draft  
**Runtime:** One Flask app on the machine where Cursor is running

## 1. Problem

L1, L2, L3, and application teams currently open a shell on each Linux server to see live memory, CPU, network, and port usage. This demo gives them one web UI for those checks.

## 2. Users

| Team | What they do in the demo |
| --- | --- |
| L1 | Confirm a server is reachable and scan CPU, memory, network, and listening ports |
| L2 | Use the same live figures while investigating an incident |
| L3 and application development | See host usage and which process owns a listening port |

The demo has one shared admin account. It does not separate teams by role.

## 3. Goals

- Show live CPU, memory, network, and listening-port data for registered Linux servers.
- Keep monitoring screens read-only.
- Let the admin add and remove servers in the local inventory.
- Sign in as `admin` with a password checked against a hash in local config.
- Run locally with a short setup.

## 4. Out of scope

- Operating systems other than Linux
- Alerts, paging, and tickets
- Charts, history, and any metric database
- Extra users, roles, or a password-change screen
- Remote actions such as shell, restart, file changes, or process control
- TLS, high availability, and production identity integration

## 5. Technical approach

- Python 3 and Flask
- Server-rendered pages with templates, CSS, and a small script for auto-refresh
- SSH from the Flask process to each registered host for a live snapshot
- Server inventory and SSH credentials in a local file on the demo machine
- Admin password stored only as a hash in local config

One process serves the UI and collects metrics. No separate frontend build and no external database.

## 6. Features

### 6.1 Read-only monitoring UI

Monitoring pages display data and navigation only. They expose no control that changes a remote server.

The admin can add and remove servers. Those actions update the local inventory only.

**Acceptance**

- A signed-in user can open the server list and a server detail page.
- The detail page shows CPU, memory, network, and listening ports.
- Monitoring pages have no control that runs a command on the host.
- The layout is clear on a desktop browser, including loading, empty, and error states.

### 6.2 Sign-in

- The username is `admin`.
- The app checks the password against a hash in a local config file.
- The config stores the password hash.
- A failed sign-in shows a generic error and stays on the sign-in page.
- A visitor without a session is sent to the sign-in page.
- Sign-out ends the session.
- The demo has this single account. There is no user-management screen.

**Acceptance**

- `admin` and the configured password open the server list.
- A wrong password does not open the app.
- A monitoring URL opened without a session redirects to sign-in.

### 6.3 Add and remove Linux servers

The add form collects:

| Field | Rule |
| --- | --- |
| Display name | Required |
| Host name or IP | Required |
| SSH port | Optional, default 22 |
| SSH user | Required |
| Authentication | Password or private key path; one of the two is required |

Remove deletes the server from the local inventory and stops collection. It leaves the host unchanged. The UI asks for confirmation before remove.

Inventory and SSH secrets stay in a local file on the demo machine.

**Acceptance**

- After a valid save, the server appears on the list.
- The form rejects a save when a required field is missing.
- After confirm, the removed server disappears from the list.
- Key path and password values are read from the local inventory file at collection time.

### 6.4 Live metrics over SSH

Each refresh opens SSH with the saved details and reads current values. The app shows that snapshot only. It does not store readings.

The server detail page refreshes in place every 5 seconds. The list refreshes reachability on the same interval.

A failed collection (timeout, authentication failure, or unreachable host) is shown on that server. Other servers still load. Per-host SSH timeout is 5 seconds.

| Area | What the page shows |
| --- | --- |
| CPU | Utilization percent and load average |
| Memory | Total, used, available, and used percent |
| Network | Per-interface receive and transmit rate in bytes per second, computed from the previous successful sample. The first sample shows counters only and waits for the next refresh to show a rate. |
| Ports | Listening TCP and UDP sockets: local address, port, protocol, and process name when the host exposes it |

**Acceptance**

- A reachable host shows all four areas with data from that host.
- An unreachable host shows the collection error.
- The detail page updates in place every 5 seconds.
- Listening ports include the process name when the SSH user can see it.

## 7. Local setup

The demo runs on the same machine as Cursor.

1. Create a virtual environment and install Flask and an SSH client library.
2. Copy the example config, set the `admin` password hash, and keep SSH secrets in the local inventory file.
3. Start Flask on localhost.
4. Sign in as `admin`, add a Linux host, and confirm the live stats.

Command-level setup belongs in a README when the app is implemented. Setup stays a single local process.

## 8. Demo defaults

| Item | Choice |
| --- | --- |
| Admin username | `admin` |
| Admin password | Hash in local config |
| Page refresh | 5 seconds |
| SSH timeout | 5 seconds |
| SSH port | 22 when omitted |
| Metric retention | None |
| Host OS | Linux |

## 9. Done when

A user can sign in, register a Linux server, and see live CPU, memory, network, and listening-port details without opening a shell on that server. Monitoring pages stay read-only. Add and remove change only the local inventory. The app runs on the machine where Cursor is running.
