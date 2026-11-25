# Task s3 (2026-11-25, E5.1 for M6): re-run the kit with each night wrapper's rules on the 7 night dirs.
# New outputs only: build\agent6\wnight\s3-regress\out-<W>-<dir>\ and <W>-<dir>.out.txt. Stored night outputs untouched.
# One process at a time, BelowNormal (the wrapper also starts python /belownormal).
$ErrorActionPreference = 'Stop'
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
Set-Location (Join-Path $PSScriptRoot '..\..\..\..')
$jobs = @(
  @('W6', '20261123-0009', 'build\agent6\w6\RUN-W6-LOGDIFF.cmd'),
  @('W6', '20261123-0313', 'build\agent6\w6\RUN-W6-LOGDIFF.cmd'),
  @('W9', '20261123-0108', 'build\agent6\wnight\RUN-W9-LOGDIFF.cmd'),
  @('W9', '20261123-0401', 'build\agent6\wnight\RUN-W9-LOGDIFF.cmd'),
  @('W5B', '20261123-0155', 'build\agent6\wnight\RUN-W5B-LOGDIFF.cmd'),
  @('W5B', '20261123-0451', 'build\agent6\wnight\RUN-W5B-LOGDIFF.cmd'),
  @('W4C', '20261123-0239', 'build\agent6\wnight\RUN-W4C-LOGDIFF.cmd')
)
foreach ($j in $jobs) {
  if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { Write-Output 'HOLD file exists, stopping'; exit 3 }
  $w, $d, $cmd = $j
  $out = "build\agent6\wnight\s3-regress\out-$w-$d"
  $txt = "build\agent6\wnight\s3-regress\$w-$d.out.txt"
  cmd /c "$cmd build\agent8\matrix\$d --out $out > $txt 2>&1"
  Write-Output ("{0}-{1}: exit {2}" -f $w, $d, $LASTEXITCODE)
}
