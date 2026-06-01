#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Full release build: web_sota + PyInstaller sidecar + Tauri NSIS installer.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Version = "0.2.0"

Write-Host "=== bookmarks-mcp Tauri Release Build ===" -ForegroundColor Cyan

Write-Host "-> [1/5] Tauri icons..." -ForegroundColor Yellow
pwsh -NoLogo -File "$Root\scripts\generate-tauri-icon.ps1"
if ($LASTEXITCODE -ne 0) { throw "Tauri icon generation failed" }

Write-Host "-> [2/5] Building web_sota..." -ForegroundColor Yellow
Push-Location "$Root\web_sota"
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "web_sota build failed" }
} finally {
    Pop-Location
}

Write-Host "-> [3/5] PyInstaller sidecar..." -ForegroundColor Yellow
pwsh -NoLogo -File "$PSScriptRoot\build-sidecar.ps1"
if ($LASTEXITCODE -ne 0) { throw "Sidecar build failed" }

Write-Host "-> [4/5] Tauri bundle..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
try {
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install in native/ failed" }
    npx @tauri-apps/cli build
    if ($LASTEXITCODE -ne 0) { throw "tauri build failed" }
} finally {
    Pop-Location
}

Write-Host "-> [5/5] Copy installer to dist/..." -ForegroundColor Yellow
$nsis = Get-ChildItem "$PSScriptRoot\target\release\bundle\nsis\*-setup.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
$distDir = "$Root\dist"
New-Item -ItemType Directory -Path $distDir -Force | Out-Null
if ($nsis) {
    $releaseName = "bookmarks-mcp-v$Version-x64-setup.exe"
    $releasePath = Join-Path $distDir $releaseName
    Copy-Item $nsis.FullName $releasePath -Force
    $sizeMB = [math]::Round((Get-Item $releasePath).Length / 1MB, 1)
    Write-Host "=== Build complete ===" -ForegroundColor Green
    Write-Host "Installer: $releasePath ($sizeMB MB)" -ForegroundColor Cyan
} else {
    $msi = Get-ChildItem "$PSScriptRoot\target\release\bundle\msi\*.msi" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($msi) {
        Copy-Item $msi.FullName (Join-Path $distDir $msi.Name) -Force
        Write-Host "MSI: $($msi.FullName)" -ForegroundColor Cyan
    } else {
        Write-Host "Bundle output in $PSScriptRoot\target\release\bundle\" -ForegroundColor Yellow
    }
}
