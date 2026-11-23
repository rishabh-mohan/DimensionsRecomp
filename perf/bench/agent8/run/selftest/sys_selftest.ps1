# sys_selftest.ps1 - self-test of drivers\sys-csv.ps1 (+ LdSys.cs) and sys_summary.py (Agent 8 helper, 2026-11-22).
# Never starts the game: the dummy "game" is a hidden ping started here. Kills only processes it started itself.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\selftest\sys_selftest.ps1 [-LongSec 60] [-NoCompile]
# Output: build\agent8\scratch\sys-test\<HHmmss>\ : selftest.txt (this log), results.json, one sub-dir per driver run.
# Items: a) bad args (+ pid already gone)   b) ~60 s run launched like the runner, 2 live reads, stop file
#        c) dummy exits -> game_exit         d) -MaxSec 5 (+ stale stop file removed)   e) csv checks on b
#        f) driver CPU                       g) sys_summary.py   h) first-row latencies (first compile + cached DLL)
# Exit 0 = no FAIL (INFO lines are measurements, not checks).
param(
    [int]$LongSec = 60,
    [switch]$NoCompile
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 1
$inv = [Globalization.CultureInfo]::InvariantCulture
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
$drv = Join-Path $repo 'bench\agent8\run\drivers\sys-csv.ps1'
$sumPy = Join-Path $repo 'bench\agent8\run\sys_summary.py'
$cacheDir = Join-Path $repo 'build\agent8\cache'
$root = Join-Path $repo ('build\agent8\scratch\sys-test\' + (Get-Date).ToString('HHmmss', $inv))
New-Item -ItemType Directory -Force -Path $root | Out-Null
$logPath = Join-Path $root 'selftest.txt'
$clock = [Diagnostics.Stopwatch]::StartNew()
$results = New-Object System.Collections.ArrayList
$mine = New-Object System.Collections.ArrayList          # every process this script started
$facts = [ordered]@{}
$Header = 't_s,epoch_s,wall,idle_s,fg_pid,fg_game,game_alive,input_desktop,screensaver,cpu_util_pct,cpu_perf_pct,base_mhz,eff_mhz,p_eff_mhz,e_eff_mhz,p_util_pct,e_util_pct,tz_passive_min_pct,tz_temp_max_c,ac,batt_saver,batt_pct,scheme,overlay'
$Col = @{}; $ci = 0; foreach ($h in $Header.Split(',')) { $Col[$h] = $ci; $ci++ }

function Log([string]$M) {
    $l = [string]::Format($inv, '{0} +{1,6:0.0}s {2}', (Get-Date).ToString('HH:mm:ss.fff', $inv), $clock.Elapsed.TotalSeconds, $M)
    Write-Host $l
    [IO.File]::AppendAllText($logPath, $l + "`r`n")
}
function Res([string]$Item, [string]$Status, [string]$Detail) {
    [void]$results.Add([ordered]@{ item = $Item; status = $Status; detail = $Detail })
    Log ('{0,-4} {1}: {2}' -f $Status, $Item, $Detail)
}
function Check([string]$Item, [bool]$Ok, [string]$Detail) { Res $Item $(if ($Ok) { 'PASS' } else { 'FAIL' }) $Detail }
function Info([string]$Item, [string]$Detail) { Res $Item 'INFO' $Detail }
function F([double]$X, [string]$Fmt = '0.000') { return $X.ToString($Fmt, $inv) }
function Num([string]$S) { $v = 0.0; if ($S -and [double]::TryParse($S, [Globalization.NumberStyles]::Float, $inv, [ref]$v)) { return $v }; return $null }
function New-Dir([string]$P) { New-Item -ItemType Directory -Force -Path $P | Out-Null; return $P }

function Start-Dummy([int]$N) {
    $p = Start-Process ping -ArgumentList '-n', "$N", '127.0.0.1' -WindowStyle Hidden -PassThru
    $null = $p.Handle
    [void]$mine.Add($p)
    return $p
}
# Exactly like the runner: Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput <run>\sys.out.txt
#   -RedirectStandardError <run>\sys.err.txt -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',<sys-csv.ps1>,...
function Start-Driver([string]$OutDir, [object[]]$DArgs) {
    $al = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $drv) + @($DArgs | ForEach-Object { [string]$_ })
    $p = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $OutDir 'sys.out.txt') -RedirectStandardError (Join-Path $OutDir 'sys.err.txt') -ArgumentList $al
    $null = $p.Handle
    [void]$mine.Add($p)
    return $p
}
function Read-Shared([string]$Path) {
    $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]'ReadWrite, Delete')
    try { $sr = New-Object IO.StreamReader($fs, (New-Object Text.UTF8Encoding($false)), $false); return $sr.ReadToEnd() }
    finally { $fs.Dispose() }
}
# complete lines only (a partial last line is dropped): @{ header; rows = ArrayList of string[] }
function Get-Rows([string]$Text) {
    $parts = @($Text.Split([string[]]@("`r`n"), [StringSplitOptions]::None))
    $rows = New-Object System.Collections.ArrayList
    $hdr = ''
    if ($parts.Count -ge 2) { $hdr = $parts[0] }
    for ($i = 1; $i -lt $parts.Count - 1; $i++) { [void]$rows.Add($parts[$i].Split(',')) }
    return @{ header = $hdr; rows = $rows }
}
function Get-Out([string]$OutDir) {
    $p = Join-Path $OutDir 'sys.out.txt'
    $lines = @()
    if (Test-Path -LiteralPath $p) { $lines = @(Get-Content -LiteralPath $p) }
    $r = @{ lines = $lines; last = ''; stop = @{}; start = ''; compiled = ''; timing = ''; err = '' }
    if ($lines.Count) { $r.last = [string]$lines[$lines.Count - 1] }
    foreach ($l in $lines) {
        if ($l -match 'sys-csv: start ') { $r.start = $l }
        if ($l -match 'sys-csv: compiled ') { $r.compiled = $l }
        if ($l -match 'sys-csv: timing ') { $r.timing = $l }
    }
    if ($r.last -match 'sys-csv: stop ') { foreach ($m in [regex]::Matches($r.last, '(\w+)=(\S*)')) { $r.stop[$m.Groups[1].Value] = $m.Groups[2].Value } }
    $e = Join-Path $OutDir 'sys.err.txt'
    if (Test-Path -LiteralPath $e) { $r.err = ((@(Get-Content -LiteralPath $e)) -join ' | ') }
    return $r
}
function S([hashtable]$H, [string]$K) { if ($H.ContainsKey($K)) { return [string]$H[$K] }; return '' }
# seconds on $clock when the csv first held a complete data row, -1 if the process exited / timeout first
function Wait-FirstRow([string]$Csv, $P, [double]$TimeoutSec) {
    $end = $clock.Elapsed.TotalSeconds + $TimeoutSec
    while ($clock.Elapsed.TotalSeconds -lt $end) {
        if ([IO.File]::Exists($Csv)) {
            try { if ([regex]::Matches((Read-Shared $Csv), "`r`n").Count -ge 2) { return $clock.Elapsed.TotalSeconds } } catch { }
        }
        if ($P.HasExited) { return -1 }
        Start-Sleep -Milliseconds 25
    }
    return -1
}
function Wait-Until([double]$T, $P) { while ($clock.Elapsed.TotalSeconds -lt $T -and -not $P.HasExited) { Start-Sleep -Milliseconds 200 } }
function Run-Py([string[]]$PyArgs) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $out = (& python $sumPy @PyArgs 2>&1 | Out-String); $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $old }
    return @{ code = $code; out = $out.Trim() }
}
function Read-Json([string]$P) { if (Test-Path -LiteralPath $P) { return (Get-Content -Raw -LiteralPath $P | ConvertFrom-Json) }; return $null }
function Keys($O) { if ($null -eq $O) { return @() }; return @($O.PSObject.Properties | ForEach-Object { $_.Name }) }
function Stop-Mine($P) { try { if (-not $P.HasExited) { $P.Kill(); $null = $P.WaitForExit(3000) } } catch { } }
function Lat-Text([hashtable]$O, [double]$Ext) {
    return ('launch->first row {0} s (external), driver first_row_s={1} first_row_t_s={2} first_sample_ms={3}' -f (F $Ext 2), (S $O.stop 'first_row_s'), (S $O.stop 'first_row_t_s'),
        $(if ($O.timing -match 'first_sample_ms=(\S+)') { $Matches[1] } else { '?' }))
}

