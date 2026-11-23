# Agent 2 (session 3, 02:15): B tool prep, part 2 (Agent 1's GO conditions, 02:05). Builds nothing and writes nothing
# under snapB: syntax checks, patch-b-tools.py (build-snap.ps1 / stage-snap-bin.ps1), the review diffs (b-diffs.py ->
# B-diffs/), default-mode gen-check and snap-gate on snap1 with the final tool versions, and the negative tests:
# prep-b.py and run-b.ps1 must both refuse install\batch (4 spellings each) before touching anything.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\b-prep2.ps1
# Log: build/agent2/b-prep2.txt. The negative tests' own logs are moved to b-prep2-neg-snapB-{prep,run}.txt.
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$log = "$A\b-prep2.txt"
function Log([string]$m) { $line = "$(Get-Date -Format HH:mm:ss) $m"; $line | Out-File -Append -Encoding utf8 $log; Write-Host $line }
$fails = 0
function Ok([bool]$c, [string]$what) { Log ("{0} {1}" -f $(if ($c) { 'PASS' } else { 'FAIL' }), $what); if (-not $c) { $script:fails++ } }
function PsParse([string]$f) {
    $tok = $null; $err = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$tok, [ref]$err)
    Ok ($err.Count -eq 0) ("PS parse {0}: {1} error(s) {2}" -f (Split-Path -Leaf $f), $err.Count, (($err | Select-Object -First 3 | ForEach-Object { "line $($_.Extent.StartLineNumber): $($_.Message)" }) -join ' | '))
}
Set-Location $R
Log 'START b-prep2'
foreach ($d in 'snapB', 'snapB-off', 'devoffB-bin') { Ok (-not (Test-Path "$A\$d")) "$d does not exist yet" }
Ok (-not (Test-Path "$A\snapB-manifest-notes.txt")) 'snapB-manifest-notes.txt does not exist yet'
foreach ($f in 'snapB-prep.txt', 'snapB-run.txt', 'snapB-robocopy.log') {
    if (Test-Path "$A\$f") { $to = "$f.old-$(Get-Date -Format HHmmss)"; Move-Item -LiteralPath "$A\$f" "$A\$to"; Log "NOTE  an old $f was moved to $to" }
}
# 1. syntax
foreach ($py in 'prep-b.py', 'gen-check.py', 'snap-gate.py', 'patch-b-tools.py', 'b-diffs.py') {
    $o = (& python -m py_compile "$A\$py" 2>&1) -join ' | '
    Ok ($LASTEXITCODE -eq 0) "py_compile $py $o"
}
foreach ($ps in 'run-b.ps1', 'b-chain.ps1', 'stop-snap.ps1') { PsParse "$A\$ps" }
# 2. patch-b-tools.py, only onto the untouched originals (a re-run finds both patched; b-diffs.py then checks that each
#    == its .pre-B with exactly patch-b-tools.py's EDITS)
$orig = @(foreach ($f in 'build-snap.ps1', 'stage-snap-bin.ps1') { (Get-FileHash "$A\$f").Hash -eq (Get-FileHash "$A\$f.pre-B").Hash })
if ($orig[0] -and $orig[1]) {
    Log 'PASS build-snap.ps1 and stage-snap-bin.ps1 == their .pre-B before patching'
    $o = @(& python "$A\patch-b-tools.py" 2>&1); $c = $LASTEXITCODE; $t = $o -join ' | '
    Ok ($c -eq 0 -and $t -match 'patched build-snap\.ps1: 7 edits' -and $t -match 'patched stage-snap-bin\.ps1: 12 edits') "patch-b-tools.py: exit $c : $t"
} elseif (-not $orig[0] -and -not $orig[1]) {
    Log 'NOTE  build-snap.ps1 and stage-snap-bin.ps1 are already patched (re-run): b-diffs.py checks them against .pre-B + EDITS'
} else { Ok $false 'only one of build-snap.ps1 / stage-snap-bin.ps1 differs from its .pre-B' }
foreach ($f in 'build-snap.ps1', 'stage-snap-bin.ps1') { PsParse "$A\$f" }
# 3. the review diffs and their mechanical checks
$o = @(& python "$A\b-diffs.py" 2>&1); $c = $LASTEXITCODE
foreach ($l in $o) { Log "  $l" }
Ok ($c -eq 0 -and ($o -contains 'RESULT: PASS')) "b-diffs.py exit $c"
# 4. default-mode gen-check and snap-gate on snap1, with the final tool versions
$sw = [Diagnostics.Stopwatch]::StartNew()
& python "$A\gen-check.py" > "$A\b-prep2-gen-check.log" 2>&1
$c = $LASTEXITCODE; $g = @(Get-Content "$A\b-prep2-gen-check.log")
Ok ($c -eq 0 -and $g[-1] -eq 'RESULT: PASS') ("gen-check default (baseline vs snap1): exit {0}, {1:N1}s: {2}" -f $c, $sw.Elapsed.TotalSeconds, (($g | Where-Object { $_ -match '^# gen-check|^RESULT|^FAIL' }) -join ' | '))
$sw = [Diagnostics.Stopwatch]::StartNew()
& python "$A\snap-gate.py" "$A\snap1-off" > "$A\b-prep2-gate-snap1-off.log" 2>&1
$c = $LASTEXITCODE; $g = @(Get-Content "$A\b-prep2-gate-snap1-off.log")
Ok ($c -eq 0 -and ($g -contains 'RESULT: PASS')) ("snap-gate default snap1-off: exit {0}, {1:N1}s: {2}" -f $c, $sw.Elapsed.TotalSeconds, (($g | Where-Object { $_ -match '^# snap-gate|^headers|^rexglue_DIR|^RESULT|^  - ' }) -join ' | '))
# 5. negative tests: install\batch must be refused by both, before anything is read or written
$cases = @('build\agent9\install\batch', "$R\build\agent9\install\batch", 'build\agent9\install\batch-nolr\..\batch', 'build/agent9/install/batch')
foreach ($i in $cases) {
    $o = (& python "$A\prep-b.py" --install $i 2>&1) -join ' | '; $c = $LASTEXITCODE
    Ok ($c -eq 1 -and $o -match 'FAIL refusing install tree') "negative: prep-b.py --install $i -> exit $c : $o"
}
foreach ($i in $cases) {
    $o = (& powershell -NoProfile -ExecutionPolicy Bypass -File "$A\run-b.ps1" -Install $i 2>&1) -join ' | '; $c = $LASTEXITCODE
    Ok ($c -eq 3 -and $o -match 'STOP: refusing install tree') "negative: run-b.ps1 -Install $i -> exit $c : $o"
}
# positive controls: the real tree passes the guards and pins, then each stops before writing anything
$o = (& powershell -NoProfile -ExecutionPolicy Bypass -File "$A\run-b.ps1" 2>&1) -join ' | '; $c = $LASTEXITCODE
Ok ($c -eq 2 -and $o -match 'run prep-b\.py first') "control: run-b.ps1 (defaults) passes step 0, then exit $c : $o"
$o = (& python "$A\prep-b.py" --skip-copy 2>&1) -join ' | '; $c = $LASTEXITCODE
Ok ($c -eq 1 -and $o -match 'every file matches SHA256SUMS' -and $o -match 'FAIL snapB vs snap1: \d+ missing') "control: prep-b.py --skip-copy passes step 1 (install pins), then stops at step 2 (no snapB): exit $c : $o"
foreach ($d in 'snapB', 'snapB-off', 'devoffB-bin') { Ok (-not (Test-Path "$A\$d")) "after the tests: $d still does not exist" }
foreach ($f in 'snapB-robocopy.log', 'snapB-manifest-notes.txt') { Ok (-not (Test-Path "$A\$f")) "after the tests: no $f" }
$stamp = Get-Date -Format HHmm
foreach ($f in 'prep', 'run') { if (Test-Path "$A\snapB-$f.txt") { Move-Item -LiteralPath "$A\snapB-$f.txt" "$A\b-prep2-neg-snapB-$f-$stamp.txt" -Force } }
Log ("RESULT: {0}" -f $(if ($fails -eq 0) { 'PASS' } else { "FAIL ($fails)" }))
exit $(if ($fails -eq 0) { 0 } else { 1 })
