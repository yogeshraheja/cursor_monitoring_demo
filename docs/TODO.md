# Implementation TODO

Work top to bottom. Each step is one small change for the local demo. Finish the security and documentation checks in a step before starting the next one.

Runtime stays one Flask process on the machine where Cursor is running. Bind to localhost. Keep secrets out of git.

## 1. Project initialization and basic UI

- [x] Add a Python 3 Flask app layout (`app` package, `requirements.txt`, `.gitignore`).
- [x] Add a home page that states this is the Linux server monitoring demo.
- [x] Add a simple shared layout and stylesheet so later pages look consistent.
- [x] Run the app on localhost and confirm the home page loads.

### Security

- [x] Ignore `.venv/`, local config, the inventory file, and private keys in `.gitignore`.
- [x] Set the Flask secret from the environment, with a local-only fallback for the demo.
- [x] Bind the dev server to `127.0.0.1`.

### Documentation

- [x] Add a short README: create a virtual environment, install dependencies, start Flask on localhost.
- [x] Point the README at `docs/requirements.md` for product scope.

## 2. Sign-in and unit tests

- [x] Add a sign-in page with username and password fields.
- [x] Accept only username `admin`, checked against a password hash in local config.
- [x] On success, start a session and open the home page. On failure, stay on the sign-in page with a generic error.
- [x] Add sign-out, which clears the session.
- [x] Add unit tests for success, wrong password, wrong username, and missing config hash.
- [x] Run the tests locally and confirm they pass.

### Security

- [x] Store only a password hash (Werkzeug or equivalent). The config file has no plaintext password.
- [x] Use a generic failure message for unknown user and bad password.
- [x] Set the session cookie `HttpOnly` and `SameSite`.
- [x] Add CSRF protection on the sign-in and sign-out forms.

### Documentation

- [x] Document how to generate the `admin` hash and where to put it in local config.
- [x] Document the sign-in test command in the README.

## 3. GitHub Actions CI

- [x] Add `.github/workflows/ci.yml` that runs on push and pull request.
- [x] The workflow installs dependencies and runs the unit tests.
- [x] Add a smoke step that imports the Flask app and checks the example config is present.
- [x] Confirm the workflow file contains no secrets and no remote deploy.

### Security

- [x] Use pinned action versions and least-privilege `permissions: contents: read`.
- [x] Tests use a fixture hash. The workflow does not receive SSH keys or the admin password.
- [x] Leave remote deployment out of the workflow. This demo runs on localhost only.

### Documentation

- [x] Note in the README that GitHub Actions runs tests, and the app is started locally.

## 4. Require a session for app pages

- [x] Redirect unsigned visitors from app pages to sign-in.
- [x] Leave the sign-in page available without a session.
- [x] Add tests for redirect when signed out and access when signed in.

### Security

- [x] Protect every new page with the same session check.
- [x] Sign-out clears the session before redirecting to sign-in.

### Documentation

- [x] Note in the README that monitoring pages require the `admin` session.

## 5. Empty server list

- [x] After sign-in, show a server list page with an empty state.
- [x] Add a link to add a server. The list itself has no host controls.
- [x] Add a test that the signed-in empty list renders.

### Security

- [x] Render the page only for a signed-in admin.
- [x] Keep Jinja auto-escaping on.

### Documentation

- [x] Describe the server list empty state in the README.

## 6. Local inventory file

- [x] Add load and save for a local JSON inventory (display name, host, SSH port, SSH user, password or key path).
- [x] Default SSH port to 22 when omitted.
- [x] Add unit tests for save, load, default port, and a missing file.
- [x] Ship an example inventory with fake values. The real inventory file stays untracked.

### Security

- [x] Read SSH secrets from the local file only. Do not log them.
- [x] Restrict the inventory path to a file under the project data directory.
- [x] Confirm `.gitignore` covers the real inventory file.

### Documentation

- [x] Document the inventory fields and that the real file stays on the demo machine.

## 7. Add-server form

- [x] Add a form for display name, host, SSH port, SSH user, and password or key path.
- [x] Require display name, host, and SSH user. Require a password or a key path.
- [x] Save a valid server and show it on the list.
- [x] Add tests for a valid save and for each missing required field.

### Security

- [x] Use POST and CSRF. Reject unexpected fields.
- [x] Validate port as an integer from 1 to 65535.
- [x] Do not echo the password back to the page after save.

