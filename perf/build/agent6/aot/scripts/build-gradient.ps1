# Step 4b: build gradient_compiler (prepared by tools/gpu-aot/prepare_native_compiler.py) at 1 thread,
# against official DXC 1.9.2609 (deviation accepted by Agent 6: the generated CMake points at the checkout's
# thirdparty/dxc-bin, which is DXC 1.8.2407; the recipe says the compiler/prelinker use official 1.9.2609).
$ErrorActionPreference = 'Continue'
$root = '<workspace>'
Set-Location $root
. .\env\devshell.ps1 -Jobs 1
$src = "$root\DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source"
$bld = "$root\build\agent6\aot\gradient-build"
"start: $(Get-Date -Format o)"
# Keep the generated file; rewrite only the dxc-bin root (binary-safe, keeps CRLF).
python -c @"
import pathlib, shutil
src = pathlib.Path(r'$src')
gen = src / 'CMakeLists.txt.generated'
cur = src / 'CMakeLists.txt'
if not gen.exists():
    shutil.copy2(cur, gen)
data = gen.read_bytes()
old = b'<workspace>/DimensionsRecomp/research/reblue/thirdparty/XenosRecomp/thirdparty/dxc-bin'
new = b'<workspace>/DimensionsRecomp/research/dxc-1.9.2609'
n = data.count(old)
cur.write_bytes(data.replace(old, new))
print('dxc-bin path occurrences replaced:', n)
"@
$sw = [Diagnostics.Stopwatch]::StartNew()
cmake -S $src -B $bld -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++ 2>&1 | ForEach-Object { "$_" }
"configure exit=$LASTEXITCODE wall_s=$([math]::Round($sw.Elapsed.TotalSeconds,1))"
$sw.Restart()
cmake --build $bld -j 1 -v 2>&1 | ForEach-Object { "$_" }
"build exit=$LASTEXITCODE wall_s=$([math]::Round($sw.Elapsed.TotalSeconds,1))"
Get-ChildItem $bld -File | Where-Object { $_.Extension -in '.exe', '.dll' } | ForEach-Object {
  "{0}  {1}  {2}  {3}" -f $_.Length, (Get-FileHash $_.FullName -Algorithm SHA256).Hash, $_.VersionInfo.FileVersion, $_.Name }
"end: $(Get-Date -Format o)"
