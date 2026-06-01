# Build Tauri desktop app (requires Rust + Tauri CLI)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Building web_sota..."
Set-Location ..\web_sota
npm run build
Set-Location ..\native

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "Rust/cargo not found — install from https://rustup.rs"
    exit 1
}

cargo tauri build
