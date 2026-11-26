# wait-s5.ps1 - S5 waiter (Overseer). Opened once on the visible desktop with the user's approval;
# then waits for GO files and runs the listed, hash-pinned .cmd scripts one after another.
#   GO file: build\agent1\s5wait\GO.txt, one job per line:  <abs path to .cmd under WS\build\>|<sha256>|<args (optional)>
#   STOP:    create build\agent1\s5wait\STOP.txt to end the waiter.
# Refuses a job whose path is outside WS\build\, isn't a .cmd, or whose sha256 differs; never starts a job while
# legodimensions.exe runs. Exits at -StopAt (default 23:30).
param(
  [string]$StopAt = '23:30',
  [int]$PollSec = 15,
  [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'
$Here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$WS    = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$Build = (Join-Path $WS 'build') + '\'
$GoFile   = Join-Path $Here 'GO.txt'
$StopFile = Join-Path $Here 'STOP.txt'
$Status   = Join-Path $Here 'status.txt'
$Done     = Join-Path $Here 'done'
New-Item -ItemType Directory -Force -Path $Done | Out-Null

function Log([string]$m) {
  $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
  Write-Host $line
  Add-Content -Path $Status -Value $line -Encoding UTF8
}

$mutex = New-Object System.Threading.Mutex($false, 'Local\LegoS5Waiter')
if (-not $mutex.WaitOne(0)) { Write-Host 'wait-s5: another waiter is already running'; exit 3 }

$stop = [datetime]::ParseExact($StopAt, 'HH:mm', $null)
if ($stop -lt (Get-Date)) { $stop = $stop.AddDays(1) }
Log ("waiter start pid=$PID ws=$WS stop_at=$($stop.ToString('yyyy-MM-dd HH:mm')) selftest=$SelfTest")

function Run-Job([string]$line) {
  $parts = $line.Split('|')
  if ($parts.Count -lt 2) { Log "REFUSED (format): $line"; return 2 }
  $path = $parts[0].Trim(); $want = $parts[1].Trim().ToUpperInvariant()
  $args_ = if ($parts.Count -ge 3) { $parts[2].Trim() } else { '' }
  if ($args_ -match '[&|<>^%]') { Log "REFUSED (args chars): $line"; return 2 }
  try { $full = [IO.Path]::GetFullPath($path) } catch { Log "REFUSED (path): $path"; return 2 }
  if (-not $full.StartsWith($Build, [StringComparison]::OrdinalIgnoreCase)) { Log "REFUSED (outside build\): $full"; return 2 }
  if ([IO.Path]::GetExtension($full) -ne '.cmd') { Log "REFUSED (not .cmd): $full"; return 2 }
  if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { Log "REFUSED (missing): $full"; return 2 }
  $got = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
  if ($got -ne $want) { Log "REFUSED (sha256 $got != $want): $full"; return 2 }
  while (Get-Process -Name legodimensions -ErrorAction SilentlyContinue) {
    Log 'waiting: legodimensions.exe is running'; Start-Sleep -Seconds 30
    if (Test-Path $StopFile) { return 4 }
  }
  Log "RUN $full $args_ (sha256 $got)"
  $p = Start-Process -FilePath $env:ComSpec -ArgumentList ('/c ""{0}" {1}"' -f $full, $args_) `
        -WorkingDirectory (Split-Path -Parent $full) -PassThru -Wait
  Log ("END $full exit=$($p.ExitCode)")
  return $p.ExitCode
}

try {
  while ((Get-Date) -lt $stop) {
    if (Test-Path $StopFile) { Log 'STOP file seen'; break }
    if (Test-Path $GoFile) {
      $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
      $taken = Join-Path $Done "GO-$stamp.txt"
      Move-Item -LiteralPath $GoFile -Destination $taken
      Log "GO taken -> $taken"
      foreach ($l in (Get-Content -LiteralPath $taken)) {
        if ($l.Trim() -eq '' -or $l.TrimStart().StartsWith('#')) { continue }
        $rc = Run-Job $l
        if ($rc -eq 4) { break }
        if (Test-Path $StopFile) { Log 'STOP file seen after job'; break }
      }
      if ($SelfTest) { break }
    }
    Start-Sleep -Seconds $PollSec
  }
} finally {
  Log 'waiter exit'
  $mutex.ReleaseMutex()
}
