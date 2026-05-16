# NetOps Toolkit

Practical AI workflows, scripts, and templates for senior network and IT engineers who want to stop doing everything the hard way.

Built and maintained by [G Talks Tech](https://gtalkstech.com). Every artifact here ships alongside a video on the [G Talks Tech YouTube channel](https://www.youtube.com/@GTalksTechOfficial) that demos it live against a real lab.

---

## Who This Is For

Senior mid-market network engineers, sysadmins, and IT operations professionals who:

- Are good at the work and tired of doing all of it manually
- Want copy-paste-and-adapt artifacts, not blog-post snippets
- Want AI in the workflow without the hype, and honesty about where it still fails

If you are early-career or looking for cert prep, this repo will not serve you well. The companion channel is built for engineers with 5 or more years in.

---

## What's Inside

Organized by what the artifact does, not by which video shipped it. Each section links out to the companion video where the workflow is demoed live.

### ai-prompts

Curated AI prompt packs for network engineering work. Every prompt is built on the same 4-piece structure (Role / Context / Constraint / Output Format) and carries a Public-safe or Enterprise-only safety label so you know whether it's safe to run on free-tier AI.

- [The Network Engineer's AI Prompt Pack](ai-prompts/prompt-engineering-network-engineers/) — 15 prompts across config generation, troubleshooting, documentation, compliance, and code generation. Multi-vendor adaptation notes for Cisco IOS-XE, Arista EOS, Junos, ArubaOS-CX, FortiOS, and PAN-OS. ([EP001 on YouTube](https://youtu.be/OEfeS8pyn_s))

### scripts/netmiko

Production-shaped Netmiko scripts that go from SSH to a finished artifact. Each folder has its own README with lab requirements, prereqs, and a matching CML topology so you can replicate the lab and run the script as-is.

- [ai-network-documentation](scripts/netmiko/ai-network-documentation/) — 5-script pipeline that turns raw show command output into AI-generated network runbooks. ([EP004 on YouTube](https://youtu.be/z89tfs7HV0I))
- [api-automation-pipeline](scripts/netmiko/api-automation-pipeline/) — One Python script. SSH to finished runbook in a single command via direct API call. No browser, no copy-paste. ([EP005 on YouTube](https://youtu.be/LA3_eIaBM1E))
- [quickstart-scripts](scripts/netmiko/quickstart-scripts/) — Starter scripts for connecting to a CML lab and running show commands. Use these to verify your environment before running the larger pipelines.

### scripts/powershell

PowerShell scripts for network evidence collection and triage on Windows endpoints.

- `Get-NetworkEvidence.ps1` — One-shot evidence collector. Captures DNS, ARP, route table, ping, traceroute, and TCP socket state in a single bundle ready to paste into a ticket.

### incident-response

Communication and evidence artifacts for the moment a ticket comes in saying "the network is down."

- [templates](incident-response/templates/) — Communication templates for initial notification, leadership updates, vendor and ISP escalation, post-incident summaries, and quick replies to "any update?" pings.
- checklists — Evidence collection checklists for network triage. (Stub. First entries arrive with the Prove It's Not the Network series.)

### getting-started

Step-by-step setup guides for the tools used in this repo. Aimed at engineers spinning up a working lab and Python environment from scratch.

- WSL2, Python 3, Netmiko, VMware Workstation Pro, CML Free.

### runbooks

Reserved for written runbooks that follow a Pre-check, Action, Post-check, Rollback structure. (Stub. First entries arrive with the Senior Engineer OS series.)

---

## How to Use This Repo

1. Find the artifact you need.
2. Read its README first. Every script and pack has lab requirements, prereqs, and limitations documented up front.
3. Replicate the lab if you want to run the script as-is. The IPs and hostnames in the examples are real (CML Free lab), not redacted. The "lab in a box" philosophy is that you should be able to clone the repo, spin up the matching CML topology, and have the script run with zero guessing.
4. Adapt for your environment. Once it works against the lab, point it at your gear.
5. Watch the companion video for the full walkthrough.

---

## Content Pillars

Everything in this repo maps to one of four pillars on the G Talks Tech channel:

- **AI-Powered Workflows.** Daily engineering tasks accelerated by AI. Prompt packs, AI-generated documentation, AI-assisted troubleshooting.
- **Prove It's Not the Network.** Triage workflows, evidence collection, and incident communication for the calls that start with "the network is broken."
- **Automation for Non-Developers.** Netmiko, Ansible, and Nornir starter scripts for engineers who think in CLI rather than IDE.
- **Senior Engineer OS.** Runbooks, documentation discipline, and the systems senior engineers build to stop firefighting and start operating at their title.

---

## Stay Connected

- Website: [gtalkstech.com](https://gtalkstech.com)
- Blog: [gtalkstech.com/blog](https://gtalkstech.com/blog)
- YouTube: [G Talks Tech](https://www.youtube.com/@GTalksTechOfficial)
- Mailing list: [join.gtalkstech.com](https://join.gtalkstech.com)
- LinkedIn: [Garrett Masters](https://www.linkedin.com/in/garrett-masters-ba6234101)
- Instagram: [@gtalkstechofficial](https://www.instagram.com/gtalkstechofficial/)
- X: [@gtalkstech](https://x.com/gtalkstech)
- Email: garrett@gtalkstech.com

---

## Disclaimer

All content here is for educational purposes. Templates and scripts are starting points. Adapt them to fit your organization's policies, ticketing systems, and incident management processes. Nothing in this repo represents the views, infrastructure, or proprietary information of any employer.

---

## Contributing

This is a solo project. If you spot a bug, a vendor adaptation that does not work as written, or a prompt you would use weekly that should be in the next pack release, open an issue or email garrett@gtalkstech.com.
