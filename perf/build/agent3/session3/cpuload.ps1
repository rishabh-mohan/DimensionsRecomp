# cpuload.ps1 - M3 (session 3, RUNPLANS.md section d2): the controlled CPU load for the f10aL/f10bL pair.
# Starts -Threads busy-loop powershell children (Start-Process -PassThru, hidden, Normal priority), each of which ends
# by itself after -Minutes, records their pids in build\agent3\session3\cpuload.pids and on exit kills ONLY those
# pids (checked by pid AND start time, so a reused pid is never touched). Touches no other process.
# Stop early: Ctrl+C, or create build\agent3\session3\cpuload.STOP. Writes build\agent3\session3\cpuload.log.
# Do NOT run during the machine-load HOLD; only after the Overseer's LOAD GO, on a host with no build and no Minecraft.
param([int]$Threads = 8, [int]$Minutes = 25)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$log = Join-Path $here 'cpuload.log'
$pidf = Join-Path $here 'cpuload.pids'
$stop = Join-Path $here 'cpuload.STOP'
function Say([string]$m) { $l = (Get-Date -Format 'HH:mm:ss') + ' ' + $m; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
if (Test-Path -LiteralPath $stop) { Remove-Item -LiteralPath $stop }
$sec = $Minutes * 60
# each child spins until its own deadline, so nothing outlives -Minutes even if this script dies
$body = "`$e=(Get-Date).AddSeconds($sec); `$x=0; while((Get-Date) -lt `$e){ for(`$i=0;`$i -lt 200000;`$i++){ `$x=`$x+`$i } }"
$kids = @()
try {
    for ($i = 0; $i -lt $Threads; $i++) {
        $p = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-NonInteractive', '-Command', $body) `
            -WindowStyle Hidden -PassThru
        $kids += [pscustomobject]@{ Id = $p.Id; Start = $p.StartTime; P = $p }
    }
    $kids | ForEach-Object { "$($_.Id) $($_.Start.ToString('o'))" } | Set-Content -LiteralPath $pidf
    Say "cpuload: $Threads busy children for $Minutes min: $(($kids.Id) -join ',')"
    $end = (Get-Date).AddSeconds($sec + 5)
    while ((Get-Date) -lt $end -and -not (Test-Path -LiteralPath $stop)) {
        if (-not ($kids | Where-Object { -not $_.P.HasExited })) { break }
        Start-Sleep -Seconds 5
    }
} finally {
    foreach ($k in $kids) {
        try {
            if (-not $k.P.HasExited -and $k.P.StartTime -eq $k.Start) { $k.P.Kill(); Say "cpuload: stopped own child $($k.Id)" }
        } catch { }
    }
    Say 'cpuload ends'
}
