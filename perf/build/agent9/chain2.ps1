# Agent 9: rebuild tool+producer (D redesign, B's flush elision, inert keys removed),
# run the producer, T1 off-identity, then the flush_mode_elision variant.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\chain2.ps1
# Every CPU-heavy step takes the Agent 9 slots itself (build-tool2.ps1, gen.ps1),
# and those wait while bench\agent9\QUIET exists.
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
$log = "$R\build\agent9\logs\chain2.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -Append -FilePath $log }
Note 'chain2 BEGIN'
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\build-tool2.ps1 -Jobs 2 *>&1 |
  Select-Object -Last 6 | ForEach-Object { Note "build: $_" }
$buildExit = $LASTEXITCODE
Note "build exit=$buildExit"
if ($buildExit -ne 0) { Note 'chain2 ABORT (build failed)'; exit 1 }
$out = "$R\build\agent9\regress\run4"
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
& "$R\build\agent9\bin\regression_interior_entries.exe" $out *>&1 |
  Select-Object -Last 5 | ForEach-Object { Note "producer: $_" }
Note "producer exit=$LASTEXITCODE"
powershell -NoProfile -File build\agent9\gen.ps1 -Variant off3 *>&1 | Out-Null
Note "gen off3 exit=$LASTEXITCODE"
powershell -NoProfile -File build\agent9\diff-gen.ps1 -A build\agent2\gen-noflag\default -B build\agent9\generated\off3\default *>&1 |
  Select-Object -Last 14 | ForEach-Object { Note "diff: $_" }
powershell -NoProfile -File build\agent9\gen.ps1 -Variant flush -Options 'flush_mode_elision = true' *>&1 | Out-Null
Note "gen flush exit=$LASTEXITCODE"
Note 'chain2 END'
