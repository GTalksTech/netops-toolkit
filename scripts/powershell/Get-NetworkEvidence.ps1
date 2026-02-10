<#
.SYNOPSIS
    G Talks Tech - Rapid Evidence Collector for Network Triage.
.DESCRIPTION
    Runs a layered check (DNS -> TCP -> HTTP) to prove if the network is at fault.
    Outputs a clean text block for ticketing systems (ServiceNow/Jira).
.EXAMPLE
    .\Get-NetworkEvidence.ps1 -Target "httpbin.org" -Port 443 -URI "/status/500"
#>

param (
    [string]$Target = "httpbin.org",
    [int]$Port = 443,
    [string]$URI = "/status/500"  # This simulates the broken page
)

Write-Host "`n🕵️  G TALKS TECH - INCIDENT EVIDENCE COLLECTOR" -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor Gray
Write-Host "Targeting: $Target on Port $Port `n"

# 1. DNS CHECK
Write-Host "[1] Checking DNS..." -NoNewline
try {
    $dns = Resolve-DnsName -Name $Target -ErrorAction Stop | Select-Object -First 1
    Write-Host " PASS " -ForegroundColor Green -NoNewline
    Write-Host "($($dns.IPAddress))"
} catch {
    Write-Host " FAIL " -ForegroundColor Red
    Write-Host "   -> ERROR: Could not resolve hostname. STOP HERE."
    exit
}

# 2. TCP CONNECT (The "Not The Network" Proof)
Write-Host "[2] Checking TCP Path..." -NoNewline
$tcp = Test-NetConnection -ComputerName $Target -Port $Port -InformationLevel Quiet
if ($tcp) {
    Write-Host " PASS " -ForegroundColor Green -NoNewline
    Write-Host "(Port $Port is OPEN)"
} else {
    Write-Host " FAIL " -ForegroundColor Red
    Write-Host "   -> ERROR: Port $Port blocked or server down. CHECK FIREWALL."
    exit
}

# 3. APP RESPONSE (The Smoking Gun)
Write-Host "[3] Checking App Response..." -NoNewline
try {
    # Using HTTPS and -SkipHttpErrorCheck (PowerShell 7 feature)
    $url = "https://$Target$URI"
    $req = Invoke-WebRequest -Uri $url -Method Head -SkipHttpErrorCheck
    
    # Check Status Code
    if ($req.StatusCode -eq 200) {
        Write-Host " PASS " -ForegroundColor Green
        Write-Host "   -> Status: 200 OK (App is working)"
    } elseif ($req.StatusCode -ge 500) {
        Write-Host " FAIL " -ForegroundColor Yellow
        Write-Host "   -> Status: $($req.StatusCode) (SERVER ERROR)"
        Write-Host "   -> PROOF: Network delivered packet, Server crashed." -ForegroundColor Yellow
    } else {
        Write-Host " WARN " -ForegroundColor Magenta
        Write-Host "   -> Status: $($req.StatusCode)"
    }
} catch {
    Write-Host " ERROR " -ForegroundColor Red
    Write-Host "   -> App layer failed completely (Possible Timeout or SSL Error)."
}

Write-Host "`n--------------------------------------------------" -ForegroundColor Gray
Write-Host "👉 COPY/PASTE THE ABOVE INTO YOUR TICKET" -ForegroundColor Cyan
