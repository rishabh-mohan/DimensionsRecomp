# run_gates.ps1 - Agent 12, task #15 (2026-11-22): thin wrapper for run_gates.py, same arguments.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\run_gates.ps1 <matrix out dir> [run_gates.py options]
# Stops with exit 4 while perf-notes\WINDOW-HOLD.txt exists (a timed window is running), unless -Force is given.
# Runs python at Below Normal priority (run_gates.py also lowers itself). The exit code is run_gates.py's:
# 0 pass, 1 a FAIL, 3 CHECK/PENDING/NO DATA/NOT RECORDED/NO WINDOW/PARTIAL/ERROR, 2 usage, 4 HOLD, 5 --expect mismatch,
# 6 the kit itself failed (traceback). -Force or --force runs it while the HOLD file exists.
# No param() block on purpose: arguments like --gate-log pass through to python unchanged.
$force = $false
$rest = @()
foreach ($x in $args) { if ("$x" -ieq '-Force' -or "$x" -ieq '--force') { $force = $true } else { $rest += "$x" } }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
if (-not $force -and (Test-Path (Join-Path $repo 'perf-notes\WINDOW-HOLD.txt'))) {
    Write-Host 'perf-notes\WINDOW-HOLD.txt exists: a timed window is running; not starting (use -Force after it ends).'
    exit 4
}
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Host 'python not found on PATH'; exit 2 }
if ($force) { $rest += '--force' }
$script = Join-Path $PSScriptRoot 'run_gates.py'
$p = Start-Process -FilePath $py.Source -ArgumentList (@('-B', "`"$script`"") + ($rest | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } })) -NoNewWindow -PassThru
$null = $p.Handle  # cache the handle now, or ExitCode can come back empty after -NoNewWindow -PassThru
try { $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal } catch { }
$p.WaitForExit()
exit $p.ExitCode
