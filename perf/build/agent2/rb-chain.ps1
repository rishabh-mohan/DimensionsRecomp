# Agent 2 (task #14, 03:45): the rollback builds rb1 / rb2 and nativeB end to end as ONE run_command background
# task, at Agent 1's GO only. Stops at the first failure; build/agent2/stop-snap.ps1 kills it (make-rb-clones.py adds
# rb-chain.ps1, prep-rb1/rb2/nb.py and run-rb1/rb2/nb.ps1 to its driver list).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\rb-chain.ps1 -Variant rb1|rb2|nb [-Jobs 10]
#       [-Resync | -SkipCopy] [-NoBuild]
# 0. Guards (nothing is written on a refusal): -Variant is rb1, rb2 or nb; -Resync and -SkipCopy exclude each other;
#    -Jobs 1..10 (exit 2 on any of these); no start 08:30-12:00, and for nb no start from 07:00 (exit 2); no other
#    snapshot driver, snap-patch.py apply or rb-chain.ps1 running (exit 4).
# 1. snap-patch.py verify <tag>: snap1 is still exactly its newest PATCHES tag (only S3 or S3d is accepted), so the
#    snapB3 copy is a recorded state. Console copy: rb-chain-<v>-verify.txt.
# 2. prep-<v>.py [--resync | --skip-copy]: its pinned install tree only, snap1 -> snapB3 copy, Agent 9's step 4
#    under snapB3, gen-check. Its notes tag line must name prep-<v>.py and the tag of step 1. Console copy:
#    rb-chain-<v>-prep.log.
# 3. run-<v>.ps1 -Jobs N [-NoBuild]: the pins again, configure, gen-check, gate, build, stage with its -CompareBin
#    (rb1/rb2: devoff3-bin; nb: native3d-bin at S3d, native3-bin at S3). Console copy: rb-chain-<v>-run.log.
# -GuardOnly (for rb-tools-test.ps1): step 0 only, then exit 0; nothing is written or run.
# Log: build/agent2/rb-chain-<v>.txt.
param([string]$Variant = '', [int]$Jobs = 10, [switch]$Resync, [switch]$SkipCopy, [switch]$NoBuild, [switch]$GuardOnly)
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$v = $Variant.Trim().ToLowerInvariant()
$outs = @{ 'rb1' = 'devoffRB1-bin'; 'rb2' = 'devoffRB2-bin'; 'nb' = 'nativeB-bin' }
# parameter refusals: console only, exit 2
if (-not $outs.ContainsKey($v)) { Write-Host "STOP: -Variant must be rb1, rb2 or nb (got '$Variant')"; exit 2 }
if ($Resync -and $SkipCopy) { Write-Host 'STOP: -Resync and -SkipCopy exclude each other'; exit 2 }
if ($Jobs -lt 1 -or $Jobs -gt 10) { Write-Host "STOP: -Jobs $Jobs is outside 1..10 (capped at 10, session-3 rule)"; exit 2 }
$tod = (Get-Date).TimeOfDay
if ($tod -ge [TimeSpan]'08:30:00' -and $tod -lt [TimeSpan]'12:00:00') { Write-Host 'STOP: no builds from 08:30 (session-3 rule)'; exit 2 }
if ($v -eq 'nb' -and $tod -ge [TimeSpan]'07:00:00' -and $tod -lt [TimeSpan]'12:00:00') { Write-Host 'STOP: nativeB does not start after 07:00 (Agent 1)'; exit 2 }
$prep = "$A\prep-$v.py"; $run = "$A\run-$v.ps1"; $out = $outs[$v]
foreach ($f in $prep, $run) { if (-not (Test-Path -LiteralPath $f)) { Write-Host "STOP: $f is missing"; exit 2 } }
# other drivers: every process but this one and its ancestors (the shell that started this one names rb-chain.ps1)
$procs = @(Get-CimInstance Win32_Process)
$byId = @{}; foreach ($p in $procs) { $byId[[int]$p.ProcessId] = $p }
$mine = @{}; $id = [int]$PID
for ($i = 0; $i -lt 16 -and $byId.ContainsKey($id) -and -not $mine.ContainsKey($id); $i++) { $mine[$id] = 1; $id = [int]$byId[$id].ParentProcessId }
$pat = 'rb-chain\.ps1|\bb-chain\.ps1|run-b\.ps1|prep-b\.py|run-s2\.ps1|run-s3\.ps1|run-s3d\.ps1|run-rb\d\.ps1|prep-rb\d\.py|run-nb\.ps1|prep-nb\.py|build-snap\.ps1|stage-snap-bin\.ps1|snap-patch\.py\s+apply'
$drv = @($procs | Where-Object { -not $mine.ContainsKey([int]$_.ProcessId) -and $_.CommandLine -match $pat })
if ($drv.Count) { Write-Host "STOP: another snapshot driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))"; exit 4 }
if ($GuardOnly) { Write-Host "GUARD OK: -Variant $v -Jobs $Jobs, no other snapshot driver ($($mine.Count) own/ancestor processes skipped); nothing run"; exit 0 }
$log = "$A\rb-chain-$v.txt"
function Log([string]$m) { $l = "$(Get-Date -Format HH:mm:ss) [rb-chain $v] $m"; $l | Out-File -Append -Encoding utf8 $log; Write-Host $l }
function Tail([string]$p, [int]$n) { (@(Get-Content -LiteralPath $p -ErrorAction SilentlyContinue) | Select-Object -Last $n) -join ' | ' }
$t0 = [Diagnostics.Stopwatch]::StartNew()
Set-Location $R
$pa = $(if ($Resync) { ' --resync' } elseif ($SkipCopy) { ' --skip-copy' } else { '' })
$ra = " -Jobs $Jobs" + $(if ($NoBuild) { ' -NoBuild' } else { '' })
Log "START $v chain: verify snap1 -> prep-$v.py$pa -> run-$v.ps1$ra -> $out (free C $('{0:N1}' -f ((Get-PSDrive C).Free / 1GB)) GB)"
# 1. snap1 == its newest tag (S3 < S3d)
$tags = @(Get-ChildItem -LiteralPath "$A\snap1" -Filter 'PATCHES-S*.tsv' | ForEach-Object {
        if ($_.Name -match '^PATCHES-S(\d+)([a-z]*)\.tsv$') { [pscustomobject]@{ Tag = "S$($Matches[1])$($Matches[2])"; N = [int]$Matches[1]; Sfx = $Matches[2] } } } |
    Sort-Object N, Sfx)
