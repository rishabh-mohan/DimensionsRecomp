# Agent 2 - stage a snapshot game build and verify the ARTIFACTS, not the build log (README-dev "Things that have
# cost real time"), the way stage-baseline-bin.ps1 does for build/baseline-bin.
#   -Variant off    : build/agent2/snap1-off, NATIVE_GPU=OFF -> build/agent2/devoff<N>-bin (S1: devoff1-bin)
#   -Variant native : build/agent2/snap1-on, NATIVE_GPU=ON with Agent 6's inputs -> build/agent2/native-bin for S1,
#                     native<N>-bin for S<N> (N >= 2)
#   -SnapTag S<N>   : the snapshot state of the build. S1 = MANIFEST-S1-*.tsv (+ PATCHES-S1.tsv); S2 and later = the
#                     newest STATE-S<N>-*.tsv written by snap-patch.py apply (+ PATCHES-S1.tsv ... PATCHES-S<N>.tsv);
#                     S<N><suffix> (S3d = S3 + one file) = the newest STATE-S3d-*.tsv (+ PATCHES-S1.tsv ...
#                     PATCHES-S<N>.tsv, then PATCHES-S3d.tsv); give it -BuildTag and -OutDir (the defaults would be
#                     snap-s3d and devoffS3d-bin / nativeS3d-bin)
#   -BuildTag       : the build-snap.ps1 -Tag of the build, for its gate log; default snap<N>
# Checks:
#   - the gate log says RESULT: PASS;
#   - freshness. S1: the exe is newer than the snapshot manifest. Every tag: each object that compiles or includes a
#     patched file (all PATCHES rows; compile_commands.json "output" + ninja -t deps) is newer than the patched copy,
#     in the game tree and, for rexglue-sdk files, in snap1-sdk; a patched rexglue-sdk/include header must also have
#     an identical snap1-sdk/install/include copy; the SDK out tree's rexruntime.dll must be newer than every rebuilt
#     object of the libraries linked into it. S2+: the exe must be newer than the STATE file when a file patched in
#     this tag is compiled or included by the game tree;
#   - the exe is newer than every object in the game tree, and the map was written with it;
#   - rexruntime.dll: game tree == snap1-sdk/install/bin == SDK out tree; rexgpu-xenos.dll: install == out tree;
#     native: amd_fidelityfx_dx12.dll == the snapshot's PrebuiltSignedDLL copy;
#   - import tables (llvm-readobj): every non-system DLL a staged binary imports is staged; nothing imports Tracy;
#   - strings of 16+ chars, including one that only the dev SDK has (Agent 12's pause_safe_order description), the
#     native build's GPU fingerprint, and -ExeStrings / -RuntimeStrings;
#   - every staged file hashes equal to its source. Writes <out>/MANIFEST.txt.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\stage-snap-bin.ps1 -Variant off|native
#        [-SnapTag S1] [-BuildTag snap1] [-ExeStrings 'literal of 16+ chars', ...] [-RuntimeStrings '...', ...]
# Build B (run-b.ps1): -GameTree build\agent2\snapB-off -OutDir build\agent2\devoffB-bin -GameSnap
#   build\agent2\snapB\DimensionsRecomp (the game's source copy: the game-tree freshness checks and FiraSans use it, and
#   every patched file's copy there must hash-equal its PATCHES row; the SDK, its out tree and the PATCHES/STATE records
#   stay snap1's) -CompareBin build\agent2\devoff2-bin (A: every staged file but the exe and map must be identical to
#   A's, and the exe must differ) -WhatText / -CodegenNote / -ManifestNotesFile (lines, each written as '# line') for
#   the MANIFEST text.
# native3d (run-s3d.ps1): -SnapTag S3d -BuildTag snap3d -OutDir build\agent2\native3d-bin -CompareBin
#   build\agent2\native3-bin -CompareWhy 'S3d changed rexlego/src/gpu_native/draw.cpp' (-CompareWhy: why the exe must
#   differ from the -CompareBin one; default 'the generated code changed', build B's reason).
# S4a (run-s4a.ps1, task #4 of board run 2): -SnapTag S4a -BuildTag snap4a -OutDir build\agent2\devoff4-bin or
#   native4-bin -PatchTagList 'S1,S2,S3,S3d,S4a' (the PATCHES-<tag>.tsv files to list and check, in this order,
#   instead of the ones derived from -SnapTag: for S4a those would skip S3d) -XenosStrings 'a,b' (more literals of 16+
#   chars rexgpu-xenos.dll must contain). No -CompareBin: the S4a SDK DLLs differ from S3d's by design.
param([ValidateSet('off', 'native')][string]$Variant = 'off', [string]$SnapTag = 'S1', [string]$BuildTag = '',
    [string[]]$ExeStrings = @(), [string[]]$RuntimeStrings = @(), [string[]]$XenosStrings = @(), [string]$PatchTagList = '',
    [string]$GameTree = '', [string]$OutDir = '', [string]$GameSnap = '', [string]$CompareBin = '',
    [string]$WhatText = '', [string]$CodegenNote = '', [string]$ManifestNotesFile = '',
    [string]$CompareWhy = 'the generated code changed')
