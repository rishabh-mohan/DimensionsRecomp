# cmp-run.ps1 - S5 natcmp (M16): n4bp60 vs a base arm (ship60 by default, or nat60) back to back with the agents quiet,
# the nongame CPU load gated before each scored arm and flagged per second in the post (CMP-DESIGN.md, option B,
# Overseer 00:35Z changes; base arm option (c), Overseer 01:38Z).
# Why: in window 20261125-1804, n4bp60 vs nat60 was confounded by a nongame load of 5.3-7.5 vs 3.0-3.8 cores (CPU
# 1.6-1.75 vs 2.7 GHz). PSO compiles explained 0/137 of the hitches. M12 p03: on quiet runs the CPU clock tracks the
# arm's GPU power (nat60 skips the ~13 % missing draws), so ship60 (which renders every draw) is the fair base.
# Words (any order):
#   (none)       short form, base ship60: prime-<base> prime-n4bp60 (unscored, ungated: they run before any gate timer),
#                then one ABBA = 2 pairs: <base> n4bp60 | n4bp60 <base>. 6 runs, ~35 min.
#   vs ship|nat  the base arm: ship (ship60, default) or nat (nat60). 'ship' or 'nat' alone also works.
#   full         4 pairs: B n4bp60 | n4bp60 B | n4bp60 B | B n4bp60. 10 runs, ~60-65 min.
#   dryrun       no game: guards and pins reported (not enforced), every real command line, run-matrix -PlanOnly per
#                arm, one gate sample (reported), cmp_post self-test. Exit 0 = pass. It hashes the two bins (verify-bins).
#   allowhidden  run even if not on the interactive desktop ('Default'). Then it is functional only, never timed.
# Each arm = one call of M8's rated runner (build\agent8\s5, PINS-S5) on natcmp\matrix-natcmp.json:
#   -Only <arm> -Repeats 1 -NoCold -NoPrompt -OutDir natcmp\matrix\<stamp>\<NN>-<label>
#   It uses the same run settings as the window (warm-up 90 s from the first frame, 180 s window, cap60, attract-long pad,
#   sys.csv, gpu.csv, GPU cooldown < 72 C, score3d). Every run has its own run dir, so the per-run-dir PSO cache is cold.
# Gate (scored arms only): nongame CPU = total CPU (\Processor(_Total)\% Processor Time x logical CPUs) with no game
#   running. It launches when one 20 s sample has mean < 2.0 cores and max < 4.0. After 180 s it launches anyway and marks
#   the arm GATE-TIMEOUT: logged and reported, but excluded from the verdict.
# Refuses (exit 3): pin mismatch (MANIFEST or helper), verify-bins FAIL, WINDOW-HOLD.txt or WINDOW-GO.txt, day launcher
#   busy, a running game, an Agent 8 runner, a timed-window kit process, a hidden desktop (unless allowhidden). These are
#   re-checked before every arm; a refusal stops the session. The runner's exit 2 also stops the session; exit 1 (run not
#   OK) is recorded and the session goes on.
# Abort/error: try/finally closes only our game (exe under our out root) and our runner child (a powershell child of
#   this process). The runner's sys sampler stops by itself when the game exits.
# Output: post\natcmp-<stamp>.txt (cmp_post.py), post\SHA256SUMS-<stamp>.txt, logs\natcmp-<stamp>.txt, LATEST.txt.
# Pins: RUN-NATCMP.cmd pins this file and every helper except the runner script itself, whose name must not be on a
#   certutil command line (M10 D1). This file pins it ($rmPin, = PINS-S5) in-process with Get-FileHash, before every arm.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'; $Full = $words -contains 'full'
$unknown = @($words | Where-Object { $_ -notin @('full', 'dryrun', 'allowhidden', 'vs', 'ship', 'nat') })
$vsBad = ($words -contains 'ship' -and $words -contains 'nat') -or ($words -contains 'vs' -and -not ($words -contains 'ship' -or $words -contains 'nat'))
if ($unknown.Count -or $vsBad) { Write-Host "usage: cmp-run.ps1 [vs ship|nat] [full] [dryrun] [allowhidden] (got: $($words -join ' '))"; exit 2 }
$Base = if ($words -contains 'nat') { 'nat60' } else { 'ship60' }
$kit = $PSScriptRoot                                   # build\agent16\natcmp
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$s5 = Join-Path $ws 'build\agent8\s5'
$rm = Join-Path $s5 ('run-' + 'matrix.ps1')
$rmPin = '8D64791873696776178B85D7C3526C862C2BE81501483B938D74DF4B5D17FC8B'   # = build\agent8\s5\PINS-S5.txt
$matrix = Join-Path $kit 'matrix-natcmp.json'
$post = Join-Path $kit 'cmp_post.py'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
# bin MANIFEST pins = build\agent8\s5 window script L28-30 (BIN-PINS.md); only the two arms of this session are checked
$bins = @(@(
    [pscustomobject]@{ arm = 'ship60'; dir = (Join-Path $ws 'build\agent2\devfinal2-bin'); pin = '4A4A13EDFBFF6A5F32798837A4156256A5A58A2C44579F272B5147768E50982D' },
    [pscustomobject]@{ arm = 'nat60'; dir = (Join-Path $ws 'build\agent2\nativefinal2-bin'); pin = '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163' },
    [pscustomobject]@{ arm = 'n4bp60'; dir = (Join-Path $ws 'build\agent16\pack\native4bp-bin'); pin = 'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690' }) |
    Where-Object { $_.arm -in @($Base, 'n4bp60') })
