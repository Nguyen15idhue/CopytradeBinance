#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($env:RUN_LIVE -ne "1") {
    Write-Host "Bỏ qua smoke collector. Đặt `$env:RUN_LIVE = '1' để chạy thật."
    exit 0
}

$base = "http://localhost:8000/api/v1"
$loginBody = @{ email = "admin@example.com"; password = "Admin123!ChangeMe" } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
    -ContentType "application/json; charset=utf-8" -Body $loginBody
$headers = @{ Authorization = "Bearer $($login.data.access_token)" }

$status = Invoke-RestMethod -Method Get -Uri "$base/collector/status" -Headers $headers
Write-Host "Collector bật: $($status.data.enabled)"
Write-Host "Tier: $($status.data.tiers | ConvertTo-Json -Compress)"
Write-Host "Raw archive: $($status.data.raw_archive.files) file / $($status.data.raw_archive.bytes) byte"

$run = Invoke-RestMethod -Method Post -Uri "$base/collector/run-scan" -Headers $headers
$jobId = $run.data.job_id
Write-Host "Đã tạo job scan: $jobId"

$final = $null
for ($i = 1; $i -le 60; $i++) {
    Start-Sleep -Seconds 5
    $job = Invoke-RestMethod -Method Get -Uri "$base/collector/jobs/$jobId" -Headers $headers
    if ($job.data.status -ne "running") {
        $final = $job.data
        Write-Host "Lần kiểm tra ${i}: trạng thái $($final.status)"
        break
    }
    Write-Host "Lần kiểm tra ${i}: đang chạy"
}

if ($null -eq $final) {
    throw "Job scan không kết thúc trong 5 phút"
}
if ($final.status -ne "success") {
    throw "Job scan kết thúc với trạng thái $($final.status): $($final.error)"
}

$scan = $final.result.scan
Write-Host "Scan xong: total=$($scan.total), pages=$($scan.pages), lỗi=$($scan.errors.Count), giây=$($scan.duration_seconds)"
Write-Host "Smoke collector: PASS"
