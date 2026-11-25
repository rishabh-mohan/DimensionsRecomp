# fixture_facts.ps1 - Agent 12, task #15 (2026-11-22). Re-derives the facts behind fixture-w5.json and
# fixture-w4b.json WITHOUT run_gates.py: PowerShell only (Import-Csv, Select-String, regex, Get-FileHash). Read-only.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\fixture_facts.ps1
# Exit 4 while perf-notes\WINDOW-HOLD.txt exists. Compare its output with RUN-GATES-FIXTURES.md.
# (PowerShell names are case-insensitive: the pattern strings are $S_*, the per-run counters $n*.)
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
if (Test-Path (Join-Path $repo 'perf-notes\WINDOW-HOLD.txt')) { 'perf-notes\WINDOW-HOLD.txt exists: not starting'; exit 4 }
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch { }
function Cnt($set, [scriptblock]$f) { @($set | Where-Object -FilterScript $f).Count }
$S_T1 = 'Host timer resolution set to 1 ms'
$S_OPT = '(background opt-out on)'
$S_PRE = 'TimerQueue: precise wait (timer_queue_precise_wait)'
$S_BAD = @('Recovered stale physical page protection', 'Unhandled guest physical write fault', 'PhysicalHeap::Protect failed')
# sys.json keeps each power field as {"first": x, "last": y, "changes": [...]}, in its window and run sections
$SYS_KEYS = @('overlay', 'scheme', 'ac', 'batt_saver')
function FirstLast([string]$text, [string]$key) {
    $re = '"' + $key + '"\s*:\s*\{\s*"first"\s*:\s*"?([^",}]*)"?\s*,\s*"last"\s*:\s*"?([^",}]*)"?\s*,\s*"changes"\s*:\s*\[([^\]]*)\]'
    $d = @([regex]::Matches($text, $re) | ForEach-Object {
            $ch = $_.Groups[3].Value.Trim()
            if ($_.Groups[1].Value -eq $_.Groups[2].Value -and -not $ch) { $_.Groups[1].Value } else { "$($_.Groups[1].Value)>$($_.Groups[2].Value) [changes: $ch]" }
        } | Sort-Object -Unique)
    if ($d.Count) { $d -join ' | ' } else { '(no field)' }
}
$windows = @(
    @{ n = 'W5'; m = 'build\agent8\matrix\20261122-1756'; q = 'build\agent1\w5\quiet-1731.log' },
    @{ n = 'W4b'; m = 'build\agent8\matrix\20261122-1541'; q = $null })
