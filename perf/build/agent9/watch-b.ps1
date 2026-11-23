# Agent 9: watch Agent 2's build B (read-only). Exits when the chain ends, or early on the first ninja FAILED line so a
# codegen failure can be triaged (musttail -> rollback 9.2 install\rb2-nomusttail) while -k 0 keeps building.
#   powershell -NoProfile -File build\agent9\watch-b.ps1 [-Minutes 60] [-StopOnFail:$false]
# Log: build/agent9/logs/watch-b.txt. Exit 0 chain DONE, 1 chain STOP, 3 first FAILED seen, 4 timeout.
param([int]$Minutes = 60, [bool]$StopOnFail = $true, [int]$PollSec = 20)
$ErrorActionPreference = 'Continue'
$A = '<workspace>\build\agent2'
$out = '<workspace>\build\agent9\logs\watch-b.txt'
function Say([string]$m) { $l = "$(Get-Date -Format HH:mm:ss) $m"; Add-Content -Path $out -Value $l -Encoding UTF8; $l }
function ReadShared([string]$p) {
  try {
    $fs = [IO.File]::Open($p, 'Open', 'Read', 'ReadWrite')
    try { (New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8, $true)).ReadToEnd() } finally { $fs.Close() }
  } catch { '' }
}
$sw = [Diagnostics.Stopwatch]::StartNew()
$lastProg = ''; $lastSay = [TimeSpan]::Zero
Say "START watch-b (poll ${PollSec}s, limit $Minutes min, stop on first FAILED: $StopOnFail)"
while ($sw.Elapsed.TotalMinutes -lt $Minutes) {
  $build = ReadShared "$A\snapB-game-build.log"
  $lines = $build -split "`r?`n"
  $fails = @($lines | Where-Object { $_ -match '^FAILED: ' })
  $prog = @($lines | Where-Object { $_ -match '^\[\d+/\d+\]' } | Select-Object -Last 1)
  if ($prog -and $prog[0] -ne $lastProg -and ($sw.Elapsed - $lastSay).TotalSeconds -ge 120) {
    $lastProg = $prog[0]; $lastSay = $sw.Elapsed
    Say ("progress: " + $lastProg.Substring(0, [Math]::Min(140, $lastProg.Length)))
  }
  if ($fails.Count -gt 0 -and $StopOnFail) {
    Start-Sleep -Seconds 30
    $lines = (ReadShared "$A\snapB-game-build.log") -split "`r?`n"
    $fails = @($lines | Where-Object { $_ -match '^FAILED: ' })
    Say "FAILED lines: $($fails.Count)"
    $fails | Select-Object -First 10 | ForEach-Object { Say ("  " + $_.Substring(0, [Math]::Min(220, $_.Length))) }
    $errs = @($lines | Where-Object { $_ -match 'error:' })
    Say "error: lines: $($errs.Count)"
    $errs | Select-Object -First 15 | ForEach-Object { Say ("  " + $_.Substring(0, [Math]::Min(300, $_.Length))) }
    exit 3
  }
  $chain = ReadShared "$A\b-chain.txt"
  if ($chain -match '\[chain\] DONE build B chain') {
    Say "chain DONE; FAILED lines $($fails.Count)"
    (ReadShared "$A\snapB-run.txt") -split "`r?`n" | Select-Object -Last 12 | Where-Object { $_ } | ForEach-Object { Say ("  run: " + $_.Substring(0, [Math]::Min(220, $_.Length))) }
    $chain -split "`r?`n" | Select-Object -Last 8 | Where-Object { $_ } | ForEach-Object { Say ("  chain: " + $_.Substring(0, [Math]::Min(220, $_.Length))) }
    exit 0
  }
  if ($chain -match '\[chain\] STOP') {
    Say "chain STOP; FAILED lines $($fails.Count)"
    $fails | Select-Object -First 10 | ForEach-Object { Say ("  " + $_.Substring(0, [Math]::Min(220, $_.Length))) }
    (ReadShared "$A\snapB-run.txt") -split "`r?`n" | Select-Object -Last 12 | Where-Object { $_ } | ForEach-Object { Say ("  run: " + $_.Substring(0, [Math]::Min(220, $_.Length))) }
    (ReadShared "$A\snapB-steps.txt") -split "`r?`n" | Select-Object -Last 8 | Where-Object { $_ } | ForEach-Object { Say ("  steps: " + $_.Substring(0, [Math]::Min(220, $_.Length))) }
    exit 1
  }
  Start-Sleep -Seconds $PollSec
}
Say "timeout after $Minutes min; last progress: $lastProg"
exit 4
