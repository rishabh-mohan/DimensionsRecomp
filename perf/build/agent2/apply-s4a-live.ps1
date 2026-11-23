# Agent 2 - task #15 (board run 2): live apply of S4a, for Agent 1 to run after W4b.
# Copies the 6 S4a files from the snapshot build\agent2\snap1 (at S4a; the tree behind devoff4-bin and native4-bin)
# over the live files, byte for byte: 5 SDK files under DimensionsRecomp\rexglue-sdk (the SDK repo) and
# rexlego\src\gpu_native\shaders.cpp (the game repo). No git commands at all (Agent 1 commits).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\apply-s4a-live.ps1           # dry run, read-only
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\apply-s4a-live.ps1 -Go       # apply
#   ... -Go -Resume   also accept files that already equal "after" (a re-run after a partial apply); they are skipped
# Dry run (default): writes nothing. For each file it prints the live sha256, the expected before and after, the snap1
#   source sha256, and PASS (live == before) / DONE (live == after, already applied) / FAIL (anything else). It also
#   lists any running game, ninja or clang process.
# -Go refuses (exit 2) unless every file is PASS (or DONE, with -Resume) and every snap1 source == after; and refuses
#   (exit 3) while any game, ninja or clang process runs (process names legodimensions*, ninja, clang*, lld-link,
#   ld.lld, cmake). Then it backs up every live file to build\agent2\live-backup-S4a-<yyyyMMdd-HHmmss>\DimensionsRecomp\
#   <rel> (each backup re-hashed == before), writes the snap1 bytes over each live file ([IO.File]::WriteAllBytes, so
#   the mtime is now and ninja rebuilds) and re-hashes it: it must equal after. On any error or mismatch it writes
#   every touched file back from its backup, re-checks before, and exits 4. Log: build\agent2\apply-s4a-live-<stamp>.txt.
# Exit: 0 = dry run with 6/6 PASS, or -Go done; 1 = dry run not all PASS; 2, 3, 4 = -Go refused / rolled back.
param([switch]$Go, [switch]$Resume)
$ErrorActionPreference = 'Stop'
$R = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent     # build\agent2 -> build -> R
$live = Join-Path $R 'DimensionsRecomp'
$snap = Join-Path $R 'build\agent2\snap1\DimensionsRecomp'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logFile = $null
function Out([string]$m) {
    Write-Host $m
    if ($logFile) { $m | Out-File -Append -Encoding utf8 $logFile }
}
# item, relpath under DimensionsRecomp/, before sha256, before size, after sha256, after size (build/agent2/s4a/HASHES.txt,
# snap1/PATCHES-S4a.tsv; Agent 10 re-derived every row: ALL PASS)
$files = @(
    @('#7 u diag (A12)', 'rexglue-sdk/src/graphics/d3d12/shared_memory.cpp',
      'B120D07C6709D0D2A7836B532ED06B2032A418CBD4A71808CD318C7E6EB6CFBC', 14514,
      'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587', 20888),
    @('#8 P2 (A12)', 'rexglue-sdk/src/graphics/shared_memory.cpp',
      '15C89EDB4B197C17487A9D45208D5CE624DE98ABE416F86942C5D14ED43EB282', 24698,
      '0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4', 26439),
    @('#5 fix (i) (A12)', 'rexglue-sdk/src/system/xmemory.cpp',
      '6E8FA1BA80EF9271D4433DD1BB2CAD0403360E222B22CED78AA4C7951D811DB4', 107670,
      '141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A', 108907),
    @('#38 precise wait (A11)', 'rexglue-sdk/src/core/timer_queue.cpp',
      'D8724B29C43286B0E7D7614C713154E3694EE96827ED847701AD6CC1A876D9EC', 12839,
      '015C04A22DACC592B8DA0F5BB395353A4DD813E1F847775B584CB974F6E98846', 16091),
    @('#32 warm boot, always on', 'rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp',
      '5DBED81F611E25B17EBBE7FE2779ED5540FD94651F2D29A631D1C8AB74AE5213', 161305,
      'DA77744302CFC1496F46CF9177D16FEBE4716A34C8086AC71B63970072841708', 161303),
    @('#2 miss cache (A4)', 'rexlego/src/gpu_native/shaders.cpp',
      'E87A2DEE43D38D8EBBEE8EFD663DE70A293F7826B5AC0231B8B8A08E6A7E916D', 41029,
      '9567FE3F3B63637D9595D6B74B72567E1CAEA2D1A071E872D12660DFB37E1EFA', 51261)
)
function Sha([string]$p) { if (Test-Path -LiteralPath $p -PathType Leaf) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash } else { 'MISSING' } }
function Size([string]$p) { if (Test-Path -LiteralPath $p -PathType Leaf) { (Get-Item -LiteralPath $p).Length } else { -1 } }

