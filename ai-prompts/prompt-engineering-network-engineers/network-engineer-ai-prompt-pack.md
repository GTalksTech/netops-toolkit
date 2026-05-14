# The Network Engineer's AI Prompt Pack

**Version 1.0.1**
**Released:** 2026-05-12
**Updated:** 2026-05-14
**Author:** Garrett Masters, G Talks Tech
**Website:** https://gtalkstech.com
**Mailing list:** https://join.gtalkstech.com
**GitHub:** https://github.com/GTalksTech/netops-toolkit/tree/main/ai-prompts/prompt-engineering-network-engineers
**Companion video:** Prompt Engineering for Network Engineers (YouTube link added at publish)

15 prompts I actually use for config generation, troubleshooting, documentation, ACL review, and compliance. Some are public-safe and work on free-tier AI. Most need enterprise-tier AI because they require real configs and live device output. Read the safety section before you paste anything.

This pack is versioned and updated quarterly. v1.1 ships in August 2026. If you build a prompt you want added, email garrett@gtalkstech.com.

---

## What this pack is

Every prompt here covers a real task a senior network engineer does every week or every month. Each prompt follows the same 4-piece structure, so once you understand the structure you can adapt any prompt to your vendor, your environment, and your standards.

The prompts assume you already know networking. They do not teach BGP. They do not teach ACL syntax. They are leverage tools for someone who already does the work and wants the output formatted and structured by AI instead of typed by hand.

## How to use this pack

Three usage patterns:

1. Copy the prompt verbatim, paste your real device data where the placeholders say `[INSERT ...]`, and run it. Fastest path.
2. Adapt the constraint line to swap vendors. Each prompt has a Vendor adaptation note showing how to retarget for FortiOS, PAN-OS, ArubaOS-CX, Junos, or Arista EOS without rewriting the whole prompt.
3. Use the 4-piece structure as a template for your own prompts. The structure is the leverage.

## The 4-piece prompt anatomy

Every prompt in this pack follows the same structure. Once you see the pattern, you can write your own.

**1. Role.** The persona the AI takes on. Sets the technical bar and stops the model from drifting into generalist territory. "You are a senior BGP engineer reviewing a peering proposal" produces tighter output than no role at all, every time.

**2. Context.** The actual data the AI is analyzing. Configs, syslog excerpts, show command output, design requirements. The model cannot infer your topology or your standards. Hand it what it needs to answer.

**3. Constraint.** The boundaries on the output. Target vendor, what NOT to include, banned syntax patterns, risk tolerance, output requirements. This is where you stop the model from inventing commands or generating IOS syntax for an IOS-XR box.

**4. Output format.** Exactly how the answer should be structured. Fenced code block, markdown table, JSON, draw.io XML. Eliminates filler text and makes the output copy-pasteable instead of something you have to clean up.

Every prompt below labels these four pieces explicitly. The structure is the leverage. The vendor specifics are interchangeable.

---

## Safety: public-safe vs enterprise-only

Every prompt in this pack carries one of two safety labels.

**Public-safe.** The prompt template needs no real device data to be useful. Concept explanations, syntax help, generic templates, scaffolding code. Run these on free-tier AI without exposing anything. The free tiers of ChatGPT, Claude, Gemini, and Copilot are all fine for these.

**Enterprise-only.** The prompt template needs real hostnames, real IP addresses, real configs, real ACLs, or live device output to be useful. Do not run these on free-tier AI. The free tiers train on your inputs by default. Pasting a real production config into free ChatGPT means that config, and whatever it tells the model about your network, is now part of the training pipeline.

For Enterprise-only prompts, use a paid tier with a no-training commitment:

- ChatGPT Team or Enterprise
- Claude Pro, Team, or Enterprise
- Microsoft Copilot Enterprise (Bing/365)
- Google Gemini for Workspace

Free Gemini with a personal Google account: check current Workspace terms before relying on it. Policies shift. The general rule does not. If you are pasting a real config into a chat box, use a tier where your tenant data is contractually excluded from foundational model training.

**A note on the example data in this pack.** Every example shown here is from my home lab on CML Free, with hostnames like `core-rtr-01` and IPs in `10.0.0.0/8` documentation space. The lab is public. The example data is safe to share. Your production data is not. Every Enterprise-only label means the template, when applied to your network, will need data that should never sit in a free-tier chat history.

If your employer has not given you written guidance on AI tier policy yet, ask. This is the question your compliance team is going to want a documented answer to anyway.

---

# Category 1: Configuration Generation

---

## Prompt 1: OSPF Standardization Generator

**Category:** Configuration Generation
**Safety:** Enterprise-only (uses real hostnames, loopback IPs, link addressing, and authentication keys)
**When to use:** Bringing up a new pair of OSPF-routed devices, or standardizing OSPF on existing devices that were configured ad-hoc.

### The prompt

```
You are a senior network engineer building OSPF on a small Cisco IOS routed network. Generate the OSPF configuration for two routers connected by a single point-to-point Ethernet link.

CONTEXT:
- Router A hostname: [INSERT HOSTNAME]
- Router A loopback0 IP: [INSERT LOOPBACK /32]
- Router A link interface and IP: [INSERT INTERFACE, IP/MASK]
- Router B hostname: [INSERT HOSTNAME]
- Router B loopback0 IP: [INSERT LOOPBACK /32]
- Router B link interface and IP: [INSERT INTERFACE, IP/MASK]
- OSPF process ID: [INSERT PID]
- OSPF area: 0
- Authentication: MD5, key id [INSERT KEY ID], key string [INSERT KEY STRING]

CONSTRAINTS:
- Target vendor is Cisco IOS-XE running classic OSPF (router ospf <pid>).
- Use the loopback0 IP as the router-id, set explicitly with "router-id".
- Set passive-interface default. Activate only the point-to-point link with "no passive-interface".
- Set the network type on the link to point-to-point. Do not leave it at default broadcast.
- Configure MD5 authentication on the link interface only, not at the area level.
- Do NOT generate redistribute, default-information originate, summary-address, or any feature outside core OSPF and link auth.

OUTPUT FORMAT:
Two fenced code blocks. First labeled "Router A: <hostname>". Second labeled "Router B: <hostname>". Each block contains only IOS CLI commands ready to paste in global config mode. No commentary outside the blocks.
```

### Example input

- Router A hostname: `core-rtr-01`
- Router A loopback0: `1.1.1.1/32`
- Router A link interface: `Ethernet0/1`, `10.0.12.1/30`
- Router B hostname: `edge-rtr-01`
- Router B loopback0: `2.2.2.2/32`
- Router B link interface: `Ethernet0/1`, `10.0.12.2/30`
- OSPF PID: `1`
- MD5 key id: `1`, key string: `ospf-key-2026`

### Example output (abbreviated)

```
Router A: core-rtr-01
router ospf 1
 router-id 1.1.1.1
 passive-interface default
 no passive-interface Ethernet0/1
 network 1.1.1.1 0.0.0.0 area 0
 network 10.0.12.0 0.0.0.3 area 0
!
interface Ethernet0/1
 ip ospf network point-to-point
 ip ospf message-digest-key 1 md5 ospf-key-2026
 ip ospf authentication message-digest
```

### Vendor adaptation

Change the constraints line "Target vendor is Cisco IOS-XE..." to:

