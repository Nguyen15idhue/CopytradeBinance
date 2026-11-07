#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if ($env:RUN_LIVE -ne "1") {
    Write-Host "Bỏ qua smoke live. Đặt `$env:RUN_LIVE = '1' để gọi BAPI thật."
    exit 0
}

if (-not (Test-Path $python)) {
    throw "Không tìm thấy $python. Hãy tạo .venv và cài requirements."
}

Push-Location (Join-Path $root "backend")
try {
    & $python -m app.services.collector.smoke @args
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke BAPI thất bại với mã $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
