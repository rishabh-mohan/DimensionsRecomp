# nops-smoke-run.ps1 - S5 Phase 2.1 nops-async smoke on devs5nops-bin (M2), modelled on sync-smoke-run.ps1.
# One approval (RUN-NOPS-SMOKE.cmd) runs up to six arms back to back on build\agent2\s5\devs5nops-bin
# (MANIFEST pin: $pin below, from s5/nops-bin/BIN-PINS.md), harness\run-game.ps1 -Seconds 240 -GpuLog, attract-long.txt
# virtual-pad route, WM_CLOSE at 240 s (run-game closes only the game it started). Default order T1 T2 N1 N2 A1 A2:
#   T1  plain default                                            timing, opt-in OFF
#   T2  d3d12_async_depth_only_pipelines=true                    timing, opt-in ON
#   N1  d3d12_pipeline_creation_no_wait=true                     timing (s33 config), opt-in OFF
#   N2  no_wait=true + d3d12_async_depth_only_pipelines=true     timing, opt-in ON
#   A1  d3d12_log_sync_pipeline_creation=true;slow_frame_log_ms=1          attribution only (D2), opt-in OFF
#   A2  A1 + d3d12_async_depth_only_pipelines=true                         attribution only (D2), opt-in ON
# Then nops_smoke_post.py (gates + report in nops-smoke\post). Words (any order): dryrun, allowhidden,
# arms=T1,T2,... (subset/order), allowsubset, nozpd.
#   N3      the no_wait pair N1+N2 is mandatory: a real run refuses an arms= list without both, unless allowsubset.
#   S1      every arm also sets d3d12_log_occlusion_queries=true (zpd-log TU in the bin: ZPD query counters, about
#           one log line per 10 s while queries come in, so timing is unaffected); nozpd drops it (bin without it).
#   N2      every arm starts from cold pipeline/shader storage: run-game makes a fresh run dir per arm and the kit
#           never passes -UserDir or -SeedXenos, so the storage is <run>\user\cache\shaders (new, empty). The post
#           gates it (run.json seed_xenos empty, user_data_root = <run>\user, no storage file older than the run).
#   shots   T1 T2 N1 N2 (N3): a background job PNGs the game window (harness winhelper Shot, read-only) at
#           60 120 146 152 200 s after the game process starts, into <run>\kit-shots\ (+ shots.txt). Same times
#           in every arm, so any capture cost is the same in each pair. A1/A2 take none. Only a game whose image is
#           under the kit's runs root is shot (M10 S2).
#   dryrun  no game: verify-bins + preconditions (reported, not enforced), the real command lines, run-game -DryRun
#           for each arm (into nops-smoke\dryrun-runs, deleted afterwards), shot-job and hold-watch self-tests,
#           nops_smoke_post.py --selftest on the sync-smoke runs (A1 = its on arm, T1 = its off arm; known values must
#           come out). Exit 0 = commands OK.
# Real run: refuses (exit 3) on verify-bins FAIL / MANIFEST not the pin, WINDOW-HOLD.txt, WINDOW-GO.txt, a timed-window
# kit script running, day launcher state of waiting-for-quiet/running, a running game, an Agent 8 runner, or a hidden
# desktop; the same guards are re-checked before every arm. During an arm a hold watch polls WINDOW-HOLD.txt (2 s) and
# closes our game (image under the runs root) if it appears. After every arm: verify-bins + MANIFEST = pin on the bin
# (it is hard-linked into the run dirs; a FAIL stops the kit and invalidates the results). try/finally cleanup stops
# our jobs, our game and our run-game only. Stops after an arm with exit != 0.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'
$AllowSubset = $words -contains 'allowsubset'; $NoZpd = $words -contains 'nozpd'
$kit = $PSScriptRoot
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'nops_smoke_post.py'
$out = Join-Path $kit 'nops-smoke'
$runsRoot = Join-Path $out $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$Seconds = 240
$bin = Join-Path $ws 'build\agent2\s5\devs5nops-bin'
$pin = '8A8B2E776D896F12F2461E466E514F412EA204EDEA87546A9542E46F27D82D54'   # MANIFEST.txt sha256 of devs5nops-bin (s5/nops-bin/BIN-PINS.md)
New-Item -ItemType Directory -Force -Path (Join-Path $out 'logs'), (Join-Path $out 'post') | Out-Null
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$log = Join-Path $out "logs\nops-smoke-run-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[nops-smoke $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
$NOPS = 'd3d12_async_depth_only_pipelines=true'; $NW = 'd3d12_pipeline_creation_no_wait=true'
$LOGC = 'd3d12_log_sync_pipeline_creation=true;slow_frame_log_ms=1'
$ZPD = if ($NoZpd) { '' } else { ';d3d12_log_occlusion_queries=true' }
$all = [ordered]@{
    T1 = ''; T2 = $NOPS; N1 = $NW; N2 = "$NW;$NOPS"; A1 = $LOGC; A2 = "$LOGC;$NOPS" }