- **Arista EOS:** "Target vendor is Arista EOS. Use `router ospf <pid>` syntax. Same passive-default model. Use `ip ospf authentication message-digest` and `ip ospf message-digest-key`."
- **Junos:** "Target vendor is Junos. Output as `set` commands under `[edit protocols ospf]` and `[edit interfaces ... unit 0 family inet]`. Use `area 0.0.0.0`. Authentication goes under `[edit protocols ospf area 0.0.0.0 interface <name> authentication md5]`."
- **ArubaOS-CX:** "Target is ArubaOS-CX. Use `router ospf <pid>` and `area 0`. Passive default supported. Authentication via `ip ospf message-digest-key` and `ip ospf authentication message-digest` on the interface."
- **FortiOS:** OSPF is not the typical Fortinet use case at scale. If you are running it, target FortiOS 7.2+ with `config router ospf` and authentication under `config interface`.

### Why this saves time

OSPF brought up by hand is fine. OSPF brought up by hand consistently across 12 sites with the same passive-default posture, the same authentication, and clean point-to-point typing is where engineers cut corners. This prompt enforces the standard every time without you having to remember it.

---

## Prompt 2: Multi-Vendor BGP Peering Generator

**Category:** Configuration Generation
**Safety:** Enterprise-only (uses real ASNs, peer IPs, and prefix lists)
**When to use:** Turning up a new BGP peer, internal or external, on any vendor. Especially valuable for ISP/transit turn-ups where prefix-list discipline matters.

### The prompt

```
You are a senior internet routing engineer turning up a new BGP peer. Generate the BGP configuration with default-deny prefix filtering applied in both directions.

CONTEXT:
- Local hostname: [INSERT HOSTNAME]
- Local ASN: [INSERT LOCAL ASN]
- Local peer IP (source for the session): [INSERT LOCAL IP]
- Local update-source interface: [INSERT INTERFACE or leave blank for direct]
- Remote ASN: [INSERT REMOTE ASN]
- Remote peer IP: [INSERT REMOTE IP]
- Peer description: [INSERT FRIENDLY DESCRIPTION, e.g., "ISP-A transit"]
- Address family: ipv4 unicast (specify ipv6 if needed)
- Prefixes I want to advertise OUT to this peer: [LIST PREFIXES] OR "none"
- Prefixes I want to accept IN from this peer: [LIST PREFIXES] OR "default route only" OR "none"

CONSTRAINTS:
- Target vendor is Cisco IOS-XE.
- Apply prefix filtering using a named prefix-list. Default behavior is permit-only-listed, deny everything else. Generate the prefix-list explicitly.
- Apply the prefix-list to both inbound and outbound directions on this neighbor.
- Add a description on the neighbor.
- Set neighbor send-community both, and apply soft-reconfiguration inbound (or use route-refresh capability if you note it explicitly).
- Do NOT generate `network` statements for advertising. Use prefix-list-driven outbound filtering only.
- Do NOT enable any redistribution between BGP and IGP unless I explicitly listed it in context.

OUTPUT FORMAT:
A single fenced code block with the full configuration: prefix-list definitions first, neighbor configuration second, address-family activation third. No commentary outside the block.
```

### Example input

- Local hostname: `edge-rtr-01`
- Local ASN: `65001`
- Local peer IP: `10.0.12.2`
- Update-source: blank (directly connected)
- Remote ASN: `65000`
- Remote peer IP: `10.0.12.1`
- Description: `core-rtr-01 iBGP`
- Address family: `ipv4 unicast`
- Advertise out: `2.2.2.2/32`
- Accept in: `1.1.1.1/32`

### Example output (abbreviated)

```
ip prefix-list PL-CORE-IN seq 5 permit 1.1.1.1/32
ip prefix-list PL-CORE-OUT seq 5 permit 2.2.2.2/32
!
router bgp 65001
 neighbor 10.0.12.1 remote-as 65000
 neighbor 10.0.12.1 description core-rtr-01 iBGP
 neighbor 10.0.12.1 send-community both
 !
 address-family ipv4
  neighbor 10.0.12.1 activate
  neighbor 10.0.12.1 prefix-list PL-CORE-IN in
  neighbor 10.0.12.1 prefix-list PL-CORE-OUT out
  neighbor 10.0.12.1 soft-reconfiguration inbound
 exit-address-family
```

### Vendor adaptation

- **Arista EOS:** Same `router bgp` syntax. Prefix-lists use `ip prefix-list` identical to IOS. Activation under `address-family ipv4` is the same.
- **Junos:** Output as `set` commands under `[edit protocols bgp group <name>]` with `peer-as`, `local-address`, `import` and `export` policy-statements. Generate the policy-statement and the prefix-list (called `prefix-list` under `[edit policy-options]`).
- **ArubaOS-CX:** Use `router bgp <asn>` with `neighbor` syntax similar to Cisco. Use `ip prefix-list` and apply via `route-map`.
- **FortiOS:** Use `config router bgp` with `config neighbor`. Filtering is via `prefix-list` (created under `config router prefix-list`) bound with `set prefix-list-in` and `set prefix-list-out` on the neighbor.
- **PAN-OS:** BGP is configured under the virtual router. Use `set network virtual-router default protocol bgp` and define the peer-group, peer, and route-map with import/export rules.

### Why this saves time

The most common BGP outage I can name from the last decade is "we accidentally advertised more than we meant to." This prompt produces a peer config that physically cannot leak. The default-deny posture is the win. The vendor-specific syntax is the small part.

---

## Prompt 3: FortiGate Site-to-Site IPSec VPN Builder

**Category:** Configuration Generation
**Safety:** Enterprise-only (uses public peer IPs and protected internal subnets)
**When to use:** Standing up a new site-to-site VPN. Cryptographic mismatches are still the leading cause of VPN failure. This prompt makes the proposal explicit.

### The prompt

```
You are a Fortinet network security engineer building a site-to-site IPSec VPN tunnel. Generate the FortiGate CLI configuration for both Phase 1 and Phase 2.

CONTEXT:
- Tunnel name (max 15 chars): [INSERT NAME]
- Local WAN interface: [INSERT INTERFACE, e.g., wan1]
- Local public IP: [INSERT IP]
- Remote public IP: [INSERT IP]
- Pre-shared key: [INSERT PSK]
- Phase 1 proposal (encryption-hash-DH): [INSERT, e.g., aes256-sha256-modp2048]
- Phase 2 proposal (encryption-hash-PFS): [INSERT, e.g., aes256-sha256-modp2048]
- Local protected subnet(s): [INSERT CIDR(s)]
- Remote protected subnet(s): [INSERT CIDR(s)]
- Phase 1 lifetime (seconds): [INSERT, default 86400]
- Phase 2 lifetime (seconds): [INSERT, default 43200]

CONSTRAINTS:
- Target is FortiOS 7.2 or later.
- Disable aggressive mode. Use IKEv2 unless I explicitly note IKEv1.
- Enable Dead Peer Detection (DPD) on-idle.
- Output CLI only. Do not include GUI navigation steps.
- Do NOT generate firewall policies or static routes. Tunnel only.
- Use named address objects for the local and remote subnets in Phase 2 quick mode selectors.

OUTPUT FORMAT:
A single fenced code block with the full configuration in order: address objects first, phase1-interface second, phase2-interface third. No commentary outside the block.
```

### Example input

- Tunnel name: `VPN-DC-EAST`
- Local WAN: `wan1`
- Local public IP: `203.0.113.1`
- Remote public IP: `198.51.100.1`
- PSK: `Replace-In-Pass-Manager-2026`
- Phase 1: `aes256-sha256-modp2048`
- Phase 2: `aes256-sha256-modp2048`
- Local subnet: `10.10.0.0/16`
- Remote subnet: `10.20.0.0/16`

