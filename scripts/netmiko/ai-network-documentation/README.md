# AI-Powered Network Documentation Workflow

Generate a complete network runbook from live device output using AI.
Collect show commands, redact sensitive data, build an AI-ready prompt,
and restore real values into the finished document.

**Video:** [G Talks Tech - EP004](https://www.youtube.com/@GTalksTechOfficial)

## What You Get

| Script | Purpose |
|--------|---------|
| `01-collector.py` | SSH into devices, run show commands, save output |
| `02-redactor.py` | Strip credentials, IPs, hostnames, and other sensitive data |
| `03-prompt-assembler.py` | Build a paste-ready prompt with token estimate |
| `04-restore.py` | Swap placeholders back to real values in the AI-generated doc |
| `05-diagram-generator.py` | Generate a draw.io network topology diagram (no AI needed) |

## Lab Topology

Three-device CML Free lab: edge router, core router, and L2 access switch.

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

**New to any of these?** Step-by-step setup guides are in the
[getting-started](../../../getting-started/) folder:

| Guide | What it covers |
|-------|---------------|
| [Install WSL2](../../../getting-started/install-wsl2.md) | Windows Subsystem for Linux setup |
| [Install Python 3](../../../getting-started/install-python.md) | Python, pip, and virtual environments |
| [Install Netmiko](../../../getting-started/install-netmiko.md) | The SSH automation library used by these scripts |
| [Install VMware Workstation Pro](../../../getting-started/install-vmware.md) | Free hypervisor for running CML |
| [Install CML Free](../../../getting-started/install-cml-free.md) | Cisco's network simulation platform |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/GTalksTech/netops-toolkit.git
cd netops-toolkit/scripts/netmiko/ai-network-documentation

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Lab Setup

1. Import `NetMiko-Lab.yaml` into CML Free
2. Start the lab and wait for all devices to boot
3. Apply the base configurations from `lab-configurations.cfg`
   (paste each device's config block into its console)
4. Verify SSH access:
   ```bash
   ssh admin@192.168.1.250   # core-rtr-01
   ssh admin@192.168.1.251   # access-sw-01
   ssh admin@10.0.0.2        # edge-rtr-01 (via loopback)
   ```

## Workflow

### Step 1: Collect show command output
```bash
python 01-collector.py
# Enter: admin / cisco123 / cisco123 (enable secret)
# Output: output/<timestamp>/<device>.txt
```

### Step 2: Redact sensitive data
```bash
python 02-redactor.py --input-dir output/<timestamp>/ --redact-all
# Output: output/<timestamp>/redacted/<device>.txt + map.json
```

### Step 3: Build the AI prompt
```bash
python 03-prompt-assembler.py --input-dir output/<timestamp>/redacted/
# Output: output/<timestamp>/prompt-<timestamp>.txt
```

### Step 4: Generate the runbook
Paste the prompt into Claude, ChatGPT, or any LLM.
Save the response as a `.md` file (e.g., `runbook.md`).

### Step 5: Restore real values
```bash
python 04-restore.py output/<timestamp>/runbook.md output/<timestamp>/redacted/map.json
# Output: runbook-restored.md with all real values back in place
```

### Bonus: Generate a network diagram
```bash
python 05-diagram-generator.py --input-dir output/<timestamp>/
# Output: output/<timestamp>/network-topology.drawio
# Open in draw.io -- no AI or tokens needed
```

## Adapting for Your Network

These scripts work with any Cisco IOS/IOS-XE device, not just this lab.
Edit the `DEVICES` list in `01-collector.py` with your own IPs and device types.
The redactor, prompt assembler, and restore scripts work on any collected output.

**Important:** Never use default credentials on production devices.
Always use `getpass` (already built in) to enter credentials at runtime.

## License

MIT
