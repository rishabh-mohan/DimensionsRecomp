# Agent 6 (J1 c): offline smoke test of the CMake prelink step (lego_gpu_prelink /
# lego_gpu_prelink_runtime) with the same sources and flags as build/dev's
# compile_commands.json, but LEGO_DXC_ROOT = research/dxc-1.9.2609 (the DXC that
# built the AOT cache). Single-threaded. Output only under build/agent6/prelink_smoke.
param(
  [Parameter(Mandatory = $true)][string]$Cache,   # lego-dxil-cache.cpp or runtime-cache.cpp
  [Parameter(Mandatory = $true)][string]$Name,    # output sub-directory name
  [switch]$Embed                                   # also run embed_linked_bank.py on the output
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../../..").Path
$dr = "$root/DimensionsRecomp"
$bin = "$root/toolchain/llvm-23.1.6/bin"
$dxc = "$dr/research/dxc-1.9.2609"
$out = "$PSScriptRoot/$Name"
$common = "$PSScriptRoot/common"
New-Item -ItemType Directory -Force $out, $common | Out-Null
$inc = @("-I$dr/rexlego/src", "-I$dr/thirdparty/miniz", "-I$dr/thirdparty/zstd", "-I$dxc/inc")
$cxx = @('-O3', '-DNDEBUG', '-std=gnu++23', '-D_DLL', '-D_MT', '-Xclang', '--dependent-lib=msvcrt')
$cc = @('-O3', '-DNDEBUG', '-D_DLL', '-D_MT', '-Xclang', '--dependent-lib=msvcrt')
$log = "$out/smoke.txt"
"prelink smoke $Name  cache=$Cache  $(Get-Date -Format s)" | Set-Content $log
function Step([string]$label, [scriptblock]$body) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & $body
  if ($LASTEXITCODE -ne 0) { "FAIL $label rc=$LASTEXITCODE" | Add-Content $log; throw "$label failed ($LASTEXITCODE)" }
  ('{0,-34} {1,8:N1} s' -f $label, $sw.Elapsed.TotalSeconds) | Tee-Object -FilePath $log -Append
}
$objs = @{
  'prelink_shader_cache' = @("$dr/tools/gpu-aot/prelink_shader_cache.cpp", 'cxx')
  'dxc_link'             = @("$dr/rexlego/src/gpu_native/dxc_link.cpp", 'cxx')
  'miniz'                = @("$dr/thirdparty/miniz/miniz.cpp", 'cxx')
  'zstddeclib'           = @("$dr/thirdparty/zstd/zstddeclib.c", 'cc')
}
foreach ($k in $objs.Keys) {
  $o = "$common/$k.obj"
  if (Test-Path $o) { continue }
  $src = $objs[$k][0]
  if ($objs[$k][1] -eq 'cxx') { Step "compile $k" { & "$bin/clang++.exe" @inc @cxx -c $src -o $o } }
  else { Step "compile $k" { & "$bin/clang.exe" @inc @cc -c $src -o $o } }
}
Step 'compile cache TU' { & "$bin/clang++.exe" @inc @cxx -c $Cache -o "$out/cache.obj" }
$exe = "$out/prelink.exe"
Step 'link prelink.exe' { & "$bin/clang++.exe" -fuse-ld=lld "$common/prelink_shader_cache.obj" "$common/dxc_link.obj" "$common/miniz.obj" "$common/zstddeclib.obj" "$out/cache.obj" "$dxc/lib/x64/dxcompiler.lib" -o $exe }
Copy-Item "$dxc/bin/x64/dxcompiler.dll", "$dxc/bin/x64/dxil.dll" $out -Force
$env:LEGO_GPU_PRELINK_JOBS = '1'
$linked = "$out/linked-dxil-cache.cpp"
$p = $null
Step 'run prelink (1 job)' {
  $script:p = Start-Process -FilePath $exe -ArgumentList "`"$linked`"" -NoNewWindow -Wait -PassThru -RedirectStandardError "$out/prelink.stderr.txt" -RedirectStandardOutput "$out/prelink.stdout.txt"
  $global:LASTEXITCODE = $script:p.ExitCode
}
('prelink cpu {0:N1} s, peak ws {1:N0} MB' -f $p.TotalProcessorTime.TotalSeconds, ($p.PeakWorkingSet64 / 1MB)) | Tee-Object -FilePath $log -Append
('linked output {0:N0} bytes' -f (Get-Item $linked).Length) | Tee-Object -FilePath $log -Append
Get-Content "$out/prelink.stderr.txt" -Tail 5 | Add-Content $log
if ($Embed) {
  $py = 'C:/Users/<user>/AppData/Local/Programs/Python/Python312/python.exe'
  Step 'embed_linked_bank.py' { & $py "$dr/tools/gpu-aot/embed_linked_bank.py" $linked "$out/linked-bank" --llvm-mc "$bin/llvm-mc.exe" --arch x86_64 }
  Get-ChildItem "$out/linked-bank" | ForEach-Object { '{0,-32} {1,12:N0}' -f $_.Name, $_.Length } | Tee-Object -FilePath $log -Append
}
'SMOKE PASS' | Tee-Object -FilePath $log -Append
