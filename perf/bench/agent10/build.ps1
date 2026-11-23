<#
  Agent 10 (task #9) bench/test driver. Builds standalone tests/benches for rex/ppc/intrinsics.h and rex/math.h
  with clang from env\devshell.ps1 (loaded automatically if clang++ is not on PATH). Outputs: build\agent10\<config>\.
  Usage: powershell -NoProfile -File bench\agent10\build.ps1 [-Test] [-Bench] [-Math] [-Quick] [-Configs v3,v2,v3noavx2,portable]
         [-Threads 2] [-BenchArgs '--reps 9'] [-Asm]
  Configs: v3 = -march=x86-64-v3 (game baseline), v2 = -march=x86-64-v2, v3noavx2 = v3 minus AVX2 (SSE4.1 paths at v3 latency),
           portable = v2 + SIMDE_NO_NATIVE (the generic simde fallbacks, as on a non-x86 host).
#>
param(
    [switch]$Test, [switch]$Bench, [switch]$Math, [switch]$Quick, [switch]$Asm,
    [string[]]$Configs = @('v3'),
    [int]$Threads = 2,
    [string]$BenchArgs = ''
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Sdk = Join-Path $Root 'DimensionsRecomp\rexglue-sdk'
$Out = Join-Path $Root 'build\agent10'
if (-not (Get-Command clang++ -ErrorAction SilentlyContinue)) { . (Join-Path $Root 'env\devshell.ps1') | Out-Null }
$Configs = @($Configs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$cfgFlags = @{
    'v3'       = @('-march=x86-64-v3')
    'v2'       = @('-march=x86-64-v2')
    'v3noavx2' = @('-march=x86-64-v3', '-mno-avx2')
    'portable' = @('-march=x86-64-v2', '-DSIMDE_NO_NATIVE')
}
$common = @('-std=c++23', '-O2', '-D_CRT_SECURE_NO_WARNINGS', '-fno-strict-aliasing', '-ffp-model=strict', '-fno-char8_t',
    "-I$Sdk\include", "-I$Sdk\thirdparty\simde", "-I$PSScriptRoot", '-Wall', '-Wno-unused-function', '-Wno-unused-variable')
$fail = 0
function Build([string]$cfg, [string]$src, [string]$exe, [string[]]$extra = @()) {
    $dir = Join-Path $Out $cfg
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $args2 = $common + $cfgFlags[$cfg] + $extra + @((Join-Path $PSScriptRoot $src), '-o', (Join-Path $dir $exe))
    Write-Host "[$cfg] clang++ $src -> $exe"
    & clang++ @args2
    if ($LASTEXITCODE -ne 0) { throw "compile failed: $src [$cfg]" }
    return (Join-Path $dir $exe)
}
foreach ($cfg in $Configs) {
    if (-not $cfgFlags.ContainsKey($cfg)) { throw "unknown config $cfg" }
    if ($Test) {
        $exe = Build $cfg 'test_intrinsics.cpp' 'test_intrinsics.exe'
        $targs = @('--threads', $Threads, '--kat', "$Sdk\tests\ppc\asm")
        if ($Quick -or $cfg -eq 'portable') { $targs += '--quick' }
        if (Select-String -Path "$Sdk\include\rex\ppc\intrinsics.h" -Pattern 'alignas\(16\) inline constexpr uint8_t VectorMaskL' -Quiet) { $targs += '--require-aligned-tables' }
        & $exe @targs
        if ($LASTEXITCODE -ne 0) { $fail++ }
    }
    if ($Math -and (Test-Path (Join-Path $PSScriptRoot 'test_math.cpp'))) {
        $exe = Build $cfg 'test_math.cpp' 'test_math.exe' @('-fsanitize=shift', '-fsanitize-trap=shift')
        & $exe
        if ($LASTEXITCODE -ne 0) { $fail++ }
    }
    if ($Bench -and (Test-Path (Join-Path $PSScriptRoot 'bench_intrinsics.cpp'))) {
        $exe = Build $cfg 'bench_intrinsics.cpp' 'bench_intrinsics.exe'
        & $exe @($BenchArgs -split ' ' | Where-Object { $_ })
        if ($LASTEXITCODE -ne 0) { $fail++ }
    }
    if ($Asm -and (Test-Path (Join-Path $PSScriptRoot 'asm_probe.cpp'))) {
        $dir = Join-Path $Out $cfg
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        & clang++ @($common + $cfgFlags[$cfg] + @('-S', '-masm=intel', (Join-Path $PSScriptRoot 'asm_probe.cpp'), '-o', (Join-Path $dir 'asm_probe.s')))
        if ($LASTEXITCODE -ne 0) { $fail++ } else { Write-Host "[$cfg] asm -> $dir\asm_probe.s" }
    }
}
if ($fail) { Write-Host "build.ps1: $fail step(s) FAILED"; exit 1 }
Write-Host 'build.ps1: all steps passed'
