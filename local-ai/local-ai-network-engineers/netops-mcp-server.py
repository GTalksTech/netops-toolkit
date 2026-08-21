# ============================================================
# Script:       netops-mcp-server.py
# Purpose:      Minimal network-tools MCP server (stdio) -- lets a LOCAL
#               model in LM Studio drive real (read-only) network tools
#               behind the host's confirmation dialog.
# Usage:        Registered in LM Studio's mcp.json (see README.md);
#               manual test:
#               python netops-mcp-server.py
# Dependencies: fastmcp (pip install -r requirements.txt), stdlib subprocess/re/pathlib
# Author:       G Talks Tech
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Public by design. All IPs are REAL lab IPs (RFC1918) --
#               the lab is meant to be replicated, never use placeholders.
#               Never hardcode credentials. Use getpass for passwords;
#               never accept a --password argument.
#               READ-ONLY tools by design: ping + parse cached configs.
#               No config-changing tool exists in this server on purpose.
# ============================================================

import pathlib
import re
import subprocess

from fastmcp import FastMCP

mcp = FastMCP("netops-local")

ARTIFACTS = pathlib.Path(__file__).parent
KNOWN_DEVICES = ["core-rtr-01", "edge-rtr-01", "access-sw-01"]


@mcp.tool
def ping_host(host: str) -> str:
    """Ping a host twice (read-only reachability check). Returns raw ping output."""
    proc = subprocess.run(
        ["ping", "-c", "2", "-W", "2000", host],
        capture_output=True,
        text=True,
        timeout=15,
    )
    out = (proc.stdout + proc.stderr).strip()
    return out or "no output"


@mcp.tool
def list_interfaces(device: str) -> str:
    """List interfaces with IPv4 addresses from a device's cached running-config.
    Valid devices: core-rtr-01, edge-rtr-01, access-sw-01."""
    if device not in KNOWN_DEVICES:
        return f"unknown device '{device}'. Valid: {', '.join(KNOWN_DEVICES)}"
    cfg = (ARTIFACTS / f"{device}.cfg").read_text()
    rows = []
    current = None
    for line in cfg.splitlines():
        m = re.match(r"^interface (\S+)", line)
        if m:
            current = m.group(1)
        m = re.match(r"^ ip address (\S+) (\S+)", line)
        if m and current:
            rows.append(f"{current}: {m.group(1)} {m.group(2)}")
            current = None
    return "\n".join(rows) or "no addressed interfaces found"


if __name__ == "__main__":
    mcp.run()
