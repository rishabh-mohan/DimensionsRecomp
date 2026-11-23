# pthrottle_readout.ps1 - S4 task #24 read-out: per run of the opt-out pairs, the opt-out read-back
# and the slow state (E cores at minimum clock: sys.csv e_eff_mhz below -EMhz for -MinRows rows in
# a row, from the first frame; the same rule as timerq_slowstate.ps1), then per arm and a verdict.
# Read-only. The read-back comes from run.json "power_throttling" or else <PtDir>\<run>.json.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_readout.ps1 -RunsDir <out>\runs [-PtDir <out>-meta\pthrottle]
[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)][string]$RunsDir,
    [string]$PtDir = '',
    [string]$OnArm = 'd0e',
    [string]$OffArm = 'd0',
    [double]$EMhz = 800,
    [int]$MinRows = 3,
    [double]$MinSpanS = 100,
    [double]$TeardownS = 1.5
)
$ErrorActionPreference = 'Stop'
if (-not $PtDir) { $PtDir = (Split-Path -Parent $RunsDir) + '-meta\pthrottle' }
function Med([double[]]$v) { if (-not $v -or $v.Count -eq 0) { return $null }; $s = $v | Sort-Object; $n = $s.Count; if ($n % 2) { return $s[($n - 1) / 2] }; return ($s[$n / 2 - 1] + $s[$n / 2]) / 2 }
function Rnd($x, [int]$d = 0) { if ($null -eq $x) { return '-' }; return [math]::Round([double]$x, $d) }
$rows = @()
foreach ($d in (Get-ChildItem -LiteralPath $RunsDir -Directory | Sort-Object Name)) {
    if ($d.Name -notmatch '^\d{4}-(?<arm>.+?)-r(?<k>\d+)(-r\d+)?$') { continue }
    $arm = $Matches.arm; $k = [int]$Matches.k
    if ($arm -ne $OnArm -and $arm -ne $OffArm) { continue }
    $rjp = Join-Path $d.FullName 'run.json'; $sysp = Join-Path $d.FullName 'sys.csv'
    $j = $null; if (Test-Path -LiteralPath $rjp) { $j = Get-Content -Raw -LiteralPath $rjp | ConvertFrom-Json }
    $pt = $null
    if ($j -and $j.power_throttling) { $pt = $j.power_throttling }
    elseif (Test-Path -LiteralPath (Join-Path $PtDir ($d.Name + '.json'))) { $pt = Get-Content -Raw -LiteralPath (Join-Path $PtDir ($d.Name + '.json')) | ConvertFrom-Json }
    $ff = 0.0; if ($j -and $j.ff_signal_epoch_s) { $ff = [double]$j.ff_signal_epoch_s }
    $onset = $null; $share = $null; $span = $null; $eMed = $null; $eSlow = $null; $euSlow = $null; $pMed = $null; $tz = $null; $fg = '-'
    if ($ff -gt 0 -and (Test-Path -LiteralPath $sysp)) {
        $s = @(Import-Csv -LiteralPath $sysp | Where-Object { $_.e_eff_mhz -ne '' -and $_.epoch_s -ne '' -and ([double]$_.epoch_s - $ff) -ge 0 })
        if ($s.Count) {
            $low = 0; $run = 0; $first = $null; $slowRows = @()
            foreach ($x in $s) {
                $t = [double]$x.epoch_s - $ff
                if ([double]$x.e_eff_mhz -lt $EMhz) { $low++; $run++; $slowRows += $x; if ($run -eq 1) { $first = $t }; if ($run -ge $MinRows -and $null -eq $onset) { $onset = $first } } else { $run = 0 }
            }
            $share = 100.0 * $low / $s.Count; $span = [double]$s[-1].epoch_s - $ff
            $eMed = Med @($s | ForEach-Object { [double]$_.e_eff_mhz })
            $pMed = Med @($s | Where-Object { $_.p_eff_mhz -ne '' } | ForEach-Object { [double]$_.p_eff_mhz })
            if ($slowRows.Count) {
                $eSlow = Med @($slowRows | ForEach-Object { [double]$_.e_eff_mhz })
                $euSlow = Med @($slowRows | Where-Object { $_.e_util_pct -ne '' } | ForEach-Object { [double]$_.e_util_pct })
            }
            $tzv = @($s | Where-Object { $_.tz_passive_min_pct -ne '' } | ForEach-Object { [double]$_.tz_passive_min_pct })
            if ($tzv.Count) { $tz = ($tzv | Measure-Object -Minimum).Minimum }
            $fg = (($s | Select-Object -ExpandProperty fg_game -Unique) -join '/')
        }
    }
    # arm state: on arm = applied, no apply error or logged error, and the record ok or its only loss
    # seen within -TeardownS s of the exit (process teardown: the state reads 0 and a set fails);
    # off arm = never applied. lost_s = first change by someone else, relative to the exit.
    $ver = $false; $lostS = '-'
    if ($pt) {
        $other = @($pt.transitions | Where-Object { $_.by -eq 'other' })
        if ($other.Count -and $pt.exited_s) { $lostS = Rnd ([double]$other[0].t_s - [double]$pt.exited_s) 2 }
        if ($arm -eq $OnArm) {
            $tear = ($pt.end -eq 'exited') -and $other.Count -and $pt.exited_s -and ([double]$other[0].t_s -ge [double]$pt.exited_s - $TeardownS)
            $ver = [bool]$pt.applied -and ("$($pt.apply_error)" -eq '0') -and (@($pt.errors).Count -eq 0) -and ([bool]$pt.ok -or $tear)
        } else { $ver = -not [bool]$pt.applied }
    } elseif ($arm -ne $OnArm) { $ver = $true }
    $rows += [pscustomobject]@{
        run = $d.Name; arm = $arm; k = $k; status = $(if ($j) { "$($j.status)" } else { 'no run.json' })
        applied = $(if ($pt) { [bool]$pt.applied } else { '-' }); readback = $(if ($pt) { "$($pt.before) -> $($pt.after), last $($pt.last_read)" } else { 'none' })
        reapplied = $(if ($pt) { $pt.reapplied } else { '-' }); held_pct = $(if ($pt) { $pt.optout_held_pct } else { '-' }); pt_ok = $(if ($pt) { [bool]$pt.ok } else { $false }); ver = $ver; lost_s = $lostS
        onset_s = $(if ($null -ne $onset) { Rnd $onset } else { '-' }); slow_pct = Rnd $share; span_s = Rnd $span
        e_mhz = Rnd $eMed; e_mhz_slow = Rnd $eSlow; e_util_slow = Rnd $euSlow; p_mhz = Rnd $pMed; tz_min = Rnd $tz; fg = $fg
    }
}
"# pthrottle_readout $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $RunsDir (slow state: E below $EMhz MHz for $MinRows+ samples, from the first frame)"
$rows | Format-Table run, arm, status, applied, readback, reapplied, held_pct, pt_ok, ver, lost_s, onset_s, slow_pct, span_s, e_mhz, e_mhz_slow, e_util_slow, p_mhz, tz_min, fg -AutoSize | Out-String -Width 320
# A run is counted only with a verified arm state (on arm: opt-out applied and the sidecar record ok;
# off arm: never applied) and with sys.csv data: the slow state seen, or at least -MinSpanS s after the
# first frame without it (a run without data must not count as "not slow").
$sum = @{}; $excl = @()
foreach ($a in @($OffArm, $OnArm)) {
    $r = @($rows | Where-Object { $_.arm -eq $a }); $use = @()
    foreach ($x in $r) {
        $why = @()
        if ($a -eq $OnArm -and -not $x.ver) { $why += 'opt-out not verified' }
        if ($a -eq $OffArm -and -not $x.ver) { $why += 'opt-out applied on the off arm' }
        if ($x.onset_s -eq '-' -and ($x.span_s -eq '-' -or [double]$x.span_s -lt $MinSpanS)) { $why += "no slow state and under $MinSpanS s of sys.csv after the first frame" }
        if ($why.Count) { $excl += "$($x.run): $($why -join '; ')" } else { $use += $x }
    }
    $sl = @($use | Where-Object { $_.onset_s -ne '-' })
    $sum[$a] = [pscustomobject]@{ n = $use.Count; slow = $sl.Count; onsets = (($sl | ForEach-Object { $_.onset_s }) -join ','); share = (($use | ForEach-Object { $_.slow_pct }) -join ',') }
    "arm {0,-4}: {1} runs, {2} counted, {3} with the slow state (onsets {4} s; slow share % per counted run {5}); arm state verified in {6}/{1} (sidecar record ok in {7}/{1})" -f $a, $r.Count, $use.Count, $sl.Count, $sum[$a].onsets, $sum[$a].share, @($r | Where-Object { $_.ver }).Count, @($r | Where-Object { $_.pt_ok }).Count
}
foreach ($e in $excl) { "not counted: $e" }
$off = $sum[$OffArm]; $on = $sum[$OnArm]
$v = if ($off.n -eq 0 -or $on.n -eq 0) { 'INCOMPLETE: an arm has no counted runs' }
  elseif ($off.slow -eq 0) { 'INCONCLUSIVE: the off arm never reached the slow state, so these runs cannot show an effect' }
  elseif ($on.slow -eq 0 -and $off.slow -ge [math]::Max(2, [math]::Ceiling($off.n / 2))) { 'OPT-OUT HELPS: no opt-out run reached the slow state, most off runs did. The state follows the process QoS decision (window-visibility / EcoQoS policy), not a hard package limit alone.' }
  elseif ($on.slow -ge $off.slow -or ($on.slow -ge 2 -and ($off.slow - $on.slow) -le 1)) { 'NO EFFECT: opt-out runs reached the slow state about as often as off runs. Process EXECUTION_SPEED throttling is not what holds the E cores; left: PL1 / package power, thread-level or visibility QoS the process flag does not override, the power-mode overlay / EPP.' }
  else { 'MIXED: fewer opt-out runs reached the slow state, but not cleanly; more pairs needed' }
"VERDICT: $v"
