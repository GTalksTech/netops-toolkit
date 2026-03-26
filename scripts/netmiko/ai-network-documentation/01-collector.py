# ============================================================
# Script:       01-collector.py
# Purpose:      SSH into lab devices and save show command output
# Usage:        python 01-collector.py
# Dependencies: netmiko
# Author:       G Talks Tech
# Episode:      EP004-L-ai-network-documentation
# GitHub:       github.com/GTalksTech/netops-toolkit
# Notes:        Update DEVICES with your own IPs before running.
#               Uses getpass -- credentials are never hardcoded.
# ============================================================

import os
import getpass
from datetime import datetime
from netmiko import ConnectHandler


# ---------------------------------------------------------------------------
# Device inventory -- update IPs and roles to match your network
# ---------------------------------------------------------------------------
DEVICES = [
    {"name": "core-rtr-01",  "host": "192.168.1.250", "device_type": "cisco_ios", "role": "router"},
    {"name": "edge-rtr-01",  "host": "10.0.0.2",      "device_type": "cisco_ios", "role": "router"},
    {"name": "access-sw-01", "host": "192.168.1.251", "device_type": "cisco_ios", "role": "switch"},
]

# ---------------------------------------------------------------------------
# Commands to run per device role
# ---------------------------------------------------------------------------
ROUTER_COMMANDS = [
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

SWITCH_COMMANDS = [
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

COMMANDS_BY_ROLE = {
    "router": ROUTER_COMMANDS,
    "switch": SWITCH_COMMANDS,
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def collect_device(device, username, password, enable_secret, output_dir):
    """Connect to a device, run its command set, write output to a file."""
    name = device["name"]
    print("")
    print("[*] Connecting to " + name + " (" + device["host"] + ")...")

    conn_params = {
        "device_type": device["device_type"],
        "host":        device["host"],
        "username":    username,
        "password":    password,
    }
    if enable_secret:
        conn_params["secret"] = enable_secret

    try:
        with ConnectHandler(**conn_params) as conn:
            if enable_secret:
                conn.enable()
            print("    Connected. Collecting output...")
            commands = COMMANDS_BY_ROLE.get(device.get("role", "router"), ROUTER_COMMANDS)
            div = "=" * 60

            sections = []
            sections.append("DEVICE: " + name + "\n")
            sections.append("HOST:   " + device["host"] + "\n")
            sections.append("COLLECTED: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
            sections.append(div + "\n")

            for cmd in commands:
                print("    -> " + cmd)
                output = conn.send_command(cmd, read_timeout=60)
                sections.append("\n" + div + "\n")
                sections.append("COMMAND: " + cmd + "\n")
                sections.append(div + "\n")
                sections.append(output + "\n")

        out_file = os.path.join(output_dir, name + ".txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(sections)
        print("    Saved -> " + out_file)

    except Exception as e:
        print("    [ERROR] Could not collect " + name + ": " + str(e))


def main():
    print("=" * 60)
    print("  GTT Network Documentation Collector")
    print("  EP004 - G Talks Tech")
    print("=" * 60)

    username = input("\nUsername: ")
    password = getpass.getpass("Password: ")
    enable_secret = getpass.getpass("Enable secret (press Enter if not needed): ")
    if not enable_secret:
        enable_secret = None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = os.path.join("output", timestamp)
    os.makedirs(output_dir, exist_ok=True)
    print("\nOutput directory: " + output_dir + "\n")

    for device in DEVICES:
        collect_device(device, username, password, enable_secret, output_dir)

    print("\n[+] Collection complete. Files saved to: " + output_dir + "/")
    print("    Raw output contains credentials -- treat this folder as sensitive.")
    print("    Next step: run 02-redactor.py on this output folder.")


if __name__ == "__main__":
    main()

