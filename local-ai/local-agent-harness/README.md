# Local Agent Harness: One Write Tool, Two Harnesses

An MCP server with three read tools and one write tool, wired into two agent
harnesses running on local models: Goose (CLI) on Ollama, and Bionic. The
point is not the model. The point is what sits between an agent and your
network gear, and which parts of that you have to build and set yourself.

> **Companion video:** [Before You Let an AI Agent Touch Your Network, Set These 3 Guardrails](https://youtu.be/dsY4_s3NL04)
>
> **Write-up:** [A Local AI Agent on a Real Router: The Three Guardrails That Held](https://gtalkstech.com/blog/local-agent-harness/)
>
> **Mailing list:** [join.gtalkstech.com](https://join.gtalkstech.com)

This replaces the pre-lab follow-along that lived here. The lab is done, the
numbers below are measured, and the corrections to the pre-lab version are
listed at the bottom.

## What's in this folder

| File | What it is |
|---|---|
| [quickstart-goose-ollama.md](quickstart-goose-ollama.md) | The main runbook. Goose driving this server on Ollama, including the two setup traps, the per-tool rule set, and the credential path. Pre-check, Action, Post-check, Rollback. |
| [quickstart-bionic.md](quickstart-bionic.md) | The shorter Bionic runbook: install, the MCP registration form, and why to give it read tools only. |
| [permission.yaml.example](permission.yaml.example) | The recommended end-state Goose permission file: reads always allowed, the write asks first, shell never allowed. |
| [mcp-hygiene-checklist.md](mcp-hygiene-checklist.md) | One page, ten checks before any MCP server gets read or write access to network gear. |
| [netops-mcp-server.py](netops-mcp-server.py) | The MCP server (FastMCP + Netmiko, stdio). Four tools, described below. |
| [requirements.txt](requirements.txt) | The server's two packages, with FastMCP pinned to the tested version. |
| `core-rtr-01.cfg`, `edge-rtr-01.cfg`, `access-sw-01.cfg` | Cached `show run all` captures the `list_interfaces` tool reads. They must sit in the same folder as the server. |

## The four tools

| Tool | Reads or writes | What it does |
|---|---|---|
| `list_interfaces` | Read, cached | Parses a saved config file. Returns every interface, flags the ones with no IP address or shut down, and prints the config's own "Last configuration change" stamp so the answer says how old it is. |
| `show_interfaces_live` | Read, live | SSHes to the device and returns `show ip interface brief`. |
| `ping_host` | Read, live | Pings a host twice from the machine running the server. |
| `set_interface_description` | **Write** | Sets or removes the description on one interface, in running-config only (never saved to startup), and returns the interface config before and after. Annotated honestly as not read-only. |

The server only accepts three device names: core-rtr-01, edge-rtr-01 and
access-sw-01. Anything else gets refused before a connection is attempted.

The cached tool and the live tool are split on purpose. Ask the same question
both ways and any difference between them is config drift. In our lab the
live router had drifted from the capture, and that is exactly what the agent
had to notice.

## Topology

The same three-device CML lab used across the G Talks Tech kits: two IOL
routers and one IOL-L2 switch, with an External Connector bridged to the host
network. The topology file is in the sibling kit:
[`../local-ai-network-engineers/cml-topology.yaml`](../local-ai-network-engineers/cml-topology.yaml).
It carries the topology, not device configs, so the nodes boot blank. Give
them the management addresses below, a local `admin` user, and SSH.

| Device | Management IP | Notes |
|---|---|---|
| core-rtr-01 | 192.168.1.250 | LAN side, reached directly |
| access-sw-01 | 192.168.1.251 | LAN side, reached directly |
| edge-rtr-01 | 10.0.0.2 | Loopback, reached by routing through core-rtr-01. Your machine needs a route to 10.0.0.2 via 192.168.1.250. Every check in the runbooks uses core-rtr-01, so you can skip edge-rtr-01. |

Credentials: `admin` / `cisco123`. These are real lab credentials for a
publicly replicable topology, published on purpose. The server reads them from
the `NETOPS_USER` and `NETOPS_PASS` environment variables and falls back to
these defaults, so against this lab you set nothing.

No lab? `list_interfaces` works from the cached files alone. The other three
tools need the devices.

## Prereqs

- A machine that can run a local model with tool calling. Everything here was
  run on a MacBook Pro M3 Max with 64 GB of unified memory.
- [Ollama](https://ollama.com) with the context window set to 65536 (Goose
  path) or [Bionic](https://lmstudio.ai/docs/bionic) (Bionic path).
- Python 3.10+ in a virtual environment with `fastmcp` and `netmiko`:
  ```bash
  python3 -m venv ~/venvs/netauto
  ~/venvs/netauto/bin/pip install -r requirements.txt
  ```
- The server file and its three `.cfg` files together in one folder. The
  server finds the configs next to itself, not in your working directory.
- macOS or Linux. `ping_host` uses Unix `ping` flags.
- Network reach from that machine to 192.168.1.0/24 and to 10.0.0.2, for the
  live tools.

## Run it under Goose (CLI)

Full steps in [quickstart-goose-ollama.md](quickstart-goose-ollama.md). The
short version:

1. Install the Goose CLI and walk its setup wizard to Ollama with
   `qwen3.8:latest`.
2. Add the server as a command-line extension. Give the wizard the WHOLE
   command line (interpreter plus script path). It splits what you type into
   the command and its arguments, so an interpreter alone leaves `args:`
   empty.
3. Goose ships in `auto` mode, which never asks before running a tool. Change
   the mode before the agent touches anything, and set a rule per tool (see
   [permission.yaml.example](permission.yaml.example)).
4. `export GOOSE_CONTEXT_LIMIT=65536` so Goose and Ollama agree on the window.

## Run it under Bionic

Full steps in [quickstart-bionic.md](quickstart-bionic.md). Register the
server through Settings > Integrations > MCP > Custom MCP, connection "On this
computer", and let Bionic start it for you. Give Bionic a read-only copy of
the server; the section below says why.

## Tested versions

| Component | Version |
|---|---|
| Goose CLI | v1.49.0 |
| Bionic | 1.1.6 |
| Model | `qwen3.8:latest`, digest `22130167c4c2` (Q4_K_M, 27.3B). The `latest` tag moves; check the digest with `ollama list`. |
| Ollama | 0.33.3 |
| FastMCP | 3.4.5 |
| OS | macOS, MacBook Pro M3 Max, 64 GB |

Both harnesses release often. As of 2026-10-06 the current releases are Goose
v1.53.0, Bionic 1.1.7 and Ollama 0.40.0, and we have not re-tested on them.
Behavior described here is for the versions in the table. The server itself
was also run on Linux (Ubuntu, Python 3.12): the MCP handshake and all three
read tools worked against the live lab.

## What the approval gate does and does not check

**Goose v1.49.0.** In `smart_approve` mode, Goose checks your own per-tool
rule first. If you have not set one, it checks the tool's `readOnlyHint`
annotation. If there is no annotation to go on, it asks the local model to
judge. None of those steps looks at what the tool actually does to a device.
So set your own rule for every tool, and read the servers you install,
because a label is taken at its word.

In `auto` mode, the shipped default, none of that applies. Our write tool
carried its honest label and still ran with no approval step. (That run used
`goose run`, not an interactive session, and we did not test a `user:`
ask-before rule while in auto.)

**Bionic 1.1.6.** The composer's command-approval menu covers shell commands.
We found no MCP approval setting in the app, and our MCP write ran with no
prompt in every mode we tried: Auto Review, Ask every time, and Off. So give Bionic read tools only, and put
any write behind a harness where you have set a rule for it.

## What actually protected the lab

Three things, all built or set by hand:

1. **Tool output that is complete and timestamped.** When `list_interfaces`
   left out interfaces with no IP address, the model got one interface right
   two times out of five. Once the tool returned every interface with the
   capture date, it got it right three times out of three (one of those runs
   already had the answer in context) and flagged the capture as stale on its
   own.
2. **An honest label plus your own rule.** The write tool says it writes, and
   a per-tool rule makes the harness ask before it runs.
3. **No write tools where nothing gates them.**

The model was the dependable part: no malformed tool call in any run, and a
clean stop when a write was denied. Where it slipped was judgment. It gave
confident causes with no evidence under them. Verify anything it tells you
about a device against the device.

## Known limits

- `ping_host` uses Unix `ping` flags. On Linux, `-W` is in seconds rather than
  milliseconds, so a host that silently drops pings makes the tool fail at its
  15-second timeout instead of returning ping's own output.
- The write tool only sets or removes interface descriptions, and only on the
  three named devices. It is a demonstration of a gated write, not a config
  tool.

## Corrections to the pre-lab version of this page

The follow-along published here before the lab said a few things the lab
settled differently:

- **Bionic and MCP tool calls.** It said Bionic shows a confirmation dialog
  before a tool call runs. That dialog is documented for classic LM Studio. In
  Bionic 1.1.6 we saw no MCP confirmation in any approval mode.
- **Where Goose keeps permissions.** It asked whether rules live in a separate
  `permission.yaml`. They do: `~/.config/goose/permission.yaml`, which does not
  exist until you set your first rule. The Goose docs list it.
- **Whether the smart_approve judgment can override your rule.** It cannot.
  Your own rule is checked first, and the lab confirmed it.

---

*Part of [netops-toolkit](https://github.com/GTalksTech/netops-toolkit) from
[G Talks Tech](https://www.youtube.com/@GTalksTechOfficial).*
