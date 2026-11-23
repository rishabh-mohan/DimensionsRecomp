# Extract whole `bool build_X(BuilderContext& ctx) { ... }` functions from vector.cpp.
# Usage: powershell -NoProfile -File bench/agent9/vmx/extract.ps1 -Out <file> [-Src <vector.cpp>] [-Names a,b,...]
# The bodies end at the first line that is exactly "}" after the header line.
param(
  [string]$Out,
  [string]$Src = "$PSScriptRoot/../../../DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp",
  [string[]]$Names = @('vsubsws', 'vsrb', 'vsrab', 'vrlw', 'vsraw', 'vsrw', 'vpkuhus', 'vpkuwus')
)
$ErrorActionPreference = 'Stop'
$lines = Get-Content $Src
$sb = [System.Text.StringBuilder]::new()
foreach ($n in $Names) {
  $start = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq "bool build_$n(BuilderContext& ctx) {") { $start = $i; break }
  }
  if ($start -lt 0) { throw "build_$n not found in $Src" }
  $end = -1
  for ($i = $start + 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq '}') { $end = $i; break }
  }
  if ($end -lt 0) { throw "end of build_$n not found" }
  for ($i = $start; $i -le $end; $i++) { [void]$sb.AppendLine($lines[$i]) }
  [void]$sb.AppendLine()
}
[System.IO.File]::WriteAllText($Out, $sb.ToString())
Write-Host "wrote $Out ($($Names.Count) functions)"
