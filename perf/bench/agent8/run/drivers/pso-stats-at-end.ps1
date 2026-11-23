# Driver for run-timing.ps1 -Driver (matrix arm field "driver"): Agent 6's PSO stats summary before the close.
# Why: in NATIVE_GPU builds WM_CLOSE arms a watchdog that calls TerminateProcess 250 ms later, so the PSO exit summary
# ("Native GPU PSO stats (exit)", the "PSO minute" table, cache hits/misses) is usually lost. The game logs the same
# summary when <exe dir>\cache\pso-stats.now appears (it polls every 2 s, then deletes the file).
# perf-notes/agent6-runspecs.md, "Exit caveat".
#
# run-timing.ps1 starts the driver at the measure-start mark with -GamePid/-RunDir, and after the window it WAITS for
# the driver before it sends WM_CLOSE (up to -DriverTimeoutSec, 120 s by default). This driver:
#   1. waits for the window end: the proc.csv row whose note says "measure end" (no fixed length, so -Quick works);
#   2. creates the trigger (path from the game.log line "PSO stats on", else <run>\cache\pso-stats.now);
#   3. waits until game.log shows "Native GPU PSO stats (pso-stats.now)" and then the "PSO frames" line (or -WaitSec);
#   4. exits, and run-timing closes the game.
# Exit 0: trigger created (a missing summary is a WARNING line in driver.out.txt, so the run's timing stays valid).
# Exit 1: the trigger could not be created. Exit 2: bad arguments. Exit 4: no window end within -MaxSec.
# The game exiting early is not a driver failure (exit 0; the runner reports the exit).
param(
    [int]$GamePid = 0,
    [string]$RunDir = '',
    [double]$WaitSec = 15,
    [double]$MaxSec = 1800,
    [string]$Log = 'game.log'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$sw = [Diagnostics.Stopwatch]::StartNew()
function Say([string]$M) { Write-Output ('{0} +{1:0.00}s {2}' -f (Get-Date).ToString('HH:mm:ss.fff'), $sw.Elapsed.TotalSeconds, $M) }

# Reads the bytes appended since $State.Offset (the file stays open in the game; share everything).
function Read-New([hashtable]$State) {
    if (-not (Test-Path -LiteralPath $State.Path)) { return '' }
    $share = [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
    $fs = [IO.File]::Open($State.Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, $share)
    try {
        if ($fs.Length -lt $State.Offset) { $State.Offset = [int64]0 }
        $n = $fs.Length - $State.Offset
        if ($n -le 0) { return '' }
        $null = $fs.Seek($State.Offset, [IO.SeekOrigin]::Begin)
        $buf = New-Object byte[] ([int][math]::Min($n, 64MB))
        $got = $fs.Read($buf, 0, $buf.Length)
        $State.Offset += $got
        $text = $State.Carry + [Text.Encoding]::UTF8.GetString($buf, 0, $got)
        $cut = $text.LastIndexOf("`n")
        if ($cut -lt 0) { $State.Carry = $text; return '' }
        $State.Carry = $text.Substring($cut + 1)
        return $text.Substring(0, $cut + 1)
    } finally { $fs.Dispose() }
}

if (-not $RunDir -or -not (Test-Path -LiteralPath $RunDir -PathType Container)) { Say "bad -RunDir '$RunDir'"; exit 2 }
$game = $null
try { $game = [Diagnostics.Process]::GetProcessById($GamePid) } catch { Say "game pid $GamePid not found (already gone?)"; exit 0 }
$logPath = if ([IO.Path]::IsPathRooted($Log)) { $Log } else { Join-Path $RunDir $Log }
$procCsv = Join-Path $RunDir 'proc.csv'
Say "pso-stats-at-end: pid $GamePid, run dir $RunDir"

# 1. Window end: run-timing writes the end-mark row (note "measure end") just before it starts waiting for us.
$pc = @{ Path = $procCsv; Offset = [int64]0; Carry = '' }
$logS = @{ Path = $logPath; Offset = [int64]0; Carry = '' }
$trigPath = $null
$ended = $false
while (-not $ended) {
    if ($game.HasExited) { Say "the game exited before the window end (exit $($game.ExitCode)); no trigger"; exit 0 }
    if ($sw.Elapsed.TotalSeconds -gt $MaxSec) { Say "!!! no 'measure end' row in proc.csv within $MaxSec s"; exit 4 }
    try { if ((Read-New $pc) -match 'measure end') { $ended = $true } } catch { }
    # Track the trigger path from the startup line while we wait (cheap: only new log bytes are read).
    try {
        foreach ($line in ((Read-New $logS) -split "`n")) {
            if (-not $trigPath -and $line -match 'PSO stats on' -and $line -match '([A-Za-z]:[\\/][^"''<>|*?\r\n]*?pso-stats\.now)') { $trigPath = $Matches[1] }
        }
    } catch { }
    if (-not $ended) { Start-Sleep -Milliseconds 250 }
}
Say 'window end seen in proc.csv'
if (-not $trigPath) { $trigPath = Join-Path (Join-Path $RunDir 'cache') 'pso-stats.now'; Say "no 'PSO stats on' path in game.log; using $trigPath" }
else { Say "trigger path from game.log: $trigPath" }

# 2. Trigger.
try {
    $dir = Split-Path -Parent $trigPath
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [IO.File]::WriteAllText($trigPath, '')
} catch { Say "!!! could not create the trigger ${trigPath}: $($_.Exception.Message)"; exit 1 }
$tTrig = $sw.Elapsed.TotalSeconds
Say "trigger created"

# 3. Summary in game.log: header, then the "PSO frames" line (the last summary line), or the time limit.
$seenHead = $false; $seenEnd = $false; $headAt = $null
while ($sw.Elapsed.TotalSeconds - $tTrig -lt $WaitSec) {
    if ($game.HasExited) { Say "!!! the game exited while waiting for the summary (exit $($game.ExitCode))"; break }
    try {
        foreach ($line in ((Read-New $logS) -split "`n")) {
            if (-not $seenHead -and $line -match 'PSO stats \(pso-stats\.now\)') { $seenHead = $true; $headAt = $sw.Elapsed.TotalSeconds; Say ('summary header after {0:0.0} s' -f ($headAt - $tTrig)) }
            elseif ($seenHead -and $line -match 'PSO frames') { $seenEnd = $true }
        }
    } catch { }
    if ($seenEnd) { break }
    if ($seenHead -and ($sw.Elapsed.TotalSeconds - $headAt) -gt 3) { break }   # header seen; give the rest 3 s
    Start-Sleep -Milliseconds 250
}
$left = Test-Path -LiteralPath $trigPath
if ($seenEnd) { Say 'summary complete (PSO frames line seen)' }
elseif ($seenHead) { Say 'WARNING: summary header seen, no PSO frames line within 3 s (check game.log)' }
else { Say "WARNING: no 'Native GPU PSO stats (pso-stats.now)' line within $WaitSec s; trigger still there: $left. Sum the 10 s lines instead" }
exit 0