$ShotArms = @('T1', 'T2', 'N1', 'N2'); $ShotTimes = @(60, 120, 146, 152, 200)
$sel = @($words | Where-Object { $_ -like 'arms=*' } | ForEach-Object { $_.Substring(5).ToUpper() -split ',' } | Where-Object { $_ })
if (-not $sel.Count) { $sel = @($all.Keys) }
$bad = @($sel | Where-Object { -not $all.Contains($_) })
if ($bad.Count) { Write-Host "unknown arm(s): $($bad -join ',') (known: $($all.Keys -join ','))"; exit 2 }
$arms = @($sel | ForEach-Object { [pscustomobject]@{ arm = $_; tag = "s5nops-$($_.ToLower())"; cvar = "$($all[$_])$ZPD".TrimStart(';') } })
Say "S5 NOPS-SMOKE kit $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); bin $bin; order $(($arms | ForEach-Object { $_.arm }) -join ' '); -Seconds $Seconds each"
Say "WS $ws"
Say "S1: $(if ($NoZpd) { 'nozpd: no occlusion query counters' } else { 'd3d12_log_occlusion_queries=true in every arm' }); N2: fresh run dir per arm, no -UserDir/-SeedXenos (cold storage <run>\user\cache\shaders); shots in $($ShotArms -join ' ') at $($ShotTimes -join ' ') s"

function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # native stderr through 2>&1 must not throw (PS 5.1)
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}

# --- preconditions ---
$fail = @(); $refuse = @()
if (-not (($sel -contains 'N1') -and ($sel -contains 'N2')) -and -not $AllowSubset) {
    $refuse += 'N3: the no_wait pair N1+N2 is mandatory (arms= without both; add allowsubset to override)'
}
foreach ($p in @($rg, $route, $vb, $post, (Join-Path $ws 'build\agent2\final\check-defaults.py'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
if (-not (Test-Path -LiteralPath (Join-Path $bin 'MANIFEST.txt'))) {
    $refuse += "bin not staged yet: $bin\MANIFEST.txt missing"
} else {
    $rc = Run-Logged 'python' @('-B', $vb, $bin)
    if ($rc -ne 0) { $refuse += "verify-bins FAIL for $bin (exit $rc)" }
    $ms = (Get-FileHash -LiteralPath (Join-Path $bin 'MANIFEST.txt') -Algorithm SHA256).Hash
    Say "MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $pin) { '= pin (s5/nops-bin/BIN-PINS.md)' } else { 'NOT the pin ' + $pin })"
    if ($ms -ne $pin) { $refuse += 'MANIFEST sha256 is not the pin' }
}
$hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
$go = Join-Path $ws 'perf-notes\WINDOW-GO.txt'
$stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
if (Test-Path -LiteralPath $stateFile) { Say "day launcher: $((Get-Content -LiteralPath $stateFile -TotalCount 1))" }
. (Join-Path $ws 'harness\guard.ps1')
Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
$desk = [LdHarness]::DesktopName()
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: not visible to the user)' })"
function Get-Refusals {
    # checked at the start and again before every arm (M10 kit rating S1: + WINDOW-GO and the timed-window kits)
    $r = @()
    if (Test-Path -LiteralPath $hold) { $r += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
    if (Test-Path -LiteralPath $go) { $r += "WINDOW-GO.txt present: $((Get-Content -LiteralPath $go -TotalCount 1))" }
    if (Test-Path -LiteralPath $stateFile) {
        $st = (Get-Content -LiteralPath $stateFile -TotalCount 1)
        if ($st -match '(?i)waiting-for-quiet|\brunning\b') { $r += "day launcher busy ($st)" }
    }
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
    if ($g.Count) { $r += "a game is running (pid $(($g | ForEach-Object Id) -join ','))" }
    $runners = @(Get-ActiveRunners)
    if ($runners.Count) { $r += "Agent 8 runner active: $($runners -join '; ')" }
    # The timed-window kit scripts as a script path on a shell/python command line (a path separator before the name and
    # a script extension after it), so a grep that only mentions a name does not refuse the kit (M10 D1).
    $win = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $_.ProcessId -ne $PID -and $_.Name -match '^(?i)(powershell|pwsh|cmd|python|py)\.exe$' -and
            $_.CommandLine -match '(?i)[\\/](window-s5\.ps1|RUN-WINDOW-S5[^\\/\s"]*\.cmd|run-matrix[^\\/\s"]*\.(ps1|cmd|py))' })
    if ($win.Count) { $r += "timed-window kit running (pid $(($win | ForEach-Object ProcessId) -join ','))" }
    if ($desk -ne 'Default' -and -not $AllowHidden) { $r += "not on the interactive desktop ($desk)" }
    $r
}
$refuse += @(Get-Refusals)
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

$rgArgs = { param($a, $root, $dry)
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $a.tag, '-RunsRoot', $root, '-InputScript', $route)
    if ($a.cvar) { $x += @('-Cvar', $a.cvar) }
    if ($dry) { $x += '-DryRun' }; $x }
