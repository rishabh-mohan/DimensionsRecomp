# Agent 9: rebuild tool+producer, run the producer, T1 off-identity, then the cr_compare_so_zero variants.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\chain.ps1
# Every CPU-heavy step takes the Agent 9 slots itself (build-tool2.ps1, gen.ps1).
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
$log = "$R\build\agent9\logs\chain.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -Append -FilePath $log }
Note 'chain BEGIN'
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\build-tool2.ps1 -Jobs 2 *>&1 |
  Select-Object -Last 6 | ForEach-Object { Note "build: $_" }
Note "build exit=$LASTEXITCODE"
$out = "$R\build\agent9\regress\run3"
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
& "$R\build\agent9\bin\regression_interior_entries.exe" $out *>&1 |
  Select-Object -Last 5 | ForEach-Object { Note "producer: $_" }
Note "producer exit=$LASTEXITCODE"
powershell -NoProfile -File build\agent9\gen.ps1 -Variant off2 *>&1 | Out-Null
Note "gen off2 exit=$LASTEXITCODE"
powershell -NoProfile -File build\agent9\diff-gen.ps1 -A build\agent2\gen-noflag\default -B build\agent9\generated\off2\default *>&1 |
  Select-Object -Last 14 | ForEach-Object { Note "diff: $_" }
powershell -NoProfile -File build\agent9\gen.ps1 -Variant crso -Options 'cr_compare_so_zero = true' *>&1 | Out-Null
Note "gen crso exit=$LASTEXITCODE"
powershell -NoProfile -File build\agent9\gen.ps1 -Variant crsoA -Options 'skip_lr = true;ctr_as_local = true;xer_as_local = true;reserved_as_local = true;cr_as_local = true;cr_compare_so_zero = true' *>&1 | Out-Null
Note "gen crsoA exit=$LASTEXITCODE"
Note 'chain END'
