# Agent 2 - B4 builds (board run 2): devoffB4 + nativeB4 = the B line + S4a. Agent 9's batch-nolr codegen (pins
# SHA256SUMS.txt 24CE1493..., config.toml E60EAF1C...; the codegen-frozen2.exe stand-in writes nothing) + the S4a
# sources (#2 native only), linked against build/agent2/snap1-sdk/install = the S4a SDK (no SDK build). Plan:
# perf-notes/agent2-baseline.md, "Task #15" section 2 (option B for devoffB4). Needs prep-b4.py --go first (it copies
# the snap1 files into snapB / snapB3 with mtime = now and writes B4-copies-<variant>.tsv and
# B4-manifest-notes-<variant>.txt). Run as a run_command background task, alone (the driver guard reads every process
# command line); build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-b4.ps1 [-Variant off|native|both] [-Jobs 10]
#       [-DryRun] [-NoBuild] [-Configure] [-NotBefore 16:00]
# off   : build-snap.ps1 -Phase game -Tag snapB4o -SnapDir snapB\DimensionsRecomp -GameDir snapB-off (incremental;
#         -SkipConfigure unless -Configure) -> stage-snap-bin.ps1 -Variant off -> build/agent2/devoffB4-bin,
#         -CompareBin devoff4-bin
# native: build-snap.ps1 -Phase game -Native -Tag snapB4n -SnapDir snapB3\DimensionsRecomp -GameDir snapB3-on (with
#         the configure, as run-nb.ps1 and the S4a native build) -> stage-snap-bin.ps1 -Variant native ->
#         build/agent2/nativeB4-bin, -CompareBin native4-bin
# both  : off, then native (the S4a order). Default.
# Guards, all before anything builds (-DryRun: all reported, nothing built or written but this log): no start before
# -NotBefore (Agent 1, 15:35: builds resume at 16:00), -Jobs capped at 10, no other snapshot build driver and no
# ninja/clang/cmake process; batch-nolr is a real folder whose SHA256SUMS.txt is the pin; the tree's config.toml is
# the pin; install/bin rexruntime.dll, rexgpu-xenos.dll and TracyClient.dll == the -CompareBin files (the S4a SDK: B4
# runs before any S4b SDK build) and the -CompareBin MANIFEST.txt is the pinned one; the prep record exists with the
# planned row count and every copied file still == its after; the notes file exists; the out folder is not staged;
# native: snapB3\rexlego\out\native-gpu exists; the game-tree exe has exactly 1 link.
# After the build: rexruntime.dll in the game tree == install/bin (relink contingency as run-s4a.ps1: rename exe + map
# to *.pre-B4, rebuild with tag <tag>r). stage-snap-bin.ps1 gets -SnapTag S4a -PatchTagList S1,S2,S3,S3d,S4a
# -GameSnap <tree> -CompareBin <S4a bin> + the S4a strings: every staged file but the exe and map must equal the S4a
# bin's and the exe must differ (default -CompareWhy: the generated code changed); checked again here.
# Log: build/agent2/snapB4-run.txt (+ build-snap's <tag>-steps.txt and <tag>-*.log, and <tag>-stage.log).
param([ValidateSet('off', 'native', 'both')][string]$Variant = 'both', [int]$Jobs = 10, [switch]$DryRun,
    [switch]$NoBuild, [switch]$Configure, [string]$NotBefore = '16:00')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$runLog = "$A\snapB4-run.txt"
