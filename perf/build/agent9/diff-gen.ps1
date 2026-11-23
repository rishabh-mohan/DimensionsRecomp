# Agent 9: compare two generated trees (byte identity + per-file size delta).
#   powershell -NoProfile -File build\agent9\diff-gen.ps1 -A build\agent2\gen-noflag\default -B build\agent9\generated\off\default
param([Parameter(Mandatory = $true)][string]$A, [Parameter(Mandatory = $true)][string]$B, [int]$Top = 10)
$R = '<workspace>'
Set-Location $R
$A = (Resolve-Path $A).Path; $B = (Resolve-Path $B).Path
function Index([string]$root) {
  $m = @{}
  Get-ChildItem $root -Recurse -File -Force | ForEach-Object { $m[$_.FullName.Substring($root.Length).TrimStart('\')] = $_ }
  $m
}
$ia = Index $A; $ib = Index $B
$onlyA = @($ia.Keys | Where-Object { -not $ib.ContainsKey($_) })
$onlyB = @($ib.Keys | Where-Object { -not $ia.ContainsKey($_) })
$same = 0; $diff = New-Object System.Collections.ArrayList
foreach ($k in $ia.Keys) {
  if (-not $ib.ContainsKey($k)) { continue }
  $fa = $ia[$k]; $fb = $ib[$k]
  if ($fa.Length -eq $fb.Length) {
    $ha = (Get-FileHash $fa.FullName -Algorithm SHA256).Hash
    $hb = (Get-FileHash $fb.FullName -Algorithm SHA256).Hash
    if ($ha -eq $hb) { $same++; continue }
  }
  [void]$diff.Add([pscustomobject]@{ File = $k; A = $fa.Length; B = $fb.Length; Delta = $fb.Length - $fa.Length })
}
$sa = ($ia.Values | Measure-Object Length -Sum).Sum; $sb = ($ib.Values | Measure-Object Length -Sum).Sum
"A: $A files=$($ia.Count) bytes=$sa"
"B: $B files=$($ib.Count) bytes=$sb delta=$($sb - $sa) ({0:N2}%)" -f (100.0 * ($sb - $sa) / [Math]::Max(1, $sa))
"identical=$same different=$($diff.Count) onlyA=$($onlyA.Count) onlyB=$($onlyB.Count)"
if ($onlyA.Count) { "onlyA: " + (($onlyA | Select-Object -First $Top) -join ', ') }
if ($onlyB.Count) { "onlyB: " + (($onlyB | Select-Object -First $Top) -join ', ') }
if ($diff.Count) {
  "largest size deltas:"
  $diff | Sort-Object { [Math]::Abs($_.Delta) } -Descending | Select-Object -First $Top | Format-Table -AutoSize | Out-String -Width 200
}
