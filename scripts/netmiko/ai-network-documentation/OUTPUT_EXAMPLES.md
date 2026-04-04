# Output Examples

Reference output from each script in the workflow. If you are following
along with the video and something scrolled by too fast, this is where
you can check what the output should look like.

All output below was generated from the included `NetMiko-Lab.yaml`
topology using credentials `admin` / `cisco123`.

---

## 01-collector.py

The collector SSHs into each device, runs a set of show commands, and
saves the raw output to `output/<timestamp>/<device>.txt`.

**File created:** `output/2026-03-22_132827/core-rtr-01.txt` (one per device)

```
DEVICE: core-rtr-01
HOST:   192.168.1.250
COLLECTED: 2026-03-22 13:28:28
============================================================

============================================================
COMMAND: show version
============================================================
Cisco IOS Software [IOSXE], Linux Software (X86_64BI_LINUX-ADVENTERPRISEK9-M), Version 17.16.1a, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2024 by Cisco Systems, Inc.
Compiled Thu 19-Dec-24 17:54 by mcpre

ROM: Bootstrap program is Linux

core-rtr-01 uptime is 1 hour, 44 minutes
...

============================================================
COMMAND: show ip interface brief
============================================================
Interface              IP-Address      OK? Method Status                Protocol
Ethernet0/0            192.168.1.250   YES NVRAM  up                    up
Ethernet0/1            10.0.12.2       YES NVRAM  up                    up
Ethernet0/2            unassigned      YES NVRAM  administratively down down
Ethernet0/3            unassigned      YES NVRAM  administratively down down
Loopback0              10.0.0.1        YES NVRAM  up                    up

============================================================
COMMAND: show interfaces
============================================================
Ethernet0/0 is up, line protocol is up
  Hardware is AmdP2, address is aabb.cc00.0200 (bia aabb.cc00.0200)
  Description: LAN -- Link to access-sw-01 E0/0
  Internet address is 192.168.1.250/24
  MTU 1500 bytes, BW 10000 Kbit/sec, DLY 1000 usec,
     reliability 255/255, txload 1/255, rxload 1/255
  ...
```

One file is created per device. The full output includes every show
command configured in the script (show version, show inventory,
show ip interface brief, show interfaces, show ip route,
show ip ospf neighbor, show running-config, and more).

---
## 02-redactor.py

The redactor replaces sensitive values (IPs, hostnames, MACs, serials,
credentials, timestamps) with placeholder tokens and writes a mapping
file so values can be restored later.

**Files created:**
- `output/<timestamp>/redacted/<device>.txt` (one per device)
- `output/<timestamp>/redacted/map.json`

### Redacted device output (core-rtr-01.txt)

```
DEVICE: <HOSTNAME_2>
HOST:   <IP_8>
COLLECTED: <TIMESTAMP>
============================================================

============================================================
COMMAND: show version
============================================================
Cisco IOS Software [IOSXE], Linux Software (...), Version <VERSION_1>, RELEASE SOFTWARE (fc1)
...

<HOSTNAME_2> uptime is <UPTIME_REDACTED>
...

Processor board ID <SERIAL_2>

============================================================
COMMAND: show ip interface brief
============================================================
Interface              IP-Address      OK? Method Status                Protocol
Ethernet0/0            <IP_8>   YES NVRAM  up                    up
Ethernet0/1            <IP_11>       YES NVRAM  up                    up
Ethernet0/2            unassigned      YES NVRAM  administratively down down
Ethernet0/3            unassigned      YES NVRAM  administratively down down
Loopback0              <IP_12>        YES NVRAM  up                    up

============================================================
COMMAND: show interfaces
============================================================
Ethernet0/0 is up, line protocol is up
  Hardware is AmdP2, address is <MAC_22> (bia <MAC_22>)
  Description: <DESCRIPTION_11>
  Internet address is <IP_8>/24
  ...
```

Every sensitive value is replaced with a consistent placeholder token.
The same IP always gets the same token across all files.

### Redaction map (map.json)

```json
{
  "ips": {
    "<IP_1>": "192.168.1.251",
    "<IP_2>": "10.10.10.1",
    "<IP_3>": "10.10.20.1",
    "<IP_8>": "192.168.1.250",
    "<IP_11>": "10.0.12.2",
    "<IP_12>": "10.0.0.1"
  },
  "hostnames": {
    "<HOSTNAME_1>": "access-sw-01",
    "<HOSTNAME_2>": "core-rtr-01",
    "<HOSTNAME_3>": "edge-rtr-01"
  },
  "macs": {
    "<MAC_1>": "aabb.cc00.0100",
    "<MAC_22>": "aabb.cc00.0200"
  },
  "serials": {
    "<SERIAL_1>": "131184641",
    "<SERIAL_2>": "131184642"
  }
}
```

The map is truncated here. The full file includes all IPs, hostnames,
MACs, serials, descriptions, VLAN names, and other redacted values.

---

## 03-prompt-assembler.py

The prompt assembler combines all redacted device output into a single
file with an AI instruction header. This is what you paste into Claude,
ChatGPT, or any LLM.

**File created:** `output/<timestamp>/prompt-<timestamp>.txt`

