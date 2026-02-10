# Network Incident Communication Templates
## GTalks Tech - "It's Not the Network" Kit

---

## Template 1: Initial Incident Notification (Internal Team)

**Purpose:** Quick heads-up to your team when an incident is reported

**When to use:** Within 5-10 minutes of receiving the initial report

**Template:**

```
Subject: Incident Report - [Brief Description] - [Severity]

Incident opened: [Ticket #]
Reported by: [User/Team]
Time reported: [HH:MM]
Issue: [1-2 sentence description]

Current status: Investigating
Next update: [Time - usually 30-60 min]

Assigned to: [Your name/team]
```

**Example:**

```
Subject: Incident Report - Application X slow response - Medium

Incident opened: INC12345
Reported by: Finance team
Time reported: 09:15
Issue: Users in Building A reporting slow response times on Application X. No complete outages reported.

Current status: Investigating
Next update: 10:00

Assigned to: Network Operations
```

---

## Template 2: Leadership/Stakeholder Update (During Active Incident)

**Purpose:** Keep leadership informed without technical overload

**When to use:** Every 30-60 minutes during active incidents, or when asked for status

**Template:**

```
Subject: Update - [Incident Description] - [Time]

Current status: [Investigating / Identified / Resolving / Monitoring]

Impact:
- Who: [Affected users/systems]
- What: [Specific symptoms]
- Severity: [High/Medium/Low]

What we know:
- [Finding 1]
- [Finding 2]
- [Finding 3]

What we've ruled out:
- [Item 1]
- [Item 2]

Next steps:
- [Action 1] - [Owner] - [ETA]
- [Action 2] - [Owner] - [ETA]

Next update: [Time]
```

**Example:**

```
Subject: Update - Application X Performance - 10:30

Current status: Identified

Impact:
- Who: 45 users in Building A (Finance and HR departments)
- What: Slow application response times (15-20 second delays)
- Severity: Medium

What we know:
- Issue is isolated to Building A users only
- Building B and remote users are unaffected
- Application server and database performance are normal
- Network latency tests show normal response times

What we've ruled out:
- Internet circuit issues (ISP confirms no problems)
- Firewall or core switching problems (utilization normal)
- WAN connectivity (all sites show green)

Next steps:
- Testing application server directly from Building A - Network Team - 10:45
- Working with vendor to check for known issues - App Team - 11:00
- Packet capture in progress for deeper analysis - Network Team - Ongoing

Next update: 11:15
```

---

## Template 3: "It's Not the Network" Evidence Summary

**Purpose:** Clearly document that network is functioning normally during an incident

**When to use:** When application/database/server teams are pointing at the network

**Template:**

```
Subject: Network Analysis - [Incident #] - Network Ruled Out

Incident: [Ticket #]
Issue: [Brief description]
Analysis completed: [Date/Time]

Network Health Check - PASSED

Layer 1 (Physical):
✓ [Finding] - [Evidence]
✓ [Finding] - [Evidence]

Layer 2 (Data Link):
✓ [Finding] - [Evidence]
✓ [Finding] - [Evidence]

Layer 3 (Network):
✓ [Finding] - [Evidence]
✓ [Finding] - [Evidence]

Layer 4 (Transport):
✓ [Finding] - [Evidence]
✓ [Finding] - [Evidence]

Summary:
Network connectivity and performance between [Source] and [Destination] is normal. No packet loss, latency issues, or configuration problems detected. Issue appears to be application-layer related.

Recommended next steps:
1. [Action for app/database/server team]
2. [Action for app/database/server team]

Evidence attached:
- [File 1]
- [File 2]
```

**Example:**

```
Subject: Network Analysis - INC12345 - Network Ruled Out

Incident: INC12345
Issue: Application X slow response for Building A users
Analysis completed: 2026-02-09 11:30

Network Health Check - PASSED

Layer 1 (Physical):
✓ Building A switch uplinks - No errors, 1G full duplex
✓ Fiber connections - Clean light levels, no CRC errors

Layer 2 (Data Link):
✓ VLAN 10 spanning tree - Root port stable, no topology changes
✓ Switch CPU/memory - 15% / 42%, normal range

Layer 3 (Network):
✓ Ping to application server - 2ms average, 0% loss over 1000 packets
✓ Traceroute - 3 hops, all responding normally
✓ Routing table - Correct next-hop, no flapping

Layer 4 (Transport):
✓ TCP handshake time - 8ms average (baseline: 6-10ms)
✓ No RST packets or connection failures observed
✓ Firewall session table - 2,400 active sessions (normal)

Summary:
Network connectivity and performance between Building A users (VLAN 10) and Application X server (10.50.20.15) is normal. No packet loss, latency issues, or configuration problems detected. Issue appears to be application-layer related based on normal network response but slow application rendering.

Recommended next steps:
1. Application team: Check Application X server resource utilization (CPU, memory, disk I/O)
2. Database team: Review query execution times and database locks
3. Application team: Review application logs for errors or slow transactions

Evidence attached:
- continuous_ping_results.txt
- traceroute_output.txt
- switch_interface_stats.log
- firewall_session_analysis.xlsx
```

