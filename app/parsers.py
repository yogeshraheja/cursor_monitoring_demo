import re
from dataclasses import dataclass


class ParseError(Exception):
    """Host output did not match the expected read-only sample."""


@dataclass(frozen=True)
class CpuSnapshot:
    utilization_percent: float
    load_1: float
    load_5: float
    load_15: float


@dataclass(frozen=True)
class MemorySnapshot:
    total_kib: int
    used_kib: int
    available_kib: int
    used_percent: float


@dataclass(frozen=True)
class InterfaceCounter:
    name: str
    rx_bytes: int
    tx_bytes: int


@dataclass(frozen=True)
class ListeningPort:
    address: str
    port: int
    protocol: str
    process: str | None


_NET_LINE = re.compile(r"^\s*([^:]+):\s*(.*)$")
_INTERFACE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,15}$")
_PROCESS = re.compile(r'users:\(\("([^"]*)"')


def parse_cpu(stat_a: str, stat_b: str, loadavg: str) -> CpuSnapshot:
    utilization = _utilization(_cpu_fields(stat_a), _cpu_fields(stat_b))
    load_1, load_5, load_15 = _load_average(loadavg)
    return CpuSnapshot(utilization, load_1, load_5, load_15)


def parse_memory(text: str) -> MemorySnapshot:
    values: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        bits = rest.split()
        if not bits:
            continue
        try:
            values[key] = int(bits[0])
        except ValueError:
            raise ParseError from None
    if "MemTotal" not in values or values["MemTotal"] <= 0:
        raise ParseError
    total = values["MemTotal"]
    if "MemAvailable" in values:
        available = values["MemAvailable"]
    elif "MemFree" in values:
        available = values["MemFree"] + values.get("Buffers", 0) + values.get("Cached", 0)
    else:
        raise ParseError
    if available < 0:
        raise ParseError
    if available > total:
        available = total
    used = total - available
    return MemorySnapshot(total, used, available, used / total * 100)


def parse_netdev(text: str) -> list[InterfaceCounter]:
    counters = []
    for line in text.splitlines():
        match = _NET_LINE.match(line)
        if not match:
            continue
        name = match.group(1).strip()
        if not _INTERFACE_NAME.fullmatch(name):
            continue
        numbers = match.group(2).split()
        if len(numbers) < 9:
            continue
        try:
            rx_bytes = int(numbers[0])
            tx_bytes = int(numbers[8])
        except ValueError:
            continue
        if rx_bytes < 0 or tx_bytes < 0:
            continue
        counters.append(InterfaceCounter(name, rx_bytes, tx_bytes))
    return counters


def parse_sockets(text: str) -> list[ListeningPort]:
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        protocol = parts[0].lower()
        if protocol not in {"tcp", "udp"}:
            continue
        try:
            address, port = _split_endpoint(parts[4])
        except ValueError:
            continue
        process_match = _PROCESS.search(line)
        process = process_match.group(1) if process_match else None
        if process == "":
            process = None
        rows.append(ListeningPort(address, port, protocol, process))
    return rows


def _cpu_fields(text: str) -> list[int]:
    for line in text.splitlines():
        if line.startswith("cpu "):
            parts = line.split()[1:9]
            if len(parts) < 4:
                raise ParseError
            try:
                return [int(part) for part in parts]
            except ValueError:
                raise ParseError from None
    raise ParseError


def _utilization(first: list[int], second: list[int]) -> float:
    idle_a, total_a = _idle_and_total(first)
    idle_b, total_b = _idle_and_total(second)
    total_delta = total_b - total_a
    idle_delta = idle_b - idle_a
    if total_delta <= 0 or idle_delta < 0 or idle_delta > total_delta:
        raise ParseError
    return (total_delta - idle_delta) / total_delta * 100


def _idle_and_total(parts: list[int]) -> tuple[int, int]:
    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
    return idle, sum(parts)


def _load_average(text: str) -> tuple[float, float, float]:
    parts = text.split()
    if len(parts) < 3:
        raise ParseError
    try:
        load_1, load_5, load_15 = (float(part) for part in parts[:3])
    except ValueError:
        raise ParseError from None
    return load_1, load_5, load_15


def _split_endpoint(token: str) -> tuple[str, int]:
    if token.startswith("["):
        host, separator, port_text = token.rpartition(":")
        if not separator or not host.endswith("]"):
            raise ValueError
        address = host[1:-1]
    else:
        address, separator, port_text = token.rpartition(":")
        if not separator:
            raise ValueError
    port = int(port_text)
    if not address or not 0 <= port <= 65535:
        raise ValueError
    return address, port
