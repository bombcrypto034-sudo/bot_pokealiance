param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"

python -m venv $VenvPath

$pythonExe = Join-Path $VenvPath "Scripts\\python.exe"

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Ambiente criado com sucesso."
Write-Host "Para ativar no PowerShell, rode:"
Write-Host ".\\$VenvPath\\Scripts\\Activate.ps1"
