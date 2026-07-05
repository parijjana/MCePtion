$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:UV_CACHE_DIR = Join-Path $Root ".uv-cache"

uv run mcp-hub --root . rescan
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
