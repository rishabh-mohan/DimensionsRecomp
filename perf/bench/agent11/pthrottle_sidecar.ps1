# pthrottle_sidecar.ps1 - S4 task #24: the runner-side execution-speed opt-out as a sidecar next to
# Agent 8's unchanged run-matrix.ps1 (nothing in bench\agent8 or harness is edited). Started by
# pthrottle_pairs.ps1. It polls for -ProcessName processes whose exe lies under -RunsDir (the runs
# dir of the pairs' own matrix). Any other process, other agents' games included, is only probed
# for its creation time and image path (QUERY_LIMITED_INFORMATION handle, closed at once), never set.
# For each tracked process it opens a narrow handle (SET_INFORMATION | QUERY_LIMITED_INFORMATION |
# SYNCHRONIZE) and:
#   - opt-out arm (run dir <HHmm>-<OnArm>-r<k>): read-modify-write so EXECUTION_SPEED is controlled
#     and off, every other bit kept; reads it back ("before" -> "after");
#   - off arm: reads only, never sets;
#   - every poll re-reads the state (transitions are logged); on the opt-out arm it re-applies when
#     the bit is gone (the game's own startup call replaces the whole state) and counts "reapplied";
#   - at exit writes <OutDir>\<run dir name>.json.
# Ends when -StopFile exists and nothing is tracked, or after -MaxMinutes. Single-threaded.
[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)][string]$RunsDir,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$ProcessName = 'legodimensions',
    [string]$OnArm = 'd0e',
    [string]$StopFile = '',
    [int]$PollMs = 500,
    [double]$MaxMinutes = 60
)
$ErrorActionPreference = 'Stop'
$csharp = @'
using System;
using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential)]
public struct PowerThrottlingState { public uint Version, ControlMask, StateMask; }
public static class PtSidecar {
  const int ProcessPowerThrottling = 4;
  public const uint ExecutionSpeed = 0x1;
  public const uint Access = 0x0200 | 0x1000 | 0x00100000; // SET_INFORMATION | QUERY_LIMITED_INFORMATION | SYNCHRONIZE
  [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetProcessInformation(IntPtr p, int c, ref PowerThrottlingState s, int n);
  [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetProcessInformation(IntPtr p, int c, ref PowerThrottlingState s, int n);
  [DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
  [DllImport("kernel32.dll", SetLastError = true)] public static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr h, uint ms);
  [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetExitCodeProcess(IntPtr h, out uint code);
  public static int Read(IntPtr p, out PowerThrottlingState s) {
    s = new PowerThrottlingState(); s.Version = 1;
    return GetProcessInformation(p, ProcessPowerThrottling, ref s, Marshal.SizeOf(typeof(PowerThrottlingState))) ? 0 : Marshal.GetLastWin32Error();
  }
  static int Write(IntPtr p, uint c, uint st) {
    PowerThrottlingState s = new PowerThrottlingState(); s.Version = 1; s.ControlMask = c; s.StateMask = st;
    return SetProcessInformation(p, ProcessPowerThrottling, ref s, Marshal.SizeOf(typeof(PowerThrottlingState))) ? 0 : Marshal.GetLastWin32Error();
  }
  public static bool IsOptedOut(PowerThrottlingState s) { return (s.ControlMask & ExecutionSpeed) != 0 && (s.StateMask & ExecutionSpeed) == 0; }
  // Read, set EXECUTION_SPEED controlled + off keeping every other bit, read back. 0 = opted out.
  public static int OptOut(IntPtr p, out PowerThrottlingState before, out PowerThrottlingState after) {
    after = new PowerThrottlingState();
    int e = Read(p, out before); if (e != 0) return e;
    e = Write(p, before.ControlMask | ExecutionSpeed, before.StateMask & ~ExecutionSpeed); if (e != 0) return e;
    e = Read(p, out after); if (e != 0) return e;
    return IsOptedOut(after) ? 0 : -1;
  }
  public static bool Exited(IntPtr h) { return WaitForSingleObject(h, 0) == 0; }
  public static long ExitCode(IntPtr h) { uint c; return GetExitCodeProcess(h, out c) ? (long)c : -1; }
  public static string Str(PowerThrottlingState s) { return string.Format("C=0x{0:X} S=0x{1:X}", s.ControlMask, s.StateMask); }
  [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern bool QueryFullProcessImageName(IntPtr h, int flags, System.Text.StringBuilder name, ref int size);
  [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetProcessTimes(IntPtr h, out long creation, out long exit, out long kernel, out long user);
  // "<creation FILETIME>|<image path>" through a QUERY_LIMITED_INFORMATION handle (valid right after
  // process creation, unlike Process.Path); null when the process cannot be opened.
  public static string Probe(int pid) {
    IntPtr h = OpenProcess(0x1000, false, pid);
    if (h == IntPtr.Zero) return null;
    try {
      long c, e, k, u; string t = GetProcessTimes(h, out c, out e, out k, out u) ? c.ToString() : "0";
      System.Text.StringBuilder sb = new System.Text.StringBuilder(1024); int n = sb.Capacity;
      return t + "|" + (QueryFullProcessImageName(h, 0, sb, ref n) ? sb.ToString() : "");
    } finally { CloseHandle(h); }
  }
}
'@
Add-Type -TypeDefinition $csharp -Language CSharp
$runsFull = [IO.Path]::GetFullPath($RunsDir).TrimEnd('\') + '\'
if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
$log = Join-Path $OutDir 'sidecar.log'
function Log([string]$s) { Add-Content -LiteralPath $log -Value ('{0:HH:mm:ss.fff} {1}' -f (Get-Date), $s) -Encoding ascii }
function Epoch { [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0 }
$onRe = '^\d{4}-' + [regex]::Escape($OnArm) + '-r\d+(-r\d+)?$'
$tracked = @{}; $ignored = @{}; $retry = @{}
$deadline = (Get-Date).AddMinutes($MaxMinutes)
function Finish($t, [string]$why) {
    $t.exited_s = [math]::Round(((Get-Date) - $t.t0).TotalSeconds, 2)
    $t.exit_code = [PtSidecar]::ExitCode($t.h)
    $null = [PtSidecar]::CloseHandle($t.h)
    $held = if ($t.reads) { [math]::Round(100.0 * $t.reads_optout / $t.reads, 1) } else { 0 }
    $ok = if ($t.on) { ($t.apply_error -eq 0) -and ($t.last_read -match '^C=0x[0-9A-F]*[13579BDF] S=0x[0-9A-F]*[02468ACE]$') -and -not $t.reapply_fail } else { ($t.reads -gt 0) -and -not $t.set_calls }
    $o = [ordered]@{ tool = 'bench/agent11/pthrottle_sidecar.ps1'; run = $t.run; pid = $t.pid; arm = $(if ($t.on) { 'opt-out on' } else { 'opt-out off (read only)' })
        applied = [bool]$t.on; first_seen = $t.first_seen; first_seen_epoch_s = $t.first_seen_epoch_s; seen_after_start_s = $t.seen_after_start_s
        before = $t.before; after = $t.after; apply_error = $t.apply_error; last_read = $t.last_read; last_read_s = $t.last_read_s
        reads = $t.reads; reads_optout = $t.reads_optout; optout_held_pct = $held; reapplied = $t.reapplied; set_calls = $t.set_calls
        exited_s = $t.exited_s; exit_code = $t.exit_code; end = $why; transitions = @($t.transitions); errors = @($t.errors); ok = [bool]$ok }
    [IO.File]::WriteAllText((Join-Path $OutDir ($t.run + '.json')), ($o | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding $false))
    Log ("end   {0} pid {1} ({2}): before {3}, after {4}, last {5}, reads {6} ({7}% opted out), reapplied {8}, exit {9}, ok {10}" -f $t.run, $t.pid, $why, $t.before, $t.after, $t.last_read, $t.reads, $held, $t.reapplied, $t.exit_code, $ok)
}
Log "ready: runs dir $runsFull, process $ProcessName, opt-out arm $OnArm ($onRe), poll $PollMs ms, max $MaxMinutes min, pid $PID"
while ($true) {
    foreach ($p in @(Get-Process -Name $ProcessName -ErrorAction SilentlyContinue)) {
        $pr = [PtSidecar]::Probe($p.Id)
        if ($null -eq $pr) { continue }
        $parts = $pr.Split([char[]]@('|'), 2); $key = '{0}-{1}' -f $p.Id, $parts[0]; $path = $parts[1]
        if ($tracked.ContainsKey($key) -or $ignored.ContainsKey($key)) { continue }
        if (-not $path) { $retry[$key] = 1 + [int]$retry[$key]; if ($retry[$key] -ge 20) { $ignored[$key] = 1; Log "ignore pid $($p.Id): no image path after 20 tries" }; continue }
        if (-not $path.StartsWith($runsFull, [StringComparison]::OrdinalIgnoreCase)) { $ignored[$key] = 1; Log "ignore pid $($p.Id): not under the runs dir ($path)"; continue }
        $h = [PtSidecar]::OpenProcess([PtSidecar]::Access, $false, $p.Id)
        if ($h -eq [IntPtr]::Zero) { $ignored[$key] = 1; Log "ERROR pid $($p.Id): OpenProcess failed ($([Runtime.InteropServices.Marshal]::GetLastWin32Error()))"; continue }
        $run = Split-Path -Leaf (Split-Path -Parent $path)
        $t = @{ h = $h; pid = $p.Id; run = $run; on = ($run -match $onRe); t0 = (Get-Date); first_seen = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')
            first_seen_epoch_s = (Epoch); seen_after_start_s = $null; before = ''; after = ''; apply_error = 0; last_read = ''; last_read_s = 0
            reads = 0; reads_optout = 0; reapplied = 0; reapply_fail = 0; set_calls = 0; transitions = (New-Object System.Collections.ArrayList); errors = (New-Object System.Collections.ArrayList) }
        try { $t.seen_after_start_s = [math]::Round(((Get-Date) - $p.StartTime).TotalSeconds, 2) } catch { }
        $b = New-Object PowerThrottlingState; $a = New-Object PowerThrottlingState
        if ($t.on) {
            $t.apply_error = [PtSidecar]::OptOut($h, [ref]$b, [ref]$a); $t.set_calls++
            $t.before = [PtSidecar]::Str($b); $t.after = [PtSidecar]::Str($a)
        } else {
            $e = [PtSidecar]::Read($h, [ref]$b); if ($e) { [void]$t.errors.Add("read $e") }
            $t.before = [PtSidecar]::Str($b); $t.after = $t.before
        }
        $t.last_read = $t.after
        [void]$t.transitions.Add([ordered]@{ t_s = 0.0; state = $t.after; by = $(if ($t.on) { 'sidecar' } else { 'found' }) })
        $tracked[$key] = $t
        Log ("start {0} pid {1} (seen {2} s after its start): {3} -> {4} (apply result {5})" -f $run, $p.Id, $t.seen_after_start_s, $t.before, $t.after, $t.apply_error)
    }
    foreach ($key in @($tracked.Keys)) {
        $t = $tracked[$key]
        if ([PtSidecar]::Exited($t.h)) { Finish $t 'exited'; $tracked.Remove($key); continue }
        $s = New-Object PowerThrottlingState
        $e = [PtSidecar]::Read($t.h, [ref]$s)
        if ($e) { if ($t.errors.Count -lt 20) { [void]$t.errors.Add("read $e") }; continue }
        $ts = [math]::Round(((Get-Date) - $t.t0).TotalSeconds, 2)
        $str = [PtSidecar]::Str($s); $t.reads++; $t.last_read = $str; $t.last_read_s = $ts
        if ([PtSidecar]::IsOptedOut($s)) { $t.reads_optout++ }
        if ($str -ne $t.transitions[$t.transitions.Count - 1].state) { [void]$t.transitions.Add([ordered]@{ t_s = $ts; state = $str; by = 'other' }) }
        if ($t.on -and -not [PtSidecar]::IsOptedOut($s)) {
            $b = New-Object PowerThrottlingState; $a = New-Object PowerThrottlingState
            $r = [PtSidecar]::OptOut($t.h, [ref]$b, [ref]$a); $t.set_calls++; $t.reapplied++; if ($r -ne 0) { $t.reapply_fail++ }
            $t.last_read = [PtSidecar]::Str($a)
            [void]$t.transitions.Add([ordered]@{ t_s = $ts; state = $t.last_read; by = 'sidecar (re-applied)' })
            Log ("reapply {0}: {1} -> {2} (result {3})" -f $t.run, $str, $t.last_read, $r)
        }
    }
    if ($StopFile -and (Test-Path -LiteralPath $StopFile) -and $tracked.Count -eq 0) { Log 'stop file seen, nothing tracked: done'; break }
    if ((Get-Date) -gt $deadline) { foreach ($key in @($tracked.Keys)) { Finish $tracked[$key] 'sidecar_timeout' }; Log "max $MaxMinutes min reached: done"; break }
    Start-Sleep -Milliseconds $PollMs
}
exit 0
