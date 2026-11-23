# Agent 1: quiet check before a timed window (re-made 17:31 after the agy-grid relaunch).
# Every 60 s: CPU cores (1-minute average) per process group, from the Process perf counters
# (readable for protected processes such as MsMpEng). QUIET = Defender, Office and CrossDevice
# each < $Limit core for $Need consecutive 1-minute averages. Also logs total busy cores, the top 5
# processes and any game/build process. Reads only; writes build/agent1/w5/quiet-<HHmm>.log.
param([int]$MaxMinutes = 20, [double]$Limit = 0.1, [int]$Need = 3)
$ErrorActionPreference = 'Stop'
$w   = '<workspace>'
$log = Join-Path $w ('build\agent1\w5\quiet-{0}.log' -f (Get-Date -Format 'HHmm'))
function L([string]$t) { $s = '{0} {1}' -f (Get-Date -Format 'HH:mm:ss'), $t; [IO.File]::AppendAllText($log, $s + "`r`n"); $s }
$groups = [ordered]@{
  Defender    = '^(MsMpEng|MpDefenderCoreService|NisSrv|MpCmdRun|MsSense|SecurityHealthService)$'
  Office      = '^(OfficeClickToRun|OfficeC2RClient|MSOSYNC|msoia|SDXHelper|OfficeSvcMgr|FileCoAuth)$'
  CrossDevice = '^(CrossDeviceService|CrossDeviceResume)$'
  Search      = '^(SearchIndexer|SearchProtocolHost|SearchFilterHost)$'
}
$gate  = @('Defender', 'Office', 'CrossDevice')
$heavy = '^(legodimensions|ninja|clang|clang\+\+|clang-cl|lld|lld-link|ld\.lld|cmake|link|cl|msbuild)$'
$ncpu  = [Environment]::ProcessorCount
function Snap {
  $d   = (New-Object System.Diagnostics.PerformanceCounterCategory('Process')).ReadCategory()
  $cpu = $d['% Processor Time']; $ids = $d['ID Process']
  $h = @{}; $ts = 0.0
  foreach ($k in @($cpu.Keys)) {
    if ($k -eq '_Total' -or $k -eq 'Idle') { continue }
    $s  = $cpu[$k]; $ts = [double]$s.Sample.TimeStamp100nSec
    $id = [int]$ids[$k].RawValue
    $h["$id"] = [pscustomobject]@{ N = ($k -replace '#\d+$', ''); T = [double]$s.RawValue }
  }
  [pscustomobject]@{ TS = $ts; P = $h }
}
L ('start: limit {0} core, need {1} consecutive 1-min averages, max {2} min, {3} logical CPUs' -f $Limit, $Need, $MaxMinutes, $ncpu) | Out-Host
$a = Snap; $ok = 0; $t0 = Get-Date
while (((Get-Date) - $t0).TotalMinutes -lt $MaxMinutes) {
  Start-Sleep -Seconds 60
  $b  = Snap; $dt = $b.TS - $a.TS
  $rows = foreach ($id in $b.P.Keys) {
    $n = $b.P[$id]; $prevT = if ($a.P.ContainsKey($id) -and $a.P[$id].N -eq $n.N) { $a.P[$id].T } else { 0.0 }
    [pscustomobject]@{ N = $n.N; Id = $id; C = [math]::Max(0.0, ($n.T - $prevT) / $dt) }
  }
  $g = [ordered]@{}; foreach ($k in $groups.Keys) { $g[$k] = ($rows | Where-Object { $_.N -match $groups[$k] } | Measure-Object C -Sum).Sum; if (-not $g[$k]) { $g[$k] = 0.0 } }
  $total = ($rows | Measure-Object C -Sum).Sum
  $top   = ($rows | Sort-Object C -Descending | Select-Object -First 5 | ForEach-Object { '{0}={1:N2}' -f $_.N, $_.C }) -join ' '
  $hv    = @($rows | Where-Object { $_.N -match $heavy } | ForEach-Object { '{0}({1})' -f $_.N, $_.Id })
  $pass  = -not ($gate | Where-Object { $g[$_] -ge $Limit })
  if ($pass -and $hv.Count -eq 0) { $ok++ } else { $ok = 0 }
  L ('{0} {1}/{2} | Defender {3:N3} Office {4:N3} CrossDevice {5:N3} Search {6:N3} | busy {7:N2} of {8} | top {9}{10}' -f $(if ($pass -and $hv.Count -eq 0) { 'pass' } else { 'FAIL' }), $ok, $Need, $g.Defender, $g.Office, $g.CrossDevice, $g.Search, $total, $ncpu, $top, $(if ($hv.Count) { ' | GAME/BUILD: ' + ($hv -join ' ') } else { '' })) | Out-Host
  if ($ok -ge $Need) { L 'QUIET' | Out-Host; exit 0 }
  $a = $b
}
L ('NOT QUIET after {0} min' -f $MaxMinutes) | Out-Host
exit 1
