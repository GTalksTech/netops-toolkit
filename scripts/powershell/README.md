# Get-NetworkEvidence.ps1

A quick triage check for the ticket that says "the network is down." Point
it at one target and it checks three layers in order: does the name
resolve, is the port reachable, and what does the app answer. The output
is plain text you paste straight into the ticket.

**Video:** [It's Not the Network: The 10-Minute Framework to Stop Getting Blamed](https://youtu.be/kdyXSark_ck)
**Write-up:** [It's Not the Network](https://gtalkstech.com/blog/its-not-the-network/)

## What This Is

| Layer | How it checks | What it prints |
|-------|---------------|----------------|
| [1] DNS | `Resolve-DnsName` | PASS, or FAIL and stop |
| [2] TCP port | `Test-NetConnection -Port` | PASS, or FAIL and stop |
| [3] App | `Invoke-WebRequest -Method Head` to `https://<target><uri>` | PASS on a 200, FAIL on any 5xx, WARN on any other status, ERROR if the request fails outright (a timeout or a TLS problem, for example) |

If DNS and TCP pass and the app answers with a 5xx, your traffic got there
and something on the server side answered with an error. That is the
evidence the ticket needs.

## Prerequisites

- Windows. `Resolve-DnsName` and `Test-NetConnection` are Windows-only
  cmdlets.
- PowerShell 7 or later, run as `pwsh`. The app check uses
  `-SkipHttpErrorCheck`, which Windows PowerShell 5.1 (the version that
  comes with Windows) does not have.
- No lab needed. The default target is httpbin.org, a public test site, so
  it runs anywhere with internet access.

## Quick Start

```powershell
# The demo: httpbin.org on port 443, a page that always returns a server error
.\Get-NetworkEvidence.ps1

# Your app
.\Get-NetworkEvidence.ps1 -Target "app.example.com" -Port 443 -URI "/"
```

| Parameter | Default | What it does |
|-----------|---------|--------------|
| `-Target` | `httpbin.org` | Hostname to check |
| `-Port` | `443` | Port for the TCP check |
| `-URI` | `/status/500` | Path for the app check. Start it with `/`. |

With no arguments, you should see DNS and TCP pass and the app fail with a
500. That is the case the script was built for.

## Known Limitations

- **One target per run.**
- **The app check ignores `-Port`.** It always requests
  `https://<target><uri>`, which means HTTPS on port 443. For plain HTTP or
  a non-standard port, layer 3 checks the wrong thing even when layer 2
  passes.
- **A 5xx proves the path to whatever answered, not to the app.** If a
  load balancer or proxy sent it (a 502, 503 or 504 is typical), the fault
  can still sit behind that device, including its network path to the app.
- **HEAD, not GET.** An app that rejects HEAD with a 405 shows up as WARN
  even when it is healthy.
- **Only a 200 is a PASS.** Other 2xx answers, like a 204, show as WARN.
- **It stops at the first DNS or TCP failure**, so you see where the chain
  broke, not a full report.
- **Console only.** Nothing is saved to a file.
