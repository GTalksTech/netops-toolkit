# MCP Network Assistant -- Starter Kit

A custom FastMCP + Netmiko server that gives Claude read-only access to
your home lab over SSH, so you can ask plain-English questions like
"something's off with OSPF on my network, take a look and tell me what
you find" and get a real diagnosis from live device output.

**Video:** [Creating a Custom MCP Server and Network Assistant](https://youtu.be/LZrmRdSMiJ0)

## What This Is

This is a from-scratch MCP (Model Context Protocol) server. It exposes
5 read-only tools that Claude can call against your lab devices over
SSH via Netmiko. You ask a question in plain English, Claude decides
which tools to call and in what order, and it synthesizes the answer
from real `show` command output.

Everything here is read-only. No config-changing commands are exposed.

## Lab Topology

Three Cisco IOL devices plus an External Connector bridged to the host
for SSH access -- the same lab used across other G Talks Tech episodes.

```
edge-rtr-01 (IOL)
  E0/0 -- 10.0.0.2 (Loopback0)
       |
       | OSPF area 0
       |
core-rtr-01 (IOL)
  E0/0 -- 192.168.1.250/24
       |
       | LAN (192.168.1.0/24)
       |
access-sw-01 (IOL-L2)
  E1/0 -- ExternalCon (bridge to host)
```

| Device | Role | Management IP | Platform |
|--------|------|----------------|----------|
| edge-rtr-01 | Edge / WAN router | 10.0.0.2 (Loopback0) | IOL (iol-xe) |
| core-rtr-01 | Core router | 192.168.1.250 | IOL (iol-xe) |
| access-sw-01 | Access switch | 192.168.1.251 | IOL-L2 (ioll2-xe) |
| ExternalCon | Bridge to host | -- | external_connector |

Credentials: `admin` / `cisco123`

These are real lab credentials for a publicly replicable topology --
import `cml-topology.yaml` into CML, build the 3 devices with these
credentials, and `inventory.yaml` will work against it unmodified.

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) -- Python
  package and virtual environment manager
