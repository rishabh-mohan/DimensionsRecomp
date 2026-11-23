# s4b-queue.ps1 - Agent 3 S4b (task #29) sequential game queue. FUNCTIONAL ONLY (run-game.ps1 = hidden desktop).
# A copy of build\agent3\s4a\s4a-queue.ps1 with these changes:
#   - files in build\agent3\s4b: queue.jsonl, queue-state.jsonl, STOP, PAUSE, logs\;
#   - perf-notes\WINDOW-HOLD.txt (a user timing window) or a PAUSE file next to this script: no launch while either
#     exists (the queue waits, it doesn't end); both are checked again right before each launch;
#   - holdwatch.ps1 runs beside attach.ps1 (build\agent3\s4a\attach.ps1, unchanged): if the HOLD file appears while a
#     game runs, it stops that game and writes logs\<id>.hold-abort.txt; such a record gets "aborted":"hold" and is not
#     "done", so the row runs again after the hold (the earlier attempt's logs are kept under time-stamped names);
#   - "needs" may be a string or a list (every path must exist);
#   - "<N>" in args = the first line of ready-N (a number); a row with <N> waits until ready-N holds one. A row with any
#     other unresolved <...> placeholder waits too (never launched);
#   - pass -LastLaunch / -GamesClosed (defaults are late on purpose; Agent 1 sets the real ones);
#   - run-2 task 2: a row with "toypad":true also starts build\agent3\toypad\toypad_sidecar.py (decision 1, user 17:27:
#     the virtual Batman/Gandalf/Wyldstyle tags go in through the game's 127.0.0.1:9191 listener, memory only, path
#     length 0; logs\<id>.sidecar.out/err.txt and <run>\toypad-events.csv); optional "toypad_mark" (an input.csv mark
#     that triggers the placing instead of the all-pads-white LED line) and "toypad_delay" (s, default 2); optional
#     "toypad_then_mark" (+ "toypad_then_delay" s, "toypad_then_action" replace|remove|place) for a second action;
#   - run-2 task 2: a row with "matrix":"<json>" (+ optional "matrix_args":[...]) runs bench\agent8\run\run-matrix.ps1
#     -Matrix <json> -NoPrompt -OutDir build\agent3\runs\<id>-<yyyyMMdd-HHmm> <matrix_args> instead of run-game
#     (FUNCTIONAL ONLY: REPIN.md section 3's boot check and 4-run matrix, W6 G3's -Quick pass). Agent 1 (20:37): every
#     functional run-matrix use passes -OutDir under build\agent3\runs, never build\agent8\matrix (a new folder there
#     trips the hold manager). holdwatch-m.ps1 runs beside it (stops run-matrix and its games if the HOLD file appears).
# queue.jsonl: one JSON object per line ('#' lines ignored):
#   {"id":"s4b01","est":265,"needs":["build\\agent3\\s4b\\ready-s4b-off"],"args":["-BinDir","...","-Tag","..."]}
# The first entry that is not done and whose needs exist runs; entries still waiting are passed over, not dropped.
# One game at a time (also waits while any legodimensions process runs). Never launches at or after -LastLaunch, nor
# when now + est would pass -GamesClosed (recorded as skipped). A STOP file ends the queue before the next launch.
param(
    [string]$LastLaunch = '23:30:00',
    [string]$GamesClosed = '23:45:00',
    # task #23 (Agent 1, 11-23 05:45): before each row, no build or other heavy process may run (QuietReason)
    [int]$QuietCpuPct = 20,
    [int]$QuietSampleSec = 5
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..\..')).Path
Set-Location $repo
$queue = Join-Path $here 'queue.jsonl'
$state = Join-Path $here 'queue-state.jsonl'
$stop = Join-Path $here 'STOP'
$pause = Join-Path $here 'PAUSE'
$hold = Join-Path $repo 'perf-notes\WINDOW-HOLD.txt'
$readyN = Join-Path $here 'ready-N'
$logs = Join-Path $here 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$runsRoot = Join-Path $repo 'build\agent3\runs'
$attach = Join-Path $repo 'build\agent3\s4a\attach.ps1'
$holdwatch = Join-Path $here 'holdwatch.ps1'
$holdwatchM = Join-Path $here 'holdwatch-m.ps1'
$runMatrix = Join-Path $repo 'bench\agent8\run\run-matrix.ps1'
# Get-ActiveRunners (harness\guard.ps1): run-game.ps1 refuses (exit 2) while an Agent 8 runner is active, so the queue
# waits for none first. 20:57 run 2: s4bL0 was refused by a short-lived runner process (pid 8152) and recorded as done.
. (Join-Path $repo 'harness\guard.ps1')
function Say([string]$m) {
    # also to logs\queue.out.txt (build\agent3\s4b\wait-event.ps1 reads it)
    $l = (Get-Date -Format 'HH:mm:ss') + ' ' + $m; Write-Host $l
    try { Add-Content -LiteralPath (Join-Path $logs 'queue.out.txt') -Value $l -Encoding UTF8 } catch { }
}
function Rec($o) { Add-Content -LiteralPath $state -Value ($o | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8 }
function Held { (Test-Path -LiteralPath $hold) -or (Test-Path -LiteralPath $pause) }
function Keep([string]$p) {
    # a file from an earlier (aborted) attempt of the same row: keep it under a time-stamped name
    if (Test-Path -LiteralPath $p) {
        $nn = (Split-Path -Leaf $p) -replace '\.txt$', ('.' + (Get-Date -Format 'HHmmss') + '.txt')
        try { Rename-Item -LiteralPath $p -NewName $nn } catch { Say "could not rename $p`: $($_.Exception.Message)" }
    }
}
function ReadN {
    if (-not (Test-Path -LiteralPath $readyN)) { return $null }
    $v = ([string](Get-Content -LiteralPath $readyN -TotalCount 1)).Trim()
    if ($v -match '^\d+$') { return $v }
    return $null
}
# task #23 (Agent 1, 11-23 05:45): quiet-host gate, checked right before every launch. QuietReason returns '' when the
# host is quiet, else the reason; $script:quietTxt keeps the last measurement (logs\<id>.quiet.txt at launch).
# Busy = any build process, any check script, or total CPU (Processor(_Total) % Processor Time, averaged over
# -QuietSampleSec s) above -QuietCpuPct. The per-process list covers my user's processes only (top 5 shown).
$buildNames = '^(clang|clang\+\+|clang-cl|cl|ninja|link|lld-link|cmake|msbuild|devenv|cc1plus|mspdbsrv)$'
$script:quietTxt = ''
function QuietReason {
    $b = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match $buildNames })
    if ($b.Count) { return ('build processes: ' + (@($b | Group-Object ProcessName | ForEach-Object { "$($_.Name) x$($_.Count)" }) -join ', ')) }
    $chk = @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 's4b_check|p2c_check|logdiff|dumpstacks|native3_boot_check|check_n_rows' })
    if ($chk.Count) { return ('check scripts running: pid ' + (@($chk | ForEach-Object { [string]$_.ProcessId }) -join ', ')) }
    $before = @{}
    foreach ($p in Get-Process -ErrorAction SilentlyContinue) { if ($null -ne $p.CPU) { $before[$p.Id] = $p.CPU } }
    $t0 = Get-Date; $tot = $null
    try {
        $cs = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples $QuietSampleSec -ErrorAction Stop).CounterSamples
        $tot = ($cs | Measure-Object -Property CookedValue -Average).Average
    } catch { Start-Sleep -Seconds $QuietSampleSec }
    $dt = ((Get-Date) - $t0).TotalSeconds; $nc = [Environment]::ProcessorCount; $procs = @()
    foreach ($p in Get-Process -ErrorAction SilentlyContinue) {
        if ($null -ne $p.CPU -and $before.ContainsKey($p.Id)) {
            $procs += [pscustomobject]@{ n = $p.ProcessName; id = $p.Id; pct = ($p.CPU - $before[$p.Id]) / $dt / $nc * 100 }
        }
    }
    $sum = ($procs | Measure-Object -Property pct -Sum).Sum
    $src = 'Processor(_Total)'
    if ($null -eq $tot) { $tot = $sum; $src = 'my-user processes (counter failed)' }
    $top = @($procs | Sort-Object pct -Descending | Select-Object -First 5 | ForEach-Object { '{0}({1}) {2:0.0}%' -f $_.n, $_.id, $_.pct }) -join ', '
    $script:quietTxt = '{0} quiet check: build processes 0, check scripts 0, total CPU {1:0.0}% ({2}) over {3:0} s, limit {4}%; my-user processes {5:0.0}%; top: {6}' -f `
        (Get-Date -Format 'HH:mm:ss'), $tot, $src, $dt, $QuietCpuPct, $sum, $top
    if ($tot -gt $QuietCpuPct) { return "busy host: $script:quietTxt" }
    return ''
}
$ll = [datetime]::Today.Add([timespan]::Parse($LastLaunch))
$gc = [datetime]::Today.Add([timespan]::Parse($GamesClosed))
Say "s4b-queue: last launch $LastLaunch, games closed $GamesClosed; queue $queue"
$lastWait = ''
while ($true) {
    if (Test-Path -LiteralPath $stop) { Say 'STOP file: queue ends'; break }
    if (Held) {
        if ($lastWait -ne 'hold') { Say 'HOLD or PAUSE file: no launch; waiting'; $lastWait = 'hold' }
        Start-Sleep -Seconds 5; continue
    }
    $now = Get-Date
    if ($now -ge $ll) { Say "past the last launch $LastLaunch`: queue ends"; break }
    $done = @()
    if (Test-Path -LiteralPath $state) {
        $done = @(Get-Content -LiteralPath $state | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } |
            Where-Object { -not $_.aborted } | ForEach-Object { $_.id })
    }
    $n = ReadN
    $next = $null; $nextArgs = $null; $waiting = @()
    if (Test-Path -LiteralPath $queue) {
        foreach ($line in Get-Content -LiteralPath $queue) {
            $t = $line.Trim(); if (-not $t -or $t.StartsWith('#')) { continue }
            $e = $t | ConvertFrom-Json
            if ($done -contains $e.id) { continue }
            if ($e.unless -and (Test-Path -LiteralPath (Join-Path $repo $e.unless))) {
                Say "DROP $($e.id): $($e.unless) exists"; Rec ([ordered]@{ id = $e.id; skipped = "unless $($e.unless)"; at = $now.ToString('HH:mm:ss') })
                $done += $e.id; continue
            }
            $miss = @(@($e.needs) | Where-Object { $_ -and -not (Test-Path -LiteralPath (Join-Path $repo $_)) })
            if ($miss.Count) { $waiting += $e.id; continue }
            $a = @($e.args | ForEach-Object { [string]$_ })
            if (($a -join ' ').Contains('<N>')) {
                if (-not $n) { $waiting += "$($e.id)(N)"; continue }
                $a = @($a | ForEach-Object { $_.Replace('<N>', $n) })
            }
            if (($a -join ' ') -cmatch '<[A-Z0-9-]+>') { $waiting += "$($e.id)(placeholder)"; continue }
            $next = $e; $nextArgs = $a; break
        }
    }
    if (-not $next) {
        $w = $waiting -join ','
        if ($w -ne $lastWait) { Say "idle; waiting for: [$w]"; $lastWait = $w }
        Start-Sleep -Seconds 5; continue
    }
    if ($now.AddSeconds([double]$next.est) -gt $gc) {
        Say "SKIP $($next.id): est $($next.est) s would end after $GamesClosed"
        Rec ([ordered]@{ id = $next.id; skipped = "est $($next.est) s past $GamesClosed"; at = $now.ToString('HH:mm:ss') }); continue
    }
    if (Get-Process legodimensions -ErrorAction SilentlyContinue) {
        if ($lastWait -ne 'game') { Say "a game is running; waiting (next: $($next.id))"; $lastWait = 'game' }
        Start-Sleep -Seconds 3; continue
    }
    $act = @(Get-ActiveRunners)
    if ($act.Count) {
        if ($lastWait -ne 'runner') { Say "a timing/boot runner is active ($($act -join '; ')); waiting (next: $($next.id))"; $lastWait = 'runner' }
        Start-Sleep -Seconds 5; continue
    }
    $qr = QuietReason   # task #23: no build or other heavy process (takes -QuietSampleSec s)
    if ($qr) {
        if ($lastWait -ne 'quiet') { Say "host not quiet ($qr); waiting (next: $($next.id))"; $lastWait = 'quiet' }
        Start-Sleep -Seconds 15; continue
    }
    if (Get-Process legodimensions -ErrorAction SilentlyContinue) { continue }   # one appeared during the sample
    if (Held) { continue }   # the last HOLD/PAUSE check, right before the launch
    $lastWait = ''
    $id = [string]$next.id
    $a = $nextArgs
    $ti = [array]::IndexOf($a, '-Tag'); $tag = if ($ti -ge 0) { $a[$ti + 1] } else { 'run' }
    $marker = Join-Path $logs "$id.hold-abort.txt"
    foreach ($f in @('run-game', 'attach.out', 'attach.err', 'holdwatch.out', 'holdwatch.err', 'hold-abort', 'sidecar.out', 'sidecar.err', 'run-matrix', 'run-matrix.err', 'quiet')) { Keep (Join-Path $logs "$id.$f.txt") }
    try { Set-Content -LiteralPath (Join-Path $logs "$id.quiet.txt") -Value $script:quietTxt -Encoding UTF8 } catch { }
    Say "quiet host before $id`: $script:quietTxt"
    $t0 = Get-Date
    if ($next.matrix) {
        $od = 'build\agent3\runs\' + $id + '-' + $t0.ToString('yyyyMMdd-HHmm')
        $ma = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $runMatrix, '-Matrix', [string]$next.matrix, '-NoPrompt', '-OutDir', $od) +
            @(@($next.matrix_args) | Where-Object { $_ } | ForEach-Object { [string]$_ })
        $mshow = @($ma | Select-Object -Skip 5)
        Say "LAUNCH $id`: run-matrix $($mshow -join ' ')"
        $mp = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $logs "$id.run-matrix.txt") `
            -RedirectStandardError (Join-Path $logs "$id.run-matrix.err.txt") -ArgumentList $ma
        $null = $mp.Handle   # keeps the handle so ExitCode is readable after the exit
        $hw = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $logs "$id.holdwatch.out.txt") `
            -RedirectStandardError (Join-Path $logs "$id.holdwatch.err.txt") `
            -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $holdwatchM, '-Root', $od, '-Marker', $marker, '-MatrixPid', [string]$mp.Id)
        $mp.WaitForExit()
        $ec = $null; try { $ec = $mp.ExitCode } catch { }
        if (-not $hw.WaitForExit(15000)) { try { $hw.Kill() } catch { } }
        $t1 = Get-Date
        $r = [ordered]@{ id = $id; exit = $ec; matrix_out = $od; start = $t0.ToString('HH:mm:ss'); end = $t1.ToString('HH:mm:ss'); args = $mshow }
        if (Test-Path -LiteralPath $marker) { $r['aborted'] = 'hold'; Say "ABORTED $id by the HOLD file; it runs again after the hold" }
        Say ("DONE {0}: run-matrix exit {1} in {2:0} s, out {3}" -f $id, $ec, ($t1 - $t0).TotalSeconds, $od)
        Rec $r
        continue
    }
    Say "LAUNCH $id`: run-game $($a -join ' ')"
    $tp = $null
    if ($next.toypad) {
        $si = [array]::IndexOf($a, '-Seconds'); $secs = if ($si -ge 0) { [int]$a[$si + 1] } else { 600 }
        $dl = if ($next.toypad_delay) { [string]$next.toypad_delay } else { '2' }
        $sa = @((Join-Path $repo 'build\agent3\toypad\toypad_sidecar.py'), '--runs-root', 'build\agent3\runs', '--tag', $tag,
            '--not-before', $t0.ToString('o'), '--timeout', [string]($secs + 240), '--delay', $dl)
        if ($next.toypad_mark) { $sa += @('--trigger-mark', [string]$next.toypad_mark, '--trigger-log', '""') }
        if ($next.toypad_then_mark) {
            # a second toypad action at an input.csv mark (sidecar --then-*): replace (default) = REMOVE x3 + LOAD x3
            $sa += @('--then-mark', [string]$next.toypad_then_mark)
            if ($next.toypad_then_delay) { $sa += @('--then-delay', [string]$next.toypad_then_delay) }
            if ($next.toypad_then_action) { $sa += @('--then-action', [string]$next.toypad_then_action) }
        }
        $tp = Start-Process python -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $logs "$id.sidecar.out.txt") `
            -RedirectStandardError (Join-Path $logs "$id.sidecar.err.txt") -ArgumentList $sa
        $null = $tp.Handle   # keeps the handle so ExitCode is readable after the exit
        Say "toypad sidecar for $id (pid $($tp.Id))"
    }
    $side = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $logs "$id.attach.out.txt") `
        -RedirectStandardError (Join-Path $logs "$id.attach.err.txt") `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $attach, '-NotBefore', $t0.ToString('o'))
    $hw = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $logs "$id.holdwatch.out.txt") `
        -RedirectStandardError (Join-Path $logs "$id.holdwatch.err.txt") `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $holdwatch, '-NotBefore', $t0.ToString('o'), '-Marker', $marker)
    # 'Continue' for the call: native builds print to stderr ("Plume D3D12 command state cache: disabled"), the game
    # inherits run-game's stderr, and with 'Stop' that first stderr line was a terminating NativeCommandError that
    # killed run-game at 14 s and left the game orphaned (S4a r5 attempt 1, 13:52).
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'harness\run-game.ps1') @a *> (Join-Path $logs "$id.run-game.txt")
    $ec = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $refused = $null
    if ($ec -eq 2) { $refused = Select-String -LiteralPath (Join-Path $logs "$id.run-game.txt") -Pattern '^REFUSED:' | Select-Object -First 1 }
    if ($refused) {
        # run-game refused to launch (a runner or a game appeared between the queue's checks and run-game's own): no game
        # ran, so stop the helpers now (the sidecar would wait for a run dir for -Seconds + 240 s) and run the row again
        foreach ($p in @($tp, $side, $hw)) { if ($p) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }
        Rec ([ordered]@{ id = $id; exit = $ec; aborted = 'refused'; start = $t0.ToString('HH:mm:ss'); end = (Get-Date).ToString('HH:mm:ss'); why = $refused.Line })
        Say "REFUSED $id by run-game ($($refused.Line)); it runs again"
        Start-Sleep -Seconds 20; continue
    }
    if (-not $side.WaitForExit(90000)) { Say "attach for $id still running 90 s after run-game; killing it"; try { $side.Kill() } catch { } }
    if (-not $hw.WaitForExit(30000)) { Say "holdwatch for $id still running 30 s after run-game; killing it"; try { $hw.Kill() } catch { } }
    $tpx = $null
    if ($tp) {
        if (-not $tp.WaitForExit(240000)) { Say "sidecar for $id still running 240 s after run-game; killing it"; try { $tp.Kill() } catch { } }
        try { $tpx = $tp.ExitCode } catch { }
    }
    $rd = Get-ChildItem -LiteralPath $runsRoot -Directory | Where-Object { $_.Name -like "*-$tag*" -and $_.CreationTime -ge $t0.AddSeconds(-2) } |
        Sort-Object CreationTime | Select-Object -Last 1
    $t1 = Get-Date
    $rn = if ($rd) { $rd.Name } else { $null }
    $r = [ordered]@{ id = $id; exit = $ec; run = $rn; start = $t0.ToString('HH:mm:ss'); end = $t1.ToString('HH:mm:ss'); args = $a }
    if ($tp) { $r['sidecar_exit'] = $tpx }
    if (Test-Path -LiteralPath $marker) { $r['aborted'] = 'hold'; Say "ABORTED $id by the HOLD file; it runs again after the hold" }
    Say ("DONE {0}: exit {1} in {2:0} s, run {3}" -f $id, $ec, ($t1 - $t0).TotalSeconds, $rn)
    Rec $r
}
