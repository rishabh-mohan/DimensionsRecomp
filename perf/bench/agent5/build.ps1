# Agent 5 benches/tests (uploads). Usage, from the workspace root:
#   powershell -File bench/agent5/build.ps1 [-Run] [-Only <name>[,<name>]]
# Outputs go to build/agent5. clang++ from env/devshell.ps1, -O2, one compile at a time.
param([switch]$Run, [string[]]$Only = @())
$ErrorActionPreference = 'Stop'
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
. "$root\env\devshell.ps1" -Quiet
$out = Join-Path $root 'build\agent5'
$gen = Join-Path $out 'gen'
New-Item -ItemType Directory -Force $gen | Out-Null
$src = Join-Path $root 'DimensionsRecomp\rexlego\src'
$here = $PSScriptRoot

# Extract the SDK tiled-offset functions verbatim (brace matched).
function Get-Block([string]$text, [string]$signature) {
    $start = $text.IndexOf($signature)
    if ($start -lt 0) { throw "signature not found: $signature" }
    $i = $text.IndexOf('{', $start) + 1; $depth = 1
    while ($depth) { if ($text[$i] -eq '{') { $depth++ } elseif ($text[$i] -eq '}') { $depth-- }; $i++ }
    return $text.Substring($start, $i - $start)
}
$util = Get-Content -Raw (Join-Path $root 'DimensionsRecomp\rexglue-sdk\src\graphics\pipeline\texture\util.cpp')
$inc = (Get-Block $util 'int32_t GetTiledOffset2D(') + "`n`n" + (Get-Block $util 'int32_t GetTiledOffset3D(') + "`n"
$incPath = Join-Path $gen 'sdk_tiled_offset.inc'
if (-not (Test-Path $incPath) -or (Get-Content -Raw $incPath) -ne $inc) { Set-Content -NoNewline -Path $incPath -Value $inc }
# The production buffers.cpp ByteSwapElements body, verbatim, for test_byteswap.cpp.
$swap = (Get-Block (Get-Content -Raw (Join-Path $src 'gpu_native\buffers.cpp')) 'void ByteSwapElements(') + "`n"
$swapPath = Join-Path $gen 'buffers_byteswap.inc'
if (-not (Test-Path $swapPath) -or (Get-Content -Raw $swapPath) -ne $swap) { Set-Content -NoNewline -Path $swapPath -Value $swap }

$common = @('-std=c++20', '-O2', '-D_CRT_SECURE_NO_WARNINGS', '-DNOMINMAX', '-Wall', '-Wno-unused-function',
            "-I$src", "-I$gen", "-I$here")
$targets = [ordered]@{
    'test_untile_v3'   = @{ arch = '-march=x86-64-v3'; files = @('test_untile_runs.cpp', 'sdk_tiled_offset.cpp') }
    'test_untile_v2'   = @{ arch = '-march=x86-64-v2'; files = @('test_untile_runs.cpp', 'sdk_tiled_offset.cpp') }
    'test_untile_sse2' = @{ arch = '-march=x86-64';    files = @('test_untile_runs.cpp', 'sdk_tiled_offset.cpp') }
    'bench_untile'     = @{ arch = '-march=x86-64-v3'; files = @('bench_untile.cpp', 'sdk_tiled_offset.cpp') }
    'bench_untile_v2'  = @{ arch = '-march=x86-64-v2'; files = @('bench_untile.cpp', 'sdk_tiled_offset.cpp') }
    'test_byteswap_v3'   = @{ arch = '-march=x86-64-v3'; files = @('test_byteswap.cpp') }
    'test_byteswap_v2'   = @{ arch = '-march=x86-64-v2'; files = @('test_byteswap.cpp') }
    'test_byteswap_sse2' = @{ arch = '-march=x86-64';    files = @('test_byteswap.cpp') }
    'bench_byteswap'     = @{ arch = '-march=x86-64-v3'; files = @('bench_byteswap.cpp') }
    'bench_byteswap_v2'  = @{ arch = '-march=x86-64-v2'; files = @('bench_byteswap.cpp') }
    'test_staging_pool_v3' = @{ arch = '-march=x86-64-v3'; files = @('test_texture_staging_pool.cpp') }
}
foreach ($name in $targets.Keys) {
    if ($Only.Count -and -not ($Only -contains $name)) { continue }
    $t = $targets[$name]
    $files = @($t.files | ForEach-Object { Join-Path $here $_ })
    $exe = Join-Path $out "$name.exe"
    Write-Host "== $name ($($t.arch))"
    & clang++ @common $t.arch @files -o $exe
    if ($LASTEXITCODE) { throw "compile failed: $name" }
    if ($Run -and $name -like 'test_*') {
        & $exe
        if ($LASTEXITCODE) { throw "test failed: $name" }
    }
}
