# smoke-run.ps1 - S5 phase 0.4c, M16: native4bp attract smoke (functional) with game-window screenshots.
# Words (any order):
#   dryrun       no game: preconditions (reported), copies + hash checks, the real command lines, run-game -DryRun,
#                watcher + smoke_post self-tests. Exit 0 = pass.
#   allowhidden  run even if not on the interactive desktop ('Default') (no screenshots then).
#   withref      after the native4bp arm, the same arm on nativefinal2 (build\agent16\dump\bin-nf2, sha256 = pin dir)
#                as the same-conditions "before" and the screenshot reference (~+6 min).
#   refonly      only the nf2 ref arm (~6 min); the 4bp arm of the newest real smoke report is reused for smoke_post.
# Arm: harness\run-game.ps1 -BinDir <copy> -Seconds 300 -GpuLog -InputScript harness\routes\attract-long.txt
#      -RunsRoot build\agent16\smoke4bp\runs -Env LEGO_NATIVE_TRACE_DIR=<abs trace dir>. Nothing else: miss cache etc.
#      at the bin's defaults. FUNCTIONAL ONLY (the trace costs frame time): never timed.
# native4bp bin = build\agent16\pack\native4bp-bin, accepted only if its MANIFEST.txt sha256 equals manifest= in
# PIN-native4bp.txt (written by M16 after checking E16.1's build; optional fp=<16 hex> = expected fingerprint).
# smoke-watch.ps1 (hidden window) saves <arm>-idle-60/120/180.png (game window client area) into shots\<stamp>.
# smoke_post.py: clean exit, route, fingerprint, first 3D, AOT-miss lines, trace missing draws in the 3D window
# (after vs before: the nf2 arm if withref, else the 0.4a dump trace), draws/frame, new warning types, screenshots.
# Refuses (exit 3): pin mismatch or missing, verify-bins FAIL, WINDOW-HOLD.txt, day launcher busy, a running game,
# an Agent 8 runner, a hidden desktop (unless allowhidden). run-game only closes the PID it launched; this script only
# stops the watcher it started.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'; $WithRef = $words -contains 'withref'
# refonly: run only the nf2 ref arm; smoke_post reuses the 4bp arm of the newest real smoke report (post\smoke-*.txt).
$RefOnly = $words -contains 'refonly'; if ($RefOnly) { $WithRef = $true }
$Seconds = 300
$kit = $PSScriptRoot                                   # build\agent16\smoke4bp
$a16 = Split-Path -Parent $kit
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'smoke_post.py'
$watch = Join-Path $kit 'smoke-watch.ps1'
$bpDir = Join-Path $a16 'pack\native4bp-bin'
$pinFile = Join-Path $kit 'PIN-native4bp.txt'
$nfPinDir = Join-Path $ws 'build\agent2\nativefinal2-bin'
$nfPin = '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163'
$nfCopy = Join-Path $a16 'dump\bin-nf2'
$bpCopy = Join-Path $kit 'bin-4bp'
$dumpLatest = Join-Path $a16 'dump\LATEST.txt'
$runsRoot = Join-Path $kit $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$shots = Join-Path $kit "shots\$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post') | Out-Null
$log = Join-Path $kit "logs\smoke-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[smoke4bp $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}
function Sync-Copy([string]$src, [string]$dst) {
    # mirror the flat bin dir $src into $dst (sha256-checked; reused when identical); returns the problem count
    $files = @(Get-ChildItem -LiteralPath $src -File)
    if (@(Get-ChildItem -LiteralPath $src -Directory).Count) { Say "FAIL $src has subdirectories (not expected)"; return 1 }
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    $bad = 0; $n = 0
    foreach ($f in $files) {
        $t = Join-Path $dst $f.Name; $hs = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
        if (-not ((Test-Path -LiteralPath $t) -and (Get-FileHash -LiteralPath $t -Algorithm SHA256).Hash -eq $hs)) { Copy-Item -LiteralPath $f.FullName -Destination $t -Force; $n++ }
        if ((Get-FileHash -LiteralPath $t -Algorithm SHA256).Hash -ne $hs) { Say "FAIL copy hash $($f.Name)"; $bad++ }
    }
    foreach ($e in @(Get-ChildItem -LiteralPath $dst -File | Where-Object { $files.Name -notcontains $_.Name })) { Say "FAIL extra file in $dst`: $($e.Name)"; $bad++ }
    Say "copy $dst`: $($files.Count) files, $n copied now, $(if ($bad) { "$bad PROBLEMS" } else { 'all sha256 = source' })"
    $bad
}
Say "S5 0.4c native4bp smoke $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); arms $(if ($RefOnly) { 'nf2 ref only (4bp arm reused)' } else { '4bp' + $(if ($WithRef) { ' + nf2 ref' }) }); -Seconds $Seconds; WS $ws"

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $route, $vb, $post, $watch, (Join-Path $nfPinDir 'MANIFEST.txt'))) { if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } }
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
$pin = @{}
if (Test-Path -LiteralPath $pinFile) { foreach ($l in Get-Content -LiteralPath $pinFile) { if ($l -match '^\s*(\w+)=(\S+)') { $pin[$Matches[1]] = $Matches[2] } } }
$bpOk = $false
if (-not $pin['manifest']) { $refuse += "no manifest= in $pinFile (native4bp not pinned yet)" }
elseif (-not (Test-Path -LiteralPath (Join-Path $bpDir 'MANIFEST.txt'))) { $refuse += "no $bpDir\MANIFEST.txt" }
else {
    $ms = (Get-FileHash -LiteralPath (Join-Path $bpDir 'MANIFEST.txt') -Algorithm SHA256).Hash
    Say "native4bp-bin MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $pin['manifest'].ToUpper()) { '= pin' } else { 'NOT the pin ' + $pin['manifest'].Substring(0,16) })"
    if ($ms -ne $pin['manifest'].ToUpper()) { $refuse += 'native4bp-bin MANIFEST is not the pin' }
    else {
        $rc = Run-Logged 'python' @('-B', $vb, $bpDir)
        if ($rc -ne 0) { $refuse += "verify-bins FAIL for $bpDir (exit $rc)" } else { $bpOk = $true }
    }
}
if ($pin['fp']) { Say "expected native4bp fingerprint $($pin['fp'])" }
$ms = (Get-FileHash -LiteralPath (Join-Path $nfPinDir 'MANIFEST.txt') -Algorithm SHA256).Hash
if ($ms -ne $nfPin) { $refuse += 'nativefinal2-bin MANIFEST is not the pin' }
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
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: not visible to the user, no screenshots)' })"
if ($desk -ne 'Default' -and -not $AllowHidden) { $refuse += "not on the interactive desktop ($desk)" }
# the before trace (0.4a dump run)
$before = ''; $beforeLog = ''
if (Test-Path -LiteralPath $dumpLatest) {
    $lt = Get-Content -LiteralPath $dumpLatest -TotalCount 1
    if ($lt -match 'trace=(\S+)') { $before = Join-Path $Matches[1] 'events.tsv' }
    if ($lt -match 'run=(\S+)') { $beforeLog = Join-Path $Matches[1] 'game.log' }
}
if (-not ($before -and (Test-Path -LiteralPath $before))) { $refuse += "no 0.4a dump trace (dump\LATEST.txt)" } else { Say "before trace $before" }
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

