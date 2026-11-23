# Agent 2 - dev OFF build 1 (and later the ON build) from the snapshot build/agent2/snap1 (task #1).
# Batch 2 (S2 = snap-patch.py apply S2 onto snap1): run the same phases with -Tag snap2. The build dirs (snap1-sdk,
# snap1-off, snap1-on) stay, so ninja rebuilds incrementally; only the log and gate-log names change.
# Build B (Agent 9's codegen option; run-b.ps1 drives it, prep-b.py prepares it): -Phase game -Tag snapB
#   -SnapDir build\agent2\snapB\DimensionsRecomp (a copy of snap1 at S2 with Agent 9's batch-nolr rexlego/generated and
#   legodimensions_config.toml) -GameDir build\agent2\snapB-off -CodegenExe build\agent2\codegen-frozen\codegen-frozen2.exe
#   (checks every source sources.cmake lists) -GenBase build\agent9\install\batch-nolr\generated (gen-check's reference;
#   never install\batch, which has skip_lr). The SDK stays snap1-sdk/install: an -SnapDir run refuses the sdk phase and
#   the snap1-off/snap1-on trees. The gate gets --snap-dir (allowed root, and the TU list from that sources.cmake).
# Run as a run_command background task:
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-snap.ps1 -Phase sdk|game|all
#       [-Jobs 10] [-Affinity F] [-SkipConfigure] [-KeepGoing] [-NoBuild] [-SnapDir D -GameDir D -CodegenExe F -GenBase D]
# SDK : standalone, configured like build/sdk (preset win-amd64 = Ninja Multi-Config, FidelityFX OFF, SDK
#       x86-64-v2) but REXGLUE_BUILD_TESTS=OFF; Release libs + tools; installed to build/agent2/snap1-sdk/install.
#       build/sdk/install is never touched.
# Game: build/agent2/snap1-off (NATIVE_GPU=OFF) or, with -Native, the fresh tree build/agent2/snap1-on (Agent 6's
#       section 5.2 flags; snap1-off stays the bootable OFF tree), from the snapshot's rexlego, Release, x86-64-v3,
#       find_package against snap1-sdk/install, NO compat shim (Agent 8 fixed native_lock_elide.cpp).
#       Codegen (20:45 fix): the snapshot's generated/ is the pinned 0.0.23.3 output; REXGLUE_HOST_CODEGEN_EXECUTABLE
#       is the codegen-frozen.exe stand-in, which writes nothing (the real tool failed at 20:11 on the unrewritten
#       [entrypoint] file_path). gen-check.py (generated/ byte-identical to baseline/, codegen.d on snapshot paths)
#       and snap-gate.py (include dirs + installed-header hashes) must pass before anything compiles.
# -Affinity F runs the build pinned to CPUs 0-3 (hex mask for cmd's start /affinity); children inherit it.
param([string]$Phase = 'all', [int]$Jobs = 10, [string]$Affinity = '', [switch]$SkipConfigure, [switch]$KeepGoing,
      [string]$Tag = 'snap1', [switch]$Native, [int]$PrelinkJobs = 0, [switch]$NoBuild,
      [string]$SnapDir = '', [string]$GameDir = '', [string]$CodegenExe = '', [string]$GenBase = '')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2"
