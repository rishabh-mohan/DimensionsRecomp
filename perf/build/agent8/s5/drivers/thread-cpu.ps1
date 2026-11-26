# Driver for run-timing.ps1 -Driver (matrix arm field "driver"): per-thread CPU of the game over the measure window
# (the headroom metric) plus a 1 s NVML GPU log. Agent 8, window 3 (2026-11-21).
# run-timing starts it at the measure-start mark with -GamePid/-RunDir and, after the window, WAITS for it before it
# sends WM_CLOSE (up to -DriverTimeoutSec, 120 s by default). This driver:
#   1. opens NVML via harness\nvml.cs (Agent 3's LdNvml, compiled once to build\agent8\cache; not with -NoGpu);
#   2. every -IntervalSec reads the CPU time (kernel+user) of every game thread (.NET ProcessThread: no compile in the
#      window), until the proc.csv row whose note says "measure end";
#   3. takes a last sample, closes NVML, writes gpu.csv, then reads the thread names (GetThreadDescription; compiled only now, so
#      the window carries no Add-Type cost);
#   4. writes <run>\threads.csv (one row per thread, busiest first), <run>\headroom.json and one "HEADROOM" line.
# Metric: busy_pct = thread CPU seconds / driver window seconds x 100 (100 = one full core). top1 = the busiest thread
# (normally the guest main or render thread); headroom_pct = 100 - top1 busy_pct. max_busy_pct = its busiest 1 s.
# The driver window starts 1-3 s after the frame window (PowerShell start-up) and ends at the same mark.
# Exit 0 normally (also when the game exits early: "partial": true). Exit 2: bad arguments. Exit 4: no window end
# within -MaxSec.
param(
    [int]$GamePid = 0,
    [string]$RunDir = '',
    [double]$IntervalSec = 1.0,
    [double]$MaxSec = 1800,
    [switch]$NoGpu
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$sw = [Diagnostics.Stopwatch]::StartNew()
$inv = [Globalization.CultureInfo]::InvariantCulture
function Say([string]$M) { Write-Output ('{0} +{1:0.00}s {2}' -f (Get-Date).ToString('HH:mm:ss.fff'), $sw.Elapsed.TotalSeconds, $M) }
function Rnd([double]$X, [int]$D) { return [math]::Round($X, $D) }

# Reads the bytes appended since $State.Offset (the runner keeps appending; share everything).
function Read-New([hashtable]$State) {
    if (-not (Test-Path -LiteralPath $State.Path)) { return '' }
    $share = [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
    $fs = [IO.File]::Open($State.Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, $share)
    try {
        if ($fs.Length -lt $State.Offset) { $State.Offset = [int64]0 }
        $n = $fs.Length - $State.Offset
        if ($n -le 0) { return '' }
        $null = $fs.Seek($State.Offset, [IO.SeekOrigin]::Begin)
        $buf = New-Object byte[] ([int][math]::Min($n, 16MB))
        $got = $fs.Read($buf, 0, $buf.Length)
        $State.Offset += $got
        $text = $State.Carry + [Text.Encoding]::UTF8.GetString($buf, 0, $got)
        $cut = $text.LastIndexOf("`n")
        if ($cut -lt 0) { $State.Carry = $text; return '' }
        $State.Carry = $text.Substring($cut + 1)
        return $text.Substring(0, $cut + 1)
    } finally { $fs.Dispose() }
}

if (-not $RunDir -or -not (Test-Path -LiteralPath $RunDir -PathType Container)) { Say "bad -RunDir '$RunDir'"; exit 2 }
if ($IntervalSec -lt 0.25) { $IntervalSec = 0.25 }
$game = $null
try { $game = [Diagnostics.Process]::GetProcessById($GamePid) } catch { Say "game pid $GamePid not found (already gone?)"; exit 0 }
$procCsv = Join-Path $RunDir 'proc.csv'
$gpuCsv = Join-Path $RunDir 'gpu.csv'
Say "thread-cpu: pid $GamePid, run dir $RunDir, interval $IntervalSec s"

# 1. GPU log: NVML through harness\nvml.cs (Agent 3's LdNvml: ~0.1 ms per sample, no extra process, nothing
#    buffered), one sample per CPU sample, kept in memory and written to gpu.csv at the end. (nvidia-smi -lms -f
#    buffered in 4 KB chunks and lost the tail when killed: verify3 gpu.csv 4167 B and 0 B.) The C# is compiled once
#    to build\agent8\cache\LdNvml-<ticks>.dll, so a normal run only loads it (no csc inside the frame window).
$nvmlOk = $false
$gpuRows = New-Object System.Collections.Generic.List[string]
$gpuHeader = 't_s,pstate,gr_mhz,mem_mhz,temp_c,power_w,util_gpu,util_mem,throttle'
if (-not $NoGpu) {
    try {
        $repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
        $nvmlCs = Join-Path $repo 'harness\nvml.cs'
        if (-not (Test-Path -LiteralPath $nvmlCs)) { throw "no $nvmlCs" }
        if (-not ('LdNvml' -as [type])) {
            $cacheDir = Join-Path $repo 'build\agent8\cache'
            $dll = Join-Path $cacheDir ('LdNvml-{0}.dll' -f (Get-Item -LiteralPath $nvmlCs).LastWriteTimeUtc.Ticks)
            if (-not (Test-Path -LiteralPath $dll)) {
                New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
                Add-Type -Path $nvmlCs -OutputAssembly $dll -OutputType Library
                Say "compiled $dll"
            }
            if (-not ('LdNvml' -as [type])) { Add-Type -Path $dll }
        }
        $e = [LdNvml]::Open()
        if ([string]::IsNullOrEmpty($e)) { $nvmlOk = $true; Say "NVML open: $([LdNvml]::Name) -> gpu.csv ($gpuHeader)" }
        else { Say "WARNING: NVML open failed: $e (no gpu.csv)" }
    } catch { Say "WARNING: no NVML: $($_.Exception.Message) (no gpu.csv)" }
}
function Take-Gpu {
    if (-not $nvmlOk) { return }
    try { $g = [LdNvml]::Sample(); if ($g) { $gpuRows.Add(('{0},{1}' -f $sw.Elapsed.TotalSeconds.ToString('0.00', $inv), $g)) } } catch { }
}

# 2. Thread CPU samples.
$prev = @{}; $first = @{}; $firstAt = @{}; $maxBusy = @{}
$script:lastAt = $null; $script:samples = 0; $script:lastCount = 0
function Take-Sample {
    $now = $sw.Elapsed.TotalSeconds
    $p = [Diagnostics.Process]::GetProcessById($GamePid)
    $n = 0
    try {
        $dt = if ($null -ne $script:lastAt) { $now - $script:lastAt } else { 0 }
        foreach ($t in $p.Threads) {
            $tid = [int]$t.Id
            $c = $null
            try { $c = $t.TotalProcessorTime.Ticks } catch { continue }
            $n++
            if ($prev.ContainsKey($tid)) {
                if ($dt -gt 0.2) {
                    $b = ($c - $prev[$tid]) / 1e7 / $dt
                    if (-not $maxBusy.ContainsKey($tid) -or $b -gt $maxBusy[$tid]) { $maxBusy[$tid] = $b }
                }
            } else { $first[$tid] = $c; $firstAt[$tid] = $now }
            $prev[$tid] = $c
        }
    } finally { $p.Dispose() }
    $script:lastAt = $now; $script:samples++; $script:lastCount = $n
    Take-Gpu
}

$partial = $false; $why = ''; $timedOut = $false
try { Take-Sample } catch { $partial = $true; $why = "first sample failed: $($_.Exception.Message)" }
$t0 = $script:lastAt
if ($null -eq $t0) { $t0 = $sw.Elapsed.TotalSeconds }
Say "first sample: $($script:lastCount) threads"
$pc = @{ Path = $procCsv; Offset = [int64]0; Carry = '' }
$ended = $false
$nextAt = $t0 + $IntervalSec
while (-not $ended -and -not $partial) {
    if ($game.HasExited) { $partial = $true; $why = "the game exited before the window end (exit $($game.ExitCode))"; break }
    if ($sw.Elapsed.TotalSeconds -gt $MaxSec) { $timedOut = $true; break }
    try { if ((Read-New $pc) -match 'measure end') { $ended = $true; break } } catch { }
    $now = $sw.Elapsed.TotalSeconds
    if ($now -ge $nextAt) {
        try { Take-Sample } catch { }
        $nextAt += $IntervalSec
        if ($nextAt -lt $sw.Elapsed.TotalSeconds) { $nextAt = $sw.Elapsed.TotalSeconds + $IntervalSec }   # late pass: no catch-up burst
    }
    Start-Sleep -Milliseconds 200
}
if ($ended) {
    Say 'window end seen in proc.csv'
    try { Take-Sample } catch { $partial = $true; $why = "last sample failed: $($_.Exception.Message)" }
} elseif ($timedOut) { Say "!!! no 'measure end' row in proc.csv within $MaxSec s" }
else { Say "!!! $why" }
$t1 = $script:lastAt
if ($null -eq $t1) { $t1 = $t0 }

# 3. Stop the GPU log, then the thread names.
if ($nvmlOk) {
    try { [LdNvml]::Close() } catch { }
    try { [IO.File]::WriteAllLines($gpuCsv, [string[]](@($gpuHeader) + @($gpuRows)), [Text.Encoding]::ASCII) } catch { Say "WARNING: gpu.csv not written: $($_.Exception.Message)" }
}
$names = @{}
if (-not $game.HasExited -and $prev.Count) {
    try {
        Add-Type -Namespace LdThr -Name Desc -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenThread(uint access, bool inherit, uint tid);
[DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
[DllImport("kernel32.dll")] static extern int GetThreadDescription(IntPtr h, out IntPtr desc);
[DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);
public static string Name(uint tid) {
    IntPtr h = OpenThread(0x0800, false, tid);
    if (h == IntPtr.Zero) return null;
    try {
        IntPtr p;
        if (GetThreadDescription(h, out p) < 0 || p == IntPtr.Zero) return null;
        try { return Marshal.PtrToStringUni(p); } finally { LocalFree(p); }
    } finally { CloseHandle(h); }
}
'@
        foreach ($tid in @($prev.Keys)) { try { $nm = [LdThr.Desc]::Name([uint32]$tid); if ($nm) { $names[$tid] = $nm.Trim() } } catch { } }
    } catch { Say "WARNING: no thread names: $($_.Exception.Message)" }
}

# 4. Outputs.
$win = $t1 - $t0
$rows = New-Object System.Collections.Generic.List[object]
foreach ($tid in @($prev.Keys)) {
    $cpu = ($prev[$tid] - $first[$tid]) / 1e7
    $rows.Add([pscustomobject][ordered]@{
        tid = $tid
        name = $(if ($names.ContainsKey($tid)) { $names[$tid] } else { '' })
        cpu_s = (Rnd $cpu 3)
        busy_pct = $(if ($win -gt 0) { Rnd ($cpu / $win * 100) 1 } else { 0 })
        max_busy_pct = $(if ($maxBusy.ContainsKey($tid)) { Rnd ($maxBusy[$tid] * 100) 1 } else { $null })
        first_seen_s = (Rnd ($firstAt[$tid] - $t0) 1)
    })
}
$sorted = @($rows | Sort-Object -Property @{ Expression = { [double]$_.cpu_s }; Descending = $true }, tid)
if ($sorted.Count) { $sorted | Export-Csv -LiteralPath (Join-Path $RunDir 'threads.csv') -NoTypeInformation -Encoding UTF8 }

$gpu = $null
if ($gpuRows.Count) {
    $u = New-Object System.Collections.Generic.List[double]; $um = New-Object System.Collections.Generic.List[double]
    $clk = New-Object System.Collections.Generic.List[double]; $pw = New-Object System.Collections.Generic.List[double]
    $tmax = $null; $pst = @{}; $thrPower = 0; $thrThermal = 0
    foreach ($line in $gpuRows) {
        # t_s,pstate,gr_mhz,mem_mhz,temp_c,power_w,util_gpu,util_mem,throttle (LdNvml.Sample after our t_s)
        $f = @($line -split ',\s*')
        if ($f.Count -lt 8) { continue }
        $x = 0.0
        if (-not [double]::TryParse($f[6], [Globalization.NumberStyles]::Float, $inv, [ref]$x)) { continue }
        $u.Add($x)
        if ([double]::TryParse($f[7], [Globalization.NumberStyles]::Float, $inv, [ref]$x)) { $um.Add($x) }
        if ([double]::TryParse($f[2], [Globalization.NumberStyles]::Float, $inv, [ref]$x)) { $clk.Add($x) }
        if ([double]::TryParse($f[5], [Globalization.NumberStyles]::Float, $inv, [ref]$x)) { $pw.Add($x) }
        if ([double]::TryParse($f[4], [Globalization.NumberStyles]::Float, $inv, [ref]$x)) { if ($null -eq $tmax -or $x -gt $tmax) { $tmax = $x } }
        $ps = $f[1].Trim(); if ($ps) { $pst[$ps] = 1 + $(if ($pst.ContainsKey($ps)) { $pst[$ps] } else { 0 }) }
        if ($f.Count -ge 9) {
            $tr = [uint64]0; $ts = $f[8].Trim()
            $okT = if ($ts -match '^0[xX]([0-9a-fA-F]+)$') { [uint64]::TryParse($Matches[1], [Globalization.NumberStyles]::HexNumber, $inv, [ref]$tr) } else { [uint64]::TryParse($ts, [ref]$tr) }
            if ($okT) { if ($tr -band 0x4) { $thrPower++ }; if ($tr -band 0x60) { $thrThermal++ } }
        }
    }
    if ($u.Count) {
        $us = @($u | Sort-Object)
        $gpu = [ordered]@{
            samples = $u.Count
            util_mean = (Rnd (($u | Measure-Object -Average).Average) 1)
            util_median = $us[[int][math]::Floor(($us.Count - 1) / 2)]
            util_p90 = $us[[int][math]::Min($us.Count - 1, [math]::Ceiling(0.9 * $us.Count) - 1)]
            util_max = $us[$us.Count - 1]
            mem_util_mean = $(if ($um.Count) { Rnd (($um | Measure-Object -Average).Average) 1 } else { $null })
            clock_gr_mean = $(if ($clk.Count) { Rnd (($clk | Measure-Object -Average).Average) 0 } else { $null })
            clock_gr_min = $(if ($clk.Count) { ($clk | Measure-Object -Minimum).Minimum } else { $null })
            power_w_mean = $(if ($pw.Count) { Rnd (($pw | Measure-Object -Average).Average) 2 } else { $null })
            temp_max = $tmax
            pstates = (($pst.Keys | Sort-Object | ForEach-Object { "$_ x$($pst[$_])" }) -join ' ')
            throttle_power_samples = $thrPower
            throttle_thermal_samples = $thrThermal
        }
    }
}

$sum = 0.0; foreach ($r in $sorted) { $sum += [double]$r.cpu_s }
$top1 = if ($sorted.Count) { $sorted[0] } else { $null }
$H = [ordered]@{
    driver = 'thread-cpu'; pid = $GamePid; partial = $partial; partial_why = $why; timed_out = $timedOut
    window_s = (Rnd $win 3); samples = $script:samples; interval_s = $IntervalSec
    threads = $sorted.Count; named = @($sorted | Where-Object { $_.name }).Count
    sum_busy_cores = $(if ($win -gt 0) { Rnd ($sum / $win) 3 } else { $null })
    top1_tid = $(if ($top1) { $top1.tid } else { $null }); top1_name = $(if ($top1) { $top1.name } else { $null })
    top1_busy_pct = $(if ($top1) { $top1.busy_pct } else { $null }); top1_max_busy_pct = $(if ($top1) { $top1.max_busy_pct } else { $null })
    top2_busy_pct = $(if ($sorted.Count -ge 2) { $sorted[1].busy_pct } else { $null })
    top3_busy_pct = $(if ($sorted.Count -ge 3) { $sorted[2].busy_pct } else { $null })
    headroom_pct = $(if ($top1) { Rnd (100 - [double]$top1.busy_pct) 1 } else { $null })
    top = @($sorted | Select-Object -First 8 | ForEach-Object { [ordered]@{ tid = $_.tid; name = $_.name; busy_pct = $_.busy_pct; max_busy_pct = $_.max_busy_pct } })
    gpu = $gpu
}
($H | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath (Join-Path $RunDir 'headroom.json') -Encoding UTF8
$tops = @($sorted | Select-Object -First 3 | ForEach-Object { "'$($_.name)' $($_.tid) $($_.busy_pct)%" }) -join ', '
$gtxt = if ($gpu) { "GPU util mean $($gpu.util_mean)% p90 $($gpu.util_p90)% max $($gpu.util_max)%, clock $($gpu.clock_gr_mean) MHz, $($gpu.samples) samples" } else { 'no GPU data' }
Say ("HEADROOM top {0}; top1 max 1 s {1}%; headroom {2}%; sum {3} cores over {4} s, {5} samples, {6} threads ({7} named); {8}{9}" -f $tops, $H.top1_max_busy_pct, $H.headroom_pct, $H.sum_busy_cores, $H.window_s, $H.samples, $H.threads, $H.named, $gtxt, $(if ($partial) { "; PARTIAL: $why" } else { '' }))
if ($timedOut) { exit 4 }
exit 0
