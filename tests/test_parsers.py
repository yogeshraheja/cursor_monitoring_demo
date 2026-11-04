import pytest

from app.parsers import (
    ParseError,
    parse_cpu,
    parse_memory,
    parse_netdev,
    parse_sockets,
)
from app.rates import RateStore
from app.parsers import InterfaceCounter
from tests.samples import command_outputs


def test_cpu_and_memory_normal_sample():
    outputs = command_outputs()
    cpu = parse_cpu(outputs[1], outputs[2], outputs[0])
    memory = parse_memory(outputs[3])
    assert cpu.utilization_percent == 50
    assert (cpu.load_1, cpu.load_5, cpu.load_15) == (0.4, 0.2, 0.1)
    assert memory.total_kib == 2048000
    assert memory.used_kib == 1024000
    assert memory.available_kib == 1024000
    assert memory.used_percent == 50


def test_cpu_and_memory_malformed_sample():
    with pytest.raises(ParseError):
        parse_cpu("garbage", "cpu 1 2", "nope")
    with pytest.raises(ParseError):
        parse_memory("MemFree: 10 kB\nBuffers: 1 kB\n")


def test_interface_names_must_match_the_safe_pattern():
    names = [item.name for item in parse_netdev(command_outputs()[4])]
    assert names == ["lo", "eth0"]


def test_first_sample_has_no_rate_and_second_sample_has_bytes_per_second(tmp_path):
    before = {path.name for path in tmp_path.iterdir()}
    store = RateStore()
    first = store.apply("server", [InterfaceCounter("eth0", 1000, 2000)], 1000)
    assert first[0].rx_bps is None
    assert first[0].tx_bps is None
    second = store.apply("server", [InterfaceCounter("eth0", 3000, 6000)], 1002)
    assert second[0].rx_bps == 1000
    assert second[0].tx_bps == 2000
    assert {path.name for path in tmp_path.iterdir()} == before


def test_listening_port_with_and_without_process_name():
    with_process = parse_sockets(command_outputs(process="sshd")[5])
    assert with_process[0].process == "sshd"
    assert with_process[0].port == 22
    assert with_process[0].protocol == "tcp"
    assert with_process[1].process is None
    assert with_process[1].protocol == "udp"
    without_process = parse_sockets(command_outputs(process=None)[5])
    assert without_process[0].process is None
    assert without_process[0].address == "0.0.0.0"
