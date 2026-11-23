# Fake matrix driver for run_selftest.ps1 section (d). It checks that run-timing.ps1 starts an arm's driver during
# the window with -GamePid/-RunDir plus the arm's args. It writes <RunDir>\driver-ran.txt, sleeps 1.5 s and exits 0.
param([int]$GamePid = 0, [string]$RunDir = '', [string]$Mode = '')
$alive = [bool](Get-Process -Id $GamePid -ErrorAction SilentlyContinue)
"pid=$GamePid alive=$alive mode=$Mode rest=$($args -join ' ') at=$(Get-Date -Format o)" |
    Set-Content -LiteralPath (Join-Path $RunDir 'driver-ran.txt') -Encoding ascii
Start-Sleep -Milliseconds 1500
exit 0
