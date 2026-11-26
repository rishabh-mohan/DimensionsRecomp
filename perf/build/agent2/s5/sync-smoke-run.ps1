# sync-smoke-run.ps1 - S5 sync-pipeline diag smoke on devs5sync-bin (M2), modelled on M8's
# build\agent8\session3\smoke-final2\smoke3d-run.ps1. One approval (RUN-SYNC-SMOKE.cmd) runs two arms back to back on
# build\agent2\s5\devs5sync-bin (MANIFEST pin 2235E6DE...), harness\run-game.ps1 -Seconds 240 -GpuLog, attract-long.txt
# virtual-pad route, WM_CLOSE at 240 s (run-game closes only the game it started):
#   off  plain default (no -Cvar)                      D3: no Initialize line, 0 'sync pipeline #' lines (+ smoke3d gates)
#   on   d3d12_log_sync_pipeline_creation=true;slow_frame_log_ms=1
#                                                     D3: the Initialize line once; ATTRIBUTION ONLY (D2), not timing
# Then sync_smoke_post.py (report in sync-smoke\post). Words (any order): dryrun, allowhidden, onfirst.
#   dryrun      no game: verify-bins + preconditions (reported, not enforced), the real command lines, run-game -DryRun
#               for both arms (into sync-smoke\dryrun-runs, deleted afterwards), sync_smoke_post.py --selftest on
#               sync-smoke\selftest-synth.log (join must match). Exit 0 = commands OK.
# Real run: refuses (exit 3) on verify-bins FAIL / MANIFEST not the pin, WINDOW-HOLD.txt, day launcher state of
# waiting-for-quiet/running, a running game, an Agent 8 runner, or a hidden desktop. Stops after an arm with exit != 0.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'; $OnFirst = $words -contains 'onfirst'
$kit = $PSScriptRoot
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'sync_smoke_post.py'
$out = Join-Path $kit 'sync-smoke'
$runsRoot = Join-Path $out $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$Seconds = 240
$bin = Join-Path $ws 'build\agent2\s5\devs5sync-bin'
$pin = '2235E6DED44A6B17D37C6FF0EB24B9D84E7D323D71CBF280AFF71884A7CDF2C9'
New-Item -ItemType Directory -Force -Path (Join-Path $out 'logs'), (Join-Path $out 'post') | Out-Null
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$log = Join-Path $out "logs\sync-smoke-run-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[sync-smoke $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
$arms = @(
    [pscustomobject]@{ arm = 'off'; tag = 's5sync-off'; cvar = '' },
    [pscustomobject]@{ arm = 'on'; tag = 's5sync-on'; cvar = 'd3d12_log_sync_pipeline_creation=true;slow_frame_log_ms=1' })
if ($OnFirst) { [array]::Reverse($arms) }
Say "S5 SYNC-SMOKE kit $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); bin $bin; order $(($arms | ForEach-Object { $_.arm }) -join ' then '); -Seconds $Seconds each"
Say "WS $ws"

function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # native stderr through 2>&1 must not throw (PS 5.1)
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $route, $vb, $post, (Join-Path $ws 'build\agent2\final\check-defaults.py'),
        (Join-Path $ws 'build\agent8\session3\smoke-final2\smoke3d_post.py'), (Join-Path $bin 'legodimensions.exe'), (Join-Path $bin 'MANIFEST.txt'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
$rc = Run-Logged 'python' @('-B', $vb, $bin)
if ($rc -ne 0) { $refuse += "verify-bins FAIL for $bin (exit $rc)" }
$ms = (Get-FileHash -LiteralPath (Join-Path $bin 'MANIFEST.txt') -Algorithm SHA256).Hash
Say "MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $pin) { '= pin (s5/sync-bin/BIN-PINS.md)' } else { 'NOT the pin ' + $pin.Substring(0,16) })"
if ($ms -ne $pin) { $refuse += 'MANIFEST sha256 is not the pin' }
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

$rgArgs = { param($a, $root, $dry)
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $a.tag, '-RunsRoot', $root, '-InputScript', $route)
    if ($a.cvar) { $x += @('-Cvar', $a.cvar) }
    if ($dry) { $x += '-DryRun' }; $x }
function Cmd-Line($a, [string]$root) { 'powershell ' + ((& $rgArgs $a $root $false | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

if ($DryRun) {
    $bad = 0
    foreach ($a in $arms) {
        Say "ARM $($a.arm.ToUpper()) COMMAND (real run): $(Cmd-Line $a (Join-Path $out 'runs'))"
        $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $true)
        Say "ARM $($a.arm.ToUpper()) run-game -DryRun exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    # selftest-synth.log = s33 game.2.log lines 7561-7575 with an Initialize line and 8 synthetic 'sync pipeline #' lines
    # (format of sync-log.diff) before slow frame #7366; the join must give 8 lines / 321.6 ms / 8 no-PS.
    $ref = Join-Path $out 'selftest-synth.log'
    if (Test-Path -LiteralPath $ref) {
        $st = Join-Path $out "logs\post-selftest-$stamp.txt"
        $rc = Run-Logged 'python' @('-B', $post, '--selftest', $ref, '--out', $st)
        Say "sync_smoke_post.py --selftest on $ref exit $rc"
        if ($rc -ne 0 -or -not (Select-String -LiteralPath $st -SimpleMatch -Quiet -Pattern 'create 322.0 (8x) new 67 | sync 8, 321.6 ms, ps none 8')) { Say 'selftest join FAIL'; $bad++ }
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
$postOut = Join-Path $out "post\sync-smoke-post-$stamp.txt"
$postArgs = @('-B', $post, '--out', $postOut)
foreach ($r in $results) { if ($r.run -ne '?') { $postArgs += @("--$($r.arm)", $r.run) } }
$prc = if ($postArgs.Count -gt 4) { Run-Logged 'python' $postArgs } else { 2 }
Say "sync_smoke_post.py exit $prc (report $postOut)"
Say "SYNC-SMOKE DONE: $(($results | ForEach-Object { "$($_.arm) exit $($_.rc) $($_.run)" }) -join '; '); post $(if ($prc -eq 0) { 'ALL PASS' } else { "FAIL (exit $prc)" })"
exit $(if (@($results | Where-Object { $_.rc -ne 0 }).Count -or $results.Count -lt 2 -or $prc -ne 0) { 1 } else { 0 })
