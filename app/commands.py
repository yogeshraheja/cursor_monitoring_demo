"""Fixed read commands. Nothing from a form is concatenated into these strings."""

LOADAVG = "cat /proc/loadavg"
STAT = "cat /proc/stat"
MEMINFO = "cat /proc/meminfo"
NETDEV = "cat /proc/net/dev"
SOCKETS = "ss -H -lnptu"

READ_COMMANDS = (LOADAVG, STAT, STAT, MEMINFO, NETDEV, SOCKETS)
ALLOWED_COMMANDS = frozenset(READ_COMMANDS)
