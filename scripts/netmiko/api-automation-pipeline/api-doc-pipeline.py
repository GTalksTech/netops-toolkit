# ============================================================
# Script:       api-doc-pipeline.py
# Purpose:      Automated network documentation pipeline --
#               SSH to finished runbook in one command
# Usage:        python api-doc-pipeline.py
#               python api-doc-pipeline.py --provider openai --diagram
# Dependencies: netmiko, pyyaml, anthropic/openai/google-genai
# Author:       G Talks Tech
# Episode:      EP005-L-api-automation-pipeline
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Copy inventory-example.yml to inventory.yml and
#               update with your device IPs before running.
#               Set your API key as an environment variable.
# ============================================================

import os
import re
import sys
import json
import getpass
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from collections import OrderedDict
from xml.dom import minidom

import yaml

try:
    from netmiko import ConnectHandler
except ImportError:
    print("[ERROR] netmiko package not installed.", file=sys.stderr)
    print("  Run: pip install netmiko", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# NL constant -- avoids escape sequence issues in tooling
# ---------------------------------------------------------------------------
NL = chr(10)

# ---------------------------------------------------------------------------
# AI provider configuration
# ---------------------------------------------------------------------------
PROVIDERS = {
    "claude": {
        "env_var": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-6",
        "signup_url": "https://console.anthropic.com/",
        "pip_package": "anthropic",
    },
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "default_model": "gpt-5.4-mini",
        "signup_url": "https://platform.openai.com/",
        "pip_package": "openai",
    },
    "gemini": {
        "env_var": "GEMINI_API_KEY",
        "default_model": "gemini-3-flash",
        "signup_url": "https://aistudio.google.com/",
        "pip_package": "google-genai",
    },
}

# ---------------------------------------------------------------------------
# Context limits (approximate token counts per model)
# ---------------------------------------------------------------------------
CONTEXT_LIMITS = {
    "claude-sonnet-4-6": 200000,
    "claude-opus-4-6": 200000,
    "gpt-5.4": 1000000,
    "gpt-5.4-mini": 400000,
    "gpt-5.4-nano": 128000,
    "gpt-4.1": 1047576,
    "gemini-3-flash": 1048576,
    "gemini-3.1-pro-preview": 1048576,
    "gemini-2.5-flash": 1048576,
    "gemini-2.5-pro": 1048576,
}

# ---------------------------------------------------------------------------
# Default command sets (copied from EP004 01-collector.py)
# ---------------------------------------------------------------------------
DEFAULT_ROUTER_COMMANDS = [
    "show version",
    "show inventory",
    "show ip interface brief",
    "show interfaces",
    "show running-config",
    "show ip route",
    "show ip protocols",
    "show ip ospf neighbor",
    "show ip ospf interface brief",
    "show ip ospf database",
    "show ip arp",
    "show cdp neighbors detail",
    "show lldp neighbors detail",
    "show ntp status",
    "show logging",
]

DEFAULT_SWITCH_COMMANDS = [
    "show version",
    "show inventory",
    "show ip interface brief",
    "show interfaces",
    "show interfaces status",
    "show running-config",
    "show vlan brief",
    "show interfaces trunk",
    "show spanning-tree",
    "show mac address-table",
    "show vtp status",
    "show etherchannel summary",
    "show ip arp",
    "show cdp neighbors detail",
    "show lldp neighbors detail",
    "show ntp status",
    "show logging",
]

DEFAULT_COMMANDS_BY_ROLE = {
    "router": DEFAULT_ROUTER_COMMANDS,
    "switch": DEFAULT_SWITCH_COMMANDS,
}

# ---------------------------------------------------------------------------
# Credential patterns (ALWAYS applied -- copied from EP004 02-redactor.py)
# ---------------------------------------------------------------------------
CREDENTIAL_PATTERNS = [
    re.compile(r'(?i)(enable\s+secret(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(enable\s+password(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(username\s+\S+(?:\s+privilege\s+\d+)?\s+secret(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(username\s+\S+(?:\s+privilege\s+\d+)?\s+password(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?im)(^\s+password(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(snmp-server\s+community)\s+(\S+)'),
    re.compile(r'(?i)(tacacs-server\s+key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(radius-server\s+key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(ip\s+ospf\s+authentication-key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(standby\s+\d+\s+authentication)\s+(\S+)'),
    re.compile(r'(?i)(key-string(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(crypto\s+isakmp\s+key(?:\s+\d+)?)\s+(\S+)'),
    re.compile(r'(?i)(neighbor\s+\S+\s+password(?:\s+\d+)?)\s+(\S+)'),
]

# ---------------------------------------------------------------------------
# IPv4 and MAC address regexes (copied from EP004 02-redactor.py)
# ---------------------------------------------------------------------------
IPV4_RE = re.compile(
    r'(?<![.\d])'
    r'((?:25[0-5]|2[0-4]\d|1?\d{1,2})\.(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.'
    r'(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.(?:25[0-5]|2[0-4]\d|1?\d{1,2}))'
    r'(?![.\d])'
)

MAC_CISCO_RE = re.compile(
    r'(?<![0-9a-fA-F\.])'
    r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})'
    r'(?![0-9a-fA-F\.])'
)
MAC_COLON_RE = re.compile(
    r'(?<![0-9a-fA-F:])'
    r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:'
    r'[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})'
    r'(?![0-9a-fA-F:])'
)