$steps = "$log\$Tag-steps.txt"
function Step([string]$name, [string]$cmd) {
    # -Affinity pins every step (configure, gate and install too), not just the builds
    if ($pin -and -not $cmd.StartsWith('start ')) { $cmd = $pin + $cmd }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    "$(Get-Date -Format HH:mm:ss) BEGIN $name : $cmd" | Out-File -Append -Encoding utf8 $steps
    cmd /d /c $cmd
    $code = $LASTEXITCODE
    # 20:45 fix (Agent 1): `start /b /wait` hides the child's exit code (the 20:11 game build "passed" in 0.5 s),
    # so a step also fails when its log shows a ninja/CMake failure.
    if ($code -eq 0 -and $cmd -match '>\s*"([^"]+\.log)"' -and (Test-Path $Matches[1])) {
        $bad = Select-String -Path $Matches[1] -Pattern '^ninja: build stopped', '^ninja: error', '^FAILED: ', '^CMake Error' |
            Select-Object -First 1
        if ($bad) {
            $code = 98
            "$(Get-Date -Format HH:mm:ss) NOTE  $name log line $($bad.LineNumber): $($bad.Line.Trim()) -> exit 98" |
                Out-File -Append -Encoding utf8 $steps
        }
    }
    $t = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
    $free = [Math]::Round((Get-PSDrive C).Free / 1GB, 2)
    "$(Get-Date -Format HH:mm:ss) END   $name exit=$code wall=${t}s freeC=${free}GB" | Out-File -Append -Encoding utf8 $steps
    return $code
}
$Rf = $R -replace '\\', '/'
function AbsR([string]$p) { if (-not [IO.Path]::IsPathRooted($p)) { $p = Join-Path $R $p }; $p.TrimEnd('\') }
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
if ($CodegenExe) { $cg = (AbsR $CodegenExe) -replace '\\', '/' }
$pin = ''
if ($Affinity) { $pin = "start `"`" /b /wait /affinity $Affinity " }
$k = ''
if ($KeepGoing) { $k = ' -- -k 0' }

if ($Phase -in 'sdk', 'all') {
    if (-not $SkipConfigure) {
        Push-Location "$snap\rexglue-sdk"
        $c = Step 'sdk-configure' ("cmake --preset win-amd64 -B `"$sdkBin`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON " +
            "-DREXGLUE_BUILD_TESTS=OFF -DCMAKE_INSTALL_PREFIX=$Rf/build/agent2/snap1-sdk/install " +
            "> `"$log\$Tag-sdk-configure.log`" 2>&1")
        Pop-Location
        if ($c -ne 0) { exit 11 }
    }
    $c = Step 'sdk-build' "${pin}cmake --build `"$sdkBin`" --config Release -j $Jobs$k > `"$log\$Tag-sdk-build.log`" 2>&1"
    if ($c -ne 0) { exit 12 }
    $c = Step 'sdk-install' "cmake --install `"$sdkBin`" --config Release > `"$log\$Tag-sdk-install.log`" 2>&1"
    if ($c -ne 0) { exit 13 }
}
if ($Phase -in 'game', 'all') {
    $gt = 'game'; $gateLog = "$log\$Tag-gate.log"
    $mode = '-DLEGODIMENSIONS_NATIVE_GPU=OFF '
    if ($Native) {
        # Agent 6's native ON flags (perf-notes/agent6-native-aot.md section 5), re-rooted on the snapshot. The
        # inputs are copied into snap1 with hashes by snap-native-inputs.py; nothing is read from the live tree.
        # Fresh tree build/agent2/snap1-on (Agent 6, section 5.2), so snap1-off stays the bootable OFF build.
        # prepare_plume.py --check runs git in thirdparty/plume, so snap1 holds a copy of plume's gitdir.
        $gt = 'native'; $gateLog = "$log\$Tag-native-gate.log"; $gameBin = "$R\build\agent2\snap1-on"
        $S = $snap -replace '\\', '/'; $ng = "$S/rexlego/out/native-gpu"
        $mode = ("-DLEGODIMENSIONS_NATIVE_GPU=ON " +
            "-DLEGO_NATIVE_SHADER_CACHE=$ng/aot/lego-dxil-cache.cpp " +
            "-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=$ng/stubs/runtime-cache.cpp " +
            "-DLEGO_TEMPORAL_SHADER_BANK=$ng/stubs/temporal-bank " +
            "-DLEGO_FLOAT_BLEND_INDICES_BANK=$ng/aot/float-blend-indices-bank " +
            "-DLEGO_INSTANCED_CONSTANTS_BANK=$ng/aot/instanced-constants-bank " +
            "-DLEGO_DXC_ROOT=$S/research/dxc-1.9.2609 -DLEGO_HOST_DXC_EXECUTABLE= -DLEGO_NATIVE_BINARY_CACHE=ON " +
            "-DLEGO_NATIVE_FIDELITYFX_RUNTIME=$S/rexglue-sdk/thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/amd_fidelityfx_dx12.dll " +
            "-DLEGO_HOST_LLVM_MC=$Rf/toolchain/llvm-23.1.6/bin/llvm-mc.exe ")
        # read by prelink_shader_cache.cpp while the build runs (unset = all 12 logical CPUs)
        $env:LEGO_GPU_PRELINK_JOBS = "$(if ($PrelinkJobs -gt 0) { $PrelinkJobs } else { $Jobs })"
        "$(Get-Date -Format HH:mm:ss) NOTE  native: LEGO_GPU_PRELINK_JOBS=$env:LEGO_GPU_PRELINK_JOBS" | Out-File -Append -Encoding utf8 $steps
    }
    if ($GameDir) { $gameBin = AbsR $GameDir }
    if ($SnapDir) {
        if ($gameBin -match 'snap1-(off|on)$') {
            "$(Get-Date -Format HH:mm:ss) STOP  -SnapDir must not use the snap1 game trees ($gameBin): pass -GameDir" | Out-File -Append -Encoding utf8 $steps
            exit 2
        }
        "$(Get-Date -Format HH:mm:ss) NOTE  snapshot $snap, game tree $gameBin, codegen stand-in $cg, gen-check reference $(if ($GenBase) { AbsR $GenBase } else { 'baseline' })" | Out-File -Append -Encoding utf8 $steps
    }
    if (-not $SkipConfigure) {
        $c = Step "$gt-configure" ("cmake -S `"$snap\rexlego`" -B `"$gameBin`" -G Ninja -DCMAKE_BUILD_TYPE=Release " +
            "-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ " +
            $mode + "-DLEGODIMENSIONS_X86_BASELINE=x86-64-v3 " +
            "-DCMAKE_PREFIX_PATH=$Rf/build/agent2/snap1-sdk/install " +
            "-DREXGLUE_HOST_CODEGEN_EXECUTABLE=$cg " +
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON > `"$log\$Tag-$gt-configure.log`" 2>&1")
        if ($c -ne 0) { exit 21 }
    }
    $gcArgs = ''; $gArgs = ''
    if ($SnapDir) { $gcArgs = " --snap `"$snap\rexlego\generated`" --snap-rex `"$snap\rexlego`""; $gArgs = " --snap-dir `"$snap`"" }
    if ($GenBase) { $gcArgs += " --base `"$(AbsR $GenBase)`"" }
    $c = Step 'gen-check' "python `"$log\gen-check.py`"$gcArgs > `"$log\$Tag-$gt-gen-check.log`" 2>&1"
    if ($c -ne 0) { exit 24 }
    $c = Step 'gate' "python `"$log\snap-gate.py`" `"$gameBin`"$gArgs > `"$gateLog`" 2>&1"
    if ($c -ne 0) { exit 22 }
    # -NoBuild: configure + gen-check + gate only (e.g. the native configure while the OFF build compiles)
    if ($NoBuild) { exit 0 }
    $c = Step "$gt-build" "${pin}cmake --build `"$gameBin`" --target legodimensions -j $Jobs$k > `"$log\$Tag-$gt-build.log`" 2>&1"
    if ($c -ne 0) { exit 23 }
}
exit 0
