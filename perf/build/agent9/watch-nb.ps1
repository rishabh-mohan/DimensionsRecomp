# Agent 9: watch Agent 2's nativeB chain (rb-chain.ps1 -Variant nb), read-only. Exits when the chain ends, or early on
# the first ninja FAILED line in a snapB3n-*.log so it can be triaged while the build goes on. Then: item 1a (S3.9).
#   powershell -NoProfile -File build\agent9\watch-nb.ps1 [-Minutes 150] [-StopOnFail:$false]
# Log: build/agent9/logs/watch-nb.txt. Exit 0 chain DONE, 1 chain STOP, 3 first FAILED seen, 4 timeout.
param([int]$Minutes = 150, [bool]$StopOnFail = $true, [int]$PollSec = 20)
$ErrorActionPreference = 'Continue'
$A = '<workspace>\build\agent2'
$out = '<workspace>\build\agent9\logs\watch-nb.txt'
function Say([string]$m) { $l = "$(Get-Date -Format HH:mm:ss) $m"; Add-Content -Path $out -Value $l -Encoding UTF8; $l }
function ReadShared([string]$p) {
  try {
    $fs = [IO.File]::Open($p, 'Open', 'Read', 'ReadWrite')
    try { (New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8, $true)).ReadToEnd() } finally { $fs.Close() }
  } catch { '' }
}
function Short([string]$s, [int]$n) { $s.Substring(0, [Math]::Min($n, $s.Length)) }
function BuildLines {
  # every snapB3n-*.log build-snap writes (configure, gen-check, gate, game build); ninja progress and FAILED lines
  $all = @()
  foreach ($f in @(Get-ChildItem -LiteralPath $A -Filter 'snapB3n-*.log' -ErrorAction SilentlyContinue)) {
    $all += @((ReadShared $f.FullName) -split "`r?`n" | ForEach-Object { "$($f.Name)`t$_" })
  }
  $all
}
function Tail([string]$p, [int]$n, [string]$tag) {
  (ReadShared $p) -split "`r?`n" | Where-Object { $_ } | Select-Object -Last $n | ForEach-Object { Say ("  ${tag}: " + (Short $_ 220)) }
}
$sw = [Diagnostics.Stopwatch]::StartNew()
$lastProg = ''; $lastSay = [TimeSpan]::Zero
Say "START watch-nb (poll ${PollSec}s, limit $Minutes min, stop on first FAILED: $StopOnFail)"
while ($sw.Elapsed.TotalMinutes -lt $Minutes) {
  $lines = BuildLines
  $fails = @($lines | Where-Object { ($_ -split "`t", 2)[1] -match '^FAILED: ' })
  $prog = @($lines | Where-Object { ($_ -split "`t", 2)[1] -match '^\[\d+/\d+\]' } | Select-Object -Last 1)
  if ($prog -and $prog[0] -ne $lastProg -and ($sw.Elapsed - $lastSay).TotalSeconds -ge 120) {
    $lastProg = $prog[0]; $lastSay = $sw.Elapsed
    Say ("progress: " + (Short $lastProg 160))
  }
  if ($fails.Count -gt 0 -and $StopOnFail) {
    Start-Sleep -Seconds 30
    $lines = BuildLines
    $fails = @($lines | Where-Object { ($_ -split "`t", 2)[1] -match '^FAILED: ' })
    Say "FAILED lines: $($fails.Count)"
    $fails | Select-Object -First 10 | ForEach-Object { Say ("  " + (Short $_ 240)) }
    $errs = @($lines | Where-Object { ($_ -split "`t", 2)[1] -match 'error' })
    Say "error lines: $($errs.Count)"
    $errs | Select-Object -First 15 | ForEach-Object { Say ("  " + (Short $_ 300)) }
    exit 3
  }
  $chain = ReadShared "$A\rb-chain-nb.txt"
  if ($chain -match '\[rb-chain nb\] DONE') {
    Say "chain DONE; FAILED lines $($fails.Count)"
    Tail "$A\snapB3n-run.txt" 14 'run'
    Tail "$A\rb-chain-nb.txt" 6 'chain'
    exit 0
  }
  if ($chain -match '\[rb-chain nb\] STOP') {
    Say "chain STOP; FAILED lines $($fails.Count)"
    $fails | Select-Object -First 10 | ForEach-Object { Say ("  " + (Short $_ 240)) }
    Tail "$A\snapB3n-run.txt" 14 'run'
    Tail "$A\snapB3n-steps.txt" 8 'steps'
    Tail "$A\rb-chain-nb.txt" 6 'chain'
    exit 1
  }
  Start-Sleep -Seconds $PollSec
}
Say "timeout after $Minutes min; last progress: $lastProg"
exit 4
