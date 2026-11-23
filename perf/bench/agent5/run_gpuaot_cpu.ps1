# Agent 5: run the CPU-only gpu-aot checks that compile files I own (one compile at a time).
# Usage, from the workspace root:
#   powershell -NoProfile -File bench/agent5/run_gpuaot_cpu.ps1 -Tag <before|after|...> [-Only <name>[,<name>]]
# Outputs and per-check logs go to build/agent5/gpuaot-<Tag>/; summary.txt lists exit codes.
# The portable checks are built twice: default target (scalar paths) and -march=x86-64-v3 (SIMD paths).
# The D3D12 tests (test_geometry_content_gpu.py, test_geometry_content_sdk_gpu.py) need --plume-lib from a
# full build, so they are not run here.
# Exit codes come from plain functions. The earlier version ran each step as a .GetNewClosure() script
# block; the closure captured a stale $LASTEXITCODE, so every step reported the previous step's exit code
# (runs before 21:35 are unreliable: read the per-step logs, not summary.txt).
param([string]$Tag = 'run', [string[]]$Only = @())
$ErrorActionPreference = 'Continue'
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
. "$root\env\devshell.ps1" -Quiet
$aot = Join-Path $root 'DimensionsRecomp\tools\gpu-aot'
$src = Join-Path $root 'DimensionsRecomp\rexlego\src'
$out = Join-Path $root "build\agent5\gpuaot-$Tag"
New-Item -ItemType Directory -Force $out | Out-Null
$script:results = @()

function Selected([string]$name) { return -not ($Only.Count -and -not ($Only -contains $name)) }

function Run-Native([string]$log, [string]$exe, [object[]]$arguments) {
    & $exe @arguments *>> $log
    return [int]$LASTEXITCODE
}

function Record([string]$name, [int]$code, [Diagnostics.Stopwatch]$sw) {
    $seconds = [int]$sw.Elapsed.TotalSeconds
    $script:results += [pscustomobject]@{ name = $name; exit = $code; seconds = $seconds }
    Write-Host ("{0,-36} exit={1} {2}s" -f $name, $code, $seconds)
}

# Compile one .cpp with clang++, then run the exe if the compile succeeded.
function Step-Compiled([string]$name, [object[]]$compileArgs, [string]$exe) {
    if (-not (Selected $name)) { return }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $log = Join-Path $out "$name.log"
    Remove-Item $log -ErrorAction SilentlyContinue
    $code = Run-Native $log 'clang++' ($compileArgs + @('-o', $exe))
    if ($code -eq 0) { $code = Run-Native $log $exe @() }
    Record $name $code $sw
}

function Step-Python([string]$name, [string]$py, [string]$dir) {
    if (-not (Selected $name)) { return }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $log = Join-Path $out "$name.log"
    Remove-Item $log -ErrorAction SilentlyContinue
    Record $name (Run-Native $log 'python' @($py, $dir)) $sw
}

$common = @('-std=c++20', '-O2', '-UNDEBUG', '-D_CRT_SECURE_NO_WARNINGS', '-DNOMINMAX', "-I$src")
$portable = 'texture_volume_upload', 'texture_alpha4_upload', 'texture_2d_upload', 'vertex_upload',
            'vertex_byte_order', 'pool_copy'
foreach ($check in $portable) {
    foreach ($flavor in @(@{ tag = 'x86-64'; arch = @() }, @{ tag = 'v3'; arch = @('-march=x86-64-v3') })) {
        $exe = Join-Path $out "test_${check}_$($flavor.tag).exe"
        Step-Compiled "test_${check}_$($flavor.tag)" ($common + $flavor.arch + @((Join-Path $aot "test_$check.cpp"))) $exe
    }
}
foreach ($test in 'test_buffer_variants', 'test_buffer_view_generation', 'test_quad_buffer_windows',
                  'test_texture_depth_upload', 'test_texture_prepare', 'test_texture_binding_failures',
                  'test_framebuffer_owners', 'test_texture_publication_lru', 'test_texture_source_residency',
                  'test_texture_upload_capture') {
    Step-Python $test (Join-Path $aot "$test.py") (Join-Path $out $test)
}
# UploadBufferPool unit test (not mine); it covers upload_buffer_pool.h, which item 4 touches.
Step-Compiled 'test_upload_buffer_pool' ($common + @((Join-Path $aot 'test_upload_buffer_pool.cpp'))) (Join-Path $out 'test_upload_buffer_pool.exe')
# The same test with the pool built at the 64 MB budget its asserts (lines 34 and 37) were written
# for; the batch-2 constructor makes that budget selectable (the texture staging pool uses it).
if (Selected 'test_upload_buffer_pool_64mb') {
    $text = Get-Content -Raw (Join-Path $aot 'test_upload_buffer_pool.cpp')
    $pool64Cpp = Join-Path $out 'test_upload_buffer_pool_64mb.cpp'
    if ($text.Contains('UploadBufferPool<Buffer> pool;')) {
        Set-Content -NoNewline -Path $pool64Cpp -Value $text.Replace('UploadBufferPool<Buffer> pool;', 'UploadBufferPool<Buffer> pool(64*1024*1024);')
        Step-Compiled 'test_upload_buffer_pool_64mb' ($common + @($pool64Cpp)) (Join-Path $out 'test_upload_buffer_pool_64mb.exe')
    } else {
        Record 'test_upload_buffer_pool_64mb' 99 ([Diagnostics.Stopwatch]::StartNew())
    }
}
$summary = $script:results | Format-Table -AutoSize | Out-String
Set-Content -Path (Join-Path $out 'summary.txt') -Value $summary
Write-Host $summary
if ($script:results | Where-Object { $_.exit -ne 0 }) { exit 1 }
