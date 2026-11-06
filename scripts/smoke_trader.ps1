#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$base = "http://localhost:8000/api/v1"
$loginBody = @{ email = "admin@example.com"; password = "Admin123!ChangeMe" } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
    -ContentType "application/json; charset=utf-8" -Body $loginBody
$headers = @{ Authorization = "Bearer $($login.data.access_token)" }

function Get-Metric {
    param($Data, [string]$Key)
    return $Data.data.metrics | Where-Object { $_.key -eq $Key }
}

$qualifiedId = "4520644381136785152"
$qualified = Invoke-RestMethod -Method Get -Uri "$base/traders/$qualifiedId" -Headers $headers
if ($qualified.data.tier -ne "qualified") { throw "Tier qualified không đúng" }
if ($qualified.data.metrics.Count -ne 10) { throw "Không đủ 10 chỉ số" }
$mdd = Get-Metric $qualified "mdd_90d"
$sharpe = Get-Metric $qualified "sharpe"
if ([math]::Abs([double]$mdd.value - 8.5435368) -gt 0.0001) { throw "MDD qualified sai" }
if ([math]::Abs([double]$sharpe.value - 2.83745888) -gt 0.0001) { throw "Sharpe qualified sai" }
Write-Host "Trader qualified: tier=$($qualified.data.tier), 10 chỉ số, MDD=$($mdd.value), Sharpe=$($sharpe.value)"

$excludedId = "5296057151807357697"
$excluded = Invoke-RestMethod -Method Get -Uri "$base/traders/$excludedId" -Headers $headers
if ($excluded.data.tier -ne "excluded") { throw "Tier excluded không đúng" }
if ($excluded.data.reasons -notcontains "runtime_lt_30") { throw "Thiếu reason runtime_lt_30" }
$exMdd = Get-Metric $excluded "mdd_90d"
$exSharpe = Get-Metric $excluded "sharpe"
if ($null -ne $exMdd.value) { throw "MDD excluded phải là null" }
if ($null -ne $exSharpe.value) { throw "Sharpe excluded phải là null" }
if ($excluded.data.flags -notcontains "missing_sharpe") { throw "Thiếu flag missing_sharpe" }
Write-Host "Trader excluded: tier=$($excluded.data.tier), reasons=$($excluded.data.reasons -join ','), MDD=null, Sharpe=null"

try {
    Invoke-RestMethod -Method Get -Uri "$base/traders/khong-ton-tai" -Headers $headers | Out-Null
    throw "Trader không tồn tại không trả 404"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    if ($status -ne 404) { throw "Mong đợi 404, nhận $status" }
    if ($_.ErrorDetails.Message -notmatch "TRADER_NOT_FOUND") { throw "Thiếu mã TRADER_NOT_FOUND" }
    Write-Host "Trader không tồn tại: 404 TRADER_NOT_FOUND"
}

try {
    Invoke-RestMethod -Method Get -Uri "$base/traders/$qualifiedId" | Out-Null
    throw "Thiếu token không trả 401"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    if ($status -ne 401) { throw "Mong đợi 401, nhận $status" }
    Write-Host "Không có token: 401"
}

Write-Host "Smoke test trader detail: PASS"