---

## Template 4: Vendor/ISP Escalation

**Purpose:** Open a case with external vendor/ISP with all necessary information

**When to use:** When you've ruled in a vendor/ISP issue and need their support

**Template:**

```
Subject: [Severity] - [Circuit ID / Service Description] - [Brief Issue]

Account: [Your company account #]
Contact: [Your name]
Phone: [Direct number]
Email: [Your email]

Service affected: [Circuit ID, site name, or service description]

Issue description:
[2-3 sentences describing the problem from a user perspective]

Impact:
- Users affected: [Number / Department / Location]
- Business impact: [Critical / High / Medium / Low]
- Duration: [When it started]

Troubleshooting completed:
1. [Action taken] - [Result]
2. [Action taken] - [Result]
3. [Action taken] - [Result]

Evidence:
- [Specific metric or test result]
- [Specific metric or test result]
- [Attachment description]

Expected vendor action:
[Clear ask - examples: "Check circuit for errors," "Verify BGP peering status," "Investigate packet loss"]

Requested response time: [Based on SLA]
```

**Example:**

```
Subject: HIGH - Circuit ABC123 - Intermittent Packet Loss

Account: ACME-12345
Contact: John Smith
Phone: 555-0100
Email: john.smith@company.com

Service affected: MPLS Circuit ABC123, Main Office to Data Center

Issue description:
Users are experiencing intermittent application timeouts and dropped connections between Main Office and Data Center. Issues began at approximately 08:00 this morning. Symptoms include database query failures and file transfer interruptions.

Impact:
- Users affected: 120 users in Main Office
- Business impact: High - Critical business applications unavailable
- Duration: 3 hours (started 08:00)

Troubleshooting completed:
1. Continuous ping tests - 3-5% packet loss observed consistently
2. Local router interface checks - No errors, correct configuration
3. Failover to backup circuit - Issue does NOT occur on backup link
4. Router reboot - No change, issue persists

Evidence:
- Packet loss averaging 3.2% over 2 hour period
- Latency spiking from normal 12ms to 150-200ms intermittently
- Router interface shows 0 errors, clean logs
- Screenshots and logs attached

Expected vendor action:
Check MPLS circuit ABC123 end-to-end for errors, investigate cause of intermittent packet loss and latency spikes on primary path.

Requested response time: 1 hour (per SLA for High severity)
```

---

## Template 5: Post-Incident Summary (RCA-Lite)

**Purpose:** Document what happened, what was done, and lessons learned

**When to use:** Within 24-48 hours after incident resolution

**Template:**

```
Subject: Post-Incident Summary - [Incident #] - [Brief Description]

Incident: [Ticket #]
Opened: [Date/Time]
Resolved: [Date/Time]
Total duration: [Hours/Minutes]

Impact:
- Users affected: [Number/Department]
- Services impacted: [List]
- Business impact: [Description]

Timeline:
[HH:MM] - [Event]
[HH:MM] - [Event]
[HH:MM] - [Event]

Root cause:
[Clear description of what actually caused the issue]

Resolution:
[What action fixed the problem]

Why it took this long:
[Honest description of troubleshooting challenges or delays]

Prevention:
- [Action item 1] - [Owner] - [Due date]
- [Action item 2] - [Owner] - [Due date]

Lessons learned:
- [Learning 1]
- [Learning 2]
```

**Example:**

