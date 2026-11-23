# Agent 2 - build/dev NATIVE_GPU=ON configure-only (task #1 step 5) -> build/dev/compile_commands.json.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\configure-dev-on.ps1
# Stub inputs + flags from Agent 6 (J1(a), 18:13). Compile DB only: do NOT run a plain ninja here (the
# prelinkers / FSR3 libs are not available yet, and no SDK targets may be built in the dev tree).
# REXGLUE_HOST_CODEGEN_EXECUTABLE pins the codegen edge to the frozen 0.0.23.3 tool, because
# DimensionsRecomp\rexlego\generated is a junction into the pristine baseline tree.
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2"
$steps = "$log\dev-on-steps.txt"
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
$root = "$Rf/DimensionsRecomp"
$stub = "$root/rexlego/out/native-gpu/stubs"
$cfg = @(
    "cmake -S `"$R\DimensionsRecomp\rexlego`" -B `"$R\build\dev`" -G Ninja",
    "-DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++",
    "-DLEGODIMENSIONS_NATIVE_GPU=ON -DLEGODIMENSIONS_X86_BASELINE=x86-64-v3",
    "-DREXSDK_DIR=$root/rexglue-sdk -DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    "-DREXGLUE_HOST_CODEGEN_EXECUTABLE=$Rf/build/agent2/codegen-tool/rexglue.exe",
    # Partition-coupling shim (same as build/baseline): native_lock_elide.cpp includes funcs.N.h
    # headers that match the author's partition sidecar, not a fresh codegen. See compat/*.
    "-DCMAKE_PROJECT_INCLUDE=$Rf/build/agent2/compat/project-include.cmake",
    "-DLEGO_TEMPORAL_SHADER_BANK=$stub/temporal-bank",
    "-DLEGO_FLOAT_BLEND_INDICES_BANK=$stub/float-blend-indices-bank",
    "-DLEGO_NATIVE_SHADER_CACHE=$stub/lego-dxil-cache.cpp",
    "-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=$stub/runtime-cache.cpp",
    "-DLEGO_NATIVE_FIDELITYFX_RUNTIME=$root/rexglue-sdk/thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/amd_fidelityfx_dx12.dll",
    "-DLEGO_NATIVE_BINARY_CACHE=OFF",
    "`"-DLEGO_HOST_DXC_EXECUTABLE=C:/Program Files (x86)/Windows Kits/10/bin/10.0.22621.0/x64/dxc.exe`"",
    "> `"$log\dev-on-configure.log`" 2>&1"
) -join ' '
$c = Step 'configure-dev-on' $cfg
exit $c
