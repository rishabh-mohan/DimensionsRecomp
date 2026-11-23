# harness/route-report.ps1 - what an input-script run (harness/run-game.ps1 -InputScript) did, step by step.
# The game holds perf.csv unshared while it runs (rexglue-sdk core/perf/counter.cpp opens it with _wfopen_s), so on the
# real game the input script logs only perf.csv's size (perf_bytes) at each step. This maps every input.csv row to the
# scene at that point in the final perf.csv (median draw calls / vertices of the 30 frames before it; perf.csv is flushed
# every 60 rows, so it can lag by up to 60 frames), lists the game.log lines that appeared between rows, checks the pad counters,
# the B-gate fail lines (perf-notes/agent10-codegen-review.md, last section) and the exit sequence.
# Native builds leave perf.csv's draw/vertex columns at 0: then the scene is 'n<draws>' from the native frame metrics
# (frames.csv from run-game.ps1, native-frames.csv from Agent 8's runner; their 'frame' column is the perf.csv row).
# FUNCTIONAL ONLY: nothing here is a timing. Agent 10's build\agent10\bgate\logdiff.py compares devoff2 with devoffB.
#   powershell -NoProfile -ExecutionPolicy Bypass -File harness\route-report.ps1 -RunDir build\agent3\runs\<run> [-LogLines 6]
# Also writes <run>\route-report.txt. Exit code: 0 no problems, 1 problems listed under Checks, 2 not an -InputScript run.
param(
    [Parameter(Mandatory = $true)][string]$RunDir,
    [int]$LogLines = 6,                              # game.log lines shown per input.csv row (0: counts only)
    [string]$LogSkip = 'Toypad\[(Read|Write)\]',     # game.log lines counted but not shown
    [int]$Bucket = 5                                 # seconds per bucket in the scene timeline
)
$ErrorActionPreference = 'Stop'
$inv = [Globalization.CultureInfo]::InvariantCulture
$out = New-Object 'System.Collections.Generic.List[string]'
function Say([string]$s = '') { $out.Add($s); Write-Host $s }
function Prop($o, [string]$n) { if ($null -ne $o -and $o.PSObject.Properties[$n]) { return $o.$n }; return $null }
function Trunc([string]$s, [int]$n) { if ($s.Length -le $n) { return $s }; return $s.Substring(0, $n) + '...' }
function Median([System.Collections.Generic.List[long]]$l, [int]$from, [int]$to) {
    $k = $to - $from
    if ($k -le 0) { return -1 }
    $c = New-Object 'long[]' $k
    $l.CopyTo($from, $c, 0, $k)
    [Array]::Sort($c)
    return $c[[int][math]::Floor($k / 2)]
}
function Top($h) { return ($h.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1).Key }

if (-not (Test-Path -LiteralPath $RunDir -PathType Container)) { Write-Host "route-report: no such run dir: $RunDir"; exit 2 }
$run = (Resolve-Path -LiteralPath $RunDir).Path
$inputCsv = Join-Path $run 'input.csv'
if (-not (Test-Path -LiteralPath $inputCsv)) { Write-Host "route-report: $run has no input.csv (not an -InputScript run)"; exit 2 }
$jsonPath = Join-Path $run 'run.json'
$info = if (Test-Path -LiteralPath $jsonPath) { Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json } else { $null }
$in = Prop $info 'input_script'
$rows = @(Import-Csv -LiteralPath $inputCsv)
$logPath = Join-Path $run 'game.log'
$log = if (Test-Path -LiteralPath $logPath) { [IO.File]::ReadAllLines($logPath) } else { @() }

# perf.csv: end offset, cumulative frame time, draw calls and vertices of every complete frame row
$ends = New-Object 'System.Collections.Generic.List[long]'
$cum = New-Object 'System.Collections.Generic.List[double]'
$dc = New-Object 'System.Collections.Generic.List[long]'
$vx = New-Object 'System.Collections.Generic.List[long]'
$perfPath = Join-Path $run 'perf.csv'
if (Test-Path -LiteralPath $perfPath) {
    $bytes = [IO.File]::ReadAllBytes($perfPath)
    $pos = 0; $lineNo = 0; $t = 0.0
    while ($pos -lt $bytes.Length) {
        $nl = [Array]::IndexOf($bytes, [byte]10, $pos)
        if ($nl -lt 0) { break }   # a last line without its newline is not a complete row
        if ($lineNo -gt 0) {
            $f = [Text.Encoding]::ASCII.GetString($bytes, $pos, $nl - $pos).TrimEnd("`r").Split(',')
            $d = [long]0; $v = [long]0; $us = 0.0
            if ($f.Count -ge 5 -and [long]::TryParse($f[2], [ref]$d)) {
                [void][double]::TryParse($f[0], [Globalization.NumberStyles]::Float, $inv, [ref]$us)
                [void][long]::TryParse($f[4], [ref]$v)
                $t += $us / 1e6
                $ends.Add([long]($nl + 1)); $cum.Add($t); $dc.Add($d); $vx.Add($v)
            }
        }
        $lineNo++
        $pos = $nl + 1
    }
}

