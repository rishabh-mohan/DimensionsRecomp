# pthrottle_runner_probe.ps1 - S4 task #19, part 2 (the runner proposal): checks the C# helper
# proposed for Agent 8's runner (Add-Type in Windows PowerShell 5.1) on a child process this
# script starts itself (PING.EXE, hidden; no game). It mirrors run-timing.ps1: Start-Process
# -PassThru, then $p.Handle. Steps:
#   1. read the child's state (C=0x0 S=0x0 expected: nothing set);
#   2. set C=0x4 S=0x0, as the game's own call does with host_timer_throttling_optout=true;
#   3. the proposed read-modify-write opt-out through $p.Handle: expect C=0x5 S=0x0 (the
#      game's timer bit is kept);
#   4. the same through an OpenProcess(PROCESS_SET_INFORMATION |
#      PROCESS_QUERY_LIMITED_INFORMATION) handle: no change (idempotent);
#   5. preset C=0x1 S=0x1 (an EcoQoS opt-in), then the opt-out: C=0x1 S=0x0;
#   6. a plain Set of C=0x1 on C=0x4 replaces it (why the runner must read first);
# then stops the child. Single-threaded; nothing in bench\agent8 is read or written.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_runner_probe.ps1
# Output: build\agent11\pthrottle\runner-probe-<stamp>.txt. Exit 0 = every step as expected.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$report = Join-Path $root ('build\agent11\pthrottle\runner-probe-{0:yyyyMMdd-HHmmss}.txt' -f (Get-Date))
$csharp = @'
using System;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential)]
public struct PowerThrottlingState { public uint Version, ControlMask, StateMask; }

public static class PowerThrottle {
  const int ProcessPowerThrottling = 4;           // PROCESS_INFORMATION_CLASS
  public const uint ExecutionSpeed = 0x1;         // PROCESS_POWER_THROTTLING_EXECUTION_SPEED
  public const uint IgnoreTimerResolution = 0x4;  // PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION
  public const uint ProcessSetInformation = 0x0200, ProcessQueryLimitedInformation = 0x1000;
  [DllImport("kernel32.dll", SetLastError = true)]
  static extern bool GetProcessInformation(IntPtr process, int infoClass, ref PowerThrottlingState info, int size);
  [DllImport("kernel32.dll", SetLastError = true)]
  static extern bool SetProcessInformation(IntPtr process, int infoClass, ref PowerThrottlingState info, int size);
  [DllImport("kernel32.dll", SetLastError = true)]
  public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
  [DllImport("kernel32.dll", SetLastError = true)]
  public static extern bool CloseHandle(IntPtr handle);