$nolr = "$R\build\agent9\install\batch-nolr"
$I = "$A\snap1-sdk\install\bin"
$script:V = '-'
# the S4a literals (run-s4a.ps1): rexruntime.dll (S3's #22 + xmemory.cpp, timer_queue.cpp), rexgpu-xenos.dll (both
# shared_memory.cpp), the exe (S3's pause_safe_order description tail; native: the 4 native toggles incl. #2)
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach,physical_protect_hold_global_lock,timer_queue_precise_wait'
$xeStrings = 'shared_memory_upload_hash_log,shared_memory_single_hold_rearm'
# no apostrophes in values passed through powershell -File
$cfg = @{
    off    = @{ Tree = 'snapB'; Game = 'snapB-off'; Tag = 'snapB4o'; Out = 'devoffB4-bin'; Compare = 'devoff4-bin'; Man = '16DCC939'; N = 35
        Exe = 'which can hang when the guest pauses'
        What = 'devoffB4: dev OFF build of the B line + S4a (snapB brought to the S4a level by prep-b4.py: Agent 9 batch-nolr codegen + the S3d rexlego sources + SDK #7 #8 #5(i) #38 with every new switch OFF + #32 always on): NATIVE_GPU=OFF' }
    native = @{ Tree = 'snapB3'; Game = 'snapB3-on'; Tag = 'snapB4n'; Out = 'nativeB4-bin'; Compare = 'native4-bin'; Man = '00D33D4F'; N = 6
        Exe = 'which can hang when the guest pauses,LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD,LEGO_NATIVE_FPS_CELL_RECTS,LEGO_NATIVE_TEXTURE_STAGING_POOL,LEGO_NATIVE_SHADER_MISS_CACHE'
        What = 'nativeB4: native build of the B line + S4a (snapB3 + the 6 S4a files: Agent 9 batch-nolr codegen + S3d + SDK #7 #8 #5(i) #38 with every new switch OFF + #32 always on + #2 miss cache, OFF by default): NATIVE_GPU=ON with Agent 6 AOT inputs' }
}
function Log([string]$m) {
    $line = "$(Get-Date -Format HH:mm:ss) [B4 $script:V] $m"
    $line | Out-File -Append -Encoding utf8 $runLog
    Write-Host $line
}
function Run([string]$what, [string[]]$argv, [string]$out) {
    # powershell -File <argv>: the exit code is the script's exit code (1 on an unhandled error)
    Log "BEGIN $what : $($argv -join ' ')"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    if ($out) { & powershell -NoProfile -ExecutionPolicy Bypass -File @argv > $out 2>&1 }
    else { & powershell -NoProfile -ExecutionPolicy Bypass -File @argv | Out-Null }
    $code = $LASTEXITCODE
    Log ("END   $what exit=$code wall={0:N1}s freeC={1:N2}GB" -f $sw.Elapsed.TotalSeconds, ((Get-PSDrive C).Free / 1GB))
    return $code
}
function Sha([string]$p) { if (Test-Path -LiteralPath $p -PathType Leaf) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash } else { 'MISSING' } }
function Pfx([string]$h) { $h.Substring(0, [Math]::Min(16, $h.Length)) }
$probs = New-Object System.Collections.Generic.List[string]
function Bad([string]$m) { $probs.Add($m); Log "  BAD  $m" }
function Ok([string]$m) { Log "  ok   $m" }
function BuildArgs([string]$v, [string]$tag, [bool]$skipCfg) {
    $c = $cfg[$v]
    $a = @("$A\build-snap.ps1", '-Phase', 'game')
    if ($v -eq 'native') { $a += '-Native' }
    $a += @('-Tag', $tag, '-Jobs', "$Jobs", '-KeepGoing', '-SnapDir', "$A\$($c.Tree)\DimensionsRecomp", '-GameDir', "$A\$($c.Game)",
        '-CodegenExe', "$A\codegen-frozen\codegen-frozen2.exe", '-GenBase', "$nolr\generated")
    if ($v -eq 'native') { $a += @('-PrelinkJobs', "$Jobs") }
    if ($skipCfg) { $a += '-SkipConfigure' }
    if ($NoBuild) { $a += '-NoBuild' }
    return , $a
}
function StageArgs([string]$v, [string]$bt) {
    $c = $cfg[$v]
    $cg = "codegen: Agent 9 batch-nolr options (build/agent9/install/batch-nolr, 430 TUs, no skip_lr; the $($c.Tree) generated output hash-checked against that install tree by gen-check.py --base; the codegen-frozen2.exe stand-in writes nothing)"
    return , @("$A\stage-snap-bin.ps1", '-Variant', $v, '-SnapTag', 'S4a', '-BuildTag', $bt, '-GameTree', "$A\$($c.Game)",
        '-OutDir', "$A\$($c.Out)", '-GameSnap', "$A\$($c.Tree)\DimensionsRecomp", '-CompareBin', "$A\$($c.Compare)",
        '-PatchTagList', 'S1,S2,S3,S3d,S4a', '-RuntimeStrings', $rtStrings, '-XenosStrings', $xeStrings, '-ExeStrings', $c.Exe,
        '-WhatText', $c.What, '-CodegenNote', $cg, '-ManifestNotesFile', "$A\B4-manifest-notes-$v.txt")
}

