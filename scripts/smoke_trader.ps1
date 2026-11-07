#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$base = "http://localhost:8010/api/v1"
$loginBody = @{ email = "admin@example.com"; password = "Admin123!ChangeMe" } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
    -ContentType "application/json; charset=utf-8" -Body $loginBody
$headers = @{ Authorization = "Bearer $($login.data.access_token)" }

function Get-Metric {
    param($Data, [string]$Key)
    return $Data.data.metrics | Where-Object { $_.key -eq $Key }
}

$qualifiedList = Invoke-RestMethod -Method Get `
    -Uri "$base/universe/traders?tier=qualified&page_size=1" -Headers $headers
if (-not $qualifiedList.data.items -or $qualifiedList.data.items.Count -eq 0) {
    throw "Không tìm thấy trader qualified trong universe"
}
$qualifiedId = $qualifiedList.data.items[0].id
$qualified = Invoke-RestMethod -Method Get -Uri "$base/traders/$qualifiedId" -Headers $headers
if (-not $qualified.data.tier) { throw "Thiếu tier của trader qualified" }
if ($qualified.data.metrics.Count -ne 10) { throw "Không đủ 10 chỉ số" }
$mdd = Get-Metric $qualified "mdd_90d"
$sharpe = Get-Metric $qualified "sharpe"
Write-Host "Trader qualified: id=$qualifiedId, tier=$($qualified.data.tier), 10 chỉ số, MDD=$($mdd.value), Sharpe=$($sharpe.value)"

$excludedList = Invoke-RestMethod -Method Get `
    -Uri "$base/universe/traders?tier=excluded&page_size=1" -Headers $headers
if (-not $excludedList.data.items -or $excludedList.data.items.Count -eq 0) {
    throw "Không tìm thấy trader excluded trong universe"
}
$excludedId = $excludedList.data.items[0].id
$excluded = Invoke-RestMethod -Method Get -Uri "$base/traders/$excludedId" -Headers $headers
if ($excluded.data.tier -ne "excluded") { throw "Tier excluded không đúng" }
if (-not $excluded.data.reasons -or $excluded.data.reasons.Count -eq 0) {
    throw "Trader excluded phải có lý do loại"
}
Write-Host "Trader excluded: id=$excludedId, reasons=$($excluded.data.reasons -join ',')"

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
