# gameplay-run.ps1 - M3 gameplay task: scripted LEGO Dimensions gameplay route (functional + visual, NEVER timed).
# Words (any order):
#   explore      the exploration route (explore-route.txt: front-end-marker-gated boot -> New Game -> the story's 3 figure
#                prompts -> 120 s observe -> single probes -> walk/fight probe loop, a mark + screenshot at every step);
#                -Seconds 1500 (a cap: the route stops itself); arms default to native only.
#                Without it: gameplay-route.txt (the same gated boot + prompts, then a walk/fight route) on native, then
#                xenos; -Seconds 1500 per arm (a cap: the route stops itself).
#   manual       an untimed hand-driven session: no route, no -InputScript (so the game keeps its default SDL input:
#                keyboard to the FOCUSED visible window, or a real pad), -Seconds 1200, native only by default,
#                tag gpman-<arm>; the sidecar still places the 3 tags (no v-replace) and answers the story's pad prompts;
#                Toypad by hand: one command per file in <run>\toypad-ctl\NNN.cmd (place <tag> <pad> | remove <tag> |
#                move <tag> <pad> | swap <a> <b> | replace <tag> | status; pads 1 centre 2 left 3 right); no watcher, no post.
#   nativeonly | xenosonly   one arm only.
#   dump         DIAGNOSTIC, only with 'manual' (native arm): adds LEGO_DUMP_MISSING_SHADERS=<kit>\shader-dumps-native-<stamp>
#                (M16 PLAN-story-dump option A: miss cache off + pool-copy hash check, so the run's timing is invalid).
#   zone         not with 'manual': the prompt sidecar gets --zone --zone-delay 45 (answers the story's zone step from the
#                Toy Pad LEDs: pad 3 Wyldstyle, pad 2 Gandalf, pad 1 Batman; see prompt_sidecar.py; first pad 3 command at
#                T0 + 45 s, M10 Z-S1: earliest evidenced accept ~T0 + 48.5 s) and the route mark v-replace is
#                not wired (it would reshuffle the figures during the step). Off unless this word is given.
#                Explore and route runs always pass --led-shots (the watcher also shoots the sidecar's LED-state rows).
#   cand5        M16 proof5 candidate (PLAN-proof5), ONLY with 'nativeonly' (exit 2 with manual / explore / dump /
#                xenosonly or without nativeonly): the native arm runs build\agent16\pack\native5pack-bin (MANIFEST
#                787CD694..46A1, exe 90BF6B45..EE7D, fp a349d5292f67b127) from its own copy bin-native5 (bin-native is
#                not touched), tag gp5-native, trace dir trace-native5-<stamp>, post --expect-fp a349d5292f67b127.
#                Without this word nothing changes (native4bp-bin, bin-native, gp-native, trace-native-<stamp>, 39129c4c).
#   dryrun       no game: preconditions (reported), pin + copy checks, the real command lines, run-game -DryRun per arm
#                (also parses the route), route = generator output, prompt sidecar --help + self-test + tag check, watcher + post
#                self-tests; removes dryrun-runs. Prints DRY RUN ALL PASS and exits 0 when everything passes.
#                HEAVY: it copies + sha256-checks the pinned bins (native ~382 MB, xenos ~225 MB) and runs verify-bins
#                twice per arm, even when a real run would refuse. Run it only when the PC is free for I/O.
#   allowhidden  run even if not on the interactive desktop ('Default') (no screenshots then).
# Arm: harness\run-game.ps1 -BinDir <kit copy> -Seconds <1500, manual 1200> -GpuLog -Tag <tag> -RunsRoot build\agent3\gameplay\runs
#      -InputScript <route> -Cvar <cap> [-Env LEGO_NATIVE_TRACE_DIR=<abs>]; each run gets a fresh <run>\user (sandbox
#      profile/saves: the user's own profile is never read or written). VPad = harness default
#      build\agent3\vpad\xinput1_4.dll (read-only; nothing under build\agent3\vpad is touched).
#   native: build\agent16\pack\native4bp-bin (MANIFEST C5181520..A690, fp 39129c4c059be5f0), native_fps_limit=60, trace on
#           (with 'cand5': native5pack-bin, see above).
#   xenos : build\agent2\devfinal2-bin (MANIFEST 4A4A13ED..982D, BIN-PINS.md), framerate_limit=60.
#   (caps as M8's build\agent8\s5\matrix-s5-baseline.json). Pinned dirs are only read: sha256-checked copies in
#   build\agent3\gameplay\bin-<arm> are what runs.
# Beside each arm (started and stopped by this script only): prompt_sidecar.py (this kit; imports build\agent3\toypad
# read-only) with --tags-dir build\agent3\gameplay\tags (places the virtual
# Batman/Gandalf/Wyldstyle tags 2 s after the front end's all-pads-white line; at the route mark v-replace it REMOVEs and
# re-LOADs them; on the story's pad prompts (pad N mode 3 lit <colour> pulses) it re-places / moves the asked figure onto
# that pad; route marks tp-<cmd>-<args> and ctl files <run>\toypad-ctl\*.cmd (place/remove/move/swap/replace/status, one
# command per line; renamed .done/.err) drive it mid-game; logs <run>\toypad-events.csv), build\agent3\s4b\holdwatch.ps1 (stops OUR game if
# perf-notes\WINDOW-HOLD.txt appears), gameplay-watch.ps1 (a JPEG of the game window at every route mark).
# Then gameplay_post.py -> post\gameplay-<stamp>.txt (+ SHA256SUMS, LATEST.txt).
# Refuses (exit 3): another instance of this kit (logs\gameplay.lock), a pin mismatch, verify-bins FAIL,
# WINDOW-HOLD.txt or WINDOW-GO.txt, a running window-s5.ps1 / RUN-WINDOW-S5 / run-matrix, day launcher state
# waiting-for-quiet/running, a running game, an Agent 8 runner (harness\guard.ps1), a hidden desktop (unless
# allowhidden), < 6 GB RAM free.
# Exit 2 = missing file / copy problem. run-game only closes the PID it launched. If this script stops early (error,
# Ctrl-C), its finally block closes OUR game (legodimensions under the runs dir, started by this run; WM_CLOSE, kill
# after 30 s) and stops the helpers it started, by their held handles. A closed console window can't run it.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$known = @('explore', 'manual', 'nativeonly', 'xenosonly', 'dryrun', 'allowhidden', 'dump', 'zone', 'cand5')
$unknown = @($words | Where-Object { $known -notcontains $_ })
if ($unknown.Count) { Write-Host "unknown word(s): $($unknown -join ' ') (known: $($known -join ' '))"; exit 2 }
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'; $Explore = $words -contains 'explore'
$Manual = $words -contains 'manual'
if ($Manual -and $Explore) { Write-Host "'manual' and 'explore' exclude each other"; exit 2 }
$Dump = $words -contains 'dump'   # FUNCTIONAL ONLY: LEGO_DUMP_MISSING_SHADERS (miss cache OFF, pool-copy hash check)
if ($Dump -and -not $Manual) { Write-Host "'dump' is allowed only with 'manual' (functional, untimed)"; exit 2 }
if ($Dump -and ($words -contains 'xenosonly')) { Write-Host "'dump' needs the native arm (not with 'xenosonly')"; exit 2 }
$Zone = $words -contains 'zone'   # prompt sidecar --zone (Toy Pad actions from the LEDs); explore / route only
if ($Zone -and $Manual) { Write-Host "'zone' is not allowed with 'manual' (there the ctl files drive the zone step)"; exit 2 }
$Cand5 = $words -contains 'cand5'   # M16 proof5: native arm = native5pack-bin (copy bin-native5, tag gp5, fp a349d529)
if ($Cand5 -and ($Manual -or $Explore -or $Dump)) { Write-Host "'cand5' is not allowed with 'manual', 'explore' or 'dump' (route runs with 'nativeonly' only)"; exit 2 }
if ($Cand5 -and (($words -notcontains 'nativeonly') -or ($words -contains 'xenosonly'))) { Write-Host "'cand5' needs 'nativeonly' (and not 'xenosonly')"; exit 2 }
$Seconds = if ($Manual) { 1200 } else { 1500 }   # explore + route: a cap (the route's 'stop' ends it, ~900 s)
$kit = $PSScriptRoot                                   # build\agent3\gameplay
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$hw = Join-Path $ws 'build\agent3\s4b\holdwatch.ps1'
$sidecar = Join-Path $ws 'build\agent3\toypad\toypad_sidecar.py'   # read-only: prompt_sidecar.py imports it (+ ldtag, toypad_client)
$psc = Join-Path $kit 'prompt_sidecar.py'
$pst = Join-Path $kit 'selftest_prompt.py'
$fake = Join-Path $ws 'build\agent3\toypad\fake_listener.py'        # read-only: the prompt self-test's stand-in listener
# the story's pad prompts (manual run 20261125-204323: each pulses 120 s, then the game's failsafe goes on without it)
$onSpecs = @('pad (?P<pad>[123]) mode 3 lit (00 00 16|00 00 05)=>batman@*', 'pad (?P<pad>[123]) mode 3 lit (F4 69 16|3D 1A 05)=>gandalf@*',
    'pad (?P<pad>[123]) mode 3 lit (F4 00 16|3D 00 05)=>wyldstyle@*')