$vars = $(if ($Variant -eq 'both') { @('off', 'native') } else { @($Variant) })
if ($Jobs -gt 10) { $Jobs = 10 }
Log "START run-b4.ps1 -Variant $Variant ($($vars -join ', then ')), -j $Jobs$(if ($DryRun) { '; -DryRun: guards only, nothing is built' })"
# ---- guards
$tod = (Get-Date).TimeOfDay
if ($tod -lt [TimeSpan]::Parse($NotBefore + ':00')) {
    if ($DryRun) { Log "  note it is before $NotBefore : a real run would stop here (Agent 1: builds resume at 16:00)" }
    else { Bad "no build starts before $NotBefore (Agent 1, 15:35: builds resume at 16:00)" }
} else { Ok "time $(Get-Date -Format HH:mm) is not before $NotBefore" }
$drv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'run-b\.ps1|\bb-chain\.ps1|rb-chain\.ps1|run-(s2|s3|s3d|s3e|nb|rb1|rb2|s4a|s4b)\.ps1|prep-(s4a|s4b|b4)\.py|build-snap\.ps1|stage-snap-bin\.ps1' })
if ($drv.Count) { Bad "another snapshot build driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))" } else { Ok 'no other snapshot build driver' }
$bp = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(ninja|clang.*|lld-link|ld\.lld|cmake)$' })
if ($bp.Count) { Bad "build processes running: $(($bp | ForEach-Object { "$($_.ProcessName)($($_.Id))" }) -join ', ')" } else { Ok 'no ninja/clang/cmake process' }
$gp = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'legodimensions*' })
if ($gp.Count) { Log "  note a game process runs ($(($gp | ForEach-Object { "$($_.ProcessName)($($_.Id))" }) -join ', ')): builds are not blocked by it, but check with Agent 1 that no timing run is on" }
$it = Get-Item -LiteralPath $nolr -Force -ErrorAction SilentlyContinue
if (-not $it -or $it.LinkType) { Bad "$nolr is missing or a link" }
else {
    $sumsSha = Sha "$nolr\SHA256SUMS.txt"
    if ($sumsSha -ne '24CE1493FB8DAE37E00B556EB8871D633921E44378D960DE4359B104B16CDB8E') { Bad "batch-nolr SHA256SUMS.txt is $(Pfx $sumsSha), not the pinned 24CE1493..." }
    else { Ok "batch-nolr is a real folder, SHA256SUMS.txt $(Pfx $sumsSha) (pin)" }
}
foreach ($v in $vars) {
    $script:V = $v; $c = $cfg[$v]
    $tree = "$A\$($c.Tree)\DimensionsRecomp"
    $cfgSha = Sha "$tree\rexlego\legodimensions_config.toml"
    if ($cfgSha -ne 'E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090') { Bad "$($c.Tree) legodimensions_config.toml is $(Pfx $cfgSha), not the pinned E60EAF1C..." }
    else { Ok "$($c.Tree) legodimensions_config.toml $(Pfx $cfgSha) (pin)" }
    $cmp = "$A\$($c.Compare)"
    $mh = Sha "$cmp\MANIFEST.txt"
    if (-not $mh.StartsWith($c.Man)) { Bad "$($c.Compare)\MANIFEST.txt is $(Pfx $mh), not $($c.Man)" } else { Ok "$($c.Compare) MANIFEST.txt $(Pfx $mh) (pin)" }
    foreach ($d in 'rexruntime.dll', 'rexgpu-xenos.dll', 'TracyClient.dll') {
        $hi = Sha "$I\$d"; $hc = Sha "$cmp\$d"
        if ($hi -ne $hc) { Bad "install/bin/$d ($(Pfx $hi)) != $($c.Compare)\$d ($(Pfx $hc)): the install is no longer the S4a SDK" }
        else { Ok "install/bin/$d == $($c.Compare)\$d ($(Pfx $hi))" }
    }
    if (Test-Path -LiteralPath "$A\$($c.Out)\MANIFEST.txt") { Bad "$($c.Out) is already staged (MANIFEST.txt exists)" } else { Ok "$($c.Out) not staged yet" }
    $rec = "$A\B4-copies-$v.tsv"; $notes = "$A\B4-manifest-notes-$v.txt"
    if (-not (Test-Path -LiteralPath $rec)) {
        if ($DryRun) { Log "  wait $(Split-Path -Leaf $rec) missing: prep-b4.py --go writes it" } else { Bad "$(Split-Path -Leaf $rec) missing: run prep-b4.py --go first" }
    } else {
        $rows = @(Get-Content -Encoding UTF8 -LiteralPath $rec | Where-Object { $_ -and -not $_.StartsWith('#') })
        $nbad = 0
        foreach ($row in $rows) {
            $x = @($row -split "`t")
            $h = Sha ("$tree\" + $x[0].Replace('/', '\'))
            if ($h -ne $x[2]) { $nbad++; Bad "$($c.Tree) $($x[0]) is $(Pfx $h), not its after $(Pfx $x[2])" }
        }
        if ($rows.Count -ne $c.N) { Bad "$(Split-Path -Leaf $rec) has $($rows.Count) rows, not $($c.N)" }
        elseif (-not $nbad) { Ok "$(Split-Path -Leaf $rec): $($rows.Count) copies, each still == its after" }
    }
    if (-not (Test-Path -LiteralPath $notes)) {
        if ($DryRun) { Log "  wait $(Split-Path -Leaf $notes) missing: prep-b4.py --go writes it" } else { Bad "$(Split-Path -Leaf $notes) missing" }
    } else { Ok "$(Split-Path -Leaf $notes) present ($((Get-Item -LiteralPath $notes).Length) B)" }
    if ($v -eq 'native') {
        if (-not (Test-Path -LiteralPath "$tree\rexlego\out\native-gpu")) { Bad "$tree\rexlego\out\native-gpu is missing" } else { Ok 'snapB3\rexlego\out\native-gpu present' }
    }
    $exe = "$A\$($c.Game)\legodimensions.exe"
    $nl = "$(& python -c 'import os,sys;print(os.stat(sys.argv[1]).st_nlink)' $exe 2>$null)".Trim()
    if ($nl -ne '1') { Bad "$($c.Game)\legodimensions.exe has $nl link(s), must be 1" } else { Ok "$($c.Game)\legodimensions.exe has 1 link" }
    $ba = BuildArgs $v $c.Tag ($v -eq 'off' -and -not $Configure)
    Log "  plan build: $($ba -join ' ')"
    $sa = StageArgs $v $c.Tag
    Log "  plan stage: $($sa -join ' ')"
}
$script:V = '-'
if ($DryRun) {
    Log "DRY RUN: $($probs.Count) problem(s)$(if ($probs.Count) { ': ' + ($probs -join ' | ') } else { '; ready once prep-b4.py --go has run' })"
    exit $(if ($probs.Count) { 1 } else { 0 })
}
if ($probs.Count) { Log "STOP: $($probs.Count) guard(s) failed; nothing built"; exit 4 }

# ---- builds
$t0 = [Diagnostics.Stopwatch]::StartNew()
foreach ($v in $vars) {
    $script:V = $v; $c = $cfg[$v]
    $game = "$A\$($c.Game)"; $tag = $c.Tag; $O = "$A\$($c.Out)"; $cmp = "$A\$($c.Compare)"
    $tv = [Diagnostics.Stopwatch]::StartNew()
    Log "START $v -> $($c.Out) (source $($c.Tree), game tree $($c.Game), tag $tag, -j $Jobs)"
    $code = Run 'build' (BuildArgs $v $tag ($v -eq 'off' -and -not $Configure)) ''
    if ($code -ne 0) { Log "STOP: build-snap.ps1 exit $code (see $tag-steps.txt)"; exit 10 }
    if ($NoBuild) { Log "$v -NoBuild done (configure, gen-check, gate)"; continue }
    $bt = $tag
    $h2 = Sha "$I\rexruntime.dll"; $h1 = Sha "$game\rexruntime.dll"
    if ($h1 -ne $h2) {
        Log "rexruntime.dll in $($c.Game) ($(Pfx $h1)) != install/bin ($(Pfx $h2)): the exe did not relink; renaming exe + map to *.pre-B4, relinking"
        foreach ($f in 'legodimensions.exe', 'legodimensions.map') {
            $p = "$game\$f"; $dst = "$p.pre-B4"
            if (Test-Path -LiteralPath $dst) { $dst = "$dst-$(Get-Date -Format HHmmss)" }
            if (Test-Path -LiteralPath $p) { Rename-Item -LiteralPath $p -NewName (Split-Path -Leaf $dst); Log "  renamed $f -> $(Split-Path -Leaf $dst)" }
        }
        $code = Run 'relink' (BuildArgs $v "${tag}r" $true) ''
        if ($code -ne 0) { Log "STOP: relink build-snap.ps1 exit $code (see ${tag}r-steps.txt)"; exit 11 }
        $bt = "${tag}r"
        $h1 = Sha "$game\rexruntime.dll"
        if ($h1 -ne $h2) { Log "STOP: rexruntime.dll in $($c.Game) still differs from install/bin after the relink"; exit 12 }
    }
    Log "rexruntime.dll in $($c.Game) == install/bin ($(Pfx $h2))"
    $stLog = "$A\$tag-stage.log"
    $code = Run 'stage' (StageArgs $v $bt) $stLog
    foreach ($l in @(Get-Content $stLog | Where-Object { $_ -match [regex]::Escape($c.Compare) })) { Log "  $l" }
    foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
    if ($code -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $code (see $(Split-Path -Leaf $stLog))"; exit 13 }
    $bad = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $O -File | Where-Object { $_.Name -ne 'MANIFEST.txt' } | Sort-Object Name)) {
        $h = Sha $f.FullName; $rp = Join-Path $cmp $f.Name
        $same = (Test-Path -LiteralPath $rp) -and ((Sha $rp) -eq $h)
        $txt = $(if ($same) { "== $($c.Compare)" } else { "differs from $($c.Compare)" })
        if ($f.Name -eq 'legodimensions.exe') { if ($same) { $txt += ' : FAIL, the generated code differs'; $bad++ } }
        elseif ($f.Name -ne 'legodimensions.map' -and -not $same) { $txt += ' : FAIL, same SDK and sources'; $bad++ }
        Log ("  staged {0}: {1} B, sha256 {2}; {3}" -f $f.Name, $f.Length, $h, $txt)
    }
    Log ("  staged MANIFEST.txt: {0} B, sha256 {1}" -f (Get-Item -LiteralPath "$O\MANIFEST.txt").Length, (Sha "$O\MANIFEST.txt"))
    $man = @(Get-Content -Encoding UTF8 -LiteralPath "$O\MANIFEST.txt")
    $cnt = @(foreach ($t in 'S1', 'S2', 'S3', 'S3d', 'S4a') { "$t $(@($man | Where-Object { $_.StartsWith("#   $t ") }).Count)" })
    $np = @($man | Where-Object { $_.StartsWith('#   PASS ') }).Count; $nf = @($man | Where-Object { $_.StartsWith('#   FAIL ') }).Count
    $nn = @($man | Where-Object { $_.StartsWith('#   NOTE ') }).Count
    Log "  MANIFEST patch rows: $($cnt -join ' / '); checks: $np PASS / $nf FAIL / $nn NOTE"
    foreach ($l in @($man | Where-Object { $_ -match "contains '(shared_memory_upload_hash_log|shared_memory_single_hold_rearm|physical_protect_hold_global_lock|timer_queue_precise_wait|LEGO_NATIVE_SHADER_MISS_CACHE|which can hang when the guest pauses)'" })) { Log "  $($l.Trim())" }
    if ($v -eq 'native') { Log "  native GPU fingerprint: $((Get-Content "$game\native-gpu-build.txt" -Raw).Trim())" }
    if ($bad) { Log "STOP: $bad staged file(s) not as expected against $($c.Compare)"; exit 15 }
    Log ("DONE $v -> $($c.Out), wall {0:N1}s" -f $tv.Elapsed.TotalSeconds)
}
$script:V = '-'
Log ("DONE run-b4.ps1 -Variant $Variant, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0
