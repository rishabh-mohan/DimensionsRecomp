# bench/agent12/build.ps1 -- sequential clang-cl build of the Agent 12 I/O / memory / logging
# tests and benches. One TU at a time (the machine is shared). Outputs go to build/agent12/bench.
#
#   powershell -ExecutionPolicy Bypass -File bench/agent12/build.ps1 [target ...]
#
# Targets: t1_scatter_test t2_watch_test b1_scatter b2_watch b3_open b4_samefile b5_log (default: all)
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Targets)
$ErrorActionPreference = 'Stop'

$all = @('t1_scatter_test', 't2_watch_test', 'b1_scatter', 'b2_watch', 'b3_open', 'b4_samefile', 'b5_log')
if (-not $Targets -or $Targets.Count -eq 0) { $Targets = $all }

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $root
try { . .\env\devshell.ps1 -Quiet } finally { Pop-Location }

$src  = Join-Path $PSScriptRoot 'src'
$out  = Join-Path $root 'build\agent12\bench'
$logs = Join-Path $out 'logs'
New-Item -ItemType Directory -Force -Path $out, $logs | Out-Null

$tp = Join-Path $root 'DimensionsRecomp\rexglue-sdk\thirdparty'
$common = @('/nologo', '/O2', '-march=x86-64-v2', '/std:c++latest', '/EHsc', '/MD', '/W3',
            '/DNOMINMAX', '/DWIN32_LEAN_AND_MEAN', '/D_CRT_SECURE_NO_WARNINGS', "/I$src", '-fuse-ld=lld')

$extra = @{
    'b2_watch' = @('/DB12_NO_COUNTERS')
    'b5_log'   = @("/I$tp\spdlog\include", "/I$tp\fmt\include", '/DSPDLOG_FMT_EXTERNAL', '/DFMT_HEADER_ONLY')
}
$sources = @{
    'b5_log' = @('b5_log.cpp', 'b5_log_registry.cpp')
}

$failed = @()
foreach ($t in $Targets) {
    if ($all -notcontains $t) { throw "build.ps1: unknown target '$t'" }
    $srcs = @("$t.cpp")
    if ($sources.ContainsKey($t)) { $srcs = $sources[$t] }
    $objDir = Join-Path $out "obj_$t"
    New-Item -ItemType Directory -Force -Path $objDir | Out-Null
    $cl = @() + $common
    if ($extra.ContainsKey($t)) { $cl += $extra[$t] }
    $cl += ($srcs | ForEach-Object { Join-Path $src $_ })
    $cl += @("/Fo$objDir\", "/Fe$out\$t.exe", '/link', 'advapi32.lib')
    $log = Join-Path $logs "build_$t.log"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $ErrorActionPreference = 'Continue'   # clang-cl warnings on stderr must not throw
    $o = & clang-cl @cl 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $o | Out-File -FilePath $log -Encoding utf8
    if ($o) { $o | Out-Host }
    Write-Host ("[build] {0}: exit={1} ({2:N1}s)" -f $t, $code, $sw.Elapsed.TotalSeconds)
    if ($code -ne 0) { $failed += $t }
}
if ($failed.Count) { Write-Host "[build] FAILED: $($failed -join ' ')"; exit 1 }
Write-Host '[build] all OK'
