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
