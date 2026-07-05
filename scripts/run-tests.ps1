$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:UV_CACHE_DIR = Join-Path $Root ".uv-cache"

uv run python -m unittest discover -s tests -p "test*.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
