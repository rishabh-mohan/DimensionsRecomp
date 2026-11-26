# window-s5.ps1 - S5 Phase 0.3 baseline window (M8). Started by RUN-WINDOW-S5.cmd (the Overseer's waiter
# build\agent1\s5wait or a computer-use open). Self-contained, no prompts, exits by itself:
#   prechecks (verify-bins + pinned MANIFEST sha256 per bin, no game, no Agent 8 runner, WINDOW-HOLD.txt, day launcher
#   not busy, interactive desktop) -> build\agent8\s5\run-matrix.ps1 -Matrix <matrix> -NoPrompt (one unscored cold run per bin)
#   -OutDir build\agent8\s5\matrix\<stamp> -> exit code of the matrix (0 all OK, 1 some run not OK, 2 matrix error,
#   3 refused by a precheck).
# Rated files: PINS-S5.txt (refuses on any mismatch). Words (any order): dryrun (prechecks reported, not enforced, then run-matrix -PlanOnly; no game), allowhidden.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'
$kit = $PSScriptRoot
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$matrix = Join-Path $kit 'matrix-s5-baseline.json'
$rm = Join-Path $kit 'run-matrix.ps1'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs') | Out-Null
$stamp = Get-Date -Format yyyyMMdd-HHmm
$log = Join-Path $kit "logs\window-s5-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[window-s5 $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # native stderr through 2>&1 must not throw (PS 5.1)
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}
# Pinned bins: MANIFEST.txt sha256 (build\agent2\final2\BIN-PINS.md; native4bp: Overseer 17:51, M16/Agent 2 board run 2 #1,
# exe FA761654, native GPU fingerprint 39129c4c059be5f0).
$pins = @(
    [pscustomobject]@{ bin = 'build\agent2\devfinal2-bin'; pin = '4A4A13EDFBFF6A5F32798837A4156256A5A58A2C44579F272B5147768E50982D' },
    [pscustomobject]@{ bin = 'build\agent2\nativefinal2-bin'; pin = '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163' },
    [pscustomobject]@{ bin = 'build\agent16\pack\native4bp-bin'; pin = 'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690' })
Say "S5 baseline window $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); matrix $matrix"
Say "WS $ws; matrix sha256 $((Get-FileHash -LiteralPath $matrix -Algorithm SHA256).Hash.Substring(0,16)); run-matrix sha256 $((Get-FileHash -LiteralPath $rm -Algorithm SHA256).Hash.Substring(0,16))"

$fail = @(); $refuse = @()
# Rated files: PINS-S5.txt (sha256 + path relative to this folder). RUN-WINDOW-S5.cmd pins PINS-S5.txt itself and checks
# every line before it starts this script; this repeats the per-file check so a direct start is held to it too.
$pinsFile = Join-Path $kit 'PINS-S5.txt'
if (-not (Test-Path -LiteralPath $pinsFile)) { $fail += "missing $pinsFile" }
else {
    foreach ($l in @(Get-Content -LiteralPath $pinsFile)) {
        if ($l -notmatch '^([0-9A-Fa-f]{64})\s+(\S.*)$') { continue }
        $pf = Join-Path $kit $Matches[2].Trim(); $want = $Matches[1].ToUpperInvariant()
        if (-not (Test-Path -LiteralPath $pf -PathType Leaf)) { $refuse += "rated file missing: $($Matches[2].Trim())" }
        elseif ((Get-FileHash -LiteralPath $pf -Algorithm SHA256).Hash -ne $want) { $refuse += "rated file changed: $($Matches[2].Trim()) (sha256 is not $($want.Substring(0,16)))" }
    }
    Say "rated files: PINS-S5.txt sha256 $((Get-FileHash -LiteralPath $pinsFile -Algorithm SHA256).Hash.Substring(0,16)), $(@(Get-Content -LiteralPath $pinsFile | Where-Object { $_ -match '^[0-9A-Fa-f]{64}\s' }).Count) files checked"
}
foreach ($p in @($matrix, $rm, (Join-Path $kit 'run-timing.ps1'), (Join-Path $kit 'score3d.py'), $vb, (Join-Path $ws 'harness\routes\attract-long.txt'), (Join-Path $ws 'harness\nvml.cs'), (Join-Path $ws 'build\agent3\vpad\xinput1_4.dll'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
foreach ($b in $pins) { foreach ($f in @('legodimensions.exe', 'MANIFEST.txt')) { $p = Join-Path (Join-Path $ws $b.bin) $f; if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } } }
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
foreach ($b in $pins) {
    $abs = Join-Path $ws $b.bin
    $rc = Run-Logged 'python' @('-B', $vb, $abs)
    if ($rc -ne 0) { $refuse += "verify-bins FAIL for $($b.bin) (exit $rc)" }
    $ms = (Get-FileHash -LiteralPath (Join-Path $abs 'MANIFEST.txt') -Algorithm SHA256).Hash
    Say "$($b.bin): MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $b.pin) { '= pin' } else { 'NOT the pin ' + $b.pin.Substring(0,16) })"
    if ($ms -ne $b.pin) { $refuse += "$($b.bin) MANIFEST sha256 is not the pin" }
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

$out = Join-Path $kit "matrix\$stamp"
$rmArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rm, '-Matrix', $matrix, '-NoPrompt', '-OutDir', $out)
if ($DryRun) { $rmArgs += '-PlanOnly' }
Say "START $(Get-Date -Format HH:mm:ss): powershell $($rmArgs -join ' ')"
$rc = Run-Logged 'powershell' $rmArgs
Say "run-matrix exit $rc$(if (-not $DryRun) { "; out $out (results.csv, summary.md, summary3d.md)" })"
if (-not $DryRun -and (Test-Path -LiteralPath (Join-Path $out 'summary3d.md'))) { Get-Content -LiteralPath (Join-Path $out 'summary3d.md') -TotalCount 12 | ForEach-Object { Say $_ } }
Say "WINDOW-S5 DONE exit $rc"
exit $rc
