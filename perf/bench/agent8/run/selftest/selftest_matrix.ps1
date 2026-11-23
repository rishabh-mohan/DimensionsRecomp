# Self-test section (d), dot-sourced by run_selftest.ps1 (it uses $repo, $root, $scratch, $fs, $SkipE2E and the
# helpers Check/Skip/Near/Summ/Stats-Of/FakeFt from there). Never starts the real game.
#   d0      frame_summary.py auto-detects a native-frames.csv (interval_ms, ms floats, partial last row)
#   d1      run-matrix.ps1 rejects unknown matrix fields (exit 2, clear message)
#   d2      -PlanOnly: round-robin order with rotation, one cold run per bin, a missing bin skips its arm
#   d3-d9   -Quick -Repeats 2 matrix against the fake exe: results.csv, summary.md, menu/settle, driver, <run>,
#           triggers, cvars, env restored between runs
#   d10-d15 order fixed + frames native + seed_cache chain (arm id; recipes only) against the fake exe
#   d16     run-timing.ps1 -SeedCache with a missing file: exit 1, nothing created
$here = Split-Path -Parent $fs
$mxRunner = Join-Path $here 'run-matrix.ps1'
$tRunner = Join-Path $here 'run-timing.ps1'
'--- (d) native frames csv + run-matrix.ps1 ---'

# d0: native csv
$nat = Join-Path $scratch 'native-synthetic.csv'
$sb = New-Object Text.StringBuilder
[void]$sb.Append("frame,interval_ms,cpu_ms,native_vsync`r`n")
for ($i = 1; $i -le 200; $i++) {
    $v = if ($i % 100 -eq 50) { '120.5' } elseif ($i % 10 -eq 5) { '40.25' } else { '16.5' }
    [void]$sb.Append("$i,$v,4.25,0`r`n")
}
[void]$sb.Append('201,16.')
[IO.File]::WriteAllText($nat, $sb.ToString(), (New-Object Text.ASCIIEncoding))
$x = Summ $nat; $r = $x.r
Check 'd0 native csv auto-detected (interval_ms in ms), partial last row dropped' ($x.code -eq 0 -and $null -ne $r -and $r.source -eq 'native' -and $r.rows_total -eq 200 -and $r.truncated_last_line -and $r.median_ms -eq 16.5 -and $r.p99_ms -eq 40.25 -and $r.p99_9_ms -eq 120.5 -and $r.over_33ms -eq 22 -and $r.over_100ms -eq 2 -and (Near $r.window_s 3.983 1e-6)) "source=$(if ($r) { $r.source }) rows=$(if ($r) { $r.rows_total }) median=$(if ($r) { $r.median_ms }) p99=$(if ($r) { $r.p99_ms }) p99.9=$(if ($r) { $r.p99_9_ms }) >33=$(if ($r) { $r.over_33ms }) >100=$(if ($r) { $r.over_100ms }) s=$(if ($r) { $r.window_s })"

$fakeBin = Join-Path $root 'fake-bin'
$mxDir = Join-Path $root 'matrix-test'
New-Item -ItemType Directory -Force -Path $mxDir | Out-Null
function Run-Mx([string[]]$A) {
    $o = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mxRunner @A 2>&1 | Out-String
    return [pscustomobject]@{ code = $LASTEXITCODE; out = $o }
}
function Read-RunJson([string]$Dir) {
    $p = Join-Path $Dir 'run.json'
    if ($Dir -and (Test-Path -LiteralPath $p)) { return (Get-Content -LiteralPath $p -Raw | ConvertFrom-Json) }
    return $null
}

