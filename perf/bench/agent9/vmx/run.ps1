# Build and run the VMX fallback proof (text check, value harness, asm sizes).
# Run it while holding a CPU slot:
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/vmx/run.ps1
# Optional: -Random <n> -AliasRandom <n> -Bench <n> -Configs sse41,v3,nonative
param([long]$Random = 10000000, [long]$AliasRandom = 2000000, [long]$Bench = 20000000,
      [string[]]$Configs = @('sse41', 'v3', 'nonative'))
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
Set-Location $PSScriptRoot
$sdk = Join-Path $root 'DimensionsRecomp/rexglue-sdk'

& powershell -NoProfile -File (Join-Path $PSScriptRoot 'extract.ps1') -Out (Join-Path $PSScriptRoot 'new_emitters.inc')
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'verify_unchanged.ps1') | Tee-Object -FilePath verify_unchanged.out.txt

Write-Host '== gen (text check) =='
& clang++ -std=c++20 -O1 gen.cpp -o gen.exe
if ($LASTEXITCODE) { Write-Host 'gen.cpp build failed'; exit 1 }
& .\gen.exe | Tee-Object -FilePath gen.out.txt
if ($LASTEXITCODE) { Write-Host "gen.exe reported $LASTEXITCODE failed checks"; exit 1 }

$inc = @("-I$sdk/include", "-I$sdk/thirdparty/simde", "-I$sdk/thirdparty/fmt/include",
         "-I$root/build/dev/rexglue-sdk/include")
$common = @('-std=gnu++23', '-DNDEBUG', '-DNOMINMAX', '-DWIN32_LEAN_AND_MEAN', '-Wno-unused-variable')
$flags = @{
  # ppc_tests flags (tests/ppc CMake): SSE4.1/SSSE3 only, so simde emulates the AVX2 sllv/srlv/srav.
  sse41    = @('-O2', '-msse4.1', '-mssse3', '-ffp-model=strict', '-fno-strict-aliasing')
  # LEGO recomp TU flags (build/dev compile_commands.json).
  v3       = @('-O3', '-march=x86-64-v3', '-msse4.1')
  # simde portable code paths only (closest local stand-in for a non-x86 host).
  nonative = @('-O2', '-msse4.1', '-mssse3', '-DSIMDE_NO_NATIVE')
}
$fail = 0
foreach ($c in $Configs) {
  Write-Host "== harness $c =="
  & clang++ @common @($flags[$c]) @inc harness.cpp -o "harness_$c.exe"
  if ($LASTEXITCODE) { Write-Host "harness build failed ($c)"; $fail++; continue }
  & ".\harness_$c.exe" $Random $AliasRandom $Bench | Tee-Object -FilePath "result_$c.txt"
  if ($LASTEXITCODE) { $fail++ }
  if ($c -ne 'nonative') {
    # Instruction counts of the distinct-operand kernels.
    & clang++ @common @($flags[$c]) @inc -S -masm=intel harness.cpp -o "harness_$c.s"
    if ($LASTEXITCODE) { Write-Host "asm build failed ($c)"; $fail++; continue }
    & powershell -NoProfile -File (Join-Path $PSScriptRoot 'asm_count.ps1') -Configs $c
  }
}
Write-Host "run.ps1 done, failures: $fail"
exit $fail