- [Node.js](https://nodejs.org/) -- needed for `npx`, which runs the MCP
  Inspector (used to test the server before wiring it into a client)
- [CML Free](https://developer.cisco.com/docs/modeling-labs/cml-free/)
  (or CML Personal) with `cml-topology.yaml` imported, OR your own lab
  with `inventory.yaml` adjusted to match
- Claude Desktop and/or [Claude Code](https://claude.com/claude-code)
- SSH access from your workstation to all 3 lab devices

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/GTalksTech/netops-toolkit.git
cd netops-toolkit/scripts/netmiko/mcp-network-assistant
```

### 2. Install dependencies

```bash
uv sync
```

This creates a `.venv/` and installs `fastmcp`, `netmiko`, and `pyyaml`
(see `requirements.txt` for versions). If you're not using `uv`, you can
also do this with plain `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Adjust the inventory (if needed)

`inventory.yaml` ships pre-configured for the lab topology above. If
your devices use different IPs, hostnames, or credentials, edit
`inventory.yaml` -- the `defaults` block applies to every device, and
each device under `devices:` only needs a `host` and a `description`.

### 4. Verify with MCP Inspector

Before wiring this into a client, run it through the MCP Inspector to
confirm all 5 tools work:

```bash
npx @modelcontextprotocol/inspector uv run python server.py
```

This opens a browser at `http://localhost:6274`. You should see all 5
tools listed. Try `list_devices` (returns your 3 devices), then try
`run_show_command` with `show running-config` (should return a BLOCKED
message).

### 5. Configure Claude Desktop

Custom local MCP servers in Claude Desktop go through
**Settings -> Developer -> Edit Config** -- NOT the Connectors tab
(Connectors is for remote OAuth-based servers like Google Drive or
Slack).

Click Edit Config, and add an entry like the one in
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "network-assistant": {
      "command": "/path/to/mcp-network-assistant/.venv/Scripts/python.exe",
      "args": [
        "/path/to/mcp-network-assistant/server.py"
      ]
    }
  }
}
```

Two things to get right:

- **Use the absolute path to the `python.exe` (or `python`) inside your
  `.venv`, not your system Python.** Claude Desktop runs as a GUI
  process and doesn't inherit your terminal's PATH or active virtual
  environment.
- **On Windows, JSON requires double backslashes** (`\\`) in paths --
  e.g. `C:\\Users\\you\\mcp-network-assistant\\.venv\\Scripts\\python.exe`.
  A single backslash silently breaks the config with no useful error.
- **On macOS/Linux**, the venv interpreter lives at
  `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

After saving, fully quit Claude Desktop (use the tray/menu bar icon ->
Quit, not just closing the window) and reopen it. Claude Desktop only
reads this config on startup. Check **Settings -> Developer** -- you
should see `network-assistant` with a green indicator and "5 tools".

#### Recommended: scope it with a project

The tool docstrings tell Claude *when* to use each tool, but a project
(or session) system prompt removes ambiguity about whether a question is
about *your* lab at all. Something like:

```
You have access to a network-assistant MCP server connected to my home lab.
The lab has three Cisco IOL devices: core-rtr-01 (192.168.1.250), edge-rtr-01 (10.0.0.2), and access-sw-01 (192.168.1.251).
When I ask about my lab network or these devices, use the network-assistant tools to investigate directly -- don't ask me for show output, just go get it.
For general networking questions not about this lab, answer normally without invoking tools.
```

### 6. Configure Claude Code (optional)

If you live in the terminal, `.mcp.json` in the project root works the
same way -- Claude Code auto-detects it automatically when you run
`claude` from this directory. Edit the placeholder paths in `.mcp.json`
the same way as step 5 above.

## Tools

`server.py` exposes 5 read-only MCP tools:

| Tool | What it does | Guardrails |
|------|---------------|------------|
| `list_devices()` | Lists all devices in `inventory.yaml` with host and description. | None -- inventory metadata only. |
| `get_device_status(device)` | Bundles `show ip interface brief`, `show ip ospf neighbor`, `show ip route`, and `show cdp neighbors` into one SSH session. | Read-only `show` commands only. |
| `run_show_command(device, command)` | Runs an arbitrary `show ...` command. | Must start with `show `. Blocked if it matches `\b(run(?:ning)?\|startup\|secret\|password\|username\|community\|key\|crypto)\b` (case-insensitive) -- e.g. `show running-config` is blocked. |
| `find_in_config(device, pattern)` | Greps `show running-config` for a regex pattern. | Server-side redaction applied before any output reaches the model (see below). |
| `compare_running_to_startup(device)` | Diffs `show running-config` vs `show startup-config` to detect unsaved drift. | Server-side redaction applied before any output reaches the model. |

Each tool's docstring is what Claude reads to decide *when* to call it.
A scoped description ("use when the user asks about their home lab") is
what keeps the tools firing on the right prompts and not on unrelated
networking questions. Adapt these docstrings if you change what the
tools do.

## Redaction

`find_in_config` and `compare_running_to_startup` both pull from
`show running-config`, which can contain secrets. Before that output
ever reaches Claude, `REDACT_PATTERNS` in `server.py` strips sensitive
values:

| Pattern | Example before | Example after |
|---------|------------------|-----------------|
| `secret <N> <value>` | `enable secret 5 $1$abc...` | `enable secret <REDACTED>` |
| `password <N> <value>` | `password 7 0822455D0A16` | `password <REDACTED>` |
| `community <value>` | `snmp-server community public RO` | `snmp-server community <REDACTED> RO` |
| `md5 <N> <value>` | `message-digest-key 1 md5 7 0822...` | `message-digest-key 1 md5 <REDACTED>` |
| `key <N> <value>` | `key 1 7 0822455D0A16` | `key <REDACTED>` |

This means Claude can still tell you *that* a community string exists,
that it's read-only, and whether there's an ACL on it -- without ever
seeing the actual string value. The structure is enough for a useful
audit.

`REDACT_PATTERNS` is a single Python list near the top of `server.py`.
Commenting it out (or setting it to `[]`) removes this layer entirely --
useful for understanding exactly what one list of regexes is protecting,
not recommended for normal use.

## Security Notes

This kit ships with **real, working credentials** (`admin` / `cisco123`)
for a **publicly replicable lab topology** (`cml-topology.yaml`). That's
intentional -- the goal is "lab in a box": clone the repo, import the
topology, and the inventory works without editing anything. These are
not production credentials and never represent a real network.

The actual security model is the combination of:

- **Whitelist enforcement** (`BLOCKED_TOKENS` in `server.py`) -- only
  `show ...` commands are allowed at all, and commands containing
  `run`/`running`/`startup`/`secret`/`password`/`username`/`community`/
  `key`/`crypto` are blocked outright. `show running-config` never
  executes through `run_show_command`.
- **Output redaction** (`REDACT_PATTERNS`) -- the two tools that *do*
  read from running-config (`find_in_config`,
  `compare_running_to_startup`) strip secret-shaped values before the
  text leaves the server.
- **No write tools** -- nothing in `server.py` can change device
  configuration. Every tool is read-only by construction.

If you point this at your own lab or network, treat it the same way you
would any other read-only automation tool with stored credentials:
restrict `inventory.yaml` permissions, and don't reuse lab-only
passwords on anything that matters.

## Known Limitations

- **3-device lab only.** `inventory.yaml` is hardcoded to 3 devices.
  Adding more devices is just adding more entries under `devices:` --
  but the tool descriptions reference "the GTT home lab" and may need
  light editing if your lab is larger or differently shaped.
- **Cisco IOS-style commands.** `get_device_status`, redaction patterns,
  and the example queries all assume `cisco_ios`-flavored `show` output.
  Other Netmiko `device_type` values should connect fine, but command
  output and redaction patterns may need adjusting.
- **Whitelist is a blocklist, not an allowlist of full commands.** It
  blocks commands *containing* certain tokens, which is intentionally
  broad (and occasionally blocks a legitimate `show` command that
  happens to contain one of those words). Tighten or loosen
  `BLOCKED_TOKENS` to fit your environment.
- **No write/config tools.** This is read-only by design. A
  read/write follow-up with approval gates is a possible future
  direction, not part of this kit.
- **Claude Desktop reads its config on startup only.** Any change to
  `claude_desktop_config.json` requires a full quit and relaunch, not
  just closing the window.

## Files

| File | Purpose |
|------|---------|
| `server.py` | The FastMCP server -- 5 read-only tools over Netmiko |
| `inventory.yaml` | Lab device inventory (defaults + per-device overrides) |
| `requirements.txt` | Python dependencies (`fastmcp`, `netmiko`, `pyyaml`) |
| `claude_desktop_config.json` | Example Claude Desktop MCP config (generic placeholder paths) |
| `.mcp.json` | Example Claude Code MCP config (generic placeholder paths) |
| `cml-topology.yaml` | CML topology for the 3-device lab + External Connector |
| `example-queries.md` | Plain-English prompts to try, one per tool, plus the headline OSPF query |

## License

MIT
