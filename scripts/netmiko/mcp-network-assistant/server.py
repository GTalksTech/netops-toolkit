"""MCP Network Assistant — Starter Kit
Read-only MCP server exposing Netmiko-driven tools to MCP-compatible clients.
"""
import logging
import re
import sys
from pathlib import Path

import yaml
from fastmcp import FastMCP
from netmiko import ConnectHandler

# Log to stderr only — stdout is reserved for JSON-RPC and any print() corrupts the stream.
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
log = logging.getLogger("mcp-net")

mcp = FastMCP("Network Assistant")

INVENTORY_PATH = Path(__file__).parent / "inventory.yaml"

# Whitelist enforcement for user-supplied commands
# Blocks anything containing 'run', 'secret', 'snmp', 'username', 'password', 'key' (read-only intent)
BLOCKED_TOKENS = re.compile(
    r"\b(run(?:ning)?|startup|secret|password|username|community|key|crypto)\b",
    re.IGNORECASE,
)

# Server-side redaction applied to outputs that come from running-config
REDACT_PATTERNS = [
    (re.compile(r"(secret \d \S+)", re.I), "secret <REDACTED>"),
    (re.compile(r"(password \d \S+)", re.I), "password <REDACTED>"),
    (re.compile(r"(community \S+)", re.I), "community <REDACTED>"),
    (re.compile(r"(md5 \d \S+)", re.I), "md5 <REDACTED>"),
    (re.compile(r"(key \d \S+)", re.I), "key <REDACTED>"),
]
# REDACT_PATTERNS = []  # Phase 5.2 demo: uncomment to override the list above and show leakage


def load_inventory() -> dict:
    with open(INVENTORY_PATH) as f:
        data = yaml.safe_load(f)
    defaults = data.get("defaults", {})
    out = {}
    for name, dev in data["devices"].items():
        merged = {**defaults, **dev}
        merged["host"] = merged.pop("host")
        out[name] = merged
    return out


def redact(text: str) -> str:
    for pat, replacement in REDACT_PATTERNS:
        text = pat.sub(replacement, text)
    return text


def device_params(name: str) -> dict:
    inv = load_inventory()
    if name not in inv:
        raise ValueError(f"Unknown device: {name}. Known: {list(inv.keys())}")
    d = inv[name]
    return {
        "device_type": d["device_type"],
        "host": d["host"],
        "username": d["username"],
        "password": d["password"],
        "port": d.get("port", 22),
    }


@mcp.tool
def list_devices() -> dict:
    """List all devices in the GTT home lab inventory.
    Use when the user asks about their home lab network. Do not use for general
    networking questions unrelated to the lab.
    """
    inv = load_inventory()
    return {
        name: {"host": d["host"], "description": d.get("description", "")}
        for name, d in inv.items()
    }


@mcp.tool
def get_device_status(device: str) -> dict:
    """Return a bundled status summary for a GTT home lab device: interfaces, neighbors,
    routes, and OSPF state. Read-only. Use when investigating live state on a lab device.
    """
    params = device_params(device)
    log.info(f"get_device_status: connecting to {device} ({params['host']})")
    with ConnectHandler(**params) as conn:
        ifaces = conn.send_command("show ip interface brief")
        ospf_neigh = conn.send_command("show ip ospf neighbor")
        routes = conn.send_command("show ip route")
        cdp = conn.send_command("show cdp neighbors")
    return {
        "device": device,
        "interfaces": ifaces,
        "ospf_neighbors": ospf_neigh,
        "routes": routes,
        "cdp_neighbors": cdp,
    }


@mcp.tool
def run_show_command(device: str, command: str) -> str:
    """Run a read-only show command on a GTT home lab device.
    Blocks commands containing run, startup, secret, password, etc.
    Only use for lab devices listed in the inventory.
    """
    if BLOCKED_TOKENS.search(command):
        return (
            f"BLOCKED: command '{command}' contains a token on the read-only whitelist "
            f"blocklist (run/startup/secret/password/community/key/crypto). "
            f"Use find_in_config() or compare_running_to_startup() for config inspection."
        )
    if not command.lower().startswith("show "):
        return f"BLOCKED: only 'show ...' commands are allowed via this tool."
    params = device_params(device)
    log.info(f"run_show_command: {device} -> {command}")
    with ConnectHandler(**params) as conn:
        out = conn.send_command(command)
    return out


@mcp.tool
def find_in_config(device: str, pattern: str) -> str:
    """Search a GTT home lab device's running-config for a pattern. Server-side redaction applied.
    Use when the user wants to inspect specific config sections on a lab device.
    """
    params = device_params(device)
    log.info(f"find_in_config: {device} -> /{pattern}/")
    with ConnectHandler(**params) as conn:
        running = conn.send_command("show running-config")
    redacted = redact(running)
    matches = [line for line in redacted.splitlines() if re.search(pattern, line, re.I)]
    if not matches:
        return f"No matches for pattern '{pattern}' in {device}'s running-config."
    return "\n".join(matches)


@mcp.tool
def compare_running_to_startup(device: str) -> str:
    """Diff running-config vs startup-config on a GTT home lab device to detect unsaved drift.
    Server-side redaction applied.
    """
    params = device_params(device)
    log.info(f"compare_running_to_startup: {device}")
    with ConnectHandler(**params) as conn:
        running = conn.send_command("show running-config")
        startup = conn.send_command("show startup-config")
    running = redact(running).splitlines()
    startup = redact(startup).splitlines()
    only_running = [l for l in running if l not in startup]
    only_startup = [l for l in startup if l not in running]
    out = []
    if only_running:
        out.append("=== Lines in running-config but not startup-config ===")
        out.extend(only_running)
    if only_startup:
        out.append("=== Lines in startup-config but not running-config ===")
        out.extend(only_startup)
    if not out:
        return "No drift detected — running-config matches startup-config."
    return "\n".join(out)


if __name__ == "__main__":
    mcp.run()
