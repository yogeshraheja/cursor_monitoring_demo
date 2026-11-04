def command_outputs(rx=1000, tx=2000, process="sshd"):
    stat_a = "cpu  100 0 0 100 0 0 0 0 0 0\n"
    stat_b = "cpu  200 0 0 200 0 0 0 0 0 0\n"
    load = "0.40 0.20 0.10 1/20 99\n"
    memory = (
        "MemTotal:       2048000 kB\n"
        "MemFree:         400000 kB\n"
        "MemAvailable:   1024000 kB\n"
        "Buffers:          10000 kB\n"
        "Cached:          200000 kB\n"
    )
    network = (
        "Inter-|   Receive                                                |  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed\n"
        "    lo: 10 0 0 0 0 0 0 0 20 0 0 0 0 0 0 0\n"
        f"  eth0: {rx} 0 0 0 0 0 0 0 {tx} 0 0 0 0 0 0 0\n"
        "  bad name: 1 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0\n"
        "  ../../x: 4 0 0 0 0 0 0 0 4 0 0 0 0 0 0 0\n"
    )
    if process is None:
        ssh_line = "tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"
    else:
        ssh_line = f'tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("{process}",pid=9,fd=3))\n'
    sockets = ssh_line + "udp UNCONN 0 0 127.0.0.1:323 0.0.0.0:*\n"
    return [load, stat_a, stat_b, memory, network, sockets]