# Native builds: perf.csv's draw/vertex columns stay 0, and the per-frame draw calls are in the native frame metrics
# (LEGO_NATIVE_FRAME_METRICS). Their 'frame' column is the 1-based perf.csv row; it starts at 2, because the first present
# has no interval (build\agent8\runs\0256-native3: interval_ms against perf.csv frame time gives r = 0.999 at that offset
# and 0.20 with row i = row i). Without a 'frame' column, row i stands for perf.csv row i.
$native = $false; $sceneSrc = 'perf.csv draw calls/vertices'
if ($dc.Count -and $dc.TrueForAll([Predicate[long]] { param($x) $x -eq 0 })) {
    foreach ($nf in @('frames.csv', 'native-frames.csv')) {
        $nfPath = Join-Path $run $nf
        if (-not (Test-Path -LiteralPath $nfPath)) { continue }
        $nfl = [IO.File]::ReadAllLines($nfPath)
        if ($nfl.Count -lt 2) { continue }
        $hdr = $nfl[0].Split(',')
        $di = [Array]::IndexOf($hdr, 'draw_calls')
        if ($di -lt 0) { continue }
        $fi = [Array]::IndexOf($hdr, 'frame')
        for ($k = 0; $k -lt $dc.Count; $k++) { $dc[$k] = -1 }
        $hit = 0
        for ($k = 1; $k -lt $nfl.Count; $k++) {
            $f = $nfl[$k].Split(','); $d = [long]0; $fr = [long]$k
            if ($f.Count -le $di -or -not [long]::TryParse($f[$di], [ref]$d)) { continue }
            if ($fi -ge 0 -and -not [long]::TryParse($f[$fi], [ref]$fr)) { continue }
            if ($fr -ge 1 -and $fr -le $dc.Count) { $dc[[int]($fr - 1)] = $d; $hit++ }
        }
        if ($dc.Count -gt 1 -and $dc[0] -lt 0) { $dc[0] = $dc[1] }   # frame 1 has no metrics row
        $native = $true
        $how = if ($fi -ge 0) { "by its 'frame' column" } else { 'by row index' }
        $sceneSrc = "$nf draw calls (native build: perf.csv has none; $hit of $($dc.Count) perf.csv rows matched $how)"
        break
    }
}
function SceneKey([long]$d, [long]$v) { if ($native) { if ($d -lt 0) { return 'n?' }; return "n$d" }; return "$d/$v" }

# complete frame rows on disk at an input.csv row: perf_bytes when the game held perf.csv, else the rows read live
function RowsAt($r) {
    $pb = Prop $r 'perf_bytes'
    if ($null -ne $pb -and [long]$pb -gt 0) {
        $i = $ends.BinarySearch([long]$pb)
        if ($i -ge 0) { return $i + 1 }
        return (-bnot $i)
    }
    $pr = [long](Prop $r 'perf_rows')
    if ($pr -gt 0) { return [int][math]::Min($pr, $ends.Count) }
    return 0
}

