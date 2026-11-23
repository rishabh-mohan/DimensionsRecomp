# Agent 2 - build/dev ON compile DB check (task #1 step 5), run after the stub configure.
#  1. re-run configure-dev-on.ps1 (now with the native_lock_elide compat shim),
#  2. build ONLY the dxc shader-header custom commands (generated/gpu_native/shaders/*.h), after proving
#     with "ninja -t commands" that their whole closure is dxc (no codegen, no SDK targets),
#  3. compile-one -SyntaxOnly on a plain TU, native_lock_elide.cpp and a shader-header user.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\dev-on-check.ps1 [-SkipConfigure]
param([switch]$SkipConfigure, [int]$Jobs = 2)
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2"
$out = "$log\dev-on-check.txt"
function Note([string]$s) { "$(Get-Date -Format HH:mm:ss) $s" | Out-File -Append -Encoding utf8 $out }
Note "=== dev-on-check start"
if (-not $SkipConfigure) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    powershell -NoProfile -ExecutionPolicy Bypass -File "$log\configure-dev-on.ps1"
    $c = $LASTEXITCODE
    $n = @(Select-String -Path "$log\dev-on-configure.log" -Pattern 'Agent 2 compat shim').Count
    Note ("configure exit={0} wall={1:N1}s shimMessages={2}" -f $c, $sw.Elapsed.TotalSeconds, $n)
    if ($c -ne 0) { Note "configure failed - stopping"; exit 1 }
}
# Shim present in the DB?
$db = Get-Content "$R\build\dev\compile_commands.json" -Raw
$hasShim = $db -match 'native_lock_elide_compat\.h'
Note "DB entries mention compat header: $hasShim"
# 2. shader headers
$hdrs = @(Select-String -Path "$R\build\dev\build.ninja" -Pattern '^build (generated/gpu_native/shaders/[^ :|$]+\.h)' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
Note ("shader header outputs: {0}" -f $hdrs.Count)
if ($hdrs.Count -gt 0) {
    $cmds = @(& ninja -C "$R\build\dev" -t commands @hdrs)
    $bad = @($cmds | Where-Object { $_ -notmatch 'dxc\.exe' })
    Note ("closure commands: {0}, non-dxc: {1}" -f $cmds.Count, $bad.Count)
    if ($bad.Count -gt 0) {
        $bad | Select-Object -First 5 | ForEach-Object { Note ("  non-dxc: " + $_.Substring(0, [Math]::Min(300, $_.Length))) }
        Note "NOT building shader headers (closure is not dxc-only)"
    } else {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        & ninja -C "$R\build\dev" -j $Jobs @hdrs > "$log\dev-shader-headers.log" 2>&1
        Note ("shader headers build exit={0} wall={1:N1}s" -f $LASTEXITCODE, $sw.Elapsed.TotalSeconds)
    }
}
# 3. compile-one checks
foreach ($src in 'src\main.cpp', 'src\native_lock_elide.cpp', 'src\gpu_native\device.cpp') {
    $name = [IO.Path]::GetFileNameWithoutExtension($src)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    powershell -NoProfile -ExecutionPolicy Bypass -File "$R\env\compile-one.ps1" "DimensionsRecomp\rexlego\$src" -OutDir "$log\obj-dev" -Db "$R\build\dev\compile_commands.json" -SyntaxOnly > "$log\dev-c1-$name.log" 2>&1
    Note ("compile-one -SyntaxOnly {0} exit={1} wall={2:N1}s" -f $src, $LASTEXITCODE, $sw.Elapsed.TotalSeconds)
}
Note "=== dev-on-check end"
