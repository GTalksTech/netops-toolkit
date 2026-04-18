# AI-Powered Network Documentation Pipeline

Fully automated network documentation. SSH to finished runbook in one
command. No copy-paste step. Supports Claude, OpenAI, and Gemini.

**Video:** [G Talks Tech - EP005](https://www.youtube.com/@GTalksTechOfficial)
**Built on:** [EP004 - AI Network Documentation](../ai-network-documentation/)

## What This Is

EP004 produced a 5-script workflow with a manual paste step into a
browser AI. EP005 collapses all of that into a single script that hits
the provider API directly and writes a finished runbook to disk.

One script. One command. One provider flag.

```bash
python api-doc-pipeline.py
# or
python api-doc-pipeline.py --provider openai --diagram
```

## Lab Topology

Same three-device CML Free lab as EP004: edge router, core router, and
L2 access switch.

```
edge-rtr-01 (IOL)
  E0/0 -- 10.0.12.1/30
       |
       | WAN transit (10.0.12.0/30, OSPF area 0)
       |
  E0/1 -- 10.0.12.2/30
core-rtr-01 (IOL)
  E0/0 -- 192.168.1.250/24
       |
       | LAN (192.168.1.0/24)
       |
  E0/0 -- trunk (VLANs 1, 10, 20, 30)
access-sw-01 (IOL-L2)
  E1/0 -- ExternalCon (bridge to host)
```

| Device | Role | Management IP | Platform |
|--------|------|---------------|----------|
| edge-rtr-01 | Edge / WAN router | 10.0.0.2 (Lo0) | IOL (iol-xe) |
| core-rtr-01 | Core router | 192.168.1.250 | IOL (iol-xe) |
| access-sw-01 | Access switch | 192.168.1.251 | IOL-L2 (ioll2-xe) |
| ExternalCon | Bridge to host | -- | external_connector |

Credentials: `admin` / `cisco123`

## Prerequisites

- [VMware Workstation Pro](https://support.broadcom.com/group/ecx/downloads) (free for personal use)
- [CML Free](https://developer.cisco.com/docs/modeling-labs/cml-free/) with the included `NetMiko-Lab.yaml` imported
- Python 3.8+
- WSL2 (recommended) or any Linux/macOS terminal
- SSH access from your workstation to all three lab devices
- An API key for at least one provider (see below)

**New to any of these?** Setup guides are in the
[getting-started](../../../getting-started/) folder.

## API Key Setup

**Important:** API access is a SEPARATE paid account from Claude Pro,
ChatGPT Plus, or Gemini Advanced. Consumer chat subscriptions do NOT
include API access. You need a developer account for the provider you
want to use. For this use case costs are minimal (cents per run).

Pick one provider and sign up:

| Provider | Where to get a key | Env var |
|----------|--------------------|---------|
| Claude (default) | https://console.anthropic.com/ | `ANTHROPIC_API_KEY` |
| OpenAI | https://platform.openai.com/api-keys | `OPENAI_API_KEY` |
| Gemini | https://aistudio.google.com/apikey | `GEMINI_API_KEY` |

Set the env var in `~/.bashrc` so it persists across terminal sessions:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

## Quick Start

```bash
# Clone the repo
git clone https://github.com/GTalksTech/netops-toolkit.git
cd netops-toolkit/scripts/netmiko/api-automation-pipeline

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy the example inventory and edit for your devices
cp inventory-example.yml inventory.yml

# Run it
python api-doc-pipeline.py
```

On first run you will be prompted for SSH username, password, and
enable secret. Output goes to `output/<timestamp>/runbook.md`.

## Flags

| Flag | Purpose |
|------|---------|
| `--provider {claude,openai,gemini}` | AI provider (default: claude) |
| `--model MODEL` | Override the default model for the provider |
| `--inventory PATH` | Path to device inventory YAML (default: inventory.yml) |
| `--commands PATH` | Custom commands YAML (defaults baked in) |
| `--diagram` | Also generate a draw.io topology diagram |
| `--template PATH` | Custom prompt header .txt file |
| `--output-dir PATH` | Override output directory |
| `--skip-redaction` | Send raw output to API (lab use only) |
| `--no-redact-ips` | Skip IP redaction |
| `--no-redact-hostnames` | Skip hostname redaction |
| `--no-redact-macs` | Skip MAC redaction |
| `--no-redact-serials` | Skip serial number redaction |
| `--no-redact-usernames` | Skip username redaction |
| `--no-redact-certs` | Skip certificate stripping |
| `--no-redact-timestamps` | Skip timestamp redaction |
| `--no-redact-versions` | Skip IOS version redaction |
| `--no-redact-descriptions` | Skip interface description redaction |
| `--no-redact-vlan-names` | Skip VLAN name redaction |

## Model Selection

Defaults are set per provider and work out of the box. Use `--model` to
upgrade or downgrade.

| Provider | Default | Upgrade option | Budget option |
|----------|---------|----------------|---------------|
| Claude | `claude-sonnet-4-6` | `claude-opus-4-6` | -- |
| OpenAI | `gpt-5.4-mini` | `gpt-5.4` | `gpt-5.4-nano` |
| Gemini | `gemini-3-flash` | `gemini-3.1-pro-preview` | -- |

For a 3-device lab, the default Sonnet 4.6 produced the most detailed
runbook in testing. Opus 4.6 was a close second. Sonnet 4.2 was
noticeably weaker (fewer findings, no severity tags).

## Redaction

Full redaction is ON by default. Everything leaving your network for the
API is stripped of credentials, IPs, hostnames, MAC addresses, serial
numbers, usernames, certificates, timestamps, versions, interface
descriptions, and VLAN names. A `map.json` file stays on your machine
and is used to restore real values in the final runbook.

Granular flags let power users disable specific categories.
`--skip-redaction` disables everything (lab only).

## Inventory Format

`inventory.yml`:

```yaml
devices:
  - name: core-rtr-01
    host: 192.168.1.250
    device_type: cisco_ios
    role: router
```

`role: router` runs router commands. `role: switch` runs switch
commands. Supported `device_type` values are any Netmiko platform
(`cisco_ios`, `cisco_nxos`, `arista_eos`, etc.).

## Running Unattended (cron / Task Scheduler)

Three env vars let the script run without interactive prompts:

| Env var | Purpose |
|---------|---------|
| `NETDEV_USER` | SSH username |
| `NETDEV_PASS` | SSH password |
| `NETDEV_ENABLE` | Enable secret (set to empty string if not used) |

If the environment does not use enable secrets, set
`export NETDEV_ENABLE=""`. Unsetting the variable triggers the
interactive prompt; setting it to empty skips it.

### Linux / WSL2 (cron)

```bash
# Edit your crontab
crontab -e

# Run every Monday at 6 AM
0 6 * * 1 cd /home/you/netops-toolkit/scripts/netmiko/api-automation-pipeline && ./venv/bin/python api-doc-pipeline.py >> /home/you/pipeline.log 2>&1
```

Env vars need to be exported in the cron shell. Add them to a wrapper
script, or source `~/.bashrc` in the cron command.

### Windows (Task Scheduler)

Create a Basic Task:
- Trigger: Weekly, Monday, 6:00 AM
- Action: Start a program
- Program: `wsl.exe`
- Arguments: `-d Ubuntu -- bash -lc "cd /home/you/netops-toolkit/scripts/netmiko/api-automation-pipeline && ./venv/bin/python api-doc-pipeline.py"`

Set `NETDEV_USER`, `NETDEV_PASS`, `NETDEV_ENABLE`, and your API key in
`~/.bashrc` so they are available to the WSL shell.

## Security Notes

- Env vars stored in `~/.bashrc` are plain text on disk. This is fine
  for a personal home lab workflow.
- In a team environment or CI/CD pipeline, use a proper secrets
  manager (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, etc.)
  for both the API key and device credentials.
- Never commit `inventory.yml` with real device IPs or credentials.

## Known Limitations

- **Large environments:** The script assembles all device output into
  a single prompt. For environments with hundreds of devices you will
  hit the model context window. Token estimation warns at 80% of the
  context limit. Workaround: split `inventory.yml` by site or
  function and run the pipeline per shard.
- **Vendor coverage:** Tested on Cisco IOS/IOS-XE. Other Netmiko
  platforms should work but command sets assume IOS-style output.
  Use `--commands` to supply role-specific commands for other vendors.

## Files

| File | Purpose |
|------|---------|
| `api-doc-pipeline.py` | The pipeline |
| `inventory-example.yml` | Copy to `inventory.yml` and edit |
| `commands-example.yml` | Optional custom command sets |
| `NetMiko-Lab.yaml` | CML Free topology for the lab |
| `lab-configurations.cfg` | Base configs for the three lab devices |
| `requirements.txt` | Python dependencies |

## License

MIT