$post = Join-Path $kit 'gameplay_post.py'
$watch = Join-Path $kit 'gameplay-watch.ps1'
$gen = Join-Path $kit 'gen_gameplay_route.py'
$tags = Join-Path $kit 'tags'                          # N4: copies of build\agent3\toypad\tags (nothing written outside the kit)
$route = Join-Path $kit $(if ($Explore) { 'explore-route.txt' } else { 'gameplay-route.txt' })
$runsRoot = Join-Path $kit $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$shots = Join-Path $kit "shots\$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $kit 'logs'), (Join-Path $kit 'post'), $runsRoot | Out-Null
$log = Join-Path $kit "logs\gameplay-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[gameplay $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}
# N1: one instance of this kit at a time (dryrun included); the lock is held until this process exits
try { $lock = [IO.File]::Open((Join-Path $kit 'logs\gameplay.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
catch { Say 'REFUSED: another gameplay-run instance holds logs\gameplay.lock'; exit 3 }
# N5: the real interpreter (not the WindowsApps alias), so a Start-Process PID is the python that runs the sidecar
$ErrorActionPreference = 'Continue'
$py = "$(& python -B -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1)".Trim()
$ErrorActionPreference = 'Stop'
if (-not $py -or -not (Test-Path -LiteralPath $py -PathType Leaf)) { Say "FAIL cannot resolve the python interpreter ('$py')"; exit 2 }
Say "python $py"
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
    foreach ($e in @(Get-ChildItem -LiteralPath $dst -Directory)) { Say "FAIL extra subdirectory in $dst`: $($e.Name)"; $bad++ }
    Say "copy $dst`: $($files.Count) files, $n copied now, $(if ($bad) { "$bad PROBLEMS" } else { 'all sha256 = source' })"
    $bad
}

$allArms = @(
    [pscustomobject]@{ name = 'native'; pinned = (Join-Path $ws 'build\agent16\pack\native4bp-bin'); copy = (Join-Path $kit 'bin-native')
        manifest = 'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690'; cvar = 'native_fps_limit=60'; trace = $true; tr = 'native' },
    [pscustomobject]@{ name = 'xenos'; pinned = (Join-Path $ws 'build\agent2\devfinal2-bin'); copy = (Join-Path $kit 'bin-xenos')
        manifest = '4A4A13EDFBFF6A5F32798837A4156256A5A58A2C44579F272B5147768E50982D'; cvar = 'framerate_limit=60'; trace = $false; tr = 'xenos' }
)
if ($Cand5) {   # arm name stays 'native' (post: --arm native=..., native fingerprint check)
    $allArms[0].pinned = Join-Path $ws 'build\agent16\pack\native5pack-bin'; $allArms[0].copy = Join-Path $kit 'bin-native5'
    $allArms[0].manifest = '787CD694F0B884D99D1D1E3C807642B33CBA22D79A8F9253C071A8898D1446A1'; $allArms[0].tr = 'native5'
}
$want = if ($words -contains 'nativeonly') { @('native') } elseif ($words -contains 'xenosonly') { @('xenos') } elseif ($Explore -or $Manual) { @('native') } else { @('native', 'xenos') }
$arms = @($allArms | Where-Object { $want -contains $_.name })
$nativeFp = if ($Cand5) { 'a349d5292f67b127' } else { '39129c4c059be5f0' }
$wiringFp = '39129c4c059be5f0'   # dryrun native wiring stand-in: M16's native4bp smoke run (always 39129c4c)
Say "gameplay $(if ($Manual) { 'MANUAL' } elseif ($Explore) { 'EXPLORE' } else { 'ROUTE' }) $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); arms $($want -join ', '); route $(if ($Manual) { 'none (manual: no -InputScript, default SDL input)' } else { $route }); -Seconds $Seconds; WS $ws"
if ($Dump) { Say "DIAGNOSTIC: dump on, timing invalid (LEGO_DUMP_MISSING_SHADERS=$(Join-Path $kit "shader-dumps-native-$stamp"))" }
if ($Zone) { Say 'ZONE: prompt sidecar --zone --zone-delay 45 on (zone step answered from the Toy Pad LEDs); route mark v-replace not wired' }
if ($Cand5) { Say "CAND5: native arm = $($allArms[0].pinned) (MANIFEST $($allArms[0].manifest.Substring(0,16))), copy $($allArms[0].copy), tag gp5-native, trace trace-native5-$stamp, post --expect-fp $nativeFp" }

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $vb, $hw, $sidecar, $psc, $pst, $fake, $post, $watch, $gen, $route, (Join-Path $tags 'batman.bin'), (Join-Path $tags 'gandalf.bin'), (Join-Path $tags 'wyldstyle.bin'))) { if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" } }
foreach ($arm in $arms) { if (-not (Test-Path -LiteralPath (Join-Path $arm.pinned 'MANIFEST.txt'))) { $fail += "missing $($arm.pinned)\MANIFEST.txt" } }
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
$rc = Run-Logged $py @('-B', $gen, '--check')
if ($rc -ne 0) { Say "FAIL route files differ from gen_gameplay_route.py output (exit $rc)"; exit 2 }
foreach ($arm in $arms) {
    $ms = (Get-FileHash -LiteralPath (Join-Path $arm.pinned 'MANIFEST.txt') -Algorithm SHA256).Hash
    Say "$($arm.name) pinned MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $arm.manifest) { '= pin' } else { 'NOT the pin ' + $arm.manifest.Substring(0,16) })"
    if ($ms -ne $arm.manifest) { $refuse += "$($arm.name) MANIFEST is not the pin" }
    else { $rc = Run-Logged $py @('-B', $vb, $arm.pinned); if ($rc -ne 0) { $refuse += "verify-bins FAIL for $($arm.pinned) (exit $rc)" } }
}
$hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
if (Test-Path -LiteralPath $hold) { $refuse += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
$wgo = Join-Path $ws 'perf-notes\WINDOW-GO.txt'
if (Test-Path -LiteralPath $wgo) { $refuse += "WINDOW-GO.txt present (a timing window is armed)" }
# S3: a timing window's own scripts (guard.ps1 covers only run-matrix / run-timing / first-boot). D1: only a shell that
# RUNS one (powershell/pwsh -File <...>.ps1, or cmd with the .cmd), so an agent shell that merely greps the names passes
$win = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -match '^(?i)(powershell|pwsh|cmd)\.exe$' -and
    "$($_.CommandLine)" -match '(?i)(-File\s+"?[^"]*(window-s5|run-matrix)\.ps1)|(RUN-WINDOW-S5[^\s"]*\.cmd)' })