### Example output (abbreviated)

```
config firewall address
  edit "VPN-DC-EAST_local"
    set subnet 10.10.0.0 255.255.0.0
  next
  edit "VPN-DC-EAST_remote"
    set subnet 10.20.0.0 255.255.0.0
  next
end

config vpn ipsec phase1-interface
  edit "VPN-DC-EAST"
    set interface "wan1"
    set ike-version 2
    set local-gw 203.0.113.1
    set remote-gw 198.51.100.1
    set proposal aes256-sha256
    set dhgrp 14
    set dpd on-idle
    set psksecret Replace-In-Pass-Manager-2026
  next
end

config vpn ipsec phase2-interface
  edit "VPN-DC-EAST_p2"
    set phase1name "VPN-DC-EAST"
    set proposal aes256-sha256
    set dhgrp 14
    set src-name "VPN-DC-EAST_local"
    set dst-name "VPN-DC-EAST_remote"
  next
end
```

### Vendor adaptation

- **Cisco IOS-XE (DMVPN/FlexVPN excluded):** "Target is Cisco IOS-XE classic crypto. Generate `crypto ikev2 proposal`, `crypto ikev2 policy`, `crypto ikev2 keyring`, `crypto ikev2 profile`, `crypto ipsec transform-set`, `crypto ipsec profile`, and an `interface Tunnel` (or crypto map) bound to the WAN interface."
- **PAN-OS:** "Target is PAN-OS. Output as `set` commands defining IKE crypto profile, IPSec crypto profile, IKE gateway, and IPSec tunnel under `network ike` and `network tunnel`."
- **Junos (SRX):** "Target is Junos SRX. Output `set` commands for `security ike proposal`, `security ike policy`, `security ike gateway`, `security ipsec proposal`, `security ipsec policy`, `security ipsec vpn`."
- **ArubaOS-CX:** Aruba switches do not typically terminate IPSec at this scale; this prompt does not adapt cleanly. Use the Cisco or Juniper variant on the actual VPN concentrator.

### Why this saves time

The GUI workflow for VPN tunnels is one of the slowest things in network engineering. CLI is faster. Generating both ends of the tunnel from one prompt, with matching proposals enforced, kills the most common failure mode (asymmetric P1/P2 settings) before it ships.

---

# Category 2: Troubleshooting

---

## Prompt 4: OSPF Adjacency and MTU Triage

**Category:** Troubleshooting
**Safety:** Enterprise-only (uses real interface state, neighbor data, and MTU values)
**When to use:** OSPF neighbors are stuck in EXSTART, EXCHANGE, INIT, or 2-WAY when they should be FULL. Pull all four of these from BOTH ends before running the prompt: `show ip ospf neighbor`, `show ip ospf interface <link>`, `show ip interface <link>`, and `show running-config interface <link>`. The first two are the obvious OSPF views. The last two are what catch IP MTU mismatches and interface-level config drift that the OSPF views can hide.

### The prompt

```
You are a senior network engineer holding a CCIE in routing. Diagnose why this OSPF adjacency is not reaching FULL state.

CONTEXT:
- Output of `show ip ospf neighbor` from Router A:
[INSERT OUTPUT]
- Output of `show ip ospf interface <link>` from Router A:
[INSERT OUTPUT]
- Output of `show ip interface <link>` from Router A:
[INSERT OUTPUT]
- Output of `show running-config interface <link>` from Router A:
[INSERT OUTPUT]
- Output of `show ip ospf neighbor` from Router B:
[INSERT OUTPUT]
- Output of `show ip ospf interface <link>` from Router B:
[INSERT OUTPUT]
- Output of `show ip interface <link>` from Router B:
[INSERT OUTPUT]
- Output of `show running-config interface <link>` from Router B:
[INSERT OUTPUT]
- Any relevant log lines from the last 10 minutes:
[INSERT LOGS or write "none"]

CONSTRAINTS:
- Compare every parameter that must match between the two interfaces: hello/dead timers, area ID, network type, IP MTU, interface MTU, authentication mode, subnet mask.
- For IP MTU specifically, do not rely on `show ip ospf interface` alone. Pull the operational IP MTU from `show ip interface` (the "MTU is N bytes" line) AND check `show running-config interface` for an explicit `ip mtu <value>` line. An `ip mtu` override applied at the interface level can break OSPF DBD exchange without changing the link-layer MTU or appearing prominently in the OSPF view. Cite the source for the IP MTU value you report.
- Identify which specific parameter is mismatched. State it directly.
- Rank likely root causes from most likely to least likely. Use only data present in the inputs. Do not speculate beyond what the outputs show.
- Do NOT recommend a remediation command yet. Diagnosis only.
- If the data is insufficient to reach a conclusion, state exactly what additional command output you need.

OUTPUT FORMAT:
1. A short diagnosis paragraph (3-5 sentences) naming the most likely root cause.
2. A markdown table comparing all match-required parameters across Router A and Router B, with a "Match?" column (Yes/No) and a "Source" column citing which show command surfaced the value.
3. A bulleted list of next-step verification commands, in priority order.
```

### Example input

This is the EP001 demo lab. `core-rtr-01` and `edge-rtr-01` are connected on Ethernet0/1. After a maintenance window, the adjacency drops to EXCHANGE. `core-rtr-01` Eth0/1 has `ip mtu 1400`. `edge-rtr-01` Eth0/1 still has the default 1500.

### Example output (abbreviated)

> The neighbor is stuck in EXCHANGE because of an IP MTU mismatch on the point-to-point link. OSPF requires equal IP MTU values on both sides for the Database Description (DBD) phase to complete. `core-rtr-01` shows `ip mtu 1400` under the Ethernet0/1 running-config, and `show ip interface Ethernet0/1` confirms an operational IP MTU of 1400. `edge-rtr-01` has no `ip mtu` override and shows the default 1500. The DBD packets cannot be reassembled cleanly, so the adjacency cannot transition to LOADING or FULL.

| Parameter | core-rtr-01 | edge-rtr-01 | Match? | Source |
|---|---|---|---|---|
| Area ID | 0.0.0.0 | 0.0.0.0 | Yes | show ip ospf interface |
| Hello timer | 10 | 10 | Yes | show ip ospf interface |
| Dead timer | 40 | 40 | Yes | show ip ospf interface |
| Network type | POINT_TO_POINT | POINT_TO_POINT | Yes | show ip ospf interface |
| IP MTU | 1400 | 1500 | **No** | show ip interface + running-config `ip mtu` |
| Authentication | MD5 | MD5 | Yes | show ip ospf interface |

Verify with:
- `show ip interface Ethernet0/1 | include MTU` on both ends to confirm the operational IP MTU
- `show running-config interface Ethernet0/1` on both ends to confirm whether `ip mtu` is explicitly set
- `show ip ospf interface Ethernet0/1 | include MTU` on both ends as a secondary check
- Check the maintenance log for an `ip mtu 1400` change made deliberately or as a side effect of a different change

### Vendor adaptation

