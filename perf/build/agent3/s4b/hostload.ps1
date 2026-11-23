# Agent 3, run 2 task 2: host-load sampler for the functional queue (Agent 1, 21:54: flag a devoff4b row whose
# post-title menu phase is still > 2x devoff4's (> 17.4 s) when run WITHOUT the compile load).
# Every 30 s: time, clang++/cl/ninja/link process counts, total CPU load %, and my game's pid if one runs.
# Writes build\agent3\s4b\logs\hostload.csv. Read-only on everything else; stops at -Until.
# Task #23 (11-23, quiet-host f10 rows): one more column, top = the 4 process names with the most CPU over the last
# interval (% of all logical processors, the instances of a name summed; only processes whose CPU time this user can
# read), so the rows around a hang show what else ran. A hostload.csv with the old header is renamed first
# (hostload-<yyyyMMdd>.csv, the date of its last write), so every file keeps one header.
param([string]$Until = '23:40:00')
$ErrorActionPreference = 'SilentlyContinue'
[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
$repo = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$out = Join-Path $PSScriptRoot 'logs\hostload.csv'
$hdr = 'time,clang,cl,ninja,link,cpu_pct,game_pid,top'
if ((Test-Path $out) -and ([string](Get-Content -LiteralPath $out -TotalCount 1) -ne $hdr)) {
    $old = Get-Item -LiteralPath $out
    $nn = 'hostload-' + $old.LastWriteTime.ToString('yyyyMMdd') + '.csv'
    if (Test-Path (Join-Path $old.DirectoryName $nn)) { $nn = 'hostload-' + $old.LastWriteTime.ToString('yyyyMMdd-HHmmss') + '.csv' }
    Rename-Item -LiteralPath $out -NewName $nn
}
if (-not (Test-Path $out)) { $hdr | Set-Content -LiteralPath $out -Encoding ascii }
$end = [datetime]::Today.Add([timespan]::Parse($Until))
$nc = [Environment]::ProcessorCount
$prev = @{}; $prevT = $null
while ((Get-Date) -lt $end) {
    $p = Get-Process
    $now = Get-Date
    $n = { param($name) @($p | Where-Object { $_.ProcessName -eq $name }).Count }
    $cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
    $g = @($p | Where-Object { $_.ProcessName -eq 'legodimensions' } | Select-Object -ExpandProperty Id) -join ' '
    $cur = @{}
    foreach ($q in $p) { if ($null -ne $q.CPU) { $cur[$q.Id] = @($q.ProcessName, [double]$q.CPU) } }
    $top = ''
    if ($prevT) {
        $dt = ($now - $prevT).TotalSeconds
        $by = @{}
        foreach ($k in $cur.Keys) {
            if ($prev.ContainsKey($k)) {
                $d = $cur[$k][1] - $prev[$k]
                if ($d -gt 0) { $nm = $cur[$k][0]; if (-not $by.ContainsKey($nm)) { $by[$nm] = 0.0 }; $by[$nm] += $d }
            }
        }
        $top = @($by.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 4 |
            ForEach-Object { '{0} {1:0.0}%' -f $_.Key, ($_.Value / $dt / $nc * 100) }) -join ' / '
    }
    $prev = @{}; foreach ($k in $cur.Keys) { $prev[$k] = $cur[$k][1] }; $prevT = $now
    '{0},{1},{2},{3},{4},{5},{6},{7}' -f $now.ToString('HH:mm:ss'), (& $n 'clang++'), (& $n 'cl'), (& $n 'ninja'), (& $n 'link'), [int]$cpu, $g, $top |
        Add-Content -LiteralPath $out -Encoding ascii
    Start-Sleep -Seconds 30
}