if ($win.Count) { $refuse += "timing window running: $(($win | ForEach-Object { "$($_.Name) pid $($_.ProcessId)" }) -join '; ')" }
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
$free = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
Say ("RAM free {0:0.0} GB" -f $free)
if ($free -lt 6) { $refuse += ("only {0:0.0} GB RAM free (< 6)" -f $free) }
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

# --- work copies (pinned dirs are only read) ---
$bad = 0
foreach ($arm in $arms) {
    $b = Sync-Copy $arm.pinned $arm.copy
    if (-not $b) { $rc = Run-Logged $py @('-B', $vb, $arm.copy); if ($rc -ne 0) { Say "FAIL verify-bins on $($arm.copy)"; $b++ } }
    $bad += $b
}
if ($bad) { exit 2 }

$tagBase = if ($Manual) { 'gpman' } elseif ($Explore) { 'gpexp' } elseif ($Cand5) { 'gp5' } else { 'gp' }
function Rg-Args($arm, [string]$root, [string]$trace, [bool]$dry) {
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $arm.copy, '-Seconds', "$Seconds", '-GpuLog',
        '-Tag', "$tagBase-$($arm.name)", '-RunsRoot', $root)
    if (-not $Manual) { $x += @('-InputScript', $route) }   # manual: no vpad, no xinput backend: the game's default SDL input
    $x += @('-Cvar', $arm.cvar)
    if ($arm.trace) {
        $e = "LEGO_NATIVE_TRACE_DIR=$trace"   # run-game splits -Env on ';' (no ';' in these kit paths)
        if ($Dump) { $e += ";LEGO_DUMP_MISSING_SHADERS=$(Join-Path $kit "shader-dumps-$($arm.name)-$stamp")" }
        $x += @('-Env', $e)
    }
    if ($dry) { $x += '-DryRun' }; $x
}
function Cmd-Line([string[]]$x) { 'powershell ' + (($x | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }
function Sidecar-Args($arm, [string]$root, [datetime]$t0) {
    $s = @('-B', $psc, '--runs-root', $root, '--tag', "$tagBase-$($arm.name)", '--not-before', $t0.ToString('o'), '--tags-dir', $tags,
        '--timeout', "$($Seconds + 240)", '--delay', '2', '--boot', 'starter')
    foreach ($o in $onSpecs) { $s += @('--on', $o) }
    if (-not $Manual) { $s += '--led-shots'; if ($Zone) { $s += @('--zone', '--zone-delay', '45') } else { $s += @('--then-mark', 'v-replace', '--then-delay', '1', '--then-action', 'replace') } }; $s
}

if ($DryRun) {
    $bad = 0
    foreach ($arm in $arms) {
        $tr = Join-Path $kit "trace-$($arm.tr)-$stamp"
        Say "COMMAND (real run, arm $($arm.name)): $(Cmd-Line (Rg-Args $arm (Join-Path $kit 'runs') $tr $false))"
        $sca = @((Sidecar-Args $arm (Join-Path $kit 'runs') (Get-Date)) | ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } })
        Say "SIDECAR (real run, arm $($arm.name)): $py $($sca -join ' ')"
        $rc = Run-Logged 'powershell' (Rg-Args $arm $runsRoot $tr $true)
        Say "run-game -DryRun ($($arm.name)) exit $rc"; if ($rc -ne 0) { $bad++ }
        $dd = Join-Path $kit "shader-dumps-$($arm.name)-$stamp"
        if (Test-Path -LiteralPath $dd) { Say "FAIL dryrun left a dump dir: $dd"; $bad++ }
    }
    $ErrorActionPreference = 'Continue'
    $h = @(& $py -B $psc --help 2>&1 | ForEach-Object { "$_" }); $hrc = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $okh = ($hrc -eq 0) -and (($h -join ' ') -match '--then-mark') -and (($h -join ' ') -match '--then-action') -and (($h -join ' ') -match '--on ') -and (($h -join ' ') -match '--zone ') -and (($h -join ' ') -match '--led-shots')
    Say "prompt sidecar --help exit $hrc, then-mark/then-action/on/zone/led-shots flags $(if ($okh) { 'present' } else { 'MISSING' })"; if (-not $okh) { $bad++ }
    $rc = Run-Logged $py @('-B', $pst)
    Say "prompt sidecar self-test (fake listener: boot, prompts, ctl place/remove/move/swap/replace/status, route marks, bad --on, zone step + retry/stop, led shots) exit $rc"; if ($rc -ne 0) { $bad++ }
    $tc = "import sys; sys.path.insert(0, r'$(Split-Path -Parent $sidecar)'); import ldtag, toypad_client as tc; t = tc.starter_tags(r'$tags'); print('tags ok: ' + ', '.join('%s id=%d pad=%d index=%d' % (n, ldtag.figure_id(x), p, i) for n, p, i, x in t)); sys.exit(0 if len(t) == 3 else 1)"
    $rc = Run-Logged $py @('-B', '-c', $tc)
    Say "starter tag check exit $rc"; if ($rc -ne 0) { $bad++ }
    $old = Join-Path $ws 'build\agent3\runs\20261122-221447-s4b-20-m1-level'
    $old2 = Join-Path $ws 'build\agent3\runs\20261122-210059-s4b-L0-off-level'
    $rc = Run-Logged 'powershell' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $watch, '-Arm', 'dry', '-OutDir', (Join-Path $kit 'logs\watch-selftest'), '-SelfTest', '-SelfTestCsv', (Join-Path $old 'input.csv'))
    Say "watcher self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    $rc = Run-Logged $py @('-B', $post, '--selftest', $old, '--selftest', $old2, '--out', (Join-Path $kit "logs\post-selftest-$stamp.txt"))
    Say "gameplay_post self-test exit $rc"; if ($rc -ne 0) { $bad++ }
    # native wiring: M16's native4bp smoke run (read-only) as a stand-in native arm (no vortex there: its RESULT FAILs by design)
    $m16 = Join-Path $ws 'build\agent16\smoke4bp'
    $nr = Join-Path $m16 'runs\20261125-174131-smoke-4bp'; $nt = Join-Path $m16 'trace-4bp-20261125-174125'; $ns = Join-Path $m16 'shots\20261125-174125'
    if ((Test-Path -LiteralPath $nr) -and (Test-Path -LiteralPath $nt)) {
        $wo = Join-Path $kit "logs\post-native-wiring-$stamp.txt"
        $rc = Run-Logged $py @('-B', $post, '--arm', "native=$nr,$nt,$ns", '--expect-fp', $wiringFp, '--out', $wo)
        $txt = Get-Content -LiteralPath $wo -Raw -ErrorAction SilentlyContinue
        $ok = ($rc -eq 0) -and ($txt -match 'PASS native fingerprint') -and ($txt -match 'missing draws \(native trace') -and ($txt -match '(?m)^RESULT: ')
        Say "post native wiring (M16 smoke run as stand-in) exit $rc, fingerprint + trace + RESULT $(if ($ok) { 'ok' } else { 'BAD' })"; if (-not $ok) { $bad++ }
    } else { Say 'note: M16 smoke run not found: native wiring test skipped' }
    # word combos that must exit 2 (they exit in the word checks, before the lock, python and any file work)
    foreach ($wc in @('zone manual', 'cand5 manual nativeonly', 'cand5 explore nativeonly', 'cand5 manual dump nativeonly', 'cand5', 'cand5 nativeonly xenosonly', 'dump', 'bogusword')) {
        $rc = Run-Logged 'powershell' (@('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath) + @($wc -split ' '))
        Say "word combo '$wc' exit $rc $(if ($rc -eq 2) { '(expected 2: ok)' } else { '(expected 2: BAD)' })"; if ($rc -ne 2) { $bad++ }
    }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say 'dryrun-runs has reparse points: NOT deleted'; $bad++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say 'dryrun-runs removed' }
    }
    Say "DRY RUN $(if ($bad) { "FAILED ($bad)" } else { 'ALL PASS' })$(if ($refuse.Count) { " ($($refuse.Count) refusal note(s): a real run now would refuse)" })"
    exit $(if ($bad) { 1 } else { 0 })
}

