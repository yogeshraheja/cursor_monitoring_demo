from dataclasses import dataclass

from app.parsers import InterfaceCounter


@dataclass(frozen=True)
class InterfaceView:
    name: str
    rx_bytes: int
    tx_bytes: int
    rx_bps: float | None
    tx_bps: float | None


class RateStore:
    """Previous counters for this process only. Nothing is written to disk."""

    def __init__(self) -> None:
        self._previous: dict[str, tuple[float, dict[str, InterfaceCounter]]] = {}

    def apply(self, server_id: str, counters: list[InterfaceCounter], now: float) -> list[InterfaceView]:
        prior = self._previous.get(server_id)
        current = {item.name: item for item in counters}
        self._previous[server_id] = (now, current)
        views = []
        for item in counters:
            rx_bps = None
            tx_bps = None
            if prior is not None:
                then, old = prior
                elapsed = now - then
                previous = old.get(item.name)
                if previous is not None and elapsed > 0:
                    rx_delta = item.rx_bytes - previous.rx_bytes
                    tx_delta = item.tx_bytes - previous.tx_bytes
                    if rx_delta >= 0:
                        rx_bps = rx_delta / elapsed
                    if tx_delta >= 0:
                        tx_bps = tx_delta / elapsed
            views.append(InterfaceView(item.name, item.rx_bytes, item.tx_bytes, rx_bps, tx_bps))
        return views

    def drop(self, server_id: str) -> None:
        self._previous.pop(server_id, None)