# ---------------------------------------------------------------------------
# Prompt template (copied from EP004 03-prompt-assembler.py)
# ---------------------------------------------------------------------------
PROMPT_HEADER = (
    "You are a network documentation engineer producing an operational runbook "
    "for a senior network engineer. This runbook must be immediately usable "
    "during incidents and change planning -- not a training document." + NL + NL +
    "CRITICAL: The device output contains sanitized placeholder tokens. "
    "You MUST copy every placeholder into your output exactly as written -- same "
    "angle brackets, same capitalization, same underscore format. "
    "Do NOT expand, paraphrase, resolve, or reformat them in any way. "
    "Treat them as opaque string literals." + NL + NL +
    "Placeholder types you may encounter:" + NL +
    "- <IP_1>, <IP_2> ... (IP addresses)" + NL +
    "- <HOSTNAME_1>, <HOSTNAME_2> ... (device hostnames)" + NL +
    "- <DOMAIN_REDACTED> (domain name)" + NL +
    "- <MAC_1>, <MAC_2> ... (MAC addresses)" + NL +
    "- <SERIAL_1>, <SERIAL_2> ... (serial numbers and board IDs)" + NL +
    "- <USER_1>, <USER_2> ... (usernames)" + NL +
    "- <VERSION_1>, <VERSION_2> ... (IOS versions and image filenames)" + NL +
    "- <DESCRIPTION_1>, <DESCRIPTION_2> ... (interface descriptions)" + NL +
    "- <VLAN_NAME_1>, <VLAN_NAME_2> ... (VLAN names)" + NL +
    "- <CERTIFICATE_REDACTED> (stripped certificate blocks)" + NL +
    "- <TIMESTAMP>, <UPTIME_REDACTED> (timestamps and uptime)" + NL +
    "- <REDACTED> (credentials)" + NL + NL +
    "Generate a Markdown runbook with these sections in this order:" + NL +
    "1. ## Topology Overview -- prose paragraph + device role table "
    "(Device | Role | Connected To)" + NL +
    "2. ## Device Inventory -- table: Hostname | Model | IOS Version | Serial" + NL +
    "3. ## IP Addressing -- table per device: Interface | IP/Prefix | Description | Status" + NL +
    "4. ## Routing Summary -- one subsection per device: protocol, neighbors table, "
    "advertised networks, passive interfaces" + NL +
    "5. ## Layer 2 Summary -- only for devices with L2 output: VLAN table, "
    "trunk table (Port | Allowed VLANs | Native VLAN), STP root per VLAN" + NL +
    "6. ## Management Services -- NTP source/server, SSH version, syslog targets, "
    "AAA method if present. Table format." + NL +
    "7. ## Findings and Flags -- numbered list. Flag mismatches, missing configs, "
    "suboptimal settings based on what is visible in the output. "
    "If values are redacted, note what could not be assessed. "
    "If nothing noteworthy, write 'None identified.'" + NL + NL +
    "Formatting rules:" + NL +
    "- Use Markdown tables for all structured data. No bullet lists where a table fits." + NL +
    "- Use H3 (###) for per-device subsections within any H2 section." + NL +
    "- Use only values from the device output. No assumptions or invented values." + NL +
    "- If a value is not present in the output, write 'Not found in output'." + NL +
    "- Place placeholder tokens directly into table cells and prose. "
    "They will be restored to real values after generation." + NL + NL +
    "--- DEVICE OUTPUT START ---" + NL
)
PROMPT_FOOTER = (
    NL + "--- DEVICE OUTPUT END ---" + NL + NL +
    "Generate the runbook now." + NL
)

# ---------------------------------------------------------------------------
# Draw.io style constants (copied from EP004 05-diagram-generator.py)
# ---------------------------------------------------------------------------
ROUTER_STYLE = (
    "verticalLabelPosition=bottom;html=1;verticalAlign=top;"
    "aspect=fixed;align=center;pointerEvents=1;"
    "shape=mxgraph.cisco19.rect;prIcon=router;"
    "fillColor=#FAFAFA;strokeColor=#005073;"
)

SWITCH_STYLE = (
    "verticalLabelPosition=bottom;html=1;verticalAlign=top;"
    "aspect=fixed;align=center;pointerEvents=1;"
    "shape=mxgraph.cisco19.rect;prIcon=l2_switch;"
    "fillColor=#FAFAFA;strokeColor=#005073;"
)

EDGE_STYLE = (
    "endFill=0;endArrow=none;html=1;rounded=0;"
    "strokeColor=#005073;fontSize=10;"
)

EDGE_LABEL_STYLE = (
    "edgeLabel;html=1;align=center;verticalAlign=middle;"
    "resizable=0;points=[];fontSize=10;"
)

NODE_W = 50
NODE_H = 50
H_SPACING = 200       # horizontal gap between devices in the same tier
V_SPACING = 180       # vertical gap between tiers
LEFT_MARGIN = 100
TOP_MARGIN = 80

# Tier order: edge at top, core in middle, access at bottom
TIER_ORDER = {"edge": 0, "core": 1, "access": 2, "other": 3}

# ---------------------------------------------------------------------------
# IPv4 and redaction helpers
# ---------------------------------------------------------------------------

def _ip_to_int(ip_str):
    val = 0
    for part in ip_str.split('.'):
        val = (val << 8) | int(part)
    return val


def is_mask(ip_str):
    """Return True if ip_str is a subnet mask or wildcard mask."""
    try:
        val = _ip_to_int(ip_str)
        if val == 0 or val == 0xFFFFFFFF:
            return True
        is_subnet = (val | (val - 1)) == 0xFFFFFFFF
        is_wildcard = (val & (val + 1)) == 0
        return is_subnet or is_wildcard
    except Exception:
        return False


def redact_credentials(text):
    """Apply all credential patterns. Returns (redacted_text, match_count)."""
    total = 0
    for pattern in CREDENTIAL_PATTERNS:
        text, n = pattern.subn(lambda m: m.group(1) + ' <REDACTED>', text)
        total += n
    return text, total


def redact_ips(text, existing_map=None, start_counter=1):
    """Replace each unique IPv4 address with <IP_N>. Masks are preserved."""
    ip_map = OrderedDict(existing_map or {})
    counter = [start_counter]

    def replace(match):
        ip = match.group(1)
        if is_mask(ip):
            return match.group(0)
        if ip not in ip_map:
            ip_map[ip] = '<IP_' + str(counter[0]) + '>'
            counter[0] += 1
        return ip_map[ip]

    redacted = IPV4_RE.sub(replace, text)
    return redacted, ip_map