  // Version must be set before the call, also for a read. Returns 0 or the Win32 error.
  public static int Read(IntPtr process, out PowerThrottlingState state) {
    state = new PowerThrottlingState();
    state.Version = 1;
    return GetProcessInformation(process, ProcessPowerThrottling, ref state,
        Marshal.SizeOf(typeof(PowerThrottlingState))) ? 0 : Marshal.GetLastWin32Error();
  }
  public static int Write(IntPtr process, uint controlMask, uint stateMask) {
    PowerThrottlingState s = new PowerThrottlingState();
    s.Version = 1; s.ControlMask = controlMask; s.StateMask = stateMask;
    return SetProcessInformation(process, ProcessPowerThrottling, ref s,
        Marshal.SizeOf(typeof(PowerThrottlingState))) ? 0 : Marshal.GetLastWin32Error();
  }
  // The runner's step. Each Set replaces the whole state, so: read, add EXECUTION_SPEED to
  // ControlMask and clear it in StateMask (controlled and off), keep every other bit, write,
  // read back. Returns 0 when the read-back shows the opt-out, else the Win32 error or -1.
  public static int OptOutExecutionSpeed(IntPtr process, out PowerThrottlingState before,
                                         out PowerThrottlingState after) {
    after = new PowerThrottlingState();
    int e = Read(process, out before);
    if (e != 0) return e;
    e = Write(process, before.ControlMask | ExecutionSpeed, before.StateMask & ~ExecutionSpeed);
    if (e != 0) return e;
    e = Read(process, out after);
    if (e != 0) return e;
    return ((after.ControlMask & ExecutionSpeed) != 0 && (after.StateMask & ExecutionSpeed) == 0) ? 0 : -1;
  }
  public static string Str(PowerThrottlingState s) {
    return string.Format("C=0x{0:X} S=0x{1:X}", s.ControlMask, s.StateMask);
  }
}
'@
$log = New-Object System.Collections.Generic.List[string]
function Say([string]$s) { $log.Add($s); Write-Host $s }
$script:bad = 0
function Expect([bool]$ok, [string]$what) {
  if ($ok) { Say "PASS  $what" } else { Say "FAIL  $what"; $script:bad++ }
}
Add-Type -TypeDefinition $csharp -Language CSharp
Say "# pthrottle_runner_probe (S4 task #19, the runner proposal)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  PowerShell $($PSVersionTable.PSVersion), CLR $($PSVersionTable.CLRVersion)"
$ping = Join-Path $env:SystemRoot 'System32\PING.EXE'
$p = Start-Process -FilePath $ping -ArgumentList '-n 30 127.0.0.1' -WindowStyle Hidden -PassThru
$null = $p.Handle
try {
  $h = $p.Handle
  Say "child: PING.EXE pid $($p.Id) (Start-Process -PassThru, `$p.Handle as in run-timing.ps1)"
  $s0 = New-Object PowerThrottlingState
  $e = [PowerThrottle]::Read($h, [ref]$s0)
  Expect (($e -eq 0) -and $s0.ControlMask -eq 0 -and $s0.StateMask -eq 0) "1. the child starts with $([PowerThrottle]::Str($s0)) (read error $e)"

  $e = [PowerThrottle]::Write($h, [PowerThrottle]::IgnoreTimerResolution, 0)
  $s1 = New-Object PowerThrottlingState
  $null = [PowerThrottle]::Read($h, [ref]$s1)
  Expect (($e -eq 0) -and $s1.ControlMask -eq 4 -and $s1.StateMask -eq 0) "2. the game's call (C=0x4 S=0x0) reads back $([PowerThrottle]::Str($s1)) (error $e)"

  $b = New-Object PowerThrottlingState; $a = New-Object PowerThrottlingState
  $e = [PowerThrottle]::OptOutExecutionSpeed($h, [ref]$b, [ref]$a)
  Expect (($e -eq 0) -and $b.ControlMask -eq 4 -and $a.ControlMask -eq 5 -and $a.StateMask -eq 0) "3. opt-out via `$p.Handle: $([PowerThrottle]::Str($b)) -> $([PowerThrottle]::Str($a)) (result $e; the timer bit is kept)"

  $lim = [PowerThrottle]::OpenProcess(([PowerThrottle]::ProcessSetInformation -bor [PowerThrottle]::ProcessQueryLimitedInformation), $false, $p.Id)
  if ($lim -eq [IntPtr]::Zero) {
    Expect $false "4. OpenProcess(SET_INFORMATION | QUERY_LIMITED_INFORMATION) failed ($([Runtime.InteropServices.Marshal]::GetLastWin32Error()))"
  } else {
    $e = [PowerThrottle]::OptOutExecutionSpeed($lim, [ref]$b, [ref]$a)
    $null = [PowerThrottle]::CloseHandle($lim)
    Expect (($e -eq 0) -and $b.ControlMask -eq 5 -and $a.ControlMask -eq 5 -and $a.StateMask -eq 0) "4. again via an OpenProcess(SET_INFORMATION | QUERY_LIMITED_INFORMATION) handle: $([PowerThrottle]::Str($b)) -> $([PowerThrottle]::Str($a)) (result $e; idempotent)"
  }

  $null = [PowerThrottle]::Write($h, [PowerThrottle]::ExecutionSpeed, [PowerThrottle]::ExecutionSpeed)
  $e = [PowerThrottle]::OptOutExecutionSpeed($h, [ref]$b, [ref]$a)
  Expect (($e -eq 0) -and $b.ControlMask -eq 1 -and $b.StateMask -eq 1 -and $a.ControlMask -eq 1 -and $a.StateMask -eq 0) "5. an EcoQoS opt-in $([PowerThrottle]::Str($b)) -> $([PowerThrottle]::Str($a)) (result $e)"

  $null = [PowerThrottle]::Write($h, [PowerThrottle]::IgnoreTimerResolution, 0)
  $e = [PowerThrottle]::Write($h, [PowerThrottle]::ExecutionSpeed, 0)
  $null = [PowerThrottle]::Read($h, [ref]$a)
  Expect (($e -eq 0) -and $a.ControlMask -eq 1 -and $a.StateMask -eq 0) "6. a plain Set of C=0x1 on C=0x4 reads back $([PowerThrottle]::Str($a)): replaced, so the runner must read first"
} finally {
  if (-not $p.HasExited) { $p.Kill(); $null = $p.WaitForExit(5000) }
  Say "child stopped (exited: $($p.HasExited))"
}
Say $(if ($script:bad) { "RESULT: FAIL ($($script:bad))" } else { 'RESULT: PASS' })
Set-Content -LiteralPath $report -Value $log -Encoding ascii
Write-Host "report: $report"
if ($script:bad) { exit 1 }
exit 0
