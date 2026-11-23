# Build tools/gpu-aot/generate_microcode_index.cpp standalone (the game's CMake target lego_gpu_microcode_index links
# rex::xxhash = rexglue-sdk/thirdparty/xxHash) and run it on the extracted shader assets, pinned to CPU1.
# Deviation: README also passes rexlego/out/native-gpu/runtime-missing (runtime captures); none exist here.
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
Set-Location $w
. .\env\devshell.ps1 -Jobs 1 | Out-Null
$r = "$w\DimensionsRecomp"
$o = "$w\build\agent6\aot\microcode-index"
New-Item -ItemType Directory -Force $o | Out-Null
$x = "$r\rexglue-sdk\thirdparty\xxHash"
"xxHash (rexglue-sdk submodule) HEAD: $(git -C $x rev-parse HEAD)"
$t0 = Get-Date
& clang -O2 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -w -c "$x\xxhash.c" -o "$o\xxhash.o" 2>&1
"clang xxhash.c exit=$LASTEXITCODE"
& clang++ -std=c++20 -O2 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -D_CRT_SECURE_NO_WARNINGS "-I$x" `
  "$r\tools\gpu-aot\generate_microcode_index.cpp" "$o\xxhash.o" -o "$o\lego_gpu_microcode_index.exe" 2>&1
"clang++ generator exit=$LASTEXITCODE build_wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2))"
$exe = "$o\lego_gpu_microcode_index.exe"
if (-not (Test-Path $exe)) { 'BUILD FAILED'; exit 1 }
"exe_bytes=$((Get-Item $exe).Length) sha256=$((Get-FileHash $exe -Algorithm SHA256).Hash)"
$out = "$r\rexlego\out\native-gpu\aot\lego-microcode-index.cpp"
$psi = New-Object System.Diagnostics.ProcessStartInfo $exe
$psi.Arguments = "`"$out`" `"$r\rexlego\out\native-gpu\shader-assets`""
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$t0 = Get-Date
$p = [Diagnostics.Process]::Start($psi)
$p.ProcessorAffinity = [IntPtr]2
$so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
$p.WaitForExit()
"--- stdout"; $so.Result; "--- stderr"; $se.Result
"run exit=$($p.ExitCode) wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2)) cpu_s=$([math]::Round($p.TotalProcessorTime.TotalSeconds,2)) mask=0x2"
if (Test-Path $out) {
  "out_bytes=$((Get-Item $out).Length) sha256=$((Get-FileHash $out -Algorithm SHA256).Hash)"
  "records=$((Select-String -Path $out -Pattern '^  \{ 0x').Count)"
  Get-Content $out -TotalCount 3; Get-Content $out -Tail 2
}