### Documentation

- [x] Document the required add-server fields in the README.

## 8. Remove a server

- [x] Add a remove action on the list, with a confirmation step.
- [x] Remove deletes that record from the local inventory only.
- [x] Add tests for confirm-and-remove and for cancel.

### Security

- [x] Use POST and CSRF for remove.
- [x] Remove only the inventory record. Send no SSH command as part of remove.

### Documentation

- [x] Note that remove updates the local inventory and leaves the host unchanged.

## 9. SSH collector with a fake transport

- [x] Add a collector that opens SSH with a 5-second timeout and runs a fixed set of read commands.
- [x] Return a structured error for timeout, authentication failure, and unreachable host.
- [x] Add unit tests with a fake transport. Tests do not open a real SSH connection.

### Security

- [x] Allow only the fixed read commands. Do not pass form input into a shell string.
- [x] Disable agent and X11 forwarding. Do not log credentials or key material.
- [x] Treat remote stdout as untrusted text.

### Documentation

- [x] Document the collector timeout and that tests use a fake transport.

## 10. CPU and memory snapshot

- [x] Parse CPU utilization, load average, and memory total, used, available, and used percent from sample command output.
- [x] Show those values on a read-only server detail page.
- [x] Add parser tests for a normal sample and a malformed sample.

### Security

- [x] Escape all host-provided text in the template.
- [x] On a malformed sample, show a collection error and no partial numbers presented as live data.

### Documentation

- [x] List the CPU and memory fields in the README.

## 11. Network rates

- [x] Parse per-interface receive and transmit counters.
- [x] Show bytes per second from the previous successful sample. The first sample shows counters only.
- [x] Keep the previous sample in memory for that process only.
- [x] Add tests for the first sample and for a rate computed from two samples.

### Security

- [x] Do not write counters to disk.
- [x] Ignore interface names that do not match a conservative hostname-safe pattern, and escape the rest on display.

### Documentation

- [x] Document that the first refresh has no rate and that rates are not stored.

## 12. Listening ports

- [x] Parse listening TCP and UDP sockets: address, port, protocol, and process name when present.
- [x] Show them in a read-only table on the detail page.
- [x] Add tests for a row with a process name and a row without one.

### Security

- [x] Display process names as text. Add no link or action from a row.
- [x] Escape process names and addresses.

### Documentation

- [x] Document the listening-port columns in the README.

## 13. Per-server errors and list reachability

- [x] On the detail page, show the collector error for a failed host.
- [x] On the list, show reachable or the error for each server.
- [x] A failure on one server still leaves the others visible.
- [x] Add tests with one success and one failure in the same inventory.

### Security

- [x] Show a short error category (timeout, authentication, unreachable). Omit raw SSH exception text that could contain paths or key details.
- [x] Keep collection read-only.

### Documentation

- [x] Document the three error states in the README.

## 14. Auto-refresh

- [x] Refresh the detail page in place every 5 seconds.
- [x] Refresh list reachability every 5 seconds.
- [x] Add a test or a small view check that the page includes the 5-second refresh.

### Security

- [x] Request same-origin JSON or HTML only. Send no inventory secrets to the browser beyond what the page already shows.
- [x] Prefer omitting the SSH password and key path from list and detail responses.

### Documentation

- [x] Document the 5-second refresh in the README.

## 15. Read-only pass

- [x] Review list and detail templates for buttons other than add, remove, sign-out, and navigation.
- [x] Confirm add and remove are the only inventory writes.
- [x] Add a test that the detail page does not contain remote-action controls.

### Security

- [x] Confirm no route accepts a remote command, shell, restart, or process kill.
- [x] Confirm CSRF is present on every POST route.

### Documentation

- [x] State in the README that monitoring pages are read-only and inventory edits stay local.

## 16. Local run-through

- [x] Follow the README from a clean virtual environment and sign in as `admin`.
- [x] Add one Linux server, open its detail page, and see CPU, memory, network, and listening ports, or a clear collection error.
- [x] Remove the server and confirm the list is empty again.

### Security

- [x] Confirm the real config and inventory are untracked (`git status`).
- [x] Confirm the app is bound to localhost.

### Documentation

- [x] Keep the README setup to the four steps in `docs/requirements.md`: virtual environment, local config and inventory, start on localhost, sign in and add a host.