function Cmd-Line($a, [string]$root) { 'powershell ' + ((& $rgArgs $a $root $false | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

# Screenshot job (N3): waits for a legodimensions process started after $t0 whose image lives under $runsRoot (run-game
# hard-links the exe into the run dir; M10 kit rating S2: never a foreign game), then PNGs its window at the given
# seconds after its start into <its run dir>\kit-shots\. Read-only: it never closes, focuses or sends input to anything.
$shotJob = { param($ws, $t0, $times, $timeout, $runsRoot)
    Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
    $rr = [IO.Path]::GetFullPath($runsRoot).TrimEnd('\') + '\'
    $deadline = (Get-Date).AddSeconds($timeout); $p = $null
    while (-not $p -and (Get-Date) -lt $deadline) {
        $p = Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object {
            $x = try { $_.Path } catch { '' }; $_.StartTime -ge $t0 -and $x -and $x.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) } | Select-Object -First 1
        if (-not $p) { Start-Sleep -Milliseconds 500 }
    }
    if (-not $p) { 'shots: no game process'; return }
    $dir = Join-Path (Split-Path -Parent $p.Path) 'kit-shots'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    foreach ($s in $times) {
        $wait = ($p.StartTime.AddSeconds($s) - (Get-Date)).TotalMilliseconds
        if ($wait -gt 0) { Start-Sleep -Milliseconds ([int]$wait) }
        if ($p.HasExited) { "shots: game exited before $s s"; break }
        $f = Join-Path $dir ('shot-{0:000}s.png' -f $s)
        $how = [LdHarness]::Shot($p.Id, $f)
        $l = 'shot {0} s (at {1:N1} s) pid {2}: {3} -> {4}' -f $s, ((Get-Date) - $p.StartTime).TotalSeconds, $p.Id, $how, $f
        Add-Content -LiteralPath (Join-Path $dir 'shots.txt') -Value $l; $l
    }
}
function Storage-Report([string]$runDir) {
    $sd = Join-Path $runDir 'user\cache\shaders'
    $fs = @(if (Test-Path -LiteralPath $sd) { Get-ChildItem -LiteralPath $sd -Recurse -File })
    Say "N2 storage after the run ($sd): $(if ($fs.Count) { ($fs | ForEach-Object { "$($_.Name) $($_.Length) B" }) -join ', ' } else { 'none' })"
}
# Hold watch (M10 kit rating S3): during an arm, polls WINDOW-HOLD.txt every 2 s; when it appears, WM_CLOSE to our game
# (image under $runsRoot only), then a forced stop after 15 s if it is still there. run-game then returns and the
# kit stops before the next arm.
$holdJob = { param($hold, $runsRoot, $maxS)
    $rr = [IO.Path]::GetFullPath($runsRoot).TrimEnd('\') + '\'
    $end = (Get-Date).AddSeconds($maxS)
    while ((Get-Date) -lt $end) {
        if (Test-Path -LiteralPath $hold) {
            $ps = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object {
                    $x = try { $_.Path } catch { '' }; $x -and $x.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) })
            if (-not $ps.Count) { 'hold: WINDOW-HOLD.txt appeared; no game of ours running'; return }
            foreach ($p in $ps) { [void]$p.CloseMainWindow(); "hold: WINDOW-HOLD.txt appeared; WM_CLOSE to our game pid $($p.Id)" }
            Start-Sleep -Seconds 15
            foreach ($p in $ps) { if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; "hold: our game pid $($p.Id) still running after 15 s: stopped" } }
            return
        }
        Start-Sleep -Seconds 2
    }
}
# Abort/error cleanup (S3), from the finally block: only what this script started. Our game = a legodimensions.exe whose
# image lives under $runsRoot; our run-game = a child powershell of this process running run-game.ps1.
function Stop-Ours {
    foreach ($jn in @('shotJ', 'holdJ')) {
        $jj = Get-Variable -Scope Script -Name $jn -ValueOnly -ErrorAction SilentlyContinue
        if ($jj) { Stop-Job $jj -ErrorAction SilentlyContinue; Remove-Job $jj -Force -ErrorAction SilentlyContinue; Set-Variable -Scope Script -Name $jn -Value $null; Say "cleanup: $jn stopped" }
    }
    if (-not $script:armActive) { return }
    $rr = [IO.Path]::GetFullPath($runsRoot).TrimEnd('\') + '\'
    foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='legodimensions.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) })) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: closed our game pid $($p.ProcessId) ($($p.ExecutablePath))"
    }
    foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ParentProcessId -eq $PID -and $_.CommandLine -match 'run-game\.ps1' })) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: stopped our run-game pid $($p.ProcessId)"
    }
    $script:armActive = $false
}
function Check-Bin([string]$when) {
    # S4 / K6: the pinned bin is hard-linked into every run dir, so re-check it (MANIFEST = pin, verify-bins) after each arm
    $rc = Run-Logged 'python' @('-B', $vb, $bin)
    $ms = (Get-FileHash -LiteralPath (Join-Path $bin 'MANIFEST.txt') -Algorithm SHA256).Hash
    $ok = ($rc -eq 0 -and $ms -eq $pin)
    Say "bin check $when`: verify-bins exit $rc, MANIFEST $($ms.Substring(0,16)) $(if ($ms -eq $pin) { '= pin' } else { 'NOT the pin' }) -> $(if ($ok) { 'OK' } else { 'FAIL' })"
    $ok
}