Say "route-report: $run"
Say ('  tag {0}; bin {1}; started {2}; pid {3}' -f (Prop $info 'tag'), (Prop $info 'bin_dir'), (Prop $info 'started'), (Prop $info 'pid'))
Say ('  script {0} ({1} steps, sha256 {2})' -f (Prop $in 'script'), (Prop $in 'steps_total'), (Prop $in 'script_sha256'))
Say ''
Say "  scene source: $sceneSrc"
Say ''
Say 'Steps (t = s since launch; perf = s of frame time since the first frame; scene = median draw calls/vertices of the'
Say '30 frames on disk at that point; pad/keys = XInputGetState calls / keystroke events since the previous row):'
$prevLog = 0; $prevReads = 0; $prevKeys = 0
$marks = New-Object System.Collections.ArrayList
foreach ($r in $rows) {
    $n = RowsAt $r
    $sd = [long]$r.scene_draws; $sv = [long]$r.scene_vertices
    if ($sd -lt 0 -and $n -gt 0) { $lo = [math]::Max(0, $n - 30); $sd = Median $dc $lo $n; $sv = Median $vx $lo $n }
    $scene = if ($sd -ge 0) { SceneKey $sd $sv } else { '-' }
    $pt = if ($n -gt 0) { $cum[$n - 1].ToString('F1', $inv) } else { '-' }
    $hi = [math]::Min([int]$r.log_lines, $log.Count)
    $new = New-Object 'System.Collections.Generic.List[string]'
    for ($k = $prevLog; $k -lt $hi; $k++) { $new.Add($log[$k]) }
    $shown = @($new | Where-Object { $_ -notmatch $LogSkip })
    $reads = [long]$r.pad_reads; $keys = [long]$r.key_events
    Say ('{0,7} L{1,-3} {2,-16} {3,-14} -> {4,-24} | pad +{5,-4} keys +{6,-2} | perf {7,6} scene {8,-10} | log +{9}' -f `
        $r.t_s, $r.line, $r.cmd, (Trunc $r.args 14), (Trunc $r.result 24), ($reads - $prevReads), ($keys - $prevKeys), $pt, $scene, $new.Count)
    if ($LogLines -gt 0) {
        foreach ($s in @($shown | Select-Object -First $LogLines)) { Say ('          | ' + (Trunc $s 150)) }
        if ($shown.Count -gt $LogLines) { Say ('          | ... {0} more' -f ($shown.Count - $LogLines)) }
    }
    if ($r.cmd -eq 'mark') { [void]$marks.Add(@($r.args, $r.t_s, $pt, $scene)) }
    $prevLog = [math]::Max($prevLog, $hi); $prevReads = $reads; $prevKeys = $keys
}

Say ''
Say 'Marks (compare devoff2 and devoffB mark by mark):'
foreach ($m in $marks) { Say ('  {0,-14} t {1,7}  perf {2,6}  scene {3}' -f $m[0], $m[1], $m[2], $m[3]) }

Say ''
Say "Scene timeline ($sceneSrc; perf.csv frame time in $Bucket-s buckets, most common scene; runs of equal buckets merged):"
if ($cum.Count) {
    $b = -1; $tally = @{}; $runs = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $cum.Count; $i++) {
        $k = [int][math]::Floor($cum[$i] / $Bucket)
        if ($k -ne $b) { if ($b -ge 0) { [void]$runs.Add(@($b, (Top $tally))) }; $b = $k; $tally = @{} }
        $key = SceneKey $dc[$i] $vx[$i]
        $tally[$key] = 1 + [int]$tally[$key]
    }
    [void]$runs.Add(@($b, (Top $tally)))
    $i = 0
    while ($i -lt $runs.Count) {
        $j = $i
        while ($j + 1 -lt $runs.Count -and $runs[$j + 1][1] -eq $runs[$i][1]) { $j++ }
        Say ('  {0,5}-{1,-5} s  {2}' -f ($runs[$i][0] * $Bucket), (($runs[$j][0] + 1) * $Bucket), $runs[$i][1])
        $i = $j + 1
    }
    Say ('  {0} frame rows, {1:F1} s of frame time' -f $cum.Count, $cum[$cum.Count - 1])
} else { Say '  (no perf.csv frame rows)' }

Say ''
Say 'Checks:'
$problems = New-Object 'System.Collections.Generic.List[string]'
function Verdict([string]$name, $ok, [string]$detail) {
    $tag = if ($null -eq $ok) { 'info' } elseif ($ok) { 'ok  ' } else { 'FAIL' }
    Say ('  {0} {1}: {2}' -f $tag, $name, $detail)
    if ($false -eq $ok) { $problems.Add($name) }
}
$exitCode = Prop $info 'exit_code'
Verdict 'exit' ($exitCode -eq 0 -and -not (Prop $info 'exited_early')) ('exit {0} ({1}); close {2} in {3} s; elapsed {4} s; exited_early {5}' -f `
    $exitCode, (Prop $info 'exit_code_hex'), (Prop $info 'close_method'), (Prop $info 'close_seconds'), (Prop $info 'elapsed_s'), (Prop $info 'exited_early'))
$dumps = @(Prop $info 'dumps' | Where-Object { $_ }); $crashEv = @(Prop $info 'crash_events' | Where-Object { $_ })
Verdict 'no crash' (-not (Prop $info 'wer_seen') -and $dumps.Count -eq 0 -and $crashEv.Count -eq 0) ('wer_seen {0}; crash_events {1}; dumps {2}' -f (Prop $info 'wer_seen'), $crashEv.Count, $dumps.Count)
$steps = '{0}/{1} done; last "{2}"; stopped by script {3}; timeouts {4} {5}; error {6}' -f (Prop $in 'steps_done'), (Prop $in 'steps_total'), `
    (Prop $in 'last_step'), (Prop $in 'stopped_by_script'), (Prop $in 'timeouts'), (Prop $in 'timeout_lines'), (Prop $in 'error')
Verdict 'script ran to the end' ($null -ne $in -and (Prop $in 'steps_done') -eq (Prop $in 'steps_total') -and (Prop $in 'stopped_by_script') -and -not (Prop $in 'error')) $steps
$from = [string](Prop $in 'dll_loaded_from')
Verdict 'pad DLL loaded by the game from the run dir' ($null -ne $in -and (Prop $in 'dll_loaded_by_pid') -eq (Prop $info 'pid') -and $from.StartsWith($run, [StringComparison]::OrdinalIgnoreCase)) `
    ('pid {0} (game {1}); {2}; maps {3}' -f (Prop $in 'dll_loaded_by_pid'), (Prop $info 'pid'), $from, (Prop $in 'dll_maps'))
Verdict 'game polled the pad' ([long](Prop $in 'pad_reads') -gt 0) ('XInputGetState {0} (with input {1}); XInputGetKeystroke {2} (events {3}); caps {4}; set_state {5}' -f `
    (Prop $in 'pad_reads'), (Prop $in 'pad_active_reads'), (Prop $in 'key_calls'), (Prop $in 'key_events'), (Prop $in 'caps_calls'), (Prop $in 'set_state_calls'))
Verdict 'perf.csv' $null ('held unshared by the game while it ran: {0}; {1} bytes at the end; {2} frame rows' -f (Prop $in 'perf_locked'), (Prop $in 'perf_bytes_at_end'), $cum.Count)
$nim = @($log | Where-Object { $_ -match 'not in any registered module' })
Verdict 'no "not in any registered module" lines' ($nim.Count -eq 0) ('{0} lines{1}' -f $nim.Count, $(if ($nim.Count) { ': ' + (Trunc $nim[0] 120) } else { '' }))
$wd = @($log | Where-Object { $_ -match '(?i)watchdog|hang detected|STUCK-LOCK|Minidump written|\[FATAL\]' })
Verdict 'no watchdog/hang lines' ($wd.Count -eq 0) ('{0} lines{1}' -f $wd.Count, $(if ($wd.Count) { ': ' + (Trunc $wd[0] 120) } else { '' }))
$cg = @($log | Where-Object { $_ -match 'crash guard:' })
$kinds = @($cg | ForEach-Object { ($_ -replace '^.*?crash guard:\s*', '') -replace '0x[0-9A-Fa-f]+', '0x#' -replace '\d+', '#' } | Group-Object | ForEach-Object { '{0} x{1}' -f (Trunc $_.Name 60), $_.Count })
Verdict 'crash guard lines (the gate compares kinds with devoff2)' $null ('{0} lines; kinds: {1}' -f $cg.Count, $(if ($kinds.Count) { $kinds -join '; ' } else { 'none' }))
$un = @($log | Where-Object { $_ -match '(?i)unimplemented' })
Verdict 'unimplemented-instruction lines (the gate compares the count with devoff2)' $null ('{0} lines' -f $un.Count)
$seq = @('Window closing, shutting down', 'Execution complete', 'Title terminated; hard-exiting process.')
$at = @($seq | ForEach-Object { $s = $_; $hit = -1; for ($k = 0; $k -lt $log.Count; $k++) { if ($log[$k].Contains($s)) { $hit = $k; break } }; $hit })
$inOrder = ($at -notcontains -1) -and $at[0] -lt $at[1] -and $at[1] -lt $at[2]
Verdict 'exit sequence in game.log' $inOrder ('line numbers {0} (Window closing / Execution complete / Title terminated)' -f (($at | ForEach-Object { if ($_ -ge 0) { $_ + 1 } else { 'missing' } }) -join ', '))
Say ''
if ($problems.Count) { Say ('PROBLEMS: ' + ($problems -join '; ')) } else { Say 'No problems: the route ran without the user.' }
[IO.File]::WriteAllLines((Join-Path $run 'route-report.txt'), $out, (New-Object System.Text.UTF8Encoding $false))
if ($problems.Count) { exit 1 }
exit 0
