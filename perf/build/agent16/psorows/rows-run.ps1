# rows-run.ps1 - S5, M16: the PSO functional rows (2.2/2.3 on native4bp-pso-bin) and the 2.4 A/B (async, #35) on native4bp.
# Words (any order; exactly one of rows / ab):
#   rows         9 arms, ~55 min: s0-ref-cold c-pso-t1 c-pso-unl w-ref-t1 w-pso-t1 w-ref-t4 w-pso-t2 w-pso-t4 w-pso-unl
#                ref = native4bp-bin (P-C1 reference), pso = native4bp-pso-bin. w-ref-*/w-pso-t* are warm from s0's cache
#                (the same cache state for both bins, B2), w-pso-unl is warm from c-pso-unl's cache (the reload check).
#   ab           AB-PLAN.md section 3 on native4bp: prime (C0, unscored, the warm source), then
#                C0 C1 W0 W1 | C1 C0 W1 W0 | C0 C1 W0 W1, then W2 x2: 15 arms, ~85 min.
#   n2           with ab: prime + the first two blocks only (AB-PLAN minimum set): 9 arms, ~50 min.
#   dryrun       no game: preconditions (reported), copies + hash checks, every real command line, run-game -DryRun,
#                the seed/warm-dir code on a synthetic seed, pso_post self-test. Exit 0 = pass.
#   allowhidden  run even if not on the interactive desktop ('Default') (functional only then, never timed).
# Every arm: harness\run-game.ps1 -BinDir <dir> -Seconds 300 -GpuLog -Tag <arm> -RunsRoot build\agent16\psorows\runs
#   -InputScript harness\routes\attract-long.txt -Env "LEGO_NATIVE_PSO_STATS=1;LEGO_NATIVE_PSO_STATS_INTERVAL=10[;extra]".
# Bin dirs (pinned dirs are only read): work\ref, work\pso = sha256-checked copies of the pinned bins, never with cache\
#   (cold); work\<name>-warm = hard links to a cold copy's files + cache\native-pso.bin and native-pso-recipes.bin from a
#   seed run dir. A seed counts only if its run-game exit was 0, its game.log says "saved N startup pipeline recipes"
#   (N > 0) and both cache files exist. The cache sha256s are recorded and re-checked before every warm arm. Saves are
#   temp+rename in the run dir, so neither the copies nor the warm dirs are written by the game.
# Summary trigger: run-game's close ends in a hard exit (no Stop(), no "PSO stats (exit)" block), so a background job
#   creates <run>\cache\pso-stats.now at <run dir creation> + 280 s (only while a game runs); the game logs the summary
#   block within 2 s. pso_post falls back to the 10 s delta lines when the block is missing.
# Config: harness\legodimensions.toml as is (present_effect fsr, passes 1, sharpness 0.0); fine within one bin, but say so in
#   the read-out if the native-fsr1 diff lands first (M10 N3). verify-bins runs on the arm's cold copy before every arm.
# Stops: a refusal or a non-zero run-game exit stops the session (AB-PLAN stop rule); an async arm with "N failed" > 0
#   skips the remaining async arms; a missing seed skips the arms that need it. pso_post.py runs on whatever finished.
# Refuses (exit 3): pin mismatch, verify-bins FAIL, WINDOW-HOLD.txt, day launcher busy, a running game, an Agent 8
#   runner, a hidden desktop (unless allowhidden). run-game only closes the PID it launched.
# Output: post\pso-<mode>-<stamp>.txt (pso_post), post\SHA256SUMS-<stamp>.txt, post\seeds-<stamp>.txt, LATEST.txt.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'; $N2 = $words -contains 'n2'
$Mode = @($words | Where-Object { $_ -in @('rows', 'ab') })
$unknown = @($words | Where-Object { $_ -notin @('rows', 'ab', 'n2', 'dryrun', 'allowhidden') })
if ($Mode.Count -ne 1 -or $unknown.Count -or ($N2 -and $Mode[0] -ne 'ab')) { Write-Host "usage: rows-run.ps1 rows|ab [n2 (ab only)] [dryrun] [allowhidden] (got: $($words -join ' '))"; exit 2 }
$Mode = $Mode[0]
$Seconds = 300
$Fp = '39129c4c059be5f0'
$kit = $PSScriptRoot                                   # build\agent16\psorows
$a16 = Split-Path -Parent $kit
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'pso_post.py'
$refDir = Join-Path $a16 'pack\native4bp-bin'
$refPin = 'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690'
$psoDir = Join-Path $a16 'psobin\native4bp-pso-bin'
$psoPin = 'CA1FB21250289D9C196879AEF5712206FF3ACFEE442E28CA0457EB24FF209544'
$work = Join-Path $kit 'work'
$refCopy = Join-Path $work 'ref'
$psoCopy = Join-Path $work 'pso'
$runsRoot = Join-Path $kit $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$stamp = Get-Date -Format yyyyMMdd-HHmmss
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post'), $work | Out-Null
$log = Join-Path $kit "logs\pso-$Mode-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
$seedLog = Join-Path $kit "post\seeds-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[psorows $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
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
    # the guards of smoke4bp\smoke-run.ps1 (re-checked before every arm)
    $r = @()
    $hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
    if (Test-Path -LiteralPath $hold) { $r += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
    $stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
    if (Test-Path -LiteralPath $stateFile) {
        $st = (Get-Content -LiteralPath $stateFile -TotalCount 1)
        if ($st -match '(?i)waiting-for-quiet|\brunning\b') { $r += "day launcher busy ($st)" }
    }
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
    if ($g.Count) { $r += "a game is running (pid $(($g | ForEach-Object Id) -join ','))" }
    $runners = @(Get-ActiveRunners)
    if ($runners.Count) { $r += "Agent 8 runner active: $($runners -join '; ')" }
    # the timed-window kits (Overseer / M10): their scripts running, or a WINDOW-GO.txt
    $go = Join-Path $ws 'perf-notes\WINDOW-GO.txt'
    if (Test-Path -LiteralPath $go) { $r += "WINDOW-GO.txt present: $((Get-Content -LiteralPath $go -TotalCount 1))" }
    $win = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match '(?i)window-s5\.ps1|RUN-WINDOW-S5|run-matrix' })
    if ($win.Count) { $r += "timed-window kit running (pid $(($win | ForEach-Object ProcessId) -join ','))" }
    $desk = [LdHarness]::DesktopName()
    if ($desk -ne 'Default' -and -not $AllowHidden) { $r += "not on the interactive desktop ($desk)" }
    $r
}
function Test-Seed([string]$runDir, [int]$rc) {
    # returns @{ ok; why; pso; rec; psoSha; recSha; n }
    $s = @{ ok = $false; why = ''; pso = (Join-Path $runDir 'cache\native-pso.bin'); rec = (Join-Path $runDir 'cache\native-pso-recipes.bin'); n = 0 }
    if (-not $runDir -or -not (Test-Path -LiteralPath $runDir)) { $s.why = 'no run dir'; return $s }
    if ($rc -ne 0) { $s.why = "run-game exit $rc"; return $s }
    $gl = Join-Path $runDir 'game.log'
    $m = if (Test-Path -LiteralPath $gl) { Select-String -LiteralPath $gl -Pattern 'saved (\d+) startup pipeline recipes' | Select-Object -Last 1 }
    if (-not $m) { $s.why = 'no "saved N startup pipeline recipes" line in game.log'; return $s }
    $s.n = [int]$m.Matches[0].Groups[1].Value
    if ($s.n -le 0) { $s.why = 'saved 0 recipes'; return $s }
    foreach ($f in @($s.pso, $s.rec)) { if (-not (Test-Path -LiteralPath $f) -or (Get-Item -LiteralPath $f).Length -le 0) { $s.why = "missing or empty $f"; return $s } }
    $s.psoSha = (Get-FileHash -LiteralPath $s.pso -Algorithm SHA256).Hash; $s.recSha = (Get-FileHash -LiteralPath $s.rec -Algorithm SHA256).Hash
    $s.ok = $true; $s
}
function New-Warm([string]$cold, [hashtable]$seed, [string]$dst, [string]$name) {
    # hard links to the cold copy's files + the seed's two cache files; returns the problem count
    # own dir: removes links only; no -Force, so a read-only attribute (shared by all links) is never cleared
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Recurse }
    New-Item -ItemType Directory -Force -Path (Join-Path $dst 'cache') | Out-Null
    $bad = 0; $ln = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $cold -File)) {
        $t = Join-Path $dst $f.Name
        if ([LdHarness]::HardLink($t, $f.FullName)) { $ln++ } else { Copy-Item -LiteralPath $f.FullName -Destination $t; Say "note: copied (no hard link) $($f.Name)" }
    }
    Copy-Item -LiteralPath $seed.pso -Destination (Join-Path $dst 'cache\native-pso.bin')
    Copy-Item -LiteralPath $seed.rec -Destination (Join-Path $dst 'cache\native-pso-recipes.bin')
    $bad += Check-Warm $dst $seed $name
    Add-Content -LiteralPath $seedLog -Value "$name dir=$dst seed_run=$(Split-Path -Parent (Split-Path -Parent $seed.pso)) recipes_saved=$($seed.n) native-pso.bin=$($seed.psoSha) native-pso-recipes.bin=$($seed.recSha) links=$ln"
    Say "warm dir $name`: $ln links to $cold + seed cache (recipes $($seed.n), pso $($seed.psoSha.Substring(0,16)), rec $($seed.recSha.Substring(0,16)))"
    $bad
}
function Check-Warm([string]$dst, [hashtable]$seed, [string]$name) {
    $bad = 0
    foreach ($p in @(@('native-pso.bin', $seed.psoSha), @('native-pso-recipes.bin', $seed.recSha))) {
        $f = Join-Path $dst "cache\$($p[0])"
        if (-not (Test-Path -LiteralPath $f) -or (Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash -ne $p[1]) { Say "FAIL warm $name`: cache\$($p[0]) is not the seed"; $bad++ }
    }
    $bad
}

# --- the arm list ---
$base = 'LEGO_NATIVE_PSO_STATS=1;LEGO_NATIVE_PSO_STATS_INTERVAL=10'
$unl = 'LEGO_NATIVE_PSO_SAVE_UNLOCKED=1;LEGO_NATIVE_PSO_AUX_UNLOCKED=1'
function Arm([string]$name, [string]$bin, [string]$warm, [string]$extra, [bool]$async = $false) {
    # bin: ref|pso; warm: '' (cold) or the seed key; seeds are taken from the arm of the same name
    [pscustomobject]@{ name = $name; bin = $bin; warm = $warm; env = $(if ($extra) { "$base;$extra" } else { $base }); async = $async }
}
$arms = @()
if ($Mode -eq 'rows') {
    $arms += Arm 's0-ref-cold' 'ref' '' ''
    $arms += Arm 'c-pso-t1' 'pso' '' ''
    $arms += Arm 'c-pso-unl' 'pso' '' $unl
    $arms += Arm 'w-ref-t1' 'ref' 's0-ref-cold' ''
    $arms += Arm 'w-pso-t1' 'pso' 's0-ref-cold' ''
    $arms += Arm 'w-ref-t4' 'ref' 's0-ref-cold' 'LEGO_NATIVE_PSO_PREPARE_THREADS=4'
    $arms += Arm 'w-pso-t2' 'pso' 's0-ref-cold' 'LEGO_NATIVE_PSO_PREPARE_THREADS=2'
    $arms += Arm 'w-pso-t4' 'pso' 's0-ref-cold' 'LEGO_NATIVE_PSO_PREPARE_THREADS=4'
    $arms += Arm 'w-pso-unl' 'pso' 'c-pso-unl' $unl
} else {
    $as = 'LEGO_NATIVE_PSO_ASYNC=1'
    $arms += Arm 'prime' 'ref' '' ''
    $blocks = @(@('c0', 'c1', 'w0', 'w1'), @('c1', 'c0', 'w1', 'w0'), @('c0', 'c1', 'w0', 'w1'))
    $nb = if ($N2) { 2 } else { 3 }
    for ($k = 1; $k -le $nb; $k++) {
        foreach ($t in $blocks[$k - 1]) {
            switch ($t) {
                'c0' { $arms += Arm "c0-$k" 'ref' '' '' }
                'c1' { $arms += Arm "c1-$k" 'ref' '' $as $true }
                'w0' { $arms += Arm "w0-$k" 'ref' 'prime' '' }
                'w1' { $arms += Arm "w1-$k" 'ref' 'prime' $as $true }
            }
        }
    }
    if (-not $N2) { 1..2 | ForEach-Object { $arms += Arm "w2-$_" 'ref' 'prime' 'LEGO_NATIVE_PSO_PREPARE_THREADS=4' } }
}
$est = [int][Math]::Ceiling($arms.Count * 5.6 + 3)
Say "S5 PSO $Mode$(if ($N2) { ' n2' }) $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); $($arms.Count) arms x -Seconds $Seconds, ~$est min; WS $ws"
Say "arms: $(($arms | ForEach-Object { $_.name }) -join ' ')"

# --- preconditions ---
$fail = @()
foreach ($p in @($rg, $route, $vb, $post, (Join-Path $ws 'harness\guard.ps1'), (Join-Path $ws 'harness\winhelper.cs'))) { if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } }
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
. (Join-Path $ws 'harness\guard.ps1')
Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
$desk = [LdHarness]::DesktopName()
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: functional only, never timed)' })"
$stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
if (Test-Path -LiteralPath $stateFile) { Say "day launcher: $(Get-Content -LiteralPath $stateFile -TotalCount 1)" }
$refuse = @(Get-Refusals)
$needPso = [bool]@($arms | Where-Object { $_.bin -eq 'pso' }).Count
$r = Check-Pin $refDir $refPin 'native4bp-bin'; if ($r) { $refuse += $r }
if ($needPso) { $r = Check-Pin $psoDir $psoPin 'native4bp-pso-bin'; if ($r) { $refuse += $r } }
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

