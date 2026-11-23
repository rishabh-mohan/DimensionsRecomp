# Agent 9: hostregs.ps1 for any source tree (task #17 item 1a, the nativeB static check). Host code that touches
# ctx.ctr / ctx.cr* / ctx.xer / ctx.reserved / ctx.fpscr / ctx.lr outside codegen, in <Root>\rexlego\src and the SDK's
# src/include (minus codegen and thirdparty), the same pattern and file set as hostregs.ps1 (live tree, 23:53).
# Writes <Out> ("path:line: text") and <Out>.set ("path: text", sorted, unique) so two trees can be compared without
# line numbers; with -Ref (a hostregs output) prints the hits whose "path: text" is not in the reference.
#   powershell -NoProfile -File build\agent9\hostregs2.ps1 -Root build\agent2\snap1\DimensionsRecomp -Out F [-Ref F]
param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$Out, [string]$Ref = '')
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
function AbsR([string]$p) { if (-not [IO.Path]::IsPathRooted($p)) { $p = Join-Path $R $p }; $p.TrimEnd('\') }
$Root = AbsR $Root; $Out = AbsR $Out
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$files = @(Get-ChildItem "$Root\rexlego\src" -Recurse -File -Include *.cpp,*.h,*.hpp,*.inl) +
  @(Get-ChildItem "$Root\rexglue-sdk\src", "$Root\rexglue-sdk\include" -Recurse -File -Include *.cpp,*.h,*.hpp,*.inl |
    Where-Object { $_.FullName -notmatch '\\(codegen|thirdparty|third_party)\\' })
$pat = '(ctx|context|ppc_context|ctx_|self_ctx|state\.context)(\.|->)(ctr|xer|cr[0-7]?|reserved|fpscr|lr)\b'
$hits = @($files | Select-String -Pattern $pat)
$rel = [regex]::Escape($Root + '\')
$lines = foreach ($h in $hits) { "{0}:{1}: {2}" -f ($h.Path -replace "^$rel", ''), $h.LineNumber, $h.Line.Trim() }
[IO.File]::WriteAllLines($Out, [string[]]$lines)
function ToSet([string[]]$ls) { $ls | ForEach-Object { $_ -replace '^([^:]+):\d+: ', '$1: ' } | Sort-Object -Unique }
$set = @(ToSet $lines)
[IO.File]::WriteAllLines("$Out.set", [string[]]$set)
"root $Root : files scanned=$($files.Count) hits=$($hits.Count) unique=$($set.Count) -> $Out"
if ($Ref) {
  $refSet = @(ToSet ([IO.File]::ReadAllLines((AbsR $Ref))))
  $h = [Collections.Generic.HashSet[string]]::new([string[]]$refSet, [StringComparer]::Ordinal)
  $new = @($set | Where-Object { -not $h.Contains($_) })
  $h2 = [Collections.Generic.HashSet[string]]::new([string[]]$set, [StringComparer]::Ordinal)
  $gone = @($refSet | Where-Object { -not $h2.Contains($_) })
  "vs $Ref : reference unique=$($refSet.Count); new in this tree=$($new.Count); only in the reference=$($gone.Count)"
  $new | ForEach-Object { "NEW  $_" }
  $gone | ForEach-Object { "GONE $_" }
}
