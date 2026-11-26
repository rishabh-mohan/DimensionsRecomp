# dtime-run.ps1 - S5, M16: the detailed-timing diagnostic (PROPOSAL-dtime-kit.md) on native4bp. DIAGNOSTIC ONLY:
#   LEGO_NATIVE_TIMING perturbs frame times, so nothing here is ever scored as timing.
# Words (any order):
#   dryrun       (the default when no mode word is given) no game: preconditions (reported), the cold copy + hash checks,
#                every real command line, run-game -DryRun per arm, a check that the copy's legodimensions.exe has both
#                switch names (LEGO_NATIVE_TIMING, LEGO_NATIVE_SLOW_OPERATIONS as C strings), dtime_post self-test.
#   run          2 arms, ~8 min: d-timing (LEGO_NATIVE_TIMING=1), d-slowops (LEGO_NATIVE_SLOW_OPERATIONS=1); 10 s apart.
#   allowhidden  run even if not on the interactive desktop ('Default') (functional only then).
#   run + dryrun together, or any other word = usage, exit 2.
# Every arm: harness\run-game.ps1 -BinDir build\agent16\dtime\work\n4bp -Seconds 150 -GpuLog -Tag <arm>
#   -RunsRoot build\agent16\dtime\runs -InputScript harness\routes\attract-long.txt -Env "<switch>=1".
#   Cold: work\n4bp = a sha256-checked copy of build\agent16\pack\native4bp-bin (only read; MANIFEST pinned), never with
#   cache\. run-game hard-links it into the run dir; the game writes only in the run dir. Config: harness\legodimensions.toml
#   as is (uncapped, as in the psorows runs whose 330-406 ms switch frame this attributes).
# Stops: a refusal or a non-zero run-game exit stops the session; dtime_post.py runs on whatever finished.
# Refuses (exit 3): pin mismatch, verify-bins FAIL, WINDOW-HOLD.txt / WINDOW-GO.txt, day launcher busy, a running game,
#   an Agent 8 runner, a timed-window kit, a hidden desktop (unless allowhidden). run-game only closes the PID it launched.
# Output: post\dtime-<stamp>.txt (dtime_post), post\SHA256SUMS-<stamp>.txt, logs\dtime-[dryrun-]<stamp>.txt, LATEST.txt.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$AllowHidden = $words -contains 'allowhidden'
$modeWords = @($words | Where-Object { $_ -in @('run', 'dryrun') })
$unknown = @($words | Where-Object { $_ -notin @('run', 'dryrun', 'allowhidden') })
if ($modeWords.Count -gt 1 -or $unknown.Count) { Write-Host "usage: dtime-run.ps1 [dryrun|run] [allowhidden] (default dryrun; got: $($words -join ' '))"; exit 2 }
$DryRun = -not ($modeWords -contains 'run')
$Seconds = 150
$Cooldown = 10
$kit = $PSScriptRoot                                   # build\agent16\dtime
$a16 = Split-Path -Parent $kit
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'dtime_post.py'
$refDir = Join-Path $a16 'pack\native4bp-bin'
$refPin = 'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690'
$work = Join-Path $kit 'work'
$copy = Join-Path $work 'n4bp'
$runsRoot = Join-Path $kit $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$stamp = Get-Date -Format yyyyMMdd-HHmmss
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post'), $work | Out-Null
$log = Join-Path $kit "logs\dtime-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[dtime $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
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
    foreach ($d in @(Get-ChildItem -LiteralPath $dst -Directory)) {
        # a cold copy must stay cold; only this script writes here
        Remove-Item -LiteralPath $d.FullName -Recurse -Force; Say "removed $($d.FullName) (a cold copy has no subdirectories)"
    }
    Say "copy $dst`: $($files.Count) files, $n copied now, $(if ($bad) { "$bad PROBLEMS" } else { 'all sha256 = source' })"
    $bad
}
function Check-Pin([string]$dir, [string]$want, [string]$name) {
    # returns '' when MANIFEST.txt = pin and verify-bins passes, else the refusal reason
    $mf = Join-Path $dir 'MANIFEST.txt'
    if (-not (Test-Path -LiteralPath $mf)) { return "no $mf" }
    $ms = (Get-FileHash -LiteralPath $mf -Algorithm SHA256).Hash
    Say "$name MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $want) { '= pin' } else { 'NOT the pin ' + $want.Substring(0,16) })"
    if ($ms -ne $want) { return "$name MANIFEST is not the pin" }
    $rc = Run-Logged 'python' @('-B', $vb, $dir)
    if ($rc -ne 0) { return "verify-bins FAIL for $dir (exit $rc)" }
    ''
}
function Get-Refusals {
    # the guards of natcmp\cmp-run.ps1 (re-checked before every arm)
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
function Test-ExeStrings([string]$exe, [string[]]$names) {
    # one sequential read of $exe; returns name -> found, for each name as a NUL-terminated ASCII string
    $enc = [Text.Encoding]::GetEncoding(28591)
    $found = [ordered]@{}; foreach ($k in $names) { $found[$k] = $false }
    $fs = [IO.File]::OpenRead($exe)
    try {
        $buf = New-Object byte[] (8MB); $carry = ''
        while (($n = $fs.Read($buf, 0, $buf.Length)) -gt 0) {
            $s = $carry + $enc.GetString($buf, 0, $n)
            foreach ($k in $names) { if (-not $found[$k] -and $s.IndexOf("$k`0", [StringComparison]::Ordinal) -ge 0) { $found[$k] = $true } }
            if (-not (@($found.Values) -contains $false)) { break }
            $carry = $s.Substring([Math]::Max(0, $s.Length - 64))
        }
    } finally { $fs.Close() }
    $found
}

# --- the arm list ---
$arms = @(
    [pscustomobject]@{ name = 'd-timing'; env = 'LEGO_NATIVE_TIMING=1' },
    [pscustomobject]@{ name = 'd-slowops'; env = 'LEGO_NATIVE_SLOW_OPERATIONS=1' }
)
Say "S5 dtime $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); $($arms.Count) arms x -Seconds $Seconds, ~8 min; DIAGNOSTIC ONLY; WS $ws"
Say "arms: $(($arms | ForEach-Object { "$($_.name) [$($_.env)]" }) -join ' ')"

# --- preconditions ---
$fail = @()
foreach ($p in @($rg, $route, $vb, $post, (Join-Path $ws 'harness\guard.ps1'), (Join-Path $ws 'harness\winhelper.cs'))) { if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } }
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
. (Join-Path $ws 'harness\guard.ps1')
Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
$desk = [LdHarness]::DesktopName()
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: functional only)' })"
$stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
if (Test-Path -LiteralPath $stateFile) { Say "day launcher: $(Get-Content -LiteralPath $stateFile -TotalCount 1)" }
$refuse = @(Get-Refusals)
$r = Check-Pin $refDir $refPin 'native4bp-bin'; if ($r) { $refuse += $r }
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

