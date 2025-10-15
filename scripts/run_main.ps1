Param(
  [switch]$VerboseLogging,
  [switch]$Live
)

$ErrorActionPreference = 'Stop'

# Resolve project root (news2linkedin directory)
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

# Python executable (prefer venv)
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
  $Python = $VenvPython
} else {
  $Python = (Get-Command py -ErrorAction SilentlyContinue)?.Source
  if (-not $Python) { $Python = (Get-Command python -ErrorAction SilentlyContinue)?.Source }
}
if (-not $Python) { throw "Python not found. Create venv or install Python." }

# Logs
$LogDir = Join-Path $ProjectRoot 'logs'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogPath = Join-Path $LogDir "run_$ts.log"

Write-Host "Running: $Python -m src.main"
Write-Host "Logging to: $LogPath"
if ($Live) {
  Write-Host "Live mode: DRY_RUN=false"
  $env:DRY_RUN = 'false'
}

if ($VerboseLogging) { $env:PYTHONWARNINGS = 'default' }

& $Python -m src.main 2>&1 | Tee-Object -FilePath $LogPath

if ($LASTEXITCODE -ne 0) {
  Write-Error "Run failed with exit code $LASTEXITCODE. See log: $LogPath"
  exit $LASTEXITCODE
}

Write-Host "Done. Log: $LogPath"
