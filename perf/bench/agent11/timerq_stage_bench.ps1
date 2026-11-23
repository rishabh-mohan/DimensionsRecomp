<#
.SYNOPSIS
  Agent 11, S3 task #10: tests the staged TimerQueue fix (cvar timer_queue_precise_wait, default
  OFF; build\agent11\timerq\stage\timer_queue.cpp from timerq_stage.ps1) against the live code.
  Builds bench_timerq.exe twice with single-threaded cl:
    live   - links the unmodified rexglue-sdk src/core/timer_queue.cpp
    staged - links the staged copy, /DBENCH_STAGED (bench_timerq.cpp then defines the cvar's
             SleepPrecise the way src/core/threading_win.cpp does)
  Correctness, in every mode (live spin/blocking; staged spin/blocking with the cvar off; staged
  precise, precise + REX_TIMER_WAIT_BLOCKING, precise without the high-resolution timer):
    stress 2000 50    the 1 ms timer plus 2000 one-shots: overflows the 512-slot ring, so the
                      claim wait and the consumer's notify run; each must fire once, never early
    stress 40 2000 0  40 one-shots 50 ms apart and no other timer: the condition-variable
                      stretch of the precise wait, then its slices
    exit              returns from main with timers armed: the static queue must stop in < 3 s
  The staged precise runs must log "TimerQueue: precise wait"; no other run may.
  Performance: the 1 ms timer for -Seconds at the OS default timer resolution (live spin, staged
  spin, staged precise, live blocking, staged precise without the high-resolution timer) and at
  timeBeginPeriod 1 (staged precise).
  Every case runs only while no legodimensions process is up (Agent 8's slot); a run during
  which a game appeared is logged, discarded and retried (3 tries). -MaxWaitMin bounds the total
  wait; cases left over are reported and the result is INCOMPLETE (exit 3). -IgnoreGame runs
  regardless (numbers then include the game's load).
  No game is started. At most 2 busy threads, one process at a time, single-threaded cl.
  Log: build\agent11\timerq\stage-bench-<time>.txt. Exit 0 = every check passed.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage_bench.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage_bench.ps1 -NoBuild -NoCorrectness
#>
param(
  [int]$Seconds = 10,
  [switch]$NoBuild,
  [switch]$NoCorrectness,
  [switch]$NoPerf,
  [switch]$IgnoreGame,
  [int]$MaxWaitMin = 60
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$out = Join-Path $root 'build\agent11\timerq'
$stage = Join-Path $out 'stage'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$log = Join-Path $out ('stage-bench-{0:yyyyMMdd-HHmmss}.txt' -f (Get-Date))
function Say([string]$s) { Write-Host $s; Add-Content -Path $log -Value $s -Encoding ascii }

$sdk = 'DimensionsRecomp\rexglue-sdk'
$liveSrc = Join-Path $root "$sdk\src\core\timer_queue.cpp"
$stagedSrc = Join-Path $stage 'timer_queue.cpp'
if (-not (Test-Path $stagedSrc)) { throw 'no staged copy: run bench\agent11\timerq_stage.ps1 first' }
$exes = @{ live = (Join-Path $out 'live\bench_timerq.exe'); staged = (Join-Path $out 'staged\bench_timerq.exe') }
function Sha12([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 12) }
$cpuName = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name.Trim()
$bat = Get-CimInstance Win32_Battery | Select-Object -First 1
Say ('# timerq_stage_bench {0:yyyy-MM-dd HH:mm:ss}  {1}  AC={2}  live timer_queue.cpp {3}  staged {4}  seconds {5}' -f `
    (Get-Date), $cpuName, ($bat.BatteryStatus -eq 2), (Sha12 $liveSrc), (Sha12 $stagedSrc), $Seconds)

$fails = New-Object System.Collections.Generic.List[string]
$skipped = New-Object System.Collections.Generic.List[string]
function Check([bool]$ok, [string]$what) {
  if ($ok) { Say "PASS  $what" } else { Say "FAIL  $what"; $fails.Add($what) }
}

if (-not $NoBuild) {
  . (Join-Path $root 'env\devshell.ps1') -Quiet
  foreach ($k in 'live', 'staged') {
    $dir = Split-Path $exes[$k]
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $src = $liveSrc; $defs = @()
    if ($k -eq 'staged') { $src = $stagedSrc; $defs = @('/DBENCH_STAGED') }
    $o = & cl /nologo /O2 /std:c++20 /EHsc /W3 /DNDEBUG /DNOMINMAX @defs `
      /I bench\agent11\timerq_shim /I "$sdk\include" /I "$sdk\thirdparty\disruptorplus\include" `
      bench\agent11\bench_timerq.cpp $src "/Fe:$($exes[$k])" "/Fo:$dir\" winmm.lib 2>&1
    $code = $LASTEXITCODE
    $o | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^(bench_timerq|timer_queue)\.cpp$' -and $_ -notmatch 'C4996' -and $_.Trim() } |
      ForEach-Object { Say "[cl $k] $_" }
    if ($code -ne 0) { Say "BUILD FAILED ($k, cl exit $code)"; exit 1 }
    Say "built $k $($exes[$k]) from $src (C4996 getenv warnings not shown)"
  }
}
foreach ($k in 'live', 'staged') { if (-not (Test-Path $exes[$k])) { Say "missing $($exes[$k]): build first"; exit 1 } }

$waitUntil = (Get-Date).AddMinutes($MaxWaitMin)
function Wait-NoGame {
  if ($IgnoreGame) { return $true }
  $said = $false
  while (Get-Process legodimensions* -ErrorAction SilentlyContinue) {
    if (-not $said) { Say ('# {0:HH:mm:ss} a legodimensions process is running (Agent 8''s slot): waiting' -f (Get-Date)); $said = $true }
    if ((Get-Date) -gt $waitUntil) { Say "# the $MaxWaitMin min wait budget is used up"; return $false }
    Start-Sleep -Seconds 5
  }
  if ($said) { Say ('# {0:HH:mm:ss} game gone, continuing' -f (Get-Date)) }
  return $true
}

# One bench process with its own environment (the parent's is not touched), killed on timeout.
function Invoke-Case([string]$kind, [hashtable]$envs, [string[]]$benchArgs, [int]$timeoutSec) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $exes[$kind]; $psi.Arguments = ($benchArgs -join ' '); $psi.WorkingDirectory = $out
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
  $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  foreach ($n in 'REX_TIMER_WAIT_BLOCKING', 'TIMERQ_PRECISE', 'TIMERQ_NO_HIRES') {
    if ($psi.EnvironmentVariables.ContainsKey($n)) { $psi.EnvironmentVariables.Remove($n) }
  }
  foreach ($n in $envs.Keys) { $psi.EnvironmentVariables[$n] = $envs[$n] }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = [Diagnostics.Process]::Start($psi)
  $o = $p.StandardOutput.ReadToEndAsync(); $e = $p.StandardError.ReadToEndAsync()
  $timedOut = -not $p.WaitForExit($timeoutSec * 1000)
  if ($timedOut) { try { $p.Kill() } catch { }; [void]$p.WaitForExit(5000) } else { $p.WaitForExit() }
  $secs = $sw.Elapsed.TotalSeconds
  $code = -1; if (-not $timedOut) { $code = $p.ExitCode }
  $text = ($o.Result + $e.Result)
  $p.Dispose()
  return @{ Code = $code; Secs = $secs; TimedOut = $timedOut; Text = $text }
}

$modes = [ordered]@{
  'live spin'               = @{ Kind = 'live';   Env = @{};                                            Label = 'live SPIN (default)' }
  'live blocking'           = @{ Kind = 'live';   Env = @{ REX_TIMER_WAIT_BLOCKING = '1' };              Label = 'live BLOCKING (REX_TIMER_WAIT_BLOCKING)' }
  'staged spin'             = @{ Kind = 'staged'; Env = @{};                                            Label = 'staged SPIN (default)' }
  'staged blocking'         = @{ Kind = 'staged'; Env = @{ REX_TIMER_WAIT_BLOCKING = '1' };              Label = 'staged BLOCKING (REX_TIMER_WAIT_BLOCKING)' }
  'staged precise'          = @{ Kind = 'staged'; Env = @{ TIMERQ_PRECISE = '1' };                       Label = 'staged PRECISE (timer_queue_precise_wait)' }
  'staged precise+blocking' = @{ Kind = 'staged'; Env = @{ TIMERQ_PRECISE = '1'; REX_TIMER_WAIT_BLOCKING = '1' }; Label = 'staged PRECISE (timer_queue_precise_wait) + REX_TIMER_WAIT_BLOCKING' }
  'staged precise no-hires' = @{ Kind = 'staged'; Env = @{ TIMERQ_PRECISE = '1'; TIMERQ_NO_HIRES = '1' };  Label = 'staged PRECISE (timer_queue_precise_wait) + TIMERQ_NO_HIRES' }
}

function Run-Mode([string]$name, [string[]]$benchArgs, [int]$timeoutSec) {
  $m = $modes[$name]
  $r = Invoke-Case $m.Kind $m.Env $benchArgs $timeoutSec
  Say ''
  Say ('## {0}: bench_timerq {1}  [{2:HH:mm:ss}  exit {3}  {4:N2} s{5}]' -f $name, ($benchArgs -join ' '), (Get-Date), $r.Code, $r.Secs,
      $(if ($r.TimedOut) { '  TIMED OUT, killed' } else { '' }))
  $r.Text -split "`r?`n" | Where-Object { $_.Trim() } | ForEach-Object { Say "  $_" }
  return $r
}

# Runs a case while no game is up; a run during which a game appeared is discarded and retried.
# Returns $null when no game-free run was possible (the case is then listed as skipped).
function Run-Clean([string]$name, [string[]]$benchArgs, [int]$timeoutSec) {
  for ($try = 1; $try -le 3; $try++) {
    if (-not (Wait-NoGame)) { break }
    $r = Run-Mode $name $benchArgs $timeoutSec
    if ($IgnoreGame) { return $r }
    $g = @(Get-Process legodimensions* -ErrorAction SilentlyContinue)
    if ($g.Count -eq 0) { return $r }
    Say ('# a game started during this run (pid {0}, started {1:HH:mm:ss}): discarded' -f $g[0].Id, $g[0].StartTime)
  }
  $skipped.Add("$name $($benchArgs -join ' ')")
  Say "# SKIPPED $name $($benchArgs -join ' '): no game-free run"
  return $null
}

# The mode line names the expected wait, and only precise runs log the switch.
function Check-Mode([string]$name, [string[]]$benchArgs, $r) {
  $m = $modes[$name]
  $wantLog = $name -like 'staged precise*'
  $hasLog = $r.Text -match 'TimerQueue: precise wait \(timer_queue_precise_wait\)'
  $labelOk = $r.Text -match ('(?m)^mode ' + [regex]::Escape($m.Label) + '(\s|$)')
  Check ((-not $r.TimedOut) -and $labelOk -and ($hasLog -eq $wantLog)) ("{0} {1}: mode '{2}', precise log line {3}" -f `
      $name, ($benchArgs -join ' '), $m.Label, $(if ($wantLog) { 'present' } else { 'absent' }))
}

function Num([string]$text, [string]$pattern) {
  if ($text -match $pattern) { return [double]$Matches[1] }
  return [double]::NaN
}
function Lat([string]$text) {
  if ($text -match 'lateness ms p50 ([\d.]+) p90 [\d.]+ p99 ([\d.]+) max ([\d.]+)') {
    return ('{0} / {1} / {2}' -f $Matches[1], $Matches[2], $Matches[3])
  }
  return 'n/a'
}

# ---- correctness ----
$stressRows = New-Object System.Collections.Generic.List[string]
if (-not $NoCorrectness) {
  foreach ($name in $modes.Keys) {
    $a = Run-Clean $name @('stress', '2000', '50') 60
    if ($a) {
      Check-Mode $name @('stress', '2000', '50') $a
      Check (($a.Code -eq 0) -and ($a.Text -match 'RESULT ok')) "$name stress 2000 50: RESULT ok, exit 0"
    }
    $b = Run-Clean $name @('stress', '40', '2000', '0') 60
    if ($b) {
      Check-Mode $name @('stress', '40', '2000', '0') $b
      Check (($b.Code -eq 0) -and ($b.Text -match 'RESULT ok')) "$name stress 40 2000 0: RESULT ok, exit 0"
    }
    $c = Run-Clean $name @('exit') 15
    if ($c) {
      Check-Mode $name @('exit') $c
      Check (($c.Code -eq 0) -and (-not $c.TimedOut) -and ($c.Secs -lt 3)) ("{0} exit: exit 0 in < 3 s (took {1:N2} s)" -f $name, $c.Secs)
    }
    $okA = 'n/a'; $latA = 'n/a'; $qt = [double]::NaN; $latB = 'n/a'; $exitS = 'n/a'
    if ($a) { $okA = $(if ($a.Text -match 'RESULT ok') { 'ok' } else { 'FAIL' }); $latA = Lat $a.Text; $qt = Num $a.Text 'longest QueueTimer call ([\d.]+) ms' }
    if ($b) { $latB = '{0} ({1})' -f (Lat $b.Text), $(if ($b.Text -match 'RESULT ok') { 'ok' } else { 'FAIL' }) }
    if ($c) { $exitS = '{0:N2}' -f $c.Secs }
    $stressRows.Add(('| {0} | {1} | {2} | {3:N3} | {4} | {5} |' -f $name, $okA, $latA, $qt, $latB, $exitS))
  }
}

# ---- performance ----
$perfRows = New-Object System.Collections.Generic.List[string]
if (-not $NoPerf) {
  $cases = @(
    @('live spin', 0), @('staged spin', 0), @('staged precise', 0), @('live blocking', 0),
    @('staged precise no-hires', 0), @('staged precise', 1)
  )
  foreach ($cs in $cases) {
    $name = $cs[0]; $tbp = $cs[1]
    $args1 = @('run', "$Seconds", "$tbp")
    $r = Run-Clean $name $args1 ($Seconds + 30)
    if (-not $r) { continue }
    Check-Mode $name $args1 $r
    Check (($r.Code -eq 0) -and ($r.Text -match 'callbacks: ')) "$name run $Seconds ${tbp}: exit 0"
    $cpu = Num $r.Text 'timer thread CPU: ([\d.]+)%'
    $cps = Num $r.Text 'callbacks: ([\d.]+)/s'
    $p50 = Num $r.Text 'gap ms p10 [\d.]+ p50 ([\d.]+)'
    $p99 = Num $r.Text 'p90 [\d.]+ p99 ([\d.]+) max'
    $mx = Num $r.Text 'p99 [\d.]+ max ([\d.]+);'
    $stale = Num $r.Text 'stale ([\d.]+)%'
    $sp = Num $r.Text 'SleepPrecise calls: ([\d.]+)/s'
    $perfRows.Add(('| {0} | {1} | {2:N1} | {3:N0} | {4:N3} | {5:N3} | {6:N3} | {7:N1} | {8} |' -f $name, $tbp, $cpu, $cps, $p50, $p99, $mx, $stale,
        $(if ([double]::IsNaN($sp)) { '-' } else { '{0:N0}' -f $sp })))
    if ($name -eq 'staged precise') {
      Check ($cpu -lt 5) ("staged precise run (timeBeginPeriod {0}): timer thread CPU < 5% (got {1:N1}%)" -f $tbp, $cpu)
      Check ($p50 -lt 1.5) ("staged precise run (timeBeginPeriod {0}): median gap < 1.5 ms (got {1:N3})" -f $tbp, $p50)
    }
  }
}

if ($stressRows.Count) {
  Say ''
  Say '### correctness (lateness ms p50 / p99 / max)'
  Say '| mode | stress 2000 50 | lateness, 1 ms timer on | longest QueueTimer ms | lateness, stress 40 2000 0 (no other timer) | exit s |'
  Say '|---|---|---|---|---|---|'
  $stressRows | ForEach-Object { Say $_ }
}
if ($perfRows.Count) {
  Say ''
  Say "### 1 ms timer, $Seconds s"
  Say '| mode | timeBeginPeriod | timer thread CPU % | callbacks/s | gap p50 ms | gap p99 ms | gap max ms | tick count >2 ms stale % | SleepPrecise/s |'
  Say '|---|---|---|---|---|---|---|---|---|'
  $perfRows | ForEach-Object { Say $_ }
}
Say ''
if ($skipped.Count) { Say "skipped ($($skipped.Count)), no game-free run:"; $skipped | ForEach-Object { Say "  - $_" } }
if ($fails.Count) { Say "RESULT: FAIL ($($fails.Count))"; $fails | ForEach-Object { Say "  - $_" } }
elseif ($skipped.Count) { Say 'RESULT: INCOMPLETE (no failures)' }
else { Say 'RESULT: PASS' }
Say ('# done {0:HH:mm:ss}  log {1}' -f (Get-Date), $log)
if ($fails.Count) { exit 1 }
if ($skipped.Count) { exit 3 }
exit 0
