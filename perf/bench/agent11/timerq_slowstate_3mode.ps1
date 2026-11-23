# timerq_slowstate_3mode.ps1 - 3-mode copy of bench\agent11\timerq_slowstate.ps1 for the W5 read-out
# (Agent 11, task #35, 2026-11-22). The original stays frozen as a W4b read-out input.
#
# Read-only scan of Agent 8's run dirs for the "slow state" (E cores busy at minimum clock:
# sys.csv e_eff_mhz below -EMhz for -MinRows rows in a row). Run selection and slow-state math
# are the original's, unchanged: run dirs under <matrix>\runs that have sys.csv and run.json and
# ff_signal_epoch_s > 0; samples from the first frame on; onset_s = start of the first run of
# -MinRows+ samples below -EMhz (s after the first frame); slow_pct = low samples / all samples.
#
# Each run gets one of 3 timer-wait modes, from env_set and the precise log line:
#   precise  - the run's game.log has "TimerQueue: precise wait (timer_queue_precise_wait)"
#              (#38, timer_queue.cpp:71, info level, logged once). Precise wins: with the cvar
#              on, REX_TIMER_WAIT_BLOCKING is not read and nothing logs it.
#   blocking - no precise line, and env_set names REX_TIMER_WAIT_BLOCKING (presence-only; the
#              same test as the original's "blocking" column).
#   spin     - neither.
#   unknown  - the precise cvar is on but there is no readable game.log, so the mode is unproven.
#              (No log and no precise cvar: precise can't be on, so env_set decides; flag no_log.)
# Columns added: arm (run.json tag without -rN), env (env var named), pcvar
# (timer_queue_precise_wait=true in args or params.cvar), precise / ms1 (counts of the precise
# line and of "Host timer resolution set to 1 ms" in game.log), flags.
# Flags: no_log, precise_lines>1, env+precise, precise_cvar_no_line, precise_line_no_cvar.
# The per-arm table (grouped by matrix and arm) says MIXED when an arm's runs have more than one mode.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate_3mode.ps1
#          [-Root build\agent8\matrix] [-Since 20261122-0000] [-Matrix 20261122-1541] [-OutCsv <path>]
#   -Matrix  scan this one matrix folder only (overrides -Since).
#   -OutCsv  also write the per-run rows to a CSV file (off by default; otherwise nothing is written).
[CmdletBinding()]
param(
    [string]$Root = 'build\agent8\matrix',
    [string]$Since = '20261122-0000',
    [string]$Matrix = '',
    [double]$EMhz = 800,
    [int]$MinRows = 3,
    [string]$OutCsv = ''
)
$ErrorActionPreference = 'Stop'
$preciseLine = 'TimerQueue: precise wait (timer_queue_precise_wait)'
$ms1Line = 'Host timer resolution set to 1 ms'
$pcvarRx = 'timer_queue_precise_wait(=(true|1))?(\s|$)'
$rows = @()
if ($Matrix -ne '') {
    $mats = @(Get-ChildItem -LiteralPath $Root -Directory | Where-Object { $_.Name -eq $Matrix })
    if ($mats.Count -eq 0) { throw "matrix folder not found: $Matrix under $Root" }
} else {
    $mats = Get-ChildItem -LiteralPath $Root -Directory | Where-Object { $_.Name -match '^\d{8}-\d{4}$' -and $_.Name -ge $Since } | Sort-Object Name
}
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
        $envOn = $false
        $envText = ''
        if ($null -ne $j.env_set) { $envText = ($j.env_set | ConvertTo-Json -Compress -Depth 4) }
        if ($envText -match 'REX_TIMER_WAIT_BLOCKING') { $envOn = $true }
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
        # 3-mode inputs: arm, precise cvar, game.log lines
        $tag = "$($j.tag)"
        if ($tag -eq '') { $tag = $r.Name -replace '^\d{4}-', '' }
        $arm = $tag -replace '-r\d+$', ''
        $argText = (@(@($j.args) + @($j.params.cvar) | Where-Object { $null -ne $_ } | ForEach-Object { "$_" })) -join ' '
        $pcvar = [bool]($argText -match $pcvarRx)
        $log = Join-Path $r.FullName 'game.log'
        if (-not (Test-Path -LiteralPath $log)) {
            $log = ''
            foreach ($a in @($j.args)) {
                if ("$a" -like '--log_file=*') {
                    $p = "$a".Substring(11).Trim('"')
                    try { if ($p -ne '' -and (Test-Path -LiteralPath $p)) { $log = $p } } catch { }
                }
            }
        }
        $haveLog = $false; $nPrecise = 0; $nMs1 = 0
        if ($log -ne '') {
            try {
                $lines = [System.IO.File]::ReadAllLines((Resolve-Path -LiteralPath $log).ProviderPath)
                $haveLog = $true
                foreach ($ln in $lines) {
                    if ($ln.Contains($preciseLine)) { $nPrecise++ }
                    if ($ln.Contains($ms1Line)) { $nMs1++ }
                }
            } catch { $haveLog = $false; $nPrecise = 0; $nMs1 = 0 }
        }
        $flags = @()
        if (-not $haveLog) { $flags += 'no_log' }
        if ($nPrecise -gt 1) { $flags += 'precise_lines>1' }
        if ($nPrecise -ge 1 -and $envOn) { $flags += 'env+precise' }
        if ($haveLog -and $pcvar -and $nPrecise -eq 0) { $flags += 'precise_cvar_no_line' }
        if ($nPrecise -ge 1 -and -not $pcvar) { $flags += 'precise_line_no_cvar' }
        $mode = 'spin'
        if ($envOn) { $mode = 'blocking' }
        if ($pcvar -and -not $haveLog) { $mode = 'unknown' }
        if ($nPrecise -ge 1) { $mode = 'precise' }
        $rows += [pscustomobject]@{
            matrix = $m.Name
            run = $r.Name
            arm = $arm
            mode = $mode
            env = $envOn
            pcvar = $pcvar
            precise = $nPrecise
            ms1 = $nMs1
            onset_s = $onsetText
            slow_pct = [math]::Round(100.0 * $low / $s.Count, 0)
            span_s = [math]::Round($span, 0)
            fg = (($s | Select-Object -ExpandProperty fg_game -Unique) -join '/')
            flags = ($flags -join ',')
            slow_raw = (100.0 * $low / $s.Count)
            onset_raw = $onset
        }
    }
}
$show = 'matrix', 'run', 'arm', 'mode', 'env', 'pcvar', 'precise', 'ms1', 'onset_s', 'slow_pct', 'span_s', 'fg', 'flags'
# -Property is explicit: PS 5.1's auto table view stops at 10 columns, which hid span_s, fg and flags.
$rows | Format-Table -Property $show -AutoSize | Out-String -Width 240
$parts = @()
foreach ($md in @('precise', 'blocking', 'spin', 'unknown')) {
    $g = @($rows | Where-Object { $_.mode -eq $md })
    if ($md -eq 'unknown' -and $g.Count -eq 0) { continue }
    $gs = @($g | Where-Object { $_.onset_s -ne '-' }).Count
    $parts += "$md runs: $($g.Count), with slow state: $gs"
}
"$($parts -join '; ') (E below $EMhz MHz for $MinRows+ samples)"
$arms = @()
foreach ($g in @($rows | Group-Object matrix, arm)) {
    $gr = @($g.Group)
    $ms = @($gr | Select-Object -ExpandProperty mode -Unique)
    $sl = @($gr | Where-Object { $null -ne $_.onset_raw })
    $mo = '-'
    if ($sl.Count -gt 0) { $mo = [string][math]::Round(($sl | Measure-Object -Property onset_raw -Average).Average, 0) }
    $arms += [pscustomobject]@{
        matrix = $gr[0].matrix
        arm = $gr[0].arm
        runs = $gr.Count
        mode = ($ms -join '/')
        slow_runs = $sl.Count
        mean_slow_pct = [math]::Round(($gr | Measure-Object -Property slow_raw -Average).Average, 1)
        mean_onset_s = $mo
        note = $(if ($ms.Count -gt 1) { 'MIXED' } else { '' })
    }
}
$arms | Sort-Object matrix, arm | Format-Table -AutoSize | Out-String -Width 240
$fl = @($rows | Where-Object { $_.flags -ne '' })
$mx = @($arms | Where-Object { $_.note -eq 'MIXED' })
"runs with flags: $($fl.Count); mixed arms: $($mx.Count)"
if ($fl.Count -gt 0) { $fl | Select-Object matrix, run, mode, flags | Format-Table -AutoSize | Out-String -Width 240 }
if ($OutCsv -ne '') {
    $rows | Export-Csv -LiteralPath $OutCsv -NoTypeInformation -Encoding ASCII
    "wrote $OutCsv"
}
