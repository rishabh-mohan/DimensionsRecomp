# Assemble, link and map every tests/ppc/asm/*.s the way tests/ppc/CMakeLists.txt + cmake/ppc_test_pipeline.cmake do.
# Run (holds one Agent 9 CPU slot):
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/ppctests/asm.ps1
# Outputs: build/agent9/ppctests/{obj,bin}/<stem>.{o,bin,map}; log: build/agent9/ppctests/logs/asm.log
param([string]$Only = '*')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
Set-Location $root
$sdk = 'DimensionsRecomp/rexglue-sdk'
$bu = "$sdk/tools/binutils"
$out = 'build/agent9/ppctests'
New-Item -ItemType Directory -Force "$out/obj", "$out/bin", "$out/logs" | Out-Null
$log = "$out/logs/asm.log"
$fail = New-Object System.Collections.Generic.List[string]
$sw = [Diagnostics.Stopwatch]::StartNew()
$files = @(Get-ChildItem "$sdk/tests/ppc/asm/$Only.s" | Sort-Object Name)
$ok = 0
foreach ($s in $files) {
  $stem = $s.BaseName
  $src = "$sdk/tests/ppc/asm/$($s.Name)"
  $o = "$out/obj/$stem.o"; $b = "$out/bin/$stem.bin"; $m = "$out/bin/$stem.map"
  $r = & "$bu/powerpc-none-elf-as.exe" -a32 -be -mregnames -mpower7 -maltivec -mvsx -mvmx128 -R -o $o $src 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) { $fail.Add("as ${stem} (exit $LASTEXITCODE): $r"); continue }
  $r = & "$bu/powerpc-none-elf-ld.exe" -A powerpc:common32 -melf32ppc -EB -nostdlib --oformat=binary -Ttext=0x82010000 -e 0x82010000 -o $b $o 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) { $fail.Add("ld ${stem} (exit $LASTEXITCODE): $r"); continue }
  # nm: capture stdout through a pipe (Cygwin nm crashes with 0xC0000005 when stdout is a
  # redirected file, which is why build/sdk/tests/ppc/bin/*.map are 0 bytes); write LF like the cmake -P step.
  $lines = @(& "$bu/powerpc-none-elf-nm.exe" --numeric-sort $o 2>$null)
  $nmExit = $LASTEXITCODE
  [IO.File]::WriteAllText((Join-Path $root $m), (($lines -join "`n") + "`n"), [Text.UTF8Encoding]::new($false))
  if ($nmExit -ne 0 -or $lines.Count -eq 0) { $fail.Add("nm ${stem} (exit $nmExit, $($lines.Count) lines)"); continue }
  $ok++
}
$sw.Stop()
$summary = "asm: {0} files, {1} ok, {2} failed, {3:n1} s" -f $files.Count, $ok, $fail.Count, $sw.Elapsed.TotalSeconds
$body = @($summary) + $fail
Set-Content -Path $log -Value $body -Encoding UTF8
$body | ForEach-Object { Write-Host $_ }
if ($fail.Count) { exit 1 } else { exit 0 }
