#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build a lean MCPB bundle for Claude Desktop (fleet staging standard).

.DESCRIPTION
    Stages only runtime files (src/, manifest.json, requirements.txt, README.md)
    into mcpb-build/, validates, packs, and fails if the bundle is oversized.
    Never packs .venv, node_modules, native/, or web_sota/.
#>
param(
    [string]$OutputDir = "dist",
    [switch]$KeepStaging
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PackageName = "bookmarks-mcp"
$Version = "0.2.0"
$BuildDir = Join-Path $ProjectRoot "mcpb-build"
$DistDir = Join-Path $ProjectRoot $OutputDir
$SrcPackage = "browser_bookmarks_tools"
$MaxSizeMB = 25

function Ensure-McpbCli {
    $mcpbCmd = Get-Command mcpb -ErrorAction SilentlyContinue
    if ($mcpbCmd) {
        return $mcpbCmd.Source
    }
    Write-Host "-> Installing MCPB CLI..." -ForegroundColor Yellow
    npm install -g @anthropic-ai/mcpb 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "MCPB CLI install failed" }
    $mcpbCmd = Get-Command mcpb -ErrorAction SilentlyContinue
    if (-not $mcpbCmd) {
        $npmGlobal = npm prefix -g 2>$null
        $mcpbExe = Join-Path $npmGlobal "mcpb.cmd"
        if (-not (Test-Path $mcpbExe)) { throw "mcpb not found after install: $mcpbExe" }
        return $mcpbExe
    }
    return $mcpbCmd.Source
}

function Copy-SourceTree {
    param(
        [string]$Source,
        [string]$Destination
    )
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $robocopyArgs = @(
        $Source,
        $Destination,
        "/E",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS",
        "/XD", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
        "/XF", "*.pyc", "*.pyo", "*.bak"
    )
    & robocopy @robocopyArgs | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "Failed copying source from $Source to $Destination (robocopy exit $LASTEXITCODE)"
    }
}

function Copy-PromptAssets {
    param([string]$DestinationRoot)
    $assetsSrc = Join-Path $ProjectRoot "assets"
    if (-not (Test-Path $assetsSrc)) {
        throw "Missing assets/ directory (required: assets/prompts/system.md, user.md, examples.json)"
    }
    $required = @(
        "prompts\system.md",
        "prompts\user.md",
        "prompts\examples.json"
    )
    foreach ($rel in $required) {
        $full = Join-Path $assetsSrc $rel
        if (-not (Test-Path $full)) {
            throw "Missing required MCPB prompt asset: assets/$($rel -replace '\\','/')"
        }
    }
    # Fleet layout: assets/prompts/*
    Copy-SourceTree -Source $assetsSrc -Destination (Join-Path $DestinationRoot "assets")
    # MCPB manifest paths: prompts/* (fastsearch fleet pattern)
    Copy-SourceTree -Source (Join-Path $assetsSrc "prompts") -Destination (Join-Path $DestinationRoot "prompts")
}

function Assert-StagingPrompts {
    param([string]$StagingRoot)
    $mustExist = @(
        (Join-Path $StagingRoot "prompts\system.md"),
        (Join-Path $StagingRoot "prompts\user.md"),
        (Join-Path $StagingRoot "prompts\examples.json"),
        (Join-Path $StagingRoot "assets\prompts\examples.json")
    )
    foreach ($path in $mustExist) {
        if (-not (Test-Path $path)) {
            throw "Staging missing required prompt file: $path"
        }
    }
}

Write-Host "=== bookmarks-mcp MCPB build (staging) ===" -ForegroundColor Cyan
$mcpbExe = Ensure-McpbCli

if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}
New-Item -ItemType Directory -Path (Join-Path $BuildDir "src") -Force | Out-Null
New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

Copy-SourceTree `
    -Source (Join-Path $ProjectRoot "src\$SrcPackage") `
    -Destination (Join-Path $BuildDir "src\$SrcPackage")

Copy-PromptAssets -DestinationRoot $BuildDir

Copy-Item (Join-Path $ProjectRoot "manifest.json") (Join-Path $BuildDir "manifest.json") -Force
if (Test-Path (Join-Path $ProjectRoot "README.md")) {
    Copy-Item (Join-Path $ProjectRoot "README.md") (Join-Path $BuildDir "README.md") -Force
}
if (Test-Path (Join-Path $ProjectRoot "CHANGELOG.md")) {
    Copy-Item (Join-Path $ProjectRoot "CHANGELOG.md") (Join-Path $BuildDir "CHANGELOG.md") -Force
}

$requirements = @"
fastmcp>=3.3.0
prefab-ui>=0.18.0
pydantic>=2.7
aiohttp>=3.9
aiosqlite>=0.20
httpx>=0.27
requests>=2.31.0
beautifulsoup4>=4.12.0
psutil>=5.9.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
"@
$requirements | Out-File -FilePath (Join-Path $BuildDir "requirements.txt") -Encoding utf8NoBOM

Assert-StagingPrompts -StagingRoot $BuildDir

Push-Location $BuildDir
try {
    & $mcpbExe validate manifest.json
    if ($LASTEXITCODE -ne 0) { throw "manifest validation failed" }
} finally {
    Pop-Location
}

$OutputFile = Join-Path $DistDir "$PackageName-v$Version.mcpb"
if (Test-Path $OutputFile) {
    Remove-Item $OutputFile -Force -ErrorAction SilentlyContinue
}

& $mcpbExe pack $BuildDir $OutputFile
if ($LASTEXITCODE -ne 0) { throw "mcpb pack failed" }
if (-not (Test-Path $OutputFile)) { throw "MCPB output missing: $OutputFile" }

$sizeMB = [math]::Round((Get-Item $OutputFile).Length / 1MB, 2)
if ($sizeMB -gt $MaxSizeMB) {
    throw "MCPB bundle is ${sizeMB} MB (limit ${MaxSizeMB} MB) - check staging excludes"
}

Write-Host "=== MCPB ready ===" -ForegroundColor Green
Write-Host "  $OutputFile ($sizeMB MB)" -ForegroundColor Cyan

if (-not $KeepStaging) {
    Remove-Item -Recurse -Force $BuildDir
}
