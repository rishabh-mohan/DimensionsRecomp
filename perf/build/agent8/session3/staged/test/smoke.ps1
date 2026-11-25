# Smoke test of a sys-csv.ps1 driver against a harmless sleeping powershell (NOT a game). BelowNormal priority throughout.
# usage: powershell -NoProfile -File smoke.ps1 -Driver <sys-csv.ps1> -RunDir <dir> [-MaxSec 15] [-ProcEvery 1]
param([string]$Driver, [string]$RunDir, [string]$MaxSec = '15', [string]$ProcEvery = '')
$ErrorActionPreference = 'Stop'
$ws = '<workspace>'
if (Test-Path (Join-Path $ws 'perf-notes\WINDOW-HOLD.txt')) { 'WINDOW-HOLD present: abort'; exit 3 }
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
[void][IO.Directory]::CreateDirectory($RunDir)
$sl = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList '-NoProfile', '-Command', 'Start-Sleep 30' -WindowStyle Hidden -PassThru
"sleeper pid $($sl.Id)"
$a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Driver, '-GamePid', [string]$sl.Id, '-RunDir', $RunDir, '-MaxSec', $MaxSec)
if ($ProcEvery) { $a += @('-ProcEvery', $ProcEvery) }
$line = ($a | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
$d = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $line -NoNewWindow -PassThru -Wait `
    -RedirectStandardOutput (Join-Path $RunDir 'sys.out.txt') -RedirectStandardError (Join-Path $RunDir 'sys.err.txt')
"driver exit $($d.ExitCode)"
if (-not $sl.HasExited) { $sl.Kill() }   # only the sleeper this script started
Get-Content (Join-Path $RunDir 'sys.out.txt')
'--- stderr:'; Get-Content (Join-Path $RunDir 'sys.err.txt')