foreach ($w in $windows) {
    $m = Join-Path $repo $w.m
    ''
    "== $($w.n): $($w.m)"
    $r = @(Import-Csv (Join-Path $m 'results.csv'))
    $sc = @($r | Where-Object { $_.scored -eq 'True' })
    "results.csv: rows $($r.Count); scored $($sc.Count); scored and valid_timing $(Cnt $sc { $_.valid_timing -eq 'True' }); excluded $(Cnt $r { $_.excluded -eq 'True' })"
    "  status OK $(Cnt $r { $_.status -eq 'OK' }); exit_code 0x00000000 $(Cnt $r { $_.exit_code -eq '0x00000000' }); close wm_close $(Cnt $r { $_.close -like 'wm_close*' }); runner_exit 0 $(Cnt $r { $_.runner_exit -eq '0' })"
    '  per arm: ' + ((@($r | Group-Object arm) | ForEach-Object { "$($_.Name) $($_.Count) ($(Cnt $_.Group { $_.scored -eq 'True' }) scored)" }) -join ', ')
    foreach ($x in @($sc | Where-Object { $_.valid_timing -ne 'True' })) { "  not valid: #$($x.seq) $($x.arm) r$($x.rep); flags_info [$($x.flags_info)]; notes [$($x.notes)]" }
    $plan = Join-Path $m 'plan.txt'
    if (Test-Path -LiteralPath $plan) {
        Select-String -LiteralPath $plan -Pattern '^(cold|estimate|sys\.csv)\s' | ForEach-Object { "plan.txt L$($_.LineNumber): $($_.Line.Trim())" }
    } else { 'plan.txt: missing' }
    $mj = [IO.File]::ReadAllText((Join-Path $m 'matrix.json'))
    $bins = @([regex]::Matches($mj, '"bin(?:_dir)?"\s*:\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value -replace '\\\\', '\' } | Sort-Object -Unique)
    foreach ($b in $bins) {
        $bp = if ([IO.Path]::IsPathRooted($b)) { $b } else { Join-Path $repo ($b -replace '/', '\') }
        $mf = Join-Path $bp 'MANIFEST.txt'
        $h = if (Test-Path -LiteralPath $mf) { (Get-FileHash -LiteralPath $mf -Algorithm SHA256).Hash.Substring(0, 16) } else { 'no MANIFEST.txt' }
        $exe = Get-Item -LiteralPath (Join-Path $bp 'legodimensions.exe') -ErrorAction SilentlyContinue
        "matrix.json bin ${b}: MANIFEST.txt sha256 $h; legodimensions.exe $(if ($exe) { "$($exe.Length) B" } else { 'missing' })"
    }
    $per = [ordered]@{}
    $badTotal = 0; $badRuns = 0; $withLog = 0; $sysN = 0
    $tally = @{}; foreach ($k in $SYS_KEYS) { $tally[$k] = @{} }
    foreach ($x in $r) {
        $logs = @(Get-ChildItem -LiteralPath $x.run_dir -Filter 'game*.log' -File -ErrorAction SilentlyContinue)
        $nT1 = 0; $nOpt = 0; $nPre = 0; $nBad = 0
        if ($logs.Count) {
            $withLog++
            foreach ($mi in @(Select-String -LiteralPath $logs.FullName -SimpleMatch -Pattern (@($S_T1, $S_PRE) + $S_BAD))) {
                $l = $mi.Line
                if ($l.Contains($S_T1)) { $nT1++; if ($l.Contains($S_OPT)) { $nOpt++ } }
                if ($l.Contains($S_PRE)) { $nPre++ }
                foreach ($s in $S_BAD) { if ($l.Contains($s)) { $nBad++ } }
            }
        }
        $badTotal += $nBad; if ($nBad) { $badRuns++ }
        if (-not $per.Contains($x.arm)) { $per[$x.arm] = @() }
        $per[$x.arm] += , ("#{0} {1}/{2}/{3}" -f $x.seq, $nT1, $nOpt, $nPre)
        $sj = Join-Path $x.run_dir 'sys.json'
        if (Test-Path -LiteralPath $sj) {
            $sysN++
            $txt = [IO.File]::ReadAllText($sj)
            foreach ($k in $SYS_KEYS) { $v = FirstLast $txt $k; $tally[$k][$v] = 1 + [int]$tally[$k][$v] }
        }
    }
    "game*.log: $withLog/$($r.Count) runs have one; stale/fault/Protect-failed lines: $badTotal (in $badRuns runs)"
    'proof lines per run (#seq timer1ms/optout/precise), by arm:'
    foreach ($k in $per.Keys) { "  ${k}: $($per[$k] -join ', ')" }
    "sys.json: $sysN/$($r.Count) runs; per run, window and run sections (value, or first>last [changes]):"
    foreach ($k in $SYS_KEYS) { "  ${k}: " + ((@($tally[$k].Keys) | Sort-Object | ForEach-Object { "$_ x$($tally[$k][$_])" }) -join ', ') }
    if ($w.q) {
        $q = Join-Path $repo $w.q
        "quiet log $($w.q): " + (Cnt (Get-Content -LiteralPath $q) { $_ -match 'FAIL' }) + ' lines with FAIL'
        Select-String -LiteralPath $q -Pattern 'QUIET' | Select-Object -Last 1 | ForEach-Object { "  L$($_.LineNumber): $($_.Line.Trim())" }
    } else { 'quiet log: none for this window' }
}
