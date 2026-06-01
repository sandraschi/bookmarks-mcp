set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# Run Python tests
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -q

# Build web dashboard
webapp:
    Set-Location '{{justfile_directory()}}\web_sota'
    npm run build

# Start backend HTTP bridge (port 10803)
serve:
    Set-Location '{{justfile_directory()}}'
    $env:MCP_TRANSPORT = 'http'
    $env:MCP_PORT = '10803'
    $env:BOOKMARKS_WEB_AUTH = '0'
    uv run bookmarks-mcp

# Dev: backend + Vite (run in two terminals; this starts backend only)
dev-backend:
    just serve

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check
