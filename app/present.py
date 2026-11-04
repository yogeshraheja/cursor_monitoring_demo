from app.collector import ERROR_TEXT, Snapshot


def present_snapshot(snapshot: Snapshot) -> dict:
    if not snapshot.ok:
        return {
            "error": ERROR_TEXT.get(snapshot.category or "", ERROR_TEXT["malformed"]),
            "cpu": None,
            "memory": None,
            "interfaces": [],
            "ports": [],
        }
    cpu = snapshot.cpu
    memory = snapshot.memory
    return {
        "error": None,
        "cpu": {
            "utilization": f"{cpu.utilization_percent:.1f}%",
            "load_1": f"{cpu.load_1:.2f}",
            "load_5": f"{cpu.load_5:.2f}",
            "load_15": f"{cpu.load_15:.2f}",
        },
        "memory": {
            "total": _format_kib(memory.total_kib),
            "used": _format_kib(memory.used_kib),
            "available": _format_kib(memory.available_kib),
            "used_percent": f"{memory.used_percent:.1f}%",
        },
        "interfaces": [
            {
                "name": item.name,
                "rx_bytes": str(item.rx_bytes),
                "tx_bytes": str(item.tx_bytes),
                "rx_rate": _format_rate(item.rx_bps),
                "tx_rate": _format_rate(item.tx_bps),
            }
            for item in snapshot.interfaces or []
        ],
        "ports": [
            {
                "address": item.address,
                "port": str(item.port),
                "protocol": item.protocol,
                "process": item.process or "",
            }
            for item in snapshot.ports or []
        ],
    }


def _format_kib(kib: int) -> str:
    gib = 1024 * 1024
    if kib >= gib and kib % gib == 0:
        return f"{kib // gib} GiB"
    if kib >= 1024:
        mib = kib / 1024
        if mib.is_integer():
            return f"{int(mib)} MiB"
        return f"{mib:.1f} MiB"
    return f"{kib} KiB"


def _format_rate(bps: float | None) -> str | None:
    if bps is None:
        return None
    return f"{round(bps)} B/s"
