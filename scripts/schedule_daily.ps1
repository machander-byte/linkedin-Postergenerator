Param(
  [string]$At = "08:30",
  [string]$TaskName = "news2linkedin-daily",
  [switch]$Remove
)

$ErrorActionPreference = 'Stop'

$ScriptPath = Join-Path $PSScriptRoot 'run_main.ps1'
if (-not (Test-Path $ScriptPath)) { throw "run_main.ps1 not found at $ScriptPath" }

if ($Remove) {
  Write-Host "Removing scheduled task: $TaskName"
  schtasks /Delete /TN "$TaskName" /F | Out-Null
  Write-Host "Removed $TaskName"
  exit 0
}

# Validate time format HH:mm
try {
  [void][DateTime]::ParseExact($At, 'HH:mm', $null)
} catch {
  throw "Invalid -At time '$At'. Use HH:mm (e.g., 09:00)"
}

# Command for scheduler
$Cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

Write-Host "Creating/updating daily task '$TaskName' at $At"
schtasks /Create /F /SC DAILY /ST $At /TN "$TaskName" /TR "$Cmd" | Out-Null
Write-Host "Scheduled. It will run daily at $At."
Write-Host "Tip: Ensure .env is configured and venv exists."
