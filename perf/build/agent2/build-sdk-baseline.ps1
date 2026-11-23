# Agent 2 - baseline SDK build (task #1 step 6).
# Run (as a run_command background task): powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-sdk-baseline.ps1 -SkipConfigure -KeepGoing
#   -KeepGoing     pass "-k 0" to ninja so everything not downstream of the PPC .map failures still builds
#                  (bundled Cygwin powerpc-none-elf-nm.exe crashes when stdout is a file), then install + ctest anyway.
#   -CtestExclude  regex for ctest -E (e.g. the PPC suite when its maps could not be produced).
param([switch]$SkipConfigure, [int]$Jobs = 10, [switch]$KeepGoing, [string]$CtestExclude = '')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
. "$R\env\devshell.ps1" 6>$null | Out-Null
$log = "$R\build\agent2"
$steps = "$log\sdk-baseline-steps.txt"
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
$src = "$R\baseline\DimensionsRecomp\rexglue-sdk"
$bin = "$R\build\sdk"
if (-not $SkipConfigure) {
    Push-Location $src
    $c = Step 'configure' "cmake --preset win-amd64 -B `"$bin`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DREXGLUE_BUILD_TESTS=ON -DCMAKE_INSTALL_PREFIX=$($R -replace '\\','/')/build/sdk/install > `"$log\sdk-configure.log`" 2>&1"
    Pop-Location
    if ($c -ne 0) { exit 1 }
}
$k = ''
if ($KeepGoing) { $k = ' -- -k 0' }
$c = Step 'build' "cmake --build `"$bin`" --config Release -j $Jobs$k > `"$log\sdk-build.log`" 2>&1"
if ($c -ne 0 -and -not $KeepGoing) { exit 2 }
$c = Step 'install' "cmake --install `"$bin`" --config Release > `"$log\sdk-install.log`" 2>&1"
if ($c -ne 0) { exit 3 }
$c = Step 'ctest-list' "ctest --test-dir `"$bin`" -C Release -N > `"$log\sdk-ctest-list.log`" 2>&1"
$e = ''
if ($CtestExclude) { $e = " -E `"$CtestExclude`"" }
$c = Step 'ctest' "ctest --test-dir `"$bin`" -C Release --output-on-failure -j 6 --timeout 900$e > `"$log\sdk-ctest.log`" 2>&1"
exit $c
