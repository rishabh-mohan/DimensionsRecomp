# Shows the vector.cpp edit touched only the 8 emitters: put the original emitter text
# (orig_emitters.inc) back into a copy of the current vector.cpp and compare the SHA256 with the
# hash of vector.cpp taken before the edit. Read-only.
# Usage: powershell -NoProfile -File bench/agent9/vmx/verify_unchanged.ps1
param(
  [string]$Src = "$PSScriptRoot/../../../DimensionsRecomp/rexglue-sdk/src/codegen/builders/vector.cpp",
  [string]$Expected = 'B3528ED4A7E0642E2F390CF3D745E18D6E496F14D1707AFEF6F7049BB84FB39D'
)
$ErrorActionPreference = 'Stop'
$latin1 = [Text.Encoding]::GetEncoding(28591)  # byte-preserving
$cur = $latin1.GetString([IO.File]::ReadAllBytes((Resolve-Path $Src)))
$crlf = $cur.Contains("`r`n")
$cur = $cur.Replace("`r`n", "`n")
$orig = $latin1.GetString([IO.File]::ReadAllBytes("$PSScriptRoot/orig_emitters.inc")).Replace("`r`n", "`n")
function Get-Fn([string]$text, [string]$name) {
  $hdr = "bool build_$name(BuilderContext& ctx) {`n"
  $s = $text.IndexOf($hdr); if ($s -lt 0) { throw "build_$name not found" }
  $e = $text.IndexOf("`n}`n", $s); if ($e -lt 0) { throw "end of build_$name not found" }
  return $text.Substring($s, $e + 3 - $s)
}
foreach ($n in 'vsubsws', 'vsrb', 'vsrab', 'vrlw', 'vsraw', 'vsrw', 'vpkuhus', 'vpkuwus') {
  $cur = $cur.Replace((Get-Fn $cur $n), (Get-Fn $orig $n))
}
if ($crlf) { $cur = $cur.Replace("`n", "`r`n") }
$sha = [Security.Cryptography.SHA256]::Create()
$hash = [BitConverter]::ToString($sha.ComputeHash($latin1.GetBytes($cur))).Replace('-', '')
$now = (Get-FileHash (Resolve-Path $Src) -Algorithm SHA256).Hash
Write-Host "vector.cpp now:                  $now"
Write-Host "with the 8 original emitters:    $hash"
Write-Host "recorded before the edit:        $Expected"
if ($hash -eq $Expected) { Write-Host 'RESULT: only the 8 emitters differ from the pre-edit file' }
else { Write-Host 'RESULT: other lines differ too (another agent may have edited vector.cpp since)' }
