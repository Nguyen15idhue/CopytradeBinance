#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$base = "http://localhost:8010/api/v1"
$body = @{ email = "admin@example.com"; password = "sai-mat-khau" } | ConvertTo-Json

$lastStatus = 0
for ($i = 1; $i -le 6; $i++) {
    try {
        Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
            -ContentType "application/json; charset=utf-8" -Body $body | Out-Null
        $lastStatus = 200
        Write-Host "Lần ${i}: 200 (không mong đợi)"
    } catch {
        $lastStatus = $_.Exception.Response.StatusCode.value__
        Write-Host "Lần ${i}: $lastStatus"
    }
}

if ($lastStatus -ne 429) {
    throw "Mong đợi lần thứ 6 bị 429, nhận $lastStatus"
}
Write-Host "Rate limit login: PASS (429 ở lần 6)"
