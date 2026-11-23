# Builds and runs the rlwinm/rlwnm/rlwimi lowering equivalence harness. Hold a CPU slot:
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/rlwinm/build.ps1
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/rlwinm/build.ps1 -Steps x64,asm"
# Steps: gen, cases, driver, run, x64, asm (default all). One clang process at a time, no -j.
param([string]$Steps = 'gen,cases,driver,run,x64,asm', [int]$Parts = 4)
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
$root = [IO.Path]::GetFullPath((Join-Path $here '../../..'))
$sdk = Join-Path $root 'DimensionsRecomp/rexglue-sdk'
$sdkRel = '../../../DimensionsRecomp/rexglue-sdk'  # for the cygwin binutils
Push-Location $root
. .\env\devshell.ps1 | Out-Null
Pop-Location
Set-Location $here
$stepList = $Steps -split ','
foreach ($d in 'bin', 'obj', 'gen', 'ppc') { New-Item -ItemType Directory -Force -Path (Join-Path $here $d) | Out-Null }
$log = Join-Path $here 'build.log'
function Log([string]$s) { Write-Host $s; Add-Content -Path $log -Value $s }
function Run([string]$what, [scriptblock]$cmd, [string]$saveTo) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $out = & $cmd 2>&1 | Out-String
  $code = $LASTEXITCODE
  Log ("[{0:yyyy-MM-dd HH:mm:ss}] {1}: exit={2} {3:n1}s" -f (Get-Date), $what, $code, $sw.Elapsed.TotalSeconds)
  if ($saveTo) { Set-Content -Path $saveTo -Value $out -Encoding ascii }
  if ($out.Trim()) { Log $out.TrimEnd() }
  if ($code -ne 0) { Log "STOP: $what failed"; exit 1 }
}
Log ("==== build.ps1 -Steps {0} -Parts {1}" -f $Steps, $Parts)

if ($stepList -contains 'gen') {
  Run 'build gen.exe' { clang++ -std=c++20 -O1 -Wall -I "$sdk/src/codegen/builders" -I "$sdk/thirdparty/fmt/include" -DFMT_HEADER_ONLY harness/gen.cpp -o bin/gen.exe }
  Remove-Item gen/cases_*.cpp -ErrorAction SilentlyContinue
  Run 'run gen.exe' { & "$here/bin/gen.exe" gen $Parts }
}
if ($stepList -contains 'cases') {
  Remove-Item obj/cases_*.o -ErrorAction SilentlyContinue
  foreach ($f in Get-ChildItem gen -Filter 'cases_*.cpp' | Sort-Object Name) {
    $o = "obj/$($f.BaseName).o"
    Run "compile $($f.Name) ($([math]::Round($f.Length / 1MB, 1)) MB)" { clang++ -std=c++20 -O1 -I harness -c $f.FullName -o $o }
  }
}
if ($stepList -contains 'driver') {
  Run 'compile driver.cpp' { clang++ -std=c++20 -O2 -Wall -I harness -I gen -c harness/driver.cpp -o obj/driver.o }
  $objs = @(Get-ChildItem obj -Filter '*.o' | ForEach-Object { $_.FullName })
  Run "link rlw_equiv.exe ($($objs.Count) objects)" { clang++ $objs -o bin/rlw_equiv.exe }
}
if ($stepList -contains 'run') {
  Run 'run rlw_equiv.exe' { & "$here/bin/rlw_equiv.exe" } (Join-Path $here 'results.txt')
}
if ($stepList -contains 'x64') {
  Run 'compile x64_forms.s (-O2 -march=x86-64-v2)' { clang++ -std=c++20 -O2 -march=x86-64-v2 -S -I harness gen/x64_forms.cpp -o gen/x64_forms.s }
  Run 'count x64 instructions' { powershell -NoProfile -File "$here/count_x64.ps1" -Asm gen/x64_forms.s -Order gen/x64_order.txt -Out x64_table.md -Listing gen/x64_listing.txt }
}
if ($stepList -contains 'asm') {
  Run 'build asmgen.exe' { clang++ -std=c++20 -O1 -Wall -I harness -I "$sdk/src/codegen/builders" harness/asmgen.cpp -o bin/asmgen.exe }
  Run 'run asmgen.exe' { & "$here/bin/asmgen.exe" gen/instr_rlw_lowering.s }
  Copy-Item gen/instr_rlw_lowering.s "$sdk/tests/ppc/asm/instr_rlw_lowering.s" -Force
  Log 'copied gen/instr_rlw_lowering.s -> tests/ppc/asm/instr_rlw_lowering.s'
  $bu = "$sdk/tools/binutils"
  Run 'assemble instr_rlw_lowering.s' { & "$bu/powerpc-none-elf-as.exe" -a32 -be -mregnames -mpower7 -maltivec -mvsx -mvmx128 -R -o ppc/instr_rlw_lowering.o "$sdkRel/tests/ppc/asm/instr_rlw_lowering.s" }
  Run 'objdump -d' { & "$bu/powerpc-none-elf-objdump.exe" -d ppc/instr_rlw_lowering.o } (Join-Path $here 'ppc/objdump.txt')
}
Log '==== done'
exit 0