$nFail = 0
try {
    Log "sys selftest: out=$root driver=$drv summary=$sumPy LongSec=$LongSec"
    $before = @(Get-ChildItem -LiteralPath $cacheDir -Filter 'LdSys-*.dll' -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    Log ('cache LdSys dlls at start: ' + $(if ($before.Count) { $before -join ' ' } else { 'none' }))

    # ---------------- a) bad args -> exit 2; pid already gone -> exit 0, game_exit, header only ----------------
    $dA = New-Dir (Join-Path $root 'a')
    $dummyA = Start-Dummy 60
    $badCases = @(
        @{ name = 'a1_missing_rundir'; args = @('-GamePid', $dummyA.Id) },
        @{ name = 'a2_gamepid_0'; args = @('-GamePid', '0', '-RunDir', '<dir>') },
        @{ name = 'a3_gamepid_abc'; args = @('-GamePid', 'abc', '-RunDir', '<dir>') },
        @{ name = 'a4_rundir_not_found'; args = @('-GamePid', $dummyA.Id, '-RunDir', (Join-Path $root 'no-such-dir')) }
    )
    foreach ($c in $badCases) {
        $d = New-Dir (Join-Path $dA $c.name)
        $al = @($c.args | ForEach-Object { if ("$_" -eq '<dir>') { $d } else { $_ } })
        $p = Start-Driver $d $al
        $done = $p.WaitForExit(90000)
        $code = if ($done) { $p.ExitCode } else { 'timeout' }
        $o = Get-Out $d
        Check "a) bad args $($c.name)" ($done -and $code -eq 2) ("exit=$code; " + $o.last)
    }
    Stop-Mine $dummyA
    $gone = Start-Process ping -ArgumentList '-n', '1', '127.0.0.1' -WindowStyle Hidden -PassThru
    $null = $gone.WaitForExit(15000); $gonePid = $gone.Id; $gone.Dispose()   # handle closed: the pid no longer exists
    $dA5 = New-Dir (Join-Path $dA 'a5_pid_gone')
    $p = Start-Driver $dA5 @('-GamePid', $gonePid, '-RunDir', $dA5)
    $done = $p.WaitForExit(120000)
    $o = Get-Out $dA5
    $csvA5 = Join-Path $dA5 'sys.csv'
    $txtA5 = if (Test-Path -LiteralPath $csvA5) { Read-Shared $csvA5 } else { '<no csv>' }
    Check 'a) pid not running at start -> exit 0, reason game_exit, header only' ($done -and $p.ExitCode -eq 0 -and (S $o.stop 'reason') -eq 'game_exit' -and (S $o.stop 'rows') -eq '0' -and $txtA5 -eq ($Header + "`r`n")) `
        ("exit=$(if ($done) { $p.ExitCode } else { 'timeout' }) csv_bytes=$($txtA5.Length) header_only=$($txtA5 -eq ($Header + "`r`n")); " + $o.last)

    # ---------------- h) first compile (deletes only LdSys-*.dll = this driver's own cache) ----------------
    if (-not $NoCompile) {
        $locked = @()
        foreach ($f in @(Get-ChildItem -LiteralPath $cacheDir -Filter 'LdSys-*.dll' -ErrorAction SilentlyContinue)) {
            try { Remove-Item -LiteralPath $f.FullName -Force } catch { $locked += $f.Name }
        }
        if ($locked.Count) { Info 'h) first compile' ('skipped, cache file locked: ' + ($locked -join ' ')) }
        else {
            $dH = New-Dir (Join-Path $root 'h_compile')
            $dummyH = Start-Dummy 60
            $t0 = $clock.Elapsed.TotalSeconds
            $p = Start-Driver $dH @('-GamePid', $dummyH.Id, '-RunDir', $dH, '-MaxSec', '3')
            $fr = Wait-FirstRow (Join-Path $dH 'sys.csv') $p 120
            $done = $p.WaitForExit(60000)
            $o = Get-Out $dH
            $lat = if ($fr -ge 0) { $fr - $t0 } else { -1 }
            $facts['first_compile_first_row_s'] = [Math]::Round($lat, 2)
            $facts['first_compile_line'] = $o.compiled
            Check 'h) first compile: compiled + cached, run ok' ($done -and $p.ExitCode -eq 0 -and $o.compiled -match '\(compiled\)' -and $fr -ge 0) `
                ((Lat-Text $o $lat) + '; ' + ($o.compiled -replace '^.*sys-csv: ', ''))
            Stop-Mine $dummyH
        }
    }
    $after = @(Get-ChildItem -LiteralPath $cacheDir -Filter 'LdSys-*.dll' -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    Log ('cache LdSys dlls now: ' + ($after -join ' '))

    # ---------------- b) long run launched exactly like the runner (default params), live reads, stop file ----------------
    $dB = New-Dir (Join-Path $root 'b')
    $csvB = Join-Path $dB 'sys.csv'
    $dummyB = Start-Dummy ($LongSec + 40)
    $t0 = $clock.Elapsed.TotalSeconds
    $pB = Start-Driver $dB @('-GamePid', $dummyB.Id, '-RunDir', $dB)
    $frB = Wait-FirstRow $csvB $pB 120
    $latB = if ($frB -ge 0) { $frB - $t0 } else { -1 }
    Check 'b) driver up, first row written' ($frB -ge 0) ('launch->first row ' + (F $latB 2) + ' s')
    if ($frB -ge 0) {
        Start-Sleep -Seconds 2
        $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($pB.Id)" | ForEach-Object { '{0}({1})' -f $_.Name, $_.ProcessId })
        $kidsReal = @($kids | Where-Object { $_ -notmatch '^conhost\.exe' })
        Check 'b) driver has no child process' ($kidsReal.Count -eq 0) ('children: ' + $(if ($kids.Count) { $kids -join ' ' } else { 'none' }))
        Wait-Until ($frB + 20) $pB
        try {
            $n1 = (Get-Rows (Read-Shared $csvB)).rows.Count
            Check 'b) live read 1 (.NET FileShare.ReadWrite) while the driver writes' ($n1 -ge 10) "rows=$n1"
        } catch { Check 'b) live read 1 (.NET FileShare.ReadWrite) while the driver writes' $false $_.Exception.Message }
        Wait-Until ($frB + 40) $pB
        $r = Run-Py @('--csv', $csvB, '--start-epoch', '0', '--end-epoch', '10000000000', '--out', (Join-Path $dB 'live.json'))
        $lj = Read-Json (Join-Path $dB 'live.json')
        Check 'b) live read 2 (python sys_summary.py on the live csv)' ($r.code -eq 0 -and $null -ne $lj) ("exit=$($r.code) run_rows=$(if ($lj) { $lj.run.rows }) | " + $r.out)
        Wait-Until ($frB + $LongSec) $pB
    }
    $runningB = -not $pB.HasExited
    $stopAt = [DateTime]::Now
    [IO.File]::WriteAllText((Join-Path $dB 'sys.stop'), 'stop')
    $doneB = $pB.WaitForExit(15000)
    $lagB = if ($doneB) { ($pB.ExitTime - $stopAt).TotalSeconds } else { 99 }
    $oB = Get-Out $dB
    $facts['b_stop_line'] = $oB.last
    $facts['b_start_line'] = $oB.start
    $facts['b_timing_line'] = $oB.timing
    Check 'b) stop file -> exit within 2 s, reason stop_file, exit 0' ($runningB -and $doneB -and $lagB -le 2.0 -and $pB.ExitCode -eq 0 -and (S $oB.stop 'reason') -eq 'stop_file') `
        ("running_before_stop=$runningB exit=$(if ($doneB) { $pB.ExitCode } else { 'timeout' }) exit_after=$(F $lagB 3) s; " + ($oB.last -replace '^.*sys-csv: ', ''))
    if ($oB.err) { Info 'b) driver stderr' $oB.err }
    $swB = if ($oB.timing -match ' stop_watch=(\S+) wakes=(\d+) stop_checks=(\d+)') { "stop_watch=$($Matches[1]) wakes=$($Matches[2]) stop_checks=$($Matches[3]) loop_s=$(S $oB.stop 'loop_s') stop->exit $(F $lagB 3) s" } else { 'no stop_watch token on the timing line' }
    $facts['b_stop_watch'] = $swB
    Info 'b) stop file watch (notify = folder change notification + one File.Exists per tick)' $swB
    Stop-Mine $dummyB

    # ---------------- e) csv checks on b ----------------
    $RB = Get-Rows (Read-Shared $csvB)
    $R = $RB.rows
    Check 'e) header exact' ($RB.header -eq $Header) $RB.header
    $loopS = Num (S $oB.stop 'loop_s'); $skB = [int](Num (S $oB.stop 'skipped'))
    $ts = @($R | ForEach-Object { Num $_[$Col['t_s']] })
    # rows + skipped ticks = grid span + 1 (+-1); loop_s also holds the wait for the first power-poll round (<= 2 s),
    # the 0.25 s first-tick spacing and the stop latency, so rows is a bit below loop_s
    $spanT = if ($ts.Count -ge 2) { $ts[$ts.Count - 1] - $ts[0] } else { 0 }
    $expRows = if ($loopS) { $loopS } else { 0 }
    $gridOk = $ts.Count -ge 2 -and [Math]::Abs(($R.Count + $skB) - ($spanT + 1)) -le 1.01
    $loopOk = $R.Count -ge ($expRows - 3.5) -and $R.Count -le ($expRows + 1)
    Check 'e) rows ~= duration' ($R.Count -ge 10 -and $gridOk -and $loopOk) ("rows=$($R.Count) skipped=$skB t_s span=$(F $spanT 3) (rows+skipped vs span+1: $gridOk) loop_s=$(S $oB.stop 'loop_s') (rows within loop_s-3.5..loop_s+1: $loopOk)")
    $deltas = @(for ($k = 1; $k -lt $ts.Count; $k++) { $ts[$k] - $ts[$k - 1] })
    if ($deltas.Count) {
        $m = $deltas | Measure-Object -Minimum -Maximum -Average
        $out = @($deltas | Where-Object { [Math]::Abs($_ - 1.0) -gt 0.15 })
        $big = @($out | Where-Object { $_ -ge 1.85 })
        $sd = [Math]::Sqrt((@($deltas | ForEach-Object { ($_ - $m.Average) * ($_ - $m.Average) }) | Measure-Object -Sum).Sum / $deltas.Count)
        $facts['b_delta_min_max_mean_sd'] = '{0}/{1}/{2}/{3}' -f (F $m.Minimum), (F $m.Maximum), (F $m.Average), (F $sd 4)
        Check 'e) t_s deltas within 1.0 +/- 0.15 s except skipped ticks' ($out.Count -eq $big.Count -and $big.Count -le $skB) `
            ("n=$($deltas.Count) min=$(F $m.Minimum) max=$(F $m.Maximum) mean=$(F $m.Average) sd=$(F $sd 4) outside=$($out.Count) skipped=$skB")
    } else { Check 'e) t_s deltas within 1.0 +/- 0.15 s except skipped ticks' $false 'no deltas' }
    $pl = if ($oB.start -match ' P=\[([^\]]*)\]') { $Matches[1] } else { '' }
    $el = if ($oB.start -match ' E=\[([^\]]*)\]') { $Matches[1] } else { '' }
    $pn = @($pl.Split(',') | Where-Object { $_ -ne '' }).Count; $en = @($el.Split(',') | Where-Object { $_ -ne '' }).Count
    $facts['P'] = $pl; $facts['E'] = $el
    $cls = if ($oB.start -match ' classes=(\S+)') { $Matches[1] } else { '?' }
    Check 'e) P set = 4 logical, E set = 8 logical (i7-1255U)' ($pn -eq 4 -and $en -eq 8) ("P=[$pl] ($pn) E=[$el] ($en) classes=$cls")
    $bas = @($R | ForEach-Object { Num $_[$Col['base_mhz']] } | Where-Object { $null -ne $_ })
    $eff = @($R | ForEach-Object { Num $_[$Col['eff_mhz']] } | Where-Object { $null -ne $_ })
    $pe = @($R | ForEach-Object { Num $_[$Col['p_eff_mhz']] } | Where-Object { $null -ne $_ })
    $ee = @($R | ForEach-Object { Num $_[$Col['e_eff_mhz']] } | Where-Object { $null -ne $_ })
    $okB = $bas.Count -ge 0.9 * $R.Count -and @($bas | Where-Object { $_ -lt 400 -or $_ -gt 6000 }).Count -eq 0
    $okE = $eff.Count -ge 0.9 * $R.Count -and @($eff | Where-Object { $_ -lt 100 -or $_ -gt 7000 }).Count -eq 0
    $mb = if ($bas.Count) { $bas | Measure-Object -Minimum -Maximum -Average } else { $null }
    $me = if ($eff.Count) { $eff | Measure-Object -Minimum -Maximum -Average } else { $null }
    Check 'e) base_mhz / eff_mhz plausible' ($okB -and $okE) `
        ("base n=$($bas.Count) $(if ($mb) { '{0:0}..{1:0} mean {2:0}' -f $mb.Minimum, $mb.Maximum, $mb.Average }); eff n=$($eff.Count) $(if ($me) { '{0:0}..{1:0} mean {2:0}' -f $me.Minimum, $me.Maximum, $me.Average }); p_eff n=$($pe.Count) mean $(if ($pe.Count) { '{0:0}' -f ($pe | Measure-Object -Average).Average }); e_eff n=$($ee.Count) mean $(if ($ee.Count) { '{0:0}' -f ($ee | Measure-Object -Average).Average })")
    $nU = @($R | Where-Object { $null -ne (Num $_[$Col['cpu_util_pct']]) }).Count; $nP = @($R | Where-Object { $null -ne (Num $_[$Col['cpu_perf_pct']]) }).Count
    $nPU = @($R | Where-Object { $null -ne (Num $_[$Col['p_util_pct']]) }).Count; $nEU = @($R | Where-Object { $null -ne (Num $_[$Col['e_util_pct']]) }).Count
    Check 'e) cpu_util_pct / cpu_perf_pct (_Total instance) and p_/e_util_pct filled' ($R.Count -gt 0 -and $nU -eq $R.Count -and $nP -eq $R.Count -and $nPU -eq $R.Count -and $nEU -eq $R.Count) `
        ("rows=$($R.Count) cpu_util=$nU cpu_perf=$nP p_util=$nPU e_util=$nEU")
    $idle = @($R | ForEach-Object { Num $_[$Col['idle_s']] })
    $pairs = 0; $pairsOk = 0; $resets = 0; $worst = 0.0
    for ($k = 1; $k -lt $R.Count; $k++) {
        if ($null -eq $idle[$k] -or $null -eq $idle[$k - 1]) { continue }
        if ($idle[$k] -lt $idle[$k - 1]) { $resets++; continue }
        $pairs++
        $dev = [Math]::Abs(($idle[$k] - $idle[$k - 1]) - ($ts[$k] - $ts[$k - 1]))
        if ($dev -gt $worst) { $worst = $dev }
        if ($dev -le 0.1) { $pairsOk++ }
    }
    Check 'e) idle_s grows with t_s between samples without input' ($pairs -gt 0 -and $pairsOk -ge 0.95 * $pairs) `
        ("pairs=$pairs ok(|d_idle-d_t|<=0.1 s)=$pairsOk worst=$(F $worst 3) input_resets=$resets idle_s first=$(if ($idle.Count) { $idle[0] }) last=$(if ($idle.Count) { $idle[$idle.Count - 1] })")
    $blankSch = @($R | Where-Object { -not $_[$Col['scheme']] }).Count
    $blankOvl = @($R | Where-Object { -not $_[$Col['overlay']] }).Count
    $schV = @($R | ForEach-Object { $_[$Col['scheme']] } | Sort-Object -Unique) -join '|'
    $ovlV = @($R | ForEach-Object { $_[$Col['overlay']] } | Sort-Object -Unique) -join '|'
    Check 'e) scheme / overlay non-blank' ($blankSch -eq 0 -and $blankOvl -eq 0) ("blank scheme=$blankSch overlay=$blankOvl; scheme=$schV overlay=$ovlV")
    $facts['scheme'] = $schV; $facts['overlay'] = $ovlV
    $uniq = { param($c) (@($R | ForEach-Object { $_[$Col[$c]] } | Sort-Object -Unique) -join '|') }
    $tzBlank = @($R | Where-Object { -not $_[$Col['tz_passive_min_pct']] -and -not $_[$Col['tz_temp_max_c']] }).Count
    $own = if ($oB.start -match ' own_desktop=(\S+)') { $Matches[1] } else { '?' }
    Info 'e) other columns' ("fg_pid=$(& $uniq 'fg_pid') fg_game=$(& $uniq 'fg_game') game_alive=$(& $uniq 'game_alive') input_desktop=$(& $uniq 'input_desktop') screensaver=$(& $uniq 'screensaver') ac=$(& $uniq 'ac') batt_saver=$(& $uniq 'batt_saver') batt_pct=$(& $uniq 'batt_pct') tz_blank_rows=$tzBlank/$($R.Count) own_desktop=$own")
    $cu = @($R | ForEach-Object { Num $_[$Col['cpu_util_pct']] } | Where-Object { $null -ne $_ })
    if ($cu.Count) { Info 'e) machine load during b' ('cpu_util_pct mean {0:0.0} (min {1:0.0} max {2:0.0})' -f ($cu | Measure-Object -Average).Average, ($cu | Measure-Object -Minimum).Minimum, ($cu | Measure-Object -Maximum).Maximum) }

    # ---------------- f) driver CPU (from b's stop / timing lines) ----------------
    # steady_cpu_pct, loop_cyc_cpu_pct, cpu_cyc_s: cycle counters / TSC rate (precise). cpu_s, loop_cpu_pct: GetProcessTimes,
    # sampled at the 15.6 ms clock tick (a ~1 ms/s load shows up as a few whole ticks -> noisy). The whole process also holds
    # the one-off powershell.exe startup.
    $steady = Num (S $oB.stop 'steady_cpu_pct'); $loopCyc = Num (S $oB.stop 'loop_cyc_cpu_pct')
    $extCpu = -1.0
    try { $extCpu = $pB.TotalProcessorTime.TotalSeconds } catch { }
    $facts['b_cpu'] = 'cpu_s={0} wall_s={1} cpu_pct={2} cpu_cyc_s={3} loop_s={4} loop_cpu_pct={5} loop_cyc_cpu_pct={6} steady_cpu_pct={7} tsc_mhz={8} ext_cpu_s={9}' -f (S $oB.stop 'cpu_s'), (S $oB.stop 'wall_s'),
        (S $oB.stop 'cpu_pct'), (S $oB.stop 'cpu_cyc_s'), (S $oB.stop 'loop_s'), (S $oB.stop 'loop_cpu_pct'), (S $oB.stop 'loop_cyc_cpu_pct'), (S $oB.stop 'steady_cpu_pct'), (S $oB.stop 'tsc_mhz'), (F $extCpu 3)
    Check 'f) driver CPU in the sampling loop < 0.5 % of one core (cycle counters)' ($null -ne $steady -and $steady -ge 0 -and $steady -lt 0.5 -and $null -ne $loopCyc -and $loopCyc -ge 0 -and $loopCyc -lt 0.5) $facts['b_cpu']
    $sc = if ($oB.timing -match 'sample_cpu_ms=(\S+)') { $Matches[1] } else { '?' }
    $ps = if ($oB.timing -match 'poll_scheme_cpu_ms=(\S+)') { $Matches[1] } else { '?' }
    $po = if ($oB.timing -match 'poll_overlay_cpu_ms=(\S+)') { $Matches[1] } else { '?' }
    $pc = if ($oB.timing -match 'parts_cpu_mean_ms=\[([^\]]*)\]') { $Matches[1] } else { '?' }
    $bt = if ($oB.timing -match 'steady_cpu_pct_by_thread=\[([^\]]*)\]') { $Matches[1] } else { '?' }
    $facts['b_cpu_ms'] = "sample_cpu_ms(first/mean/max)=$sc parts_cpu_mean_ms=[$pc] poll_scheme_cpu_ms(mean/max)=$ps poll_overlay_cpu_ms(mean/max)=$po steady_cpu_pct_by_thread=[$bt]"
    Info 'f) CPU ms per sample / per power poll (cycle counters)' $facts['b_cpu_ms']
    $cycS = Num (S $oB.stop 'cpu_cyc_s'); $loopSec = Num (S $oB.stop 'loop_s')
    $proj = '?'; $startCpu = '?'
    if ($null -ne $cycS -and $cycS -ge 0 -and $null -ne $loopCyc -and $null -ne $loopSec -and $null -ne $steady) {
        $sc0 = $cycS - $loopCyc / 100 * $loopSec
        $startCpu = F $sc0 3
        $proj = '{0} % over a 10 min run, {1} % over 60 min' -f (F (($sc0 + $steady / 100 * 600) / 600 * 100) 2), (F (($sc0 + $steady / 100 * 3600) / 3600 * 100) 2)
        $facts['startup_cpu_s'] = [Math]::Round($sc0, 3)
    }
    Info 'f) whole driver process: cpu_s / wall_s from the stop line (incl. powershell.exe startup + DLL load)' ('cpu_s={0} wall_s={1} -> cpu_pct={2} % of one core (cycle-based cpu_cyc_s={3}); one-off startup CPU {4} s, so the whole process averages {5}' -f
        (S $oB.stop 'cpu_s'), (S $oB.stop 'wall_s'), (S $oB.stop 'cpu_pct'), (S $oB.stop 'cpu_cyc_s'), $startCpu, $proj)
    Info 'f) GetProcessTimes view of the loop (tick-sampled, for comparison)' ('loop_cpu_s={0} loop_cpu_pct={1}' -f (S $oB.stop 'loop_cpu_s'), (S $oB.stop 'loop_cpu_pct'))

    # ---------------- c) the dummy exits -> reason game_exit within 2 s ----------------
    $dC = New-Dir (Join-Path $root 'c')
    $dummyC = Start-Dummy 12
    $t0 = $clock.Elapsed.TotalSeconds
    $pC = Start-Driver $dC @('-GamePid', $dummyC.Id, '-RunDir', $dC)
    $frC = Wait-FirstRow (Join-Path $dC 'sys.csv') $pC 60
    $latC = if ($frC -ge 0) { $frC - $t0 } else { -1 }
    $null = $dummyC.WaitForExit(60000)
    $doneC = $pC.WaitForExit(15000)
    $lagC = if ($doneC) { ($pC.ExitTime - $dummyC.ExitTime).TotalSeconds } else { 99 }
    $oC = Get-Out $dC
    $RC = New-Object System.Collections.ArrayList
    if (Test-Path -LiteralPath (Join-Path $dC 'sys.csv')) { $RC = (Get-Rows (Read-Shared (Join-Path $dC 'sys.csv'))).rows }
    $lastAlive = if ($RC.Count) { $RC[$RC.Count - 1][$Col['game_alive']] } else { '' }
    Check 'c) dummy exit -> exit 0, reason game_exit within 2 s, last row game_alive=0' ($doneC -and $pC.ExitCode -eq 0 -and (S $oC.stop 'reason') -eq 'game_exit' -and $lagC -ge 0 -and $lagC -le 2.0 -and $RC.Count -ge 1 -and $lastAlive -eq '0') `
        ("exit=$(if ($doneC) { $pC.ExitCode } else { 'timeout' }) driver_exit_after_dummy=$(F $lagC 3) s rows=$($RC.Count) last_game_alive=$lastAlive; " + ($oC.last -replace '^.*sys-csv: ', ''))

    # ---------------- d) -MaxSec 5 -> reason max_sec (+ a stale stop file from "an earlier run" is removed, not obeyed) ----------------
    $dD = New-Dir (Join-Path $root 'd')
    [IO.File]::WriteAllText((Join-Path $dD 'sys.stop'), 'left over')
    Start-Sleep -Milliseconds 200
    $dummyD = Start-Dummy 60
    $t0 = $clock.Elapsed.TotalSeconds
    $pD = Start-Driver $dD @('-GamePid', $dummyD.Id, '-RunDir', $dD, '-MaxSec', '5')
    $frD = Wait-FirstRow (Join-Path $dD 'sys.csv') $pD 60
    $latD = if ($frD -ge 0) { $frD - $t0 } else { -1 }
    $doneD = $pD.WaitForExit(60000)
    $oD = Get-Out $dD
    $rowsD = [int](Num (S $oD.stop 'rows'))
    Check 'd) -MaxSec 5 -> exit 0, reason max_sec, ~5 rows' ($doneD -and $pD.ExitCode -eq 0 -and (S $oD.stop 'reason') -eq 'max_sec' -and $rowsD -ge 4 -and $rowsD -le 6) `
        ("exit=$(if ($doneD) { $pD.ExitCode } else { 'timeout' }) rows=$rowsD; " + ($oD.last -replace '^.*sys-csv: ', ''))
    Check 'd) stale stop file (older than the driver) removed at start' ($oD.start -match 'stale_stop_file=removed' -and -not (Test-Path -LiteralPath (Join-Path $dD 'sys.stop'))) `
        $(if ($oD.start -match '(stale_stop_file=\S+|stop_file_present_at_start=\S+)') { $Matches[1] } else { 'no stale-stop-file note on the start line' })
    Stop-Mine $dummyD

    # ---------------- g) sys_summary.py ----------------
    $dG = New-Dir (Join-Path $root 'g')
    $ep = @($R | ForEach-Object { Num $_[$Col['epoch_s']] })
    $topKeys = @('csv', 'window_start_epoch', 'window_end_epoch', 'flags', 'window', 'run')
    $winKeys = @('rows', 'span_s', 'max_gap_s', 'idle_min_s', 'input_events', 'fg_game_share', 'game_alive_all', 'desktop_not_default_rows', 'screensaver_rows',
        'cpu_util_mean', 'eff_mhz_mean', 'eff_mhz_min', 'p_eff_mhz_mean', 'e_eff_mhz_mean', 'p_util_mean', 'e_util_mean', 'tz_passive_min', 'tz_temp_max_c',
        'ac', 'batt_saver', 'batt_pct', 'scheme', 'overlay')
    if ($ep.Count -ge 46) {
        $ws = $ep[15]; $we = $ws + 30
        $j = Join-Path $dG 'win30.json'
        $r = Run-Py @('--csv', $csvB, '--start-epoch', (F $ws), '--end-epoch', (F $we), '--out', $j)
        $J = Read-Json $j
        $missTop = @($topKeys | Where-Object { (Keys $J) -notcontains $_ })
        $missWin = @($winKeys | Where-Object { (Keys $J.window) -notcontains $_ })
        $missRun = @($winKeys | Where-Object { (Keys $J.run) -notcontains $_ })
        $missSub = @(foreach ($k in @('ac', 'batt_saver', 'batt_pct', 'scheme', 'overlay')) { foreach ($s in @('first', 'last', 'changes')) { if ($J -and (Keys $J.window.$k) -notcontains $s) { "$k.$s" } } })
        $fl = if ($J) { @($J.flags) } else { @() }
        $wr = if ($J) { [int]$J.window.rows } else { -1 }
        $flagsOk = ($fl -contains 'not_foreground') -and ($fl -notcontains 'short_window') -and ($skB -gt 0 -or $fl -notcontains 'sample_gaps')
        Check 'g) 30 s sub-window: exit 0, keys, rows 29..32, flags sensible' ($r.code -eq 0 -and $missTop.Count -eq 0 -and $missWin.Count -eq 0 -and $missRun.Count -eq 0 -and $missSub.Count -eq 0 -and $wr -ge 29 -and $wr -le 32 -and $flagsOk) `
            ("exit=$($r.code) window_rows=$wr flags=[$($fl -join ',')] missing=[$(($missTop + $missWin + $missSub) -join ',')] | " + $r.out)
    } else { Check 'g) 30 s sub-window' $false "b has only $($ep.Count) rows" }
    if ($ep.Count -ge 2) {
        $j = Join-Path $dG 'whole.json'
        $r = Run-Py @('--csv', $csvB, '--start-epoch', (F ($ep[0] - 0.001)), '--end-epoch', (F ($ep[$ep.Count - 1] + 0.001)), '--out', $j)
        $J = Read-Json $j
        $fl = if ($J) { @($J.flags) } else { @() }
        Check 'g) whole file: exit 0, window rows = csv rows' ($r.code -eq 0 -and $J -and [int]$J.window.rows -eq $R.Count -and [int]$J.run.rows -eq $R.Count -and $fl -notcontains 'short_window') `
            ("exit=$($r.code) window_rows=$(if ($J) { $J.window.rows }) csv_rows=$($R.Count) flags=[$($fl -join ',')]")
        $facts['g_whole_summary'] = $r.out
        $tr = Join-Path $dG 'truncated.csv'
        $bytes = [IO.File]::ReadAllBytes($csvB)
        [IO.File]::WriteAllBytes($tr, [byte[]]($bytes[0..($bytes.Length - 11)]))
        $j = Join-Path $dG 'truncated.json'
        $r = Run-Py @('--csv', $tr, '--start-epoch', (F ($ep[0] - 0.001)), '--end-epoch', (F ($ep[$ep.Count - 1] + 0.001)), '--out', $j)
        $J = Read-Json $j
        Check 'g) csv with a truncated last line: exit 0, partial row dropped' ($r.code -eq 0 -and $J -and $J.file.truncated_last_line -eq $true -and [int]$J.run.rows -eq ($R.Count - 1)) `
            ("exit=$($r.code) truncated_last_line=$(if ($J) { $J.file.truncated_last_line }) rows=$(if ($J) { $J.run.rows }) (csv rows $($R.Count))")
    }
    $j = Join-Path $dG 'missing.json'
    $r = Run-Py @('--csv', (Join-Path $dG 'no-such.csv'), '--start-epoch', '0', '--end-epoch', '1', '--out', $j)
    $J = Read-Json $j
    Check 'g) missing csv: exit 1, {"error": ...} written' ($r.code -eq 1 -and $J -and (Keys $J) -contains 'error') ("exit=$($r.code) | " + $r.out)
    $j = Join-Path $dG 'header_only.json'
    $r = Run-Py @('--csv', $csvA5, '--start-epoch', '0', '--end-epoch', '30', '--out', $j)
    $J = Read-Json $j
    Check 'g) header-only csv (a5): exit 0, rows 0, short_window' ($r.code -eq 0 -and $J -and [int]$J.window.rows -eq 0 -and @($J.flags) -contains 'short_window') ("exit=$($r.code) | " + $r.out)
    $csvC = Join-Path $dC 'sys.csv'
    $j = Join-Path $dG 'c_game_exit.json'
    $r = Run-Py @('--csv', $csvC, '--start-epoch', '0', '--end-epoch', '10000000000', '--out', $j)
    $J = Read-Json $j
    Check 'g) game-exit csv (c): exit 0, run.game_alive_all = false' ($r.code -eq 0 -and $J -and $J.run.game_alive_all -eq $false) ("exit=$($r.code) game_alive_all=$(if ($J) { $J.run.game_alive_all }) | " + $r.out)

    # ---------------- h) latencies ----------------
    $facts['cached_first_row_s'] = 'b={0} c={1} d={2}' -f (F $latB 2), (F $latC 2), (F $latD 2)
    Info 'h) cached DLL, case b' (Lat-Text $oB $latB)
    Info 'h) cached DLL, case c' (Lat-Text $oC $latC)
    Info 'h) cached DLL, case d' (Lat-Text $oD $latD)
    $initB = if ($oB.start -match ' init_ms=(\S+) init_parts_ms=\[([^\]]*)\]') { "init_ms=$($Matches[1]) [$($Matches[2])]" } else { '' }
    Info 'h) init breakdown (b)' $initB
} catch {
    Res 'selftest' 'FAIL' ('unexpected error: ' + $_.Exception.Message + ' @ ' + ($_.InvocationInfo.PositionMessage -replace '\s+', ' '))
} finally {
    foreach ($p in $mine) { try { if (-not $p.HasExited) { $p.Kill(); Log "killed leftover (own) pid $($p.Id)" } } catch { } }
    $nPass = @($results | Where-Object { $_.status -eq 'PASS' }).Count
    $nFail = @($results | Where-Object { $_.status -eq 'FAIL' }).Count
    $nInfo = @($results | Where-Object { $_.status -eq 'INFO' }).Count
    $obj = [ordered]@{ out_dir = $root; pass = $nPass; fail = $nFail; info = $nInfo; results = @($results); facts = $facts }
    [IO.File]::WriteAllText((Join-Path $root 'results.json'), ($obj | ConvertTo-Json -Depth 6))
    Log ("SELFTEST {0}: pass={1} fail={2} info={3} -> {4}" -f $(if ($nFail) { 'FAILED' } else { 'OK' }), $nPass, $nFail, $nInfo, $root)
}
if ($nFail) { exit 1 }
exit 0
