# Activates a reviewed campus profile on the real database (uninav-campus.db) and restarts the campus service.
#   powershell -ExecutionPolicy Bypass -File scripts\activate_campus.ps1                 # six floors (ucc-six-floors-c18) on port 8001
#   powershell -ExecutionPolicy Bypass -File scripts\activate_campus.ps1 -Restore backups\<file>.db   # roll back
# 1. Stops only the scripts.run_campus process serving the port (refuses if another program serves it).
# 2. Copies the database to backups\ before changing it (or restores the given backup).
# 3. Starts scripts.run_campus detached, logging to logs\, and waits for /health.
# 4. Prints the number of places served. The upgrade keeps users, history and IDs; going back to an older profile is
#    refused by the launcher, so a rollback restores the backup and starts without --profile.
param([string]$CampusProfile = "ucc-six-floors-c18", [int]$Port = 8001, [string]$Restore = "")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$db = Join-Path $root "uninav-campus.db"
$python = Join-Path $root "venv\Scripts\python.exe"

foreach ($c in @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($c.OwningProcess)"
  if ($proc.CommandLine -notmatch "scripts\.run_campus") { throw "Port $Port is served by another program: $($proc.CommandLine)" }
  $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)" -ErrorAction SilentlyContinue
  $target = if ($parent -and $parent.CommandLine -match "scripts\.run_campus") { $parent.ProcessId } else { $proc.ProcessId }
  taskkill /PID $target /T /F | Out-Null
}
Start-Sleep -Seconds 1

New-Item -ItemType Directory -Force (Join-Path $root "backups") | Out-Null
if ($Restore) {
  Copy-Item (Resolve-Path $Restore) $db -Force
  $arguments = @("-m", "scripts.run_campus", "--port", "$Port")
  "Restored $Restore"
} else {
  $backup = Join-Path $root ("backups\uninav-campus-{0}-before-{1}.db" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $CampusProfile)
  Copy-Item $db $backup
  $arguments = @("-m", "scripts.run_campus", "--port", "$Port", "--profile", $CampusProfile)
  "Backup: $backup"
}

New-Item -ItemType Directory -Force (Join-Path $root "logs") | Out-Null
$p = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput (Join-Path $root "logs\campus-$Port.out.log") -RedirectStandardError (Join-Path $root "logs\campus-$Port.err.log")
$ready = $false
for ($i = 0; $i -lt 60 -and -not $ready; $i++) {
  try { Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2 | Out-Null; $ready = $true } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) { throw "The campus service did not start. See logs\campus-$Port.err.log" }
# Windows PowerShell 5.1 returns a JSON array as one pipeline object, so count the array itself.
$response = Invoke-RestMethod "http://127.0.0.1:$Port/buildings"
$places = $response.Count
"UniNav campus on http://127.0.0.1:$Port/ (PID $($p.Id)): $places places"
