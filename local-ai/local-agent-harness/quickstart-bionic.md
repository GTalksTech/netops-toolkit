# Quickstart: Bionic with a Local MCP Server

**Author:** Garrett Masters, G Talks Tech
**Tested on:** Bionic 1.1.6 (released 2026-09-23), macOS on a MacBook Pro M3
Max with 64 GB. The current release as of 2026-10-06 is 1.1.7; we have not
re-tested on it.

What you end with: Bionic running the netops server's read tools over stdio,
with its approval menu set so shell commands ask first.

**Scope note, read this first.** Bionic's composer has a command-approval
menu (Off, Ask every time, Auto Review, Allow all). In 1.1.6 that menu covers
shell commands, and LM Studio's own changelog describes those settings as
shell modes. We found no MCP approval setting in the app or the docs, and our
MCP write tool ran without a prompt in every mode we tried (Auto Review, Ask
every time, and Off). So in Bionic, give the agent read tools only.

---

## Pre-check

**1. A read-only copy of the server.** In the folder that holds
`netops-mcp-server.py` and its three `.cfg` files, copy the server to
`netops-readonly.py`. In the copy, delete the `set_interface_description`
tool: the line starting `@mcp.tool(annotations=` and the whole function under
it, down to the line before `if __name__ == "__main__":`. Keep the copy in the
same folder so it still finds the `.cfg` files.

**2. The copy lists three tools.**

```bash
cd ~/netops-agent
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'; sleep 2; } \
  | ~/venvs/netauto/bin/python netops-readonly.py
```

Expect `list_interfaces`, `show_interfaces_live` and `ping_host`, and no
`set_interface_description`.

**3. Classic LM Studio is quit.** Both apps cannot serve local inference at
the same time.

---

## Action

**1. Install Bionic.**

```bash
brew install --cask --force lm-studio-bionic
```

Then accept the in-app update if one is offered. If you ever installed Bionic
by hand, brew refuses with "It seems there is already an App at
'/Applications/Bionic.app'". The `--force` flag takes over the app bundle;
your models and settings live outside it and survive.

**2. Create a project.** Leave "Working directory (optional)" empty. Know that
this does not remove shell: with no working directory, Bionic runs shell
commands in its own per-project folder under
`~/.lmstudio/apps/bionic/projects/`. The approval menu (step 4) is what
controls shell.

**3. Pick a model** with tool support that fits your memory. What the gate
does is host behavior, so a small model is enough to follow this runbook. We
used Qwen3.5 9B MLX (5.9 GB).

**4. Set the approval menu.** Click the shield icon beside `+` in the
composer ("Choose how Bionic gets command approvals") and choose **Ask every
time**, or **Off** if you want no shell at all. Auto Review is the default.

**5. Register the server. It is a form, not a JSON file.** Settings >
Integrations > MCP > **Custom MCP** ("Connect an MCP server that is not in
the catalog"). Turn on Show advanced options, then fill in:

| Field | Value |
|---|---|
| Name | `netops` |
| Connection | **On this computer** (this is stdio) |
| Command | Full path to your venv's Python, e.g. `/Users/<you>/venvs/netauto/bin/python` |
| Arguments | Full path to `netops-readonly.py` |
| Environment variables | Empty. The server falls back to the public lab creds, `admin` / `cisco123`. For another lab, set `NETOPS_USER` and `NETOPS_PASS` here. |
| Working directory | Empty. The server finds its `.cfg` files next to itself. |
| Request timeout | `120` (the default is 60; an SSH connect can take 15 seconds, and a timeout looks like a failure of something else) |

**Do not start the server yourself.** With "On this computer", Bionic
launches the command, talks to it over the process's stdin and stdout, and
manages it. A copy you start by hand in a terminal is connected to nothing
and just waits for keyboard input.

Bionic keeps custom MCP servers in
`~/.lmstudio/apps/bionic/.internal/ng-mcp.json`, separate from classic LM
Studio's `~/.lmstudio/mcp.json`. It does not read the classic file.

---

## Post-check

**1. The server shows as connected.** Settings > MCP > netops should read
"Connected" with three tools ready.

**2. Allow Local Network access when macOS asks.** The first tool that
touches the LAN triggers "Allow 'Bionic' to find devices on local networks?".
That is macOS, not Bionic's approval gate. Click **Allow**. If you deny it,
every live tool fails with "No route to host", which looks exactly like a
down lab. To fix it later: System Settings, Privacy and Security, Local
Network, and switch Bionic on.

**3. Test the wiring by using a tool.** In a fresh session, ask:
`List the interfaces on core-rtr-01`. Expect a table of every interface in the
cached config with the capture's "Last configuration change" stamp.

Do not ask the model which MCP servers are connected. It sees one flat list of
tools and cannot tell where each came from. Ours went looking on disk, read
the stale classic LM Studio file, and named the wrong server with confidence.

**4. Shell asks.** With the menu on Ask every time, ask it to run `ls` in the
terminal. Expect a "Confirm shell command" dialog before anything runs.

---

## Rollback

Complete on its own.

**1. Remove the server.** Settings > Integrations > MCP > netops, then
Installation > **Remove MCP**. Or switch its Status off to stop it without
removing it.

**2. Pick up server edits.** Bionic keeps the server process running across
sessions, so editing the server file changes nothing until it restarts.
Switch the server's Status off and back on; the new process starts at the next
tool call.

**3. If a live tool ever changed a device.** The read-only copy cannot. If you
registered the full server anyway and a description was set, remove it by
hand:

```text
ssh admin@192.168.1.250
configure terminal
interface Ethernet0/3
no description
end
show running-config interface Ethernet0/3
```

Use the device and interface the agent touched. The tool writes running-config
only, never startup-config.

**4. Reset the approval menu** to whatever you had before (Auto Review is the
shipped default).

**5. Remove Bionic completely.** `brew uninstall --cask lm-studio-bionic`.
Projects and settings live under `~/.lmstudio/apps/bionic/`, outside the app
bundle, so check there if you want them gone too.