- **Arista EOS:** Same four commands work as-is (`show ip ospf neighbor`, `show ip ospf interface`, `show ip interface`, `show running-config interfaces <int>`). EOS surfaces `ip mtu` under the same name.
- **Junos:** Replace with `show ospf neighbor extensive`, `show ospf interface extensive`, `show interfaces <int> extensive` (for operational MTU), and `show configuration interfaces <int>` (for any explicit `mtu` statement). Junos uses a single `mtu` per family rather than separate interface and IP MTU values.
- **ArubaOS-CX:** Same four commands work with minor syntax (`show ip ospf neighbors`, `show ip ospf interface`, `show interface <int>`, `show running-config interface <int>`). ArubaOS-CX uses `ip mtu` under the L3 interface stanza.
- **FortiOS:** Use `get router info ospf neighbor`, `get router info ospf interface`, `get system interface physical` (for the port), and `show system interface <name>` (for the config). FortiOS combines L2 and L3 MTU into a single `mtu` value per interface, so the prompt's IP MTU vs interface MTU distinction does not apply the same way.

### Why this saves time

OSPF state machine stalls take time to diagnose by hand because the data is spread across two devices and four show commands. The model excels at side-by-side parameter comparison, which is the actual diagnostic work. You stay in charge of the fix.

---

## Prompt 5: BGP Neighbor State Analyzer

**Category:** Troubleshooting
**Safety:** Enterprise-only (uses real ASNs, peer IPs, and live state output)
**When to use:** A BGP peer is not in Established state. You have `show ip bgp summary` and recent BGP-related syslogs in hand. Use this before opening a TAC case.

### The prompt

```
You are an internet routing engineer triaging a BGP neighbor that is not in Established state.

CONTEXT:
- Output of `show ip bgp summary`:
[INSERT OUTPUT]
- Output of `show ip bgp neighbor <peer-ip>`:
[INSERT OUTPUT]
- Recent BGP-related syslogs (last 1 hour):
[INSERT LOGS or write "none"]
- The peer in question: [INSERT PEER IP and ASN]

CONSTRAINTS:
- Determine the current state (Idle, Connect, Active, OpenSent, OpenConfirm, Established).
- Differentiate between transport-layer failure (TCP/179 unreachable, MTU PMTUD, no route to peer), session-layer failure (ASN mismatch, hold-timer expiration, password mismatch), and policy-layer failure (peer rejecting OPEN due to capability mismatch).
- Use only data present in the inputs. Do not invent log lines or output that is not shown.
- If state is "Active" or "Idle", call out which one explicitly and explain the difference in this scenario.

OUTPUT FORMAT:
A markdown table with these columns:
| Neighbor IP | Current State | Diagnosed Failure Layer | Specific Root Cause | Next Verification Command |

Followed by a brief paragraph (2-3 sentences) on what to check next.
```

### Example output (abbreviated)

| Neighbor IP | Current State | Failure Layer | Root Cause | Next Command |
|---|---|---|---|---|
| 192.0.2.10 | Active | Transport | TCP/179 not reaching peer (Connection refused in syslog) | `telnet 192.0.2.10 179 /source-interface Loopback0` |

> The neighbor is in Active state, meaning the local router is actively trying to open a TCP session and the remote is refusing it. The "Connection refused" log line confirms TCP-level rejection rather than a routing reachability issue. Verify with a sourced telnet to TCP/179, then check whether the remote side has a peer configured for this local IP/ASN.

### Vendor adaptation

- **Arista EOS:** `show ip bgp summary` and `show ip bgp neighbors <peer>` are identical to Cisco. Prompt works as-is.
- **Junos:** Use `show bgp summary` and `show bgp neighbor <peer>`. State naming is the same. Replace command references in the constraints.
- **ArubaOS-CX:** `show bgp ipv4 unicast summary` and `show bgp ipv4 unicast neighbors <peer>`. Same state machine.
- **FortiOS:** `get router info bgp summary` and `get router info bgp neighbors <peer>`. Less verbose output; include `config router bgp` block if needed.
- **PAN-OS:** `show routing protocol bgp peer` and `show routing protocol bgp peer-group`. State naming is consistent.

### Why this saves time

BGP outages produce a lot of output and not a lot of clarity. The model is good at correlating the summary state ("Active" vs "Idle" vs "Established") with the syslog line that explains why. The diagnosis comes back in 5 seconds instead of 5 minutes of grep.

---

## Prompt 6: Interface Counter and Microburst Correlator

**Category:** Troubleshooting
**Safety:** Enterprise-only (uses live interface telemetry)
**When to use:** Users complain about packet loss or slow performance on a specific link. You pull `show interfaces` and need to know if it is a physical issue or buffer exhaustion before you escalate.

### The prompt

```
You are a senior data center network engineer diagnosing intermittent loss on a single interface.

CONTEXT:
- Output of `show interfaces <interface>`:
[INSERT FULL OUTPUT]
- The interface: [INSERT NAME and description]
- How long this counter has been accumulating (since last `clear counters`): [INSERT, e.g., "7 days" or "unknown"]
- What the user reported: [INSERT, e.g., "voice quality issues, intermittent", "tcp retransmits", "slow file transfer"]

CONSTRAINTS:
- Differentiate between physical-layer issues (input errors, CRC, FCS, runts, giants, late collisions) and queue/buffer issues (output drops, output discards, output queue depth).
- Calculate error rates as a percentage of total packets, both input and output. Show the math.
- If output drops are present, name the typical root cause categories: microburst, oversubscription on egress, QoS misclassification.
- Do NOT recommend "replace the cable" if there are zero physical-layer indicators.

OUTPUT FORMAT:
1. A short diagnosis paragraph (3-5 sentences) naming the fault domain (physical, queue, or other).
2. A markdown table:
   | Counter | Value | Total packets | Rate |
3. A prioritized "next steps" list (bulleted), shortest path to root cause first.
```

### Example output (abbreviated)

> Physical media is clean. Output drops are accumulating at roughly 0.4% of egress traffic, which is consistent with microburst behavior on an oversubscribed egress queue. CRC and input errors are zero, so this is not a cable, optic, or link-quality issue. Recommend looking at the egress QoS policy and queue depth before touching the physical layer.

| Counter | Value | Total Packets | Rate |
|---|---|---|---|
| Input errors | 0 | 1,200,000,000 | 0.000% |
| CRC | 0 | 1,200,000,000 | 0.000% |
| Output drops | 4,800,000 | 1,150,000,000 | 0.417% |

Next:
- `show queueing interface <intf>` to see queue depth and drop distribution
- `show policy-map interface <intf>` if QoS is applied
- Check upstream traffic patterns for bursting application sources

### Vendor adaptation

- **Arista EOS:** `show interfaces <intf>` and `show interfaces <intf> queue` map directly. Output drops are reported as `output discards`.
- **Junos:** `show interfaces <intf> extensive` and `show interfaces queue <intf>`. Counter names differ (`Discards`, `Drops`).
- **ArubaOS-CX:** `show interface <intf>` and `show interface <intf> queues`. Counter naming similar to Cisco.
- **FortiOS:** `diagnose hardware deviceinfo nic <intf>` for physical counters; `diagnose netlink interface list` for general state.

### Why this saves time

Most engineers default to "swap the optic" or "replace the cable" before they look at queue counters. The math on error rates lives across multiple counter sets, and reading them by hand is tedious. The prompt does the percentage math and tells you whether you are chasing the right fault domain.

---

# Category 3: Documentation

> **A note before this category.** If you are looking for full automated device documentation across an entire network, the workflow you actually want is in EP004: AI Network Documentation, with a working public Python/Netmiko script at https://github.com/GTalksTech/netops-toolkit (folder: `scripts/netmiko/ai-network-documentation/`). The three prompts in this category are point-tools for specific artifacts: a single-device audit runbook, a topology diagram, and a post-incident review. They are not a substitute for that workflow. Use them when you need one of those specific artifacts on demand.

