# timerq_slowstate.ps1 - read-only scan of Agent 8's run dirs for the "slow state"
# (E cores busy at minimum clock: sys.csv e_eff_mhz below -EMhz for -MinRows rows in a row).
# For each run dir under -Root that has sys.csv and run.json it prints: the arm, whether
# REX_TIMER_WAIT_BLOCKING was set, the slow-state onset (s after the first frame), and the
# share of samples (first frame .. last sample) in the slow state.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 [-Root build\agent8\matrix] [-Since 20261122-0000]
[CmdletBinding()]
param(
    [string]$Root = 'build\agent8\matrix',
    [string]$Since = '20261122-0000',
    [double]$EMhz = 800,
    [int]$MinRows = 3
)
$ErrorActionPreference = 'Stop'
$rows = @()
$mats = Get-ChildItem -LiteralPath $Root -Directory | Where-Object { $_.Name -match '^\d{8}-\d{4}$' -and $_.Name -ge $Since } | Sort-Object Name
foreach ($m in $mats) {
    $rd = Join-Path $m.FullName 'runs'
    if (-not (Test-Path -LiteralPath $rd)) { continue }
    foreach ($r in (Get-ChildItem -LiteralPath $rd -Directory | Sort-Object Name)) {
        $sys = Join-Path $r.FullName 'sys.csv'
        $rj = Join-Path $r.FullName 'run.json'
        if (-not (Test-Path -LiteralPath $sys) -or -not (Test-Path -LiteralPath $rj)) { continue }
        try { $j = Get-Content -LiteralPath $rj -Raw | ConvertFrom-Json } catch { continue }
        $ff = 0.0
        if ($null -ne $j.ff_signal_epoch_s -and "$($j.ff_signal_epoch_s)" -ne '') { $ff = [double]$j.ff_signal_epoch_s }
        if ($ff -le 0) { continue }
        $blocking = $false
        $envText = ''
        if ($null -ne $j.env_set) { $envText = ($j.env_set | ConvertTo-Json -Compress -Depth 4) }
        if ($envText -match 'REX_TIMER_WAIT_BLOCKING') { $blocking = $true }
        $csv = @(Import-Csv -LiteralPath $sys)
        $s = @($csv | Where-Object { $_.e_eff_mhz -ne '' -and $_.epoch_s -ne '' -and ([double]$_.epoch_s - $ff) -ge 0 })
        if ($s.Count -eq 0) { continue }
        $low = 0; $run = 0; $onset = $null; $first = $null
        foreach ($x in $s) {
            $t = [double]$x.epoch_s - $ff
            if ([double]$x.e_eff_mhz -lt $EMhz) {
                $low++; $run++
                if ($run -eq 1) { $first = $t }
                if ($run -ge $MinRows -and $null -eq $onset) { $onset = $first }
            } else { $run = 0 }
        }
        $span = [double]$s[-1].epoch_s - $ff
        $onsetText = '-'
        if ($null -ne $onset) { $onsetText = [string][math]::Round($onset, 0) }
        $rows += [pscustomobject]@{
            matrix = $m.Name
            run = $r.Name
            blocking = $blocking
            onset_s = $onsetText
            slow_pct = [math]::Round(100.0 * $low / $s.Count, 0)
            span_s = [math]::Round($span, 0)
            fg = (($s | Select-Object -ExpandProperty fg_game -Unique) -join '/')
        }
    }
}
$rows | Format-Table -AutoSize | Out-String -Width 200
$b = @($rows | Where-Object { $_.blocking })
$n = @($rows | Where-Object { -not $_.blocking })
$bs = @($b | Where-Object { $_.onset_s -ne '-' }).Count
$ns = @($n | Where-Object { $_.onset_s -ne '-' }).Count
"blocking runs: $($b.Count), with slow state: $bs; spin runs: $($n.Count), with slow state: $ns (E below $EMhz MHz for $MinRows+ samples)"