# --- real run ---
$postArgs = @('-B', $post, '--expect-fp', $nativeFp)
$rcAll = 0
$runStart = Get-Date; $armsDone = $false; $helpers = @()
function Stop-Ours {
    # S2: the run stopped early (error / Ctrl-C). Close OUR game: legodimensions whose exe is under $runsRoot and that
    # started after this run began (the same filter as holdwatch); the handle is taken first and the start time checked
    # again through it. Then the helpers this script started, by their held handles. Nothing else is touched.
    $ErrorActionPreference = 'Continue'
    foreach ($g in @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)) {
        try {
            if (-not ($g.Path -like "$runsRoot\*")) { continue }
            $null = $g.Handle
            if ($g.StartTime -lt $runStart.AddSeconds(-2)) { continue }
            Say "ABORT cleanup: closing our game pid $($g.Id) ($($g.Path))"
            $null = $g.CloseMainWindow()
            if (-not $g.WaitForExit(30000)) { Say "ABORT cleanup: game pid $($g.Id) still open after 30 s: kill"; $g.Kill(); $null = $g.WaitForExit(15000) }
            Say "ABORT cleanup: game pid $($g.Id) exited: $($g.HasExited)"
        } catch { Say "ABORT cleanup: game pid $($g.Id): $($_.Exception.Message)" }
    }
    foreach ($h in $script:helpers) {
        try { if ($h -and -not $h.HasExited) { Say "ABORT cleanup: stopping helper pid $($h.Id) (started by this script)"; $h.Kill(); $null = $h.WaitForExit(10000) } }
        catch { Say "ABORT cleanup: helper pid $($h.Id): $($_.Exception.Message)" }
    }
}
try {
foreach ($arm in $arms) {
    if (Test-Path -LiteralPath $hold) { Say "WINDOW-HOLD.txt appeared: arm $($arm.name) not started"; $rcAll = 3; break }
    $tr = Join-Path $kit "trace-$($arm.tr)-$stamp"
    $tag = "$tagBase-$($arm.name)"
    $base = Join-Path $kit "logs\$stamp-$($arm.name)"
    $x = Rg-Args $arm $runsRoot $tr $false
    $t0 = Get-Date
    $marker = "$base.hold-abort.txt"
    # holdwatch + sidecar share this console with redirected output (as build\agent3\toypad\explore.ps1): no extra windows
    # N2: holdwatch looks for the game for up to 300 s (run-game's bin mirror + launch can take > 150 s)
    $hp = Start-Process -FilePath 'powershell' -NoNewWindow -PassThru -RedirectStandardOutput "$base.holdwatch.out.txt" -RedirectStandardError "$base.holdwatch.err.txt" `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$hw`"", '-RunsRoot', "`"$runsRoot`"", '-NotBefore', $t0.ToString('o'), '-Marker', "`"$marker`"", '-FindTimeoutSec', '300')
    $null = $hp.Handle; $script:helpers = @($hp)
    $sp = Start-Process -FilePath $py -NoNewWindow -PassThru -RedirectStandardOutput "$base.sidecar.out.txt" -RedirectStandardError "$base.sidecar.err.txt" `
        -ArgumentList @((Sidecar-Args $arm $runsRoot $t0) | ForEach-Object { if ("$_" -match '\s') { "`"$_`"" } else { "$_" } })
    $null = $sp.Handle; $script:helpers += $sp
    $wp = $null
    if (-not $Manual) {   # manual: no marks, so no watcher (the session's screenshots are taken by hand)
        $wp = Start-Process -FilePath 'powershell' -WindowStyle Hidden -PassThru -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            "`"$watch`"", '-Arm', $arm.name, '-RunsRoot', "`"$runsRoot`"", '-Tag', $tag, '-OutDir', "`"$shots`"", '-Seconds', "$Seconds")
        $null = $wp.Handle; $script:helpers += $wp   # held handles: ExitCode stays readable and Kill() can't hit a reused PID
    }
    Say "arm $($arm.name): holdwatch pid $($hp.Id), sidecar pid $($sp.Id), watcher $(if ($wp) { "pid $($wp.Id)" } else { 'off (manual)' })"
    Say "Toypad ctl dir: <run>\toypad-ctl under $runsRoot (exact path: the ctl-dir line in $base.sidecar.out.txt)"
    Say "START $($arm.name): $(Cmd-Line $x)"
    $rc = Run-Logged 'powershell' $x
    if ($rc -ne 0) { $rcAll = 1 }
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$tag" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '' }
    Say "run-game ($($arm.name)) exit $rc, run $(if ($runDir) { $runDir } else { '?' }), $([int]((Get-Date) - $t0).TotalSeconds) s"
    foreach ($pp in @(@($sp, 'sidecar', 240), @($hp, 'holdwatch', 30), @($wp, 'watcher', 60))) {
        if (-not $pp[0]) { continue }
        if (-not $pp[0].WaitForExit($pp[2] * 1000)) { Say "$($pp[1]) $($pp[0].Id) still running after $($pp[2]) s: stopping it (started by this script)"; try { $pp[0].Kill() } catch { } }
        else { Say "$($pp[1]) exit $($pp[0].ExitCode)" }
    }
    $script:helpers = @()
    if (Test-Path -LiteralPath $marker) { Say "HOLD ABORT: WINDOW-HOLD.txt appeared during arm $($arm.name) (holdwatch stopped the game)"; $rcAll = 3 }
    if ($runDir) { $postArgs += @('--arm', "$($arm.name)=$runDir,$(if ($arm.trace) { $tr }),$shots") }
    if ($rcAll -eq 3) { break }
}
$armsDone = $true
} finally {
    if (-not $armsDone) { Say 'ABORTED (error or Ctrl-C) during an arm: cleanup of what this run started'; Stop-Ours }
}
if ($Manual) {   # no marks -> no post report; the run dir (game.log, toypad-events.csv, user\) is the record
    Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp manual exit=$rcAll runs=$runsRoot (no post)$(if ($Dump) { ' DIAGNOSTIC dump on, timing invalid' })" -Encoding ascii
    Say "GAMEPLAY MANUAL DONE: run-game $(if ($rcAll) { "exit code $rcAll" } else { 'exit 0' }); no post (manual session)"
    exit $rcAll
}
$postOut = Join-Path $kit "post\gameplay-$stamp.txt"
$postArgs += @('--out', $postOut)
$prc = Run-Logged $py $postArgs
$verdict = (Select-String -LiteralPath $postOut -Pattern '^RESULT: ' -ErrorAction SilentlyContinue | Select-Object -Last 1).Line
$sums = Join-Path $kit "post\SHA256SUMS-$stamp.txt"
$items = @(Get-Item -LiteralPath $postOut -ErrorAction SilentlyContinue)
if (Test-Path -LiteralPath $shots) { $items += Get-ChildItem -LiteralPath $shots -File }
$items | ForEach-Object { "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)  $($_.Length)  $($_.FullName.Substring($ws.Length + 1))" } | Set-Content -LiteralPath $sums -Encoding ascii
Set-Content -LiteralPath (Join-Path $kit 'LATEST.txt') -Value "$stamp $(if ($Explore) { 'explore' } else { 'route' })$(if ($Cand5) { ' cand5' }) exit=$rcAll post=$prc shots=$shots report=$postOut $verdict" -Encoding ascii
Say "GAMEPLAY DONE: run-game $(if ($rcAll) { "exit code $rcAll" } else { 'exit 0' }); post exit $prc; $verdict; shots $shots; report $postOut"
exit $(if ($rcAll -ne 0 -or $prc -ne 0) { $(if ($rcAll -eq 3) { 3 } else { 1 }) } else { 0 })
