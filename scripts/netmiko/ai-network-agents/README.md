# AI Network Agent -- Bounded Security Audit Companion

The companion kit for the bounded network AI agent build: an agent with real
network tools that audits a live lab, finds a real CVE by checking running
configs against Cisco's live PSIRT API, writes the fix, and then gets stopped
by a server-side boundary until a named human approves the change.

**Video:** (video link coming with the companion episode)

## Where the code lives

The full agent -- the MCP server, the boundary, the audit detectors, and the
test suite -- lives in the Hardrails repo, because the boundary IS the
framework's reference implementation:

- Framework front door: <https://gtalkstech.com/hardrails>
- Code + spec: <https://github.com/GTalksTech/hardrails> (install and run docs
  in `netagent/README.md` there)

This folder holds the lab context and the exact prompts from the video so you
can replicate the demo end to end.

## Lab Topology

The base lab is the same three-device CML setup used across other G Talks Tech
builds (see `../mcp-network-assistant/` for the base topology and its CML
YAML), extended for the security-audit scenario:

| Piece | Purpose |
|-------|---------|
| edge-rtr-01 (IOL) | Edge router; inbound ACL (`PROTECT_SERVERS`) guards the server subnet on its server-facing path |
| core-rtr-01 (IOL) | Core router; deliberately dual-homed into an untrusted segment (172.16.99.0/24) with a route to the server subnet -- the staged cross-device gap |
| access-sw-01 (IOL-L2) | Access switch |
| Servers subnet | 10.10.30.0/24 (VLAN 30), an HTTP server as the reachable target |
| Untrusted segment | 172.16.99.0/24 on an unmanaged switch, with a test client to prove the path |
| NetBox (netbox-docker) | Source of truth the agent compares reality against, at `http://localhost:8000` |

The point of the staging: neither router's config is wrong on its own. The edge
filters the front door; the core offers an unfiltered side path. Only reading
both configs together exposes it, which is exactly the kind of finding the
agent is for.

[`cml-topology.yaml`](cml-topology.yaml) in this folder is the ready-to-import
extended lab with the device configs embedded, pulled from the validated lab
itself. Import it into CML, start the nodes, and the staged findings are live.
Device and console credentials are the standard public lab set. All seven nodes
carry their configs in the import, including the two Linux endpoints: the
net-tools attacker (172.16.99.10) and the nginx server (10.10.30.10) bring up
their addressing from an embedded boot script, and nginx serves on port 80.

## Prereqs

- CML (the lab above) with SSH reachable from your host
- Python 3.11+ on the host, `pip install hardrails[lab]`
- NetBox via [netbox-docker](https://github.com/netbox-community/netbox-docker)
  (optional: the drift finding needs it; the sweep tells you loudly if it
  cannot reach it)
- Cisco PSIRT openVuln API credentials for live CVE data (optional: a frozen
  cache ships with the code so clone-and-run works offline)
- Claude Code (or any MCP host) wired to the server per the Hardrails
  `netagent/README.md`

Lab credentials are the standard public lab set (`admin` / `cisco123`).

## The demo prompts

See [`example-prompts.md`](example-prompts.md) for the exact prompts from the
video, in order, with what to expect from each.

## Safety note

The agent's write path is gated server-side: one write tool, blocked unless it
carries a named human approval for one device, every call logged to an
append-only audit file. That is enforced in code, not requested in a prompt.
Run it against labs, not production. The design is the point; the video and the
Hardrails spec walk through why.