---

## Prompt 7: show tech-support to Severity-Ranked Audit Runbook

**Category:** Documentation
**Safety:** Enterprise-only (consumes a full device configuration)
**When to use:** You need a written runbook of every weak spot on a single device, prioritized by severity, before a maintenance window or an audit. The video walks through this exact prompt against a lab Cisco IOS router.

### The prompt

```
You are a senior network engineer producing a written audit of a single device. Output must be in runbook format ready to paste into a Confluence or Notion page.

CONTEXT:
- Device hostname: [INSERT HOSTNAME]
- Device role: [INSERT, e.g., "core router", "WAN edge", "distribution switch"]
- Output of `show tech-support`:
[INSERT FULL OUTPUT]

CONSTRAINTS:
- Identify exactly 10 findings. If you find more than 10, rank them and keep the top 10. If fewer, fill the remaining slots with positive observations or note "no further findings".
- Severity-rank every finding: High, Medium, or Low.
- Each finding must include: title, severity, the relevant config snippet (verbatim from input), the impact, the recommended remediation command(s).
- Do NOT invent commands or features that are not in the input. If a feature is missing, say "feature not configured" rather than fabricating a config line.
- Do NOT skip the positive observations. If something is configured well (e.g., explicit router-id, MD5 auth, passive default), call it out at the end.

OUTPUT FORMAT:
A markdown document with this structure:
- # Audit: <hostname>
- ## Findings (ranked by severity)
  - 10 numbered subsections, each with **Severity**, **Config**, **Impact**, **Remediation** as bold sub-headings
- ## Positive observations (bulleted list)
- ## Suggested next maintenance window items (bulleted list, ordered)
```

### Example output (abbreviated)

> # Audit: core-rtr-01
>
> ## Findings (ranked by severity)
>
> ### 1. Default route points to a router with no upstream
> **Severity:** High
> **Config:** `ip route 0.0.0.0 0.0.0.0 10.0.12.1`
> **Impact:** Default traffic blackholes if edge-rtr-01 is not actually transit. Verify upstream reachability of 10.0.12.1.
> **Remediation:** Confirm upstream design; if 10.0.12.1 is intended only for OSPF transit, remove static default and let OSPF distribute it.
>
> ### 2. NTP master configured on a router that should be an NTP client
> ...
>
> ## Positive observations
> - OSPF authentication MD5 enabled on Eth0/1
> - Passive-interface default applied
> - Loopback0 used as router-id explicitly

### Vendor adaptation

- **Arista EOS:** Use `show tech-support` (same command). Findings format works as-is.
- **Junos:** Use `request support information`. Findings will reference Junos config stanzas (`set` style or hierarchy paths).
- **ArubaOS-CX:** Use `show tech`. Output format adapts cleanly.
- **FortiOS:** Use `diagnose debug config-error-log read` plus `show full-configuration`. Less standardized than Cisco-style `show tech`; you may need to feed multiple show commands.
- **PAN-OS:** Use `show config running` and `show system info`. PAN-OS does not have a single equivalent to `show tech-support`.

### Why this saves time

Manual device audits take 1-2 hours per box and the engineer doing them is bored before they start. The prompt produces a runbook in the time it takes to read it. The severity ranking and the positive observations both matter: senior engineers do not want a list of nitpicks, they want priority and credit for what is right.

---

## Prompt 8: Topology Diagram in draw.io XML

**Category:** Documentation
**Safety:** Enterprise-only (uses real CDP/LLDP neighbor data and interface descriptions)
**When to use:** You need a network diagram for a wiki, a runbook, or a change ticket and you do not want to drag boxes in a GUI for 45 minutes. Paste real CDP or LLDP output, get back importable draw.io XML.

### The prompt

```
You are a senior network engineer producing a topology diagram from neighbor discovery output. Output must be valid draw.io XML that can be pasted directly into a new draw.io file.

CONTEXT:
- Output of `show cdp neighbors detail` (or `show lldp neighbors detail`) from each device in scope:
[INSERT OUTPUT, one device at a time, with the device hostname clearly labeled before each output block]
- Device roles, if you want them grouped on the diagram:
[INSERT, e.g., "core-rtr-01: core", "dist-sw-01: distribution", "access-sw-01: access"]
- Layout preference: [INSERT, e.g., "left-to-right tiered", "top-down hierarchical", "ring"]

CONSTRAINTS:
- Output draw.io-compatible XML inside an `<mxfile>...<mxGraphModel>...</mxGraphModel></mxfile>` wrapper. Do NOT output Mermaid syntax. Do NOT output PlantUML.
- Each device is a node. Each unique link between two devices is a single edge, with both interface labels shown on the edge.
- Use the `shape=mxgraph.cisco.routers.router` style for nodes labeled as routers. Use `shape=mxgraph.cisco.switches.workgroup_switch` for switches.
- Do not invent neighbors that are not in the input data. If only one direction of a link is shown, render it once and note in a comment that the reverse was not provided.
- Set node positions explicitly with `x` and `y` attributes. Space nodes at least 200 pixels apart.

OUTPUT FORMAT:
A single fenced code block containing the complete `<mxfile>` XML, ready to copy. After the code block, include one line of instructions: how to import the XML into draw.io (Extras > Edit Diagram > paste).
```

### Example output (abbreviated)

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Topology" id="t1">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="core01" value="core-rtr-01" style="shape=mxgraph.cisco.routers.router" vertex="1" parent="1">
          <mxGeometry x="200" y="100" width="80" height="80" as="geometry" />
        </mxCell>
        <mxCell id="edge01" value="edge-rtr-01" style="shape=mxgraph.cisco.routers.router" vertex="1" parent="1">
          <mxGeometry x="500" y="100" width="80" height="80" as="geometry" />
        </mxCell>
        <mxCell id="link1" value="Eth0/1 - Eth0/1" style="endArrow=none" edge="1" parent="1" source="core01" target="edge01">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

To import: open https://app.diagrams.net (or your local draw.io), File > New, then Extras > Edit Diagram, paste, OK.

### Vendor adaptation

- **Arista EOS / ArubaOS-CX / Junos:** Use `show lldp neighbors detail` instead of CDP. The prompt structure is identical; the parser inside the model handles either format.
- **FortiOS:** `diagnose lldp neighbors-summary` for the LLDP table.
- **PAN-OS:** `show lldp neighbors all`.

### Why this saves time

Drawing topology in Visio or draw.io is universally disliked. The data already exists in your devices via CDP/LLDP. This prompt closes the gap: live neighbor data goes in, a real diagram comes out. Update it the same way next quarter.

**Caveat from real-world testing:** AI models occasionally drift to Mermaid output even when explicitly told to produce draw.io XML. If the response comes back as Mermaid, re-prompt with "Output draw.io XML, not Mermaid. Wrap in `<mxfile>` and `<mxGraphModel>`." Models are inconsistent on this; the constraint catches most attempts.

---

## Prompt 9: Post-Incident Review Generator

**Category:** Documentation
**Safety:** Enterprise-only (uses real timeline, devices, and root cause data)
**When to use:** Incident is resolved. You owe the team a written PIR and you do not want to spend 90 minutes writing prose. Paste your timeline notes, get a structured document.

### The prompt

