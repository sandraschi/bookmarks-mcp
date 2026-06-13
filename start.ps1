Param([switch]$Headless)
$SkipFrontend = $Headless

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'
# browser-bookmarks-tools Start - Standards-Compliant SOTA
Write-Host 'Starting browser-bookmarks-tools...' -ForegroundColor Cyan

Set-Location $PSScriptRoot
Write-Host 'Starting Standardized Fullstack Hybrid...' -ForegroundColor Green
# Launch backend Hidden by default to prevent console spam
Start-Process pwsh -ArgumentList '-NoProfile', '-Command', 'uv run -m browser_bookmarks_tools' -WindowStyle Hidden
Set-Location web_sota
if ($SkipFrontend) { return }
npm run dev
