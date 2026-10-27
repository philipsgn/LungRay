# scripts/verify.ps1 - Runner kiem thu tu dong hoa cho LungRay
$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "verify.py"

$pyExe = "python"
$py310 = "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
if (Test-Path $py310) {
    $pyExe = $py310
}

& $pyExe "$scriptPath"
exit $LASTEXITCODE