```
You are a senior network engineer writing a post-incident review for an internal engineering audience. Tone is direct, factual, blameless. No marketing voice.

CONTEXT:
- Incident summary (one sentence): [INSERT]
- Detected at: [INSERT TIMESTAMP, with timezone]
- Resolved at: [INSERT TIMESTAMP, with timezone]
- Affected services or users: [INSERT]
- Timeline notes (raw, unordered is fine; include timestamps where you have them):
[INSERT TIMELINE NOTES]
- Root cause as known so far: [INSERT]
- Remediation actions taken during the incident: [INSERT]
- Open questions or outstanding items: [INSERT or write "none"]

CONSTRAINTS:
- Output is internal engineering only. Do not write for an executive or external audience.
- Blameless tone. Do not name individuals as the cause. Reference roles or actions.
- Do NOT speculate beyond the data provided. If root cause is uncertain, say so.
- Do NOT invent timestamps. Use the timeline as given.
- Length target: 400-700 words. Pad ruthlessly less rather than more.

OUTPUT FORMAT:
Markdown with these sections:
- # PIR: <one-line incident title>
- ## Summary (3-4 sentences)
- ## Timeline (chronological table: Time, Event, Action)
- ## Root Cause
- ## Contributing Factors (bulleted)
- ## What went well (bulleted)
- ## What needs to improve (bulleted, with owner placeholders like [OWNER])
- ## Action items (numbered, each with [OWNER] and target date placeholder [DATE])
```

### Example output structure

(See live example output structure in the rendered version of this prompt; substantially follows the standard PIR format used in SRE/NetOps culture.)

### Vendor adaptation

This prompt is vendor-neutral. Timeline data comes from whatever source your team uses (Slack, ticket, syslog, NMS). No CLI dependencies.

### Why this saves time

PIRs do not get written because writing them is tedious. The model is genuinely good at converting unstructured timeline notes into a structured document, and a structured document is what makes the action items actually get owned. The 400-700 word target keeps it short enough that people will read it.

---

# Category 4: Compliance and Audit

---

## Prompt 10: ACL Shadowing and Overlap Auditor

**Category:** Compliance and Audit
**Safety:** Enterprise-only (uses real ACL entries with hosts, networks, and services)
**When to use:** Reviewing an ACL or firewall policy that has grown organically over years. Looking for shadowed rules (never matched), duplicate intent, and rules that are too permissive given the rules above them.

### The prompt

```
You are a senior network security engineer reviewing an access-control list for shadowing, redundancy, and overly permissive entries. The list will be processed top-down (first match wins).

CONTEXT:
- ACL or policy name: [INSERT NAME]
- Direction and binding: [INSERT, e.g., "inbound on edge-rtr-01 GigabitEthernet0/0", or "FortiGate IPv4 policy WAN to LAN"]
- The ACL entries, in order:
[INSERT FULL ACL]

CONSTRAINTS:
- Process top-down. First match wins.
- For each entry, evaluate: is it shadowed by a higher entry? is it redundant with another entry? is it overly permissive given the entries above and below?
- Use the correct ACL terminology: "shadowed" means a higher rule prevents this rule from ever matching. "Redundant" means another rule already covers the same traffic but neither shadows the other. "Overly permissive" means broader than necessary.
- Do NOT recommend changes outside the scope of this ACL. Do not suggest adding rules that are not implied by the existing ones.
- If you spot an unintended bonus finding (e.g., ICMP scoped wider than necessary), include it but mark it as a "bonus finding" so I know it was not in my original ask.

OUTPUT FORMAT:
A markdown table with these columns:
| Line # | Entry | Finding | Severity | Reasoning | Recommendation |

After the table, a short paragraph (3-5 sentences) summarizing the most critical finding and the recommended order of remediation.
```

### Example output (abbreviated)

| Line # | Entry | Finding | Severity | Reasoning | Recommendation |
|---|---|---|---|---|---|
| 4 | `permit tcp host 10.0.0.5 any eq 443` | Shadowed | High | Line 3 already permits all TCP from `10.0.0.0/24`. Line 4 will never match. | Remove Line 4. |
| 7 | `permit ip any any` | Overly permissive | Critical | Catch-all permit at the bottom defeats every preceding deny. | Replace with explicit permits or `deny ip any any` if default-deny is intended. |
| 6 | `permit icmp any any` | Bonus finding | Medium | ICMP scoped to entire any-to-any. Likely broader than intended for production. | Restrict to specific source or destination subnets if used for monitoring. |

### Vendor adaptation

- **Arista EOS:** Same `ip access-list` semantics. Prompt works as-is.
- **FortiOS:** Replace "ACL" with "firewall policy". Constraints become "FortiGate policies process top-down by sequence number, first match wins". Output format unchanged.
- **PAN-OS:** Replace "ACL" with "security policy rule". PAN-OS rules also process top-down. Note: PAN-OS uses zone + service + application, so the "Entry" column should include all three.
- **Junos (SRX):** Use "security policies" terminology. Process is top-down within a from-zone/to-zone context.
- **ArubaOS-CX:** Same `ip access-list extended` semantics.

### Why this saves time

ACLs accumulate scar tissue. Every change adds a rule, no change removes one. Reading a 200-line ACL by hand looking for shadowing is tedious. The model is actually good at this kind of formal logic check. The example in the EP001 video catches a planted shadowing problem AND a real ICMP scoping issue the engineer did not put there. That is the typical pattern.

---

## Prompt 11: CIS Benchmark Audit (Cisco IOS-XE)

**Category:** Compliance and Audit
**Safety:** Enterprise-only (uses a full running config)
**When to use:** Pre-audit. Compliance team is asking about hardening posture. You have running configs and want a structured gap report against CIS controls without buying Titania.

### The prompt

```
You are a network security auditor reviewing a Cisco IOS-XE device configuration against CIS Cisco IOS Benchmark controls. Output is a gap report.

CONTEXT:
- Device hostname: [INSERT HOSTNAME]
- Running configuration:
[INSERT FULL RUNNING CONFIG]
- CIS Benchmark version reference: CIS Cisco IOS XE 17.x Benchmark (publicly available; cite specific control numbers in your output where possible).

CONSTRAINTS:
- Audit against these control families at minimum: management-plane access, AAA, logging, NTP, SSH (banner, version 2 only, transport input ssh), password policies, SNMP, control-plane policing, ACL hygiene, unused services (CDP, LLDP on insecure interfaces, HTTP server, DNS lookup).
- For each finding, state: control number (where you can confidently cite it), the current configured state, the CIS-recommended state, severity (High/Medium/Low), and the specific commands to remediate.
- Do NOT invent CIS control numbers. If you are not certain of the exact number, say "CIS family: management-plane access" without a specific number.
- Do NOT include findings for features that are not configured at all unless their absence is itself a violation.

OUTPUT FORMAT:
Markdown with these sections:
- # CIS Audit: <hostname>
- ## Summary (count of findings by severity)
- ## Findings (numbered, each with **Control**, **Current State**, **Recommended State**, **Severity**, **Remediation**)
- ## Manual Verification Required (controls that cannot be confirmed from config alone, e.g., banner content review, password complexity at the AAA server)
```

### Vendor adaptation

- **Arista EOS:** Use the CIS Cisco/Arista mapping where available; fall back to general best practices documented in the Arista security configuration guide.
- **Junos:** Use the CIS Juniper Junos OS Benchmark. The control families are similar; the syntax is different.
- **ArubaOS-CX:** No formal CIS benchmark for ArubaOS-CX as of 2026. Audit against general hardening standards (NIST 800-53 NW-relevant controls, AAA, logging, SSH, SNMP, banner).
- **FortiOS:** Use the CIS Fortinet FortiGate Benchmark. Audit against FortiGate-specific controls.

### Why this saves time

