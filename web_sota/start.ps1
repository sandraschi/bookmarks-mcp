param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$WebPort = 10802
$BackendPort = 10803
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly
Stop-FleetPortSquatters -Ports @($WebPort, $BackendPort) -Label "bookmarks-mcp"

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background)
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan

# Use TRIPLE backtick to ensure $env:PYTHONPATH reaches the REAL shell
$srcPath = Join-Path $ProjectRoot "src"
$backendCmd = "`$env:BOOKMARKS_WEB_AUTH = '0'; `$env:PYTHONPATH = '$srcPath;$PSScriptRoot'; Set-Location '$PSScriptRoot'; uv run uvicorn browser_bookmarks_tools.server:app --host 127.0.0.1 --port $BackendPort --log-level info"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Run server (Vite dev)
if (-not $FleetStart.RunFrontend) { return }

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if (-not $FleetStart.RunFrontend) { return }
npm run dev -- --port $WebPort --host






