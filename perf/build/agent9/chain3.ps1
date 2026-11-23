# Agent 9: first jobs after quiet window 2: rebuild the tool, then run fixture D (run7).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\chain3.ps1 *> build\agent9\logs\chain3.out.txt
# build-tool2.ps1 takes both Agent 9 slots itself and waits while bench\agent9\QUIET exists.
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
Set-Location $R
$steps = "$R\build\agent9\logs\chain3-steps.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -Append -FilePath $steps }
Note 'BEGIN build-tool2 -Jobs 2'
& powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\build-tool2.ps1 -Jobs 2 *> build\agent9\logs\build-tool2-run7.out.txt
$code = $LASTEXITCODE
Get-Content build\agent9\logs\build-tool2-steps.txt -Tail 6 | ForEach-Object { Note "  $_" }
if ($code -ne 0) { Note "build-tool2 FAILED exit=$code"; exit 1 }
$sha = (Get-FileHash build\agent9\bin\rexglue.exe -Algorithm SHA256).Hash.Substring(0, 16)
Note "tool sha=$sha"
if ($sha -eq 'EEBB5406CF78E392') { Note 'tool unchanged: stop'; exit 2 }
New-Item -ItemType Directory -Force build\agent9\regress\run7 | Out-Null
. "$R\bench\agent9\slots.ps1"
$held = Enter-Agent9Slots 1
try {
  & build\agent9\bin\regression_interior_entries.exe build\agent9\regress\run7 *> build\agent9\logs\regress-run7.txt
  $rc = $LASTEXITCODE
} finally { Exit-Agent9Slots $held }
Note "fixture D run7 exit=$rc"
Get-Content build\agent9\logs\regress-run7.txt -Tail 4 | ForEach-Object { Note "  $_" }
if ($rc -ne 0) { exit 3 }
Note 'END ok'
