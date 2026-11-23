# Build build/agent6/aot/merge/merge_dxil_cache.exe against the same zstd_static.lib gradient_compiler links (1 thread).
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
Set-Location $w
. .\env\devshell.ps1 -Jobs 1 | Out-Null
$x = "$w\DimensionsRecomp\research\reblue\thirdparty\XenosRecomp"
$src = "$w\build\agent6\aot\merge\merge_dxil_cache.cpp"
$exe = "$w\build\agent6\aot\merge\merge_dxil_cache.exe"
$t0 = Get-Date
& clang++ -std=c++17 -O2 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -D_CRT_SECURE_NO_WARNINGS `
  "-I$x\thirdparty\zstd\lib" $src "$x\out\build\lego-release\thirdparty\zstd\build\cmake\lib\zstd_static.lib" `
  -o $exe 2>&1
"clang++ exit=$LASTEXITCODE wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2))"
if (Test-Path $exe) { "exe_bytes=$((Get-Item $exe).Length) sha256=$((Get-FileHash $exe -Algorithm SHA256).Hash)" }
