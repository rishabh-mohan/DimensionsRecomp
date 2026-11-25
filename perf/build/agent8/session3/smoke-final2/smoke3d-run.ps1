# smoke3d-run.ps1 - SMOKE-FINAL2 first-3D smoke of the final2 bin pair (M8, session 3), modelled on M3's
# build\agent3\session3\s33-rows\row3\row3-run.ps1. One approval (RUN-SMOKE3D.cmd) runs both arms back to back:
# devfinal2-bin (Xenos ship) then nativefinal2-bin (native), plain default arm (no -Cvar, no -Env), harness\run-game.ps1
# -Seconds 240 -GpuLog with the attract-long.txt virtual-pad route (START, A, A, then idle marks), WM_CLOSE at 240 s.
# Then smoke3d_post.py: clean exit, plain default, route, first 3D (xenos perf.csv draws >= 600; native PROXY), no_wait,
# check-defaults. Words (any order): dryrun, allowhidden, nativefirst.
#   dryrun      no game: verify-bins + preconditions (reported, not enforced), the real command lines, run-game -DryRun
#               for both arms (into smoke-final2\dryrun-runs, deleted afterwards), smoke3d_post.py on an old run (only
#               asserts it runs). Exit 0 = commands OK.
#   allowhidden run even if not on the interactive desktop ('Default'); the pad route also works on a hidden desktop.
#   nativefirst native arm first.
# Real run: refuses (exit 3) on verify-bins FAIL / pinned MANIFEST mismatch, WINDOW-HOLD.txt, day launcher state of
# waiting-for-quiet/running, a running game, an Agent 8 runner, or a hidden desktop. Stops after an arm with exit != 0.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'; $NativeFirst = $words -contains 'nativefirst'
$kit = $PSScriptRoot
$ws = (Resolve-Path (Join-Path $kit '..\..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'smoke3d_post.py'
$runsRoot = Join-Path $kit $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$Seconds = 240
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post') | Out-Null
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$log = Join-Path $kit "logs\smoke3d-run-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[smoke3d $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
$arms = @(
    [pscustomobject]@{ arm = 'xenos'; tag = 'final2-3d-xenos'; bin = (Join-Path $ws 'build\agent2\devfinal2-bin'); pin = '4A4A13EDFBFF6A5F32798837A4156256A5A58A2C44579F272B5147768E50982D' },
    [pscustomobject]@{ arm = 'native'; tag = 'final2-3d-native'; bin = (Join-Path $ws 'build\agent2\nativefinal2-bin'); pin = '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163' })
if ($NativeFirst) { [array]::Reverse($arms) }
Say "SMOKE-FINAL2 first-3D kit $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); order $(($arms | ForEach-Object { $_.arm }) -join ' then '); -Seconds $Seconds each"
Say "WS $ws"

function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # native stderr through 2>&1 must not throw (PS 5.1)
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $route, $vb, $post, (Join-Path $ws 'build\agent2\final\check-defaults.py'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
foreach ($a in $arms) {
    foreach ($p in @((Join-Path $a.bin 'legodimensions.exe'), (Join-Path $a.bin 'MANIFEST.txt'))) { if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } }
}
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
foreach ($a in $arms) {
    $rc = Run-Logged 'python' @('-B', $vb, $a.bin)
    if ($rc -ne 0) { $refuse += "verify-bins FAIL for $($a.bin) (exit $rc)" }
    $ms = (Get-FileHash -LiteralPath (Join-Path $a.bin 'MANIFEST.txt') -Algorithm SHA256).Hash
    Say "$($a.arm): MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $a.pin) { '= pin (final2/BIN-PINS.md)' } else { 'NOT the pin ' + $a.pin.Substring(0,16) })"
    if ($ms -ne $a.pin) { $refuse += "$($a.arm) MANIFEST sha256 is not the pin" }
}
$hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
if (Test-Path -LiteralPath $hold) { $refuse += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
$stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
if (Test-Path -LiteralPath $stateFile) {
    $st = (Get-Content -LiteralPath $stateFile -TotalCount 1)
    Say "day launcher: $st"
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

$rgArgs = { param($a, $root, $dry) $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $a.bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $a.tag, '-RunsRoot', $root, '-InputScript', $route); if ($dry) { $x += '-DryRun' }; $x }
function Cmd-Line($a, [string]$root) { 'powershell ' + ((& $rgArgs $a $root $false | ForEach-Object { if ("$_" -match '\s') { "`"$_`"" } else { "$_" } }) -join ' ') }

if ($DryRun) {
    $bad = 0
    foreach ($a in $arms) {
        Say "ARM $($a.arm.ToUpper()) COMMAND (real run): $(Cmd-Line $a (Join-Path $kit 'runs'))"
        $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $true)
        Say "ARM $($a.arm.ToUpper()) run-game -DryRun exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    $ref = Join-Path $ws 'build\agent3\runs\20261125-071741-s33-offsf'
    if (Test-Path -LiteralPath $ref) {
        $rc = Run-Logged 'python' @('-B', $post, '--arm', "xenos=$ref", '--out', (Join-Path $kit "logs\post-selftest-$stamp.txt"))
        Say "smoke3d_post.py on old run $ref exit $rc (FAILs expected: old bin has a cvar and older defaults; only checks it runs)"
        if (-not (Select-String -LiteralPath (Join-Path $kit "logs\post-selftest-$stamp.txt") -Pattern '^RESULT: ' -Quiet)) { $bad++ }
    } else { Say "post self-test skipped (no $ref)" }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say "dryrun-runs has reparse points: NOT deleted"; $bad++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say "dryrun-runs removed" }
    }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
$results = @()
$first = $true
foreach ($a in $arms) {
    if (-not $first) { Say 'settle 20 s between arms'; Start-Sleep -Seconds 20 }
    $first = $false
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
    if ($g.Count) { Say "REFUSED: a game is still running (pid $(($g | ForEach-Object Id) -join ','))"; exit 3 }
    $ARM = $a.arm.ToUpper()
    Say "ARM $ARM START $(Get-Date -Format HH:mm:ss): $(Cmd-Line $a $runsRoot)"
    $t0 = Get-Date
    $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $false)
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($a.tag)*" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '?' }
    Say "ARM $ARM DONE: run-game exit $rc, run $runDir"
    $results += [pscustomobject]@{ arm = $a.arm; rc = $rc; run = $runDir }
    if ($rc -ne 0) { Say "ARM $ARM exit ${rc}: stopping (no further arm)"; break }
}
$postOut = Join-Path $kit "post\smoke3d-post-$stamp.txt"
$postArgs = @('-B', $post, '--out', $postOut)
foreach ($r in $results) { if ($r.run -ne '?') { $postArgs += @('--arm', "$($r.arm)=$($r.run)") } }
$prc = if ($postArgs.Count -gt 4) { Run-Logged 'python' $postArgs } else { 2 }
Say "smoke3d_post.py exit $prc (report $postOut)"
Say "SMOKE3D DONE: $(($results | ForEach-Object { "$($_.arm) exit $($_.rc) $($_.run)" }) -join '; '); post $(if ($prc -eq 0) { 'ALL PASS' } else { "FAIL (exit $prc)" })"
exit $(if (@($results | Where-Object { $_.rc -ne 0 }).Count -or $results.Count -lt 2 -or $prc -ne 0) { 1 } else { 0 })
