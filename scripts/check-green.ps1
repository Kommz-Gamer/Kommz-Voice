param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [Parameter(Mandatory = $false)]
    [string]$LicenseKey = "VCV-TEST-INVALID-KEY",
    [Parameter(Mandatory = $false)]
    [int]$TimeoutSec = 20
)

$ErrorActionPreference = "Stop"

function Invoke-JsonPost {
    param(
        [string]$Url,
        [hashtable]$Body
    )
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Post -Body ($Body | ConvertTo-Json -Depth 6) -ContentType "application/json" -TimeoutSec $TimeoutSec
        return @{ ok = $true; body = $response; status = 200 }
    } catch {
        $status = 0
        try { $status = [int]$_.Exception.Response.StatusCode.value__ } catch {}
        return @{ ok = $false; body = $_.Exception.Message; status = $status }
    }
}

$base = $BaseUrl.TrimEnd("/")
$results = @()

Write-Host "Checking GREEN environment: $base"

# 1) health
try {
    $health = Invoke-RestMethod -Uri "$base/health" -Method Get -TimeoutSec $TimeoutSec
    $results += [pscustomobject]@{ Check = "GET /health"; Ok = $true; Detail = ($health | ConvertTo-Json -Compress) }
} catch {
    $results += [pscustomobject]@{ Check = "GET /health"; Ok = $false; Detail = $_.Exception.Message }
}

# 2) license verification smoke test
$lic = Invoke-JsonPost -Url "$base/license/voice/verify-web" -Body @{ license_key = $LicenseKey }
$results += [pscustomobject]@{
    Check = "POST /license/voice/verify-web"
    Ok = ($lic.status -in 200, 400)
    Detail = "HTTP=$($lic.status) body=$($lic.body | ConvertTo-Json -Compress)"
}

# 3) me endpoint should return 401 or 200, but never 5xx
try {
    $meResp = Invoke-WebRequest -Uri "$base/me" -Method Get -TimeoutSec $TimeoutSec
    $status = [int]$meResp.StatusCode
    $ok = $status -in 200, 401
    $results += [pscustomobject]@{ Check = "GET /me"; Ok = $ok; Detail = "HTTP=$status" }
} catch {
    $status = 0
    try { $status = [int]$_.Exception.Response.StatusCode.value__ } catch {}
    $ok = $status -in 200, 401
    $results += [pscustomobject]@{ Check = "GET /me"; Ok = $ok; Detail = "HTTP=$status msg=$($_.Exception.Message)" }
}

$results | Format-Table -AutoSize

$failed = $results | Where-Object { $_.Ok -eq $false }
if ($failed.Count -gt 0) {
    Write-Error "GO/NO-GO: NO-GO ($($failed.Count) check(s) failed)."
    exit 1
}

Write-Host "GO/NO-GO: GO (all automated checks passed)." -ForegroundColor Green