$GateMean = 2.0; $GateMax = 4.0; $GateWin = 20; $GateTimeout = 180
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$outRoot = Join-Path $kit $(if ($DryRun) { "dryrun-matrix\$stamp" } else { "matrix\$stamp" })
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post') | Out-Null
$log = Join-Path $kit "logs\natcmp-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[natcmp $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}
function Check-Bin($b) {
    # '' when MANIFEST.txt = pin and verify-bins passes, else the refusal reason
    $mf = Join-Path $b.dir 'MANIFEST.txt'
    if (-not (Test-Path -LiteralPath $mf)) { return "no $mf" }
    $ms = (Get-FileHash -LiteralPath $mf -Algorithm SHA256).Hash
    Say "$($b.arm) bin MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $b.pin) { '= pin' } else { 'NOT the pin ' + $b.pin.Substring(0,16) })"
    if ($ms -ne $b.pin) { return "$($b.arm) MANIFEST is not the pin" }
    $rc = Run-Logged 'python' @('-B', $vb, $b.dir)
    if ($rc -ne 0) { return "verify-bins FAIL for $($b.dir) (exit $rc)" }
    ''
}
function Check-Runner {
    if (-not (Test-Path -LiteralPath $rm)) { return "missing $rm" }
    $h = (Get-FileHash -LiteralPath $rm -Algorithm SHA256).Hash
    if ($h -ne $rmPin) { return "runner script changed (sha256 $($h.Substring(0,16)), pin $($rmPin.Substring(0,16)))" }
    ''
}
function Get-Refusals {
    # the guards of psorows\rows-run.ps1 (re-checked before every arm)
    $r = @()
    $hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
    if (Test-Path -LiteralPath $hold) { $r += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
    $go = Join-Path $ws 'perf-notes\WINDOW-GO.txt'
    if (Test-Path -LiteralPath $go) { $r += "WINDOW-GO.txt present: $((Get-Content -LiteralPath $go -TotalCount 1))" }
    $stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
    if (Test-Path -LiteralPath $stateFile) {
        $st = (Get-Content -LiteralPath $stateFile -TotalCount 1)
        if ($st -match '(?i)waiting-for-quiet|\brunning\b') { $r += "day launcher busy ($st)" }
    }
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
    if ($g.Count) { $r += "a game is running (pid $(($g | ForEach-Object Id) -join ','))" }
    $runners = @(Get-ActiveRunners)
    if ($runners.Count) { $r += "Agent 8 runner active: $($runners -join '; ')" }
    # M10 S1 (M3's form): only a powershell/pwsh/cmd that runs the window script or the runner with -File, or the window .cmd
    $win = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne $PID -and $_.Name -match '(?i)^(powershell|pwsh|cmd)\.exe$' -and $_.CommandLine -match '(?i)-File\s+"?[^"]*(window-s5|run-matrix)\.ps1|RUN-WINDOW-S5[^\s"]*\.cmd' })
    if ($win.Count) { $r += "timed-window kit or runner running (pid $(($win | ForEach-Object ProcessId) -join ','))" }
    $desk = [LdHarness]::DesktopName()
    if ($desk -ne 'Default' -and -not $AllowHidden) { $r += "not on the interactive desktop ($desk)" }
    $r
}
function Measure-Load([int]$n) {
    # nongame cores per second over $n s (no game is running when this is called; the total CPU is the nongame load)
    $lp = [Environment]::ProcessorCount
    try {
        $c = Get-Counter -Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples $n -ErrorAction Stop
        @($c | ForEach-Object { [double]$_.CounterSamples[0].CookedValue * $lp / 100.0 })
    } catch {
        Say "note: Get-Counter failed ($($_.Exception.Message)); Win32_PerfFormattedData fallback"
        @(1..$n | ForEach-Object { Start-Sleep -Seconds 1; [double](Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'").PercentProcessorTime * $lp / 100.0 })
    }
}
function Wait-Quiet([string]$label) {
    # 'ok' or 'timeout'
    $t0 = Get-Date
    while ($true) {
        $s = @(Measure-Load $GateWin)
        $mean = ($s | Measure-Object -Average).Average; $max = ($s | Measure-Object -Maximum).Maximum
        $ok = ($mean -lt $GateMean -and $max -lt $GateMax)
        Say ("gate {0}: {1} s nongame mean {2:N2} cores, max {3:N2} ({4})" -f $label, $s.Count, $mean, $max, $(if ($ok) { 'quiet: go' } else { "not quiet (need mean < $GateMean, max < $GateMax)" }))
        if ($ok) { return 'ok' }
        if (((Get-Date) - $t0).TotalSeconds + $GateWin -gt $GateTimeout) { return 'timeout' }   # M10 N4: never past the timeout
    }
}

# --- the arm list ---
$seq = @(
    [pscustomobject]@{ label = "prime-$Base"; arm = $Base; prime = $true },
    [pscustomobject]@{ label = 'prime-n4bp60'; arm = 'n4bp60'; prime = $true })
$abba = if ($Full) { @($Base, 'n4bp60', 'n4bp60', $Base, 'n4bp60', $Base, $Base, 'n4bp60') } else { @($Base, 'n4bp60', 'n4bp60', $Base) }
$i = 0
foreach ($a in $abba) { $i++; $seq += [pscustomobject]@{ label = "s$i-$a"; arm = $a; prime = $false } }
$est = [int][Math]::Ceiling($seq.Count * 5.6 + ($seq.Count - 2) * 0.7 + 2)
Say "S5 natcmp n4bp60 vs $Base, $(if ($Full) { 'full (4 pairs)' } else { 'short (2 pairs)' }) $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); $($seq.Count) runs, ~$est min (+ up to $GateTimeout s per gated arm); WS $ws"
Say "order: $(($seq | ForEach-Object { $_.label }) -join ' ')"
Say "gate: $GateWin s samples, mean < $GateMean cores and max < $GateMax, timeout $GateTimeout s (GATE-TIMEOUT arms are excluded from the verdict); primes are not gated"

# --- preconditions ---
$fail = @()
foreach ($p in @($rm, $matrix, $post, $vb, (Join-Path $ws 'harness\guard.ps1'), (Join-Path $ws 'harness\winhelper.cs'))) { if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } }
foreach ($b in $bins) { foreach ($f in @('legodimensions.exe', 'MANIFEST.txt')) { $p = Join-Path $b.dir $f; if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } } }
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
. (Join-Path $ws 'harness\guard.ps1')
Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
$desk = [LdHarness]::DesktopName()
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: functional only, never timed)' })"
$refuse = @(Get-Refusals)
$r = Check-Runner; if ($r) { $refuse += $r } else { Say "runner script sha256 = pin $($rmPin.Substring(0,16))" }
foreach ($b in $bins) { $r = Check-Bin $b; if ($r) { $refuse += $r } }
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}
function Rm-Args($s, [int]$k, [bool]$plan) {
    $od = Join-Path $outRoot ('{0:D2}-{1}' -f $k, $s.label)
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rm, '-Matrix', $matrix, '-Only', $s.arm, '-Repeats', '1', '-NoCold', '-NoPrompt', '-OutDir', $od)
    if ($plan) { $x += '-PlanOnly' }; $x
}
function Cmd-Line([string[]]$x) { 'powershell ' + (($x | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

if ($DryRun) {
    $bad = 0; $k = 0
    foreach ($s in $seq) {
        $k++
        Say "COMMAND (real run, $($s.label)$(if (-not $s.prime) { ', after the gate' })): $(Cmd-Line (Rm-Args $s $k $false))"
        $rc = Run-Logged 'powershell' (Rm-Args $s $k $true)
        Say "runner -PlanOnly ($($s.label)) exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    $smp = @(Measure-Load 5)
    Say ("gate sample now (5 s, report only): nongame mean {0:N2} cores, max {1:N2}; {2} samples" -f ($smp | Measure-Object -Average).Average, ($smp | Measure-Object -Maximum).Maximum, $smp.Count)
    if ($smp.Count -ne 5) { $bad++ }
    $rc = Run-Logged 'python' @('-B', $post, '--selftest', '--out', (Join-Path $kit "logs\post-selftest-$stamp.txt"))
    Say "cmp_post self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    $dm = Join-Path $kit 'dryrun-matrix'
    if (Test-Path -LiteralPath $dm) {
        $rp = @(Get-ChildItem -LiteralPath $dm -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say 'dryrun-matrix has reparse points: NOT deleted'; $bad++ } else { Remove-Item -LiteralPath $dm -Recurse -Force; Say 'dryrun-matrix removed' }
    }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
$done = @(); $gateTimeouts = @(); $skipped = @(); $stop = ''; $rcAll = 0
function Stop-Ours {
    # abort/error cleanup: only what this script started. Our game = a legodimensions.exe whose image lives under our
    # out root (the runner hard-links the bin into its run dir); our runner = a child powershell of this process.
    if (-not $script:armActive) { return }
    if (Test-Path -LiteralPath $outRoot) {
        $rr = (Resolve-Path -LiteralPath $outRoot).Path.TrimEnd('\') + '\'
        foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='legodimensions.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) })) {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: closed our game pid $($p.ProcessId) ($($p.ExecutablePath))"
        }
    }
    foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ParentProcessId -eq $PID -and $_.CommandLine -match 'run-matrix\.ps1' })) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: stopped our runner pid $($p.ProcessId)"
    }
    $script:armActive = $false
}
$armActive = $false; $k = 0
try {
foreach ($s in $seq) {
    $k++
    if ($stop) { $skipped += "$($s.label) (stopped: $stop)"; continue }
    $r = Check-Runner
    if ($r) { $stop = "refused before $($s.label): $r"; Say "REFUSED: $stop"; $rcAll = 1; $skipped += "$($s.label) (refused)"; continue }
    $b = @($bins | Where-Object { $_.arm -eq $s.arm })[0]
    $rc = Run-Logged 'python' @('-B', $vb, $b.dir)
    if ($rc -ne 0) { $stop = "verify-bins FAIL on $($b.dir) before $($s.label)"; Say "FAIL $stop"; $rcAll = 1; $skipped += "$($s.label) ($stop)"; continue }
    $ref = @(Get-Refusals)
    if ($ref.Count) { $stop = "refused before $($s.label): $($ref -join '; ')"; Say "REFUSED: $stop"; $skipped += "$($s.label) (refused)"; continue }
    if (-not $s.prime) {
        $g = Wait-Quiet $s.label
        if ($g -eq 'timeout') { $gateTimeouts += $s.label; Say "GATE-TIMEOUT $($s.label): not quiet within $GateTimeout s; it runs, logged, excluded from the verdict" }
        $ref = @(Get-Refusals)
        if ($ref.Count) { $stop = "refused before $($s.label) (after the gate): $($ref -join '; ')"; Say "REFUSED: $stop"; $skipped += "$($s.label) (refused)"; continue }
    }
    $x = Rm-Args $s $k $false
    $od = $x[$x.Count - 1]
    Say "START $($s.label): $(Cmd-Line $x)"
    $t0 = Get-Date
    $armActive = $true
    $rc = Run-Logged 'powershell' $x
    $armActive = $false
    # M10 N3: the runner adds a -N suffix if the OutDir exists; take the newest matching dir
    $odLeaf = Split-Path -Leaf $od
    $odHit = @(Get-ChildItem -LiteralPath $outRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match ('^' + [regex]::Escape($odLeaf) + '(-\d+)?$') } | Sort-Object CreationTime | Select-Object -Last 1)
    if ($odHit.Count) { $od = $odHit[0].FullName }
    $rd = @(Get-ChildItem -LiteralPath (Join-Path $od 'runs') -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'run.json') } | Sort-Object CreationTime | Select-Object -Last 1)
    Say "runner ($($s.label)) exit $rc, run $(if ($rd.Count) { $rd[0].FullName } else { '?' }), $([int]((Get-Date) - $t0).TotalSeconds) s"
    if (Test-Path -LiteralPath $od) { $done += "$($s.label)=$od" }
    if ($rc -eq 2 -or $rc -lt 0 -or $rc -gt 2) { $rcAll = 1; $stop = "runner exit $rc on $($s.label)"; continue }
    if ($rc -ne 0) { $rcAll = 1; Say "note: $($s.label) run not OK (runner exit 1); recorded, the session goes on" }
}
} catch { Say "ERROR: $($_.Exception.Message)"; $rcAll = 1; if (-not $stop) { $stop = "error: $($_.Exception.Message)" } } finally { Stop-Ours }
$skipped | ForEach-Object { Say "skipped: $_" }
foreach ($b in $bins) { $rc = Run-Logged 'python' @('-B', $vb, $b.dir); if ($rc -ne 0) { Say "FAIL verify-bins on $($b.dir) after the arms"; $rcAll = 1 } }
$postOut = Join-Path $kit "post\natcmp-$stamp.txt"
$postArgs = @('-B', $post)
foreach ($d in $done) { $postArgs += @('--run', $d) }
foreach ($t in $gateTimeouts) { $postArgs += @('--gate-timeout', $t) }
$postArgs += @('--base', $Base, '--out', $postOut)
$prc = Run-Logged 'python' $postArgs
$verdict = (Select-String -LiteralPath $postOut -Pattern '^RESULT: ' -ErrorAction SilentlyContinue | Select-Object -Last 1).Line
$sums = Join-Path $kit "post\SHA256SUMS-$stamp.txt"
@(Get-Item -LiteralPath $postOut, $log -ErrorAction SilentlyContinue) | ForEach-Object { "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)  $($_.Length)  $($_.FullName.Substring($ws.Length + 1))" } | Set-Content -LiteralPath $sums -Encoding ascii
Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp natcmp-$(if ($Full) { 'full' } else { 'short' })-vs-$Base exit=$rcAll post=$prc runs=$($done.Count)/$($seq.Count) gate_timeouts=$($gateTimeouts.Count) report=$postOut $(if ($stop) { "stopped=[$stop] " })$verdict" -Encoding ascii
Say "NATCMP DONE: $($done.Count)/$($seq.Count) runs; gate timeouts $($gateTimeouts.Count); runner $(if ($rcAll) { 'had a problem' } else { 'all exit 0' }); post exit $prc; $verdict; report $postOut"
exit $(if ($rcAll -ne 0 -or $prc -ne 0 -or $stop) { 1 } else { 0 })