if ($Go) {
    $logFile = Join-Path $R "build\agent2\apply-s4a-live-$stamp.txt"
}
Out "apply-s4a-live.ps1 $(if ($Go) { '-Go' } else { 'dry run (read-only)' })$(if ($Resume) { ' -Resume' }) at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Out "  live  : $live"
Out "  source: $snap (snap1 at S4a)"
if (-not (Test-Path -LiteralPath $live -PathType Container) -or -not (Test-Path -LiteralPath $snap -PathType Container)) {
    Out 'FAIL: live or snap1 DimensionsRecomp folder not found'; exit 2
}
$rows = @(); $i = 0
foreach ($f in $files) {
    $i++
    $item, $rel, $before, $bsize, $after, $asize = $f
    $lp = Join-Path $live ($rel -replace '/', '\'); $sp = Join-Path $snap ($rel -replace '/', '\')
    $lh = Sha $lp; $ls = Size $lp; $sh = Sha $sp; $ss = Size $sp
    $repo = if ($rel -like 'rexglue-sdk/*') { 'SDK repo DimensionsRecomp/rexglue-sdk' } else { 'game repo DimensionsRecomp' }
    $status = if ($lh -eq $before) { 'PASS' } elseif ($lh -eq $after) { 'DONE' } else { 'FAIL' }
    $srcOk = ($sh -eq $after)
    Out ''
    Out "[$i/6] $item  $rel  ($repo)"
    Out ("      live   {0}  {1,7} B" -f $lh, $ls)
    Out ("      before {0}  {1,7} B" -f $before, $bsize)
    Out ("      after  {0}  {1,7} B" -f $after, $asize)
    Out ("      snap1  {0}  {1,7} B  {2}" -f $sh, $ss, $(if ($srcOk) { '== after' } else { 'FAIL: != after' }))
    switch ($status) {
        'PASS' { Out '      PASS: live == before' }
        'DONE' { Out '      DONE: live == after (already applied)' }
        default { Out '      FAIL: live is neither before nor after' }
    }
    $rows += [pscustomobject]@{ Item = $item; Rel = $rel; Live = $lp; Src = $sp; Before = $before; After = $after; Status = $status; SrcOk = $srcOk }
}
$procs = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(legodimensions.*|ninja|clang.*|lld-link|ld\.lld|cmake)$' })
$nPass = @($rows | Where-Object Status -eq 'PASS').Count
$nDone = @($rows | Where-Object Status -eq 'DONE').Count
$nFail = @($rows | Where-Object Status -eq 'FAIL').Count
$nSrcBad = @($rows | Where-Object { -not $_.SrcOk }).Count
Out ''
Out "Summary: $nPass PASS, $nDone DONE, $nFail FAIL; snap1 sources == after: $(6 - $nSrcBad)/6"
if ($procs.Count) {
    Out "Running game/ninja/clang processes ($($procs.Count)): $(($procs | ForEach-Object { "$($_.ProcessName)($($_.Id))" }) -join ', ')"
} else { Out 'Running game/ninja/clang processes: none' }

if (-not $Go) {
    if ($nPass -eq 6 -and $nSrcBad -eq 0) {
        Out "Dry run: READY. -Go would back up and overwrite these 6 live files$(if ($procs.Count) { ', but only once the processes above have ended' })."
        exit 0
    }
    Out 'Dry run: NOT READY for -Go (see the FAIL/DONE lines above).'
    exit 1
}

# -Go
$okStatus = if ($Resume) { @('PASS', 'DONE') } else { @('PASS') }
$bad = @($rows | Where-Object { $okStatus -notcontains $_.Status })
if ($bad.Count -or $nSrcBad) {
    Out "REFUSED (exit 2): $($bad.Count) file(s) not $($okStatus -join '/'), $nSrcBad snap1 source(s) != after. Nothing written."
    exit 2
}
if ($procs.Count) {
    Out 'REFUSED (exit 3): a game, ninja or clang process is running. Nothing written.'
    exit 3
}
$todo = @($rows | Where-Object Status -eq 'PASS')
if (-not $todo.Count) { Out 'Nothing to do: every file already == after.'; exit 0 }
$bk = Join-Path $R "build\agent2\live-backup-S4a-$stamp\DimensionsRecomp"
$touched = @()
try {
    foreach ($r in $todo) {
        $b = Join-Path $bk ($r.Rel -replace '/', '\')
        New-Item -ItemType Directory -Force -Path (Split-Path $b -Parent) | Out-Null
        [IO.File]::WriteAllBytes($b, [IO.File]::ReadAllBytes($r.Live))
        if ((Sha $b) -ne $r.Before) { throw "backup of $($r.Rel) != before" }
    }
    Out "Backups: $bk ($($todo.Count) files, each == before)"
    foreach ($r in $todo) {
        $bytes = [IO.File]::ReadAllBytes($r.Src)
        $touched += $r
        [IO.File]::WriteAllBytes($r.Live, $bytes)
        $h = Sha $r.Live
        if ($h -ne $r.After) { throw "$($r.Rel): live after copy $h != after $($r.After)" }
        Out "  WROTE $($r.Rel): $h == after"
    }
} catch {
    Out "ERROR: $($_.Exception.Message). Rolling back $($touched.Count) file(s) from $bk"
    foreach ($r in $touched) {
        try {
            $b = Join-Path $bk ($r.Rel -replace '/', '\')
            [IO.File]::WriteAllBytes($r.Live, [IO.File]::ReadAllBytes($b))
            $h = Sha $r.Live
            Out "  restored $($r.Rel): $h $(if ($h -eq $r.Before) { '== before' } else { 'FAIL: != before' })"
        } catch { Out "  FAIL restoring $($r.Rel): $($_.Exception.Message)" }
    }
    exit 4
}
Out ''
Out "DONE: $($todo.Count) file(s) written, $nDone already applied; every live file == after. No git commands were run."
Out 'Commit (Agent 1): the SDK repo DimensionsRecomp/rexglue-sdk (5 files), then the game repo DimensionsRecomp (shaders.cpp; and the submodule pointer if the SDK commit moves it).'
exit 0