# --- work copies (pinned dirs are only read) ---
$bad = 0
if ($bpOk) { $bad += Sync-Copy $bpDir $bpCopy; if (-not $bad) { $rc = Run-Logged 'python' @('-B', $vb, $bpCopy); if ($rc -ne 0) { Say "FAIL verify-bins on $bpCopy"; $bad++ } } }
if ($WithRef -or -not $bpOk) { $bad += Sync-Copy $nfPinDir $nfCopy }
if ($bad) { exit 2 }

$arms = @()
$prev4bp = ''
if ($RefOnly) {
    # the 4bp arm of the newest real smoke report: "== arm 4bp: run <dir>" in post\smoke-<S>.txt; trace-4bp-<S>, shots\<S>
    foreach ($r in @(Get-ChildItem -LiteralPath (Join-Path $kit 'post') -Filter 'smoke-2*.txt' -ErrorAction SilentlyContinue | Sort-Object Name -Descending)) {
        $m = Select-String -LiteralPath $r.FullName -Pattern '^== arm 4bp: run (.+)$' | Select-Object -First 1
        if (-not $m) { continue }
        $s = $r.BaseName.Substring(6); $rd = $m.Matches[0].Groups[1].Value.Trim()
        $tr4 = Join-Path $kit "trace-4bp-$s"; $sh4 = Join-Path $kit "shots\$s"
        if ((Test-Path -LiteralPath $rd) -and (Test-Path -LiteralPath $tr4)) { $prev4bp = "4bp=$rd,$tr4,$sh4"; break }
    }
    if (-not $prev4bp) { Say 'FAIL refonly: no earlier real 4bp arm (post\smoke-*.txt with its run and trace dirs)'; exit 2 }
    Say "refonly: 4bp arm reused from $prev4bp"
}
if (-not $RefOnly) { $arms += [pscustomobject]@{ name = '4bp'; bin = $(if ($bpOk) { $bpCopy } else { $nfCopy }); tag = 'smoke-4bp' } }
if ($WithRef) { $arms += [pscustomobject]@{ name = 'nf2'; bin = $nfCopy; tag = 'smoke-nf2ref' } }
function Rg-Args($arm, [string]$root, [string]$trace, [bool]$dry) {
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $arm.bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $arm.tag,
        '-RunsRoot', $root, '-InputScript', $route, '-Env', "LEGO_NATIVE_TRACE_DIR=$trace")
    if ($dry) { $x += '-DryRun' }; $x
}
function Cmd-Line([string[]]$x) { 'powershell ' + (($x | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

if ($DryRun) {
    $bad = 0
    if (-not $bpOk) { Say 'note: native4bp not pinned yet; the dry run uses the nf2 copy as a stand-in BinDir' }
    foreach ($arm in $arms) {
        $tr = Join-Path $kit "trace-$($arm.name)-$stamp"
        Say "COMMAND (real run, arm $($arm.name)): $(Cmd-Line (Rg-Args $arm (Join-Path $kit 'runs') $tr $false))"
        $rc = Run-Logged 'powershell' (Rg-Args $arm $runsRoot $tr $true)
        Say "run-game -DryRun ($($arm.name)) exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    $csv = ''; if ($beforeLog) { $csv = Join-Path (Split-Path -Parent $beforeLog) 'input.csv' }
    $rc = Run-Logged 'powershell' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $watch, '-Arm', 'dry', '-OutDir', (Join-Path $kit 'logs\watch-selftest'), '-SelfTest', '-SelfTestCsv', $csv)
    Say "watcher self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    if ($before) {
        $rc = Run-Logged 'python' @('-B', $post, '--selftest', $before, '--out', (Join-Path $kit "logs\post-selftest-$stamp.txt"))
        Say "smoke_post self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    if ($prev4bp) {
        # refonly wiring: the reused 4bp arm + a stand-in nf2 arm (the same dirs; its fingerprint check FAILs by design)
        $ro = Join-Path $kit "logs\post-refonly-dry-$stamp.txt"
        $rc = Run-Logged 'python' @('-B', $post, '--arm', $prev4bp, '--arm', ('nf2=' + $prev4bp.Substring(4)), '--before', $before, '--out', $ro)
        $ok = [bool](Select-String -LiteralPath $ro -Pattern '^RESULT: ' -ErrorAction SilentlyContinue) -and [bool](Select-String -LiteralPath $ro -Pattern '^== arm nf2' -ErrorAction SilentlyContinue)
        Say "refonly smoke_post wiring (stand-in nf2 arm) exit $rc, report $(if ($ok) { 'ok' } else { 'BAD' })"; if (-not $ok) { $bad++ }
    }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say 'dryrun-runs has reparse points: NOT deleted'; $bad++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say 'dryrun-runs removed' }
    }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })$(if (-not $bpOk) { ' (native4bp not pinned yet: a real run would refuse)' })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
