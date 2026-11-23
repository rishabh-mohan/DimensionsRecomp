<#
.SYNOPSIS
  Compile-check rexlego/src translation units with the shipped Release flags.
  It compiles objects only and never links.

  DRAFT, written 2026-11-21 with no toolchain available. It has NOT been run.
  The design is in perf-notes/agent3-build.md, section 1.

.DESCRIPTION
  1. Dot-sources env/devshell.ps1 (Agent 2's toolchain).
  2. Installs harness/stub-generated into DimensionsRecomp/rexlego/generated.
     generated/ is gitignored. A real generated/ (one without the marker file) is never touched.
  3. Configures rexlego once into build/agent3/rexlego-cfg[-gpu]. It uses the installed SDK
     through find_package and passes CMAKE_EXPORT_COMPILE_COMMANDS=ON.
  4. Turns compile_commands.json into a small check.ninja. That file holds only the selected
     TUs plus their PCH, with objects redirected to -OutDir. It runs outside CMake's graph, so
     an object compile never triggers the DXC, prelink or cache custom commands.
  5. Runs ninja -j<=4 -k 0, then prints PASS or FAIL per TU. It exits 1 if any TU failed.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness/check-rexlego.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness/check-rexlego.ps1 -Files src/main.cpp,src/native_lock_elide.cpp -OutDir build/agent4/check
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File harness/check-rexlego.ps1 -NativeGpu   # needs harness/stubs/native-gpu + plume/FidelityFX submodules
#>
[CmdletBinding()]
param(
    # rexlego/src files to check. Paths can be relative to rexlego/ or absolute.
    # If omitted, every TU in compile_commands.json under rexlego/src is checked.
    [string[]]$Files,
    # Object/log directory. Relative paths resolve against games/lego-dimensions-recomp.
    [string]$OutDir,
    [ValidateRange(1, 4)][int]$Jobs = 4,
    [switch]$NativeGpu,
    [switch]$Reconfigure,
    # This is the shipped baseline (README.md:431-436). rexlego/CMakeLists.txt:840 still defaults to v3.
    [string]$Baseline = 'x86-64-v2'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot                     # games/lego-dimensions-recomp
$Game = Join-Path $Root 'DimensionsRecomp'
$Lego = Join-Path $Game 'rexlego'
$Gen = Join-Path $Lego 'generated'
$StubSrc = Join-Path $PSScriptRoot 'stub-generated'
$Marker = '.rexlego-compile-check-stub'
$SdkInstall = Join-Path $Root 'build\sdk\install'
$Cfg = Join-Path $Root ('build\agent3\rexlego-cfg' + $(if ($NativeGpu) { '-gpu' } else { '' }))
if (-not $OutDir) { $OutDir = Join-Path $Root 'build\agent3\check' }
elseif (-not [IO.Path]::IsPathRooted($OutDir)) { $OutDir = Join-Path $Root $OutDir }
$OutDir = [IO.Path]::GetFullPath($OutDir)

function Norm([string]$p) { [IO.Path]::GetFullPath($p).Replace('\', '/').ToLowerInvariant() }

if ($Root -match ' ' -or $OutDir -match ' ') {
    Write-Warning 'Path contains a space; Ninja depfile tracking breaks on spaces (README-dev).'
}

# 1. Toolchain
$devshell = Join-Path $Root 'env\devshell.ps1'
if (-not (Test-Path $devshell)) { throw "env/devshell.ps1 not found (Agent 2 provides it)" }
. $devshell
foreach ($tool in 'cmake', 'ninja', 'clang++') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "$tool not on PATH after devshell" }
}
if (-not (Test-Path (Join-Path $SdkInstall 'lib\cmake\rexglue'))) {
    Write-Warning "SDK install not found under $SdkInstall\lib\cmake\rexglue; configure will probably fail"
}

# 2. The generated/ stub
if ((Test-Path (Join-Path $Gen 'rexglue.cmake')) -and -not (Test-Path (Join-Path $Gen $Marker))) {
    Write-Host "Using the real rexlego/generated (no $Marker marker)."
} else {
    if (-not (Test-Path (Join-Path $StubSrc $Marker))) {
        throw "harness/stub-generated is missing or has no marker; see perf-notes/agent3-build.md 1.2"
    }
    robocopy $StubSrc $Gen /MIR /NJH /NJS /NFL /NDL /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy of the stub failed ($LASTEXITCODE)" }
    $global:LASTEXITCODE = 0
}

# 3. Configure (cached)
$cc = Join-Path $Cfg 'compile_commands.json'
$needCfg = $Reconfigure -or -not (Test-Path $cc)
if (-not $needCfg) {
    $ccTime = (Get-Item $cc).LastWriteTimeUtc
    foreach ($f in (Join-Path $Lego 'CMakeLists.txt'), (Join-Path $Gen 'rexglue.cmake')) {
        if ((Get-Item $f).LastWriteTimeUtc -gt $ccTime) { $needCfg = $true }
    }
}
if ($needCfg) {
    $cmakeArgs = @('-S', $Lego, '-B', $Cfg, '-G', 'Ninja',
        '-DCMAKE_BUILD_TYPE=Release',                 # always explicit: a failed reconfigure blanks it
        '-DCMAKE_C_COMPILER=clang', '-DCMAKE_CXX_COMPILER=clang++',
        "-DCMAKE_PREFIX_PATH=$SdkInstall",
        '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
        "-DLEGODIMENSIONS_X86_BASELINE=$Baseline",
        "-DLEGODIMENSIONS_NATIVE_GPU=$(if ($NativeGpu) { 'ON' } else { 'OFF' })")
    if ($NativeGpu) {
        $s = Join-Path $PSScriptRoot 'stubs\native-gpu'
        $dxc = 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\dxc.exe'
        # LEGO_NATIVE_MICROCODE_INDEX only takes effect once CMakeLists.txt:274 is a CACHE FILEPATH (report 3.9).
        $cmakeArgs += @(
            "-DLEGO_TEMPORAL_SHADER_BANK=$s\temporal",
            "-DLEGO_FLOAT_BLEND_INDICES_BANK=$s\float-blend-indices-bank",
            "-DLEGO_NATIVE_SHADER_CACHE=$s\lego-dxil-cache.cpp",
            "-DLEGO_NATIVE_MICROCODE_INDEX=$s\lego-microcode-index.cpp",
            "-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=$s\runtime-cache.cpp",
            "-DLEGO_NATIVE_FIDELITYFX_RUNTIME=$s\fidelityfx-stub.dll",
            '-DLEGO_NATIVE_BINARY_CACHE=OFF',
            "-DLEGO_HOST_DXC_EXECUTABLE=$dxc")
    }
    & cmake @cmakeArgs
    if ($LASTEXITCODE -ne 0) { throw "cmake configure failed ($LASTEXITCODE)" }
}

# 4. Build-time headers (NativeGpu only). Build only the generated *.h outputs from CMake's own graph.
if ($NativeGpu) {
    $hdrs = & ninja -C $Cfg -t targets all | ForEach-Object { ($_ -split ':')[0] } |
        Where-Object { $_ -match '^generated[/\\].*\.h$' }
    if ($hdrs) {
        & ninja -C $Cfg "-j$Jobs" @hdrs
        if ($LASTEXITCODE -ne 0) { throw 'generating build-time headers failed' }
    }
}

# 5. compile_commands.json -> check.ninja
function Split-Cmd([string]$s) {
    $tokens = New-Object System.Collections.Generic.List[string]
    $cur = New-Object System.Text.StringBuilder
    $inQ = $false
    foreach ($ch in $s.ToCharArray()) {
        if ($ch -eq '"') { $inQ = -not $inQ; [void]$cur.Append($ch); continue }
        if (-not $inQ -and [char]::IsWhiteSpace($ch)) {
            if ($cur.Length) { $tokens.Add($cur.ToString()); [void]$cur.Clear() }
            continue
        }
        [void]$cur.Append($ch)
    }
    if ($cur.Length) { $tokens.Add($cur.ToString()) }
    return , $tokens
}
function Esc-Path([string]$p) { $p.Replace('\', '/').Replace('$', '$$').Replace(' ', '$ ').Replace(':', '$:') }
function Esc-Val([string]$v) { $v.Replace('$', '$$') }

$entries = Get-Content $cc -Raw | ConvertFrom-Json
$srcRoot = (Norm (Join-Path $Lego 'src')) + '/'
$wanted = $null
if ($Files) {
    $wanted = @{}
    foreach ($f in $Files) {
        $p = if ([IO.Path]::IsPathRooted($f)) { $f } else { Join-Path $Lego $f }
        $wanted[(Norm $p)] = $true
    }
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('ninja_required_version = 1.10')
[void]$sb.AppendLine("builddir = $(Esc-Path $OutDir)")
foreach ($r in 'cc', 'pch') {
    [void]$sb.AppendLine("rule $r")
    [void]$sb.AppendLine('  command = $cmd')
    [void]$sb.AppendLine("  description = $($r.ToUpper()) `$src")
    [void]$sb.AppendLine('  deps = gcc')
    [void]$sb.AppendLine('  depfile = $out.d')
}

$tus = @()
$pchEdges = @{}
foreach ($e in $entries) {
    $file = Norm $e.file
    $isPch = $file -like '*/cmake_pch.hxx.cxx'
    if (-not $isPch) {
        if (-not $file.StartsWith($srcRoot)) { continue }
        if ($wanted -and -not $wanted.ContainsKey($file)) { continue }
    }
    $cmdText = if ($e.command) { $e.command } else { ($e.arguments | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' ' }
    $tok = Split-Cmd $cmdText
    $keep = New-Object System.Collections.Generic.List[string]
    $origOut = $null; $pchUse = $null
    for ($i = 0; $i -lt $tok.Count; $i++) {
        $t = $tok[$i]
        if ($t -in '-MD', '-MMD') { continue }
        if ($t -in '-MF', '-MT', '-MQ') { $i++; continue }
        if ($t -eq '-o') { $origOut = $tok[$i + 1].Trim('"'); $i++; continue }
        if ($t -eq '-include-pch' -and $i + 2 -lt $tok.Count) { $pchUse = $tok[$i + 2].Trim('"') }
        $keep.Add($t)
    }
    if ($pchUse -and -not [IO.Path]::IsPathRooted($pchUse)) { $pchUse = Join-Path $e.directory $pchUse }
    if ($isPch) {
        # The .pch stays where CMake expects it, because TUs reference that path.
        $out = if ([IO.Path]::IsPathRooted($origOut)) { $origOut } else { Join-Path $e.directory $origOut }
        $pchEdges[(Norm $out)] = @{ out = $out; src = $e.file; dir = $e.directory; tok = $keep }
        continue
    }
    $rel = $file.Substring($srcRoot.Length) -replace '[/:]', '_'
    $out = Join-Path $OutDir ($rel + '.obj')
    $tus += @{ out = $out; src = $e.file; dir = $e.directory; tok = $keep; pch = $pchUse }
}
if (-not $tus) { throw 'No matching rexlego/src entries in compile_commands.json' }

$usedPch = @{}
foreach ($t in $tus) { if ($t.pch) { $usedPch[(Norm $t.pch)] = $true } }
$edgeList = @()
foreach ($k in $pchEdges.Keys) { if ($usedPch.ContainsKey($k)) { $edgeList += @{ rule = 'pch'; e = $pchEdges[$k] } } }
foreach ($t in $tus) { $edgeList += @{ rule = 'cc'; e = $t } }
foreach ($x in $edgeList) {
    $e = $x.e
    $cmd = ($e.tok -join ' ') + " -MD -MF `"$($e.out).d`" -o `"$($e.out)`""
    if ((Norm $e.dir) -ne (Norm $Cfg)) { $cmd = "cmd /c cd /d $($e.dir) && $cmd" }
    $line = "build $(Esc-Path $e.out): $($x.rule) $(Esc-Path $e.src)"
    if ($x.rule -eq 'cc' -and $e.pch) { $line += " || $(Esc-Path $e.pch)" }
    [void]$sb.AppendLine($line)
    [void]$sb.AppendLine("  cmd = $(Esc-Val $cmd)")
    [void]$sb.AppendLine("  src = $(Esc-Val ([IO.Path]::GetFileName($e.src)))")
}
$ninjaFile = Join-Path $OutDir 'check.ninja'
[IO.File]::WriteAllText($ninjaFile, $sb.ToString())

# 6. Run
$log = Join-Path $OutDir 'check.log'
$sw = [Diagnostics.Stopwatch]::StartNew()
& ninja -C $Cfg -f $ninjaFile "-j$Jobs" -k 0 2>&1 | Tee-Object -FilePath $log | Out-Host
$rc = $LASTEXITCODE
$sw.Stop()

$failed = @{}
foreach ($m in (Select-String -Path $log -Pattern '^FAILED: (.+)$')) { $failed[(Norm ($m.Matches[0].Groups[1].Value.Trim()))] = $true }
$nFail = 0
foreach ($t in $tus) {
    $ok = (Test-Path $t.out) -and -not $failed.ContainsKey((Norm $t.out))
    if (-not $ok) { $nFail++ }
    '{0}  {1}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $t.src | Write-Host
}
'{0} TUs, {1} failed, {2:N1}s at -j{3}. Log: {4}' -f $tus.Count, $nFail, $sw.Elapsed.TotalSeconds, $Jobs, $log | Write-Host
if ($nFail -or $rc) { exit 1 }
exit 0
