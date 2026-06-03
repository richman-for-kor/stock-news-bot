$TaskName   = "MingdongStockNewsBot"
$PythonPath = (Get-Command python).Source
$ScriptPath = "$PSScriptRoot\main.py"
$WorkDir    = $PSScriptRoot

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$Action  = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $WorkDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Trigger.Delay = "PT1M"
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Mingdong Stock News Bot"

Write-Host "OK: $TaskName registered" -ForegroundColor Green
