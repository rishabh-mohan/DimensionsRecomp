# Agent 2: stop the snapshot builds (build-snap.ps1, the run-s2.ps1 / run-b.ps1 drivers, prep-b.py) and everything
# under them, without touching other agents' work.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\stop-snap.ps1
# 1) taskkill /T the driver PowerShell / python processes (tree: cmd -> cmake --build -> ninja -> clang/lld/...,
#    robocopy),
# 2) then anything left whose command line names build/agent2/snap1* or build/agent2/snapB* (orphans), excluding this
#    process. (23:40: run-b.ps1, prep-b.py and snapB added for Agent 9's codegen build B; 02:15: the b-chain.ps1
#    driver and run-s3.ps1; 02:59: run-s3d.ps1, the native3d driver; 03:25: task #14's rb-chain.ps1, run-rb1.ps1,
#    run-rb2.ps1, prep-rb1.py, prep-rb2.py, run-nb.ps1 and prep-nb.py; their trees build/agent2/snapB3* match the
#    orphan pattern already.)
$me = $PID
$drivers = 'build-snap\.ps1|run-s2\.ps1|run-s3\.ps1|run-s3d\.ps1|run-b\.ps1|prep-b\.py|b-chain\.ps1|rb-chain\.ps1|run-rb\d\.ps1|prep-rb\d\.py|run-nb\.ps1|prep-nb\.py'
$ps = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $me -and $_.Name -match '^(powershell|python)' -and $_.CommandLine -match $drivers -and
    $_.CommandLine -notmatch 'snap\.py' -and $_.CommandLine -notmatch 'stop-snap\.ps1' }
foreach ($p in $ps) {
    "kill tree $($p.ProcessId): $($p.CommandLine)"
    taskkill /T /F /PID $p.ProcessId 2>&1 | Measure-Object -Line | ForEach-Object { "  taskkill lines: $($_.Lines)" }
}
Start-Sleep -Seconds 2
$left = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $me -and $_.CommandLine -match 'agent2[\\/]+snap(1|B)' -and $_.Name -notmatch '^powershell' }
foreach ($p in $left) {
    "orphan $($p.ProcessId) $($p.Name)"
    taskkill /T /F /PID $p.ProcessId 2>&1 | Out-Null
}
Start-Sleep -Seconds 1
$n = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $me -and $_.CommandLine -match ('agent2[\\/]+snap(1|B)|' + $drivers) -and
    $_.CommandLine -notmatch 'snap\.py' -and $_.CommandLine -notmatch 'stop-snap\.ps1' }).Count
"remaining snapshot-build processes: $n"
