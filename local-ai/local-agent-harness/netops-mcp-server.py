# ============================================================
# Script:       netops-mcp-server.py
# Purpose:      Network-tools MCP server (stdio) for driving a three-device
#               lab from a local agent harness (Goose, Bionic). Three read
#               tools (cached config, live `show`, ping) and one write tool
#               (set an interface description), so the same question can be
#               asked of the cached config and of the running device.
# Usage:        Registered as a harness extension: a Goose command-line
#               extension, or a Bionic "On this computer" MCP server. The
#               harness starts it; there is no daemon and no port.
#               Handshake test (hold the pipe open or it exits on EOF):
#               see quickstart-goose-ollama.md, Pre-check step 6.
# Dependencies: fastmcp, netmiko (pip install -r requirements.txt), stdlib
# Author:       G Talks Tech
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Public by design. All IPs are REAL lab IPs (RFC1918) --
#               the lab is meant to be replicated, never use placeholders.
#               Lab creds are public by design so the server runs against
#               the matching CML topology with zero guessing. They are read
#               from env vars so the same file works against a different
#               lab without editing.
#               NO getpass: the harness starts this as a subprocess with no
#               terminal attached, so an interactive prompt hangs or throws.
#               Credentials come from the extension's env-var field.
#               READ tools: cached file, ping, `show`. ONE WRITE tool,
#               set_interface_description. It is the only thing here that
#               changes a device, it writes running-config only, and a
#               description is about the most reversible change there is.
#               The .cfg files must live NEXT TO this script: ARTIFACTS
#               resolves from __file__, not the working directory.
# ============================================================

import os
import pathlib
import re
import subprocess

from fastmcp import FastMCP

mcp = FastMCP("netops-local")

ARTIFACTS = pathlib.Path(__file__).parent
KNOWN_DEVICES = ["core-rtr-01", "edge-rtr-01", "access-sw-01"]

# Real lab addressing. core-rtr-01 and access-sw-01 sit on the LAN and are
# reachable directly. edge-rtr-01 is a loopback reached by routing through
# core-rtr-01, so the machine running this server needs a route to 10.0.0.2
# via 192.168.1.250.
DEVICE_HOSTS = {
    "core-rtr-01": "192.168.1.250",
    "edge-rtr-01": "10.0.0.2",
    "access-sw-01": "192.168.1.251",
}

LAB_USER = os.environ.get("NETOPS_USER", "admin")
LAB_PASS = os.environ.get("NETOPS_PASS", "cisco123")


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
    """List EVERY interface from a device's CACHED running-config, each with
    its IPv4 address or an explicit 'no ip address' / 'shutdown' flag, plus the
    config's own 'Last configuration change' stamp. This reads a config file
    captured earlier and may be out of date; for the running device use
    show_interfaces_live. Valid devices: core-rtr-01, edge-rtr-01, access-sw-01."""
    # Returns EVERY interface, not just the addressed ones. An earlier version
    # silently dropped interfaces with no IP address, and the model filled the
    # gap with guesses: it got Ethernet0/3 right in 2 of 5 runs. Complete
    # output plus the capture's own timestamp closed the gap.
    if device not in KNOWN_DEVICES:
        return f"unknown device '{device}'. Valid: {', '.join(KNOWN_DEVICES)}"
    cfg = (ARTIFACTS / f"{device}.cfg").read_text()
    m = re.search(r"^! Last configuration change at (.+)$", cfg, re.M)
    stamp = m.group(1).strip() if m else "unknown"

    rows = []
    current = None
    addr = None
    shut = False

    def flush():
        if current is None:
            return
        if addr:
            rows.append(f"{current}: {addr}" + (" (shutdown)" if shut else ""))
        else:
            rows.append(f"{current}: no ip address" + (", shutdown" if shut else ""))

    for line in cfg.splitlines():
        m = re.match(r"^interface (\S+)", line)
        if m:
            flush()
            current, addr, shut = m.group(1), None, False
            continue
        if current is None:
            continue
        if line.startswith("!"):
            flush()
            current = None
            continue
        m = re.match(r"^ ip address (\S+) (\S+)", line)
        if m:
            addr = f"{m.group(1)} {m.group(2)}"
            continue
        if re.match(r"^ shutdown\s*$", line):
            shut = True
    flush()

    if not rows:
        return f"{device} CACHED config (last configuration change per file: {stamp})\nno interfaces found"
    addressed = sum(1 for r in rows if ": no ip address" not in r)
    header = f"{device} CACHED config (last configuration change per file: {stamp})"
    footer = (
        f"{len(rows)} interfaces in cached config, {addressed} with IPv4 addresses. "
        "Interfaces marked 'no ip address' EXIST in the config but have no IPv4."
    )
    return "\n".join([header, *rows, footer])


