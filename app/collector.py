import time
from dataclasses import dataclass

from app.commands import READ_COMMANDS, STAT
from app.parsers import (
    CpuSnapshot,
    ListeningPort,
    MemorySnapshot,
    ParseError,
    parse_cpu,
    parse_memory,
    parse_netdev,
    parse_sockets,
)
from app.rates import InterfaceView, RateStore
from app.transport import TransportFailure

ERROR_TEXT = {
    "timeout": "Timed out",
    "authentication": "Authentication failed",
    "unreachable": "Host unreachable",
    "malformed": "The host returned data that could not be read.",
}


@dataclass
class Snapshot:
    ok: bool
    category: str | None = None
    cpu: CpuSnapshot | None = None
    memory: MemorySnapshot | None = None
    interfaces: list[InterfaceView] | None = None
    ports: list[ListeningPort] | None = None


def collect(server, transport, rate_store: RateStore, clock, sample_gap: float) -> Snapshot:
    """Run the fixed read commands and parse stdout as untrusted text."""
    outputs = []
    previous = None
    try:
        for command in READ_COMMANDS:
            if previous == STAT and command == STAT and sample_gap:
                time.sleep(sample_gap)
            outputs.append(transport.run(server, command))
            previous = command
    except TransportFailure as exc:
        return _failed(_safe_category(exc.category))
    try:
        cpu = parse_cpu(outputs[1], outputs[2], outputs[0])
        memory = parse_memory(outputs[3])
        counters = parse_netdev(outputs[4])
        ports = parse_sockets(outputs[5])
    except ParseError:
        return _failed("malformed")
    interfaces = rate_store.apply(server.id, counters, clock())
    return Snapshot(ok=True, cpu=cpu, memory=memory, interfaces=interfaces, ports=ports)


def status_text(snapshot: Snapshot) -> str:
    if snapshot.ok:
        return "Reachable"
    return ERROR_TEXT.get(snapshot.category or "", ERROR_TEXT["unreachable"])


def _failed(category: str) -> Snapshot:
    return Snapshot(ok=False, category=category)


def _safe_category(category: str) -> str:
    if category in ERROR_TEXT and category != "malformed":
        return category
    if category == "malformed":
        return "malformed"
    return "unreachable"
