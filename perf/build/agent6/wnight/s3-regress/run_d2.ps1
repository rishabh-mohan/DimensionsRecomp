# Task s3 D2 (2026-11-25, E5.1 for M6): re-run the existing kit tests after the A/B/harness changes.
# New outputs only: build\agent6\wnight\s3-regress\d2-*.out.txt and out-test-*\. One process at a time, BelowNormal.
$ErrorActionPreference = 'Continue'
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
Set-Location (Join-Path $PSScriptRoot '..\..\..\..')
$S = 'build\agent6\wnight\s3-regress'
$jobs = @(
  @('stuck_parse',   'python -B build\agent6\w6\test_stuck_parse.py'),
  @('synth_make',    'python -B build\agent6\w6\make_synth.py'),
  @('synth_kit',     "python -B build\agent6\w6\w6_kit.py build\agent6\w6\test-synth\W6SYNTH --out $S\out-test-synth"),
  @('s4b17_make',    'python -B build\agent6\wnight\make_test_s4b17.py'),
  @('s4b17_kit',     "build\agent6\wnight\RUN-W9-LOGDIFF.cmd build\agent6\wnight\test-s4b17 --out $S\out-test-s4b17"),
  @('s4b17neg_make', 'python -B build\agent6\wnight\make_test_s4b17.py --neg'),
  @('s4b17neg_kit',  "build\agent6\wnight\RUN-W9-LOGDIFF.cmd build\agent6\wnight\test-s4b17-neg --out $S\out-test-s4b17-neg"),
  @('w9env',         'python -B build\agent6\wnight\make_test_w9env.py'),
  @('w9_usage',      'build\agent6\wnight\RUN-W9-LOGDIFF.cmd'),
  @('w6_usage',      'build\agent6\w6\RUN-W6-LOGDIFF.cmd')
)
foreach ($j in $jobs) {
  if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { Write-Output 'HOLD file exists, stopping'; exit 3 }
  $name, $c = $j
  cmd /c "$c > $S\d2-$name.out.txt 2>&1"
  Write-Output ("{0}: exit {1}  ({2})" -f $name, $LASTEXITCODE, $c)
}