```
Subject: Post-Incident Summary - INC12345 - Application X Performance Issues

Incident: INC12345
Opened: 2026-02-09 09:15
Resolved: 2026-02-09 14:30
Total duration: 5 hours 15 minutes

Impact:
- Users affected: 45 users in Building A (Finance and HR)
- Services impacted: Application X (financial reporting system)
- Business impact: Medium - Month-end reports delayed, no data loss

Timeline:
09:15 - Initial report received from Finance team
09:25 - Network team engaged, initial investigation started
10:30 - Network ruled out, escalated to application team
11:45 - Application team identified database connection pool exhaustion
12:30 - Database connection pool settings adjusted
13:15 - Application server restarted with new configuration
14:00 - Users report normal performance
14:30 - Incident closed after 30-minute monitoring period

Root cause:
Database connection pool on Application X server was configured for maximum 50 connections. During month-end processing, actual demand exceeded 50 concurrent connections, causing new requests to queue and timeout. This created slow response times for all users.

Resolution:
Database connection pool increased from 50 to 150 connections. Application server restarted with new configuration. Performance returned to normal immediately.

Why it took this long:
Initial troubleshooting focused on network and infrastructure (switches, firewalls, circuits) because symptoms appeared network-related. Application team required additional time to identify connection pool exhaustion because this metric is not monitored by default.

Prevention:
- Add database connection pool monitoring to Application X - App Team - 2026-02-16
- Review and right-size connection pools for all critical applications - App Team - 2026-02-23
- Update troubleshooting runbook to include application-layer checks earlier - Network Team - 2026-02-12

Lessons learned:
- Slow application response does not always mean network issues
- Connection pool exhaustion can mimic network latency problems
- Application-layer metrics should be checked alongside network metrics during initial triage
```

---

## Template 6: Quick Status for "Just Checking In" Requests

**Purpose:** Fast response when someone asks "any update?" during an incident

**When to use:** Quick replies to avoid disrupting your troubleshooting

**Template:**

```
Still investigating. No change since last update at [Time].

Current focus: [One sentence]

Next scheduled update: [Time]
```

**Example:**

```
Still investigating. No change since last update at 11:15.

Current focus: Working with ISP to check circuit for errors.

Next scheduled update: 12:00
```

---

## Bonus: AI Prompt Pack for Incident Communication

**Use these prompts to speed up your incident documentation:**

### Prompt 1: Turn rough notes into a leadership update

```
I need to send a status update to leadership about an ongoing incident. Here are my rough notes:

[Paste your notes here]

Please format this into a clear, non-technical leadership update using this structure:
- Current status (Investigating/Identified/Resolving/Monitoring)
- Impact (who, what, severity)
- What we know
- What we've ruled out
- Next steps with owners and ETAs
- Next update time

Keep it concise and avoid technical jargon.
```

### Prompt 2: Create a vendor escalation email

```
I need to escalate an issue to our [ISP/vendor]. Here's what I know:

Service: [Circuit ID or service description]
Problem: [What's happening]
Impact: [Who's affected and how badly]
What I've tested: [Your troubleshooting steps]
Evidence: [Metrics or test results]

Please write a professional escalation email that clearly explains the issue and what we need them to investigate. Include all relevant technical details but keep it organized.
```

### Prompt 3: Write a "network ruled out" summary

```
I need to document that the network is NOT the cause of this incident. Here's my evidence:

[Paste your test results, metrics, logs]

Please write a clear summary showing that network connectivity and performance are normal, organized by OSI layers (physical, data link, network, transport). Include the evidence for each layer and conclude with recommended next steps for the application/database/server team.
```

### Prompt 4: Create a post-incident summary

```
I need to write a post-incident summary. Here's what happened:

Timeline: [Key events with timestamps]
Root cause: [What actually caused it]
How we fixed it: [Resolution steps]
Impact: [Who was affected, for how long]

Please format this into a professional post-incident summary with these sections: Impact, Timeline, Root Cause, Resolution, Why It Took This Long, Prevention (action items), and Lessons Learned.
```

---

## Usage Notes

**Customization:**
- These templates are starting points. Adapt them to match your organization's tone and format.
- Add or remove sections based on your company's incident management process.
- Save your customized versions somewhere easily accessible (email templates, OneNote, Notion, etc.).

**When to use which template:**
- Template 1: Always, for every incident
- Template 2: For medium/high severity incidents, or when leadership asks
- Template 3: When you need to prove the network is healthy
- Template 4: When escalating to external vendors/ISPs
- Template 5: After resolution, for documentation and learning
- Template 6: Quick replies during active troubleshooting

**Pro tips:**
- Copy these into your email client as templates or saved drafts
- Keep a notepad file with the template structure for quick access
- Use the AI prompts to speed up writing (but always review before sending)
- Take screenshots and save logs as you troubleshoot (don't wait until later)
- When in doubt, over-communicate rather than under-communicate

**Employer compatibility:**
- If your organization uses a ticketing system with structured fields, extract the relevant information from these templates and paste into the appropriate fields.
- For companies with strict change management or incident response procedures, these templates supplement (not replace) your existing workflows.
- The core structure (status, impact, evidence, next steps) works across most formats.

---

## Download and Use

Save this document and refer back to it during incidents. The more you use these templates, the faster you'll be able to communicate clearly under pressure.

For more practical network engineering workflows and templates, visit https://gtalkstech.com

---

© 2026 GTalks Tech - "It's Not the Network" Incident Communication Templates