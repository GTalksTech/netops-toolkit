# The Network Engineer's AI Prompt Pack

15 prompts I actually use for network engineering work, organized into five categories and tested against real lab output before release.

> **Companion video:** [Prompt Engineering for Network Engineers - 4 Rules and 15 Free Prompts](https://youtu.be/OEfeS8pyn_s)
>
> **Mailing list:** [join.gtalkstech.com](https://join.gtalkstech.com) -- get the v1.1 update when it ships in August 2026.

## Open the pack

[**network-engineer-ai-prompt-pack.md**](network-engineer-ai-prompt-pack.md)

The whole pack lives in that one file. Copy whichever prompt you need into your AI tool (Claude, Gemini, ChatGPT). Each prompt has a "When to use," the prompt itself, an example, and vendor adaptation notes.

## What's in it

Five categories, three prompts each.

| Category | Prompts |
|---|---|
| Configuration Generation | OSPF standardization, multi-vendor BGP peering, FortiGate IPSec VPN |
| Troubleshooting | OSPF/MTU triage, BGP neighbor state, interface counter / microburst |
| Documentation | Single-device audit runbook, draw.io topology from CDP, post-incident review |
| Compliance and Audit | ACL shadowing/overlap, CIS Benchmark audit, configuration drift |
| Code Generation | Jinja2 switchport template, Nornir+Netmiko scaffold, Ansible multi-vendor playbook |

## Read the safety section before pasting anything

The pack opens with a safety section that explains the Public-safe vs Enterprise-only labeling. Short version:

- **Public-safe (3 prompts):** Template logic only, no real device data goes in. Free-tier AI is fine.
- **Enterprise-only (12 prompts):** Require pasting real configs, ACLs, hostnames, or live output. Use a paid tier with a no-training commitment (Claude Pro/Team/Max, ChatGPT Team/Enterprise, Copilot Enterprise). Never paste real device data into a tier that may train on it.

## Vendors covered

Every prompt is written first against Cisco IOS-XE. Each prompt has an adaptation block for:

- Arista EOS
- Junos
- ArubaOS-CX
- FortiOS
- PAN-OS

Where a vendor doesn't have a clean equivalent (e.g., ArubaOS-CX doesn't terminate IPSec at scale), the adaptation note says so. No invented syntax.

## Honest limitations

The pack ends with six anti-patterns -- the places AI still gets networking wrong in 2026. Read that section before treating any AI output as authoritative. The shortest version: every output in this pack is a draft. The engineer reviewing the draft is responsible for what runs.

## Updates and feedback

- **v1.1 ships August 2026.** Subscribers to [join.gtalkstech.com](https://join.gtalkstech.com) get the release email and early-access drafts.
- **Want a prompt added?** Email garrett@gtalkstech.com with subject "Prompt Pack v1.x Feedback." Real-name credit in the changelog if your contribution ships (anonymous if you ask).

## License

Free to use, copy, adapt, and redistribute. Attribution appreciated but not required. The pack is published under the same terms as the rest of [netops-toolkit](https://github.com/GTalksTech/netops-toolkit).
