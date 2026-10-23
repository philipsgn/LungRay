# scripts/verify.ps1 - Runner kiem thu tu dong hoa cho LungRay
$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "verify.py"

python $scriptPath
exit $LASTEXITCODE