def redact_hostnames(text, existing_map=None, start_counter=1):
    """Detect hostnames from config and replace all occurrences."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    hostnames = list(dict.fromkeys(re.findall(r'(?im)^hostname\s+(\S+)', text)))
    for h in hostnames:
        if h not in mapping:
            mapping[h] = '<HOSTNAME_' + str(counter[0]) + '>'
            counter[0] += 1

    domain_match = re.search(r'(?im)^ip\s+domain[-\s]name\s+(\S+)', text)
    if domain_match:
        domain = domain_match.group(1)
        if domain not in mapping:
            mapping[domain] = '<DOMAIN_REDACTED>'

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping


def redact_macs(text, existing_map=None, start_counter=1):
    """Replace MAC addresses with <MAC_N> placeholders."""
    mac_map = OrderedDict(existing_map or {})
    counter = [start_counter]

    def replace_mac(match):
        mac = match.group(1)
        if mac not in mac_map:
            mac_map[mac] = '<MAC_' + str(counter[0]) + '>'
            counter[0] += 1
        return mac_map[mac]

    text = MAC_CISCO_RE.sub(replace_mac, text)
    text = MAC_COLON_RE.sub(replace_mac, text)
    return text, mac_map


def redact_serials(text, existing_map=None, start_counter=1):
    """Replace serial numbers, processor board IDs with <SERIAL_N>."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    for m in re.finditer(r'Processor board ID\s+(\S+)', text):
        val = m.group(1)
        if val not in mapping:
            mapping[val] = '<SERIAL_' + str(counter[0]) + '>'
            counter[0] += 1

    for m in re.finditer(r'SN:\s*(\S+)', text):
        val = m.group(1)
        if val not in mapping:
            mapping[val] = '<SERIAL_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping


def redact_usernames(text, existing_map=None, start_counter=1):
    """Detect usernames from config/logs and replace all occurrences."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    config_users = re.findall(r'(?im)^username\s+(\S+)', text)
    log_users = re.findall(r'\[user:\s*(\S+?)\]', text)
    by_users = re.findall(r'\bby\s+(\S+)\s+on\s+', text)

    all_users = list(dict.fromkeys(config_users + log_users + by_users))
    for user in all_users:
        if user not in mapping:
            mapping[user] = '<USER_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = re.sub(r'\b' + re.escape(original) + r'\b', mapping[original], text)

    return text, mapping


def redact_certificates(text):
    """Strip certificate blocks and hex material. Not mapped (no restore)."""
    text = re.sub(
        r'crypto pki certificate chain\s+\S+.*?quit',
        '<CERTIFICATE_REDACTED>',
        text,
        flags=re.DOTALL
    )
    text = re.sub(
        r'(?m)^\s+certificate (?:self-signed )?\S+\s*\n(?:\s+[0-9A-Fa-f ]+\n)+\s+quit',
        ' <CERTIFICATE_REDACTED>',
        text
    )
    return text


def redact_timestamps(text):
    """Replace timestamps with static placeholder. Not mapped (no restore)."""
    text = re.sub(
        r'\*?[A-Z][a-z]{2}\s+\d{1,2}\s+\d{1,2}:\d{2}:\d{2}\.\d+',
        '<TIMESTAMP>',
        text
    )
    text = re.sub(
        r'\d{1,2}:\d{2}:\d{2}\s+\S+\s+\S{3}\s+\S{3}\s+\d{1,2}\s+\d{4}',
        '<TIMESTAMP>',
        text
    )
    text = re.sub(
        r'\d{4}-\d{2}-\d{2}[_ ]\d{2}:?\d{2}:?\d{2}',
        '<TIMESTAMP>',
        text
    )
    text = re.sub(
        r'(uptime is\s+).+',
        r'\1<UPTIME_REDACTED>',
        text
    )
    text = re.sub(
        r'(Last configuration change at\s+).+',
        r'\1<TIMESTAMP>',
        text
    )
    text = re.sub(
        r'(Configuration last modified by\s+).+',
        r'\1<TIMESTAMP>',
        text
    )
    return text


def redact_versions(text, existing_map=None, start_counter=1):
    """Replace IOS version strings and image filenames with placeholders."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    for m in re.finditer(r'Version\s+(\d+\.\d+\.\d+[a-zA-Z0-9_.]*)', text):
        ver = m.group(1)
        if ver not in mapping:
            mapping[ver] = '<VERSION_' + str(counter[0]) + '>'
            counter[0] += 1

    for m in re.finditer(r'System image file is "(\S+)"', text):
        img = m.group(1)
        if img not in mapping:
            mapping[img] = '<VERSION_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping


def redact_descriptions(text, existing_map=None, start_counter=1):
    """Replace interface description values with <DESCRIPTION_N>."""
    mapping = dict(existing_map or {})
    counter = [start_counter]

    for m in re.finditer(r'(?im)^(\s+description\s+)(.+)$', text):
        desc = m.group(2).strip()
        if desc and desc not in mapping:
            mapping[desc] = '<DESCRIPTION_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(original, mapping[original])

    return text, mapping


def redact_vlan_names(text, existing_map=None, start_counter=1):
    """Replace VLAN names with <VLAN_NAME_N>."""
    mapping = dict(existing_map or {})
    counter = [start_counter]
    skip_names = {'default', 'fddi-default', 'token-ring-default',
                  'fddinet-default', 'trnet-default'}

    for m in re.finditer(
        r'(?m)^(\d{1,4})\s+(.+?)\s{2,}(?:active|suspended|act/unsup|act/lshut)',
        text
    ):
        name = m.group(2).strip()
        if name and name.lower() not in skip_names and name not in mapping:
            mapping[name] = '<VLAN_NAME_' + str(counter[0]) + '>'
            counter[0] += 1

    for m in re.finditer(r'(?im)^\s+name\s+(\S+)$', text):
        name = m.group(1)
        if name.lower() not in skip_names and name not in mapping:
            mapping[name] = '<VLAN_NAME_' + str(counter[0]) + '>'
            counter[0] += 1

    for original in sorted(mapping.keys(), key=len, reverse=True):
        placeholder = mapping[original]
        text = re.sub(
            r'(?m)(^\d{1,4}\s+)' + re.escape(original) + r'(\s{2,})',
            lambda m, p=placeholder: m.group(1) + p + m.group(2),
            text
        )
        text = re.sub(
            r'(?im)(^\s+name\s+)' + re.escape(original) + r'$',
            lambda m, p=placeholder: m.group(1) + p,
            text
        )
        text = re.sub(
            r'(?im)(^\s+description\s+.*)' + re.escape(original),
            lambda m, o=original, p=placeholder: m.group(0).replace(o, p),
            text
        )

    return text, mapping


