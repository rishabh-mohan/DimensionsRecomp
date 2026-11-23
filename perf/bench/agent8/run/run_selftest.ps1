# Self-test for run-timing.ps1 and frame_summary.py. Prints PASS/FAIL/SKIP per check and a total; exit 1 on FAIL.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run_selftest.ps1 [-RealCsv build\agent8\runs\1928-first\perf.csv] [-SkipE2E]
# (a) frame_summary.py on synthetic perf.csv files with known frame times
# (b) frame_summary.py on a real perf.csv (parse + count consistency only; frame times there are not valid timing)
# (c) run-timing.ps1 end to end against a FAKE legodimensions.exe (built here with csc into
#     build\agent8\run-selftest\fake-bin), once as a timing run and once with -Profile. Never starts the real game.
# (d) native-frames.csv parsing, then run-matrix.ps1 against the same fake exe: field validation, -PlanOnly, a -Quick
#     2-arm x 2-repeat matrix (cold run, menu, driver, <run>, triggers), a native seed_cache chain (selftest\selftest_matrix.ps1)
param(
    [string]$RealCsv = 'build\agent8\runs\1928-first\perf.csv',
    [switch]$SkipE2E
)
$ErrorActionPreference = 'Continue'
Set-StrictMode -Version 2
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$fs = Join-Path $PSScriptRoot 'frame_summary.py'
$root = Join-Path $repo 'build\agent8\run-selftest'
$scratch = Join-Path $root 'scratch'
New-Item -ItemType Directory -Force -Path $scratch | Out-Null
$script:pass = 0; $script:fail = 0; $script:skip = 0
function Check([string]$Name, [bool]$Ok, [string]$Detail = '') {
    if ($Ok) { $script:pass++; "PASS $Name $Detail" } else { $script:fail++; "FAIL $Name $Detail" }
}
function Skip([string]$Name, [string]$Why) { $script:skip++; "SKIP $Name ($Why)" }
function Near($A, $B, [double]$Tol) { return ($null -ne $A) -and ([math]::Abs([double]$A - [double]$B) -le $Tol) }
function Summ([string]$Csv, [string[]]$A = @()) {
    $json = Join-Path $scratch ('fs-' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.json')
    $out = & python $fs $Csv @A --json $json 2>&1 | Out-String
    $code = $LASTEXITCODE
    $obj = $null
    if (Test-Path -LiteralPath $json) { $obj = Get-Content -LiteralPath $json -Raw | ConvertFrom-Json; Remove-Item -LiteralPath $json }
    return [pscustomobject]@{ code = $code; out = $out; r = $obj }
}
function Stats-Of([long[]]$V) {
    $s = @($V | Where-Object { $_ -gt 0 } | Sort-Object)
    $n = $s.Count
    $nr = { param($num, $den) $k = [long][math]::Floor(($num * $n + $den - 1) / $den); $k = [math]::Max(1, [math]::Min($n, $k)); $s[$k - 1] / 1000.0 }
    return [pscustomobject]@{ frames = $n; median = (& $nr 1 2); p99 = (& $nr 99 100); p999 = (& $nr 999 1000)
        over33 = @($s | Where-Object { $_ -gt 33000 }).Count; over100 = @($s | Where-Object { $_ -gt 100000 }).Count
        sum_s = (($s | Measure-Object -Sum).Sum) / 1e6 }
}
$hdr = 'frame_time_us,fps,draw_calls,command_buffer_stalls,vertices_processed,xma_frames_decoded,audio_frame_latency_us,buffer_queue_depth,functions_dispatched,interrupt_dispatches,active_threads,apc_queue_depth,critical_region_contentions,texture_cache_hits,texture_cache_misses,pipeline_cache_hits,pipeline_cache_misses'
function Row([long]$Ft) { return "$Ft,60,100,0,0,0,0,0,0,0,42,0,0,0,0,0,0" }
function SynFt([long]$I) { if ($I % 100 -eq 99) { 120000 } elseif ($I % 100 -eq 49) { 40000 } elseif ($I % 10 -eq 5) { 20000 } else { 16000 } }
function FakeFt([long]$I) { if ($I % 50 -eq 49) { 120000 } elseif ($I % 50 -eq 24) { 40000 } elseif ($I % 5 -eq 2) { 20000 } else { 16000 } }

"=== run_selftest $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
'--- (a) synthetic perf.csv ---'
$syn = Join-Path $scratch 'synthetic.csv'
$sb = New-Object Text.StringBuilder
[void]$sb.Append($hdr + "`r`n")
$ends = New-Object 'System.Collections.Generic.List[long]'
for ($i = 0; $i -lt 1000; $i++) { [void]$sb.Append((Row (SynFt $i)) + "`r`n"); $ends.Add($sb.Length) }
[IO.File]::WriteAllText($syn, $sb.ToString(), (New-Object Text.ASCIIEncoding))

$x = Summ $syn
$r = $x.r
Check 'a1 whole file parses' ($x.code -eq 0 -and $r.header_ok -and $r.rows_total -eq 1000 -and -not $r.truncated_last_line -and $r.bad_rows -eq 0) "rows=$($r.rows_total)"
Check 'a2 whole-file stats exact' ($r.frames -eq 1000 -and $r.median_ms -eq 16.0 -and $r.p99_ms -eq 40.0 -and $r.p99_9_ms -eq 120.0 -and $r.over_33ms -eq 20 -and $r.over_100ms -eq 10 -and (Near $r.window_s 17.68 1e-9) -and (Near $r.mean_fps (1000 / 17.68) 0.001)) "median=$($r.median_ms) p99=$($r.p99_ms) p99.9=$($r.p99_9_ms) >33=$($r.over_33ms) >100=$($r.over_100ms) s=$($r.window_s) fps=$($r.mean_fps)"
$x = Summ $syn @('--skip-rows', '100', '--rows', '100'); $r = $x.r
Check 'a3 rows window 100..199 exact' ($r.window.first_row -eq 100 -and $r.frames -eq 100 -and $r.median_ms -eq 16.0 -and $r.p99_ms -eq 40.0 -and $r.p99_9_ms -eq 120.0 -and $r.over_33ms -eq 2 -and $r.over_100ms -eq 1 -and (Near $r.window_s 1.768 1e-9)) "first=$($r.window.first_row) n=$($r.frames) >33=$($r.over_33ms) >100=$($r.over_100ms) s=$($r.window_s)"
$b0 = $ends[99] + 5; $b1 = $ends[199] + 3
$x = Summ $syn @('--start-bytes', "$b0", '--end-bytes', "$b1"); $r = $x.r
Check 'a4 byte marks mid-row -> rows 100..199' ($r.window.first_row -eq 100 -and $r.window.rows -eq 100 -and $r.window.rows_by_end_bytes -eq 100 -and $r.over_100ms -eq 1 -and (Near $r.window_s 1.768 1e-9)) "start=$b0 end=$b1 first=$($r.window.first_row) rows=$($r.window.rows)"
$x = Summ $syn @('--start-bytes', "$($ends[99])"); $r = $x.r
Check 'a5 byte mark exactly at a row end' ($r.window.first_row -eq 100 -and $r.window.rows -eq 900) "first=$($r.window.first_row) rows=$($r.window.rows)"
$x = Summ $syn @('--seconds', '1.0'); $r = $x.r
Check 'a6 seconds cut 1.0 s exact' ($r.window.rows -eq 60 -and $r.window.end_by -eq 'seconds' -and -not $r.window.short -and (Near $r.window_s 1.008 1e-9) -and $r.over_33ms -eq 1 -and $r.over_100ms -eq 0 -and $r.median_ms -eq 16.0 -and $r.p99_ms -eq 40.0 -and $r.p99_9_ms -eq 40.0) "rows=$($r.window.rows) s=$($r.window_s) p99.9=$($r.p99_9_ms)"
$x = Summ $syn @('--start-bytes', "$b0", '--seconds', '1.768', '--end-bytes', "$b1"); $r = $x.r
Check 'a7 start bytes + seconds + end-bytes cross-check' ($r.window.first_row -eq 100 -and $r.window.rows -eq 100 -and $r.window.end_bytes_minus_seconds_rows -eq 0) "rows=$($r.window.rows) diff=$($r.window.end_bytes_minus_seconds_rows)"
$x = Summ $syn @('--skip-seconds', '1.0', '--rows', '10'); $r = $x.r
Check 'a8 skip-seconds 1.0 -> first row 60' ($r.window.first_row -eq 60 -and $r.frames -eq 10) "first=$($r.window.first_row)"
$x = Summ $syn @('--skip-rows', '990', '--seconds', '5'); $r = $x.r
Check 'a9 seconds cut past EOF is flagged short' ($r.window.rows -eq 10 -and $r.window.short) "rows=$($r.window.rows) short=$($r.window.short)"
$ho = Join-Path $scratch 'header-only.csv'
[IO.File]::WriteAllText($ho, $hdr + "`r`n", (New-Object Text.ASCIIEncoding))
$x = Summ $ho @('--seconds', '5'); $r = $x.r
Check 'a10 header-only file' ($x.code -eq 0 -and $r.header_ok -and $r.rows_total -eq 0 -and $r.frames -eq 0 -and $null -eq $r.median_ms -and $r.window.short) "code=$($x.code) rows=$($r.rows_total) frames=$($r.frames)"
$tr = Join-Path $scratch 'truncated.csv'
$t = $hdr + "`r`n"; for ($i = 0; $i -lt 10; $i++) { $t += (Row 16000) + "`r`n" }; $t += '16000,60,1'
[IO.File]::WriteAllText($tr, $t, (New-Object Text.ASCIIEncoding))
$x = Summ $tr; $r = $x.r
Check 'a11 truncated last line dropped and flagged' ($x.code -eq 0 -and $r.rows_total -eq 10 -and $r.truncated_last_line -and $r.bad_rows -eq 0 -and $r.frames -eq 10) "rows=$($r.rows_total) truncated=$($r.truncated_last_line)"
$z = Join-Path $scratch 'zero-first.csv'
$t = $hdr + "`n" + (Row 0) + "`n"; for ($i = 0; $i -lt 4; $i++) { $t += (Row 20000) + "`n" }
[IO.File]::WriteAllText($z, $t, (New-Object Text.ASCIIEncoding))
$x = Summ $z; $r = $x.r
Check 'a12 LF file, zero first row left out of stats' ($r.rows_total -eq 5 -and $r.window.zero_rows -eq 1 -and $r.frames -eq 4 -and $r.median_ms -eq 20.0) "zero_rows=$($r.window.zero_rows) frames=$($r.frames)"
$x = Summ (Join-Path $scratch 'does-not-exist.csv')
Check 'a13 missing file -> exit 2' ($x.code -eq 2) "code=$($x.code)"

'--- (b) real perf.csv ---'
$real = if ([IO.Path]::IsPathRooted($RealCsv)) { $RealCsv } else { Join-Path $repo $RealCsv }
$readable = $false
if (Test-Path -LiteralPath $real) {
    try { $h = [IO.File]::Open($real, 'Open', 'Read', 'ReadWrite'); $h.Dispose(); $readable = $true } catch { }
}
if (-not (Test-Path -LiteralPath $real)) { Skip 'b real perf.csv' "not found: $real" }
elseif (-not $readable) { Skip 'b real perf.csv' "cannot open $real (game still running?)" }
else {
    $x = Summ $real; $r = $x.r
    "INFO real: $($r.file_bytes) B, $($r.rows_total) rows, newlines $($r.newlines), zero rows $($r.window.zero_rows), truncated $($r.truncated_last_line)"
    Check 'b1 real parses (17-field header, no bad rows)' ($x.code -eq 0 -and $r.header_ok -and $r.header_fields -eq 17 -and $r.bad_rows -eq 0 -and $r.rows_total -gt 0) "rows=$($r.rows_total)"
    $nlExpect = $r.rows_total + 1 + $r.bad_rows
    Check 'b2 real counts consistent (newlines = rows + header)' ($r.newlines -eq $nlExpect -and $r.frames -eq ($r.rows_total - $r.window.zero_rows) -and $r.window.rows -eq $r.rows_total) "newlines=$($r.newlines) expected=$nlExpect"
    Check 'b3 real first row is the zero (no previous swap)' ($r.window.zero_rows -ge 1) "zero_rows=$($r.window.zero_rows)"
    $x2 = Summ $real @('--skip-seconds', '60'); $r2 = $x2.r
    "INFO real after 60 s: frames $($r2.frames), median $($r2.median_ms) p99 $($r2.p99_ms) p99.9 $($r2.p99_9_ms) >33 $($r2.over_33ms) >100 $($r2.over_100ms) (Agent 8: 22.96 / 104.19 / 473.77 / 6906 / 245; NOT valid timing: locked desktop)"
    Check 'b4 real after 60 s agrees with Agent 8 counts (+-3) and median (+-0.1 ms)' ((Near $r2.over_33ms 6906 3) -and (Near $r2.over_100ms 245 3) -and (Near $r2.median_ms 22.96 0.1)) ''
    $x3 = Summ $real @('--start-bytes', '100000', '--seconds', '30', '--end-bytes', '400000'); $r3 = $x3.r
    Check 'b5 real byte-window slicing is consistent' ($x3.code -eq 0 -and $r3.window.first_row -gt 0 -and $r3.window_s -ge 30 -and $null -ne $r3.window.rows_by_end_bytes) "first=$($r3.window.first_row) rows=$($r3.window.rows) by_end=$($r3.window.rows_by_end_bytes)"
}

'--- (c) end to end against a fake exe ---'
if ($SkipE2E) { Skip 'c end-to-end' '-SkipE2E' }
else {
    $bin = Join-Path $root 'fake-bin'
    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    $src = Join-Path $PSScriptRoot 'selftest\fakegame_timing.cs'
    $exe = Join-Path $bin 'legodimensions.exe'
    $csc = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
    if (-not (Test-Path $exe) -or (Get-Item $src).LastWriteTime -gt (Get-Item $exe).LastWriteTime) {
        $cout = & $csc /nologo /target:winexe /optimize+ "/out:$exe" $src 2>&1 | Out-String
        Check 'c0 fake exe builds' ($LASTEXITCODE -eq 0 -and (Test-Path $exe)) $cout.Trim()
    } else { Check 'c0 fake exe up to date' $true '' }
    [IO.File]::WriteAllText((Join-Path $bin 'legodimensions.map'), " legodimensions (fake map for run_selftest.ps1)`r`n")
    $m = @('# fake bin for bench\agent8\run\run_selftest.ps1 (not the game)', "# name`tsize`tmtime`tsha256`tsource")
    foreach ($n in @('legodimensions.exe', 'legodimensions.map')) {
        $f = Get-Item (Join-Path $bin $n)
        $m += "$n`t$($f.Length)`t$($f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))`t$((Get-FileHash $f.FullName -Algorithm SHA256).Hash)`tbench\agent8\run\selftest\fakegame_timing.cs"
    }
    $m | Set-Content -LiteralPath (Join-Path $bin 'MANIFEST.txt') -Encoding ascii
    $runner = Join-Path $PSScriptRoot 'run-timing.ps1'
    $runs = Join-Path $root 'runs'

    # c1: timing run, warm-up 3 s, window 5 s
    $W = 3; $S = 5
    $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -BinDir $bin -Tag st-timing -Warmup $W -Seconds $S -RunsRoot $runs -MinFreeRamGB 0 -CloseTimeoutSec 15 2>&1 | Out-String
    $code = $LASTEXITCODE
    $out | Set-Content -LiteralPath (Join-Path $scratch 'e2e-timing.txt') -Encoding utf8
    $rd = if ($out -match 'run dir: (.+)') { $Matches[1].Trim() } else { $null }
    Check 'c1 timing run exit 0' ($code -eq 0 -and $null -ne $rd) "exit=$code run=$rd"
    if ($rd -and (Test-Path (Join-Path $rd 'run.json'))) {
        $j = Get-Content (Join-Path $rd 'run.json') -Raw | ConvertFrom-Json
        Check 'c2 run dir has proc.csv/run.json/summary.txt/frames.json' ((Test-Path (Join-Path $rd 'proc.csv')) -and (Test-Path (Join-Path $rd 'summary.txt')) -and (Test-Path (Join-Path $rd 'frames.json'))) ''
        $pc = @(Import-Csv (Join-Path $rd 'proc.csv'))
        Check 'c3 proc.csv has one row per second' ($pc.Count -eq ($W + $S)) "rows=$($pc.Count)"
        Check 'c4 closed by WM_CLOSE, not killed, exit 0' ($j.close.wm_close_posted -ge 1 -and -not $j.close.killed -and $j.close.exit_code -eq 0 -and -not $j.exited_early) "posted=$($j.close.wm_close_posted) killed=$($j.close.killed) exit=$($j.close.exit_code) wait=$($j.close.exit_wait_s)"
        Check 'c5 status OK, mode TIMING, no profiler env' ($j.status -eq 'OK' -and $j.mode -eq 'TIMING' -and -not (@($j.env_set.PSObject.Properties | ForEach-Object { $_.Name }) -contains 'LEGO_SAMPLE_PROFILE')) "status=$($j.status) problems=$($j.problems -join ' | ')"
        Check 'c6 perf.csv size tracked while held with FileShare.None' ($j.measure_start.perf_csv_bytes -gt 0 -and $j.measure_end.perf_csv_bytes -gt $j.measure_start.perf_csv_bytes) "start=$($j.measure_start.perf_csv_bytes) end=$($j.measure_end.perf_csv_bytes)"
        $f = $j.frames; $win = $f.window
        $vals = for ($i = [long]$win.first_row; $i -lt $win.first_row + $win.rows; $i++) { FakeFt $i }
        $e = Stats-Of $vals
        Check 'c7 summary equals the known pattern over the reported window' ($f.frames -eq $e.frames -and $f.median_ms -eq $e.median -and $f.p99_ms -eq $e.p99 -and $f.p99_9_ms -eq $e.p999 -and $f.over_33ms -eq $e.over33 -and $f.over_100ms -eq $e.over100 -and (Near $f.window_s $e.sum_s 1e-6)) "rows $($win.first_row)+$($win.rows): median $($f.median_ms)/$($e.median) p99 $($f.p99_ms)/$($e.p99) p99.9 $($f.p99_9_ms)/$($e.p999) >33 $($f.over_33ms)/$($e.over33) >100 $($f.over_100ms)/$($e.over100)"
        Check 'c8 window length = -Seconds (+ <= 1 frame)' ($f.window_s -ge $S -and $f.window_s -lt ($S + 0.121) -and $win.end_by -eq 'seconds' -and -not $win.short) "window_s=$($f.window_s)"
        $rowsAtT0 = 0; $acc = 0.0; while ($acc + (FakeFt $rowsAtT0) -le $W * 1e6) { $acc += FakeFt $rowsAtT0; $rowsAtT0++ }
        Check 'c9 window start within flush lag of the warm-up end' ($win.first_row -le $rowsAtT0 + 5 -and $win.first_row -ge $rowsAtT0 - 59 - 40) "first_row=$($win.first_row) rows-at-$W-s=$rowsAtT0 (allowed -99..+5: 59 flush lag + process start)"
        Check 'c10 end-mark cross-check within 59 rows + jitter' ($null -ne $win.end_bytes_minus_seconds_rows -and [math]::Abs($win.end_bytes_minus_seconds_rows) -le 70) "diff=$($win.end_bytes_minus_seconds_rows) wall=$($j.window_wall_s)"
        Check 'c11 window cpu/memory recorded' ($j.window_cpu_samples -eq $S -and $null -ne $j.window_cpu_cores_mean -and $j.window_peak_ws_mb -gt 0 -and $j.window_peak_commit_mb -gt 0) "cpu mean=$($j.window_cpu_cores_mean) max=$($j.window_cpu_cores_max) ws=$($j.window_peak_ws_mb) commit=$($j.window_peak_commit_mb)"
        Check 'c12 run.json has QPC marks' ($j.qpc_frequency -gt 0 -and $j.measure_end.qpc -gt $j.measure_start.qpc -and (Near $j.window_wall_s $S 0.5)) "wall=$($j.window_wall_s)"
    } else { Check 'c2 run.json exists' $false "see $(Join-Path $scratch 'e2e-timing.txt')" }

    # c13: -Profile run, warm-up 3 s, window 4 s, trigger for 2 s
    $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -BinDir $bin -Tag st-profile -Warmup 3 -Seconds 4 -Profile -ProfileSeconds 2 -RunsRoot $runs -MinFreeRamGB 0 -CloseTimeoutSec 15 2>&1 | Out-String
    $code = $LASTEXITCODE
    $out | Set-Content -LiteralPath (Join-Path $scratch 'e2e-profile.txt') -Encoding utf8
    $rd = if ($out -match 'run dir: (.+)') { $Matches[1].Trim() } else { $null }
    Check 'c13 profile run exit 0' ($code -eq 0 -and $null -ne $rd) "exit=$code run=$rd"
    if ($rd -and (Test-Path (Join-Path $rd 'run.json'))) {
        $j = Get-Content (Join-Path $rd 'run.json') -Raw | ConvertFrom-Json
        $sumTxt = Get-Content (Join-Path $rd 'summary.txt') -Raw
        Check 'c14 labelled PROFILE ONLY, NOT FOR TIMING (summary, run.json, console)' ($sumTxt -match 'PROFILE ONLY, NOT FOR TIMING' -and $j.mode -eq 'PROFILE ONLY, NOT FOR TIMING' -and $out -match 'PROFILE ONLY, NOT FOR TIMING' -and $j.status -eq 'PROFILE') "status=$($j.status)"
        $bins = @(Get-ChildItem -LiteralPath $rd -Filter 'profile-*.bin')
        $magic = if ($bins.Count) { [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($bins[0].FullName), 0, 4) } else { '' }
        Check 'c15 profile-*.bin written in the run dir (LSP1) and map present' ($bins.Count -eq 1 -and $magic -eq 'LSP1' -and (Test-Path (Join-Path $rd 'legodimensions.map'))) "bins=$($bins.Count) magic=$magic"
        $meta = Get-Content (Join-Path $rd 'profile-meta.json') -Raw | ConvertFrom-Json
        $dWall = $meta.profile_trigger_end - $meta.profile_trigger_start
        $dQpc = ($meta.qpc_trigger_end - $meta.qpc_trigger_start) / [double]$meta.qpc_frequency
        Check 'c16 trigger window ~2 s by wall and QPC; trigger file removed' ((Near $dWall 2 0.6) -and (Near $dQpc 2 0.6) -and -not (Test-Path (Join-Path $rd 'profile.trigger'))) "wall=$dWall qpc=$dQpc"
        $ana = Join-Path $repo 'DimensionsRecomp\tools\native-cpu'
        $py = "import sys; sys.path.insert(0, r'$ana'); import analyze_profile as a; print(a._meta_duration(r'$(Join-Path $rd 'profile-meta.json')', a.TRIGGER_LATENCY_S)[0])"
        $md = (& python -c $py 2>&1 | Out-String).Trim()
        Check 'c17 analyze_profile.py accepts the meta JSON (trigger window - 0.175 s)' ((Near ($md -as [double]) ($dWall - 0.175) 0.01)) "meta duration=$md"
        Check 'c18 profile run closed by WM_CLOSE' ($j.close.wm_close_posted -ge 1 -and -not $j.close.killed -and $j.close.exit_code -eq 0) "posted=$($j.close.wm_close_posted) killed=$($j.close.killed)"
        Check 'c19 profiler env set only in profile mode' ($j.env_set.LEGO_SAMPLE_PROFILE -eq '1' -and $j.env_set.LEGO_SAMPLE_PROFILE_TRIGGER -eq (Join-Path $rd 'profile.trigger')) ''
    } else { Check 'c14 run.json exists' $false "see $(Join-Path $scratch 'e2e-profile.txt')" }
}

. (Join-Path $PSScriptRoot 'selftest\selftest_matrix.ps1')

''
"TOTAL: $($script:pass) PASS, $($script:fail) FAIL, $($script:skip) SKIP"
if ($script:fail -gt 0) { exit 1 }
exit 0