A real CIS gap analysis by hand takes a day per device family and the auditor reading it has to verify the same controls anyway. The prompt produces a structured report your auditor recognizes, in the format they expect. You retain the ability to challenge any finding before it goes upstream.

---

## Prompt 12: Configuration Drift Analyzer

**Category:** Compliance and Audit
**Safety:** Enterprise-only (uses two production configs)
**When to use:** Pre- and post-maintenance window. You want to know exactly what changed, in plain English, ignoring noise (timestamps, certificate counters, dynamic routing tables, encrypted password rotations).

### The prompt

```
You are a senior network engineer analyzing configuration drift between two snapshots of the same device.

CONTEXT:
- Device hostname: [INSERT HOSTNAME]
- Snapshot A (the "before"): [INSERT TIMESTAMP and config]
- Snapshot B (the "after"): [INSERT TIMESTAMP and config]

CONSTRAINTS:
- Identify only logical, intent-bearing changes. Ignore: dynamic timestamps, log uptime references, changing encrypted password hashes when the underlying password did not change, NTP clock-period drift, certificate validity counters.
- Group findings by config section: management plane, AAA, interfaces, routing, ACLs, services, miscellaneous.
- For each change, state whether it is: ADDITION, REMOVAL, or MODIFICATION.
- For each change, infer intent if possible. If you cannot infer intent, say "intent unclear from config alone".
- Do NOT speculate about why the change was made. Stick to what changed.

OUTPUT FORMAT:
Markdown with these sections:
- # Drift Analysis: <hostname>
- ## Summary (total changes, breakdown by ADDITION/REMOVAL/MODIFICATION)
- ## Changes by Config Section (one subsection per section, each with a markdown table: Type, Lines, Description, Intent)
- ## Suggested Verification Commands (bulleted, prioritized by change risk)
```

### Vendor adaptation

This prompt is largely vendor-neutral. Replace the "config sections" list in the constraint to match the target vendor structure. For Junos, group by hierarchy (`[edit system]`, `[edit interfaces]`, `[edit protocols]`, etc.) instead of Cisco-style sections.

### Why this saves time

`diff` of two configs gives you noise. This prompt gives you the changes that matter, grouped, with intent. After a maintenance window, this is the artifact you paste into the change ticket to close it out.

---

# Category 5: Code Generation

The three prompts in this category are public-safe. They produce structural code with no real device data inside, so they are appropriate to run on free-tier AI. You will substitute your own data inside the resulting scaffold separately, on a paid tier or directly in your editor.

---

## Prompt 13: Jinja2 Switchport and VLAN Template Builder

**Category:** Code Generation
**Safety:** Public-safe (template logic only; no device data)
**When to use:** You are starting an Ansible or Nornir project and need a clean, reusable Jinja2 template for switchport configuration. Used as the starting scaffold, not the final template.

### The prompt

```
You are a network automation engineer writing a Jinja2 template for switchport configuration on Cisco IOS-XE access switches.

CONTEXT:
- The template will be rendered against per-host variables defined in a YAML inventory.
- Required variable structure (this is the contract; the template must consume these):
  hostname: <string>
  interfaces:
    - name: <string>
      mode: access | trunk
      vlan: <int>            # for access mode
      allowed_vlans: <list>  # for trunk mode
      voice_vlan: <int>      # optional, access mode only
      description: <string>
      stp_portfast: <bool>
      stp_bpduguard: <bool>

CONSTRAINTS:
- Output a single .j2 template file.
- Handle both access and trunk modes via if/else.
- Apply portfast and bpduguard only when their flags are true.
- Skip voice_vlan if not defined.
- Include a comment block at the top of the template explaining the contract and one example invocation.
- Do NOT generate the YAML inventory. Template only.

OUTPUT FORMAT:
A single fenced code block tagged `jinja2` with the template content. No commentary outside the block.
```

### Why this saves time

Most engineers learning Jinja2 burn an evening on whitespace and `{%- -%}` trimming. The prompt gives you a clean starting template you can immediately render and iterate on. You learn the syntax by reading working code, not Jinja2 docs.

---

## Prompt 14: Netmiko + Nornir Multi-Threaded Scaffold

**Category:** Code Generation
**Safety:** Public-safe (scaffold only; no device data)
**When to use:** Starting a new automation script and you want production-shaped Nornir + Netmiko scaffolding without copy-pasting from three different blog posts.

### The prompt

```
You are a senior network automation engineer writing a Nornir + Netmiko script that runs a single show command across a multi-vendor inventory and writes per-device output to disk.

CONTEXT:
- The script must run from a CLI entrypoint accepting two arguments: --command "<show command>" and --output-dir <path>.
- The Nornir inventory is loaded from a `config.yaml` plus `hosts.yaml` and `groups.yaml` in standard SimpleInventory format. Do not generate the inventory files. Reference them by path.
- Vendors in scope: cisco_ios, cisco_xe, arista_eos, juniper_junos, fortinet, paloalto_panos, aruba_aoscx.

CONSTRAINTS:
- Use Nornir 3.x and the nornir-netmiko plugin (NOT nornir-utils for execution).
- Use ThreadPoolExecutor implicitly through Nornir's built-in concurrency. Do not roll your own threading.
- Each device's output goes to `<output-dir>/<hostname>.txt`.
- Handle and log per-device exceptions cleanly. One bad device does not abort the run.
- Include a top-of-file comment block matching this format:
"""
Script: <name>.py
Purpose: <one line>
Author: <leave blank for user to fill>
Lab note: Tested against <leave blank>
Usage: python <name>.py --command "show version" --output-dir ./output
"""
- Do NOT generate the YAML inventory files. Just the Python script.
- Do NOT include credential handling beyond what Nornir's inventory natively supports. The user can wire credentials in via inventory `password` or environment variables.
- Do NOT include dead-code branches, placeholder guards, or commented-out alternatives. Either implement a check or omit it entirely. The script should look like production code, not draft code.

OUTPUT FORMAT:
A single fenced code block tagged `python` containing the complete script. No commentary outside the block.
```

### Why this saves time

The hard part of Nornir + Netmiko is the boilerplate, not the network logic. This prompt produces production-shaped scaffolding (concurrency, exception handling, output organization) so you can drop your show command in and run it the same hour.

---

## Prompt 15: Ansible Multi-Vendor Playbook Scaffold

**Category:** Code Generation
**Safety:** Public-safe (scaffold only; no device data)
**When to use:** You need an Ansible playbook scaffold for a multi-vendor inventory and you want to skip the YAML indentation pain and the "which collection do I import" debate.

### The prompt

```
You are a senior network automation engineer writing an Ansible playbook scaffold that runs a single read-only command against a multi-vendor inventory and saves the output per host.

CONTEXT:
- Vendors in scope: cisco.ios, cisco.iosxe, arista.eos, junipernetworks.junos, fortinet.fortios, paloaltonetworks.panos, arubanetworks.aoscx.
- The inventory uses ansible_network_os group_vars to identify each device's vendor.

CONSTRAINTS:
- Use the modern collections (cisco.ios.ios_command, arista.eos.eos_command, etc.). Do NOT use the deprecated network_cli generic modules.
- One play per vendor, gated by a `when: ansible_network_os == "..."` clause.
- Output is written to `./output/{{ inventory_hostname }}.txt` using the `copy` or `template` module against a registered command result.
- Variables to parameterize: `target_command` (the show command), `output_dir`.
- Include block-level error handling (`block`/`rescue`) so a failed device produces a logged warning, not a playbook abort.
- Do NOT generate the inventory. Reference it by path.

OUTPUT FORMAT:
A single fenced code block tagged `yaml` containing the complete playbook. After the playbook, in a separate fenced code block tagged `yaml`, generate a sample `requirements.yml` listing the collections needed.
```