# ---------------------------------------------------------------------------
# Counter helper and map persistence
# ---------------------------------------------------------------------------

def _next_counter(mapping, prefix):
    """Get the next available counter for a placeholder prefix like 'IP_'."""
    if not mapping:
        return 1
    nums = []
    for placeholder in mapping.values():
        m = re.match(r'<' + re.escape(prefix) + r'(\d+)>', placeholder)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def save_map(map_path, all_maps):
    """Save all redaction mappings to JSON. Inverts each: placeholder -> original."""
    data = {}
    for category, mapping in all_maps.items():
        if mapping:
            data[category] = {placeholder: original
                              for original, placeholder in mapping.items()}
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return map_path


# ---------------------------------------------------------------------------
# API key validation
# ---------------------------------------------------------------------------

def validate_api_key(provider):
    """Check that the required API key environment variable is set."""
    cfg = PROVIDERS[provider]
    env_var = cfg["env_var"]
    api_key = os.environ.get(env_var)
    if not api_key:
        print("", file=sys.stderr)
        print("[ERROR] " + env_var + " is not set.", file=sys.stderr)
        print("", file=sys.stderr)
        print("  To set it, run:", file=sys.stderr)
        print('    export ' + env_var + '="your-key-here"', file=sys.stderr)
        print("", file=sys.stderr)
        print("  Get your API key at: " + cfg["signup_url"], file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)
    return api_key


# ---------------------------------------------------------------------------
# Inventory and command loading
# ---------------------------------------------------------------------------

def load_inventory(inventory_path):
    """Load device inventory from a YAML file."""
    p = Path(inventory_path)
    if not p.exists():
        print("[ERROR] Inventory file not found: " + str(p), file=sys.stderr)
        print("", file=sys.stderr)
        print("  Copy inventory-example.yml to inventory.yml and update", file=sys.stderr)
        print("  with your device IPs before running.", file=sys.stderr)
        sys.exit(1)

    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "devices" not in data or not data["devices"]:
        print("[ERROR] No devices found in: " + str(p), file=sys.stderr)
        print("  Expected a 'devices' list with name, host, device_type, role.", file=sys.stderr)
        sys.exit(1)

    required_fields = ["name", "host", "device_type", "role"]
    devices = []
    for idx, dev in enumerate(data["devices"], 1):
        missing = [f for f in required_fields if f not in dev or not dev[f]]
        if missing:
            print("[ERROR] Device #" + str(idx) + " is missing fields: "
                  + ", ".join(missing), file=sys.stderr)
            sys.exit(1)
        devices.append(dev)

    return devices


def load_commands(commands_path):
    """Load custom command sets from a YAML file. Returns commands_by_role dict."""
    p = Path(commands_path)
    if not p.exists():
        print("[ERROR] Commands file not found: " + str(p), file=sys.stderr)
        sys.exit(1)

    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        print("[ERROR] Commands file is empty: " + str(p), file=sys.stderr)
        sys.exit(1)

    commands_by_role = {}
    for role in ("router", "switch"):
        if role in data and data[role]:
            commands_by_role[role] = data[role]

    if not commands_by_role:
        print("[ERROR] No 'router' or 'switch' command lists in: " + str(p),
              file=sys.stderr)
        sys.exit(1)

    return commands_by_role

# ---------------------------------------------------------------------------
# Stage functions
# ---------------------------------------------------------------------------

