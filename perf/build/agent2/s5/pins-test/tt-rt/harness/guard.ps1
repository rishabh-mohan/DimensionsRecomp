# harness/guard.ps1 - dot-sourced by run-game.ps1 and selftest\selftest.ps1.
# Get-ActiveRunners lists Agent 8's timing and boot runners (bench\agent8\run\run-matrix.ps1, run-timing.ps1,
# first-boot.ps1, bench\agent8\RUN-TIMING-MATRIX.cmd). A runner starts a new game every few minutes and leaves gaps
# with no game running (cooldown, settle), so "no legodimensions.exe" alone does not mean the machine is free: at
# 22:48 the self-test started in such a gap of the user's matrix and its crash case's WER dump was picked up by
# matrix run 2248-r0-r3. The caller's own ancestors are skipped, so a command line that merely mentions a runner's
# name does not block itself.
function Get-ActiveRunners {
    $procs = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name, CommandLine -ErrorAction SilentlyContinue)
    $parent = @{}
    foreach ($p in $procs) { $parent[[int]$p.ProcessId] = [int]$p.ParentProcessId }
    $skip = @{}; $id = $PID
    for ($i = 0; $i -lt 32 -and $id -and -not $skip.ContainsKey($id); $i++) { $skip[$id] = $true; $id = $parent[$id] }
    $re = '(?i)run-matrix\.ps1|run-timing\.ps1|first-boot\.ps1|RUN-TIMING-MATRIX\.cmd'
    @($procs | Where-Object { $_.Name -match '^(powershell|pwsh|cmd)\.exe$' -and -not $skip.ContainsKey([int]$_.ProcessId) -and "$($_.CommandLine)" -match $re } |
        ForEach-Object { "pid $($_.ProcessId) $([regex]::Match("$($_.CommandLine)", $re).Value)" })
}
