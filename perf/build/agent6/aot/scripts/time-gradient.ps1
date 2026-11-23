# Time one gradient_compiler run (DXIL only + HLSL dump) on a given input dir, pinned to one CPU.
param(
  [Parameter(Mandatory)] [string]$InputDir,
  [Parameter(Mandatory)] [string]$OutCpp,
  [Parameter(Mandatory)] [string]$DumpDir,
  [long]$Mask = 2,
  [string]$Exe = '<workspace>\build\agent6\aot\gradient-build\gradient_compiler.exe',
  [string]$Common = '<workspace>\DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h'
)
$env:XENOS_RECOMP_DXIL_ONLY = '1'
$env:XENOS_RECOMP_HLSL_DUMP = $DumpDir
$psi = New-Object System.Diagnostics.ProcessStartInfo $Exe
$psi.Arguments = "`"$InputDir`" `"$OutCpp`" `"$Common`""
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$t0 = Get-Date
$p = [Diagnostics.Process]::Start($psi)
$p.ProcessorAffinity = [IntPtr]$Mask
$o = $p.StandardOutput.ReadToEndAsync(); $e = $p.StandardError.ReadToEndAsync()
$p.WaitForExit()
$wall = ((Get-Date) - $t0).TotalSeconds
"--- stdout"; $o.Result; "--- stderr"; $e.Result
"exit=$($p.ExitCode) wall_s=$([math]::Round($wall,2)) cpu_s=$([math]::Round($p.TotalProcessorTime.TotalSeconds,2)) mask=0x$('{0:X}' -f $Mask)"
if (Test-Path $OutCpp) { "out_bytes=$((Get-Item $OutCpp).Length) sha256=$((Get-FileHash $OutCpp -Algorithm SHA256).Hash)" }
if (Test-Path $DumpDir) { "dump_files=$((Get-ChildItem $DumpDir -File).Count) dump_bytes=$((Get-ChildItem $DumpDir -File | Measure-Object Length -Sum).Sum)" }
