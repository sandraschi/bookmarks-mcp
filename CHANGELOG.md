
## [Unreleased] — 2026-06-14

### Added
- Tauri CORS: 	auri://localhost, http://tauri.localhost, https://tauri.localhost in CORS origins
- Tauri CORS: _TAURI env var toggle with llow_origin_regex for secure WebView access
- build.ps1: auto-copy NSIS installer to dist/ on build
- CUA-NSIS: config-driven smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- CUA-NSIS: `just build-native` + `just cua-nsis-test` recipes
- CUA-NSIS: 11-phase smoke (install, launch, WebView OCR, feature route, diagnostics, uninstall)
- CUA-NSIS: local certification — all 11 phases pass locally (2026-06-14)

### Changed
- CORS: llow_origins=["*"] → explicit origins list for Tauri webview compatibility
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepa-changelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **MCP Module Entry Point**: Added `__main__.py` to enable `python -m browser_bookmarks_tools` execution
- **Documentation**: Comprehensive README and MCP configuration guide

## [0.1.0] - 2025-12-11

### Added
- Initial FastMCP 2.13 compliant implementation
- Firefox bookmark support (SQLite)
- Chrome/Edge/Brave bookmark support (JSON)
- Safari bookmark support (plist) - macOS only
- Unified portmanteau tool interface
- AI-powered bookmark analysis and tagging
- Cross-browser synchronization
- CRUD operations for bookmarks
- Automatic organization and duplicate detection
- Smart tagging and summarization features

### Technical
- FastMCP 2.13 framework
- Async/await architecture
- Browser-specific implementations
- Modular design with separate AI and bookmark management components
- Comprehensive test suite

