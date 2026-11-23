# Agent 1: freeze W5's inputs (hash list) after promotion. Reads only; writes build/agent1/w5/W5-INPUTS-<HHmm>.txt.
$ErrorActionPreference = 'Stop'
$w   = '<workspace>'
$out = Join-Path $w ('build\agent1\w5\W5-INPUTS-{0}.txt' -f (Get-Date -Format 'HHmm'))
$files = @(
  'bench\agent8\RUN-WINDOW5-S3D.cmd',
  'bench\agent8\run\matrix-window5-s3d.json',
  'harness\legodimensions.toml',
  'build\agent2\devoff3-bin\MANIFEST.txt', 'build\agent2\devoff3-bin\rexruntime.dll', 'build\agent2\devoff3-bin\legodimensions.exe',
  'build\agent2\devoff4-bin\MANIFEST.txt', 'build\agent2\devoff4-bin\rexruntime.dll', 'build\agent2\devoff4-bin\legodimensions.exe'
)
$files += Get-ChildItem -LiteralPath (Join-Path $w 'bench\agent8\run') -File | Where-Object { $_.Extension -in '.ps1', '.py', '.cs' } | ForEach-Object { 'bench\agent8\run\' + $_.Name }
foreach ($dd in 'bench\agent8\run\drivers', 'bench\agent8\drivers') {
  $full = Join-Path $w $dd
  if (Test-Path -LiteralPath $full) { $files += Get-ChildItem -LiteralPath $full -File | ForEach-Object { $dd + '\' + $_.Name } }
}
$lines = @('# W5 inputs, hashed by Agent 1 at ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' (SHA-256, size, relative path)')
foreach ($f in $files) {
  $p = Join-Path $w $f
  if (Test-Path -LiteralPath $p) { $lines += '{0}  {1,10}  {2}' -f (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash, (Get-Item -LiteralPath $p).Length, $f }
  else { $lines += 'MISSING  {0}' -f $f }
}
[IO.File]::WriteAllText($out, (($lines -join "`n") + "`n"), [Text.Encoding]::ASCII)
$lines | Where-Object { $_ -match 'MANIFEST|rexruntime|toml|MISSING|RUN-WINDOW5|window5' }
'{0} entries -> {1}' -f ($lines.Count - 1), $out
