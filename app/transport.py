import errno
import socket

import paramiko

from app.commands import ALLOWED_COMMANDS

SSH_TIMEOUT_SECONDS = 5


class TransportFailure(Exception):
    def __init__(self, category: str):
        self.category = category if category in {"timeout", "authentication", "unreachable", "malformed"} else "unreachable"
        super().__init__(self.category)


def connect_kwargs(server, timeout: float) -> dict:
    kwargs = {
        "hostname": server.host,
        "port": server.ssh_port,
        "username": server.ssh_user,
        "timeout": timeout,
        "banner_timeout": timeout,
        "auth_timeout": timeout,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if server.key_path:
        kwargs["key_filename"] = server.key_path
    elif server.password:
        kwargs["password"] = server.password
    return kwargs


def classify_exception(exc: BaseException) -> str:
    if isinstance(exc, paramiko.AuthenticationException):
        return "authentication"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, (paramiko.ssh_exception.NoValidConnectionsError, socket.gaierror, ConnectionRefusedError)):
        return "unreachable"
    if isinstance(exc, OSError) and getattr(exc, "errno", None) == errno.ETIMEDOUT:
        return "timeout"
    if isinstance(exc, OSError):
        return "unreachable"
    if isinstance(exc, paramiko.SSHException):
        text = str(exc).lower()
        if "timed out" in text or "timeout" in text:
            return "timeout"
        if "authentication" in text:
            return "authentication"
        return "unreachable"
    return "unreachable"


class ParamikoTransport:
    def __init__(self, timeout: float = SSH_TIMEOUT_SECONDS, client_factory=None):
        self.timeout = timeout
        self._client_factory = client_factory

    def run(self, server, command: str) -> str:
        if command not in ALLOWED_COMMANDS:
            raise TransportFailure("unreachable")
        try:
            return open_paramiko(server, command, self.timeout, self._client_factory)
        except TransportFailure:
            raise
        except Exception as exc:
            raise TransportFailure(classify_exception(exc)) from None


def open_paramiko(server, command: str, timeout: float, client_factory=None) -> str:
    client = (client_factory or paramiko.SSHClient)()
    try:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.load_system_host_keys()
        except Exception:
            pass
        # Agent and X11 forwarding are never requested on the session channel.
        client.connect(**connect_kwargs(server, timeout))
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        text = stdout.read().decode("utf-8", errors="replace")
        stderr.read()
        if stdout.channel.recv_exit_status() != 0:
            raise TransportFailure("malformed")
        return text
    finally:
        client.close()