# --- cold work copy ---
$bad = Sync-Copy $refDir $copy
if (-not $bad) { $rc = Run-Logged 'python' @('-B', $vb, $copy); if ($rc -ne 0) { Say "FAIL verify-bins on $copy"; $bad++ } }
if ($bad) { exit 2 }

function Rg-Args($arm, [string]$root, [bool]$dry) {
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $copy, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $arm.name,
        '-RunsRoot', $root, '-InputScript', $route, '-Env', $arm.env)
    if ($dry) { $x += '-DryRun' }; $x
}
function Cmd-Line([string[]]$x) { 'powershell ' + (($x | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

if ($DryRun) {
    $bad = 0
    foreach ($arm in $arms) {
        Say "COMMAND (real run, arm $($arm.name)): $(Cmd-Line (Rg-Args $arm (Join-Path $kit 'runs') $false))"
        $rc = Run-Logged 'powershell' (Rg-Args $arm $runsRoot $true)
        Say "run-game -DryRun ($($arm.name)) exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    $exe = Join-Path $copy 'legodimensions.exe'
    $t0 = Get-Date
    $found = Test-ExeStrings $exe @('LEGO_NATIVE_TIMING', 'LEGO_NATIVE_SLOW_OPERATIONS')
    foreach ($k in $found.Keys) { Say "exe string $k`: $(if ($found[$k]) { 'present' } else { 'MISSING (the switch is not in this bin)' })"; if (-not $found[$k]) { $bad++ } }
    Say "exe scan $([int]((Get-Date) - $t0).TotalSeconds) s ($exe)"
    $rc = Run-Logged 'python' @('-B', $post, '--selftest', '--out', (Join-Path $kit "logs\post-selftest-$stamp.txt"))
    Say "dtime_post self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say 'dryrun-runs has reparse points: NOT deleted'; $bad++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say 'dryrun-runs removed' }
    }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
$done = @(); $skipped = @(); $stop = ''; $rcAll = 0
function Stop-Ours {
    # abort/error cleanup: only what this script started. Our game = a legodimensions.exe whose image lives under our
    # runs root (run-game hard-links the exe into the run dir); our run-game = a child powershell of this process.
    if (-not $script:armActive) { return }
    if (Test-Path -LiteralPath $runsRoot) {
        $rr = (Resolve-Path -LiteralPath $runsRoot).Path.TrimEnd('\') + '\'
        foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='legodimensions.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) })) {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: closed our game pid $($p.ProcessId) ($($p.ExecutablePath))"
        }
    }
    foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ParentProcessId -eq $PID -and $_.CommandLine -match 'run-game\.ps1' })) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: stopped our run-game pid $($p.ProcessId)"
    }
    $script:armActive = $false
}
$armActive = $false; $first = $true
try {
foreach ($arm in $arms) {
    if ($stop) { $skipped += "$($arm.name) (stopped: $stop)"; continue }
    if (-not $first) { Say "cooldown $Cooldown s"; Start-Sleep -Seconds $Cooldown }
    $first = $false
    if (@(Get-ChildItem -LiteralPath $copy -Directory).Count) { $stop = "cold copy $copy has a subdirectory"; $skipped += "$($arm.name) ($stop)"; continue }
    $rc = Run-Logged 'python' @('-B', $vb, $copy)
    if ($rc -ne 0) { $stop = "verify-bins FAIL on $copy before $($arm.name)"; Say "FAIL $stop"; $rcAll = 1; $skipped += "$($arm.name) ($stop)"; continue }
    $ref = @(Get-Refusals)
    if ($ref.Count) { $stop = "refused before $($arm.name): $($ref -join '; ')"; Say "REFUSED: $stop"; $skipped += "$($arm.name) (refused)"; continue }
    $x = Rg-Args $arm $runsRoot $false
    Say "START $($arm.name): $(Cmd-Line $x)"
    $t0 = Get-Date
    $armActive = $true
    $rc = Run-Logged 'powershell' $x
    $armActive = $false
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($arm.name)*" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^\d{8}-\d{6}-$([regex]::Escape($arm.name))(-\d+)?$" -and $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '' }
    Say "run-game ($($arm.name)) exit $rc, run $(if ($runDir) { $runDir } else { '?' }), $([int]((Get-Date) - $t0).TotalSeconds) s"
    if ($runDir) { $done += "$($arm.name)=$runDir" }
    if ($rc -ne 0) { $rcAll = 1; $stop = "run-game exit $rc on $($arm.name)"; continue }
}
} catch { Say "ERROR: $($_.Exception.Message)"; $rcAll = 1; if (-not $stop) { $stop = "error: $($_.Exception.Message)" } } finally { Stop-Ours }
$skipped | ForEach-Object { Say "skipped: $_" }
# the cold copy must still match its source (nothing writes into it)
$rc = Run-Logged 'python' @('-B', $vb, $copy); if ($rc -ne 0) { Say "FAIL verify-bins on $copy after the arms"; $rcAll = 1 }
$postOut = Join-Path $kit "post\dtime-$stamp.txt"
$postArgs = @('-B', $post)
foreach ($d in $done) { $postArgs += @('--arm', $d) }
$postArgs += @('--out', $postOut)
$prc = Run-Logged 'python' $postArgs
$verdict = (Select-String -LiteralPath $postOut -Pattern '^RESULT: ' -ErrorAction SilentlyContinue | Select-Object -Last 1).Line
$sums = Join-Path $kit "post\SHA256SUMS-$stamp.txt"
@(Get-Item -LiteralPath $postOut, $log -ErrorAction SilentlyContinue) | ForEach-Object { "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)  $($_.Length)  $($_.FullName.Substring($ws.Length + 1))" } | Set-Content -LiteralPath $sums -Encoding ascii
Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp exit=$rcAll post=$prc arms=$($done.Count)/$($arms.Count) report=$postOut $(if ($stop) { "stopped=[$stop] " })$verdict" -Encoding ascii
Say "DTIME DONE: $($done.Count)/$($arms.Count) arms; run-game $(if ($rcAll) { 'had a problem' } else { 'all exit 0' }); post exit $prc; $verdict; report $postOut"
exit $(if ($rcAll -ne 0 -or $prc -ne 0 -or $stop) { 1 } else { 0 })
