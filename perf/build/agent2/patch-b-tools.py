"""Agent 2 (23:40): add the build-B parameters to build-snap.ps1 and stage-snap-bin.ps1 (defaults unchanged).
Each replacement must match exactly once; a file is written only if all its edits apply. Originals: <file>.pre-B."""
import os, sys

A = r'<workspace>\build\agent2'
EDITS = {
    'build-snap.ps1': [
        (r'''# Run as a run_command background task:
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-snap.ps1 -Phase sdk|game|all
#       [-Jobs 10] [-Affinity F] [-SkipConfigure] [-KeepGoing]''',
         r'''# Build B (Agent 9's codegen option; run-b.ps1 drives it, prep-b.py prepares it): -Phase game -Tag snapB
#   -SnapDir build\agent2\snapB\DimensionsRecomp (a copy of snap1 at S2 with Agent 9's batch-nolr rexlego/generated and
#   legodimensions_config.toml) -GameDir build\agent2\snapB-off -CodegenExe build\agent2\codegen-frozen\codegen-frozen2.exe
#   (checks every source sources.cmake lists) -GenBase build\agent9\install\batch-nolr\generated (gen-check's reference;
#   never install\batch, which has skip_lr). The SDK stays snap1-sdk/install: an -SnapDir run refuses the sdk phase and
#   the snap1-off/snap1-on trees. The gate gets --snap-dir (allowed root, and the TU list from that sources.cmake).
# Run as a run_command background task:
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-snap.ps1 -Phase sdk|game|all
#       [-Jobs 10] [-Affinity F] [-SkipConfigure] [-KeepGoing] [-NoBuild] [-SnapDir D -GameDir D -CodegenExe F -GenBase D]'''),
        (r'''      [string]$Tag = 'snap1', [switch]$Native, [int]$PrelinkJobs = 0, [switch]$NoBuild)''',
         r'''      [string]$Tag = 'snap1', [switch]$Native, [int]$PrelinkJobs = 0, [switch]$NoBuild,
      [string]$SnapDir = '', [string]$GameDir = '', [string]$CodegenExe = '', [string]$GenBase = '')'''),
        (r'''$snap = "$R\build\agent2\snap1\DimensionsRecomp"
$sdkBin = "$R\build\agent2\snap1-sdk"
$gameBin = "$R\build\agent2\snap1-off"''',
         r'''function AbsR([string]$p) { if (-not [IO.Path]::IsPathRooted($p)) { $p = Join-Path $R $p }; $p.TrimEnd('\') }
$snap = "$R\build\agent2\snap1\DimensionsRecomp"
if ($SnapDir) {
    if ($Phase -ne 'game') {
        "$(Get-Date -Format HH:mm:ss) STOP  -SnapDir needs -Phase game (the SDK is built from snap1 only)" | Out-File -Append -Encoding utf8 $steps
        exit 2
    }
    $snap = AbsR $SnapDir
}
$sdkBin = "$R\build\agent2\snap1-sdk"
$gameBin = "$R\build\agent2\snap1-off"
$cg = "$Rf/build/agent2/codegen-frozen/codegen-frozen.exe"
if ($CodegenExe) { $cg = (AbsR $CodegenExe) -replace '\\', '/' }'''),
        (r'''        $S = "$Rf/build/agent2/snap1/DimensionsRecomp"; $ng = "$S/rexlego/out/native-gpu"''',
         r'''        $S = $snap -replace '\\', '/'; $ng = "$S/rexlego/out/native-gpu"'''),
        (r'''        "$(Get-Date -Format HH:mm:ss) NOTE  native: LEGO_GPU_PRELINK_JOBS=$env:LEGO_GPU_PRELINK_JOBS" | Out-File -Append -Encoding utf8 $steps
    }
    if (-not $SkipConfigure) {''',
         r'''        "$(Get-Date -Format HH:mm:ss) NOTE  native: LEGO_GPU_PRELINK_JOBS=$env:LEGO_GPU_PRELINK_JOBS" | Out-File -Append -Encoding utf8 $steps
    }
    if ($GameDir) { $gameBin = AbsR $GameDir }
    if ($SnapDir) {
        if ($gameBin -match 'snap1-(off|on)$') {
            "$(Get-Date -Format HH:mm:ss) STOP  -SnapDir must not use the snap1 game trees ($gameBin): pass -GameDir" | Out-File -Append -Encoding utf8 $steps
            exit 2
        }
        "$(Get-Date -Format HH:mm:ss) NOTE  snapshot $snap, game tree $gameBin, codegen stand-in $cg, gen-check reference $(if ($GenBase) { AbsR $GenBase } else { 'baseline' })" | Out-File -Append -Encoding utf8 $steps
    }
    if (-not $SkipConfigure) {'''),
        (r'''            "-DREXGLUE_HOST_CODEGEN_EXECUTABLE=$Rf/build/agent2/codegen-frozen/codegen-frozen.exe " +''',
         r'''            "-DREXGLUE_HOST_CODEGEN_EXECUTABLE=$cg " +'''),
        (r'''    $c = Step 'gen-check' "python `"$log\gen-check.py`" > `"$log\$Tag-$gt-gen-check.log`" 2>&1"
    if ($c -ne 0) { exit 24 }
    $c = Step 'gate' "python `"$log\snap-gate.py`" `"$gameBin`" > `"$gateLog`" 2>&1"''',
         r'''    $gcArgs = ''; $gArgs = ''
    if ($SnapDir) { $gcArgs = " --snap `"$snap\rexlego\generated`" --snap-rex `"$snap\rexlego`""; $gArgs = " --snap-dir `"$snap`"" }
    if ($GenBase) { $gcArgs += " --base `"$(AbsR $GenBase)`"" }
    $c = Step 'gen-check' "python `"$log\gen-check.py`"$gcArgs > `"$log\$Tag-$gt-gen-check.log`" 2>&1"
    if ($c -ne 0) { exit 24 }
    $c = Step 'gate' "python `"$log\snap-gate.py`" `"$gameBin`"$gArgs > `"$gateLog`" 2>&1"'''),
    ],
    'stage-snap-bin.ps1': [
        (r'''#        [-SnapTag S1] [-BuildTag snap1] [-ExeStrings 'literal of 16+ chars', ...] [-RuntimeStrings '...', ...]
param([ValidateSet('off', 'native')][string]$Variant = 'off', [string]$SnapTag = 'S1', [string]$BuildTag = '',
    [string[]]$ExeStrings = @(), [string[]]$RuntimeStrings = @())''',
         r'''#        [-SnapTag S1] [-BuildTag snap1] [-ExeStrings 'literal of 16+ chars', ...] [-RuntimeStrings '...', ...]
# Build B (run-b.ps1): -GameTree build\agent2\snapB-off -OutDir build\agent2\devoffB-bin -GameSnap
#   build\agent2\snapB\DimensionsRecomp (the game's source copy: the game-tree freshness checks and FiraSans use it, and
#   every patched file's copy there must hash-equal its PATCHES row; the SDK, its out tree and the PATCHES/STATE records
#   stay snap1's) -CompareBin build\agent2\devoff2-bin (A: every staged file but the exe and map must be identical to
#   A's, and the exe must differ) -WhatText / -CodegenNote / -ManifestNotesFile (lines, each written as '# line') for
#   the MANIFEST text.
param([ValidateSet('off', 'native')][string]$Variant = 'off', [string]$SnapTag = 'S1', [string]$BuildTag = '',
    [string[]]$ExeStrings = @(), [string[]]$RuntimeStrings = @(),
    [string]$GameTree = '', [string]$OutDir = '', [string]$GameSnap = '', [string]$CompareBin = '',
    [string]$WhatText = '', [string]$CodegenNote = '', [string]$ManifestNotesFile = '')'''),
        (r'''$RO = "$R\toolchain\llvm-23.1.6\bin\llvm-readobj.exe"''',
         r'''$RO = "$R\toolchain\llvm-23.1.6\bin\llvm-readobj.exe"
function AbsR([string]$p) { if (-not [IO.Path]::IsPathRooted($p)) { $p = Join-Path $R $p }; $p.TrimEnd('\') }
if ($GameTree) { $B = AbsR $GameTree }
if ($OutDir) { $O = AbsR $OutDir }
$GS = $(if ($GameSnap) { AbsR $GameSnap } else { $S })
if ($CompareBin) { $CompareBin = AbsR $CompareBin }'''),
        (r'''    'FiraSans-Regular.ttf'     = "$S\rexlego\res\FiraSans-Regular.ttf"''',
         r'''    'FiraSans-Regular.ttf'     = "$GS\rexlego\res\FiraSans-Regular.ttf"'''),
        (r'''function FreshCheck([string]$tree, [string[]]$rels) {''',
         r'''function FreshCheck([string]$tree, [string[]]$rels, $map) {'''),
        (r'''    $paths = @(foreach ($rel in $rels) { $rowPaths[$rel] })''',
         r'''    $paths = @(foreach ($rel in $rels) { $map[$rel] })'''),
        (r'''        foreach ($p in $rowPaths[$rel]) {''',
         r'''        foreach ($p in $map[$rel]) {'''),
        (r'''$rowPaths = [ordered]@{}
foreach ($pr in @($lastRow.Values | Where-Object { $_.After -ne 'DELETED' })) {
    $l = New-Object System.Collections.Generic.List[string]
    $l.Add((NormFull ("$S\" + $pr.Rel) $S))
    if ($pr.Rel.StartsWith('rexglue-sdk/include/')) {
        $inst = "$SB\install\include\" + $pr.Rel.Substring(20).Replace('/', '\')
        if (Test-Path -LiteralPath $inst) {
            Check ((Sha $inst) -eq $pr.After) "snap1-sdk/install/include copy of $($pr.Rel) == the patched file ($(Pfx $pr.After))"
            $l.Add((NormFull $inst $S))
        } else { Note "$($pr.Rel) has no snap1-sdk/install/include copy" }
    }
    $rowPaths[$pr.Rel] = $l
}''',
         r'''# $rowPaths: what the game tree compiles or includes (the patched file in the game's source copy $GS, plus the installed
# header copy); $rowPathsSdk: the same rows in snap1, which snap1-sdk compiles. Identical unless -GameSnap is given.
$rowPaths = [ordered]@{}; $rowPathsSdk = [ordered]@{}
foreach ($pr in @($lastRow.Values | Where-Object { $_.After -ne 'DELETED' })) {
    $l = New-Object System.Collections.Generic.List[string]; $ls = New-Object System.Collections.Generic.List[string]
    $gp = "$GS\" + $pr.Rel.Replace('/', '\')
    if ($GS -eq $S -or (Test-Path -LiteralPath $gp)) { $l.Add((NormFull $gp $GS)) }
    $ls.Add((NormFull ("$S\" + $pr.Rel) $S))
    if ($GS -ne $S) {
        Check ((Test-Path -LiteralPath $gp) -and ((Sha $gp) -eq $pr.After)) "game snapshot copy of $($pr.Rel) == the patched file ($(Pfx $pr.After))"
    }
    if ($pr.Rel.StartsWith('rexglue-sdk/include/')) {
        $inst = "$SB\install\include\" + $pr.Rel.Substring(20).Replace('/', '\')
        if (Test-Path -LiteralPath $inst) {
            Check ((Sha $inst) -eq $pr.After) "snap1-sdk/install/include copy of $($pr.Rel) == the patched file ($(Pfx $pr.After))"
            $l.Add((NormFull $inst $S)); $ls.Add((NormFull $inst $S))
        } else { Note "$($pr.Rel) has no snap1-sdk/install/include copy" }
    }
    $rowPaths[$pr.Rel] = $l; $rowPathsSdk[$pr.Rel] = $ls
}'''),
        (r'''$gameAff = @(FreshCheck $B @($rowPaths.Keys))''',
         r'''$gameAff = @(FreshCheck $B @($rowPaths.Keys) $rowPaths)'''),
        (r'''    $null = @(FreshCheck $SB $sdkRels)''',
         r'''    $null = @(FreshCheck $SB $sdkRels $rowPathsSdk)'''),
        (r'''    Check ((Sha "$B\amd_fidelityfx_dx12.dll") -eq (Sha "$S\rexglue-sdk\thirdparty\FidelityFX-SDK\PrebuiltSignedDLL\amd_fidelityfx_dx12.dll")) "amd_fidelityfx_dx12.dll == the snapshot's PrebuiltSignedDLL copy"
}
# import tables: every DLL that is neither an API set nor in System32 must be staged''',
         r'''    Check ((Sha "$B\amd_fidelityfx_dx12.dll") -eq (Sha "$GS\rexglue-sdk\thirdparty\FidelityFX-SDK\PrebuiltSignedDLL\amd_fidelityfx_dx12.dll")) "amd_fidelityfx_dx12.dll == the snapshot's PrebuiltSignedDLL copy"
}
# -CompareBin (build B vs A): the same snapshot and SDK, so everything but the exe and map must be identical
if ($CompareBin) {
    $cl = Split-Path -Leaf $CompareBin
    foreach ($k in $items.Keys) {
        $cp = Join-Path $CompareBin $k
        if (-not (Test-Path -LiteralPath $cp)) { Note "$k is not in $cl"; continue }
        $same = (Sha $items[$k]) -eq (Sha $cp)
        if ($k -eq 'legodimensions.exe') { Check (-not $same) "legodimensions.exe differs from the one in $cl (the generated code changed)" }
        elseif ($k -eq 'legodimensions.map') { Note ("legodimensions.map {0} the one in $cl" -f $(if ($same) { 'is identical to' } else { 'differs from' })) }
        else { Check $same "$k == the one in $cl" }
    }
}
# import tables: every DLL that is neither an API set nor in System32 must be staged'''),
        (r'''$what = $(if ($Variant -eq 'off') { "dev OFF build ${bn}: NATIVE_GPU=OFF" } else { "native build ${bn}: NATIVE_GPU=ON with Agent 6's AOT inputs" })''',
         r'''$what = $(if ($Variant -eq 'off') { "dev OFF build ${bn}: NATIVE_GPU=OFF" } else { "native build ${bn}: NATIVE_GPU=ON with Agent 6's AOT inputs" })
if ($WhatText) { $what = $WhatText }'''),
        (r'''$man.Add("# SDK: build/agent2/snap1-sdk (REXGLUE_BUILD_TESTS=OFF), built from the same snapshot (incrementally after S1) and installed to snap1-sdk/install; game tree build/agent2/$(Split-Path -Leaf $B); codegen 0.0.23.3 (pinned generated output hash-checked against baseline/ by gen-check.py; codegen-frozen.exe stand-in writes nothing).")''',
         r'''if ($GS -ne $S) { $man.Add("# game sources: $($GS.Substring($R.Length + 1).Replace('\', '/')) = a copy of that snapshot (its rexlego/generated and rexlego/legodimensions_config.toml replaced, see below); each patched file's copy there is hash-checked.") }
$cgText = $(if ($CodegenNote) { $CodegenNote } else { 'codegen 0.0.23.3 (pinned generated output hash-checked against baseline/ by gen-check.py; codegen-frozen.exe stand-in writes nothing)' })
$man.Add("# SDK: build/agent2/snap1-sdk (REXGLUE_BUILD_TESTS=OFF), built from the same snapshot (incrementally after S1) and installed to snap1-sdk/install; game tree build/agent2/$(Split-Path -Leaf $B); $cgText.")
if ($ManifestNotesFile) { foreach ($nl in @(Get-Content -Encoding UTF8 -LiteralPath (AbsR $ManifestNotesFile))) { if ($nl.Trim()) { $man.Add("# $nl") } } }'''),
    ],
}

for name, pairs in EDITS.items():
    p = os.path.join(A, name)
    if not os.path.exists(p + '.pre-B'):
        sys.exit('no backup %s.pre-B' % name)
    text = open(p, 'rb').read().decode('utf-8')
    if '\r\n' in text:
        sys.exit('unexpected CRLF in ' + name)
    for i, (old, new) in enumerate(pairs):
        n = text.count(old)
        if n != 1:
            sys.exit('%s edit %d: %d matches (expected 1); nothing written for this file' % (name, i, n))
        text = text.replace(old, new)
    open(p, 'wb').write(text.encode('utf-8'))
    print('patched %s: %d edits' % (name, len(pairs)))