if ($DryRun) {
    $badn = 0
    if (Test-Path -LiteralPath (Join-Path $bin 'legodimensions.exe')) {
        foreach ($a in $arms) {
            Say "ARM $($a.arm) COMMAND (real run): $(Cmd-Line $a (Join-Path $out 'runs'))"
            $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $true)
            Say "ARM $($a.arm) run-game -DryRun exit $rc"; if ($rc -ne 0) { $badn++ }
        }
    } else { Say 'bin not staged: run-game -DryRun skipped (FAIL)'; $badn++ }
    # The screenshot job must load winhelper and give up cleanly when no game starts (t0 in the future).
    $j = Start-Job -ScriptBlock $shotJob -ArgumentList $ws, (Get-Date).AddHours(1), @(1), 3, $runsRoot
    $jo = @(Receive-Job -Job $j -Wait -AutoRemoveJob -ErrorAction Continue 2>&1 | ForEach-Object { "$_" })
    Say "shot job self-test: $($jo -join ' | ')"
    if (($jo -join ' ') -ne 'shots: no game process') { Say 'shot job self-test FAIL'; $badn++ }
    # The hold watch must see a hold file and close nothing when no game of ours runs (a scratch file, not WINDOW-HOLD).
    $fh = Join-Path $out "logs\holdtest-$stamp.txt"; Set-Content -LiteralPath $fh -Value 'hold self-test' -Encoding ascii
    $j = Start-Job -ScriptBlock $holdJob -ArgumentList $fh, $runsRoot, 10
    $jo = @(Receive-Job -Job $j -Wait -AutoRemoveJob -ErrorAction Continue 2>&1 | ForEach-Object { "$_" })
    Remove-Item -LiteralPath $fh -Force
    Say "hold watch self-test: $($jo -join ' | ')"
    if (($jo -join ' ') -ne 'hold: WINDOW-HOLD.txt appeared; no game of ours running') { Say 'hold watch self-test FAIL'; $badn++ }
    # Post self-test on the sync-smoke runs (devs5sync-bin, 17:49): A1 = its on arm, T1 = its off arm.
    $sOn = Join-Path $kit 'sync-smoke\runs\20261125-175402-s5sync-on'
    $sOff = Join-Path $kit 'sync-smoke\runs\20261125-174932-s5sync-off'
    $st = Join-Path $out "logs\post-selftest-$stamp.txt"
    $rc = Run-Logged 'python' @('-B', $post, '--selftest', "A1=$sOn", "T1=$sOff", '--out', $st)
    Say "nops_smoke_post.py --selftest exit $rc"
    foreach ($needle in @('line 7857 frame #7601 945.7 ms | create 458.5 (8x) new 67 | dropped 137 | sync 8 / 458.6 / 8',
            'data row 7545 at 143.3 s: misses 67, frame 940.1 ms', 'movable by the opt-in (ps none, memexport vs 0, host RT) 44')) {
        if ($rc -ne 0 -or -not (Select-String -LiteralPath $st -SimpleMatch -Quiet -Pattern $needle)) { Say "selftest needle FAIL: $needle"; $badn++ }
    }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say "dryrun-runs has reparse points: NOT deleted"; $badn++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say "dryrun-runs removed" }
    }
    Say "DRY RUN $(if ($badn) { "FAILED ($badn)" } else { 'ALL PASS' })"
    exit $(if ($badn) { 1 } else { 0 })
}

