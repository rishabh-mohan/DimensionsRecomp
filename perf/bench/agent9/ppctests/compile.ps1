# Compile one generated ppc test TU with the pin build's ppc_tests flags
# (from `ninja -f build-Release.ninja -t commands ppc_tests` in build/sdk), via a response file.
# Run (one Agent 9 CPU slot per TU):
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/compile.ps1 -Variant default -Tu functions"
# -Headers dev: rex headers from DimensionsRecomp/rexglue-sdk/include (what the dev-tree tool targets); pin libs either way.
# -Headers pin: rex headers from baseline/DimensionsRecomp/rexglue-sdk/include (exactly the pin build).
param([ValidateSet('default', 'opt', 'crso', 'opt9')][string]$Variant = 'default', [ValidateSet('functions', 'cases')][string]$Tu = 'functions',
      [ValidateSet('dev', 'pin')][string]$Headers = 'dev', [string]$OptLevel = '-O3')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
Set-Location $root
. .\env\devshell.ps1 | Out-Null
$R = $root -replace '\\', '/'
$B = "$R/baseline/DimensionsRecomp/rexglue-sdk"
$inc = if ($Headers -eq 'dev') { "$R/DimensionsRecomp/rexglue-sdk/include" } else { "$B/include" }
$vdir = "$R/build/agent9/ppctests/$Variant"
$objdir = "$vdir/obj-$Headers"
New-Item -ItemType Directory -Force $objdir | Out-Null
$src = "$vdir/generated/ppc_test_$Tu.cpp"; $obj = "$objdir/ppc_test_$Tu.obj"
$rsp = "$objdir/ppc_test_$Tu.rsp"; $log = "$objdir/ppc_test_$Tu.log"
$flags = @'
-DNOMINMAX -DREXGLUE_BUILD_CONFIG=\"Release\" -DREXGLUE_ENABLE_PERF_COUNTERS -DREX_HAS_D3D12=1 -DREX_PLATFORM_WINDOWS=1 -DSPDLOG_COMPILED_LIB -DSPDLOG_FMT_EXTERNAL -DWIN32_LEAN_AND_MEAN -DCMAKE_INTDIR=\"Release\"
-I<INC> -I<GEN> -I<B>/thirdparty/simde -I<B>/thirdparty/simde/simde -I<R>/build/sdk/include -I<B>/thirdparty/imgui -I<B>/thirdparty/fmt/include -I<B>/thirdparty/spdlog/include -I<R>/build/sdk/thirdparty/sdl3/include-revision -I<B>/thirdparty/sdl3/include -I<B>/thirdparty/dxc/include -I<B>/thirdparty/catch2/src/catch2/.. -I<R>/build/sdk/thirdparty/catch2/generated-includes -isystem <B>/thirdparty/tomlplusplus/include
-march=x86-64-v2 <OPT> -DNDEBUG -std=c++23 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -fno-strict-aliasing -ffp-model=strict <OPT> -DNDEBUG -fno-char8_t -Wall -Wextra -UTRACY_ENABLE -UREXGLUE_ENABLE_PROFILING -UREXGLUE_ENABLE_PERF_COUNTERS -UREXGLUE_PROFILE_GUEST_FUNCTIONS -msse4.1 -mssse3 -c <SRC> -o <OBJ>
'@
$flags = $flags.Replace('<INC>', $inc).Replace('<GEN>', "$vdir/generated").Replace('<B>', $B).Replace('<R>', $R).Replace('<OPT>', $OptLevel).Replace('<SRC>', $src).Replace('<OBJ>', $obj)
[IO.File]::WriteAllText($rsp, ($flags -replace "`r?`n", ' '))
if (Test-Path $obj) { Remove-Item -Force $obj }
$sw = [Diagnostics.Stopwatch]::StartNew()
$out = @(& "$R/toolchain/llvm-23.1.6/bin/clang++.exe" "@$rsp" 2>&1 | ForEach-Object { "$_" })
$code = $LASTEXITCODE
$sw.Stop()
Set-Content -Path $log -Value $out -Encoding UTF8
$warn = @($out | Select-String -Pattern 'warning:').Count
$err = @($out | Select-String -Pattern 'error:').Count
$line = "compile $Variant/$Tu ($Headers headers, $OptLevel): exit $code, {0:n1} s, $warn warnings, $err errors, log $log" -f $sw.Elapsed.TotalSeconds
Add-Content -Path "$R/build/agent9/ppctests/logs/compile.log" -Value "$(Get-Date -Format HH:mm:ss) $line"
Write-Host $line
$out | Select-String -Pattern 'error:' | Select-Object -First 25 | ForEach-Object { Write-Host "  $_" }
exit $code
