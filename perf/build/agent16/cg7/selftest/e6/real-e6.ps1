$ErrorActionPreference = 'Stop'
Set-Location <workspace>
$g = 'build\agent3\gameplay'
$log = 'build\agent16\cg7\selftest\e6\real-e6.log'
$runs = @(
  @{ label = 'base073150'; trace = "$g\trace-native5-20261126-073150\events.tsv"; log = "$g\runs\20261126-073156-gp5-native\game.log"; runlog = "$g\logs\gameplay-20261126-073150.txt"; out = 'build\agent16\cg7\roles-073150' },
  @{ label = 'B082648'; trace = "$g\trace-native5d-20261126-082648\events.tsv"; log = "$g\runs\20261126-082653-gp5d-native\game.log"; runlog = "$g\logs\gameplay-20261126-082648.txt"; out = 'build\agent16\cg7\roles-082648' }
)
"real-data e6_roles runs $(Get-Date -Format s)" | Out-File -Encoding ascii $log
foreach ($r in $runs) {
  "== $($r.label)" | Out-File -Encoding ascii -Append $log
  cmd /c "python -B build\agent16\cg7\e6_roles.py --trace $($r.trace) --log $($r.log) --runlog $($r.runlog) --fp a349d5292f67b127 --label $($r.label) --out $($r.out) >> $log 2>&1"
  "exit=$LASTEXITCODE" | Out-File -Encoding ascii -Append $log
}
