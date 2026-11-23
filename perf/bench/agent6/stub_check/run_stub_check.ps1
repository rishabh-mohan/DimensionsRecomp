# Agent 6, J1(a): regenerate the native-GPU stubs and verify them.
# Compiles the stub caches through the real tiny consumer TUs (runtime_shader_cache.cpp,
# runtime_linked_shader_cache.cpp) plus a mimic of temporal/float-blend lookups, links with
# the stub .obj blobs and the same zstd/miniz sources the game uses, then runs the checks.
# Single-threaded; output in build/agent6/stub_check.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
. "$root\env\devshell.ps1" | Out-Null
$dr = "$root\DimensionsRecomp"
$stubs = "$dr\rexlego\out\native-gpu\stubs"
$out = "$root\build\agent6\stub_check"
New-Item -ItemType Directory -Force $out | Out-Null

python "$stubs\make_stubs.py"
if ($LASTEXITCODE) { throw "make_stubs.py failed" }

$common = @('--target=x86_64-pc-windows-msvc', '-O1', '-w', "-I$dr\rexlego\src", "-I$dr\thirdparty\miniz", "-I$dr\thirdparty\zstd")
$cxx = $common + @('-std=c++20', '-DNOMINMAX')
$objs = @()
function Compile($src, $obj, $flags) {
  & clang @flags -c $src -o $obj
  if ($LASTEXITCODE) { throw "compile failed: $src" }
  $script:objs += $obj
}
$tb = ($stubs + '\temporal-bank\temporal-bank.cpp').Replace('\', '/')
$fb = ($stubs + '\float-blend-indices-bank\float-blend-indices-bank.cpp').Replace('\', '/')
$rc = ($stubs + '\runtime-cache.cpp').Replace('\', '/')
# String-valued -D macros go through clang response files (GNU quoting: \" is a literal quote).
# Passing them inline loses the quotes under Windows PowerShell's native-argument rules.
function Rsp($name, [string[]]$lines) {
  $path = "$out\$name.rsp"
  [IO.File]::WriteAllLines($path, $lines)
  return "@$path"
}
$checkDefs = Rsp 'stub_check_defs' @(('-DLEGO_TEMPORAL_SHADER_METADATA=\"' + $tb + '\"'), ('-DLEGO_FLOAT_BLEND_INDICES_METADATA=\"' + $fb + '\"'))
$runtimeDefs = Rsp 'runtime_cache_defs' @(('-DLEGO_NATIVE_RUNTIME_LIBRARY_SOURCE=\"' + $rc + '\"'))
Compile "$PSScriptRoot\stub_check.cpp" "$out\stub_check.obj" ($cxx + @($checkDefs))
Compile "$stubs\lego-dxil-cache.cpp" "$out\lego-dxil-cache.obj" $cxx
Compile "$dr\rexlego\src\gpu_native\runtime_shader_cache.cpp" "$out\runtime_shader_cache.obj" ($cxx + @($runtimeDefs))
Compile "$dr\rexlego\out\native-gpu\lego-microcode-index.cpp" "$out\lego-microcode-index.obj" $cxx
Compile "$dr\rexlego\out\native-gpu\lego-linked-dxil-cache.cpp" "$out\lego-linked-dxil-cache.obj" $cxx
Compile "$dr\rexlego\src\gpu_native\runtime_linked_shader_cache.cpp" "$out\runtime_linked_shader_cache.obj" $cxx
Compile "$dr\thirdparty\miniz\miniz.cpp" "$out\miniz.obj" $cxx
Compile "$dr\thirdparty\zstd\zstddeclib.c" "$out\zstddeclib.obj" $common
$objs += "$stubs\temporal-bank\temporal-bank.obj", "$stubs\float-blend-indices-bank\float-blend-indices-bank.obj"
& clang --target=x86_64-pc-windows-msvc -fuse-ld=lld @objs -o "$out\stub_check.exe"
if ($LASTEXITCODE) { throw "link failed" }
& "$out\stub_check.exe"
exit $LASTEXITCODE
