# row3-run.ps1 - #33 row 3 (TESTPLAN section 2 row 3; section 4 condition 3): both arms back to back on the VISIBLE
# desktop, from ONE approval (RUN-ROW3.cmd). M3, session 3. Words (any order): dryrun, noauto, onfirst, allowhidden.
#   dryrun      no game: prints the full command lines, runs harness\run-game.ps1 -DryRun for both arms (into
#               row3\dryrun-runs, deleted afterwards), replays two existing runs through the watcher and self-tests
#               row3_post.py. Safe from a hidden agent shell. Exit 0 = all checks passed.
#   noauto      no automatic game-window captures (manual computer-cli screenshots only).
#   onfirst     ON then OFF (TESTPLAN row 3 text order); default OFF then ON (Overseer's brief).
#   allowhidden run even if this process is not on the interactive desktop ('Default'); never needed for row 3.
# Real run: refuses (exit 3) on WINDOW-HOLD.txt, a day launcher state of waiting-for-quiet/running, a running game,
# an Agent 8 runner, or a hidden desktop. Per arm: watcher (row3-watch.ps1) + run-game (cold, -Seconds 540, attract-long
# pad route, WM_CLOSE at the end = self-closing). Stops after an arm with exit != 0. Then row3_post.py.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $NoAuto = $words -contains 'noauto'; $OnFirst = $words -contains 'onfirst'; $AllowHidden = $words -contains 'allowhidden'
$row3 = $PSScriptRoot
$ws = (Resolve-Path (Join-Path $row3 '..\..\..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$bin = Join-Path $ws 'build\agent2\devoff4b-s33-bin'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$runsRoot = Join-Path $row3 $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$Seconds = 540
New-Item -ItemType Directory -Force -Path (Join-Path $row3 'logs') | Out-Null
$log = Join-Path $row3 "logs\row3-run-$(if ($DryRun) { 'dryrun-' })$(Get-Date -Format yyyyMMdd-HHmmss).txt"
function Say([string]$s) { $l = "[row3 $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
$arms = @(
    [pscustomobject]@{ arm = 'off'; tag = 's33-row3-off'; cvar = 'slow_frame_log_ms=1'; ref = 'build\agent3\runs\20261125-071741-s33-offsf' },
    [pscustomobject]@{ arm = 'on'; tag = 's33-row3-on'; cvar = 'slow_frame_log_ms=1;d3d12_pipeline_creation_no_wait=true'; ref = 'build\agent3\runs\20261125-095932-s33-onsf' })
if ($OnFirst) { [array]::Reverse($arms) }
Say "#33 row 3 kit $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN (visible desktop)' }); order $(($arms | ForEach-Object { $_.arm.ToUpper() }) -join ' then '); auto capture $(if ($NoAuto) { 'off' } else { 'on' })"
Say "WS $ws"

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $bin, (Join-Path $bin 'legodimensions.exe'), (Join-Path $bin 'MANIFEST.txt'), $route, (Join-Path $row3 'row3-watch.ps1'), (Join-Path $row3 'row3_post.py'), (Join-Path $row3 'row3-schedule.json'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
$exeSha = (Get-FileHash -LiteralPath (Join-Path $bin 'legodimensions.exe') -Algorithm SHA256).Hash
$man = Get-Content -LiteralPath (Join-Path $bin 'MANIFEST.txt') -Raw
Say "bin $bin; legodimensions.exe sha256 $($exeSha.Substring(0,16)) $(if ($man -match $exeSha) { '= MANIFEST' } else { 'NOT IN MANIFEST' })"
if ($man -notmatch $exeSha) { $refuse += 'exe sha256 not in the bin MANIFEST' }
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

function Cmd-Line($a, [string]$root, [switch]$Dry) {
    $parts = @('powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$rg`"", '-BinDir', "`"$bin`"", '-Seconds', $Seconds, '-GpuLog',
        '-Tag', $a.tag, '-RunsRoot', "`"$root`"", '-InputScript', "`"$route`"", '-Cvar', "`"$($a.cvar)`"")
    if ($Dry) { $parts += '-DryRun' }
    $parts -join ' '
}
function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # native stderr through 2>&1 must not throw (PS 5.1)
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}
$rgArgs = { param($a, $root, $dry) $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $a.tag, '-RunsRoot', $root, '-InputScript', $route, '-Cvar', $a.cvar); if ($dry) { $x += '-DryRun' }; $x }

if ($DryRun) {
    $bad = 0
    foreach ($a in $arms) {
        Say "ARM $($a.arm.ToUpper()) COMMAND (real run): $(Cmd-Line $a (Join-Path $row3 'runs'))"
        Say "ARM $($a.arm.ToUpper()) watcher: powershell -NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $row3 'row3-watch.ps1')`" -Arm $($a.arm) -RunsRoot `"$(Join-Path $row3 'runs')`" -Tag $($a.tag) -OutDir `"$row3`" -Seconds $Seconds$(if ($NoAuto) { ' -NoAuto' })"
        $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $true)
        Say "ARM $($a.arm.ToUpper()) run-game -DryRun exit $rc"; if ($rc -ne 0) { $bad++ }
        $ref = Join-Path $ws $a.ref
        $rc = Run-Logged 'powershell' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $row3 'row3-watch.ps1'), '-Arm', $a.arm, '-OutDir', (Join-Path $row3 'dryrun-out'), '-SelfTestRun', $ref)
        Say "ARM $($a.arm.ToUpper()) watcher self-test (replay $($a.ref)) exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    $rc = Run-Logged 'python' @('-B', (Join-Path $row3 'row3_post.py'), '--selftest', '--arm', "off=$(Join-Path $ws 'build\agent3\runs\20261125-111422-s33-offd')", '--arm', "on=$(Join-Path $ws 'build\agent3\runs\20261125-123609-s33-ond')", '--row3', (Join-Path $row3 'dryrun-out'))
    Say "row3_post.py --selftest exit $rc"; if ($rc -ne 0) { $bad++ }
    # The dry-run run dirs are hard-link mirrors of the bin (no reparse points); remove them.
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
    Say "ARM $ARM START: $(Cmd-Line $a $runsRoot)"
    $wargs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$(Join-Path $row3 'row3-watch.ps1')`"", '-Arm', $a.arm, '-RunsRoot', "`"$runsRoot`"", '-Tag', $a.tag, '-OutDir', "`"$row3`"", '-Seconds', "$Seconds")
    if ($NoAuto) { $wargs += '-NoAuto' }
    $w = Start-Process powershell -ArgumentList $wargs -NoNewWindow -PassThru
    $t0 = Get-Date
    $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $false)
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($a.tag)*" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '?' }
    if (-not $w.WaitForExit(60000)) { Say "watcher still running after 60 s: stopping it"; Stop-Process -Id $w.Id -Force -ErrorAction SilentlyContinue }
    Say "ARM $ARM DONE: run-game exit $rc, run $runDir"
    $results += [pscustomobject]@{ arm = $a.arm; rc = $rc; run = $runDir }
    if ($rc -ne 0) { Say "ARM $ARM exit ${rc}: stopping (no further arm)"; break }
}
$postArgs = @('-B', (Join-Path $row3 'row3_post.py'), '--row3', $row3)
foreach ($r in $results) { if ($r.run -ne '?') { $postArgs += @('--arm', "$($r.arm)=$($r.run)") } }
$prc = Run-Logged 'python' $postArgs
Say "row3_post.py exit $prc (captions: $(Join-Path $row3 'post\captions.txt'))"
Say "ROW3 DONE: $(($results | ForEach-Object { "$($_.arm) exit $($_.rc) $($_.run)" }) -join '; ')"
exit $(if (@($results | Where-Object { $_.rc -ne 0 }).Count -or $results.Count -lt 2) { 1 } else { 0 })
