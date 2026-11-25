<#
.SYNOPSIS
  Native re-pin check. Agent 4, 2026-11-22: written for S4b at 14:28 (board run 2, task #20); adapted at 19:50 for
  tonight's S4b + S4c build and the one re-pin on native4b (run 2, task #12). See REPIN.md next to this file.

.DESCRIPTION
  DRY RUN BY DEFAULT. Reads the snapshot tree, its native build dir, the staged S4b + S4c inputs and the s35 pack,
  then prints what it finds and what it would do. It writes nothing except the -Report file, which must be under
  build/agent4/.

  Checks:
    [1] the staged files behind the two native fingerprint inputs that change tonight: C1's rexlego file
        (memory_watch.cpp; the v1 rexlego diff, reused by C1 v3) and S4c's rexlego CMakeLists.txt (#24 + #30, both
        OFF); also the C1 v3 SDK diff and S4c's new TU, neither of which is a fingerprint input
    [2] the s35 pack bytes against run-071627/SHA256SUMS.txt
    [3] the tree: memory_watch.cpp (base, C1 applied or other; line ends), CMakeLists.txt (base, S4c or other; #24
        in or not; line ends; the fingerprint input list), gpu_wait_backoff.cpp, shader_archive.cpp, the AOT index
        and the prelinked runtime cache
    [4] the build dir: the cache entries, native-gpu-build.txt == generated/native_gpu_build_info.h, the
        fingerprint recomputed from today's input files (the list in generate-native-gpu-fingerprint.cmake), and
        the expected S4b + S4c fingerprint: the same inputs with memory_watch.cpp and CMakeLists.txt replaced by
        the staged after-files. Once both are in the tree, the recomputed value must equal it; once built, the
        built value must equal the recomputed one and must not be an old pin (5e3ff55de10f4f64 = native4)
    [5] the staged bins' MANIFEST fingerprints (the exe sha256 too with -FullHash); the -BinDir bin must match the
        build dir and, once C1 and S4c are in the tree, must not carry an old pin

  -Go does only the copies listed under WOULD DO. Each copy gets a backup under build/agent4/repin/backup/, a fresh
  LastWriteTime and a sha256 check afterwards. The fresh mtime matters: Copy-Item keeps the source's old mtime,
  and both ninja and the fingerprint rule (CMakeLists.txt:782-790, DEPENDS on the inputs) go by mtime.
    -C1    copies build/agent12/s4-c1/new/.../memory_watch.cpp (70829846...) into the tree, per the landing rule
    -Pack  copies run-071627/runtime-cache.cpp to <tree>/rexlego/out/native-gpu/runtime-cache.cpp, and copies the
           merged index over the tree's index, but only while that index is still the merge base 2DB85917...13A2
  -Go also needs -W4bDone. It refuses while legodimensions.exe runs or while any check FAILs.

  This script never runs cmake, ninja, git, a build or the game, and never writes under build/agent2/*-bin. The
  cmake lines it prints are for Agent 2.

.EXAMPLE
  & .\build\agent4\repin\repin_check.ps1 -Line snap1 -Report build\agent4\repin\dryrun-native4b-1b-HHMM.txt
  Step 1b, after Agent 2's CMake re-run: [3] shows C1 and S4c in the tree, [4] the fingerprint the build must write.
.EXAMPLE
  & .\build\agent4\repin\repin_check.ps1 -Line snap1 -BinDir build\agent2\native4b-bin -FullHash -Report build\agent4\repin\pin-native4b-HHMM.txt
  Step 3, once native4b-bin is staged: the pin record ([4] built = recomputed = expected, [5] MANIFEST = built).
#>
[CmdletBinding()]
param(
    [ValidateSet('snap1', 'snapB3')][string]$Line = 'snap1',
    [string]$Tree = '',
    [string]$BuildDir = '',
    [string]$BinDir = '',
    [switch]$C1,
    [switch]$Pack,
    [switch]$Go,
    [switch]$W4bDone,
    [switch]$FullHash,
    [switch]$NoRecompute,
    [string]$Report = ''
)

$ErrorActionPreference = 'Stop'
if ($Go -and -not $W4bDone) {
    Write-Host 'REFUSED: -Go needs -W4bDone (Agent 1 has announced W4b done and given the S4b GO). Nothing was read or written.'
    exit 2
}

$R = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Abs([string]$p) {
    if ([IO.Path]::IsPathRooted($p)) { return [IO.Path]::GetFullPath($p) }
    return [IO.Path]::GetFullPath((Join-Path $R $p))
}
function Rel([string]$p) {
    if ($p -and $p.StartsWith($R, [StringComparison]::OrdinalIgnoreCase)) { return $p.Substring($R.Length).TrimStart('\', '/') }
    return $p
}
if (-not $Tree) { $Tree = "build/agent2/$Line/DimensionsRecomp" }
if (-not $BuildDir) { $BuildDir = "build/agent2/$Line-on" }
$TreeA = Abs $Tree
$BuildA = Abs $BuildDir

$lines = New-Object System.Collections.Generic.List[string]
$script:nFail = 0
$script:nWarn = 0
function Say([string]$s) { Write-Host $s; $lines.Add($s) }
function Mark([string]$tag, [string]$msg) {
    if ($tag -eq 'FAIL') { $script:nFail++ } elseif ($tag -eq 'WARN') { $script:nWarn++ }
    Say ('  [{0}] {1}' -f $tag, $msg)
}
function Sha([string]$p) {
    if (-not $p -or -not (Test-Path -LiteralPath $p -PathType Leaf)) { return '' }
    return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
}
function S16([string]$h) { if ($h) { return $h.Substring(0, 16) }; return 'missing' }
function Is([string]$h, [string]$prefix, [string]$suffix = '') {
    if (-not $h -or -not $prefix) { return $false }
    return ($h.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -and $h.EndsWith($suffix, [StringComparison]::OrdinalIgnoreCase))
}
function MTime([string]$p) { if ($p -and (Test-Path -LiteralPath $p)) { return (Get-Item -LiteralPath $p).LastWriteTime }; return $null }
function Fmt($t) { if ($t) { return $t.ToString('MM-dd HH:mm:ss') }; return 'missing' }
function Finish([int]$code) {
    Say ''
    Say ('SUMMARY: {0} FAIL, {1} WARN; exit {2}' -f $script:nFail, $script:nWarn, $code)
    if ($Report) {
        [IO.File]::WriteAllLines((Abs $Report), $lines, (New-Object Text.UTF8Encoding($false)))
        Write-Host ('report: {0}' -f (Rel (Abs $Report)))
    }
    exit $code
}

function Eol([string]$p) {
    # @(CRLF count, bare LF count, bytes); @(0, 0, 0) when the file is missing
    if (-not $p -or -not (Test-Path -LiteralPath $p -PathType Leaf)) { return @(0, 0, 0) }
    $b = [IO.File]::ReadAllBytes($p); $c = 0; $n = 0
    for ($i = 0; $i -lt $b.Length; $i++) { if ($b[$i] -eq 10) { if ($i -gt 0 -and $b[$i - 1] -eq 13) { $c++ } else { $n++ } } }
    return @($c, $n, $b.Length)
}

# Records: sha256 prefixes from the staging notes (REPIN.md, Sources).
$MW_BASE = '19AE1606C6DB7273'     # memory_watch.cpp: live = snap1 = build/agent12/s4-c1/orig (166 CRLF, 0 bare LF)
$MW_TARGET = '70829846C4F321A9'   # memory_watch.cpp after C1: build/agent12/s4-c1/new, s4-c1/HASHES.txt (C1 v1, v2 and v3 alike)
$MW_DIFF = '4D0C10794188CF45'     # keep-watch-rexlego.diff (LF only; git apply fails on the CRLF file)
$C1V2_DIFF = '418D3D39947DB146'   # keep-watch-v2.diff (not selected tonight; SDK only)
$C1V3_DIFF = 'DECCFE3373C27C3C'   # keep-watch-v3.diff (tonight's C1; SDK only, not a native fingerprint input)
$CML_BASE = '3690D5D76AA9FBED'    # rexlego/CMakeLists.txt: live = snap1 = S4c's base (885 CRLF)
$CML_S4C = '1BF46D7878BA9A25'     # rexlego/CMakeLists.txt after S4c's s4c-24-30.diff (#24 + #30, both OFF; 907 CRLF)
$S4C_DIFF = 'DC02104EA76E0BF6'    # build/agent9/s4/fence-wait/s4c/s4c-24-30.diff
$WAIT_LF = '01D9F8F3464C8614'     # S4c's new rexlego/src/gpu_wait_backoff.cpp, LF (Xenos builds only; not a fingerprint input)
$WAIT_CRLF = '34D281E006FB5FBE'   # the same text in CRLF form (Agent 9's s4c/HASHES.txt, info)
$ARCHIVE = '1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC'  # shader_archive.cpp in the s35 lookups
$SHADERS_S4A = '9567FE3F3B63637D' # shaders.cpp at the S4a level (#2 miss cache)
$PINS = @{ '335ff2d47268f3a1' = 'native3d (S3d)'; '81d1c3a71be3c096' = 'nativeB (S3d + batch-nolr)'; '5e3ff55de10f4f64' = 'native4 (S4a)'; '9b40acbbef4c57b3' = 'native4b (S4b + S4c)' }
$PACK_HASHES = @('0x75A4D1ABA62F7594', '0xACAF01F01E1C03D2', '0xCCD7655302B54D80', '0xE81FD692C3AB35E1')

$S35 = Abs 'build/agent4/s35/run-071627'
$stMwNew = Abs 'build/agent12/s4-c1/new/game/rexlego/src/gpu_native/memory_watch.cpp'
$stMwOrig = Abs 'build/agent12/s4-c1/orig/game/rexlego/src/gpu_native/memory_watch.cpp'
$stMwDiff = Abs 'build/agent12/s4-c1/keep-watch-rexlego.diff'
$stC1v2 = Abs 'build/agent12/s4-c1v2/keep-watch-v2.diff'
$stC1v3 = Abs 'build/agent12/s4-c1v3/keep-watch-v3.diff'
$stS4c = Abs 'build/agent9/s4/fence-wait/s4c/s4c-24-30.diff'
$stCmlNew = Abs 'build/agent9/s4/fence-wait/s4c/new/rexlego/CMakeLists.txt'
$stWait = Abs 'build/agent9/s4/fence-wait/s4c/new/rexlego/src/gpu_wait_backoff.cpp'
$rex = Join-Path $TreeA 'rexlego'
$tMw = Join-Path $rex 'src\gpu_native\memory_watch.cpp'
$tCml = Join-Path $rex 'CMakeLists.txt'
$tArchive = Join-Path $rex 'src\gpu_native\shader_archive.cpp'
$tShaders = Join-Path $rex 'src\gpu_native\shaders.cpp'
$tIndex = Join-Path $rex 'out\native-gpu\lego-microcode-index.cpp'
$tStub = Join-Path $rex 'out\native-gpu\stubs\runtime-cache.cpp'
$tPackDst = Join-Path $rex 'out\native-gpu\runtime-cache.cpp'
$tLinked = Join-Path $rex 'out\native-gpu\runtime-linked-dxil-cache.cpp'
$tWait = Join-Path $rex 'src\gpu_wait_backoff.cpp'
$liveCml = Abs 'DimensionsRecomp/rexlego/CMakeLists.txt'
$actions = New-Object System.Collections.Generic.List[object]

$modeText = 'DRY RUN: reads only'
if ($Report) { $modeText += ', writes only the report' }
if ($Go) { $modeText = 'GO: the copies under [6], with backups' }
Say ('repin_check.ps1 {0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $modeText)
Say ('  line {0}: tree {1}, build dir {2}, bin dir {3}; planned copies: C1 {4}, pack {5}' -f $Line, (Rel $TreeA), (Rel $BuildA), $(if ($BinDir) { $BinDir } else { '(none)' }), $(if ($C1) { 'yes' } else { 'no' }), $(if ($Pack) { 'yes' } else { 'no' }))
if ($Report -and -not ((Rel (Abs $Report)) -like 'build\agent4\*')) { Write-Host 'REFUSED: -Report must be under build/agent4/'; exit 2 }
foreach ($p in @($TreeA, $BuildA, $rex)) {
    if (-not (Test-Path -LiteralPath $p)) { Mark 'FAIL' ('missing {0}' -f (Rel $p)); Finish 2 }
}

# ---------------------------------------------------------------------------------------------------------------
Say ''
Say '[1] staged S4b + S4c files behind the native fingerprint inputs (sha256 vs the staging records)'
$h = Sha $stMwDiff
Mark $(if (Is $h $MW_DIFF) { 'ok' } else { 'FAIL' }) ('C1 rexlego diff  {0}  {1} (record {2}; v1, reused by C1 v3; LF only, so git apply fails on the CRLF file: copy the after-file)' -f (Rel $stMwDiff), (S16 $h), $MW_DIFF)
$mwNewSha = Sha $stMwNew
$eMwNew = Eol $stMwNew
Mark $(if (Is $mwNewSha $MW_TARGET) { 'ok' } else { 'FAIL' }) ('C1 after-file    {0}  {1} (record {2}), {3} CRLF / {4} bare LF, {5}' -f (Rel $stMwNew), (S16 $mwNewSha), $MW_TARGET, $eMwNew[0], $eMwNew[1], (Fmt (MTime $stMwNew)))
$h = Sha $stMwOrig
Mark $(if (Is $h $MW_BASE) { 'ok' } else { 'FAIL' }) ('C1 before-file   {0}  {1} (record {2})' -f (Rel $stMwOrig), (S16 $h), $MW_BASE)
$h = Sha $stC1v3
Mark $(if (Is $h $C1V3_DIFF) { 'ok' } else { 'WARN' }) ('C1 v3 SDK diff   {0}  {1} (record {2}; tonight''s C1; SDK only, no native fingerprint input)' -f (Rel $stC1v3), (S16 $h), $C1V3_DIFF)
$h = Sha $stC1v2
Mark 'info' ('C1 v2 SDK diff   {0}  {1} (record {2}; not selected tonight)' -f (Rel $stC1v2), (S16 $h), $C1V2_DIFF)
$h = Sha $stS4c
Mark $(if (Is $h $S4C_DIFF) { 'ok' } else { 'FAIL' }) ('S4c diff         {0}  {1} (record {2}; #24 + #30, both OFF: CMakeLists.txt {3} -> {4}, plus the new gpu_wait_backoff.cpp)' -f (Rel $stS4c), (S16 $h), $S4C_DIFF, $CML_BASE.Substring(0, 8), $CML_S4C.Substring(0, 8))
$cmlNewSha = Sha $stCmlNew
$eCmlNew = Eol $stCmlNew
Mark $(if (Is $cmlNewSha $CML_S4C) { 'ok' } else { 'FAIL' }) ('S4c after-file   {0}  {1} (record {2}), {3} B, {4} CRLF / {5} bare LF' -f (Rel $stCmlNew), (S16 $cmlNewSha), $CML_S4C, $eCmlNew[2], $eCmlNew[0], $eCmlNew[1])
$h = Sha $stWait
Mark $(if (Is $h $WAIT_LF) { 'ok' } else { 'WARN' }) ('S4c new TU       {0}  {1} (record {2}; {3} in CRLF form; Xenos builds only, not a fingerprint input)' -f (Rel $stWait), (S16 $h), $WAIT_LF, $WAIT_CRLF.Substring(0, 8))

# ---------------------------------------------------------------------------------------------------------------
Say ''
Say ('[2] s35 pack bytes ({0}) against its SHA256SUMS.txt' -f (Rel $S35))
$sums = @{}
foreach ($l in [IO.File]::ReadAllLines((Join-Path $S35 'SHA256SUMS.txt'))) {
    if ($l -match '^([0-9A-Fa-f]{64})\s+\*?(.+)$') { $sums[$Matches[2].Trim()] = $Matches[1].ToUpper() }
}
foreach ($n in @('runtime-cache.cpp', 'lego-microcode-index.cpp', 'index-addition.cpp')) {
    $h = Sha (Join-Path $S35 $n)
    $rec = $sums[$n]
    Mark $(if ($h -and $rec -and $h -eq $rec) { 'ok' } else { 'FAIL' }) ('{0,-25} {1} (SHA256SUMS {2})' -f $n, (S16 $h), (S16 $rec))
}
$packCacheSha = $sums['runtime-cache.cpp']
$packIndexSha = $sums['lego-microcode-index.cpp']

# ---------------------------------------------------------------------------------------------------------------
Say ''
Say ('[3] tree {0}' -f (Rel $TreeA))
$mwSha = Sha $tMw
$bytes = [IO.File]::ReadAllBytes($tMw)
$crlf = 0; $bare = 0
for ($i = 0; $i -lt $bytes.Length; $i++) { if ($bytes[$i] -eq 10) { if ($i -gt 0 -and $bytes[$i - 1] -eq 13) { $crlf++ } else { $bare++ } } }
$mwState = 'other'
if (Is $mwSha $MW_BASE) { $mwState = 'base' } elseif (Is $mwSha $MW_TARGET) { $mwState = 'applied' }
$mwNote = @{ base = 'the pre-C1 base, so C1 is not applied yet'; applied = 'C1 is applied: the landing hash is met'; other = 'neither base nor target: by the landing rule, copy the staged after-file (-C1)' }[$mwState]
Mark $(if ($mwState -eq 'other') { 'WARN' } else { 'ok' }) ('memory_watch.cpp {0}, {1} B, {2} CRLF / {3} bare LF, {4}: {5}' -f (S16 $mwSha), $bytes.Length, $crlf, $bare, (Fmt (MTime $tMw)), $mwNote)
if ($mwState -eq 'applied' -and (MTime $tMw) -eq (MTime $stMwNew)) {
    Mark 'WARN' 'memory_watch.cpp has the staged file''s own mtime (a plain copy): set its LastWriteTime to now before building, or ninja and the fingerprint rule can miss it'
}
if ($C1) {
    if ($mwState -eq 'applied') { Say '  (C1 copy not needed: the tree is already at the target)' }
    else { $actions.Add(@{ What = 'C1 landing copy, memory_watch.cpp to 70829846'; Src = $stMwNew; Dst = $tMw; Expect = $mwNewSha }) }
}

$cml = [IO.File]::ReadAllLines($tCml)
$s = -1; $e = -1
for ($i = 0; $i -lt $cml.Length; $i++) {
    if ($s -lt 0 -and $cml[$i] -match '^\s*set\(\s*LEGO_NATIVE_GPU_FINGERPRINT_INPUTS\b') { $s = $i }
    if ($s -ge 0 -and $cml[$i] -match 'list\(\s*REMOVE_DUPLICATES\s+LEGO_NATIVE_GPU_FINGERPRINT_INPUTS') { $e = $i; break }
}
$cmlSha = Sha $tCml
$liveSha = Sha $liveCml
$eCml = Eol $tCml
$cmlState = 'other'
if (Is $cmlSha $CML_BASE) { $cmlState = 'base' } elseif (Is $cmlSha $CML_S4C) { $cmlState = 's4c' }
$waitIn = @($cml | Where-Object { $_ -match 'gpu_wait_backoff' }).Count
$cmlNote = @{ base = 'the S4c base, so S4c is not applied yet'; s4c = 'S4c is applied (#24 + #30, both OFF)'; other = ('neither the S4c base {0} nor S4c''s {1}' -f $CML_BASE.Substring(0, 8), $CML_S4C.Substring(0, 8)) }[$cmlState]
Mark $(if ($cmlState -eq 'other') { 'WARN' } else { 'ok' }) ('CMakeLists.txt {0}, {1} B, {2} CRLF / {3} bare LF, {4}: {5}; live {6} ({7}); gpu_wait_backoff on {8} line(s), so #24 is {9}' -f (S16 $cmlSha), $eCml[2], $eCml[0], $eCml[1], (Fmt (MTime $tCml)), $cmlNote, (S16 $liveSha), $(if ($cmlSha -eq $liveSha) { 'same' } else { 'differs' }), $waitIn, $(if ($waitIn -gt 0) { 'in' } else { 'not in yet' }))
if ($cmlState -eq 's4c' -and (MTime $tCml) -eq (MTime $stCmlNew)) {
    Mark 'WARN' 'CMakeLists.txt has the staged file''s own mtime (a plain copy): set its LastWriteTime to now before building, or CMake and the fingerprint rule can miss it'
}
$waitSha = Sha $tWait
$waitState = 'absent'
if ($waitSha) { if (Is $waitSha $WAIT_LF) { $waitState = 'the staged text, LF' } elseif (Is $waitSha $WAIT_CRLF) { $waitState = 'the staged text, CRLF' } else { $waitState = 'other' } }
$waitTag = 'info'; $waitNote = ''
if ($waitIn -gt 0 -and -not $waitSha) { $waitTag = 'WARN'; $waitNote = ': #24 is in CMakeLists.txt but the TU is missing, so the OFF build fails (the native build skips it)' }
elseif ($waitState -eq 'other') { $waitTag = 'WARN'; $waitNote = ': not the staged TU' }
elseif ($waitSha) { $waitTag = 'ok' }
Mark $waitTag ('src/gpu_wait_backoff.cpp {0} ({1}){2}' -f (S16 $waitSha), $waitState, $waitNote)
$applied = ($mwState -eq 'applied' -and $cmlState -eq 's4c')
if ($s -lt 0 -or $e -lt 0) { Mark 'FAIL' 'CMakeLists.txt: the LEGO_NATIVE_GPU_FINGERPRINT_INPUTS block (set ... REMOVE_DUPLICATES) was not found' }
else {
    $blk = $cml[$s..$e]
    $fCml = @($blk | Where-Object { $_ -match 'CMakeLists\.txt' }).Count -gt 0
    $fMw = @($blk | Where-Object { $_ -match 'memory_watch\.cpp' }).Count -gt 0
    $fWait = @($blk | Where-Object { $_ -match 'gpu_wait_backoff' }).Count -gt 0
    Mark $(if ($fCml -and $fMw) { 'ok' } else { 'FAIL' }) ('fingerprint input list, CMakeLists.txt:{0}-{1}: CMakeLists.txt {2}, memory_watch.cpp {3}, gpu_wait_backoff {4}; so C1 and #24 each change the fingerprint' -f ($s + 1), ($e + 1), $(if ($fCml) { 'listed' } else { 'NOT listed' }), $(if ($fMw) { 'listed' } else { 'NOT listed' }), $(if ($fWait) { 'listed' } else { 'not listed' }))
}

$h = Sha $tArchive
if ($h -eq $ARCHIVE) { Mark 'ok' ('shader_archive.cpp {0} = the archive the s35 lookups compiled' -f (S16 $h)) }
else { Mark $(if ($Pack) { 'WARN' } else { 'info' }) ('shader_archive.cpp {0} is not the 1C5B1767 of the s35 lookups: re-run the lookups (REPIN.md step 5) before trusting the pack' -f (S16 $h)) }
$h = Sha $tShaders
Mark 'info' ('shaders.cpp {0} ({1})' -f (S16 $h), $(if (Is $h $SHADERS_S4A) { 'the S4a level, with the #2 miss cache' } else { 'not the S4a level 9567FE3F' }))

$ixSha = Sha $tIndex
$ixState = 'other'
if (Is $ixSha '2DB85917' '13A2') { $ixState = 'base' } elseif ($ixSha -and $ixSha -eq $packIndexSha) { $ixState = 'pack' }
$ixNote = @{ base = 'the s35 merge base 2DB85917...13A2, so the merged index can be copied'; pack = 'the s35 merged index E4C05782...0617 is in'; other = 'neither the merge base nor the s35 index: re-merge index-addition.cpp (6 rows), do not copy' }[$ixState]
Mark $(if ($ixState -eq 'other' -and $Pack) { 'WARN' } else { 'ok' }) ('lego-microcode-index.cpp {0}, {1} B, {2}: {3}' -f (S16 $ixSha), (Get-Item -LiteralPath $tIndex).Length, (Fmt (MTime $tIndex)), $ixNote)
if ($ixState -eq 'pack' -and (MTime $tIndex) -eq (MTime (Join-Path $S35 'lego-microcode-index.cpp'))) {
    Mark 'WARN' 'lego-microcode-index.cpp has the s35 file''s own mtime (a plain copy): set its LastWriteTime to now before building'
}

# ---------------------------------------------------------------------------------------------------------------
Say ''
Say ('[4] build dir {0}' -f (Rel $BuildA))
$ccl = [IO.File]::ReadAllLines((Join-Path $BuildA 'CMakeCache.txt'))
function CacheVal([string]$name) {
    foreach ($l in $ccl) { if ($l.StartsWith($name + ':')) { return $l.Substring($l.IndexOf('=') + 1) } }
    return $null
}
$homeDir = CacheVal 'CMAKE_HOME_DIRECTORY'
$ngpu = CacheVal 'LEGODIMENSIONS_NATIVE_GPU'
$bank = CacheVal 'LEGO_NATIVE_RUNTIME_PRELINKED_BANK'
$rsc = CacheVal 'LEGO_NATIVE_RUNTIME_SHADER_CACHE'
$homeOk = ($homeDir -and ([IO.Path]::GetFullPath($homeDir) -ieq $rex))
Mark $(if ($homeOk -and $ngpu -eq 'ON') { 'ok' } else { 'FAIL' }) ('CMAKE_HOME_DIRECTORY {0}; LEGODIMENSIONS_NATIVE_GPU={1}' -f $(if ($homeOk) { 'is this tree''s rexlego' } else { 'is NOT this tree: ' + $homeDir }), $ngpu)
$bankEmpty = [string]::IsNullOrEmpty($bank)
Mark $(if ($bankEmpty) { 'ok' } else { 'WARN' }) ('LEGO_NATIVE_RUNTIME_PRELINKED_BANK="{0}": {1}' -f $bank, $(if ($bankEmpty) { 'empty, so the build re-runs lego_gpu_prelink_runtime, which the pack needs' } else { 'set, so the pack''s DXIL libraries would not be prelinked: clear it for a pack build' }))
$rscA = ''
if ($rsc) { $rscA = [IO.Path]::GetFullPath($rsc) }
$rscSha = Sha $rscA
$cacheState = 'other'
if ($rscA -and $rscA -ieq $tStub) { $cacheState = 'stub' } elseif ($rscSha -and $rscSha -eq $packCacheSha) { $cacheState = 'pack' }
Mark $(if ($cacheState -eq 'other') { 'WARN' } else { 'ok' }) ('LEGO_NATIVE_RUNTIME_SHADER_CACHE = {0} ({1}, {2}): {3}' -f (Rel $rscA), (S16 $rscSha), (Fmt (MTime $rscA)), @{ stub = 'the stub, no pack'; pack = 'the s35 runtime cache'; other = 'neither the stub nor the s35 cache' }[$cacheState])
if ($Pack -and $cacheState -ne 'pack') {
    if ((Test-Path -LiteralPath $tPackDst) -and (Sha $tPackDst) -eq $packCacheSha) { Say ('  (the s35 cache is already at {0}; only the cmake -D line is missing)' -f (Rel $tPackDst)) }
    else { $actions.Add(@{ What = 's35 runtime cache copy'; Src = (Join-Path $S35 'runtime-cache.cpp'); Dst = $tPackDst; Expect = $packCacheSha }) }
}
if ($Pack -and $ixState -eq 'base') { $actions.Add(@{ What = 's35 merged index over the merge base'; Src = (Join-Path $S35 'lego-microcode-index.cpp'); Dst = $tIndex; Expect = $packIndexSha }) }

$lk = [IO.File]::ReadAllText($tLinked)
$m = [regex]::Match($lk, 'g_linkedShaderCacheEntryCount\s*=\s*(\d+)')
$nLinked = -1
if ($m.Success) { $nLinked = [int]$m.Groups[1].Value }
$have = @($PACK_HASHES | Where-Object { $lk.Contains('{ ' + $_ + ',') })
$lkInfo = 'runtime-linked-dxil-cache.cpp {0} B, {1}: {2} entries, {3} of the 4 pack hashes' -f (Get-Item -LiteralPath $tLinked).Length, (Fmt (MTime $tLinked)), $nLinked, $have.Count
if ($cacheState -eq 'stub') {
    if ($nLinked -eq 0) { Mark 'ok' ($lkInfo + '; no pack, consistent with the stub cache') }
    else { Mark 'WARN' ($lkInfo + '; left over from a pack build: the next build regenerates it from the stub') }
}
elseif ($cacheState -eq 'pack') {
    if ($have.Count -eq 4 -and $nLinked -ge 4) { Mark 'ok' ($lkInfo + '; the pack is prelinked') }
    elseif ((MTime $tLinked) -lt (MTime $rscA)) { Mark 'WARN' ($lkInfo + '; older than the configured cache, so a build is pending') }
    else { Mark 'FAIL' ($lkInfo + '; newer than the configured s35 cache but without all 4 pack hashes') }
}
else { Mark 'WARN' $lkInfo }

$ngb = Join-Path $BuildA 'native-gpu-build.txt'
$hdr = Join-Path $BuildA 'generated\native_gpu_build_info.h'
$fpTxt = ''; $fpHdr = ''
if (Test-Path -LiteralPath $ngb) { $m = [regex]::Match([IO.File]::ReadAllText($ngb), 'native GPU ([0-9a-f]{16})'); if ($m.Success) { $fpTxt = $m.Groups[1].Value } }
if (Test-Path -LiteralPath $hdr) { $m = [regex]::Match([IO.File]::ReadAllText($hdr), 'kNativeGpuBuildFingerprint\[\]\s*=\s*"([0-9a-f]{16})"'); if ($m.Success) { $fpHdr = $m.Groups[1].Value } }
$pinName = 'not a current pin'
if ($fpTxt -and $PINS.ContainsKey($fpTxt)) { $pinName = 'the ' + $PINS[$fpTxt] + ' pin' }
Mark $(if ($fpTxt -and $fpTxt -eq $fpHdr) { 'ok' } else { 'FAIL' }) ('built fingerprint: native-gpu-build.txt {0} ({1}), native_gpu_build_info.h {2}; {3}' -f $fpTxt, (Fmt (MTime $ngb)), $fpHdr, $pinName)

$fpScript = Join-Path $BuildA 'generate-native-gpu-fingerprint.cmake'
if ($NoRecompute) { Say '  (fingerprint recompute skipped: -NoRecompute)' }
elseif (-not (Test-Path -LiteralPath $fpScript)) { Mark 'WARN' 'generate-native-gpu-fingerprint.cmake is missing, so the fingerprint cannot be recomputed' }
else {
    $first = @([IO.File]::ReadAllLines($fpScript) | Where-Object { $_ -match '^set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "' })[0]
    $list = @(([regex]::Match($first, '^set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "(.*)"\)\s*$')).Groups[1].Value.Split(';') | Where-Object { $_ })
    $sbNow = New-Object Text.StringBuilder
    $sbC1 = New-Object Text.StringBuilder
    $sbExp = New-Object Text.StringBuilder
    $missing = @(); $newest = $null; $newestName = ''; $t0 = Get-Date; $mwListed = $false; $cmlListed = $false
    foreach ($inp in $list) {
        $p = [IO.Path]::GetFullPath($inp.Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { $missing += $p; continue }
        $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
        [void]$sbNow.Append($h)
        if ($p -ieq $tMw) { $mwListed = $true; [void]$sbC1.Append($mwNewSha.ToLower()); [void]$sbExp.Append($mwNewSha.ToLower()) }
        elseif ($p -ieq $tCml) { $cmlListed = $true; [void]$sbC1.Append($h); [void]$sbExp.Append($cmlNewSha.ToLower()) }
        else { [void]$sbC1.Append($h); [void]$sbExp.Append($h) }
        $mt = (Get-Item -LiteralPath $p).LastWriteTime
        if (-not $newest -or $mt -gt $newest) { $newest = $mt; $newestName = $p }
    }
    $hasher = [Security.Cryptography.SHA256]::Create()
    $fpNow = (-join ($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($sbNow.ToString())) | ForEach-Object { $_.ToString('x2') })).Substring(0, 16)
    $fpC1 = (-join ($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($sbC1.ToString())) | ForEach-Object { $_.ToString('x2') })).Substring(0, 16)
    $fpExp = (-join ($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($sbExp.ToString())) | ForEach-Object { $_.ToString('x2') })).Substring(0, 16)
    $secs = ((Get-Date) - $t0).TotalSeconds
    $ngbT = MTime $ngb
    if ($missing.Count -gt 0) { Mark 'WARN' ('{0} fingerprint input(s) missing, first {1}: the next fingerprint run fails' -f $missing.Count, (Rel $missing[0])) }
    $newer = ($newest -and $ngbT -and $newest -gt $ngbT)
    if ($fpNow -eq $fpTxt) {
        Mark 'ok' ('recomputed fingerprint {0} from {1} inputs ({2:n1} s) = built: the build dir is fresh; newest input {3} ({4})' -f $fpNow, $list.Count, $secs, (Rel $newestName), (Fmt $newest))
    }
    elseif ($newer) {
        Mark 'info' ('recomputed fingerprint {0} from {1} inputs ({2:n1} s) != built {3}: inputs changed and {4} ({5}) is newer than native-gpu-build.txt, so the next build writes {0}' -f $fpNow, $list.Count, $secs, $fpTxt, (Rel $newestName), (Fmt $newest))
    }
    else {
        Mark 'FAIL' ('recomputed fingerprint {0} != built {1}, but no input is newer than native-gpu-build.txt ({2}): a copied input kept an old mtime, so ninja would not re-run the fingerprint. Touch the changed input(s), then build' -f $fpNow, $fpTxt, (Fmt $ngbT))
    }
    if ($mwListed -and $cmlListed) {
        $expMsg = 'expected S4b + S4c fingerprint {0}: the inputs as they are now, with memory_watch.cpp = the staged {1} and CMakeLists.txt = the staged {2}' -f $fpExp, $MW_TARGET.Substring(0, 8), $CML_S4C.Substring(0, 8)
        if ($applied) {
            if ($fpNow -eq $fpExp) { Mark 'ok' ($expMsg + '; the tree recomputes to the same value, so C1 and S4c are the only input changes') }
            else { Mark 'WARN' ($expMsg + '; the tree recomputes to ' + $fpNow + ', so another fingerprint input changed too: find it before pinning') }
        }
        else { Mark 'info' ($expMsg + $(if ($mwState -eq 'base' -and $cmlState -eq 'base') { '; C1 alone would give ' + $fpC1 } else { '' })) }
    }
    else { Mark 'WARN' ('the generated input list has memory_watch.cpp: {0}, CMakeLists.txt: {1}; the expected fingerprint needs both' -f $mwListed, $cmlListed) }
    if ($applied -and $fpTxt -and $fpNow -eq $fpTxt) {
        if ($PINS.ContainsKey($fpTxt)) { Mark 'FAIL' ('built fingerprint {0} is an old pin ({1}) although C1 and S4c are in the tree' -f $fpTxt, $PINS[$fpTxt]) }
        else { Mark 'ok' ('built fingerprint {0} is new: not 5e3ff55de10f4f64 (native4) or another old pin' -f $fpTxt) }
    }
}

$objDir = Join-Path $BuildA 'CMakeFiles\legodimensions.dir'
foreach ($pr in @(@('src\gpu_native\memory_watch.cpp.obj', $tMw), @('out\native-gpu\lego-microcode-index.cpp.obj', $tIndex), @('src\gpu_native\runtime_shader_cache.cpp.obj', $rscA), @('src\gpu_native\runtime_linked_shader_cache.cpp.obj', $tLinked))) {
    $ot = MTime (Join-Path $objDir $pr[0])
    $srcT = MTime $pr[1]
    if (-not $ot) { Mark 'info' ('{0}: no object yet' -f $pr[0]); continue }
    if ($srcT -and $srcT -gt $ot) { Mark 'info' ('{0} {1} is older than its source ({2}): the next build recompiles it' -f $pr[0], (Fmt $ot), (Fmt $srcT)) }
    else { Mark 'ok' ('{0} {1}, source {2}' -f $pr[0], (Fmt $ot), (Fmt $srcT)) }
}

# ---------------------------------------------------------------------------------------------------------------
Say ''
Say '[5] staged bins: MANIFEST fingerprints (read-only)'
$oldBins = @('build/agent2/native3d-bin', 'build/agent2/nativeB-bin', 'build/agent2/native4-bin')
$oldBinsA = @($oldBins | ForEach-Object { (Abs $_).ToLower() })
$bins = @($oldBins)
if ($BinDir) { $bins += $BinDir }
$seen = @{}
foreach ($bd in $bins) {
    $bdA = Abs $bd
    if ($seen.ContainsKey($bdA.ToLower())) { continue }
    $seen[$bdA.ToLower()] = $true
    $isTarget = ($BinDir -and $bdA -ieq (Abs $BinDir))
    $isOldBin = ($oldBinsA -contains $bdA.ToLower())
    $man = Join-Path $bdA 'MANIFEST.txt'
    if (-not (Test-Path -LiteralPath $man)) { Mark $(if ($isTarget) { 'WARN' } else { 'info' }) ('{0}: no MANIFEST.txt' -f $bd); continue }
    $m = [regex]::Match([IO.File]::ReadAllText($man), 'native GPU ([0-9a-f]{16})')
    $fpMan = ''
    if ($m.Success) { $fpMan = $m.Groups[1].Value }
    $exeNote = ''
    if ($FullHash) { $exeNote = ', exe ' + (S16 (Sha (Join-Path $bdA 'legodimensions.exe'))) }
    if ($isTarget) {
        $same = ($fpMan -and $fpMan -eq $fpTxt)
        $oldPin = ($fpMan -and $PINS.ContainsKey($fpMan))
        $tag = $(if ($same) { 'ok' } else { 'WARN' })
        if ($oldPin -and $applied) { $tag = $(if ($isOldBin) { 'info' } else { 'FAIL' }) }
        Mark $tag ('{0}: MANIFEST {1}, fingerprint {2}{3}; {4}{5}' -f $bd, (S16 (Sha $man)), $fpMan, $exeNote, $(if ($same) { 'the same as the build dir' } else { 'not the build dir''s ' + $fpTxt + ' (staged from another build, or the build dir moved on)' }), $(if ($oldPin) { '; an old pin (' + $PINS[$fpMan] + ')' + $(if ($applied -and $isOldBin) { '; a frozen old-pin bin, and the tree has moved on (C1 and S4c are in it)' } elseif ($applied) { ', but C1 and S4c are in the tree' } else { '' }) } else { '; not an old pin' }))
    }
    else { Mark 'info' ('{0}: MANIFEST {1}, fingerprint {2}{3}' -f $bd, (S16 (Sha $man)), $fpMan, $exeNote) }
}

# ---------------------------------------------------------------------------------------------------------------
Say ''
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$bk = Abs ('build/agent4/repin/backup/{0}-{1}' -f $stamp, $Line)
if ($actions.Count -eq 0) {
    Say '[6] WOULD DO: no copies (add -C1 and/or -Pack to plan them, or they are already done)'
}
else {
    Say ('[6] {0}' -f $(if ($Go) { 'DOING:' } else { 'WOULD DO with -Go -W4bDone:' }))
    foreach ($a in $actions) {
        Say ('  - {0}: copy {1} -> {2}; back up the old file to {3}; set LastWriteTime to now; then sha256 must be {4}' -f $a.What, (Rel $a.Src), (Rel $a.Dst), (Rel $bk), (S16 $a.Expect))
    }
}
Say '  Not done by this script (Agent 2, after Agent 1''s GO):'
if ($Pack) {
    Say ('    cmake -D LEGO_NATIVE_RUNTIME_SHADER_CACHE={0} {1}' -f $tPackDst.Replace('\', '/'), (Rel $BuildA).Replace('\', '/'))
}
Say '    the usual native build of this build dir (it re-runs lego_gpu_prelink_runtime and the fingerprint), staged to a NEW bin folder; native4-bin and the other bins stay untouched'
Say '    then this script again without -Go: [4] must show a fresh fingerprint, and with -Pack all 4 pack hashes in the prelinked cache'
Say ('  Rollback: copy the files in the backup folder back (then set their LastWriteTime to now){0}' -f $(if ($Pack) { ('; cmake -D LEGO_NATIVE_RUNTIME_SHADER_CACHE={0} {1}' -f $tStub.Replace('\', '/'), (Rel $BuildA).Replace('\', '/')) } else { '' }))

if ($Go -and $actions.Count -gt 0) {
    if ($script:nFail -gt 0) { Say 'REFUSED: fix the FAIL lines first; nothing was copied.'; Finish 2 }
    if (Get-Process -Name legodimensions -ErrorAction SilentlyContinue) { Say 'REFUSED: legodimensions.exe is running; nothing was copied.'; Finish 2 }
    foreach ($a in $actions) {
        if ((Rel $a.Dst) -match '^build\\agent2\\[^\\]+-bin(\\|$)') { Say ('REFUSED: {0} is inside a staged bin folder' -f (Rel $a.Dst)); Finish 2 }
        if ((Sha $a.Src) -ne $a.Expect) { Mark 'FAIL' ('source {0} no longer matches {1}; stopped' -f (Rel $a.Src), (S16 $a.Expect)); Finish 1 }
    }
    New-Item -ItemType Directory -Force -Path $bk | Out-Null
    foreach ($a in $actions) {
        $bdst = ''
        if (Test-Path -LiteralPath $a.Dst) {
            $bdst = Join-Path $bk (Rel $a.Dst)
            New-Item -ItemType Directory -Force -Path (Split-Path $bdst) | Out-Null
            Copy-Item -LiteralPath $a.Dst -Destination $bdst
        }
        Copy-Item -LiteralPath $a.Src -Destination $a.Dst -Force
        (Get-Item -LiteralPath $a.Dst).LastWriteTime = Get-Date
        $after = Sha $a.Dst
        if ($after -ne $a.Expect) {
            if ($bdst) { Copy-Item -LiteralPath $bdst -Destination $a.Dst -Force; (Get-Item -LiteralPath $a.Dst).LastWriteTime = Get-Date }
            Mark 'FAIL' ('{0}: sha256 after the copy is {1}, not {2}; the old file was restored' -f (Rel $a.Dst), (S16 $after), (S16 $a.Expect))
            Finish 1
        }
        Mark 'ok' ('{0}: {1} is now {2}; backup {3}' -f $a.What, (Rel $a.Dst), (S16 $after), $(if ($bdst) { Rel $bdst } else { '(none: new file)' }))
    }
    [IO.File]::WriteAllLines((Join-Path $bk 'GO-LOG.txt'), $lines, (New-Object Text.UTF8Encoding($false)))
}

Finish $(if ($script:nFail -gt 0) { 1 } else { 0 })
