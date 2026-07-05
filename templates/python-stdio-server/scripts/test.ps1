$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

uv run python -m unittest discover -s tests -p "test*.py"
