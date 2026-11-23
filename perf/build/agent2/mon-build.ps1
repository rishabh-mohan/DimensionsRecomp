# Agent 2 - samples memory + build progress every $Every seconds until "$Steps" shows "END   build".
# powershell -NoProfile -File build\agent2\mon-build.ps1 -Steps build\agent2\game-baseline-steps.txt -BuildLog build\agent2\game-build.log -Out build\agent2\game-mon.txt
param([string]$Steps, [string]$BuildLog, [string]$Out, [int]$Every = 30, [int]$MaxMinutes = 240)
$R = '<workspace>'
Set-Location $R
$deadline = (Get-Date).AddMinutes($MaxMinutes)
while ((Get-Date) -lt $deadline) {
    $os = Get-CimInstance Win32_OperatingSystem
    $cl = @(Get-Process -Name clang, clang++, 'clang-cl', 'lld-link' -ErrorAction SilentlyContinue)
    $ws = ($cl | Measure-Object WorkingSet64 -Sum).Sum
    $mx = ($cl | Measure-Object WorkingSet64 -Maximum).Maximum
    $prog = ''
    if (Test-Path $BuildLog) {
        $last = Get-Content $BuildLog -Tail 40 | Where-Object { $_ -match '^\[\d+/\d+\]' } | Select-Object -Last 1
        if ($last) { $prog = ($last -split ' ')[0] }
    }
    '{0} freeRAM={1:N2}GB freeCommit={2:N2}GB clang={3} clangWS={4:N2}GB maxWS={5:N2}GB {6}' -f (Get-Date -Format HH:mm:ss),
        ($os.FreePhysicalMemory / 1MB), ($os.FreeVirtualMemory / 1MB), $cl.Count, ($ws / 1GB), ($mx / 1GB), $prog |
        Out-File -Append -Encoding utf8 $Out
    # Stop once every "BEGIN build" line has a matching "END   build" (steps files accumulate across runs).
    if (Test-Path $Steps) {
        $nb = @(Select-String -Path $Steps -Pattern 'BEGIN build').Count
        $ne = @(Select-String -Path $Steps -Pattern 'END   build').Count
        if ($nb -gt 0 -and $ne -ge $nb) { break }
    }
    Start-Sleep -Seconds $Every
}