# --- cold work copies ---
$bad = Sync-Copy $refDir $refCopy
if ($needPso) { $bad += Sync-Copy $psoDir $psoCopy }
if (-not $bad) { foreach ($c in @($refCopy) + $(if ($needPso) { @($psoCopy) } else { @() })) { $rc = Run-Logged 'python' @('-B', $vb, $c); if ($rc -ne 0) { Say "FAIL verify-bins on $c"; $bad++ } } }
if ($bad) { exit 2 }
$cold = @{ ref = $refCopy; pso = $psoCopy }

function Rg-Args($arm, [string]$bin, [string]$root, [bool]$dry) {
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $arm.name,
        '-RunsRoot', $root, '-InputScript', $route, '-Env', $arm.env)
    if ($dry) { $x += '-DryRun' }; $x
}
$TriggerLead = 20   # the watchdog hard-exits the game (no Stop(), no exit summary): ask for the summary 20 s before the close
$TriggerJob = {
    # creates <run>\cache\pso-stats.now at <run dir creation> + Seconds - Lead (only while the game runs, unless -not $needGame)
    param([string]$root, [string]$tag, [datetime]$t0, [int]$sec, [int]$lead, [bool]$needGame)
    $deadline = (Get-Date).AddSeconds(180); $run = $null
    while (-not $run -and (Get-Date) -lt $deadline) {
        $run = Get-ChildItem -LiteralPath $root -Directory -Filter "*-$tag*" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^\d{8}-\d{6}-$([regex]::Escape($tag))(-\d+)?$" -and $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1
        if (-not $run) { Start-Sleep -Milliseconds 500 }
    }
    if (-not $run) { return "trigger: no run dir for $tag" }
    $at = $run.CreationTime.AddSeconds($sec - $lead); $w = ($at - (Get-Date)).TotalSeconds
    if ($w -gt 0) { Start-Sleep -Seconds ([int][Math]::Ceiling($w)) }
    # only a game started for this arm (after the run dir appeared) counts, not a foreign one
    if ($needGame -and -not (Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $run.CreationTime.AddSeconds(-5) })) { return "trigger: game not running at +$($sec - $lead) s, not created" }
    $f = Join-Path $run.FullName 'cache\pso-stats.now'
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $f) | Out-Null
    New-Item -ItemType File -Force -Path $f | Out-Null
    "trigger: created $f at $((Get-Date).ToString('HH:mm:ss'))"
}
function Cmd-Line([string[]]$x) { 'powershell ' + (($x | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }
function Warm-Dir($arm) { Join-Path $work "$($arm.bin)-warm-$($arm.warm)" }

if ($DryRun) {
    $bad = 0
    foreach ($arm in $arms) {
        $bin = if ($arm.warm) { Warm-Dir $arm } else { $cold[$arm.bin] }
        Say "COMMAND (real run, arm $($arm.name)$(if ($arm.warm) { ", warm from $($arm.warm)" })): $(Cmd-Line (Rg-Args $arm $bin (Join-Path $kit 'runs') $false))"
        $rc = Run-Logged 'powershell' (Rg-Args $arm $cold[$arm.bin] $runsRoot $true)   # stand-in BinDir: the cold copy
        Say "run-game -DryRun ($($arm.name)) exit $rc"; if ($rc -ne 0) { $bad++ }
    }
    # the seed / warm-dir code on a synthetic seed run dir (game.log + two small cache files)
    $fake = Join-Path $kit 'logs\dry-seed'
    if (Test-Path -LiteralPath $fake) { Remove-Item -LiteralPath $fake -Recurse -Force }
    New-Item -ItemType Directory -Force -Path (Join-Path $fake 'cache') | Out-Null
    Set-Content -LiteralPath (Join-Path $fake 'game.log') -Value '[info] Native GPU: saved 7 startup pipeline recipes' -Encoding ascii
    Set-Content -LiteralPath (Join-Path $fake 'cache\native-pso.bin') -Value 'dry pso blob' -Encoding ascii
    Set-Content -LiteralPath (Join-Path $fake 'cache\native-pso-recipes.bin') -Value 'dry recipes' -Encoding ascii
    $neg = Test-Seed $fake 1; $s = Test-Seed $fake 0
    Say "seed check: exit-1 seed $(if ($neg.ok) { 'ACCEPTED (BAD)' } else { "refused ($($neg.why))" }); synthetic seed $(if ($s.ok) { "ok, $($s.n) recipes" } else { "REFUSED (BAD): $($s.why)" })"
    if ($neg.ok -or -not $s.ok) { $bad++ }
    if ($s.ok) {
        $wd = Join-Path $work 'dry-warm'
        $bad += New-Warm $refCopy $s $wd 'dry'
        $nl = @(Get-ChildItem -LiteralPath $wd -File).Count; $nc = @(Get-ChildItem -LiteralPath $refCopy -File).Count
        Say "dry warm dir: $nl files (cold copy $nc), cache\ $(@(Get-ChildItem -LiteralPath (Join-Path $wd 'cache') -File).Count) files"
        if ($nl -ne $nc) { $bad++ }
        Remove-Item -LiteralPath $wd -Recurse; Remove-Item -LiteralPath $fake -Recurse -Force
        $left = @(Get-ChildItem -LiteralPath $refCopy -File).Count
        Say "dry warm dir removed; cold copy still $left files"; if ($left -ne $nc) { $bad++ }
    }
    # the pso-stats.now trigger job on a synthetic run dir (fires at once: sec = lead + 1, no game needed)
    $td = Join-Path $runsRoot "$stamp-trigtest"; New-Item -ItemType Directory -Force -Path $td | Out-Null
    $j = Start-Job -ScriptBlock $TriggerJob -ArgumentList $runsRoot, 'trigtest', (Get-Date), ($TriggerLead + 1), $TriggerLead, $false
    $jr = if (Wait-Job $j -Timeout 30) { Receive-Job $j } else { 'trigger job timed out' }; Remove-Job $j -Force
    $tok = Test-Path -LiteralPath (Join-Path $td 'cache\pso-stats.now')
    Say "trigger self-test: $jr; file $(if ($tok) { 'present' } else { 'MISSING' })"; if (-not $tok) { $bad++ }
    $rc = Run-Logged 'python' @('-B', $post, '--selftest', '--out', (Join-Path $kit "logs\post-selftest-$stamp.txt"))
    Say "pso_post self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say 'dryrun-runs has reparse points: NOT deleted'; $bad++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say 'dryrun-runs removed' }
    }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
$seeds = @{}; $warmReady = @{}; $done = @(); $skipped = @(); $stop = ''; $asyncStop = ''; $rcAll = 0
Set-Content -LiteralPath $seedLog -Value "S5 PSO $Mode seeds $stamp" -Encoding ascii
function Stop-Ours {
    # abort/error cleanup: only what this script started. Our game = a legodimensions.exe whose image lives under our
    # runs root (run-game hard-links the exe into the run dir); our run-game = a child powershell of this process.
    if ($script:j) { Stop-Job $script:j -ErrorAction SilentlyContinue; Remove-Job $script:j -Force -ErrorAction SilentlyContinue; $script:j = $null; Say 'cleanup: trigger job stopped' }
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
$j = $null; $armActive = $false
try {
foreach ($arm in $arms) {
    if ($stop) { $skipped += "$($arm.name) (stopped: $stop)"; continue }
    if ($arm.async -and $asyncStop) { $skipped += "$($arm.name) ($asyncStop)"; continue }
    $bin = $cold[$arm.bin]
    if ($arm.warm) {
        if (-not $seeds[$arm.warm]) { $skipped += "$($arm.name) (no valid seed from $($arm.warm))"; Say "SKIP $($arm.name): no valid seed from $($arm.warm)"; continue }
        $bin = Warm-Dir $arm
        if (-not $warmReady[$bin]) {
            if (New-Warm $cold[$arm.bin] $seeds[$arm.warm] $bin "$($arm.bin)-warm-$($arm.warm)") { $stop = "warm dir $bin failed"; $skipped += "$($arm.name) ($stop)"; continue }
            $warmReady[$bin] = $true
        } elseif (Check-Warm $bin $seeds[$arm.warm] "$($arm.bin)-warm-$($arm.warm)") { $stop = "warm dir $bin changed"; $skipped += "$($arm.name) ($stop)"; continue }
    } elseif (@(Get-ChildItem -LiteralPath $bin -Directory).Count) { $stop = "cold copy $bin has a subdirectory"; $skipped += "$($arm.name) ($stop)"; continue }
    # M10 S2: the arm's cold copy (also the data behind its warm dir's hard links) = MANIFEST, before every arm
    $rc = Run-Logged 'python' @('-B', $vb, $cold[$arm.bin])
    if ($rc -ne 0) { $stop = "verify-bins FAIL on $($cold[$arm.bin]) before $($arm.name)"; Say "FAIL $stop"; $rcAll = 1; $skipped += "$($arm.name) ($stop)"; continue }
    $ref = @(Get-Refusals)
    if ($ref.Count) { $stop = "refused before $($arm.name): $($ref -join '; ')"; Say "REFUSED: $stop"; $skipped += "$($arm.name) (refused)"; continue }
    $x = Rg-Args $arm $bin $runsRoot $false
    Say "START $($arm.name): $(Cmd-Line $x)"
    $t0 = Get-Date
    $j = Start-Job -ScriptBlock $TriggerJob -ArgumentList $runsRoot, $arm.name, $t0, $Seconds, $TriggerLead, $true
    $armActive = $true
    $rc = Run-Logged 'powershell' $x
    $armActive = $false
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($arm.name)*" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^\d{8}-\d{6}-$([regex]::Escape($arm.name))(-\d+)?$" -and $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '' }
    $jr = if (Wait-Job $j -Timeout 10) { Receive-Job $j } else { 'trigger job still waiting: stopped' }; Remove-Job $j -Force; $j = $null
    $sumLine = if ($runDir) { Select-String -LiteralPath (Join-Path $runDir 'game.log') -Pattern 'PSO stats \(pso-stats\.now\)' -ErrorAction SilentlyContinue | Select-Object -Last 1 }
    Say "$jr; summary block $(if ($sumLine) { 'logged' } else { 'NOT logged (pso_post falls back to the delta lines)' })"
    Say "run-game ($($arm.name)) exit $rc, run $(if ($runDir) { $runDir } else { '?' }), $([int]((Get-Date) - $t0).TotalSeconds) s"
    if ($runDir) { $done += "$($arm.name)=$runDir" }
    if ($rc -ne 0) { $rcAll = 1; $stop = "run-game exit $rc on $($arm.name)"; continue }
    if (@($arms | Where-Object { $_.warm -eq $arm.name }).Count) {
        $s = Test-Seed $runDir $rc
        if ($s.ok) { $seeds[$arm.name] = $s; Say "seed $($arm.name): $($s.n) recipes saved, pso $($s.psoSha.Substring(0,16)), rec $($s.recSha.Substring(0,16))" }
        else { Say "FAIL seed $($arm.name): $($s.why) (the arms warm from it are skipped)"; $rcAll = 1 }
    }
    if ($arm.async -and $runDir) {
        $m = Select-String -LiteralPath (Join-Path $runDir 'game.log') -Pattern 'PSO async: .*?(\d+) failed' -ErrorAction SilentlyContinue | Where-Object { [int]$_.Matches[0].Groups[1].Value -gt 0 } | Select-Object -First 1
        if ($m) { $asyncStop = "async stop rule: $($arm.name) had failed > 0"; Say "STOP RULE: $asyncStop" }
    }
}
} catch { Say "ERROR: $($_.Exception.Message)"; $rcAll = 1; if (-not $stop) { $stop = "error: $($_.Exception.Message)" } } finally { Stop-Ours }
$skipped | ForEach-Object { Say "skipped: $_" }
# the cold copies must still match their sources (nothing writes into them)
foreach ($c in @($refCopy) + $(if ($needPso) { @($psoCopy) } else { @() })) { $rc = Run-Logged 'python' @('-B', $vb, $c); if ($rc -ne 0) { Say "FAIL verify-bins on $c after the arms"; $rcAll = 1 } }
$postOut = Join-Path $kit "post\pso-$Mode-$stamp.txt"
$postArgs = @('-B', $post, '--mode', $Mode)
if ($N2) { $postArgs += '--n2' }
foreach ($d in $done) { $postArgs += @('--arm', $d) }
$postArgs += @('--expect-fp', $Fp, '--out', $postOut)
$prc = Run-Logged 'python' $postArgs
$verdict = (Select-String -LiteralPath $postOut -Pattern '^RESULT: ' -ErrorAction SilentlyContinue | Select-Object -Last 1).Line
$sums = Join-Path $kit "post\SHA256SUMS-$stamp.txt"
@(Get-Item -LiteralPath $postOut, $seedLog, $log -ErrorAction SilentlyContinue) | ForEach-Object { "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)  $($_.Length)  $($_.FullName.Substring($ws.Length + 1))" } | Set-Content -LiteralPath $sums -Encoding ascii
Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp mode=$Mode$(if ($N2) { '-n2' }) exit=$rcAll post=$prc arms=$($done.Count)/$($arms.Count) report=$postOut $(if ($stop) { "stopped=[$stop] " })$verdict" -Encoding ascii
Say "PSO $Mode DONE: $($done.Count)/$($arms.Count) arms; run-game $(if ($rcAll) { 'had a problem' } else { 'all exit 0' }); post exit $prc; $verdict; report $postOut"
exit $(if ($rcAll -ne 0 -or $prc -ne 0 -or $stop) { 1 } else { 0 })
