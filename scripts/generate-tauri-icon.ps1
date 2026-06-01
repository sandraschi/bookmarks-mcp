#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$iconDir = Join-Path $Root "native\icons"
$src = Join-Path $Root "assets\icon.png"
$out = Join-Path $iconDir "icon.png"

if (-not (Test-Path $src)) {
    Write-Host "-> Generating default icon..." -ForegroundColor Yellow
    uv run python (Join-Path $Root "scripts\generate-icon.py")
}

New-Item -ItemType Directory -Path $iconDir -Force | Out-Null
Copy-Item $src $out -Force
Write-Host "Copied icon to $out" -ForegroundColor Green

Push-Location (Join-Path $Root "native")
try {
    npx --yes @tauri-apps/cli icon icons/icon.png
    if ($LASTEXITCODE -ne 0) { throw "tauri icon failed" }
} finally {
    Pop-Location
}
