#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$base = "http://localhost:8010/api/v1"

function Login {
    param([string]$Email, [string]$Password)
    $body = @{ email = $Email; password = $Password } | ConvertTo-Json
    return Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
        -ContentType "application/json; charset=utf-8" -Body $body
}

$admin = Login "admin@example.com" "Admin123!ChangeMe"
Write-Host "Đăng nhập admin: $($admin.data.user.email) / $($admin.data.user.role)"

$headers = @{ Authorization = "Bearer $($admin.data.access_token)" }
$me = Invoke-RestMethod -Method Get -Uri "$base/auth/me" -Headers $headers
Write-Host "Thông tin cá nhân: $($me.data.email) / $($me.data.role)"

$ping = Invoke-RestMethod -Method Get -Uri "$base/admin/ping" -Headers $headers
Write-Host "Admin ping: $($ping.data.admin)"

$refreshBody = @{ refresh_token = $admin.data.refresh_token } | ConvertTo-Json
$refreshed = Invoke-RestMethod -Method Post -Uri "$base/auth/refresh" `
    -ContentType "application/json; charset=utf-8" -Body $refreshBody
Write-Host "Refresh token: OK"

try {
    Invoke-RestMethod -Method Post -Uri "$base/auth/refresh" `
        -ContentType "application/json; charset=utf-8" -Body $refreshBody | Out-Null
    throw "Refresh token cũ vẫn dùng được — lỗi"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    if ($status -ne 401) { throw "Mong đợi 401 cho refresh cũ, nhận $status" }
    Write-Host "Refresh token cũ bị thu hồi: 401"
}

$viewer = Login "viewer@example.com" "Viewer123!ChangeMe"
Write-Host "Đăng nhập viewer: $($viewer.data.user.email) / $($viewer.data.user.role)"
$viewerHeaders = @{ Authorization = "Bearer $($viewer.data.access_token)" }

try {
    Invoke-RestMethod -Method Get -Uri "$base/admin/ping" -Headers $viewerHeaders | Out-Null
    throw "Viewer không bị chặn admin — lỗi"
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    if ($status -ne 403) { throw "Mong đợi 403, nhận $status" }
    Write-Host "Viewer bị chặn admin: 403"
}

Write-Host "Smoke test auth: PASS"