def collect_device(device, username, password, enable_secret, output_dir, commands_by_role):
    """Connect to a device, run its command set, write output to a file.
    Returns True on success, or an error string on failure.
    """
    name = device["name"]
    host = device["host"]
    conn_params = {
        "device_type": device["device_type"],
        "host": host,
        "username": username,
        "password": password,
    }
    if enable_secret:
        conn_params["secret"] = enable_secret
    try:
        with ConnectHandler(**conn_params) as conn:
            if enable_secret:
                conn.enable()
            commands = commands_by_role.get(
                device.get("role", "router"), commands_by_role.get("router", [])
            )
            div = "=" * 60
            sections = []
            sections.append("DEVICE: " + name + NL)
            sections.append("HOST:   " + host + NL)
            sections.append("COLLECTED: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + NL)
            sections.append(div + NL)
            for cmd in commands:
                output = conn.send_command(cmd, read_timeout=60)
                sections.append(NL + div + NL)
                sections.append("COMMAND: " + cmd + NL)
                sections.append(div + NL)
                sections.append(output + NL)
        out_file = os.path.join(output_dir, name + ".txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(sections)
        return True
    except Exception as e:
        return str(e)


def stage_collect(devices, output_dir, commands_by_role):
    """Stage 1: SSH into devices and collect show command output.
    Returns (collected_files, failures).
    """
    print("[1/5] COLLECTING -- SSH into devices, run show commands")
    print("")
    # Env var fallback lets this script run unattended (cron, Task Scheduler).
    # Interactive prompts are still used when env vars are unset.
    username = os.environ.get("NETDEV_USER")
    password = os.environ.get("NETDEV_PASS")
    enable_secret = os.environ.get("NETDEV_ENABLE")
    if username:
        print("  Username: (from NETDEV_USER)")
    else:
        username = input("  Username: ")
    if password:
        print("  Password: (from NETDEV_PASS)")
    else:
        password = getpass.getpass("  Password: ")
    if enable_secret is None:
        enable_secret = getpass.getpass("  Enable secret (press Enter if not needed): ")
    else:
        print("  Enable secret: (from NETDEV_ENABLE)")
    if not enable_secret:
        enable_secret = None
    os.makedirs(output_dir, exist_ok=True)
    collected = []
    failures = []
    for device in devices:
        name = device["name"]
        host = device["host"]
        result = collect_device(device, username, password, enable_secret, output_dir, commands_by_role)
        if result is True:
            cmd_count = len(commands_by_role.get(device.get("role", "router"), commands_by_role.get("router", [])))
            print("    [OK]    " + name + " (" + host + ") -- " + str(cmd_count) + " commands, saved")
            collected.append(Path(output_dir) / (name + ".txt"))
        else:
            print("    [FAIL]  " + name + " (" + host + ") -- " + result)
            failures.append((name, result))
    print("")
    if failures:
        fail_path = os.path.join(output_dir, "failures.log")
        with open(fail_path, "w", encoding="utf-8") as f:
            for name, error in failures:
                f.write(name + ": " + error + NL)
        print("  Failures logged to: failures.log")
    if not collected:
        print("[ERROR] All devices failed. Nothing to process.", file=sys.stderr)
        sys.exit(1)
    print("  Collected " + str(len(collected)) + " of " + str(len(devices)) + " devices")
    print("  Output: " + output_dir)
    print("")
    return collected, failures


def stage_redact(output_dir, args):
    """Stage 2: Redact collected device output. Returns path to redacted directory."""
    print("[2/5] REDACTING -- sanitize output (credentials, IPs, hostnames, etc.)")
    print("")
    input_path = Path(output_dir)
    txt_files = sorted([f for f in input_path.glob("*.txt")], key=lambda p: p.name)
    if not txt_files:
        print("[ERROR] No .txt files found in: " + str(output_dir), file=sys.stderr)
        sys.exit(1)
    redacted_dir = input_path / "redacted"
    redacted_dir.mkdir(exist_ok=True)
    shared = {
        "ips": OrderedDict(), "hostnames": {}, "macs": OrderedDict(),
        "serials": {}, "usernames": {}, "versions": {},
        "descriptions": {}, "vlan_names": {},
    }
    total_creds = 0
    do_ips = not args.no_redact_ips
    do_hostnames = not args.no_redact_hostnames
    do_macs = not args.no_redact_macs
    do_serials = not args.no_redact_serials
    do_usernames = not args.no_redact_usernames
    do_certs = not args.no_redact_certs
    do_timestamps = not args.no_redact_timestamps
    do_versions = not args.no_redact_versions
    do_descriptions = not args.no_redact_descriptions
    do_vlan_names = not args.no_redact_vlan_names

    if do_hostnames:
        hn_counter = 1
        for f in txt_files:
            scan_text = f.read_text(encoding="utf-8")
            for h in dict.fromkeys(re.findall(r'(?im)^hostname\s+(\S+)', scan_text)):
                if h not in shared["hostnames"]:
                    shared["hostnames"][h] = "<HOSTNAME_" + str(hn_counter) + ">"
                    hn_counter += 1
            dm = re.search(r'(?im)^ip\s+domain[-\s]name\s+(\S+)', scan_text)
            if dm and dm.group(1) not in shared["hostnames"]:
                shared["hostnames"][dm.group(1)] = "<DOMAIN_REDACTED>"

    for f in txt_files:
        print("    [" + f.name + "]")
        text = f.read_text(encoding="utf-8")
        text, cred_count = redact_credentials(text)
        total_creds += cred_count
        if do_certs:
            text = redact_certificates(text)
        if do_descriptions:
            start = _next_counter(shared["descriptions"], "DESCRIPTION_")
            text, shared["descriptions"] = redact_descriptions(text, shared["descriptions"], start)
        if do_vlan_names:
            start = _next_counter(shared["vlan_names"], "VLAN_NAME_")
            text, shared["vlan_names"] = redact_vlan_names(text, shared["vlan_names"], start)
        if do_serials:
            start = _next_counter(shared["serials"], "SERIAL_")
            text, shared["serials"] = redact_serials(text, shared["serials"], start)
        if do_versions:
            start = _next_counter(shared["versions"], "VERSION_")
            text, shared["versions"] = redact_versions(text, shared["versions"], start)
        if do_hostnames:
            start = _next_counter(shared["hostnames"], "HOSTNAME_")
            text, shared["hostnames"] = redact_hostnames(text, shared["hostnames"], start)
        if do_ips:
            start = _next_counter(shared["ips"], "IP_")
            text, shared["ips"] = redact_ips(text, shared["ips"], start)
        if do_macs:
            start = _next_counter(shared["macs"], "MAC_")
            text, shared["macs"] = redact_macs(text, shared["macs"], start)
        if do_usernames:
            start = _next_counter(shared["usernames"], "USER_")
            text, shared["usernames"] = redact_usernames(text, shared["usernames"], start)
        if do_timestamps:
            text = redact_timestamps(text)
        out_path = redacted_dir / f.name
        out_path.write_text(text, encoding="utf-8")
    map_path = redacted_dir / "map.json"
    save_map(map_path, shared)
    total_redacted = sum(len(m) for m in shared.values()) + total_creds
    print("")
    print("  Credentials redacted : " + str(total_creds))
    print("  Other placeholders   : " + str(total_redacted - total_creds))
    print("  Map saved            : map.json")
    print("  Output               : " + str(redacted_dir))
    print("")
    return str(redacted_dir)


# ---------------------------------------------------------------------------
# Stage 3: Assemble
# ---------------------------------------------------------------------------

def load_template(template_path):
    """Load a custom prompt header from a .txt file."""
    p = Path(template_path)
    if not p.exists():
        print("[ERROR] Template not found: " + template_path, file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8").rstrip() + NL + NL + "--- DEVICE OUTPUT START ---" + NL


def stage_assemble(output_dir, redacted_dir, args, model):
    """Stage 3: Assemble prompt from device output files.
    Returns the assembled prompt string.
    """
    print("[3/5] ASSEMBLING -- build prompt from "
          + ("redacted" if redacted_dir else "raw") + " output")
    print("")
    input_dir = Path(redacted_dir) if redacted_dir else Path(output_dir)
    txt_files = sorted([f for f in input_dir.glob("*.txt")], key=lambda p: p.name)
    if not txt_files:
        print("[ERROR] No .txt files found in: " + str(input_dir), file=sys.stderr)
        sys.exit(1)
    header = load_template(args.template) if args.template else PROMPT_HEADER
    div = "=" * 60
    sections = [header]
    for idx, f in enumerate(txt_files, 1):
        content = f.read_text(encoding="utf-8").strip()
        sections.append(NL + NL + "[[ DEVICE " + str(idx) + " ]]")
        sections.append(NL + div)
        sections.append(NL + content)
        sections.append(NL)
    sections.append(PROMPT_FOOTER)
    prompt = "".join(sections)
    word_count = len(prompt.split())
    token_est = int(word_count * 1.3)
    print("    Devices assembled  : " + str(len(txt_files)))
    print("    Prompt size        : ~" + f"{token_est:,}" + " tokens")
    limit = CONTEXT_LIMITS.get(model)
    if limit and token_est > int(limit * 0.8):
        print("")
        print("  [WARNING] Prompt is ~" + f"{token_est:,}" + " tokens. "
              + model + " supports ~" + f"{limit:,}" + ".")
        print("            Results may be truncated or the API call may fail.")
        print("            Consider splitting your inventory into smaller groups")
        print("            (by site or function) and running the pipeline per group.")
    print("")
    return prompt


# ---------------------------------------------------------------------------
# Stage 4: Generate
# ---------------------------------------------------------------------------

def call_claude(api_key, model, prompt):
    """Send prompt to Claude API. Returns response text."""
    try:
        import anthropic
    except ImportError:
        print("[ERROR] anthropic package not installed.", file=sys.stderr)
        print("  Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def call_openai(api_key, model, prompt):
    """Send prompt to OpenAI API. Returns response text."""
    try:
        import openai
    except ImportError:
        print("[ERROR] openai package not installed.", file=sys.stderr)
        print("  Run: pip install openai", file=sys.stderr)
        sys.exit(1)
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_gemini(api_key, model, prompt):
    """Send prompt to Gemini API. Returns response text."""
    try:
        from google import genai
    except ImportError:
        print("[ERROR] google-genai package not installed.", file=sys.stderr)
        print("  Run: pip install google-genai", file=sys.stderr)
        sys.exit(1)
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text


PROVIDER_CALLERS = {
    "claude": call_claude,
    "openai": call_openai,
    "gemini": call_gemini,
}


def stage_generate(provider, model, api_key, prompt, output_dir):
    """Stage 4: Send prompt to AI API and save response.
    Returns (raw_path, response_text).
    """
    print("[4/5] GENERATING -- send prompt to " + provider + " API, receive runbook")
    print("    Model: " + model)
    print("")
    caller = PROVIDER_CALLERS[provider]
    try:
        print("    Waiting for response...")
        response_text = caller(api_key, model, prompt)
    except Exception as e:
        print("", file=sys.stderr)
        print("[ERROR] API call failed: " + str(e), file=sys.stderr)
        sys.exit(1)
    raw_path = Path(output_dir) / "runbook-raw.md"
    raw_path.write_text(response_text, encoding="utf-8")
    word_count = len(response_text.split())
    print("    Response received  : ~" + f"{word_count:,}" + " words")
    print("    Raw saved          : runbook-raw.md")
    print("")
    return str(raw_path), response_text


# ---------------------------------------------------------------------------
# Stage 5: Restore
# ---------------------------------------------------------------------------

def load_map(map_path):
    """Load and merge all category dicts from the JSON map file.
    Returns a single dict of {placeholder: original_value}.
    """
    with open(map_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    combined = {}
    for category in data.values():
        combined.update(category)
    return combined


def restore(text, mapping):
    """Replace placeholders with real values.
    Processes longest placeholders first to prevent partial matches.
    Returns (restored_text, count_of_placeholders_found).
    """
    found = 0
    for placeholder in sorted(mapping.keys(), key=len, reverse=True):
        original = mapping[placeholder]
        if placeholder in text:
            text = text.replace(placeholder, original)
            found += 1
    return text, found


def stage_restore(output_dir, redacted_dir, response_text):
    """Stage 5: Restore redacted placeholders in the AI response."""
    print("[5/5] RESTORING -- swap placeholders back to real values")
    print("")
    map_path = Path(redacted_dir) / "map.json"
    if not map_path.exists():
        print("[ERROR] Redaction map not found: " + str(map_path), file=sys.stderr)
        sys.exit(1)
    mapping = load_map(map_path)
    if not mapping:
        print("    No placeholders in map -- nothing to restore.")
        restored = response_text
        found = 0
    else:
        restored, found = restore(response_text, mapping)
    runbook_path = Path(output_dir) / "runbook.md"
    runbook_path.write_text(restored, encoding="utf-8")
    print("    Placeholders found : " + str(found) + " of " + str(len(mapping)))
    print("    Runbook saved      : runbook.md")
    print("")
    return str(runbook_path)


# ---------------------------------------------------------------------------
# Stage 6: Diagram helpers
# ---------------------------------------------------------------------------

def extract_sections(text):
    """Split a collector output file into {command: output} sections."""
    parts = re.split("={40,}" + chr(10) + "COMMAND: (.+)" + chr(10) + "={40,}" + chr(10), text)
    sections = {}
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip()] = parts[i + 1]
    return sections


def parse_device_header(text):
    """Extract device name and role hint from the collector header."""
    name_match = re.search(r"^DEVICE:\s+(.+)$", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else "unknown"
    return name


def detect_role(name, sections):
    """Detect device role from hostname pattern and available commands."""
    lower = name.lower()
    if "sw" in lower or "switch" in lower:
        return "switch"
    if "fw" in lower or "firewall" in lower:
        return "firewall"
    if "show vlan brief" in sections:
        return "switch"
    return "router"


def classify_tier(name):
    """Assign a layout tier based on hostname prefix."""
    lower = name.lower()
    if lower.startswith("edge"):
        return "edge"
    if lower.startswith("core"):
        return "core"
    if lower.startswith("access") or lower.startswith("dist"):
        return "access"
    return "other"


def parse_ip_interfaces(section_text):
    """Parse show ip interface brief into {interface: ip}."""
    interfaces = {}
    for line in section_text.splitlines():
        m = re.match(
            r"^(\S+)\s+(\d+\.\d+\.\d+\.\d+)\s+YES",
            line,
        )
        if m:
            interfaces[m.group(1)] = m.group(2)
    return interfaces


def normalize_intf(raw):
    """Normalize interface names: Et0/0 -> Ethernet0/0, Gi0/1 -> GigabitEthernet0/1, etc."""
    raw = raw.strip()
    abbrevs = [
        (r"^Et(\d)", r"Ethernet\1"),
        (r"^Eth(\d)", r"Ethernet\1"),
        (r"^Gi(\d)", r"GigabitEthernet\1"),
        (r"^Fa(\d)", r"FastEthernet\1"),
        (r"^Te(\d)", r"TenGigabitEthernet\1"),
        (r"^Lo(\d)", r"Loopback\1"),
    ]
    for pattern, replacement in abbrevs:
        raw = re.sub(pattern, replacement, raw)
    return raw


def shorten_intf(name):
    """Shorten interface name for edge labels: Ethernet0/0 -> E0/0."""
    name = re.sub(r"^Ethernet", "E", name)
    name = re.sub(r"^GigabitEthernet", "Gi", name)
    name = re.sub(r"^FastEthernet", "Fa", name)
    name = re.sub(r"^TenGigabitEthernet", "Te", name)
    return name


def parse_cdp_neighbors(section_text):
    """Parse show cdp neighbors detail into a list of neighbor dicts."""
    neighbors = []
    entries = re.split(r"^-{10,}", section_text, flags=re.MULTILINE)
    for entry in entries:
        dev_match = re.search(r"Device ID:\s*(\S+)", entry)
        local_match = re.search(
            r"Interface:\s*(\S+),\s*Port ID \(outgoing port\):\s*(\S+)", entry
        )
        if dev_match and local_match:
            remote_name = dev_match.group(1).split(".")[0]
            local_intf = normalize_intf(local_match.group(1))
            remote_intf = normalize_intf(local_match.group(2))
            neighbors.append({
                "remote_device": remote_name,
                "local_intf": local_intf,
                "remote_intf": remote_intf,
            })
    return neighbors


def build_topology(input_dir):
    """Read all .txt files in input_dir and build devices + links."""
    devices = {}
    links = []
    seen_links = set()

    txt_files = sorted(
        f for f in os.listdir(input_dir)
        if f.endswith(".txt") and not f.startswith("prompt")
    )

    for fname in txt_files:
        fpath = os.path.join(input_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()

        name = parse_device_header(text)
        sections = extract_sections(text)
        role = detect_role(name, sections)
        tier = classify_tier(name)

        ip_intf = {}
        if "show ip interface brief" in sections:
            ip_intf = parse_ip_interfaces(sections["show ip interface brief"])

        devices[name] = {
            "role": role,
            "tier": tier,
            "interfaces": ip_intf,
        }

        if "show cdp neighbors detail" in sections:
            cdp_neighbors = parse_cdp_neighbors(
                sections["show cdp neighbors detail"]
            )
            for nbr in cdp_neighbors:
                pair = tuple(sorted([
                    (name, nbr["local_intf"]),
                    (nbr["remote_device"], nbr["remote_intf"]),
                ]))
                if pair not in seen_links:
                    seen_links.add(pair)
                    links.append({
                        "a_device": name,
                        "a_intf": nbr["local_intf"],
                        "b_device": nbr["remote_device"],
                        "b_intf": nbr["remote_intf"],
                    })

    return devices, links


def compute_positions(devices):
    """Assign x, y positions based on tier grouping."""
    tiers = {}
    for name, info in devices.items():
        tier = info["tier"]
        tiers.setdefault(tier, []).append(name)

    positions = {}
    sorted_tiers = sorted(tiers.keys(), key=lambda t: TIER_ORDER.get(t, 99))

    for tier_idx, tier in enumerate(sorted_tiers):
        members = sorted(tiers[tier])
        tier_width = len(members) * H_SPACING
        start_x = LEFT_MARGIN + (3 * H_SPACING - tier_width) // 2
        y = TOP_MARGIN + tier_idx * V_SPACING

        for i, name in enumerate(members):
            x = start_x + i * H_SPACING
            positions[name] = (x, y)

    return positions


def build_endpoint_label(device_name, intf, devices):
    """Build a label for one end of a link: 'E0/0 (10.0.12.1)' or just 'E0/0'."""
    short = shorten_intf(intf)
    ip = devices.get(device_name, {}).get("interfaces", {}).get(intf, "")
    if ip:
        return short + chr(10) + ip
    return short


def generate_drawio(devices, links, positions, output_path):
    """Generate the .drawio XML file."""
    mxfile = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", id="topology", name="Network Topology")
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "0", "dy": "0", "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1",
        "pageWidth": "1100", "pageHeight": "850",
        "math": "0", "shadow": "0",
    })
    root = ET.SubElement(model, "root")

    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    device_ids = {}
    cell_id = 2

    for name, info in sorted(devices.items()):
        did = "d" + str(cell_id)
        device_ids[name] = did
        cell_id += 1

        style = SWITCH_STYLE if info["role"] == "switch" else ROUTER_STYLE
        x, y = positions.get(name, (100, 100))

        cell = ET.SubElement(root, "mxCell", {
            "id": did,
            "value": name,
            "style": style,
            "vertex": "1",
            "parent": "1",
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x), "y": str(y),
            "width": str(NODE_W), "height": str(NODE_H),
            "as": "geometry",
        })

    for link in links:
        eid = "e" + str(cell_id)
        cell_id += 1

        source_id = device_ids.get(link["a_device"])
        target_id = device_ids.get(link["b_device"])

        if not source_id or not target_id:
            continue

        cell = ET.SubElement(root, "mxCell", {
            "id": eid,
            "value": "",
            "style": EDGE_STYLE,
            "edge": "1",
            "parent": "1",
            "source": source_id,
            "target": target_id,
        })
        ET.SubElement(cell, "mxGeometry", {
            "relative": "1",
            "as": "geometry",
        })

        src_label_id = eid + "_src"
        src_label = build_endpoint_label(link["a_device"], link["a_intf"], devices)
        src_cell = ET.SubElement(root, "mxCell", {
            "id": src_label_id,
            "value": src_label,
            "style": EDGE_LABEL_STYLE,
            "vertex": "1",
            "connectable": "0",
            "parent": eid,
        })
        src_geo = ET.SubElement(src_cell, "mxGeometry", {
            "x": "-0.4",
            "relative": "1",
            "as": "geometry",
        })
        ET.SubElement(src_geo, "mxPoint", {"as": "offset"})

        tgt_label_id = eid + "_tgt"
        tgt_label = build_endpoint_label(link["b_device"], link["b_intf"], devices)
        tgt_cell = ET.SubElement(root, "mxCell", {
            "id": tgt_label_id,
            "value": tgt_label,
            "style": EDGE_LABEL_STYLE,
            "vertex": "1",
            "connectable": "0",
            "parent": eid,
        })
        tgt_geo = ET.SubElement(tgt_cell, "mxGeometry", {
            "x": "0.4",
            "relative": "1",
            "as": "geometry",
        })
        ET.SubElement(tgt_geo, "mxPoint", {"as": "offset"})

    rough = ET.tostring(mxfile, encoding="unicode")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    lines = pretty.splitlines()
    if lines and lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines))


def stage_diagram(output_dir):
    """Stage 6 (optional): Generate draw.io topology diagram.
    Uses raw (unredacted) collector output.
    """
    print("[+]   DIAGRAM -- generating draw.io topology")
    print("")
    devices, links = build_topology(output_dir)
    if not devices:
        print("    [WARNING] No devices found -- skipping diagram.")
        print("")
        return None
    print("    Devices : " + str(len(devices)))
    print("    Links   : " + str(len(links)))
    positions = compute_positions(devices)
    output_path = os.path.join(output_dir, "network-topology.drawio")
    generate_drawio(devices, links, positions, output_path)
    print("    Saved   : network-topology.drawio")
    print("")
    return output_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Automated network documentation pipeline -- "
                    "SSH to finished runbook in one command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--provider", choices=["claude", "openai", "gemini"], default="claude",
                        help="AI provider (default: claude)")
    parser.add_argument("--model", default=None,
                        help="Override the default model for the selected provider")
    parser.add_argument("--inventory", default="inventory.yml",
                        help="Path to device inventory YAML (default: inventory.yml)")
    parser.add_argument("--commands", default=None,
                        help="Path to custom commands YAML file")
    parser.add_argument("--diagram", action="store_true",
                        help="Also generate a draw.io topology diagram")
    parser.add_argument("--skip-redaction", action="store_true",
                        help="Send raw output to API without redaction (lab use only)")
    parser.add_argument("--no-redact-ips", action="store_true",
                        help="Skip IP redaction")
    parser.add_argument("--no-redact-hostnames", action="store_true",
                        help="Skip hostname redaction")
    parser.add_argument("--no-redact-macs", action="store_true",
                        help="Skip MAC redaction")
    parser.add_argument("--no-redact-serials", action="store_true",
                        help="Skip serial number redaction")
    parser.add_argument("--no-redact-usernames", action="store_true",
                        help="Skip username redaction")
    parser.add_argument("--no-redact-certs", action="store_true",
                        help="Skip certificate stripping")
    parser.add_argument("--no-redact-timestamps", action="store_true",
                        help="Skip timestamp redaction")
    parser.add_argument("--no-redact-versions", action="store_true",
                        help="Skip IOS version redaction")
    parser.add_argument("--no-redact-descriptions", action="store_true",
                        help="Skip interface description redaction")
    parser.add_argument("--no-redact-vlan-names", action="store_true",
                        help="Skip VLAN name redaction")
    parser.add_argument("--template", default=None,
                        help="Path to custom prompt header .txt file")
    parser.add_argument("--output-dir", default=None,
                        help="Override output directory (default: output/<timestamp>)")
    args = parser.parse_args()

    print("=" * 60)
    print("  GTT Automated Documentation Pipeline")
    print("  EP005 - G Talks Tech")
    print("=" * 60)

    # Load inventory
    devices = load_inventory(args.inventory)
    print("")
    print("  Inventory  : " + str(args.inventory) + " (" + str(len(devices)) + " devices)")

    # Load commands
    if args.commands:
        commands_by_role = load_commands(args.commands)
        print("  Commands   : " + args.commands + " (custom)")
    else:
        commands_by_role = DEFAULT_COMMANDS_BY_ROLE
        print("  Commands   : built-in defaults")

    # Resolve model
    provider_cfg = PROVIDERS[args.provider]
    model = args.model if args.model else provider_cfg["default_model"]
    print("  Provider   : " + args.provider + " (" + model + ")")
    print("")

    # Validate API key (fail fast before SSH collection)
    api_key = validate_api_key(args.provider)

    # Create output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_dir = os.path.join("output", timestamp)

    # Stage 1: Collect
    collected_files, failures = stage_collect(devices, output_dir, commands_by_role)

    # Stage 2: Redact (skip if --skip-redaction)
    if not args.skip_redaction:
        redacted_dir = stage_redact(output_dir, args)
    else:
        redacted_dir = None
        print("[2/5] REDACTING -- skipped (--skip-redaction)")
        print("")


    # Stage 3: Assemble prompt
    prompt = stage_assemble(output_dir, redacted_dir, args, model)

    # Stage 4: Generate
    raw_path, response_text = stage_generate(
        args.provider, model, api_key, prompt, output_dir
    )

    # Stage 5: Restore (skip if --skip-redaction)
    if not args.skip_redaction and redacted_dir:
        runbook_path = stage_restore(output_dir, redacted_dir, response_text)
    else:
        runbook_path = os.path.join(output_dir, "runbook.md")
        Path(runbook_path).write_text(response_text, encoding="utf-8")
        print("[5/5] RESTORING -- skipped (--skip-redaction)")
        print("    Runbook saved      : runbook.md")
        print("")

    # Stage 6: Diagram (optional)
    if args.diagram:
        stage_diagram(output_dir)

    # Final summary
    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print("")
    print("  Output directory : " + output_dir)
    print("  Runbook          : runbook.md")
    if args.diagram:
        print("  Diagram          : network-topology.drawio")
    if failures:
        print("  Failed devices   : " + str(len(failures))
              + " (see failures.log)")
    print("")
    print("  Open " + output_dir + "/runbook.md to review your documentation.")
    print("")


if __name__ == "__main__":
    main()
