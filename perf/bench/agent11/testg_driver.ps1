<#
.SYNOPSIS
  Test G driver (task #19): N pause/unpause cycles on a running Lego Dimensions game, checked with
  the "Guest suspended/resumed (N threads)" lines that ReXApp::SetGuestPaused logs (rex_app.cpp).

.DESCRIPTION
  Modes:
    post   The driver makes each cycle by posting the focus messages SDL reacts to (WM_NCACTIVATE,
           WM_ACTIVATE, WM_KILLFOCUS / WM_SETFOCUS) to the game window. The game must run with
           --pause_when_unfocused=true. SDL 3.5 acts on them only when GetForegroundWindow() agrees
           (SDL_windowsevents.c:324-333), so on a locked desktop a posted gain is ignored: the
           driver then reports INCONCLUSIVE, not a hang.
    watch  The game makes the cycles (a debug timer cvar in rex_app.cpp that calls SetGuestPaused on
           the UI thread). The driver only watches game.log and the UI thread.
  A cycle passes when "Guest resumed" follows "Guest suspended". A hang is any of:
    - post: no "Guest resumed" within ResumeTimeoutMs of posting the gain while the UI thread is silent;
    - watch: "Guest resumed" more than PeriodMs + ResumeTimeoutMs after "Guest suspended" (log
      timestamps), or not at all by then;
    - the UI thread not answering WM_NULL for UiHangMs (the unpause runs on it);
    - the game exiting.
  On a hang the driver writes hang-HHmmss-threads.txt (state and wait reason per thread; 'Suspended'
marks a suspended thread) and a small minidump (threads, stacks, handles) next to the report, and
also when the pause cycles stop early while the game still runs. If the cycles stop while the UI
thread is silent, the driver waits for the UI-hang rule (FAIL) instead of calling it INCONCLUSIVE.
  Exit codes: 0 PASS, 1 FAIL (hang or crash), 2 setup error, 3 INCONCLUSIVE (no pause activity,
  or posted focus messages ignored).

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_driver.ps1 -GamePid 1234 -Log <run>\game.log -Mode watch -Cycles 50 -PeriodMs 1000
#>
param(
    [Parameter(Mandatory = $true)][int]$GamePid,
    [Parameter(Mandatory = $true)][string]$Log,
    [ValidateSet('post', 'watch')][string]$Mode = 'watch',
    [int]$Cycles = 50,
    [int]$PeriodMs = 1000,            # watch: the game's toggle period (paused PeriodMs, running PeriodMs)
    [int]$HoldMs = 1000,              # post: time unfocused before the gain is posted
    [int]$GapMs = 1000,               # post: running time between cycles
    [int]$SuspendTimeoutMs = 5000,    # post: wait for "Guest suspended" after posting the loss
    [int]$ResumeTimeoutMs = 5000,     # a resume later than this after it was due is a hang
    [int]$FirstEventTimeoutSec = 180, # watch: no "Guest suspended" at all by then = INCONCLUSIVE
    [int]$UiHangMs = 10000,           # UI thread silent this long = hang
    [int]$PingEveryMs = 1000,
    [int]$GiveUpAfter = 2,            # post: stop after this many cycles in a row without full effect
    [switch]$FromStart,               # watch: also count pause lines already in the log
    [switch]$NoDump,
    [string]$Out = ''                 # report path; default <log dir>\testg_report.txt (+ .csv)
)

$ErrorActionPreference = 'Stop'
if (-not ('TestGWin' -as [type])) {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_win.cs'))) -Language CSharp
}
if (-not [IO.Path]::IsPathRooted($Log)) { $Log = Join-Path $PWD.Path $Log }
if (-not $Out) { $Out = Join-Path (Split-Path -Parent $Log) 'testg_report.txt' }
if (-not [IO.Path]::IsPathRooted($Out)) { $Out = Join-Path $PWD.Path $Out }
$csv = [IO.Path]::ChangeExtension($Out, '.csv')

try { $proc = [Diagnostics.Process]::GetProcessById($GamePid) } catch { Write-Host "SETUP ERROR: no process with id $GamePid"; exit 2 }

$S = @{
    sw = [Diagnostics.Stopwatch]::StartNew(); events = New-Object System.Collections.ArrayList
    tailLines = New-Object 'System.Collections.Generic.Queue[string]'; counting = $false; errorLines = 0; stray = 0
    hwnd = [IntPtr]::Zero; nextPing = 0; pings = 0; pingFails = 0; pingMax = 0; silentSince = -1; silentMax = 0
    exited = $false
}
$tail = New-Object 'TestGWin+LogTail' -ArgumentList $Log, $true
$rxGuest = [regex]'^(?:\[(?<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\] \[(?<lvl>[^\]]+)\] \[(?<cat>[^\]]*)\] \[t(?<tid>\d+)\] )?.*?Guest (?<what>suspended|resumed) \((?<n>\d+) threads\)'
$rxError = [regex]'^\[[^\]]+\] \[(error|critical)\]'
$inv = [Globalization.CultureInfo]::InvariantCulture

function Now { return $S.sw.ElapsedMilliseconds }

# Reads new log lines, pings the UI thread every PingEveryMs and notes whether the game still runs.
function Poll {
    foreach ($line in $tail.Read()) {
        $S.tailLines.Enqueue($line)
        while ($S.tailLines.Count -gt 40) { [void]$S.tailLines.Dequeue() }
        if ($S.counting -and $rxError.IsMatch($line)) { $S.errorLines++ }
        $m = $rxGuest.Match($line)
        if (-not $m.Success) { continue }
        $lt = $null
        if ($m.Groups['ts'].Success) { $lt = [datetime]::ParseExact($m.Groups['ts'].Value, 'yyyy-MM-dd HH:mm:ss.fff', $inv) }
        [void]$S.events.Add([pscustomobject]@{ Obs = (Now); Kind = $m.Groups['what'].Value; Threads = [int]$m.Groups['n'].Value; LogTime = $lt; Tid = $m.Groups['tid'].Value })
    }
    $t = Now
    if ($t -ge $S.nextPing) {
        $S.nextPing = $t + $PingEveryMs
        if (-not [TestGWin]::IsAlive($S.hwnd)) { $S.hwnd = [TestGWin]::MainWindow($GamePid) }
        if ([TestGWin]::IsAlive($S.hwnd)) {
            $ms = [TestGWin]::Ping($S.hwnd, 2000)
            $S.pings++
            if ($ms -lt 0) { $S.pingFails++; if ($S.silentSince -lt 0) { $S.silentSince = $t } }
            else { if ($ms -gt $S.pingMax) { $S.pingMax = $ms }; $S.silentSince = -1 }
        }
    }
    if ($S.silentSince -ge 0) { $sil = (Now) - $S.silentSince; if ($sil -gt $S.silentMax) { $S.silentMax = $sil } }
    if ($proc.HasExited) { $S.exited = $true }
}

function UiHung { return ($S.silentSince -ge 0 -and ((Now) - $S.silentSince) -ge $UiHangMs) }

function FindEvent([int]$from, [string]$kind) {
    for ($k = $from; $k -lt $S.events.Count; $k++) { if ($S.events[$k].Kind -eq $kind) { return $k } }
    return -1
}

# Polls until the condition holds (returns $true), or the time is up, the game exits or its UI thread hangs.
function WaitFor([int]$waitMs, [scriptblock]$cond) {
    $end = (Now) + $waitMs
    while ($true) {
        Poll
        if (& $cond) { return $true }
        if ($S.exited -or (UiHung)) { return $false }
        if ((Now) -ge $end) { return $false }
        Start-Sleep -Milliseconds 50
    }
}

function LogDelta($a, $b) {
    if ($a.LogTime -and $b.LogTime) { return [int](($b.LogTime - $a.LogTime).TotalMilliseconds) }
    return [int]($b.Obs - $a.Obs)
}

function NewCycle([int]$i) {
    return [pscustomobject]@{ Cycle = $i; Verdict = ''; SuspendLatMs = ''; ResumeLatMs = ''; PausedMs = ''; SuspendThreads = ''; ResumeThreads = ''; SuspendTid = ''; ResumeTid = ''; LossPost = ''; GainPost = ''; Note = '' }
}

function Median($xs) {
    $a = @($xs | Sort-Object)
    if ($a.Count -eq 0) { return '-' }
    return $a[[int][math]::Floor(($a.Count - 1) / 2)]
}

Poll                      # what the log already holds
$S.counting = $true
$pre = $S.events.Count
$initial = 'running'
if ($pre -gt 0 -and $S.events[$pre - 1].Kind -eq 'suspended') { $initial = 'paused' }
$hwnd0 = [TestGWin]::MainWindow($GamePid)
$win0 = [TestGWin]::Describe($hwnd0)
$desk0 = [TestGWin]::DesktopState()
$started = Get-Date
$results = New-Object System.Collections.ArrayList
$final = ''; $reason = ''; $dumpAnyway = $false
Write-Host "testg_driver: $Mode mode, pid $GamePid, $Cycles cycles"
Write-Host "testg_driver: window $win0"
Write-Host "testg_driver: $desk0"
Write-Host "testg_driver: guest $initial at start ($pre pause line(s) already in the log)"
if ($Mode -eq 'post' -and $hwnd0 -eq [IntPtr]::Zero) { $final = 'SETUP'; $reason = 'no visible game window' }

if ($Mode -eq 'post' -and -not $final) {
    $noEffect = 0
    for ($i = 1; $i -le $Cycles; $i++) {
        Poll
        if ($S.exited) { $final = 'FAIL'; $reason = "game exited before cycle $i"; break }
        $h = [TestGWin]::MainWindow($GamePid)
        if ($h -eq [IntPtr]::Zero) { $final = 'SETUP'; $reason = "game window gone before cycle $i"; break }
        $c = NewCycle $i
        $base = $S.events.Count
        $t0 = Now
        $c.LossPost = [TestGWin]::PostFocus($h, $false)
        [void](WaitFor $SuspendTimeoutMs { (FindEvent $base 'suspended') -ge 0 })
        $si = FindEvent $base 'suspended'
        if ($si -ge 0) { $e = $S.events[$si]; $c.SuspendLatMs = $e.Obs - $t0; $c.SuspendThreads = $e.Threads; $c.SuspendTid = $e.Tid }
        [void](WaitFor $HoldMs { $false })
        $base2 = $S.events.Count
        if ($si -ge 0) { $base2 = $si + 1 }
        $t1 = Now
        $c.GainPost = [TestGWin]::PostFocus($h, $true)
        [void](WaitFor $ResumeTimeoutMs { (FindEvent $base2 'resumed') -ge 0 })
        $ri = FindEvent $base2 'resumed'
        if ($ri -ge 0) { $e = $S.events[$ri]; $c.ResumeLatMs = $e.Obs - $t1; $c.ResumeThreads = $e.Threads; $c.ResumeTid = $e.Tid }
        if ($si -ge 0 -and $ri -ge 0) { $c.PausedMs = LogDelta $S.events[$si] $S.events[$ri] }
        if ($S.exited) { $c.Verdict = 'CRASH' }
        elseif ($si -ge 0 -and $ri -ge 0) { $c.Verdict = 'ok' }
        elseif (UiHung) { $c.Verdict = 'HANG' }
        elseif ($si -ge 0) { $c.Verdict = 'stuck-paused'; $c.Note = 'gain ignored, UI thread answers' }
        elseif ($ri -ge 0) { $c.Verdict = 'resume-only' }
        else { $c.Verdict = 'ignored' }
        [void]$results.Add($c)
        Write-Host ("cycle {0,3}: {1,-12} suspend {2,5} ms, resume {3,5} ms, threads {4}/{5}; loss [{6}] gain [{7}]" -f $i, $c.Verdict, $c.SuspendLatMs, $c.ResumeLatMs, $c.SuspendThreads, $c.ResumeThreads, $c.LossPost, $c.GainPost)
        if ($c.Verdict -eq 'CRASH') { $final = 'FAIL'; $reason = "game exited during cycle $i"; break }
        if ($c.Verdict -eq 'HANG') { $final = 'FAIL'; $reason = "cycle ${i}: no resume and the UI thread silent for $UiHangMs ms"; break }
        if ($c.Verdict -eq 'ok' -or $c.Verdict -eq 'resume-only') { $noEffect = 0 } else { $noEffect++ }
        if ($noEffect -ge $GiveUpAfter) { $final = 'INCONCLUSIVE'; $reason = "posted focus messages had no full effect in $noEffect cycles in a row (last: $($c.Verdict))"; break }
        [void](WaitFor $GapMs { $false })
    }
}
elseif ($Mode -eq 'watch' -and -not $final) {
    $next = $pre
    if ($FromStart) { $next = 0 }
    $cur = $null; $curS = $null; $lastResumeObs = -1
    $deadline = (Now) + $FirstEventTimeoutSec * 1000
    $hangAfter = $PeriodMs + $ResumeTimeoutMs
    while (-not $final) {
        Poll
        while ($next -lt $S.events.Count) {
            $e = $S.events[$next]; $next++
            if ($e.Kind -eq 'suspended') {
                if ($cur) { $cur.Verdict = 'NO-RESUME'; $cur.Note = 'a second suspend came first'; [void]$results.Add($cur) }
                $cur = NewCycle ($results.Count + 1); $curS = $e
                $cur.SuspendThreads = $e.Threads; $cur.SuspendTid = $e.Tid
            }
            elseif ($cur) {
                $cur.ResumeThreads = $e.Threads; $cur.ResumeTid = $e.Tid
                $cur.PausedMs = LogDelta $curS $e
                if ($cur.PausedMs -gt $hangAfter) { $cur.Verdict = 'LATE' } else { $cur.Verdict = 'ok' }
                if ($cur.SuspendThreads -ne $cur.ResumeThreads) { $cur.Note = 'thread counts differ' }
                [void]$results.Add($cur)
                Write-Host ("cycle {0,3}: {1,-5} paused {2,5} ms, threads {3}/{4}, tid {5}/{6}" -f $cur.Cycle, $cur.Verdict, $cur.PausedMs, $cur.SuspendThreads, $cur.ResumeThreads, $cur.SuspendTid, $cur.ResumeTid)
                $cur = $null; $lastResumeObs = $e.Obs
            }
            else { $S.stray++ }
        }
        $bad = @($results | Where-Object { $_.Verdict -ne 'ok' })
        if ($bad.Count -gt 0) { $final = 'FAIL'; $reason = "cycle $($bad[0].Cycle): $($bad[0].Verdict) (paused $($bad[0].PausedMs) ms, limit $hangAfter ms)"; break }
        if ($results.Count -ge $Cycles) { break }
        if ($S.exited) { $final = 'FAIL'; $reason = "game exited after $($results.Count) cycles"; break }
        if (UiHung) {
            $final = 'FAIL'; $reason = "UI thread did not answer WM_NULL for $UiHangMs ms after $($results.Count) cycles"
            if ($cur) { $reason += ' (guest paused)'; $cur.Verdict = 'HANG'; [void]$results.Add($cur) }
            elseif ($lastResumeObs -ge 0) { $reason += (" (guest running: no 'Guest suspended' since the last 'Guest resumed' {0:N1} s ago, so the next pause never got as far as its log line)" -f (((Now) - $lastResumeObs) / 1000.0)) }
            break
        }
        if ($cur -and ((Now) - $curS.Obs) -gt $hangAfter) { $final = 'FAIL'; $reason = "cycle $($cur.Cycle): no 'Guest resumed' within $hangAfter ms of 'Guest suspended'"; $cur.Verdict = 'HANG'; [void]$results.Add($cur); break }
        if ($results.Count -eq 0 -and -not $cur -and (Now) -gt $deadline) { $final = 'INCONCLUSIVE'; $reason = "no 'Guest suspended' line within $FirstEventTimeoutSec s (is the debug pause timer on?)"; break }
        if (-not $cur -and $lastResumeObs -ge 0 -and ((Now) - $lastResumeObs) -gt ($hangAfter + 5000)) {
            # Toggling stopped early. If the UI thread is silent right now, this is probably the hang
            # itself (the original pause order logs 'Guest suspended' only after it has suspended),
            # so keep polling until the UI-hang rule above fires; any answer ends the wait.
            # (Test G control, 21:37: this rule won the race by 0.5 s, with 9.5 s of silence.)
            if ($S.silentSince -ge 0) { Start-Sleep -Milliseconds 50; continue }
            $final = 'INCONCLUSIVE'; $reason = "pause cycles stopped after $($results.Count) of $Cycles (timer count reached, or toggling stopped)"
            if ($results.Count -lt $Cycles) { $dumpAnyway = $true }
            break
        }
        Start-Sleep -Milliseconds 50
    }
}

if (-not $final) { $final = 'PASS'; $reason = "$($results.Count) cycles, every one resumed in time" }
$dump = ''
$threadsInfo = ''
if (($final -eq 'FAIL' -or $dumpAnyway) -and -not $S.exited -and -not $NoDump) {
    $stamp = '{0:HHmmss}' -f (Get-Date)
    $dumpDir = Split-Path -Parent $Out
    New-Item -ItemType Directory -Force -Path $dumpDir | Out-Null
    # Thread states first: a minidump from dbghelp always records SuspendCount 0, so the threads
    # the runtime suspended are found here instead (wait reason 'Suspended'); match them by tid
    # with the stacks in the dump (bench/agent11/testg_dump.ps1).
    try {
        $tl = New-Object 'System.Collections.Generic.List[string]'
        $susp = New-Object 'System.Collections.Generic.List[string]'
        $gp = [Diagnostics.Process]::GetProcessById($GamePid)
        $tl.Add(('{0:yyyy-MM-dd HH:mm:ss.fff} game pid {1}: {2} threads' -f (Get-Date), $GamePid, $gp.Threads.Count))
        $tl.Add('tid     state          wait_reason       prio  cpu_ms')
        foreach ($t in $gp.Threads) {
            $st = '?'; $wr = ''; $pr = ''; $cpu = ''
            try { $st = [string]$t.ThreadState } catch { }
            if ($st -eq 'Wait') { try { $wr = [string]$t.WaitReason } catch { $wr = '?' } }
            try { $pr = $t.CurrentPriority } catch { }
            try { $cpu = [long]$t.TotalProcessorTime.TotalMilliseconds } catch { }
            if ($wr -eq 'Suspended') { $susp.Add([string]$t.Id) }
            $tl.Add(('{0,-7} {1,-14} {2,-17} {3,4} {4,7}' -f $t.Id, $st, $wr, $pr, $cpu))
        }
        $tf = Join-Path $dumpDir "hang-$stamp-threads.txt"
        [IO.File]::WriteAllLines($tf, $tl)
        $threadsInfo = "$tf : $($gp.Threads.Count) threads, $($susp.Count) suspended ($($susp -join ','))"
    }
    catch { $threadsInfo = "thread list failed: $($_.Exception.Message)" }
    $dumpPath = Join-Path $dumpDir "hang-$stamp.dmp"
    $dump = "$dumpPath : " + [TestGWin]::MiniDump($GamePid, $dumpPath)
}

$lines = New-Object 'System.Collections.Generic.List[string]'
$lines.Add("Test G driver report (bench/agent11/testg_driver.ps1), $Mode mode")
$lines.Add(("started {0:yyyy-MM-dd HH:mm:ss}, ran {1:N1} s; game pid {2}; log {3}" -f $started, ((Now) / 1000.0), $GamePid, $Log))
$lines.Add("window at start: $win0")
$lines.Add("desktop at start: $desk0")
$lines.Add("guest at start: $initial ($pre pause line(s) already in the log)")
$lines.Add("parameters: Cycles=$Cycles PeriodMs=$PeriodMs HoldMs=$HoldMs GapMs=$GapMs SuspendTimeoutMs=$SuspendTimeoutMs ResumeTimeoutMs=$ResumeTimeoutMs UiHangMs=$UiHangMs FromStart=$FromStart")
$lines.Add('')
$lines.Add('cycle verdict       susp_ms res_ms paused_ms threads(s/r) tid(s/r)        note')
foreach ($c in $results) {
    $note = $c.Note
    if ($Mode -eq 'post') { $note = ("{0} loss[{1}] gain[{2}]" -f $c.Note, $c.LossPost, $c.GainPost).Trim() }
    $lines.Add(("{0,5} {1,-13} {2,7} {3,6} {4,9} {5,12} {6,-15} {7}" -f $c.Cycle, $c.Verdict, $c.SuspendLatMs, $c.ResumeLatMs, $c.PausedMs, ('{0}/{1}' -f $c.SuspendThreads, $c.ResumeThreads), ('{0}/{1}' -f $c.SuspendTid, $c.ResumeTid), $note))
}
$lines.Add('')
$counts = (@($results | Group-Object Verdict | ForEach-Object { '{0}={1}' -f $_.Name, $_.Count })) -join ', '
$paused = @($results | Where-Object { $_.PausedMs -is [int] } | ForEach-Object { $_.PausedMs })
$resLat = @($results | Where-Object { $_.ResumeLatMs -is [long] -or $_.ResumeLatMs -is [int] } | ForEach-Object { $_.ResumeLatMs })
$lines.Add("cycles: $($results.Count) ($counts); stray 'Guest resumed' lines: $($S.stray)")
$lines.Add(("paused time per cycle (log timestamps): median {0} ms, max {1} ms; post-mode resume latency: median {2} ms, max {3} ms" -f (Median $paused), $(if ($paused.Count) { ($paused | Measure-Object -Maximum).Maximum } else { '-' }), (Median $resLat), $(if ($resLat.Count) { ($resLat | Measure-Object -Maximum).Maximum } else { '-' })))
$lines.Add("UI thread: $($S.pings) WM_NULL pings, $($S.pingFails) unanswered, slowest answer $($S.pingMax) ms, longest silence $($S.silentMax) ms")
$lines.Add("error/critical log lines during the test: $($S.errorLines)")
if ($threadsInfo) { $lines.Add("threads: $threadsInfo") }
if ($dump) { $lines.Add("minidump: $dump") }
$lines.Add("VERDICT: $final - $reason")
if ($final -ne 'PASS') {
    $lines.Add('')
    $lines.Add('last log lines:')
    foreach ($l in $S.tailLines) { $lines.Add('  ' + $l) }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
[IO.File]::WriteAllLines($Out, $lines)
$results | Export-Csv -LiteralPath $csv -NoTypeInformation
$lines | Where-Object { $_ -match '^(cycles|paused time|UI thread|error/critical|threads|minidump|VERDICT):' } | ForEach-Object { Write-Host "testg_driver: $_" }
Write-Host "testg_driver: report $Out"
switch ($final) { 'PASS' { exit 0 } 'FAIL' { exit 1 } 'SETUP' { exit 2 } default { exit 3 } }