### Vendor limitation note

FortiOS and PAN-OS do not expose a generic show-command runner the way Cisco IOS, Arista EOS, Junos, and Aruba AOS-CX do. The scaffold will use `fortinet.fortios.fortios_monitor` (REST selectors) for FortiOS and `paloaltonetworks.panos.panos_op` (operational XML) for PAN-OS instead of a plain CLI command module. Plan to override `target_command` semantics for those two vendors, or wrap with a vendor-specific variable (e.g. `target_command_panos`) in your inventory.

### Why this saves time

Ansible's network collections changed substantially in 2.10+ and the docs are scattered across vendor sites. This prompt produces a clean scaffold using modern collections, with the `requirements.yml` matched to it. You drop your inventory in, fill in `target_command`, and run.

---

# Honest Limitations: Where AI Still Fails on Networking

The pack would not be complete without this section. The same model that produces a clean OSPF config in Prompt 1 will, given the wrong question, confidently destroy a production network. Read this before you treat AI output as authoritative.

## Anti-pattern 1: "Diagnose and fix"

Asking the model to triage AND remediate in one shot is the most consistent failure mode in network engineering today. The model produces syntactically clean commands that apply to the wrong address family, clear the wrong neighbor, or assume a topology that does not exist. Every prompt in this pack stops short of "and here is the fix command, run it." Diagnosis comes from AI. Remediation comes from you.

## Anti-pattern 2: Subnetting and cryptographic math

Models are probabilistic text engines. They are not calculators. Asking for a complex VLSM design, a wildcard mask conversion across 14 subnets, or a hash collision check produces results that look right and sometimes are not. Use a real subnet calculator. Use real crypto libraries. The model can write a script that calls the calculator. It is not the calculator itself.

## Anti-pattern 3: Blind cross-vendor translation

"Translate this Cisco ASA config to Palo Alto" without specifying architectural constraints is dangerous. ASA uses interface-bound ACLs. PAN-OS uses zone-based policies. An unconstrained translation can map interfaces to zones incorrectly and silently allow lateral traffic that the original ASA blocked. Translation prompts must specify the architectural mapping. Better yet: translate manually and use AI to validate, not generate.

## Anti-pattern 4: Massive unfiltered syslog dumps

Pasting 10,000 lines of syslog into a chat box and asking "what is wrong" is asking the model to invent patterns. It will. Models will correlate an unrelated authentication failure with a spanning-tree change because the timestamps were close. Always scope syslog input by time window AND by relevant subsystem. Filter first, prompt second.

## Anti-pattern 5: Treating AI output as authoritative for change windows

Every output in this pack is a draft. The engineer reviewing the draft is responsible for what runs. If your team is using AI to skip review and push commands directly into production, you are accumulating risk that does not show up until something breaks at 2am. Use AI to accelerate the work that produces the change. Do not use it to skip the review.

## Anti-pattern 6: Trusting AI on vendor command syntax for new platforms

Models trained primarily on older docs will hallucinate syntax for newly released features (e.g., post-2025 features added to a vendor OS the model has not seen recent docs for). Always cross-check command syntax against the vendor's current command reference if the prompt is touching anything released in the last 12 months.

---

# Changelog and Roadmap

## v1.0.1 (2026-05-14)

Post-release fix to Prompt 4 (OSPF Adjacency and MTU Triage).

- **What was wrong.** The original CONTEXT only requested `show ip ospf neighbor` and `show ip ospf interface` from each end. During EP001 recording, an `ip mtu 1400` override on one side of a point-to-point link was not surfaced clearly by those two views, and the model did not catch the IP MTU mismatch.
- **What changed.** CONTEXT now requires four commands per side: `show ip ospf neighbor`, `show ip ospf interface`, `show ip interface`, and `show running-config interface`. CONSTRAINTS now explicitly tell the model not to rely on `show ip ospf interface` alone for IP MTU, to pull the operational value from `show ip interface`, and to check running-config for any explicit `ip mtu` line. Output now includes a Source column citing which command surfaced each parameter.
- **Vendor adaptation notes** for Arista EOS, Junos, ArubaOS-CX, and FortiOS updated to match.
- **Credit.** Caught during recording when the original prompt missed the demo break. Real lab beats clever prompt every time.

## v1.0 (2026-05-12)
Initial release.

- 15 prompts across 5 categories (Configuration Generation, Troubleshooting, Documentation, Compliance and Audit, Code Generation).
- 4-piece anatomy (Role / Context / Constraint / Output format) applied uniformly.
- Safety labeling: 12 Enterprise-only, 3 Public-safe.
- Multi-vendor adaptation notes for Cisco IOS-XE, Arista EOS, Junos, ArubaOS-CX, FortiOS, and PAN-OS where applicable.
- Honest limitations section covering 6 anti-patterns.
- Every prompt tested before release against representative inputs on Sonnet 4.6, Opus 4.7, and Gemini 2.5 Pro. The 5 highest-stakes prompts (BGP analyzer, interface counter, draw.io topology, CIS audit, drift analyzer) passed cross-model checks. All models honored the no-fabricated-CIS-control-numbers constraint and resisted inventing faults when interface counters were clean.

## v1.1 (planned for 2026-08)

Likely additions, in priority order. Subscribers to https://join.gtalkstech.com get the v1.1 release email when it ships.

- **Change ticket / MOP builder.** Pre-check, action, post-check, rollback structure. Vendor-neutral.
- **Cisco ASA to PAN-OS migration helper.** Architecturally-aware (interface-to-zone mapping, policy granularity), not blind translation.
- **GlobalProtect VPN log triage.** Authentication phase isolation, IP pool exhaustion detection.
- **FortiGate IKE debug parser.** Translates `diagnose debug application ike` output into mismatched-parameter callouts.
- **Aruba CX VLAN/AAA standardization generator.** Sister prompt to Prompt 1's OSPF generator, but for access-layer config.
- **Vendor-specific variants of existing pack prompts.** Each major prompt with a dedicated FortiOS, Junos, and Arista version (instead of constraint-line adaptation).

If a prompt above is critical for your week and you cannot wait until August, email garrett@gtalkstech.com. The mailing list gets early-access drafts of in-progress prompts.

---

# Feedback and Contributions

This pack is maintained quarterly. The most useful additions come from working engineers, not from me reading docs.

If you have:
- A prompt you use weekly that should be in v1.1
- A vendor adaptation that does not work as written
- A failure mode that should be in the anti-patterns section
- A correction to vendor command syntax

Send it to **garrett@gtalkstech.com** with subject line "Prompt Pack v1.x Feedback". Real-name credit in the changelog if your contribution ships, unless you ask me to keep it anonymous.

---

# About G Talks Tech

G Talks Tech is a YouTube channel and mailing list for senior mid-market network engineers who want to use AI and automation without the hype.

- YouTube: https://www.youtube.com/@GTalksTechOfficial
- Mailing list: https://join.gtalkstech.com
- LinkedIn: https://www.linkedin.com/in/garrett-masters-ba6234101/
- GitHub: https://github.com/GTalksTech

If this pack saved you time, the most useful thing you can do is send it to one engineer who would also use it. The list grows by referral.

---

*Version 1.0. Released 2026-05-05. Next update: August 2026.*
