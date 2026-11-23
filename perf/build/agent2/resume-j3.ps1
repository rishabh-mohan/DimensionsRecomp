# Agent 2: 19:40 switch of the snapshot pre-build to -j3 on CPUs 0-3 (Agent 6's DXIL slot uses CPUs 4-11).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\resume-j3.ps1
# - If the -j10 build is running: kill the build-snap.ps1 tree.
# - If the SDK configure is still running: kill only the build-snap.ps1 PowerShell (no -j10 build can start),
#   let the configure finish, and check it wrote the build files.
# - Refresh the snapshot (S0d: picks up Agent 12's 19:27 logging/macros.h edit) while nothing compiles.
# - Then build-snap.ps1 -Phase sdk -SkipConfigure -Jobs 3 -Affinity F, then -Phase game -Jobs 3 -Affinity F.
param([string]$Tag = 'S0d')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
$log = "$R\build\agent2"
$steps = "$log\snap1-steps.txt"
function Note([string]$s) { "$(Get-Date -Format HH:mm:ss) NOTE  $s" | Out-File -Append -Encoding utf8 $steps; $s }
function Snap1Procs {
    Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID }
}
$all = Snap1Procs
$bs = @($all | Where-Object { $_.Name -match '^powershell' -and $_.CommandLine -match 'build-snap\.ps1' -and
        $_.CommandLine -notmatch 'snap\.py|resume-j3' })
$cfg = @($all | Where-Object { $_.Name -match '^cmake' -and $_.CommandLine -match '--preset' -and
         $_.CommandLine -match 'snap1-sdk' })
$bld = @($all | Where-Object { $_.Name -match '^cmake' -and $_.CommandLine -match '--build' -and
         $_.CommandLine -match 'snap1' })
if ($bld.Count -gt 0) {
    foreach ($p in $bs) { taskkill /T /F /PID $p.ProcessId 2>&1 | Out-Null }
    foreach ($p in $bld) { taskkill /T /F /PID $p.ProcessId 2>&1 | Out-Null }
    Note "stopped the running snapshot build tree (build-snap pids $(@($bs.ProcessId) -join ','))"
} elseif ($cfg.Count -gt 0) {
    foreach ($p in $bs) { taskkill /F /PID $p.ProcessId 2>&1 | Out-Null }
    Note "SDK configure still running; killed only build-snap.ps1 (pids $(@($bs.ProcessId) -join ',')) so no -j10 build starts"
    Start-Sleep -Seconds 2
    # race: if the configure ended just before the kill, a -j10 build may have started; stop it
    $late = @(Snap1Procs | Where-Object { $_.Name -match '^cmake' -and $_.CommandLine -match '--build' -and
              $_.CommandLine -match 'snap1' })
    foreach ($p in $late) { taskkill /T /F /PID $p.ProcessId 2>&1 | Out-Null; Note "killed late-started build $($p.ProcessId)" }
    while (Get-Process -Id $cfg[0].ProcessId -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }
} else {
    foreach ($p in $bs) { taskkill /T /F /PID $p.ProcessId 2>&1 | Out-Null }
    Note "no snapshot configure/build process found; build-snap pids killed: $(@($bs.ProcessId) -join ',')"
}
$ok = Select-String -Path "$log\snap1-sdk-configure.log" -Pattern 'Build files have been written' -SimpleMatch -Quiet
Note "SDK configure log has 'Build files have been written': $ok"
if (-not $ok) { Note 'SDK configure did not complete; stopping (exit 11)'; exit 11 }

$t0 = Get-Date
cmd /d /c "python build\agent2\snap.py $Tag > build\agent2\snap-$Tag.log 2>&1"
$se = $LASTEXITCODE
Note "snapshot $Tag exit=$se wall=$([Math]::Round(((Get-Date) - $t0).TotalSeconds, 1))s"
Get-Content "$log\snap-$Tag.log" -Tail 12
if ($se -ne 0) { exit 30 }

powershell -NoProfile -ExecutionPolicy Bypass -File "$log\build-snap.ps1" -Phase sdk -SkipConfigure -Jobs 3 -Affinity F
$c = $LASTEXITCODE
"build-snap sdk exit=$c"
if ($c -ne 0) { exit $c }
powershell -NoProfile -ExecutionPolicy Bypass -File "$log\build-snap.ps1" -Phase game -Jobs 3 -Affinity F
$c = $LASTEXITCODE
"build-snap game exit=$c"
exit $c