$postArgs = @('-B', $post)
if ($prev4bp) { $postArgs += @('--arm', $prev4bp) }
$rcAll = 0
foreach ($arm in $arms) {
    $tr = Join-Path $kit "trace-$($arm.name)-$stamp"
    $x = Rg-Args $arm $runsRoot $tr $false
    $wp = Start-Process -FilePath 'powershell' -WindowStyle Hidden -PassThru -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        "`"$watch`"", '-Arm', $arm.name, '-RunsRoot', "`"$runsRoot`"", '-Tag', $arm.tag, '-OutDir', "`"$shots`"", '-Seconds', "$Seconds")
    Say "watcher pid $($wp.Id) for arm $($arm.name)"
    Say "START $($arm.name): $(Cmd-Line $x)"
    $t0 = Get-Date
    $rc = Run-Logged 'powershell' $x
    if ($rc -ne 0) { $rcAll = 1 }
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($arm.tag)*" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '' }
    Say "run-game ($($arm.name)) exit $rc, run $(if ($runDir) { $runDir } else { '?' }), $([int]((Get-Date) - $t0).TotalSeconds) s"
    if (-not $wp.WaitForExit(60000)) { Say "watcher $($wp.Id) still running after 60 s: stopping it (started by this script)"; Stop-Process -Id $wp.Id -Force -ErrorAction SilentlyContinue }
    if ($runDir) { $postArgs += @('--arm', "$($arm.name)=$runDir,$tr,$shots") }
}
$postOut = Join-Path $kit "post\smoke-$stamp.txt"
$postArgs += @('--before', $before, '--before-log', $beforeLog, '--out', $postOut)
if ($pin['fp']) { $postArgs += @('--expect-fp', $pin['fp']) }
$prc = Run-Logged 'python' $postArgs
$verdict = (Select-String -LiteralPath $postOut -Pattern '^RESULT: ' -ErrorAction SilentlyContinue | Select-Object -Last 1).Line
$sums = Join-Path $kit "post\SHA256SUMS-$stamp.txt"
$items = @(Get-Item -LiteralPath $postOut -ErrorAction SilentlyContinue)
if (Test-Path -LiteralPath $shots) { $items += Get-ChildItem -LiteralPath $shots -File }
$items | ForEach-Object { "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)  $($_.Length)  $($_.FullName.Substring($ws.Length + 1))" } | Set-Content -LiteralPath $sums -Encoding ascii
Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp exit=$rcAll post=$prc shots=$shots report=$postOut $verdict" -Encoding ascii
Say "SMOKE DONE: run-game $(if ($rcAll) { 'had a non-zero exit' } else { 'exit 0' }); post exit $prc; $verdict; shots $shots; report $postOut"
exit $(if ($rcAll -ne 0 -or $prc -ne 0) { 1 } else { 0 })
