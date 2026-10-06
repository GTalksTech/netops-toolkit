# Quickstart: Goose on Ollama with a Local MCP Server

**Author:** Garrett Masters, G Talks Tech
**Tested on:** Goose CLI v1.49.0, Ollama 0.33.3, `qwen3.8:latest` (digest
`22130167c4c2`), FastMCP 3.4.5, macOS on a MacBook Pro M3 Max with 64 GB.
Current releases as of 2026-10-06 are Goose v1.53.0 and Ollama 0.40.0; we have
not re-tested on them.

What you end with: the Goose CLI driving `netops-mcp-server.py` on a local
model, where the three read tools run without a dialog, the write tool asks
every time, and shell is off the table.

Format: Pre-check, Action, Post-check, Rollback. The Rollback section stands
on its own; you do not need to read Action to use it.

---

## Pre-check

**1. Ollama is current enough and the model is present.**

```bash
ollama --version          # tested on 0.33.3; qwen3.8 support arrived in 0.32.12
ollama pull qwen3.8:latest
ollama list               # note the ID column for qwen3.8:latest
```

We tested digest `22130167c4c2`. The `latest` tag moves, so if your ID
differs you are on a newer build than the one tested here.

**2. Ollama's context window is 65536.** An agent session fills context fast,
and Goose needs to know the real size (Action step 2).

- **macOS:** open the Ollama app, Settings, and set Context length to 64k.
  What we saw in our lab: the slider sat at 256k, `launchctl getenv
  OLLAMA_CONTEXT_LENGTH` was empty, and Ollama still granted 65536, most
  likely capping the window to what fit in memory. So neither setting is proof
  on its own. Set the slider explicitly and verify (below). You can also run
  `launchctl setenv OLLAMA_CONTEXT_LENGTH 65536` and restart the app, but we
  did not test which of the two wins when they disagree.
- **Linux (systemd):** `sudo systemctl edit ollama.service`, add
  `Environment="OLLAMA_CONTEXT_LENGTH=65536"` under `[Service]`, then
  `sudo systemctl daemon-reload` and `sudo systemctl restart ollama`.
- **Windows:** quit Ollama from the taskbar, open Settings (Windows 11) or
  Control Panel (Windows 10), choose "Edit environment variables for your
  account", add `OLLAMA_CONTEXT_LENGTH` with the value `65536`, then start
  Ollama again from the Start menu.

The Linux and Windows steps follow Ollama's own FAQ; this lab ran on macOS
only.

Verify: run any prompt, then look for `n_ctx_slot = 65536` in the Ollama
server log (macOS: `~/.ollama/logs/server.log`). That is the line we checked
on 0.33.3.

**3. Ollama cloud is off, if you want everything to stay local.** In the
Ollama app's Settings, turn the cloud toggle off, or set
`"disable_ollama_cloud": true` in `~/.ollama/server.json` and restart Ollama.
Models ending in `:cloud` in `ollama list` run remotely. We found cloud
switched on in our own lab after an earlier shoot, so check rather than
assume.

**4. A Python venv with the server's two packages.**

```bash
python3 -m venv ~/venvs/netauto
~/venvs/netauto/bin/pip install "fastmcp==3.4.5" netmiko
```

(Or `pip install -r requirements.txt` from this folder. Same two packages.)

**5. The server and its configs sit in one folder.** Put
`netops-mcp-server.py`, `core-rtr-01.cfg`, `edge-rtr-01.cfg` and
`access-sw-01.cfg` together, for example in `~/netops-agent/`. The server looks
for the configs next to itself. If they are missing, it registers fine and then
fails with file-not-found in the middle of a task.

**6. The server answers an MCP handshake on its own.**

```bash
cd ~/netops-agent
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'; sleep 2; } \
  | ~/venvs/netauto/bin/python netops-mcp-server.py
```

Expect a reply naming the server `netops-local`, then a tool list with four
tools. Keep the `sleep 2`. Without it the pipe closes after the first message
and the server exits before it answers `tools/list`. That is the test, not the
server.

**7. The lab is reachable (live tools only).**

```bash
ping -c 2 192.168.1.250     # core-rtr-01
ping -c 2 192.168.1.251     # access-sw-01
ping -c 2 10.0.0.2          # edge-rtr-01, routed through core-rtr-01
ssh admin@192.168.1.250     # password cisco123, then: show ip interface brief
```

If core-rtr-01 says "no route to host" while access-sw-01 answers, the router
may be fine and the ARP entry on your machine stuck. Ping your machine from the
router once (hop to it through access-sw-01) and it clears. No lab at all?
`list_interfaces` still works from the cached files.

---

## Action

**1. Install the Goose CLI.**

```bash
curl -fsSL https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh | bash
```

This installs the current stable release. We tested v1.49.0. The installer
also takes a `GOOSE_VERSION` variable if you want to match our version
(`... | GOOSE_VERSION=v1.49.0 bash`); that option is documented in the
installer, but we did not use it ourselves.

Run from a terminal, the installer goes straight into the interactive
`goose configure` wizard. It does not drop you back at a shell first. Answer
it like this:

- Share anonymous usage data: your call (we said No).
- "How would you like to set up your provider?" Three options. Two are cloud
  logins and one of those is labelled Recommended. Pick **Manual
  Configuration**.
- Provider **Ollama**, host **localhost**, model **qwen3.8:latest**.

Then confirm: `goose --version`.

**2. Tell Goose the real context size.**

```bash
echo 'export GOOSE_CONTEXT_LIMIT=65536' >> ~/.zshrc    # or ~/.bashrc
source ~/.zshrc
```

Without it, Goose v1.49.0 assumed a 128000-token window for this model while
Ollama was giving it 65536. Goose also uses that number to decide when to
compact the conversation, so a long session could lose its middle while the
status line still says there is room. Goose reads this variable when the CLI
starts, not from `config.yaml`. The Goose desktop app does not read your shell
profile, so this fix is for the CLI.

**3. Add the server as an extension.**

Run `goose configure`, choose **Add Extension**, then **Command-line
Extension**:

- Name: `netops-mcp-server` (the rule names in step 6 depend on this exact name)
- Command: the WHOLE command line, interpreter and script path together, for
  example `/Users/<you>/venvs/netauto/bin/python /Users/<you>/netops-agent/netops-mcp-server.py`
- Timeout: `300`
- Environment variables: none needed against this lab (see step 5)

**Easy mistake: the command prompt wants the whole command line.** There is
no separate prompt for arguments; Goose splits what you type into `cmd` and
`args`. If you enter only the interpreter (we did, the first time), you end up
with `args: []` and Goose launches a bare Python prompt instead of the server.
The fix is either to re-add the extension with the full command, or to open
`~/.config/goose/config.yaml`, find the block the wizard wrote, and add the
script path under `args:`. Either way the block should end up like this:

```yaml
  netops-mcp-server:
    enabled: true
    type: stdio
    name: netops-mcp-server
    description: Netops MCP Server
    cmd: /Users/<you>/venvs/netauto/bin/python
    args:
    - /Users/<you>/netops-agent/netops-mcp-server.py
    envs: {}
    env_keys: []
    timeout: 300
    cwd: null
    bundled: null
```

Use full paths. Goose starts the server itself over stdio. There is no port and
nothing for you to launch.

**4. Change the mode. It ships in auto.**

**Setup trap: Goose ships in `auto` mode and the wizard never asks.**
In auto, the agent runs tools, including shell, without asking you anything.
Out of the box, our first session ran a network tool with no prompt and no
click. Later, in auto, our honestly labeled write tool changed the router
with no approval step (that run used `goose run`, not an interactive
session).

Start a session and check:

```text
goose session
/status          # shows Mode: auto on a fresh install
/mode smart_approve
/status          # confirm the change
```

Type the mode name. A bare `/mode` with no argument is not treated as a
command. It goes to the model as a chat message, and ours answered with
confidence that no such command existed.

In our lab the mode set this way was saved to `config.yaml` as
`GOOSE_MODE: smart_approve` and fresh sessions picked it up. The lab ran
`smart_approve`. `approve` is the stricter documented option: it asks about
every tool you have not given your own rule. Either one, never `auto`.

**5. Credentials: the environment-variable path.**

Goose starts the server as a background process with no terminal attached, so
a password prompt (`getpass`) has nothing to read from and would hang or fail.
That is why the server reads `NETOPS_USER` and `NETOPS_PASS` from its
environment and falls back to `admin` / `cisco123`, the public lab
credentials. Against this lab, leave the extension's environment variables
empty. Against a different lab, set those two variables in the extension's
environment-variable field when you add it. Our lab ran on the defaults, so
that field was never exercised.

**6. Set a rule for every tool.**

Run `goose configure`, then **goose settings**, then the tool permission
option ("Choose a tool to update permission"). Tool names are
`<extension name>__<tool name>`, with a double underscore. Set:

| Tool | Rule |
|---|---|
| `netops-mcp-server__list_interfaces` | Always Allow |
| `netops-mcp-server__ping_host` | Always Allow |
| `netops-mcp-server__show_interfaces_live` | Always Allow |
| `netops-mcp-server__set_interface_description` | Ask Before |
| `shell` | Never Allow |

Goose saves these to `~/.config/goose/permission.yaml`. That file does not
exist until you set your first rule. The finished file should look like
[permission.yaml.example](permission.yaml.example).

Why a rule for every tool: Goose checks your own rule first. Without one, in
`smart_approve` it goes by the tool's `readOnlyHint` label, and if there is no
label it asks the local model to judge. Your rule is the only one of those you
control.

Why reads get Always Allow: approval fatigue. With nothing set, one simple
task threw three dialogs, and two of them were the bundled todo extension
updating its own checklist. That is how people end up clicking Always Allow on
everything. If the todo dialogs still wear on you, give
`todo__todo_write` Always Allow too; it only edits the agent's own list.

Why shell gets Never Allow: given a general shell next to purpose-built tools,
this model reached for the shell, and with a vague prompt it produced a wrong
answer. With the shell removed, the same vague prompt got the right answer. If
you want shell gone entirely, disable the `developer` extension in
`goose configure`.

