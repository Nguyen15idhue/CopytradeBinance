#requires -Version 5.1
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $envPath = Join-Path $root ".env"
    if (-not (Test-Path $envPath)) {
        throw "Không tìm thấy .env"
    }

    $values = @{}
    foreach ($line in Get-Content $envPath -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed -and -not $trimmed.StartsWith("#") -and $trimmed.Contains("=")) {
            $parts = $trimmed.Split("=", 2)
            $values[$parts[0].Trim()] = $parts[1].Trim()
        }
    }

    $dbUser = if ($values.ContainsKey("POSTGRES_USER")) { $values["POSTGRES_USER"] } else { "copytrade" }
    $dbName = if ($values.ContainsKey("POSTGRES_DB")) { $values["POSTGRES_DB"] } else { "copytrade" }
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $backupDir = Join-Path $root "backups"
    $dumpPath = Join-Path $backupDir "db-$stamp.dump"
    $envBackup = Join-Path $backupDir "env-$stamp.bak"

    if ($DryRun) {
        Write-Host "[DryRun] Sẽ tạo $dumpPath"
        Write-Host "[DryRun] Sẽ copy .env -> $envBackup"
        Write-Host "[DryRun] Sẽ xóa file backup cũ hơn 7 ngày"
        exit 0
    }

    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

    $command = "docker compose exec -T db pg_dump -Fc -U $dbUser -d $dbName > `"$dumpPath`""
    Write-Host "Đang backup database..."
    cmd.exe /c $command
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump thất bại với mã $LASTEXITCODE"
    }

    Copy-Item -Path $envPath -Destination $envBackup -Force
    Get-ChildItem -Path $backupDir -Filter "db-*.dump" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
        Remove-Item -Force
    Get-ChildItem -Path $backupDir -Filter "env-*.bak" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
        Remove-Item -Force

    Write-Host "Backup xong: $dumpPath"
} finally {
    Pop-Location
}
