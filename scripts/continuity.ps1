[CmdletBinding()]
param(
    [ValidateSet('Start', 'Status', 'Stop', 'Logs', 'Install', 'Uninstall')]
    [string]$Action = 'Status'
)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $workspace 'venv\Scripts\python.exe'
$stateDirectory = Join-Path $workspace '.uninav-continuity'
$taskName = 'UniNav-Codex-Continuity'
$taskArguments = '-m scripts.codex_continuity run'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python environment not found: $pythonPath"
}

function Install-ContinuityTask {
    $taskAction = New-ScheduledTaskAction -Execute $pythonPath -Argument $taskArguments -WorkingDirectory $workspace
    $logon = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
    $watchdog = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 5)
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger @($logon, $watchdog) -Settings $settings -Principal $principal -Description 'Resume the authorized UniNav Codex worker after quota resets and recover its supervisor after login or process failure.' -Force | Out-Null
}

switch ($Action) {
    'Install' {
        Install-ContinuityTask
        Write-Output "Installed task: $taskName. Use Start to enable project work."
    }
    'Start' {
        $statePath = Join-Path $stateDirectory 'state.json'
        if (Test-Path -LiteralPath $statePath) {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($state.status -eq 'complete') {
                Write-Output 'All work is already marked complete. Review the recorded evidence before starting a new objective.'
                break
            }
        }
        if (-not (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
            Install-ContinuityTask
        }
        & $pythonPath -m scripts.codex_continuity enable
        if ($LASTEXITCODE -ne 0) { throw 'Could not enable continuity.' }
        Start-ScheduledTask -TaskName $taskName
        Write-Output "Started $taskName. Local status: $stateDirectory\state.json"
    }
    'Status' {
        & $pythonPath -m scripts.codex_continuity status
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $taskName
            $info | Select-Object TaskName, LastRunTime, LastTaskResult, NextRunTime
            Write-Output "Scheduled task state: $($task.State)"
        }
    }
    'Stop' {
        & $pythonPath -m scripts.codex_continuity stop
    }
    'Logs' {
        $logPath = Join-Path $stateDirectory 'supervisor.log'
        if (Test-Path -LiteralPath $logPath) {
            Get-Content -LiteralPath $logPath -Tail 30 -Wait -Encoding UTF8
        } else {
            Write-Output 'No continuity log exists yet.'
        }
    }
    'Uninstall' {
        & $pythonPath -m scripts.codex_continuity stop
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Output 'Removed the Windows task. Checkpoints and logs remain available.'
    }
}
