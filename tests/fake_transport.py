from app.commands import ALLOWED_COMMANDS
from app.transport import TransportFailure


class FakeTransport:
    def __init__(self):
        self._outputs = {}
        self._failures = {}
        self.seen = []

    def queue(self, host, outputs):
        self._outputs.setdefault(host, []).extend(outputs)

    def fail(self, host, category):
        self._failures[host] = category

    def run(self, server, command):
        self.seen.append(command)
        if command not in ALLOWED_COMMANDS:
            raise TransportFailure("unreachable")
        if server.host in self._failures:
            raise TransportFailure(self._failures[server.host])
        pending = self._outputs.get(server.host) or []
        if not pending:
            raise TransportFailure("unreachable")
        return self._outputs[server.host].pop(0)