$ErrorActionPreference = 'Stop'
# powershell -File passes "-ExeStrings a,b" as ONE string, so split on commas (no literal checked here has a comma)
$ExeStrings = @($ExeStrings | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$RuntimeStrings = @($RuntimeStrings | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$XenosStrings = @($XenosStrings | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$R = '<workspace>'
$A = "$R\build\agent2"; $S = "$A\snap1\DimensionsRecomp"; $SB = "$A\snap1-sdk"
$B = $(if ($Variant -eq 'off') { "$A\snap1-off" } else { "$A\snap1-on" }); $I = "$SB\install\bin"; $sdkOut = "$S\rexglue-sdk\out\win-amd64\Release"
$SnapN = $(if ($SnapTag -match '^S(\d+)$') { [int]$Matches[1] } else { 0 })
$bn = $(if ($SnapN -gt 0) { "$SnapN" } else { $SnapTag })
if (-not $BuildTag) { $BuildTag = $(if ($SnapN -gt 0) { "snap$SnapN" } else { 'snap-' + $SnapTag.ToLower() }) }
$O = $(if ($Variant -eq 'off') { "$A\devoff$bn-bin" } elseif ($SnapN -eq 1) { "$A\native-bin" } else { "$A\native$bn-bin" })
$gateLog = $(if ($Variant -eq 'off') { "$A\$BuildTag-gate.log" } else { "$A\$BuildTag-native-gate.log" })
$RO = "$R\toolchain\llvm-23.1.6\bin\llvm-readobj.exe"
function AbsR([string]$p) { if (-not [IO.Path]::IsPathRooted($p)) { $p = Join-Path $R $p }; $p.TrimEnd('\') }
if ($GameTree) { $B = AbsR $GameTree }
if ($OutDir) { $O = AbsR $OutDir }
$GS = $(if ($GameSnap) { AbsR $GameSnap } else { $S })
if ($CompareBin) { $CompareBin = AbsR $CompareBin }
$items = [ordered]@{
    'legodimensions.exe'       = "$B\legodimensions.exe"
    'legodimensions.map'       = "$B\legodimensions.map"
    'rexruntime.dll'           = "$B\rexruntime.dll"
    'rexgpu-xenos.dll'         = "$I\rexgpu-xenos.dll"
    'TracyClient.dll'          = "$I\TracyClient.dll"
    'achievement_unlocked.wav' = "$B\achievement_unlocked.wav"
    'FiraSans-Regular.ttf'     = "$GS\rexlego\res\FiraSans-Regular.ttf"
}
if ($Variant -eq 'native') { $items['amd_fidelityfx_dx12.dll'] = "$B\amd_fidelityfx_dx12.dll" }
$fails = New-Object System.Collections.Generic.List[string]
$report = New-Object System.Collections.Generic.List[string]
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash }
function Check([bool]$ok, [string]$what) { $report.Add(("{0} {1}" -f ($(if ($ok) { 'PASS' } else { 'FAIL' })), $what)); if (-not $ok) { $fails.Add($what) } }
function Note([string]$what) { $report.Add("NOTE $what") }
function Pfx([string]$h) { if ($h.Length -gt 16) { $h.Substring(0, 16) } else { $h } }
function HasStrings([string]$file, [string[]]$needles) {
    $text = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($file))
    foreach ($needle in $needles) { Check ($text.Contains($needle)) ("{0} contains '{1}'" -f (Split-Path -Leaf $file), $needle) }
    $text = $null; [GC]::Collect()
}
function NormFull([string]$p, [string]$base) {
    # absolute, '\'-separated, '.' and '..' resolved, lower case (no GetFullPath: snapshot paths can pass MAX_PATH)
    $p = $p.Trim().Replace('/', '\')
    if ($p -notmatch '^[A-Za-z]:\\') { $p = $base.Replace('/', '\').TrimEnd('\') + '\' + $p }
    $segs = New-Object System.Collections.Generic.List[string]
    foreach ($seg in $p.Split('\')) {
        if ($seg -eq '' -or $seg -eq '.') { continue }
        if ($seg -eq '..') { if ($segs.Count -gt 1) { $segs.RemoveAt($segs.Count - 1) }; continue }
        $segs.Add($seg)
    }
    ($segs -join '\').ToLowerInvariant()
}
function Dependents([string]$tree, [string[]]$paths) {
    # objects of $tree that compile (compile_commands.json "output") or include (ninja -t deps) one of $paths.
    # Returns @{ normalized path = List[normalized object path] }. Read-only: ninja tools never rebuild the manifest.
    $ErrorActionPreference = 'Continue'
    $hits = @{}; $leaf = @{}
    foreach ($p in $paths) {
        $k = NormFull $p $tree
        if (-not $hits.ContainsKey($k)) { $hits[$k] = New-Object System.Collections.Generic.List[string] }
        $leaf[$k.Substring($k.LastIndexOf('\') + 1)] = 1
    }
    $cc = Join-Path $tree 'compile_commands.json'
    if (Test-Path $cc) {
        Add-Type -AssemblyName System.Web.Extensions
        $ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
        $ser.MaxJsonLength = [int]::MaxValue
        foreach ($e in $ser.DeserializeObject([System.IO.File]::ReadAllText($cc))) {
            if (-not $e.ContainsKey('output')) { continue }
            $f = NormFull $e['file'] $e['directory']
            if ($hits.ContainsKey($f)) {
                $obj = NormFull $e['output'] $e['directory']
                if (-not $hits[$f].Contains($obj)) { $hits[$f].Add($obj) }
            }
        }
    }
    $mk = (Select-String -Path "$tree\CMakeCache.txt" -Pattern '^CMAKE_MAKE_PROGRAM:[A-Z]+=(.+)$' | Select-Object -First 1).Matches[0].Groups[1].Value
    $nf = @(); if (Test-Path "$tree\build-Release.ninja") { $nf = @('-f', 'build-Release.ninja') }
    $target = $null
    foreach ($line in @(& $mk -C $tree @nf -t deps 2>$null)) {
        if ($line -match '^(\S.*): #deps \d+, deps mtime -?\d+ \(\w+\)\s*$') { $target = NormFull $Matches[1] $tree; continue }
        if ($null -eq $target -or $line.Length -lt 2 -or $line[0] -ne ' ') { continue }
        $d = $line.Trim()
        if (-not $leaf.ContainsKey($d.Substring($d.LastIndexOfAny([char[]]@('/', '\')) + 1).ToLowerInvariant())) { continue }
        $k = NormFull $d $tree
        if ($hits.ContainsKey($k) -and -not $hits[$k].Contains($target)) { $hits[$k].Add($target) }
    }
    return $hits
}
function FreshCheck([string]$tree, [string[]]$rels, $map) {
    # every built object that compiles or includes a patched file is newer than it; emits the rels that have one
    $label = Split-Path -Leaf $tree
    $paths = @(foreach ($rel in $rels) { $map[$rel] })
    if (-not $paths.Count) { return }
    $hits = Dependents $tree $paths
    foreach ($rel in $rels) {
        $seen = @{}; $stale = New-Object System.Collections.Generic.List[string]; $missing = 0
        foreach ($p in $map[$rel]) {
            $pt = (Get-Item -LiteralPath $p).LastWriteTimeUtc
            foreach ($obj in $hits[$p]) {
                if ($seen.ContainsKey($obj)) { continue }
                $seen[$obj] = 1
                if (-not (Test-Path -LiteralPath $obj)) { $missing++; continue }
                if ((Get-Item -LiteralPath $obj).LastWriteTimeUtc -lt $pt) { $stale.Add($obj) }
                $script:depObjs.Add($obj)
            }
        }
        if ($seen.Count -eq 0) { Note "$rel is not compiled or included in $label"; continue }
        $built = $seen.Count - $missing
        $more = $(if ($missing) { "; $missing listed object(s) not built (other configurations)" } else { '' })
        $st = $(if ($stale.Count) { '; STALE: ' + (($stale | Select-Object -First 3) -join ', ') } else { '' })
        Check ($stale.Count -eq 0 -and $built -gt 0) "${rel}: $built object(s) in $label compile or include it, all newer than the patched copy$more$st"
        if ($built -gt 0) { $rel }
    }
}
foreach ($k in $items.Keys) { Check (Test-Path $items[$k]) "source exists: $($items[$k].Substring($R.Length + 1))" }
Check (Test-Path $gateLog) "gate log exists: $(Split-Path -Leaf $gateLog)"
$snapMan = Get-ChildItem "$A\snap1" -File | Where-Object { $_.Name -like "MANIFEST-$SnapTag-*.tsv" -or $_.Name -like "STATE-$SnapTag-*.tsv" } | Sort-Object LastWriteTime | Select-Object -Last 1
Check ($null -ne $snapMan) "snapshot record MANIFEST-$SnapTag-*.tsv or STATE-$SnapTag-*.tsv exists"
if ($fails.Count) { $report; "NOT staged: $($fails.Count) check(s) failed"; exit 1 }
Check ([bool](Select-String -Path $gateLog -Pattern '^RESULT: PASS' -Quiet)) "$(Split-Path -Leaf $gateLog) says RESULT: PASS"
# patches applied to snap1 since S1: S<N> (N >= 2) lists the rows of every tag S1..S<N> (S3 = S1 + S2 + S3, so S2's
# rows stay in S3's MANIFEST and freshness checks); S<N><suffix> lists S1..S<N>, then its own (S3d = S1 + S2 + S3 +
# S3d); any other tag lists S1's rows, then its own
$SnapBaseN = $(if ($SnapTag -match '^S(\d+)[A-Za-z]+$') { [int]$Matches[1] } else { 0 })
$patchTags = $(if ($SnapN -ge 2) { @(1..$SnapN | ForEach-Object { "S$_" }) } elseif ($SnapBaseN -ge 1) { @(1..$SnapBaseN | ForEach-Object { "S$_" }) + @($SnapTag) } else { @('S1', $SnapTag) })
# -PatchTagList (S4a): the given tags, in order (PowerShell names ignore case, hence not -PatchTags = $patchTags)
if ($PatchTagList) { $patchTags = @($PatchTagList -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$patchFiles = @($patchTags | Select-Object -Unique | ForEach-Object { "$A\snap1\PATCHES-$_.tsv" } | Where-Object { Test-Path $_ })
$patchRows = @(foreach ($pf in $patchFiles) {
        foreach ($line in @(Get-Content $pf | Where-Object { $_ -and -not $_.StartsWith('#') })) {
            $c = $line -split "`t"
            [pscustomobject]@{ File = (Split-Path -Leaf $pf); Rel = $c[0]; Before = $c[1]; After = $c[2]; Tag = $c[5].Split(':')[0] }
        }
    })
# the last row per file wins (a file patched in S1 and again in this tag is checked against this tag's version)
$lastRow = [ordered]@{}
foreach ($pr in $patchRows) { $lastRow[$pr.Rel] = $pr }
# $rowPaths: what the game tree compiles or includes (the patched file in the game's source copy $GS, plus the installed
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
}
# freshness
$exe = Get-Item $items['legodimensions.exe']
$newestObj = Get-ChildItem "$B\CMakeFiles" -Recurse -Filter *.obj | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Check ($exe.LastWriteTime -ge $newestObj.LastWriteTime) ("exe {0:HH:mm:ss} newer than newest obj {1} {2:HH:mm:ss}" -f $exe.LastWriteTime, $newestObj.Name, $newestObj.LastWriteTime)
$map = Get-Item $items['legodimensions.map']
Check ($map.LastWriteTime -ge $exe.LastWriteTime.AddSeconds(-5)) ("map written with the exe ({0:HH:mm:ss})" -f $map.LastWriteTime)
Check ([bool](Select-String -Path $map.FullName -Pattern 'native_lock_elide\.cpp\.obj' -Quiet)) "map lists native_lock_elide.cpp.obj"
$script:depObjs = New-Object System.Collections.Generic.List[string]
$gameAff = @(FreshCheck $B @($rowPaths.Keys) $rowPaths)
$sdkRels = @($rowPaths.Keys | Where-Object { $_.StartsWith('rexglue-sdk/') })
if ($sdkRels.Count) {
    $script:depObjs = New-Object System.Collections.Generic.List[string]
    $null = @(FreshCheck $SB $sdkRels $rowPathsSdk)
    $core = @($script:depObjs | Where-Object { $_ -match '\\(rexruntime|rexcore|rexfilesystem|rexinput|rexui|rexaudio)\.dir\\' } | Sort-Object -Unique)
    if ($core.Count) {
        $newestCore = @($core | ForEach-Object { (Get-Item -LiteralPath $_).LastWriteTime } | Sort-Object)[-1]
        $dll = Get-Item "$sdkOut\rexruntime.dll"
        Check ($dll.LastWriteTime -ge $newestCore) ("SDK out tree rexruntime.dll {0:HH:mm:ss} is newer than the {1} rebuilt object(s) linked into it (newest {2:HH:mm:ss})" -f $dll.LastWriteTime, $core.Count, $newestCore)
    }
}
if ($snapMan.Name -like 'MANIFEST-*') {
    Check ($exe.LastWriteTime -gt $snapMan.LastWriteTime) ("exe {0:HH:mm:ss} newer than {1} ({2:HH:mm:ss})" -f $exe.LastWriteTime, $snapMan.Name, $snapMan.LastWriteTime)
} else {
    $thisRels = @($patchRows | Where-Object { $_.File -eq "PATCHES-$SnapTag.tsv" } | ForEach-Object { $_.Rel })
    $hitRels = @($gameAff | Where-Object { $thisRels -contains $_ })
    if ($hitRels.Count) {
        Check ($exe.LastWriteTime -gt $snapMan.LastWriteTime) ("exe {0:HH:mm:ss} relinked after {1} ({2:HH:mm:ss}); {3} {4} file(s) are compiled or included here" -f $exe.LastWriteTime, $snapMan.Name, $snapMan.LastWriteTime, $hitRels.Count, $SnapTag)
    } else {
        Note ("exe {0:HH:mm:ss}, {1} {2:HH:mm:ss}: no {3} file is compiled or included by {4}{5}" -f $exe.LastWriteTime, $snapMan.Name, $snapMan.LastWriteTime, $SnapTag, (Split-Path -Leaf $B), $(if ($exe.LastWriteTime -gt $snapMan.LastWriteTime) { '; relinked anyway (an SDK library or import library changed)' } else { '; ninja kept the exe' }))
    }
}
# DLL identity
Check ((Sha "$B\rexruntime.dll") -eq (Sha "$I\rexruntime.dll")) "$(Split-Path -Leaf $B)/rexruntime.dll == snap1-sdk/install/bin/rexruntime.dll"
Check ((Sha "$I\rexruntime.dll") -eq (Sha "$sdkOut\rexruntime.dll")) "install/bin/rexruntime.dll == SDK out tree rexruntime.dll"
Check ((Sha "$I\rexgpu-xenos.dll") -eq (Sha "$sdkOut\rexgpu-xenos.dll")) "install/bin/rexgpu-xenos.dll == SDK out tree rexgpu-xenos.dll"
if ($Variant -eq 'native') {
    Check ((Sha "$B\amd_fidelityfx_dx12.dll") -eq (Sha "$GS\rexglue-sdk\thirdparty\FidelityFX-SDK\PrebuiltSignedDLL\amd_fidelityfx_dx12.dll")) "amd_fidelityfx_dx12.dll == the snapshot's PrebuiltSignedDLL copy"
}
# -CompareBin (build B vs A; native3d vs native3): the same SDK build, so everything but the exe and map must be
# identical; -CompareWhy says why the exe must differ
if ($CompareBin) {
    $cl = Split-Path -Leaf $CompareBin
    foreach ($k in $items.Keys) {
        $cp = Join-Path $CompareBin $k
        if (-not (Test-Path -LiteralPath $cp)) { Note "$k is not in $cl"; continue }
        $same = (Sha $items[$k]) -eq (Sha $cp)
        if ($k -eq 'legodimensions.exe') { Check (-not $same) "legodimensions.exe differs from the one in $cl ($CompareWhy)" }
        elseif ($k -eq 'legodimensions.map') { Note ("legodimensions.map {0} the one in $cl" -f $(if ($same) { 'is identical to' } else { 'differs from' })) }
        else { Check $same "$k == the one in $cl" }
    }
}
# import tables: every DLL that is neither an API set nor in System32 must be staged
$importLines = New-Object System.Collections.Generic.List[string]
foreach ($k in @($items.Keys | Where-Object { $_ -match '\.(exe|dll)$' })) {
    $imp = @(& $RO --coff-imports $items[$k] 2>&1 | Select-String -Pattern '^\s*Name:\s*(\S+\.dll)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
    Check ($imp.Count -gt 0) "$k import table readable ($($imp.Count) DLLs)"
    foreach ($d in $imp) {
        $sys = ($d -match '^(api|ext)-ms-') -or (Test-Path (Join-Path "$env:WINDIR\System32" $d))
        if (-not $sys) { Check ($items.Contains($d)) "$k imports $d (not a system DLL), which is staged" }
    }
    if ($k -ne 'TracyClient.dll') { Check ($imp -notcontains 'TracyClient.dll') "$k does not import TracyClient.dll" }
    $importLines.Add(("#   {0} imports: {1}" -f $k, ($imp -join ', ')))
}
# strings (README-dev: look in the actual binary); literals of 16+ chars only (clang builds <=15-char std::string
# literals from immediates, MSVC SSO)
$fpStrings = @(); if ($Variant -eq 'native') { $fpStrings = @(((Get-Content "$B\native-gpu-build.txt" -Raw).Trim() -split ' ')[-1]) }
HasStrings $items['legodimensions.exe'] (@('ui_font', 'FiraSans-Regular.ttf', 'depth_of_field', 'rexruntime.dll',
        'Pause and unpause the guest without allocating') + $ExeStrings + $fpStrings)
HasStrings $items['rexgpu-xenos.dll'] (@('Use bindless resources where available', 'd3d12_readback_memexport') + $XenosStrings)
HasStrings $items['rexruntime.dll'] (@('rexcrt_heap_enable', 'rexcrt_heap_size_mb') + $RuntimeStrings)
if ($fails.Count) { $report; "NOT staged: $($fails.Count) check(s) failed"; exit 1 }
# stage
New-Item -ItemType Directory -Force $O | Out-Null
$man = New-Object System.Collections.Generic.List[string]
$what = $(if ($Variant -eq 'off') { "dev OFF build ${bn}: NATIVE_GPU=OFF" } else { "native build ${bn}: NATIVE_GPU=ON with Agent 6's AOT inputs" })
if ($WhatText) { $what = $WhatText }
$man.Add("# build/agent2/$(Split-Path -Leaf $O) - Agent 2 (Agent 1's batch schedule). $what; Release, game x86-64-v3, SDK x86-64-v2.")
$man.Add("# staged $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'). Source: snapshot build/agent2/snap1/DimensionsRecomp at $SnapTag ($($snapMan.Name), sha256 $(Sha $snapMan.FullName)); build tag $BuildTag; every patch applied to the snapshot since S1 is listed below.")
if ($GS -ne $S) { $man.Add("# game sources: $($GS.Substring($R.Length + 1).Replace('\', '/')) = a copy of that snapshot (its rexlego/generated and rexlego/legodimensions_config.toml replaced, see below); each patched file's copy there is hash-checked.") }
$cgText = $(if ($CodegenNote) { $CodegenNote } else { 'codegen 0.0.23.3 (pinned generated output hash-checked against baseline/ by gen-check.py; codegen-frozen.exe stand-in writes nothing)' })
$man.Add("# SDK: build/agent2/snap1-sdk (REXGLUE_BUILD_TESTS=OFF), built from the same snapshot (incrementally after S1) and installed to snap1-sdk/install; game tree build/agent2/$(Split-Path -Leaf $B); $cgText.")
if ($ManifestNotesFile) { foreach ($nl in @(Get-Content -Encoding UTF8 -LiteralPath (AbsR $ManifestNotesFile))) { if ($nl.Trim()) { $man.Add("# $nl") } } }
if ($Variant -eq 'native') {
    foreach ($ni in @(Get-ChildItem "$A\snap1" -Filter 'NATIVE-INPUTS-*.tsv' | Sort-Object Name)) { $man.Add("# native inputs: $($ni.Name) (sha256 $(Sha $ni.FullName)).") }
    $man.Add("# native flags: build-snap.ps1 -Native. Native GPU fingerprint (native-gpu-build.txt, checked in the exe): $((Get-Content "$B\native-gpu-build.txt" -Raw).Trim()).")
}
foreach ($pf in $patchFiles) {
    $pn = Split-Path -Leaf $pf
    $man.Add("# patches in $pn (sha256 $(Sha $pf)); before -> after sha256 prefixes:")
    foreach ($pr in @($patchRows | Where-Object { $_.File -eq $pn })) { $man.Add(("#   {0} {1}: {2} -> {3}" -f $pr.Tag, $pr.Rel, (Pfx $pr.Before), (Pfx $pr.After))) }
}
$man.Add("# No PDBs: the exe links without /DEBUG; symbols are in legodimensions.map. Runtime also needs legodimensions.toml in the working dir.")
$man.Add("# TracyClient.dll is staged for parity with build/baseline-bin; no staged binary imports it.")
$man.Add("# name`tsize`tmtime`tsha256`tsource")
foreach ($k in $items.Keys) {
    $src = $items[$k]; $dst = Join-Path $O $k
    Copy-Item $src $dst -Force
    $hs = Sha $src; $hd = Sha $dst
    Check ($hs -eq $hd) "staged copy identical: $k"
    $f = Get-Item $src
    $man.Add(("{0}`t{1}`t{2:yyyy-MM-dd HH:mm:ss}`t{3}`t{4}" -f $k, $f.Length, $f.LastWriteTime, $hd, $src.Substring($R.Length + 1)))
}
$man.Add("# imports (llvm-readobj --coff-imports):")
foreach ($l in $importLines) { $man.Add($l) }
$man.Add("# checks:")
foreach ($l in $report) { $man.Add("#   $l") }
$man | Out-File -Encoding utf8 "$O\MANIFEST.txt"
$report
if ($fails.Count) { "STAGED WITH FAILURES: $($fails.Count)"; exit 1 }
"staged $($items.Count) files into $O ($([Math]::Round(((Get-ChildItem $O -File | Measure-Object Length -Sum).Sum) / 1MB, 1)) MB)"
exit 0