```
You are a network documentation engineer producing an operational
runbook for a senior network engineer. This runbook must be immediately
usable during incidents and change planning -- not a training document.

CRITICAL: The device output contains sanitized placeholder tokens.
You MUST copy every placeholder into your output exactly as written
-- same angle brackets, same capitalization, same underscore format.
Do NOT expand, paraphrase, resolve, or reformat them in any way.

Placeholder types you may encounter:
- <IP_1>, <IP_2> ... (IP addresses)
- <HOSTNAME_1>, <HOSTNAME_2> ... (device hostnames)
- <MAC_1>, <MAC_2> ... (MAC addresses)
- <SERIAL_1>, <SERIAL_2> ... (serial numbers)
...

Generate a Markdown runbook with these sections in this order:
1. ## Topology Overview
2. ## Device Inventory
3. ## IP Addressing
4. ## Routing Summary
5. ## Layer 2 Summary
6. ## Management Services
7. ## Findings and Flags

--- DEVICE OUTPUT START ---

[[ DEVICE 1 ]]
============================================================
DEVICE: <HOSTNAME_1>
HOST:   <IP_1>
...
(all redacted show command output for each device follows)
```

The prompt includes a token count estimate so you know whether it fits
in your LLM's context window.

---

## 04-restore.py

After the LLM generates a runbook using placeholder tokens, the restore
script swaps every placeholder back to its real value using map.json.

**Input:** `runbook.md` (AI-generated, contains placeholders)
**Output:** `runbook-restored.md` (real values restored)

### Before (AI-generated runbook with placeholders)

```markdown
## Topology Overview

`<HOSTNAME_1>` is operating as a Layer 2 switch with SVIs for
VLAN 1, 10, 20, and 30, with a trunk on `Ethernet0/0` toward
`<HOSTNAME_2>`. `<HOSTNAME_2>` is a router with one interface
toward `<HOSTNAME_1>` and one point-to-point OSPF link toward
`<HOSTNAME_3>`.

| Device | Role | Connected To |
|---|---|---|
| `<HOSTNAME_1>` | Layer 2 switch | `<HOSTNAME_2>` via `Ethernet0/0` |
| `<HOSTNAME_2>` | Router and OSPF transit node | `<HOSTNAME_1>` via `Ethernet0/0`; `<HOSTNAME_3>` via `Ethernet0/1` |
| `<HOSTNAME_3>` | Router and OSPF downstream node | `<HOSTNAME_2>` via `Ethernet0/0` |

## Device Inventory

| Hostname | Model | IOS Version | Serial |
|---|---|---|---|
| `<HOSTNAME_1>` | Not found in output | `<VERSION_1>` | `<SERIAL_1>` |
| `<HOSTNAME_2>` | Not found in output | `<VERSION_1>` | `<SERIAL_2>` |
| `<HOSTNAME_3>` | Not found in output | `<VERSION_1>` | `<SERIAL_4>` |
```

### After (restored with real values)

```markdown
## Topology Overview

`access-sw-01` is operating as a Layer 2 switch with SVIs for
VLAN 1, 10, 20, and 30, with a trunk on `Ethernet0/0` toward
`core-rtr-01`. `core-rtr-01` is a router with one interface
toward `access-sw-01` and one point-to-point OSPF link toward
`edge-rtr-01`.

| Device | Role | Connected To |
|---|---|---|
| `access-sw-01` | Layer 2 switch | `core-rtr-01` via `Ethernet0/0` |
| `core-rtr-01` | Router and OSPF transit node | `access-sw-01` via `Ethernet0/0`; `edge-rtr-01` via `Ethernet0/1` |
| `edge-rtr-01` | Router and OSPF downstream node | `core-rtr-01` via `Ethernet0/0` |

## Device Inventory

| Hostname | Model | IOS Version | Serial |
|---|---|---|---|
| `access-sw-01` | Not found in output | `17.16.1a` | `131184641` |
| `core-rtr-01` | Not found in output | `17.16.1a` | `131184642` |
| `edge-rtr-01` | Not found in output | `17.16.1a` | `131184643` |
```

---

## 05-diagram-generator.py

The diagram generator reads the raw collector output and builds a
draw.io XML file with Cisco-styled device icons and labeled links.
No AI or API tokens needed.

**File created:** `output/<timestamp>/network-topology.drawio`

Open the `.drawio` file in [draw.io](https://app.diagrams.net) or the
draw.io VS Code extension. The generated diagram includes:

- Cisco-styled icons for routers and switches
- Interface labels on each link (e.g., E0/0, E0/1)
- IP addresses on connected interfaces
- Automatic layout based on device roles

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram id="topology" name="Network Topology">
    <mxGraphModel ...>
      <root>
        <mxCell id="d2" value="access-sw-01"
          style="...shape=mxgraph.cisco19.rect;prIcon=l2_switch..." />
        <mxCell id="d3" value="core-rtr-01"
          style="...shape=mxgraph.cisco19.rect;prIcon=router..." />
        <mxCell id="d4" value="edge-rtr-01"
          style="...shape=mxgraph.cisco19.rect;prIcon=router..." />
        <!-- link and label elements for each connection -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

The XML is abbreviated here. The full file renders a complete topology
diagram when opened in draw.io.
