# Agent 1: pre-GO check for tonight's windows. Without -Go it only checks.
# With -Go and every check passing, it writes perf-notes\WINDOW-GO.txt from build\agent1\night\GO-<Window>.txt.
param(
  [Parameter(Mandatory = $true)][ValidatePattern('^W[0-9A-Za-z-]+$')][string]$Window,
  [string]$Latest = '',   # session 3: 'HH:mm' latest GO; default 07:30 - 10 min margin - 10 min gate - runner estimate (pass -Latest)
  [switch]$Go
)
$ErrorActionPreference = 'Stop'
$root = '<workspace>'
$night = Join-Path $root 'build\agent1\night'
$pn = Join-Path $root 'perf-notes'
$latestTbl = @{ 'W6' = '06:22'; 'W9' = '06:22'; 'W5b' = '06:26'; 'W4c' = '06:40' }  # second passes (SESSION2 03:09): 07:30 - 10 min margin - 10 min gate - runner estimate
if ($Latest) { $latestTbl[$Window] = $Latest } elseif (-not $latestTbl.ContainsKey($Window)) { $latestTbl[$Window] = '06:00' }
$fail = New-Object System.Collections.Generic.List[string]
$now = Get-Date
"now: " + $now.ToString('yyyy-MM-dd HH:mm:ss') + "  window: $Window  latest GO: " + $latestTbl[$Window]

# 1. GO line and the matrix sha
$goFile = Join-Path $night ("GO-" + $Window + ".txt")
$lines = @(Get-Content -LiteralPath $goFile | Where-Object { $_.Trim() -ne '' })
if ($lines.Count -ne 1) { $fail.Add("GO-$Window.txt has $($lines.Count) non-empty lines") }
$line = ($lines[0]).Trim()
$tok = $line -split '\s+'
if ($tok.Count -ne 6 -or $tok[0] -ne 'GO' -or $tok[1] -ne $Window -or $tok[4] -notlike 'only=*' -or $tok[5] -notlike 'repeats=*') { $fail.Add("malformed GO line: $line") }
$json = Join-Path $root ('bench\agent8\run\' + $tok[2])
if (-not (Test-Path -LiteralPath $json)) { $fail.Add("matrix missing: $json") }
else {
  $h = (Get-FileHash -LiteralPath $json -Algorithm SHA256).Hash
  if ($h -ne $tok[3].ToUpper()) { $fail.Add("sha mismatch: file $h vs GO $($tok[3])") } else { "sha OK: $($tok[2]) $h" }
}
"GO line: $line"

# 2. time: GOs only between 00:00 and the window's latest GO
$lt = [datetime]::ParseExact($latestTbl[$Window], 'HH:mm', $null)
if ($now.Hour -ge 12) { $fail.Add('before midnight: no GO before 00:00') }
elseif ($now.TimeOfDay -gt $lt.TimeOfDay) { $fail.Add("past the latest GO " + $latestTbl[$Window]) }

# 3. control files
foreach ($f in 'WINDOW-HOLD.txt', 'WINDOW-GO.txt', 'WINDOW-STOP.txt') {
  if (Test-Path -LiteralPath (Join-Path $pn $f)) { $fail.Add("$f exists") }
}

# 4. processes: no builds, no game, no runner; the night launcher running
$bad = @(Get-Process -Name ninja, cmake, 'clang++', clang, 'clang-cl', 'lld-link', link, cl, msbuild, legodimensions -ErrorAction SilentlyContinue)
if ($bad.Count) { $fail.Add('busy: ' + (($bad | Group-Object Name | ForEach-Object { $_.Name + ' x' + $_.Count }) -join ', ')) }
$ps = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" | Select-Object ProcessId, CommandLine)
$runner = @($ps | Where-Object { $_.CommandLine -like '*run-matrix.ps1*' })
if ($runner.Count) { $fail.Add('run-matrix running: ' + (($runner | ForEach-Object { $_.ProcessId }) -join ',')) }
$launcher = @($ps | Where-Object { $_.CommandLine -like '*run-night.ps1*' })
if (-not $launcher.Count) { $fail.Add('night launcher (run-night.ps1) not running') } else { 'launcher pid(s): ' + (($launcher | ForEach-Object { $_.ProcessId }) -join ',') }

# 5. launcher status log
$log = Join-Path $root 'bench\agent5\launch\status\log.txt'
if (Test-Path -LiteralPath $log) { 'launcher log tail:'; Get-Content -LiteralPath $log -Tail 4 | ForEach-Object { '  ' + $_ } } else { 'no launcher status log yet' }
'free GB: ' + [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)

if ($fail.Count) {
  'NOT READY:'
  $fail | ForEach-Object { ' - ' + $_ }
  if ($Go) { 'GO NOT WRITTEN' }
  exit 1
}
'READY'
if ($Go) {
  $dst = Join-Path $pn 'WINDOW-GO.txt'
  [System.IO.File]::WriteAllText($dst, $line + "`r`n", (New-Object System.Text.UTF8Encoding($false)))
  'GO WRITTEN ' + (Get-Date).ToString('HH:mm:ss') + ': ' + (Get-Content -LiteralPath $dst)
}
