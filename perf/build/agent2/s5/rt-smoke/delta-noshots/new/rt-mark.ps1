# rt-mark.ps1 - read-only timing helper for the matched manual capture of RUN-RT-SMOKE noshots (M2). It never launches,
# closes, focuses or sends input to anything; it only reads Get-Process. The kit's game = the newest legodimensions.exe
# whose image is under rt-smoke\runs\ (run-game hard-links the bin into each run dir) and that is younger than 235 s
# (an arm is 240 s, so the previous arm's game is never picked). The route clock starts at the process start (+-0.5 s).
#   rt-mark.ps1                  wait (<= -Timeout s) for the kit's game; print pid, run dir, start and target clock times
#   rt-mark.ps1 -Until 122.25    then block until start + 122.25 s - Lead; exit 0. Exit 2 = no game, or already > 1 s past.
param([double]$Until = -1, [double]$Lead = 0.5, [double[]]$Times = @(60, 122.25, 146.75, 201.5), [int]$Timeout = 180)
$rr = (Join-Path $PSScriptRoot 'rt-smoke\runs').TrimEnd('\') + '\'
$deadline = (Get-Date).AddSeconds($Timeout); $p = $null
while (-not $p) {
    $p = Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object {
        $x = try { $_.Path } catch { '' }
        $x -and $x.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) -and $_.StartTime -gt (Get-Date).AddSeconds(-235) } |
        Sort-Object StartTime | Select-Object -Last 1
    if (-not $p) {
        if ((Get-Date) -ge $deadline) { 'rt-mark: no kit game process'; exit 2 }
        Start-Sleep -Milliseconds 250
    }
}
$t0 = $p.StartTime
$run = Split-Path -Leaf (Split-Path -Parent $p.Path)
if ($Until -lt 0) {
    "rt-mark: pid $($p.Id) run $run started $($t0.ToString('HH:mm:ss.fff'))"
    foreach ($t in $Times) { '  {0,6:0.##} s = {1}' -f $t, $t0.AddSeconds($t).ToString('HH:mm:ss.f') }
    exit 0
}
$wait = ($t0.AddSeconds($Until - $Lead) - (Get-Date)).TotalMilliseconds
if ($wait -lt -1000) { 'rt-mark: {0} s already past (now {1:N1} s, run {2})' -f $Until, ((Get-Date) - $t0).TotalSeconds, $run; exit 2 }
if ($wait -gt 0) { Start-Sleep -Milliseconds ([int]$wait) }
'rt-mark: pid {0} run {1} at {2:N2} s (target {3} s, lead {4} s)' -f $p.Id, $run, ((Get-Date) - $t0).TotalSeconds, $Until, $Lead
exit 0