---

## Post-check

Start a fresh session for each check. An earlier answer in the same session
can stand in for a tool call and hide what you are testing.

**1. Mode and context.** `/status` shows your mode (not `auto`) and a context
figure out of 65536 (it may display as 66k).

**2. A read runs without a dialog.** Ask: `List the interfaces on core-rtr-01`.
Expect no dialog, a `list_interfaces` call, every interface in the cached
config including the ones with no IP address, and the capture's "Last
configuration change" stamp. The answer should treat it as cached data.

**3. The write asks, and shows you what it will do.** Ask:
`Set the description on interface Ethernet0/3 of core-rtr-01 to LAB-TEST`.
Expect "Goose would like to call the above tool, do you allow?" with the tool
name and its arguments. Pick **Allow**, which allows this one call. **Always
Allow** would write a permanent rule into your file, which is the opposite of
what you want for a write. Then verify from a second terminal, not through the
agent:

```text
ssh admin@192.168.1.250
show running-config interface Ethernet0/3
```

Expect `description LAB-TEST`. The change is in running-config only. If the
agent offers to copy running-config to startup-config, say no; ours offered
without being asked.

**4. A denied write stops cleanly.** Repeat the ask and pick **Deny**. Ours
reported that the call was declined and took no other action. It did not
retry or reach for another tool.

**5. Shell is refused.** Ask it to use its shell tool to run `ls -la`. It
should not run. Ours called `shell`, got no dialog, had the call declined, and
stopped on its own without retrying or working around it.

**6. The rule file matches.** `cat ~/.config/goose/permission.yaml` and check
the `user:` block against the table in Action step 6. You may also see a
`smart_approve:` block. Goose writes that one itself, and in our lab it held
only "ask before" entries.

---

## Rollback

Complete on its own. Do the parts that apply.

**1. Remove any description the agent set.** Either ask the agent to remove
the description on Ethernet0/3 of core-rtr-01 and approve it, or do it by
hand:

```text
ssh admin@192.168.1.250
configure terminal
interface Ethernet0/3
no description
end
show running-config interface Ethernet0/3
```

The tool never saves to startup-config, so a reload of the device also reverts
it, unless someone ran `copy running-config startup-config` in between.

**2. Take the write tool away from Goose.** Fastest: in
`~/.config/goose/permission.yaml`, move
`netops-mcp-server__set_interface_description` to `never_allow:`. To remove
the whole server, delete the `netops-mcp-server:` block from
`~/.config/goose/config.yaml`, or set `enabled: false` in it.

**3. Remove your tool rules.** Delete `~/.config/goose/permission.yaml`. Goose
recreates it the next time you set a rule. Any `smart_approve:` entries in it
go too.

**4. Decide on the mode.** If you keep Goose, leave it on `approve` or
`smart_approve`. The shipped default is `/mode auto` (or `GOOSE_MODE: auto` in
`~/.config/goose/config.yaml`), which runs every tool without asking, so only
go back to it with the server removed.

**5. Undo the context setting.** Remove the `export GOOSE_CONTEXT_LIMIT=65536`
line from `~/.zshrc` (or `~/.bashrc`) and open a new terminal. Then, on the
Ollama side:

- macOS: reset the Ollama app's Context length slider if you changed it, run
  `launchctl unsetenv OLLAMA_CONTEXT_LENGTH` if you set it, and restart the
  app.
- Linux: `sudo systemctl edit ollama.service`, delete the
  `OLLAMA_CONTEXT_LENGTH` line, then `sudo systemctl daemon-reload` and
  `sudo systemctl restart ollama`.
- Windows: quit Ollama, delete `OLLAMA_CONTEXT_LENGTH` under "Edit environment
  variables for your account", and start Ollama again.

**6. Remove Goose completely.** `which goose` shows where the installer put
the binary; delete it. Then delete `~/.config/goose/` (config, rules,
history), `~/.local/share/goose/` (saved sessions) and `~/.local/state/goose/`
(logs). The server files and the venv are yours to keep or delete; nothing
else points at them.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Goose hangs on the extension, or you see a Python prompt | `args:` is empty: the wizard got only the interpreter. Action step 3. |
| `list_interfaces` fails with file not found | The `.cfg` files are not in the same folder as the server. |
| Live tools fail with "no route to host" | The lab is down, the macOS Local Network permission was denied for your terminal (System Settings, Privacy and Security, Local Network), or the stuck ARP case in Pre-check step 7. Our terminal already had the permission, so we never saw the dialog under Goose. |
| `/status` shows 128k of context | `GOOSE_CONTEXT_LIMIT` is not set in the shell that started Goose. |
| Every task throws dialogs you did not expect | Mode is `approve` and the tool has no rule, or it is the todo extension. Action step 6. |
| The model states which server, extension or file it is using | Check it. In our lab a model listed the wrong extensions, and another named the wrong MCP server, both with confidence. Test the wiring by calling a tool, not by asking about it. |
