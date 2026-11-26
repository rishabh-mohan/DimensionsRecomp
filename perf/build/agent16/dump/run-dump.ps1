# run-dump.ps1 - S5 phase 0.4(a), M16: one attract run of a COPY of nativefinal2-bin with LEGO_DUMP_MISSING_SHADERS,
# to dump the shaders the native AOT pack misses in the 3D attract (~43 of ~59 draws/frame skipped there).
# Modelled on build\agent8\session3\smoke-final2\smoke3d-run.ps1 (RUN-SMOKE3D.cmd B0B52007). Words (any order):
#   dryrun       no game: preconditions (reported), the copy + its hash check, the real command line, run-game -DryRun
#                (into dump\dryrun-runs, removed afterwards), dump_post.py self-test on an old trace. Exit 0 = pass.
#   allowhidden  run even if not on the interactive desktop ('Default').
#   long         -Seconds 540 (the route's own stop at ~472 s; also sees whether the attract loops) instead of 300.
# Real run: copies build\agent2\nativefinal2-bin (MANIFEST pin 4E5E2620...) to build\agent16\dump\bin-nf2 (every file
# sha256-checked against the pin dir; reused if already identical), then harness\run-game.ps1 -BinDir <copy>
# -Seconds 300 -GpuLog -InputScript harness\routes\attract-long.txt -RunsRoot build\agent16\dump\runs
# -Env LEGO_DUMP_MISSING_SHADERS=<abs dump root>;LEGO_NATIVE_TRACE_DIR=<abs trace dir>. Plain default otherwise (as the
# final2 smoke, which reached native first 3D). FUNCTIONAL ONLY: the dump env keeps the full shader lookup path (miss
# cache OFF) and the trace turns off fast paths and saves a frame every 5 s; never timed.
# Then dump_post.py: run sanity, AOT-miss lines, every dumped file (sha256; the 4 s35 containers marked KNOWN), the
# missing-draw count from the trace (the 'before' number), and stages NEW candidates into dump\pack-input-<stamp>.
# Refuses (exit 3) on: pin MANIFEST mismatch, verify-bins FAIL, WINDOW-HOLD.txt, day launcher busy, a running game,
# an Agent 8 runner, a hidden desktop (unless allowhidden). run-game only closes the PID it launched.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'
$Seconds = if ($words -contains 'long') { 540 } else { 300 }
$kit = $PSScriptRoot                                   # build\agent16\dump
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'dump_post.py'
$pinDir = Join-Path $ws 'build\agent2\nativefinal2-bin'
$pin = '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163'
$copyDir = Join-Path $kit 'bin-nf2'
$runsRoot = Join-Path $kit $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$dumpRoot = Join-Path $kit "shader-dumps-$stamp"
$traceDir = Join-Path $kit "trace-$stamp"
$stage = Join-Path $kit "pack-input-$stamp"
$tag = 'dump-attract-nf2'
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post') | Out-Null
$log = Join-Path $kit "logs\run-dump-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[dump $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}
Say "S5 0.4(a) attract shader dump $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); -Seconds $Seconds; WS $ws"

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $route, $vb, $post, (Join-Path $pinDir 'legodimensions.exe'), (Join-Path $pinDir 'MANIFEST.txt'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
$ms = (Get-FileHash -LiteralPath (Join-Path $pinDir 'MANIFEST.txt') -Algorithm SHA256).Hash
Say "nativefinal2-bin MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $pin) { '= pin' } else { 'NOT the pin ' + $pin.Substring(0,16) })"
if ($ms -ne $pin) { $refuse += 'nativefinal2-bin MANIFEST is not the pin' }
$rc = Run-Logged 'python' @('-B', $vb, $pinDir)
if ($rc -ne 0) { $refuse += "verify-bins FAIL for $pinDir (exit $rc)" }
$hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
if (Test-Path -LiteralPath $hold) { $refuse += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
$stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
if (Test-Path -LiteralPath $stateFile) {
    $st = (Get-Content -LiteralPath $stateFile -TotalCount 1); Say "day launcher: $st"
    if ($st -match '(?i)waiting-for-quiet|\brunning\b') { $refuse += "day launcher busy ($st)" }
}
$g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
if ($g.Count) { $refuse += "a game is running (pid $(($g | ForEach-Object Id) -join ','))" }
. (Join-Path $ws 'harness\guard.ps1')
$runners = @(Get-ActiveRunners)
if ($runners.Count) { $refuse += "Agent 8 runner active: $($runners -join '; ')" }
Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
$desk = [LdHarness]::DesktopName()
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: not visible to the user)' })"
if ($desk -ne 'Default' -and -not $AllowHidden) { $refuse += "not on the interactive desktop ($desk)" }
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

# --- the work copy (the pin dir is only read) ---
$srcFiles = @(Get-ChildItem -LiteralPath $pinDir -File)
if (@(Get-ChildItem -LiteralPath $pinDir -Directory).Count) { Say 'FAIL pin dir has subdirectories (not expected)'; exit 2 }
New-Item -ItemType Directory -Force -Path $copyDir | Out-Null
$copied = 0; $bad = 0
foreach ($f in $srcFiles) {
    $dst = Join-Path $copyDir $f.Name
    $hs = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    if (-not ((Test-Path -LiteralPath $dst) -and (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -eq $hs)) {
        Copy-Item -LiteralPath $f.FullName -Destination $dst -Force; $copied++
    }
    if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ne $hs) { Say "FAIL copy hash $($f.Name)"; $bad++ }
}
$extra = @(Get-ChildItem -LiteralPath $copyDir -File | Where-Object { $srcFiles.Name -notcontains $_.Name })
foreach ($e in $extra) { Say "note: extra file in the copy dir (not mirrored by the pin): $($e.Name)"; $bad++ }
Say "work copy $copyDir`: $($srcFiles.Count) files, $copied copied now, $(if ($bad) { "$bad PROBLEMS" } else { 'all sha256 = pin dir' })"
if ($bad) { exit 2 }
$rc = Run-Logged 'python' @('-B', $vb, $copyDir)
if ($rc -ne 0) { Say "FAIL verify-bins on the copy (exit $rc)"; exit 2 }

$envs = "LEGO_DUMP_MISSING_SHADERS=$dumpRoot;LEGO_NATIVE_TRACE_DIR=$traceDir"
$rgArgs = { param($root, $dry) $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $copyDir, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $tag, '-RunsRoot', $root, '-InputScript', $route, '-Env', $envs); if ($dry) { $x += '-DryRun' }; $x }
function Cmd-Line([string]$root) { 'powershell ' + ((& $rgArgs $root $false | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

if ($DryRun) {
    $bad = 0
    Say "COMMAND (real run): $(Cmd-Line (Join-Path $kit 'runs'))"
    $rc = Run-Logged 'powershell' (& $rgArgs $runsRoot $true)
    Say "run-game -DryRun exit $rc"; if ($rc -ne 0) { $bad++ }
    $ref = Join-Path $ws 'build\agent3\s4a\trace\r6off-t\events.tsv'
    if (Test-Path -LiteralPath $ref) {
        $o = Join-Path $kit "logs\post-selftest-$stamp.txt"
        $rc = Run-Logged 'python' @('-B', $post, '--trace-only', $ref, '--out', $o)
        Say "dump_post.py trace self-test exit $rc"
        if ($rc -ne 0 -or -not (Select-String -LiteralPath $o -Pattern '^RESULT: ' -Quiet)) { $bad++ }
    } else { Say "post self-test skipped (no $ref)" }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say 'dryrun-runs has reparse points: NOT deleted'; $bad++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say 'dryrun-runs removed' }
    }
    foreach ($d in @($dumpRoot, $traceDir)) { if (Test-Path -LiteralPath $d) { Say "note: $d exists after a dry run"; $bad++ } }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
Say "START: $(Cmd-Line $runsRoot)"
$t0 = Get-Date
$rc = Run-Logged 'powershell' (& $rgArgs $runsRoot $false)
$run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$tag*" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
$runDir = if ($run.Count) { $run[0].FullName } else { '' }
Say "run-game exit $rc, run $(if ($runDir) { $runDir } else { '?' }), $([int]((Get-Date) - $t0).TotalSeconds) s"
$postOut = Join-Path $kit "post\dump-post-$stamp.txt"
$prc = 2
if ($runDir) { $prc = Run-Logged 'python' @('-B', $post, '--run', $runDir, '--dumps', $dumpRoot, '--trace', $traceDir, '--stage', $stage, '--out', $postOut) }
# SHA256SUMS of everything the run produced that the pack step reads
$sums = Join-Path $kit "post\SHA256SUMS-$stamp.txt"
$items = @()
foreach ($d in @($dumpRoot, $stage)) { if (Test-Path -LiteralPath $d) { $items += Get-ChildItem -LiteralPath $d -Recurse -File } }
if ($runDir) { foreach ($n in 'game.log', 'run.json', 'input.csv') { $p = Join-Path $runDir $n; if (Test-Path -LiteralPath $p) { $items += Get-Item -LiteralPath $p } } }
$items | ForEach-Object { "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)  $($_.Length)  $($_.FullName.Substring($ws.Length + 1))" } | Set-Content -LiteralPath $sums -Encoding ascii
Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp run=$runDir exit=$rc post=$prc dumps=$dumpRoot trace=$traceDir stage=$stage" -Encoding ascii
Say "DUMP DONE: run-game exit $rc; post exit $prc ($postOut); sums $sums; dumps $dumpRoot; pack input $stage"
exit $(if ($rc -ne 0 -or $prc -ne 0) { 1 } else { 0 })