@mcp.tool
def show_interfaces_live(device: str) -> str:
    """SSH to a device and return LIVE 'show ip interface brief' output.
    This reads the running device right now, unlike list_interfaces which
    reads a cached file. Read-only: issues a show command only.
    Valid devices: core-rtr-01, edge-rtr-01, access-sw-01."""
    if device not in KNOWN_DEVICES:
        return f"unknown device '{device}'. Valid: {', '.join(KNOWN_DEVICES)}"

    try:
        from netmiko import ConnectHandler
    except ImportError:
        return "netmiko is not installed in the interpreter running this server"

    host = DEVICE_HOSTS[device]
    try:
        conn = ConnectHandler(
            device_type="cisco_ios",
            host=host,
            username=LAB_USER,
            password=LAB_PASS,
            conn_timeout=15,
            banner_timeout=15,
            fast_cli=False,
        )
    except Exception as exc:
        return f"could not connect to {device} ({host}): {type(exc).__name__}: {exc}"

    try:
        out = conn.send_command("show ip interface brief", read_timeout=30)
    except Exception as exc:
        return f"connected to {device} but command failed: {type(exc).__name__}: {exc}"
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass

    return out.strip() or "no output"


# Honest annotation: this tool writes, so it says so. Goose in smart_approve
# lets a tool labeled readOnlyHint: True run without asking, unless you have
# set your own rule for it. Never label a write as read-only.
@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False})
def set_interface_description(device: str, interface: str, text: str) -> str:
    """CHANGE the running config: set (or with empty text, remove) the
    description on one interface of a device, then read it back. This WRITES
    to the device. Valid devices: core-rtr-01, edge-rtr-01, access-sw-01.
    interface is the IOS name, e.g. Ethernet0/3. Returns the interface config
    before and after the change."""
    # The one write tool. Deliberately harmless, visible, and reversible: a
    # description changes nothing about forwarding.
    if device not in KNOWN_DEVICES:
        return f"unknown device '{device}'. Valid: {', '.join(KNOWN_DEVICES)}"
    if not re.fullmatch(r"[A-Za-z]+[0-9]+(/[0-9]+)*", interface):
        return f"'{interface}' is not an interface name I will touch (expected e.g. Ethernet0/3)"
    text = text.strip()
    if "\n" in text or "\r" in text:
        return "description text must be a single line"

    try:
        from netmiko import ConnectHandler
    except ImportError:
        return "netmiko is not installed in the interpreter running this server"

    host = DEVICE_HOSTS[device]
    try:
        conn = ConnectHandler(
            device_type="cisco_ios",
            host=host,
            username=LAB_USER,
            password=LAB_PASS,
            secret=LAB_PASS,
            conn_timeout=15,
            banner_timeout=15,
            fast_cli=False,
        )
    except Exception as exc:
        return f"could not connect to {device} ({host}): {type(exc).__name__}: {exc}"

    show = f"show running-config interface {interface}"
    try:
        conn.enable()
        before = conn.send_command(show, read_timeout=30)
        cmds = [f"interface {interface}", f"description {text}" if text else "no description"]
        applied = conn.send_config_set(cmds, read_timeout=30)
        after = conn.send_command(show, read_timeout=30)
    except Exception as exc:
        return f"connected to {device} but the change failed: {type(exc).__name__}: {exc}"
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass

    if "Invalid input" in applied or "% " in applied:
        return f"{device}: IOS rejected the change:\n{applied.strip()}"
    action = f"set description to '{text}'" if text else "removed the description"
    return "\n".join([
        f"{device} {interface}: {action} (running-config only, not saved to startup-config)",
        "--- BEFORE ---", before.strip(),
        "--- AFTER ---", after.strip(),
    ])


if __name__ == "__main__":
    mcp.run()
