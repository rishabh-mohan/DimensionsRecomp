# w9_clock_check.ps1 -- Agent 9, task #30 (2026-11-23). Read-only: reads runner logs and threads.csv, writes nothing.
#
# Why: in W9's second pass (build/agent8/matrix/20261123-0401) some q125/q250 runs used more CPU and drew fewer
# frames than the other runs of the same arm. This prints, per run of each W9 pass:
#   start time, frames in the 50 s window, process CPU (cores), effective clock (all / P / E cores, MHz),
#   E-core utility %, and the busy % of the Main XThread and GPU Commands threads (threads.csv), plus the sum of all
#   threads' busy %.
# A run is marked "lowclk" when its effective clock is >= 100 MHz under the median of its own arm in the same pass.
# Spinning arms (off, q0) sit at lower clocks than the back-off arms in every run, so compare only within an arm.
#
# Usage (from the workspace root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\handoff\w9_clock_check.ps1 |
#     Out-File -Encoding utf8 build\agent9\handoff\w9-clock-check.txt
param(
    [string[]]$Matrix = @('build\agent8\matrix\20261123-0108', 'build\agent8\matrix\20261123-0401'),
    [int]$LowClockMHz = 100
)

if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { 'HOLD: perf-notes\WINDOW-HOLD.txt exists; not running.'; exit 3 }

function Get-Median([double[]]$v) {
    $s = $v | Sort-Object
    $n = $s.Count
    if ($n -eq 0) { return [double]::NaN }
    if ($n % 2) { return [double]$s[($n - 1) / 2] }
    return ([double]$s[$n / 2 - 1] + [double]$s[$n / 2]) / 2
}

$sysRe = 'eff (\d+) MHz \(min (\d+); P (\d+) / E (\d+)\), util ([\d\.]+)% \(P ([\d\.]+) / E ([\d\.]+)\)'
$bad = 0
foreach ($m in $Matrix) {
    $logs = Join-Path $m 'logs'
    $runs = Join-Path $m 'runs'
    if (-not (Test-Path $logs)) { "== $m : no logs folder"; $bad++; continue }
    $rows = @()
    foreach ($f in (Get-ChildItem $logs -Filter '*.txt' | Sort-Object Name)) {
        $t = Get-Content $f.FullName
        # File names: NN-<arm>-rK.txt or NN-cold-off.txt
        $parts = $f.BaseName -split '-'
        $arm = if ($parts[1] -eq 'cold') { 'off(cold)' } else { $parts[1] }
        $runDirLine = $t | Where-Object { $_ -like 'run dir: *' } | Select-Object -First 1
        $runLeaf = if ($runDirLine) { Split-Path -Leaf ($runDirLine -replace '^run dir: ', '') } else { '' }
        $start = ''
        $sl = $t | Where-Object { $_ -match '^started pid \d+ at (\d\d:\d\d:\d\d)' } | Select-Object -First 1
        if ($sl -and $sl -match 'at (\d\d:\d\d:\d\d)') { $start = $Matches[1] }
        $frames = ''
        $fl = $t | Where-Object { $_ -match '^frames\s+(\d+) frames' } | Select-Object -First 1
        if ($fl -and $fl -match '^frames\s+(\d+) frames') { $frames = [int]$Matches[1] }
        $cpu = ''
        $cl = $t | Where-Object { $_ -match '^process\s+window cpu mean ([\d\.]+) cores' } | Select-Object -First 1
        if ($cl -and $cl -match 'cpu mean ([\d\.]+) cores') { $cpu = [double]$Matches[1] }
        $eff = $effP = $effE = $utilE = $null
        $sy = $t | Where-Object { $_ -like 'sys      SYS*' } | Select-Object -First 1
        if ($sy -and $sy -match $sysRe) {
            $eff = [int]$Matches[1]; $effP = [int]$Matches[3]; $effE = [int]$Matches[4]; $utilE = [double]$Matches[7]
        }
        $main = $gpuc = $sum = ''
        $tc = if ($runLeaf) { Join-Path (Join-Path $runs $runLeaf) 'threads.csv' } else { '' }
        if ($tc -and (Test-Path $tc)) {
            $th = Import-Csv $tc
            $main = ($th | Where-Object { $_.name -like 'Main XThread*' } | Select-Object -First 1).busy_pct
            $gpuc = ($th | Where-Object { $_.name -like 'GPU Commands*' } | Select-Object -First 1).busy_pct
            $sum = [math]::Round(($th | ForEach-Object { [double]$_.busy_pct } | Measure-Object -Sum).Sum, 1)
        }
        if ($null -eq $eff -or $frames -eq '' -or $cpu -eq '') { $bad++ }
        $rows += [pscustomobject]@{ Run = $f.BaseName; Arm = $arm; Start = $start; Frames = $frames; Cpu = $cpu;
            Eff = $eff; EffP = $effP; EffE = $effE; UtilE = $utilE; Main = $main; Gpuc = $gpuc; Sum = $sum; Flag = '' }
    }
    foreach ($g in ($rows | Group-Object Arm)) {
        $med = Get-Median ([double[]]($g.Group | Where-Object { $null -ne $_.Eff } | ForEach-Object { $_.Eff }))
        foreach ($r in $g.Group) { if ($null -ne $r.Eff -and $r.Eff -le $med - $LowClockMHz) { $r.Flag = 'lowclk' } }
    }
    "== $m"
    '{0,-12} {1,-9} {2,-8} {3,6} {4,5} {5,5} {6,5} {7,5} {8,6} {9,6} {10,6} {11,6}  {12}' -f `
        'run', 'arm', 'start', 'frames', 'cpu', 'eff', 'effP', 'effE', 'utilE', 'main%', 'gpuc%', 'sum%', 'flag'
    foreach ($r in $rows) {
        '{0,-12} {1,-9} {2,-8} {3,6} {4,5} {5,5} {6,5} {7,5} {8,6} {9,6} {10,6} {11,6}  {12}' -f `
            $r.Run, $r.Arm, $r.Start, $r.Frames, $r.Cpu, $r.Eff, $r.EffP, $r.EffE, $r.UtilE, $r.Main, $r.Gpuc, $r.Sum, $r.Flag
    }
    $low = @($rows | Where-Object Flag -eq 'lowclk')
    'lowclk runs: {0} of {1}{2}' -f $low.Count, $rows.Count, $(if ($low.Count) { ' (' + (($low | ForEach-Object { $_.Run + ' ' + $_.Start }) -join ', ') + ')' } else { '' })
    ''
}
if ($bad) { "INCOMPLETE: $bad run(s) or folder(s) without the expected lines"; exit 2 }
'OK'
exit 0