if (-not $tags.Count) { Log 'STOP: no PATCHES-S*.tsv in snap1'; exit 20 }
$tag = $tags[-1].Tag
if ($tag -notin 'S3', 'S3d') { Log "STOP: snap1's newest tag is $tag; only S3 or S3d is accepted (ask Agent 1)"; exit 20 }
$o = "$A\rb-chain-$v-verify.txt"
$sw = [Diagnostics.Stopwatch]::StartNew()
& cmd /d /c "python $A\snap-patch.py verify $tag > $o 2>&1"
$c = $LASTEXITCODE
$pass = (@(Get-Content -LiteralPath $o) | ForEach-Object { $_.Trim() }) -contains 'RESULT: PASS'
Log ("verify {0}: exit {1}, {2:N1}s: {3}" -f $tag, $c, $sw.Elapsed.TotalSeconds, (Tail $o 2))
if ($c -ne 0 -or -not $pass) { Log "STOP: snap1 is not exactly $tag (see rb-chain-$v-verify.txt)"; exit 20 }
# 2. prep-<v>.py
$o = "$A\rb-chain-$v-prep.log"
$sw = [Diagnostics.Stopwatch]::StartNew()
& cmd /d /c "python $prep$pa > $o 2>&1"
$c = $LASTEXITCODE
Log ("prep-{0}.py{1}: exit {2}, {3:N1}s: {4}" -f $v, $pa, $c, $sw.Elapsed.TotalSeconds, (Tail $o 2))
if ($c -ne 0 -or (Tail $o 1) -notmatch 'DONE prep-') { Log "STOP: prep-$v.py failed (see rb-chain-$v-prep.log)"; exit 21 }
$tl = @(Select-String -LiteralPath "$A\snapB3-manifest-notes.txt" -Pattern "^snapB3 = build/agent2/snap1/DimensionsRecomp at (S\d+[a-z]*), copied by prep-$v\.py ")
if ($tl.Count -ne 1 -or $tl[0].Matches[0].Groups[1].Value -ne $tag) { Log "STOP: snapB3-manifest-notes.txt does not name prep-$v.py at $tag"; exit 21 }
Log "snapB3 = snap1 at $tag, prepared by prep-$v.py"
# 3. run-<v>.ps1
$o = "$A\rb-chain-$v-run.log"
$sw = [Diagnostics.Stopwatch]::StartNew()
& cmd /d /c "powershell -NoProfile -ExecutionPolicy Bypass -File $run$ra > $o 2>&1"
$c = $LASTEXITCODE
Log ("run-{0}.ps1{1}: exit {2}, {3:N1}s: {4}" -f $v, $ra, $c, $sw.Elapsed.TotalSeconds, (Tail $o 3))
if ($c -ne 0) { Log "STOP: run-$v.ps1 exit $c (see rb-chain-$v-run.log and the run script's own log)"; exit 22 }
if ($NoBuild) { Log ("DONE {0} chain -NoBuild (configure, gen-check, gate), total wall {1:N1}s" -f $v, $t0.Elapsed.TotalSeconds); exit 0 }
foreach ($f in 'legodimensions.exe', 'legodimensions.map', 'rexruntime.dll', 'rexgpu-xenos.dll', 'MANIFEST.txt') {
    $p = "$A\$out\$f"
    if (Test-Path -LiteralPath $p) { Log ("{0}\{1}: {2} B sha256 {3}" -f $out, $f, (Get-Item -LiteralPath $p).Length, (Get-FileHash -LiteralPath $p).Hash) }
    elseif ($f -ne 'rexgpu-xenos.dll' -or $v -eq 'nb') { Log "$out\$f is missing" }
}
Log ("DONE {0} chain -> {1}, total wall {2:N1}s, free C {3:N1} GB" -f $v, $out, $t0.Elapsed.TotalSeconds, ((Get-PSDrive C).Free / 1GB))
exit 0
