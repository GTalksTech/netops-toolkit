# Example Queries

Plain-English prompts you can paste into Claude (Desktop or Code) once
the `network-assistant` MCP server is wired up. Each one exercises at
least one of the 5 tools in `server.py`.

For best results, use these inside a project (Claude Desktop) or a
session (Claude Code) that knows about your lab. See the README for the
recommended system prompt.

---

## 1. list_devices

> "List all devices in my network inventory."

Claude calls `list_devices()` and returns the 3 lab devices with their
hosts and descriptions.

---

## 2. get_device_status

> "Give me a status summary for core-rtr-01."

Claude calls `get_device_status("core-rtr-01")`, which bundles
`show ip interface brief`, `show ip ospf neighbor`, `show ip route`, and
`show cdp neighbors` into a single SSH session. Watch for Claude
proactively flagging anything unusual in the OSPF neighbor table without
being asked.

---

## 3. run_show_command (allowed)

> "What does the routing table look like on edge-rtr-01?"

Claude calls `run_show_command("edge-rtr-01", "show ip route")`. This is
an allowed read-only command, so it runs normally.

---

## 4. run_show_command (blocked)

> "Show me the running configuration of core-rtr-01."

Claude calls `run_show_command("core-rtr-01", "show running-config")`.
The `BLOCKED_TOKENS` whitelist catches `running` and returns a BLOCKED
message instead of the config. Claude never receives the actual
running-config text. Watch what Claude does next -- it typically offers
to use `find_in_config` instead.

---

## 5. find_in_config (with redaction)

> "Find any SNMP community strings configured on core-rtr-01."

Claude calls `find_in_config("core-rtr-01", "snmp")`. The matching lines
come back with the community string value replaced by `<REDACTED>` --
Claude can still tell you the community string exists, what mode it's
in, and whether there's an ACL on it, without ever seeing the actual
value.

---

## 6. compare_running_to_startup

> "Has anything changed on core-rtr-01's running config that isn't saved
> to startup yet?"

Claude calls `compare_running_to_startup("core-rtr-01")` and returns a
diff showing any unsaved configuration drift.

---

## 7. The Headline Query (OSPF Troubleshooting)

This is the on-camera query from the video -- a single open-ended
prompt that forces Claude to chain multiple tools and synthesize a
diagnosis from live device output:

> "Something's off with OSPF on my network. Take a look and tell me what
> you find."

In testing, Claude worked through the following chain on its own, with
no further prompting:

1. `list_devices()` -- inventories what's available, finds both
   OSPF-capable routers
2. `get_device_status()` on both `core-rtr-01` and `edge-rtr-01` --
   pulls status from both sides; OSPF neighbor tables come back empty
3. `find_in_config()` -- searches OSPF-related config on both devices
4. `run_show_command()` -- checks the OSPF hello/dead timer values on
   the relevant interface

The result: a complete diagnosis (Hello/Dead timer mismatch between
`core-rtr-01` and `edge-rtr-01`), the root cause, and the one-line fix
command -- all from real `show` output, in about 30 seconds.

---

## 8. Multi-device comparison

> "Compare the interface status on core-rtr-01 and access-sw-01. Are
> there any down interfaces I should know about?"

Forces Claude to call `get_device_status()` on two devices and reason
across both results.

---

## 9. CDP / topology check

> "Based on CDP neighbors, can you sketch out how my lab devices are
> connected to each other?"

Uses the `cdp_neighbors` field returned by `get_device_status()` across
all 3 devices to reconstruct the topology.

---

## 10. General networking question (no tools expected)

> "What's the difference between OSPF area 0 and a totally stubby area?"

This is a general networking question, not a question about your lab.
With a properly scoped project system prompt (see README), Claude
answers this conversationally without invoking any tools.
