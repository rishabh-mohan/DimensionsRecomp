<#
.SYNOPSIS
  Summarize Agent 8's TimerQueue functional runs: a reference (d0f) and one or more test arms (d0t, d11t).
  S3 task #10, Agent 11.
.DESCRIPTION
  Read-only: no game, no build. For each run dir it reads
    threads.csv  - rex::thread::TimerQueue busy % of one core (and its busiest 1 s), plus the sum over all threads
    summary.txt  - frames over 100 ms and over 33 ms, mean fps, cvars, env, and the sys line
                   (effective MHz and utility of the P and E cores in the window, power overlay)
    run.json     - status, exit code, close (killed or not), WerFault, env_set, the first-frame time
    perf.csv     - frames per 10 s from the first frame
    sys.csv      - P and E core effective MHz and E-core utility per 10 s from the first frame
  and looks for *.dmp files under the run dir.
  The first run dir is the reference (d0f); each further one is a test arm. A test arm passes when:
    - its TimerQueue busy % is <= MaxTimerQueuePct (default 3.0);
    - it has no more >100 ms frames than the reference;
    - its mean fps is at most MaxFpsDropPct (default 10) below the reference's (added at 03:45 after the
      first d0t run; Agent 1's W4b rule is "fps within noise of d0f");
    - it closed cleanly (status OK, not killed, exit 0x00000000) and left no dump;
    - REX_TIMER_WAIT_BLOCKING is in its env_set and not in the reference's.
  Context (not checked): window 3's d0 on the interactive desktop, 62.0 % TimerQueue (mean of 4 runs,
  60.6-62.9) at 163.6 fps; verify3b's d0 on the hidden desktop (23:46), 32.9 % at 226.9 fps.
  Exit: 0 = every test arm passes, 1 = one fails, 2 = bad input.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_pair.ps1 -RunDirs <d0f dir>,<d0t dir>,<d11t dir>
  (-File passes "a,b" as one string; it is split on commas, and "a, b" with a space works too)
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_pair.ps1
  (no -RunDirs: the newest *-d0f-r* and *-d0t-r* run dirs under build\agent8\matrix, plus the newest
  *-d11t-r* if there is one)
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$RunDirs = '',
    [double]$MaxTimerQueuePct = 3.0,
    [double]$MaxFpsDropPct = 10.0,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest
)
$ErrorActionPreference = 'Stop'
$dirs = @((@($RunDirs) + @($Rest)) | Where-Object { $_ } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$outDir = Join-Path $root 'build\agent11\timerq'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$log = Join-Path $outDir ('pair-{0}.txt' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$lines = New-Object System.Collections.Generic.List[string]
function Say([string]$s) { $lines.Add($s); Write-Output $s }

if ($dirs.Count -eq 0) {
    $m = Join-Path $root 'build\agent8\matrix'
    $newest = { param($pat) Get-ChildItem -Recurse -Directory -Path $m -Filter $pat -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1 }
    $f = & $newest '*-d0f-r*'; $t = & $newest '*-d0t-r*'; $e = & $newest '*-d11t-r*'
    if (-not $f -or -not $t) { Write-Output 'no d0f/d0t run dirs under build\agent8\matrix yet; pass -RunDirs'; exit 2 }
    $dirs = @($f.FullName, $t.FullName)
    if ($e) { $dirs += $e.FullName }
}
if ($dirs.Count -lt 2) { Write-Output 'need at least two run dirs: the reference (d0f), then one or more test arms (d0t, d11t)'; exit 2 }

$NB = 12   # 10 s buckets from the first frame; the measured window is 60-110 s (warm-up floor 60 s, window 50 s)
function Read-Run([string]$dir) {
    if (-not [IO.Path]::IsPathRooted($dir)) { $dir = Join-Path $root $dir }
    if (-not (Test-Path -LiteralPath $dir)) { throw "no such run dir: $dir" }
    $r = [ordered]@{ Dir = $dir; Name = Split-Path -Leaf $dir; TQ = $null; TQMax = $null; Sum = $null; Threads = 0
                     Over100 = $null; Over33 = $null; Fps = $null; Status = '?'; Exit = '?'; Killed = '?'
                     WerFault = '?'; EnvBlocking = $false; Cores = $null; Dumps = @(); Cvars = ''; Env = ''
                     PMhz = $null; EMhz = $null; PUtil = $null; EUtil = $null; Overlay = ''; FF = $null
                     BF = $null; BP = $null; BE = $null; BEU = $null; BN = $null }
    $tc = Join-Path $dir 'threads.csv'
    if (Test-Path -LiteralPath $tc) {
        $rows = @(Import-Csv -LiteralPath $tc)
        $r.Threads = $rows.Count
        $sum = 0.0; foreach ($x in $rows) { $sum += [double]$x.busy_pct }; $r.Sum = $sum
        $q = $rows | Where-Object { $_.name -eq 'rex::thread::TimerQueue' } | Select-Object -First 1
        if ($q) { $r.TQ = [double]$q.busy_pct; if ($q.max_busy_pct) { $r.TQMax = [double]$q.max_busy_pct } }
    }
    $st = Join-Path $dir 'summary.txt'
    if (Test-Path -LiteralPath $st) {
        $s = Get-Content -LiteralPath $st -Raw
        if ($s -match '>100 ms (\d+)') { $r.Over100 = [int]$Matches[1] }
        if ($s -match '>33 ms (\d+)') { $r.Over33 = [int]$Matches[1] }
        if ($s -match '= ([\d.]+) fps mean') { $r.Fps = [double]$Matches[1] }
        if ($s -match '(?m)^cvars[ \t]+([^\r\n]*)') { $r.Cvars = $Matches[1].Trim() }
        if ($s -match '(?m)^env[ \t]+([^\r\n]*)') { $r.Env = $Matches[1].Trim() }
        if ($s -match 'P (\d+) / E (\d+)\), util [\d.]+% \(P ([\d.]+) / E ([\d.]+)\)') {
            $r.PMhz = [double]$Matches[1]; $r.EMhz = [double]$Matches[2]; $r.PUtil = [double]$Matches[3]; $r.EUtil = [double]$Matches[4]
        }
        if ($s -match 'overlay ([A-Za-z_]+)') { $r.Overlay = $Matches[1] }
    }
    $rj = Join-Path $dir 'run.json'
    if (Test-Path -LiteralPath $rj) {
        $j = Get-Content -LiteralPath $rj -Raw | ConvertFrom-Json
        $r.Status = $j.status; $r.Exit = $j.exit_code_hex; $r.WerFault = $j.werfault_seen
        if ($j.close) { $r.Killed = $j.close.killed }
        if ($j.env_set -and ($j.env_set.PSObject.Properties.Name -contains 'REX_TIMER_WAIT_BLOCKING')) { $r.EnvBlocking = $true }
        $r.Cores = $j.window_cpu_cores_mean
        if ($j.ff_signal_epoch_s) { $r.FF = [double]$j.ff_signal_epoch_s }
    }
    $bf = New-Object int[] $NB; $bp = New-Object double[] $NB; $be = New-Object double[] $NB; $beu = New-Object double[] $NB; $bn = New-Object int[] $NB
    $pc = Join-Path $dir 'perf.csv'
    if (Test-Path -LiteralPath $pc) {
        $t = 0.0
        foreach ($x in (Import-Csv -LiteralPath $pc)) {
            $ft = [double]$x.frame_time_us / 1000.0
            if ($ft -le 0) { continue }
            $t += $ft
            $k = [int][math]::Floor($t / 10000.0)
            if ($k -lt $NB) { $bf[$k]++ }
        }
    }
    $sc = Join-Path $dir 'sys.csv'
    if ((Test-Path -LiteralPath $sc) -and $null -ne $r.FF) {
        foreach ($x in (Import-Csv -LiteralPath $sc)) {
            if (-not $x.epoch_s -or -not $x.p_eff_mhz -or -not $x.e_eff_mhz) { continue }
            $tt = [double]$x.epoch_s - $r.FF
            if ($tt -lt 0) { continue }
            $k = [int][math]::Floor($tt / 10.0)
            if ($k -lt $NB) {
                $bp[$k] += [double]$x.p_eff_mhz; $be[$k] += [double]$x.e_eff_mhz
                if ($x.e_util_pct) { $beu[$k] += [double]$x.e_util_pct }
                $bn[$k]++
            }
        }
    }
    $r.BF = $bf; $r.BP = $bp; $r.BE = $be; $r.BEU = $beu; $r.BN = $bn
    $r.Dumps = @(Get-ChildItem -LiteralPath $dir -Recurse -Filter '*.dmp' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    return $r
}

try { $runs = @($dirs | ForEach-Object { Read-Run $_ }) } catch { Write-Output $_.Exception.Message; exit 2 }
$ref = $runs[0]; $arms = @($runs | Select-Object -Skip 1)

function Fmt($v, [string]$f = '{0}') { if ($null -eq $v) { '-' } else { $f -f $v } }
Say ('# timerq_pair {0}  reference {1}  test arms {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $ref.Name, (($arms | ForEach-Object { $_.Name }) -join ', '))
Say ''
Say '| run | cvars; env | TimerQueue busy % (max 1 s) | all threads, cores | window cores | fps mean | >33 ms | >100 ms | eff MHz P / E | utility % P / E | status, close, exit | dumps |'
Say '|---|---|---|---|---|---|---|---|---|---|---|---|'
foreach ($x in $runs) {
    $close = $(if ($x.Killed -eq $false) { 'WM_CLOSE' } elseif ($x.Killed -eq $true) { 'KILLED' } else { '?' })
    Say ('| {0} | {1}; {2} | {3} ({4}) | {5} | {6} | {7} | {8} | {9} | {10} / {11} | {12} / {13} | {14} {15} {16} | {17} |' -f $x.Name,
        $(if ($x.Cvars) { $x.Cvars } else { '-' }), $(if ($x.Env) { $x.Env } else { '-' }),
        (Fmt $x.TQ '{0:N1}'), (Fmt $x.TQMax '{0:N1}'), (Fmt $(if ($null -ne $x.Sum) { $x.Sum / 100 }) '{0:N2}'),
        (Fmt $x.Cores '{0:N2}'), (Fmt $x.Fps '{0:N1}'), (Fmt $x.Over33), (Fmt $x.Over100),
        (Fmt $x.PMhz '{0:N0}'), (Fmt $x.EMhz '{0:N0}'), (Fmt $x.PUtil '{0:N1}'), (Fmt $x.EUtil '{0:N1}'),
        $x.Status, $close, $x.Exit, $x.Dumps.Count)
}
Say '| context: window 3 d0 (interactive desktop, mean of 4) | framerate_limit=0; - | 62.0 | 3.48 | | 163.6 | | | | | | |'
Say '| context: verify3b d0 (hidden desktop, 23:46) | framerate_limit=0; - | 32.9 | 2.73 | 2.73 | 226.9 | 5 | 0 | | | | |'
$ov = @($runs | ForEach-Object { $_.Overlay } | Where-Object { $_ } | Sort-Object -Unique)
if ($ov.Count -gt 0) { Say ('Power overlay: {0}' -f ($ov -join ', ')) }
Say ''
Say 'Per 10 s from the first frame (* = inside the measured window, 60-110 s); MHz and E utility from sys.csv:'
$hdr = '| run | metric |'
for ($k = 0; $k -lt $NB; $k++) { $s0 = $k * 10; $hdr += $(if ($s0 -ge 60 -and $s0 -lt 110) { " $s0* |" } else { " $s0 |" }) }
Say $hdr
Say ('|---|---|' + ('---|' * $NB))
foreach ($x in $runs) {
    $rowF = '| {0} | fps |' -f $x.Name; $rowP = '| {0} | P MHz |' -f $x.Name; $rowE = '| {0} | E MHz |' -f $x.Name; $rowU = '| {0} | E util % |' -f $x.Name
    for ($k = 0; $k -lt $NB; $k++) {
        $rowF += (' {0} |' -f [math]::Round($x.BF[$k] / 10.0))
        if ($x.BN[$k] -gt 0) {
            $rowP += (' {0:N0} |' -f ($x.BP[$k] / $x.BN[$k])); $rowE += (' {0:N0} |' -f ($x.BE[$k] / $x.BN[$k])); $rowU += (' {0:N0} |' -f ($x.BEU[$k] / $x.BN[$k]))
        } else { $rowP += ' - |'; $rowE += ' - |'; $rowU += ' - |' }
    }
    Say $rowF; Say $rowP; Say $rowE; Say $rowU
}

$fail = 0
function Check([bool]$ok, [string]$what) { if ($ok) { Say "PASS  $what" } else { Say "FAIL  $what"; $script:fail++ } }
if ($ref.Status -ne 'OK' -or $ref.Killed -ne $false -or $ref.Dumps.Count -gt 0) { Say ''; Say ('NOTE  the reference did not close cleanly (status {0}, killed {1}, dumps {2}): the comparisons are weak' -f $ref.Status, $ref.Killed, $ref.Dumps.Count) }
foreach ($arm in $arms) {
    Say ''
    Say ('## {0} against {1}' -f $arm.Name, $ref.Name)
    Check ($null -ne $arm.TQ -and $arm.TQ -le $MaxTimerQueuePct) ("TimerQueue busy <= {0} % (got {1}; reference {2})" -f $MaxTimerQueuePct, (Fmt $arm.TQ '{0:N1}'), (Fmt $ref.TQ '{0:N1}'))
    Check ($null -ne $arm.Over100 -and $null -ne $ref.Over100 -and $arm.Over100 -le $ref.Over100) (">100 ms frames <= reference (got {0} vs {1})" -f (Fmt $arm.Over100), (Fmt $ref.Over100))
    $dp = $(if ($null -ne $arm.Fps -and $null -ne $ref.Fps -and $ref.Fps -gt 0) { ($arm.Fps / $ref.Fps - 1) * 100 })
    Check ($null -ne $dp -and $dp -ge -$MaxFpsDropPct) ("fps mean at most {0} % below the reference (got {1} vs {2}, {3})" -f $MaxFpsDropPct, (Fmt $arm.Fps '{0:N1}'), (Fmt $ref.Fps '{0:N1}'), (Fmt $dp '{0:+0.0;-0.0} %'))
    Check ($arm.Status -eq 'OK' -and $arm.Killed -eq $false -and $arm.Exit -eq '0x00000000') ("closed cleanly (status {0}, killed {1}, exit {2})" -f $arm.Status, $arm.Killed, $arm.Exit)
    Check ($arm.Dumps.Count -eq 0 -and $arm.WerFault -ne $true) ("no dump (dumps {0}, WerFault {1})" -f $arm.Dumps.Count, $arm.WerFault)
    Check ($arm.EnvBlocking -and -not $ref.EnvBlocking) ("REX_TIMER_WAIT_BLOCKING set in the test arm only (test {0}, reference {1})" -f $arm.EnvBlocking, $ref.EnvBlocking)
    if ($null -ne $ref.TQ -and $null -ne $arm.TQ) {
        Say ('INFO  TimerQueue {0:N1} -> {1:N1} % of a core ({2:N2} cores freed on the hidden desktop; window 3 d0 had 0.62 cores)' -f $ref.TQ, $arm.TQ, (($ref.TQ - $arm.TQ) / 100))
    }
    if ($null -ne $ref.EMhz -and $null -ne $arm.EMhz) {
        Say ('INFO  window eff MHz P {0:N0} -> {1:N0}, E {2:N0} -> {3:N0}; utility P {4:N1} -> {5:N1}, E {6:N1} -> {7:N1}' -f $ref.PMhz, $arm.PMhz, $ref.EMhz, $arm.EMhz, $ref.PUtil, $arm.PUtil, $ref.EUtil, $arm.EUtil)
    }
}
Say ''
Say $(if ($fail -eq 0) { 'RESULT: PASS' } else { "RESULT: FAIL ($fail)" })
Say "# log $log"
[IO.File]::WriteAllLines($log, $lines)
exit $(if ($fail -eq 0) { 0 } else { 1 })