# d1: unknown fields
$bad = [ordered]@{ title = 'bad'; bogus = 1; arms = @([ordered]@{ id = 'A'; bin = $fakeBin; colour = 'red' }) }
$badPath = Join-Path $mxDir 'matrix-bad.json'
($bad | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $badPath -Encoding ascii
$x = Run-Mx @('-Matrix', $badPath, '-PlanOnly', '-AllowRunningGame')
Check 'd1 unknown matrix fields -> exit 2 with a clear message' ($x.code -eq 2 -and $x.out -match "unknown top-level field 'bogus'" -and $x.out -match "arm 'A': unknown field 'colour'") "exit=$($x.code)"

if ($SkipE2E) { Skip 'd2-d16 matrix end-to-end' '-SkipE2E' }
elseif (-not (Test-Path -LiteralPath (Join-Path $fakeBin 'MANIFEST.txt'))) { Skip 'd2-d16 matrix end-to-end' "no fake bin at $fakeBin (section c failed?)" }
else {
    $drvPs = Join-Path $here 'selftest\fake-driver.ps1'
    $quick = [ordered]@{ warmup_s = 2; measure_s = 3; settle_s = 1; menu_s = 2; cooldown_s = 1; boot_timeout_s = 30; close_timeout_s = 15 }
    $mx = [ordered]@{
        title = 'selftest matrix (fake exe)'; reference = 'A'; cold_run = $true; warmup_s = 60; measure_s = 120; repeats = 3
        notes = @('selftest note'); quick = $quick
        arms = @(
            [ordered]@{ id = 'A'; bin = $fakeBin; group = 'g'; ref = $true; note = 'fake ref arm' },
            [ordered]@{ id = 'B'; bin = $fakeBin; group = 'g'; cvars = @('vsync=false'); env = [ordered]@{ LD_SELFTEST_ARM = 'B'; LD_PATH = '<run>\x.txt' }
                        menu = 'selftest menu step (nothing to do)'; driver = [ordered]@{ script = $drvPs; args = @('-Mode', 'st') }; triggers = @('<run>\t.trigger') },
            [ordered]@{ id = 'C'; bin = 'build\agent8\run-selftest\no-such-bin'; group = 'g' }
        )
    }
    $mxPath = Join-Path $mxDir 'matrix-st.json'
    ($mx | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $mxPath -Encoding ascii

    # d2: plan only
    $x = Run-Mx @('-Matrix', $mxPath, '-Repeats', '2', '-Quick', '-PlanOnly', '-AllowRunningGame')
    $x.out | Set-Content -LiteralPath (Join-Path $scratch 'e2e-matrix-plan.txt') -Encoding utf8
    Check 'd2 plan: order A B | B A, one cold run (shared bin), C skipped, 5 runs, exit 0' ($x.code -eq 0 -and $x.out -match 'order\s+A B \| B A' -and $x.out -match 'SKIPPED ARM C:' -and $x.out -match 'cold\s+A \(' -and $x.out -match 'estimate\s+5 runs \(1 cold\)' -and $x.out -match 'note\s+selftest note') "exit=$($x.code)"

    # d3..d9: the matrix for real (fake exe)
    $mxOut = Join-Path $root ('matrix-' + (Get-Date -Format 'HHmmss'))
    $x = Run-Mx @('-Matrix', $mxPath, '-Repeats', '2', '-Quick', '-NoPrompt', '-OutDir', $mxOut, '-AllowRunningGame')
    $x.out | Set-Content -LiteralPath (Join-Path $scratch 'e2e-matrix.txt') -Encoding utf8
    Check 'd3 matrix run exit 0' ($x.code -eq 0) "exit=$($x.code) out=$mxOut (console: $(Join-Path $scratch 'e2e-matrix.txt'))"
    $rc = Join-Path $mxOut 'results.csv'
    $res = @(); if (Test-Path -LiteralPath $rc) { $res = @(Import-Csv -LiteralPath $rc) }
    $scoredOrder = (@($res | Where-Object { $_.scored -eq 'True' } | ForEach-Object { $_.arm }) -join ' ')
    $stats = (@($res | ForEach-Object { "$($_.arm):$($_.status)" }) -join ' ')
    Check 'd4 results.csv: 1 cold run of A, then A B B A, all OK with frames' ($res.Count -eq 5 -and $res[0].scored -eq 'False' -and $res[0].arm -eq 'A' -and $scoredOrder -eq 'A B B A' -and @($res | Where-Object { $_.status -ne 'OK' -or [int]$_.frames -le 0 -or $_.median_ms -eq '' }).Count -eq 0) "rows=$($res.Count) order=$scoredOrder $stats"
    $smd = Join-Path $mxOut 'summary.md'
    $sm = if (Test-Path -LiteralPath $smd) { Get-Content -LiteralPath $smd -Raw } else { '' }
    Check 'd5 summary.md: group g with ref A, B row with a verdict, C skipped, FUNCTIONAL ONLY banner' ($sm -match '## Group g: ref A \(ref arm of the group\)' -and $sm -match '\| A \| 2/2 \|' -and $sm -match '\| B \| 2/2 \|.*\| (within noise|FASTER \(outside noise\)|SLOWER \(outside noise\)|no noise band) \|' -and $sm -match '\| C \|.*SKIPPED' -and $sm -match 'FUNCTIONAL ONLY' -and (Test-Path -LiteralPath (Join-Path $mxOut 'plan.txt')) -and (Test-Path -LiteralPath (Join-Path $mxOut 'matrix.json'))) "summary=$smd"
    $bRows = @($res | Where-Object { $_.arm -eq 'B' }); $aRows = @($res | Where-Object { $_.arm -eq 'A' })
    $okMenu = $bRows.Count -eq 2; $okDrv = $bRows.Count -eq 2; $okTrig = $bRows.Count -eq 2; $okEnv = $bRows.Count -eq 2; $why = @()
    foreach ($b in $bRows) {
        $j = Read-RunJson $b.run_dir
        if ($null -eq $j) { $okMenu = $okDrv = $okTrig = $okEnv = $false; $why += "no run.json in $($b.run_dir)"; continue }
        $gap = if ($null -ne $j.warmup_start_s -and $null -ne $j.boot_s) { [double]$j.warmup_start_s - [double]$j.boot_s } else { -1 }
        if ($null -eq $j.menu_prompt_at_s -or $gap -lt 2.5) { $okMenu = $false; $why += "menu_at=$($j.menu_prompt_at_s) gap=$gap" }
        $dr = Join-Path $b.run_dir 'driver-ran.txt'
        $dtxt = if (Test-Path -LiteralPath $dr) { Get-Content -LiteralPath $dr -Raw } else { '' }
        if ($null -eq $j.driver -or $j.driver.exit_code -ne 0 -or $dtxt -notmatch 'alive=True mode=st') { $okDrv = $false; $why += "driver: $dtxt" }
        $mt = @($j.measure_triggers)
        if ($mt.Count -ne 1 -or $mt[0].path -ne (Join-Path $b.run_dir 't.trigger') -or $null -ne $mt[0].error) { $okTrig = $false; $why += "triggers=$($mt.Count)" }
        if ($j.env_set.LD_PATH -ne (Join-Path $b.run_dir 'x.txt') -or $j.env_set.LD_SELFTEST_ARM -ne 'B' -or (@($j.args) -join ' ') -notmatch '--vsync=false') { $okEnv = $false; $why += "env LD_PATH=$($j.env_set.LD_PATH)" }
    }
    Check 'd6 arm B: menu prompt after the first frame + settle, warm-up >= 2.5 s later' $okMenu ($why -join '; ')
    Check 'd7 arm B: driver ran in the window with -GamePid/-RunDir/-Mode st, exit 0' $okDrv ''
    Check 'd8 arm B: <run> trigger created at the measure start; <run> env expanded; cvar passed' ($okTrig -and $okEnv) ''
    $okA = $aRows.Count -eq 3
    foreach ($a in $aRows) {
        $j = Read-RunJson $a.run_dir
        if ($null -eq $j -or @($j.env_set.PSObject.Properties | ForEach-Object { $_.Name }) -contains 'LD_SELFTEST_ARM' -or (Test-Path -LiteralPath (Join-Path $a.run_dir 'driver-ran.txt')) -or $null -ne $j.menu_prompt_at_s) { $okA = $false }
    }
    Check 'd9 arm A runs (cold + 2): no B env, driver or menu; no ENV LEAK in the matrix' ($okA -and $x.out -notmatch 'ENV LEAK' -and -not [Environment]::GetEnvironmentVariable('LD_SELFTEST_ARM')) "A rows=$($aRows.Count)"

    # d10..d15: fixed order, native frames, seed chain N1 -> N2 (full) -> N3 (recipes only, no save)
    $mx2 = [ordered]@{
        title = 'selftest native + seed chain (fake exe)'; order = 'fixed'; repeats = 1; cold_run = $false
        quick = [ordered]@{ warmup_s = 2; measure_s = 3; settle_s = 1; cooldown_s = 1; boot_timeout_s = 30; close_timeout_s = 15 }
        arms = @(
            [ordered]@{ id = 'N1'; bin = $fakeBin; frames = 'native'; group = 'n'; ref = $true },
            [ordered]@{ id = 'N2'; bin = $fakeBin; frames = 'native'; group = 'n'; seed_cache = 'N1' },
            [ordered]@{ id = 'N3'; bin = $fakeBin; frames = 'native'; group = 'n'; seed_cache = 'N2'; seed_recipes_only = $true; env = [ordered]@{ LEGO_NATIVE_PSO_CACHE = '0' } }
        )
    }
    $mx2Path = Join-Path $mxDir 'matrix-st-native.json'
    ($mx2 | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $mx2Path -Encoding ascii
    $mx2Out = Join-Path $root ('matrix-native-' + (Get-Date -Format 'HHmmss'))
    $x = Run-Mx @('-Matrix', $mx2Path, '-Quick', '-NoPrompt', '-OutDir', $mx2Out, '-AllowRunningGame')
    $x.out | Set-Content -LiteralPath (Join-Path $scratch 'e2e-matrix-native.txt') -Encoding utf8
    $res2 = @(); $rc2 = Join-Path $mx2Out 'results.csv'; if (Test-Path -LiteralPath $rc2) { $res2 = @(Import-Csv -LiteralPath $rc2) }
    $ord2 = (@($res2 | ForEach-Object { "$($_.arm):$($_.status):$($_.frames_source)" }) -join ' ')
    Check 'd10 native matrix: exit 0, N1 N2 N3 in file order, all OK, frames from native-frames.csv' ($x.code -eq 0 -and $ord2 -eq 'N1:OK:native N2:OK:native N3:OK:native') "exit=$($x.code) $ord2 (console: $(Join-Path $scratch 'e2e-matrix-native.txt'))"
    if ($res2.Count -eq 3) {
        $j1 = Read-RunJson $res2[0].run_dir; $j2 = Read-RunJson $res2[1].run_dir; $j3 = Read-RunJson $res2[2].run_dir
        $okNat = $null -ne $j1 -and $j1.frames.source -eq 'native' -and $j1.frames.frames -gt 0 -and $j1.frames_csv_header_bytes -eq 0 -and $null -ne $j1.first_frame_signal_s -and $j1.env_set.LEGO_NATIVE_FRAME_METRICS -eq (Join-Path $res2[0].run_dir 'native-frames.csv')
        $detail = ''
        if ($okNat) {
            $f = $j1.frames; $win = $f.window
            $vals = for ($i = [long]$win.first_row; $i -lt $win.first_row + $win.rows; $i++) { FakeFt $i }
            $e = Stats-Of $vals
            $okNat = $f.frames -eq $e.frames -and $f.median_ms -eq $e.median -and $f.p99_ms -eq $e.p99 -and $f.over_33ms -eq $e.over33 -and $f.over_100ms -eq $e.over100 -and (Near $f.window_s $e.sum_s 1e-6) -and $f.window_s -ge 3
            $detail = "rows $($win.first_row)+$($win.rows): median $($f.median_ms)/$($e.median) p99 $($f.p99_ms)/$($e.p99) >33 $($f.over_33ms)/$($e.over33) s $($f.window_s)/$($e.sum_s); first frame $($j1.first_frame_signal_s) s"
        }
        Check 'd11 N1 native window stats equal the known pattern (header 0 B, first-frame signal seen)' $okNat $detail
        $c1 = Join-Path $res2[0].run_dir 'cache'
        $h1 = @{}; foreach ($n in @('native-pso.bin', 'native-pso-recipes.bin')) { $p = Join-Path $c1 $n; if (Test-Path -LiteralPath $p) { $h1[$n] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash } }
        Check 'd12 N1 wrote its cache at exit (fake PSO cache)' ($h1.Count -eq 2) "cache=$c1"
        $sf2 = @(if ($j2 -and $j2.seed_cache) { $j2.seed_cache.files })   # @(if ...): a 1-item array would unroll to a scalar (StrictMode: no .Count)
        $ok2 = $sf2.Count -eq 2 -and $res2[1].seed_from -eq $res2[0].run_dir
        foreach ($s in $sf2) { if (-not $h1.ContainsKey($s.name) -or $s.sha256 -ne $h1[$s.name] -or -not $s.source.StartsWith($c1)) { $ok2 = $false } }
        $log2 = Join-Path $res2[1].run_dir 'game.log'
        $l2 = if (Test-Path -LiteralPath $log2) { Get-Content -LiteralPath $log2 -Raw } else { '' }
        Check 'd13 N2 seeded from N1''s run (both files, same sha256), present before the game started' ($ok2 -and $l2 -match 'fake pso cache at start: native-pso.bin=\d+ B native-pso-recipes.bin=\d+ B') "files=$($sf2.Count) seed_from=$($res2[1].seed_from)"
        $sf3 = @(if ($j3 -and $j3.seed_cache) { $j3.seed_cache.files })
        $c2 = Join-Path $res2[1].run_dir 'cache'
        $log3 = Join-Path $res2[2].run_dir 'game.log'
        $l3 = if (Test-Path -LiteralPath $log3) { Get-Content -LiteralPath $log3 -Raw } else { '' }
        Check 'd14 N3 seeded recipes only from N2''s run' ($sf3.Count -eq 1 -and $sf3[0].name -eq 'native-pso-recipes.bin' -and $sf3[0].source.StartsWith($c2) -and $j3.seed_cache.recipes_only -and $l3 -match 'native-pso.bin=missing native-pso-recipes.bin=\d+ B') "files=$($sf3.Count)"
        $c3 = @(Get-ChildItem -LiteralPath (Join-Path $res2[2].run_dir 'cache') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
        Check 'd15 N3 arm env reached the game (LEGO_NATIVE_PSO_CACHE=0: no save)' ($l3 -match 'LEGO_NATIVE_PSO_CACHE=0' -and ($c3 -join ',') -eq 'native-pso-recipes.bin') "cache files=$($c3 -join ',')"
    } else { Check 'd11 native matrix produced 3 rows' $false "rows=$($res2.Count)" }

    # d16: missing seed file -> not started
    $emptySeed = Join-Path $mxDir 'empty-seed'
    New-Item -ItemType Directory -Force -Path $emptySeed | Out-Null
    $seedRuns = Join-Path $mxDir 'seed-runs'
    if (Test-Path -LiteralPath $seedRuns) { Remove-Item -LiteralPath $seedRuns -Recurse -Force }
    $o = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tRunner -BinDir $fakeBin -Tag st-seedmiss -Warmup 1 -Seconds 1 -RunsRoot $seedRuns -MinFreeRamGB 0 -SeedCache $emptySeed -SeedRecipesOnly 2>&1 | Out-String
    $code = $LASTEXITCODE
    Check 'd16 -SeedCache with a missing file: exit 1, no run dir, clear message' ($code -eq 1 -and $o -match 'SEED CACHE: missing native-pso-recipes.bin' -and -not (Test-Path -LiteralPath $seedRuns)) "exit=$code"
}
