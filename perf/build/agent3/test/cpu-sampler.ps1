# build/agent3/test/cpu-sampler.ps1 - machine CPU load next to a game run (Agent 3; read-only perf counters, 1 thread).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\test\cpu-sampler.ps1 [-Seconds 900] [-Out build\agent3\logs\cpu-sampler.csv]
# Columns: total busy % of the machine, CPU performance % (of the 1.7 GHz base), and cores used by a few processes.
param([int]$Seconds = 900, [string]$Out = 'build\agent3\logs\cpu-sampler.csv')
$names = @('msmpeng', 'presentmon_x64', 'dwm', 'legodimensions', 'rg', 'clang++', 'ninja', 'python', 'powershell')
$list = @('\Processor Information(_Total)\% Processor Time', '\Processor Information(_Total)\% Processor Performance') + ($names | ForEach-Object { "\Process($_)\% Processor Time" })
'time,total_pct,perf_pct,' + (($names | ForEach-Object { ($_ -replace '\+', 'p') + '_cores' }) -join ',') | Out-File -Encoding ascii $Out
$end = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $end) {
    $s = Get-Counter -Counter $list -SampleInterval 2 -MaxSamples 1 -ErrorAction SilentlyContinue
    $tot = ''; $perf = ''; $v = @{}
    if ($s) {
        foreach ($c in $s.CounterSamples) {
            $p = $c.Path.ToLowerInvariant()
            if ($p -match 'processor information\(_total\)\\% processor time') { $tot = '{0:F1}' -f $c.CookedValue }
            elseif ($p -match 'processor information\(_total\)\\% processor performance') { $perf = '{0:F1}' -f $c.CookedValue }
            elseif ($p -match '\\process\(([^)#]+)\)\\') { $k = $Matches[1]; if (-not $v.ContainsKey($k)) { $v[$k] = 0.0 }; $v[$k] += $c.CookedValue / 100.0 }
        }
    }
    $row = @((Get-Date -Format 'HH:mm:ss'), $tot, $perf) + ($names | ForEach-Object { if ($v.ContainsKey($_)) { '{0:F2}' -f $v[$_] } else { '' } })
    ($row -join ',') | Out-File -Encoding ascii -Append $Out
}
