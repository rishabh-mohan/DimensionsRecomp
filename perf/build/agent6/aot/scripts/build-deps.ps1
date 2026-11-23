# Step 4a: build the pinned XenosRecomp checkout's upstream deps (xxhash, zstd_static, fmt) at 1 thread.
# Output dir is the one hard-coded by prepare_alpha_candidate.py's generated CMake:
#   <checkout>/out/build/lego-release
$ErrorActionPreference = 'Continue'
$root = '<workspace>'
Set-Location $root
. .\env\devshell.ps1 -Jobs 1
$x = "$root\DimensionsRecomp\research\reblue\thirdparty\XenosRecomp"
$b = "$x\out\build\lego-release"
"start: $(Get-Date -Format o)"
$sw = [Diagnostics.Stopwatch]::StartNew()
cmake -S $x -B $b -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ `
  -DBUILD_SHARED_LIBS=ON -DXXHASH_BUILD_XXHSUM=OFF -DZSTD_BUILD_PROGRAMS=OFF -DZSTD_BUILD_SHARED=OFF `
  -DZSTD_BUILD_TESTS=OFF -DFMT_TEST=OFF -DFMT_DOC=OFF 2>&1 | ForEach-Object { "$_" }
"configure exit=$LASTEXITCODE wall_s=$([math]::Round($sw.Elapsed.TotalSeconds,1))"
$sw.Restart()
cmake --build $b -j 1 --target xxhash libzstd_static fmt 2>&1 | ForEach-Object { "$_" }
"build exit=$LASTEXITCODE wall_s=$([math]::Round($sw.Elapsed.TotalSeconds,1))"
foreach ($f in @("$b\thirdparty\xxHash\cmake_unofficial\xxhash.lib",
                 "$b\thirdparty\xxHash\cmake_unofficial\xxhash.dll",
                 "$b\thirdparty\zstd\build\cmake\lib\zstd_static.lib",
                 "$b\thirdparty\fmt\fmt.lib",
                 "$b\thirdparty\fmt\bin\fmt.dll")) {
  if (Test-Path $f) { $i = Get-Item $f; "{0}  {1}  {2}" -f $i.Length, (Get-FileHash $f -Algorithm SHA256).Hash, $f } else { "MISSING  $f" }
}
"end: $(Get-Date -Format o)"
