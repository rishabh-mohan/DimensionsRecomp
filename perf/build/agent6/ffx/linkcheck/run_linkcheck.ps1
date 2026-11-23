# Agent 6, task #12: build the FSR3 link check with the game's compile flags, then run it.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent6\ffx\linkcheck\run_linkcheck.ps1 [-Device] [-LibDir <dir>]
# The default -LibDir is DimensionsRecomp\rexglue-sdk\bin\ffx_sdk, which is where rexlego/CMakeLists.txt links from.
# Headers come from rexglue-sdk\thirdparty\FidelityFX-SDK\sdk\include, the same include path the game uses.
param([switch]$Device, [string]$LibDir = '')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
. "$root\env\devshell.ps1" -Jobs 1 | Out-Null
$inc = "$root\DimensionsRecomp\rexglue-sdk\thirdparty\FidelityFX-SDK\sdk\include"
if (-not $LibDir) { $LibDir = "$root\DimensionsRecomp\rexglue-sdk\bin\ffx_sdk" }
$out = "$PSScriptRoot\out"
New-Item -ItemType Directory -Force $out | Out-Null
Write-Host "linkcheck: libs from $LibDir"
& clang++ --target=x86_64-pc-windows-msvc -O3 -DNDEBUG -std=gnu++23 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt `
    '-msse4.1' -march=x86-64-v3 -DNOMINMAX -DWIN32_LEAN_AND_MEAN "-I$inc" "$PSScriptRoot\linkcheck.cpp" `
    -fuse-ld=lld -o "$out\linkcheck.exe" "$LibDir\ffx_backend_dx12_x64.lib" "$LibDir\ffx_fsr3upscaler_x64.lib" `
    -ld3d12 -ldxgi -ldxguid
if ($LASTEXITCODE) { Write-Host 'linkcheck: FAIL (compile or link)'; exit 1 }
$runArgs = @()
if ($Device) { $runArgs += '--device' }
& "$out\linkcheck.exe" @runArgs
exit $LASTEXITCODE
