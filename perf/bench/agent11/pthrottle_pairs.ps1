# pthrottle_pairs.ps1 - S4 task #24: alternating devoff2 d0 pairs, the execution-speed opt-out off
# (d0) and on (d0e), through Agent 8's UNCHANGED run-matrix.ps1 plus pthrottle_sidecar.ps1, which
# opts the game out from outside (documented SetProcessInformation on its own narrow handle; no
# game rebuild). FUNCTIONAL ONLY (hidden desktop): never a timing run. Nothing in bench\agent8,
# harness or any window-4b file is written: run-matrix gets a generated matrix and an out dir
# under build\agent11, and the window-4b closure is hashed before and after (pthrottle_w4b_hash.ps1).
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_pairs.ps1 [-MeasureS 90] [-Pairs 3] [-PlanOnly] [-DryRun]
# Out: build\agent11\pthrottle\pairs\<yyyyMMdd-HHmm> (run-matrix's out dir: runs\, logs\, results.csv)
#      and <same>-meta: matrix, sidecar records + log, w4b-before/after.tsv, readout.txt, report.txt.
# Each run's run.json gets "power_throttling" (the sidecar's read-back), BOM kept.
# -PlanOnly: run-matrix -PlanOnly on the generated matrix (order, time estimate), nothing started.
# -DryRun: no game, no run-matrix: a simulated runner starts a PING.EXE copy (pthrottle_standin.exe)
#   in each run dir in the same order and names, sets C=0x4 on it like the game's own startup call,
#   writes synthetic sys.csv/run.json; plus one stand-in outside the runs dir that must stay untouched.
# Exit: 0 ok; 1 a run, record, merge or check failed; 2 preflight failed or the hashes differ.
[CmdletBinding(PositionalBinding = $false)]
param(
    [int]$MeasureS = 90,
    [int]$Pairs = 3,
    [string]$BinDir = 'build/agent2/devoff2-bin',
    [string]$OutRoot = 'build\agent11\pthrottle\pairs',
    [switch]$PlanOnly,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if (($DryRun -or $PlanOnly) -and -not $PSBoundParameters.ContainsKey('OutRoot')) { $OutRoot = 'build\agent11\pthrottle\pairs-dry' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $root
$rm = Join-Path $root 'bench\agent8\run\run-matrix.ps1'
$hashPs = Join-Path $PSScriptRoot 'pthrottle_w4b_hash.ps1'
$sidePs = Join-Path $PSScriptRoot 'pthrottle_sidecar.ps1'
$readPs = Join-Path $PSScriptRoot 'pthrottle_readout.ps1'
$slowPs = Join-Path $PSScriptRoot 'timerq_slowstate.ps1'
$outRootFull = Join-Path $root $OutRoot
for ($try = 0; $true; $try++) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmm'
    $out = Join-Path $outRootFull $stamp; $meta = "$out-meta"
    if (-not (Test-Path -LiteralPath $out) -and -not (Test-Path -LiteralPath $meta)) { break }
    if ($try -ge 2) { throw "out dir $out exists" }
    Start-Sleep -Seconds (61 - (Get-Date).Second)
}
New-Item -ItemType Directory -Force -Path $meta | Out-Null
$log = New-Object System.Collections.Generic.List[string]
function Say([string]$s) { $log.Add($s); Write-Host $s }
function Save-Report { Set-Content -LiteralPath (Join-Path $meta 'report.txt') -Value $log -Encoding ascii }
function Invoke-Ps([string[]]$a) {
    $ErrorActionPreference = 'Continue'
    $o = & powershell -NoProfile -ExecutionPolicy Bypass -File @a 2>&1 | ForEach-Object { "$_" }
    return [pscustomobject]@{ rc = $LASTEXITCODE; text = @($o) }
}
$bad = 0
$mode = if ($DryRun) { 'DRY RUN (no game)' } elseif ($PlanOnly) { 'PLAN ONLY' } else { 'FUNCTIONAL ONLY (hidden desktop)' }
Say "# pthrottle_pairs (S4 task #24) $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $mode; $Pairs pairs, measure $MeasureS s, bin $BinDir"
Say "out $out ; meta $meta"
$note = 'Agent 11 task #24, FUNCTIONAL ONLY (hidden desktop). d0e = d0 plus the runner-side EXECUTION_SPEED opt-out by bench/agent11/pthrottle_sidecar.ps1 (SetProcessInformation on its own handle); game, bin, cvars and env are identical. The sidecar reads the state of d0 runs too, never sets it.'
$arm = { param($id, $n) [ordered]@{ id = $id; group = 'pt'; ref = ($id -eq 'd0'); bin = $BinDir; frames = 'perf'; cvars = @('framerate_limit=0'); env = @{}; driver = 'drivers/thread-cpu.ps1'; note = $n } }
$mx = [ordered]@{ title = 'Agent 11 task #24: execution-speed opt-out pairs, devoff2 d0 (off) vs d0e (on)'; reference = 'd0'
    warmup_s = 55; warmup_from = 'firstframe'; measure_s = $MeasureS; repeats = $Pairs; order = 'roundrobin'; settle_s = 5; cooldown_s = 5
    boot_timeout_s = 240; close_timeout_s = 60; cold_run = $false; sys_csv = $true; min_window_after_ff_s = 60; notes = @($note)
    arms = @((& $arm 'd0' 'opt-out off (sidecar reads only)'), (& $arm 'd0e' 'opt-out on (sidecar sets EXECUTION_SPEED controlled + off)')) }
$mj = Join-Path $meta 'pthrottle-pairs.json'
[IO.File]::WriteAllText($mj, ($mx | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding $false))
if ($PlanOnly) {
    $r = Invoke-Ps @($rm, '-Matrix', $mj, '-PlanOnly', '-NoCold', '-NoPrompt')
    $r.text | ForEach-Object { Say $_ }; Say "run-matrix -PlanOnly exit $($r.rc)"; Save-Report; exit $r.rc
}
# preflight: no game anywhere (one game at a time), the bin and Agent 8's runner present
$games = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
if (-not $DryRun -and $games.Count) { Say "PREFLIGHT FAIL: legodimensions.exe is running (pid $($games.Id -join ',')): one game at a time"; Save-Report; exit 2 }
foreach ($f in @((Join-Path $root $BinDir), $rm, $hashPs, $sidePs, $readPs, $slowPs)) { if (-not (Test-Path -LiteralPath $f)) { Say "PREFLIGHT FAIL: missing $f"; Save-Report; exit 2 } }
$h1 = Invoke-Ps @($hashPs, '-Out', (Join-Path $meta 'w4b-before.tsv'))
Say "hash before: $($h1.text | Select-Object -First 1) (exit $($h1.rc))"
if ($h1.rc -ne 0) { $h1.text | ForEach-Object { Say $_ }; Save-Report; exit 2 }
# sidecar
$pn = if ($DryRun) { 'pthrottle_standin' } else { 'legodimensions' }
$ptDir = Join-Path $meta 'pthrottle'; $stop = Join-Path $ptDir 'stop'
$maxMin = [math]::Ceiling($Pairs * 2 * ($MeasureS + 160) / 60.0) + 20
$sa = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -RunsDir "{1}" -OutDir "{2}" -ProcessName {3} -OnArm d0e -StopFile "{4}" -MaxMinutes {5}' -f $sidePs, (Join-Path $out 'runs'), $ptDir, $pn, $stop, $maxMin
$sc = Start-Process -FilePath powershell -ArgumentList $sa -WindowStyle Hidden -PassThru
$slog = Join-Path $ptDir 'sidecar.log'
$ready = $false
for ($i = 0; $i -lt 40 -and -not $ready -and -not $sc.HasExited; $i++) { Start-Sleep -Milliseconds 500; $ready = (Test-Path -LiteralPath $slog) -and (Select-String -LiteralPath $slog -Pattern ' ready: ' -Quiet) }
if (-not $ready -or $sc.HasExited) { Say 'FAIL: the sidecar did not start'; if (-not $sc.HasExited) { Stop-Process -Id $sc.Id }; Save-Report; exit 2 }
Say "sidecar pid $($sc.Id) ready (process $pn, max $maxMin min)"
$env:PYTHONDONTWRITEBYTECODE = '1'
$outside = $null
if ($DryRun) { . (Join-Path $PSScriptRoot 'pthrottle_dryrunner.ps1'); $outside = Start-Outside $meta; $rc = Invoke-DryRunner $out $Pairs $MeasureS }
else {
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $rm -Matrix $mj -NoCold -NoPrompt -OutDir $out
    $rc = $LASTEXITCODE; $ErrorActionPreference = 'Stop'
}
Say "runner exit $rc"; if ($rc -ne 0) { $bad++ }
New-Item -ItemType File -Force -Path $stop | Out-Null
if (-not $sc.WaitForExit(30000)) { Say 'sidecar still running after 30 s: stopped'; Stop-Process -Id $sc.Id; $bad++ }
Get-Content -LiteralPath $slog | ForEach-Object { Say "  sidecar: $_" }
if ($outside) { $bad += Test-Outside $outside $slog }
# merge each sidecar record into its run.json (text insert after the first '{', BOM kept, re-parsed)
$runDirs = @(Get-ChildItem -LiteralPath (Join-Path $out 'runs') -Directory -ErrorAction SilentlyContinue | Sort-Object Name)
foreach ($d in $runDirs) {
    $rj = Join-Path $d.FullName 'run.json'; $pj = Join-Path $ptDir ($d.Name + '.json')
    if (-not (Test-Path -LiteralPath $rj)) { Say "merge $($d.Name): no run.json"; $bad++; continue }
    $bytes = [IO.File]::ReadAllBytes($rj)
    $bom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
    $skip = if ($bom) { 3 } else { 0 }
    $text = [Text.Encoding]::UTF8.GetString($bytes, $skip, $bytes.Length - $skip)
    if ($text -match '"power_throttling"') { Say "merge $($d.Name): already present"; continue }
    if (Test-Path -LiteralPath $pj) { $rec = Get-Content -Raw -LiteralPath $pj | ConvertFrom-Json; $pt = $rec | ConvertTo-Json -Depth 4 -Compress }
    else { $rec = $null; $pt = '{"seen":false}'; $bad++ }
    $i = $text.IndexOf('{')
    $new = $text.Substring(0, $i + 1) + "`r`n    `"power_throttling`":  " + $pt + ',' + $text.Substring($i + 1)
    try { $null = $new | ConvertFrom-Json } catch { Say "merge $($d.Name): FAIL, the merged text does not parse (left unchanged)"; $bad++; continue }
    [IO.File]::WriteAllText($rj, $new, (New-Object Text.UTF8Encoding $bom))
    $want = $d.Name -match '^\d{4}-d0e-r'
    $okRec = $rec -and $rec.ok -and ([bool]$rec.applied -eq $want)
    if (-not $okRec) { $bad++ }
    Say ("merge {0}: {1}; bom {2}; record {3}" -f $d.Name, $(if ($rec) { "applied $($rec.applied), $($rec.before) -> $($rec.after), last $($rec.last_read), reapplied $($rec.reapplied), held $($rec.optout_held_pct)%" } else { 'NO sidecar record' }), $bom, $(if ($okRec) { 'ok' } else { 'FAIL' }))
}
if ($runDirs.Count -ne 2 * $Pairs) { Say "FAIL: $($runDirs.Count) run dirs, expected $(2 * $Pairs)"; $bad++ }
$r = Invoke-Ps @($readPs, '-RunsDir', (Join-Path $out 'runs'), '-PtDir', $ptDir)
Set-Content -LiteralPath (Join-Path $meta 'readout.txt') -Value $r.text -Encoding ascii
$r.text | ForEach-Object { Say $_ }
$r = Invoke-Ps @($slowPs, '-Root', $outRootFull, '-Since', $stamp)
Say '--- timerq_slowstate.ps1 cross-check'; $r.text | Where-Object { $_.Trim() } | ForEach-Object { Say $_ }
$h2 = Invoke-Ps @($hashPs, '-Out', (Join-Path $meta 'w4b-after.tsv'), '-Compare', (Join-Path $meta 'w4b-before.tsv'))
$h2.text | ForEach-Object { Say "hash after: $_" }
$code = if ($h2.rc -ne 0) { 2 } elseif ($bad) { 1 } else { 0 }
Say "RESULT: $(@('OK', 'FAIL (a run, record, merge or check)', 'FAIL (window-4b hashes differ)')[$code]); bad $bad; $(Get-Date -Format 'HH:mm:ss')"
Save-Report
Write-Host "report: $(Join-Path $meta 'report.txt')"
exit $code
