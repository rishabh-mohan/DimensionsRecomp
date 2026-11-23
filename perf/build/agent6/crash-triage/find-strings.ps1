# Agent 6 crash triage: read-only chunked ASCII string search in large binaries (exe, dumps).
# Usage: powershell -NoProfile -File find-strings.ps1 -Path <file> -Needle a,b,c [-Context 160] [-MaxHits 8]
param(
  [Parameter(Mandatory)] [string]$Path,
  [Parameter(Mandatory)] [string[]]$Needle,
  [int]$Context = 160,
  [int]$MaxHits = 8
)
$ErrorActionPreference = 'Stop'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr]0x20
$enc = [Text.Encoding]::GetEncoding(28591)
$maxLen = ($Needle | Measure-Object -Property Length -Maximum).Maximum
$overlap = $maxLen + $Context
$chunk = 16MB
$fs = [IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
try {
  $len = $fs.Length
  $hits = @{}; foreach ($n in $Needle) { $hits[$n] = New-Object System.Collections.Generic.List[string] }
  $counts = @{}; foreach ($n in $Needle) { $counts[$n] = 0 }
  $buf = New-Object byte[] ($chunk + $overlap)
  $pos = [int64]0
  while ($pos -lt $len) {
    $fs.Position = $pos
    $want = [int][Math]::Min([int64]($chunk + $overlap), $len - $pos)
    $got = 0
    while ($got -lt $want) { $r = $fs.Read($buf, $got, $want - $got); if ($r -le 0) { break }; $got += $r }
    $s = $enc.GetString($buf, 0, $got)
    $limit = [Math]::Min($chunk, $got)   # only count matches that START inside this chunk
    foreach ($n in $Needle) {
      $i = $s.IndexOf($n, [StringComparison]::Ordinal)
      while ($i -ge 0 -and $i -lt $limit) {
        $counts[$n]++
        if ($hits[$n].Count -lt $MaxHits) {
          $ctxLen = [Math]::Min($Context, $got - $i)
          $ctx = ($s.Substring($i, $ctxLen) -replace '[^\x20-\x7E]', '.')
          $hits[$n].Add(("0x{0:X}: {1}" -f ($pos + $i), $ctx))
        }
        $i = $s.IndexOf($n, $i + 1, [StringComparison]::Ordinal)
      }
    }
    $pos += $chunk
  }
} finally { $fs.Close() }
"FILE {0} ({1:N0} bytes)" -f $Path, $len
foreach ($n in $Needle) {
  "  [{0}] count={1}" -f $n, $counts[$n]
  foreach ($h in $hits[$n]) { "      $h" }
}
