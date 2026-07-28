# Per-repo fleet start config for bookmarks-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'bookmarks-mcp'
    BackendPort  = 10803
    FrontendPort = 10802
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\bookmarks-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'browser_bookmarks_tools.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10803' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
