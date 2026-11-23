# Link ppc_tests.exe for one variant with the pin build's link line (build/sdk build-Release.ninja), via a response file,
# and copy the pin runtime DLLs next to it (pin ppc_tests runs from rexruntime's output dir).
# Objects: <variant>/obj-<h>/ppc_test_functions.obj, and the variant's own ppc_test_cases.obj, or another variant's
# (default first, then opt) when that variant's generated ppc_test_cases.cpp, ppc_config.h and ppc_test_decls.h are
# byte-identical to this one's (crso reuses default's; opt9 reuses opt's: both drop the cr expectations). An object older
# than its generated source is refused (exit 2), so a regenerated variant cannot link stale code.
# Run (one Agent 9 CPU slot):
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/ppctests/link.ps1 -Variant default"
param([ValidateSet('default', 'opt', 'crso', 'opt9')][string]$Variant = 'default', [ValidateSet('dev', 'pin')][string]$Headers = 'dev')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
Set-Location $root
. .\env\devshell.ps1 | Out-Null
$R = $root -replace '\\', '/'
$O = "$R/baseline/DimensionsRecomp/rexglue-sdk/out/win-amd64/Release"
$P = "$R/build/agent9/ppctests"
$vdir = "$P/$Variant"
function Test-Fresh([string]$obj, [string]$src) {
  (Test-Path $obj) -and (Test-Path $src) -and ((Get-Item $obj).LastWriteTime -gt (Get-Item $src).LastWriteTime)
}
$fn = "$vdir/obj-$Headers/ppc_test_functions.obj"
if (-not (Test-Fresh $fn "$vdir/generated/ppc_test_functions.cpp")) {
  Write-Host "link ${Variant}: $fn is missing or older than its source; run compile.ps1 -Variant $Variant -Tu functions"; exit 2
}
$cs = "$vdir/obj-$Headers/ppc_test_cases.obj"
if (-not (Test-Fresh $cs "$vdir/generated/ppc_test_cases.cpp")) {
  $found = ''
  # (not $o: PowerShell names are case-insensitive, so $o would overwrite $O, the pin libs dir)
  foreach ($ov in @('default', 'opt') | Where-Object { $_ -ne $Variant }) {
    $og = "$P/$ov/generated"; $ocs = "$P/$ov/obj-$Headers/ppc_test_cases.obj"
    $same = $true
    foreach ($f in 'ppc_test_cases.cpp', 'ppc_config.h', 'ppc_test_decls.h') {
      if (-not ((Test-Path "$og/$f") -and (Test-Path "$vdir/generated/$f") -and
                ((Get-FileHash "$og/$f").Hash -eq (Get-FileHash "$vdir/generated/$f").Hash))) { $same = $false; break }
    }
    if ($same -and (Test-Fresh $ocs "$og/ppc_test_cases.cpp")) { $found = $ocs; break }
  }
  if (-not $found) {
    Write-Host "link ${Variant}: no current ppc_test_cases.obj (own, or default's/opt's for identical generated sources); run compile.ps1 -Variant $Variant -Tu cases"; exit 2
  }
  $cs = $found
}
# dev headers reference rex::detail::SharedLogLevelFloor(), which the pin rexruntime.dll lacks: add the shim object.
$shim = if ($Headers -eq 'dev') { "$P/shim/shim_logfloor.obj" } else { '' }
$exe = "$vdir/ppc_tests.exe"; $rsp = "$vdir/link-$Headers.rsp"; $log = "$vdir/link-$Headers.log"
$flags = @'
-fuse-ld=lld-link -nostartfiles -nostdlib -march=x86-64-v2 -O3 -DNDEBUG -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -Xlinker /subsystem:console <FN> <CS> <SHIM> -o <EXE> -Xlinker /MANIFEST:EMBED
<O>/rexruntime.lib <O>/fmt.lib <O>/Catch2Main.lib <O>/spdlog.lib <O>/fmt.lib <O>/SDL3-static.lib -lkernel32.lib -luser32.lib -lgdi32.lib -lwinmm.lib -limm32.lib -lole32.lib -loleaut32.lib -lversion.lib -luuid.lib -ladvapi32.lib -lsetupapi.lib -lshell32.lib -lhid.lib -ldinput8.lib -ldxgi.lib -ldxguid.lib <O>/Catch2.lib -lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -loldnames
'@
$flags = $flags.Replace('<FN>', $fn).Replace('<CS>', $cs).Replace('<SHIM>', $shim).Replace('<EXE>', $exe).Replace('<O>', $O)
[IO.File]::WriteAllText($rsp, ($flags -replace "`r?`n", ' '))
if (Test-Path $exe) { Remove-Item -Force $exe }
$sw = [Diagnostics.Stopwatch]::StartNew()
$out = @(& "$R/toolchain/llvm-23.1.6/bin/clang++.exe" "@$rsp" 2>&1 | ForEach-Object { "$_" })
$code = $LASTEXITCODE
$sw.Stop()
Set-Content -Path $log -Value $out -Encoding UTF8
foreach ($d in 'rexruntime.dll', 'TracyClient.dll') { Copy-Item -Force "$O/$d" $vdir }
$line = "link $Variant ($Headers headers): exit $code, {0:n1} s, cases obj $($cs.Substring($P.Length + 1)), log $log" -f $sw.Elapsed.TotalSeconds
Add-Content -Path "$P/logs/compile.log" -Value "$(Get-Date -Format HH:mm:ss) $line"
Write-Host $line
$out | Select-Object -First 30 | ForEach-Object { Write-Host "  $_" }
exit $code
