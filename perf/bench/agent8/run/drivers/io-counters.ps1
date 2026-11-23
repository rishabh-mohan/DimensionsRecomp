# Driver for run-timing.ps1 -Driver (matrix arm field "driver"): host I/O counters of the game process.
# Agent 12's metric 3 (perf-notes/agent12-io-memory.md, "In-game A/B plan"): ReadOperationCount/ReadTransferCount.
#
# run-timing.ps1 starts the driver at the measure-start mark with -GamePid/-RunDir and waits for it after the window
# (before WM_CLOSE). This driver samples GetProcessIoCounters (cumulative since the game started) every -IntervalSec
# until the proc.csv row whose note says "measure end" (the window end; no fixed length, so -Quick works), then
# writes <run>\io.csv and prints a summary line.
#   - The first row is everything up to the window start: boot, menus and any level load.
#   - Rows: t_s (seconds since this driver's process start, which is about the measure-start mark), cumulative ops
#     and MB for read/write/other.
# Cost: one Add-Type compile (csc) at the start of the window, the same in every arm that uses this driver; do not
# compare cpu_cores between arms with and without it.
# Exit 0 always once the game pid was opened (the game exiting early is reported by the runner); 2 = bad arguments.
param(
    [int]$GamePid = 0,
    [string]$RunDir = '',
    [double]$IntervalSec = 1,
    [double]$MaxSec = 1800,
    [string]$Out = 'io.csv'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$t0 = (Get-Process -Id $PID).StartTime
function Now-S { return ((Get-Date) - $t0).TotalSeconds }
function Say([string]$M) { Write-Output ('{0} +{1:0.00}s {2}' -f (Get-Date).ToString('HH:mm:ss.fff'), (Now-S), $M) }
if (-not $RunDir -or -not (Test-Path -LiteralPath $RunDir -PathType Container)) { Say "bad -RunDir '$RunDir'"; exit 2 }

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class LdIoCounters {
    [StructLayout(LayoutKind.Sequential)]
    public struct IO_COUNTERS {
        public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount;
        public ulong ReadTransferCount, WriteTransferCount, OtherTransferCount;
    }
    [DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError = true)] public static extern bool GetProcessIoCounters(IntPtr h, out IO_COUNTERS c);
    [DllImport("kernel32.dll", SetLastError = true)] public static extern uint WaitForSingleObject(IntPtr h, uint ms);
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
}
'@
# PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE: enough for GetProcessIoCounters and the exit check.
$h = [LdIoCounters]::OpenProcess(0x1000 -bor 0x00100000, $false, $GamePid)
if ($h -eq [IntPtr]::Zero) { Say "could not open pid $GamePid (error $([Runtime.InteropServices.Marshal]::GetLastWin32Error()); gone?)"; exit 0 }
$outPath = if ([IO.Path]::IsPathRooted($Out)) { $Out } else { Join-Path $RunDir $Out }
$procCsv = Join-Path $RunDir 'proc.csv'
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add('t_s,read_ops,read_mb,write_ops,write_mb,other_ops,other_mb,note')
$inv = [Globalization.CultureInfo]::InvariantCulture
$first = $null; $last = $null; $n = 0
function Sample([string]$Note) {
    $c = New-Object LdIoCounters+IO_COUNTERS
    if (-not [LdIoCounters]::GetProcessIoCounters($h, [ref]$c)) { return $null }
    $s = [ordered]@{ t = (Now-S); r = $c.ReadOperationCount; rb = $c.ReadTransferCount; w = $c.WriteOperationCount; wb = $c.WriteTransferCount
                     o = $c.OtherOperationCount; ob = $c.OtherTransferCount }
    $rows.Add([string]::Format($inv, '{0:0.00},{1},{2:0.000},{3},{4:0.000},{5},{6:0.000},{7}', $s.t, $s.r, $s.rb / 1MB, $s.w, $s.wb / 1MB, $s.o, $s.ob / 1MB, $Note))
    return $s
}
Say "io-counters: pid $GamePid, every $IntervalSec s until the window end, out $outPath"
$pcOffset = [int64]0; $ended = $false; $why = 'window end'
try {
    $first = Sample 'first'; $last = $first
    while ($true) {
        if ([LdIoCounters]::WaitForSingleObject($h, 0) -eq 0) { $why = 'game exited'; break }
        if ((Now-S) -gt $MaxSec) { $why = "MaxSec $MaxSec"; break }
        try {
            if (Test-Path -LiteralPath $procCsv) {
                $share = [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
                $fs = [IO.File]::Open($procCsv, [IO.FileMode]::Open, [IO.FileAccess]::Read, $share)
                try {
                    if ($fs.Length -gt $pcOffset) {
                        $null = $fs.Seek($pcOffset, [IO.SeekOrigin]::Begin)
                        $buf = New-Object byte[] ([int]($fs.Length - $pcOffset)); $got = $fs.Read($buf, 0, $buf.Length); $pcOffset += $got
                        if ([Text.Encoding]::ASCII.GetString($buf, 0, $got) -match 'measure end') { $ended = $true }
                    }
                } finally { $fs.Dispose() }
            }
        } catch { }
        if ($ended) { break }
        Start-Sleep -Milliseconds ([int]($IntervalSec * 1000))
        $s = Sample ''; if ($null -ne $s) { $last = $s; $n++ }
    }
    $s = Sample "last ($why)"; if ($null -ne $s) { $last = $s }
} finally {
    [void][LdIoCounters]::CloseHandle($h)
    $rows | Set-Content -LiteralPath $outPath -Encoding ascii
}
if ($null -ne $first -and $null -ne $last) {
    Say ([string]::Format($inv, 'io: up to the window start (t={0:0.0} s): reads {1} ops {2:0.0} MB, writes {3} ops {4:0.0} MB, other {5} ops',
        $first.t, $first.r, $first.rb / 1MB, $first.w, $first.wb / 1MB, $first.o))
    Say ([string]::Format($inv, 'io: at the end ({0}, t={1:0.0} s): reads {2} ops {3:0.0} MB; in the window: reads {4} ops {5:0.0} MB, writes {6} ops',
        $why, $last.t, $last.r, $last.rb / 1MB, ($last.r - $first.r), (($last.rb - $first.rb) / 1MB), ($last.w - $first.w)))
} else { Say 'io: no samples' }
exit 0