# --- real run ---
$results = @()
$first = $true
$stop = ''
$shotJ = $null; $holdJ = $null; $armActive = $false
try {
foreach ($a in $arms) {
    if (-not $first) { Say 'settle 20 s between arms'; Start-Sleep -Seconds 20 }
    $first = $false
    $ref = @(Get-Refusals)
    if ($ref.Count) { $stop = "refused before arm $($a.arm): $($ref -join '; ')"; Say "REFUSED: $stop"; break }
    Say "ARM $($a.arm) START $(Get-Date -Format HH:mm:ss): $(Cmd-Line $a $runsRoot)"
    Say "ARM $($a.arm) N2: cold storage (fresh run dir under $runsRoot, no -UserDir/-SeedXenos)"
    $t0 = Get-Date
    if ($ShotArms -contains $a.arm) { $shotJ = Start-Job -ScriptBlock $shotJob -ArgumentList $ws, $t0.AddSeconds(-2), $ShotTimes, 180, $runsRoot }
    $holdJ = Start-Job -ScriptBlock $holdJob -ArgumentList $hold, $runsRoot, ($Seconds + 600)
    $armActive = $true
    $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $false)
    $armActive = $false
    if ($shotJ) {
        if (-not (Wait-Job -Job $shotJ -Timeout 30)) { Stop-Job -Job $shotJ }
        Receive-Job -Job $shotJ -ErrorAction Continue 2>&1 | ForEach-Object { Say "ARM $($a.arm) $_" }
        Remove-Job -Job $shotJ -Force; $shotJ = $null
    }
    Stop-Job -Job $holdJ
    $ho = @(Receive-Job -Job $holdJ -ErrorAction Continue 2>&1 | ForEach-Object { "$_" })
    Remove-Job -Job $holdJ -Force; $holdJ = $null
    $ho | ForEach-Object { Say "ARM $($a.arm) $_" }
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($a.tag)*" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '?' }
    Say "ARM $($a.arm) DONE: run-game exit $rc, run $runDir"
    if ($runDir -ne '?') { Storage-Report $runDir }
    $results += [pscustomobject]@{ arm = $a.arm; rc = $rc; run = $runDir }
    if ($ho.Count) { $stop = "WINDOW-HOLD.txt during arm $($a.arm)"; Say "STOP: $stop (no further arm)"; break }
    if (-not (Check-Bin "after arm $($a.arm)")) { $stop = "bin check FAIL after arm $($a.arm) (results invalid, K6)"; Say "STOP: $stop"; break }
    if ($rc -ne 0) { $stop = "arm $($a.arm) exit $rc"; Say "ARM $($a.arm) exit ${rc}: stopping (no further arm)"; break }
}
} catch { Say "ERROR: $($_.Exception.Message)"; if (-not $stop) { $stop = "error: $($_.Exception.Message)" } } finally { Stop-Ours }
if ($stop) { Say "stopped: $stop" }
$postOut = Join-Path $out "post\nops-smoke-post-$stamp.txt"
$postArgs = @('-B', $post, '--out', $postOut)
if ($NoZpd) { $postArgs += '--nozpd' }
foreach ($r in $results) { if ($r.run -ne '?') { $postArgs += @("--$($r.arm)", $r.run) } }
$prc = if ($postArgs.Count -gt 4 + [int]$NoZpd) { Run-Logged 'python' $postArgs } else { 2 }
Say "nops_smoke_post.py exit $prc (report $postOut)"
Say "NOPS-SMOKE DONE: $(($results | ForEach-Object { "$($_.arm) exit $($_.rc) $($_.run)" }) -join '; '); post $(if ($prc -eq 0) { 'ALL PASS' } else { "FAIL (exit $prc)" })$(if ($stop) { "; stopped: $stop" })"
exit $(if ($stop -or @($results | Where-Object { $_.rc -ne 0 }).Count -or $results.Count -lt $arms.Count -or $prc -ne 0) { 1 } else { 0 })
