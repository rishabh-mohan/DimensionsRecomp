# Agent 2 - NATIVE_GPU=OFF baseline game build (task #1 step 4, README-dev step 4).
# Run (as a run_command background task):
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-game-baseline.ps1 [-SkipConfigure] [-Jobs 10] [-Target legodimensions]
# Source: the pristine snapshot baseline\DimensionsRecomp\rexlego (generated\ = codegen 0.0.23.3, --pointer_table_scan).
# SDK:    find_package against build\sdk\install (CMAKE_PREFIX_PATH), no REXSDK_DIR.
# The in-build codegen edge uses the frozen copy of the installed rexglue.exe (byte-identical), so a
# later SDK reinstall can never make this tree regenerate (and rewrite) the baseline generated sources.
param([switch]$SkipConfigure, [int]$Jobs = 10, [string]$Target = 'legodimensions', [string]$Tag = 'game', [switch]$KeepGoing)
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2"
$steps = "$log\$Tag-baseline-steps.txt"
function Step([string]$name, [string]$cmd) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    "$(Get-Date -Format HH:mm:ss) BEGIN $name : $cmd" | Out-File -Append -Encoding utf8 $steps
    cmd /d /c $cmd
    $code = $LASTEXITCODE
    $t = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
    $free = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
    "$(Get-Date -Format HH:mm:ss) END   $name exit=$code wall=${t}s freeC=${free}GB" | Out-File -Append -Encoding utf8 $steps
    return $code
}
$Rf = $R -replace '\\', '/'
$src = "$R\baseline\DimensionsRecomp\rexlego"
$bin = "$R\build\baseline"
if (-not $SkipConfigure) {
    $c = Step 'configure' ("cmake -S `"$src`" -B `"$bin`" -G Ninja -DCMAKE_BUILD_TYPE=Release " +
        "-DCMAKE_CXX_COMPILER=clang++ -DLEGODIMENSIONS_NATIVE_GPU=OFF -DLEGODIMENSIONS_X86_BASELINE=x86-64-v3 " +
        "-DCMAKE_PREFIX_PATH=$Rf/build/sdk/install " +
        "-DREXGLUE_HOST_CODEGEN_EXECUTABLE=$Rf/build/agent2/codegen-tool/rexglue.exe " +
        "-DCMAKE_PROJECT_INCLUDE=$Rf/build/agent2/compat/project-include.cmake " +
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON > `"$log\$Tag-configure.log`" 2>&1")
    if ($c -ne 0) { exit 1 }
}
$k = ''
if ($KeepGoing) { $k = ' -- -k 0' }
$c = Step 'build' "cmake --build `"$bin`" --target $Target -j $Jobs$k > `"$log\$Tag-build.log`" 2>&1"
exit $c
