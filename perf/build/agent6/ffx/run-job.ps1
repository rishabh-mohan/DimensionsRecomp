# Agent 6 / subagent B helper: run a command inside a Win32 job object and report wall time and CPU
# time (user and kernel, summed over every process the command spawned), plus the process count.
# The current PowerShell process joins a fresh (nested) job before the command starts, so every
# descendant (cmake, ninja, cmd, FidelityFX_SC, clang++, llvm-ar, ...) is accounted for with no race.
# Usage (after `. .\env\devshell.ps1 -Jobs 1`):
#   & build\agent6\ffx\run-job.ps1 -LogFile <log> -Exe cmake -ArgLine "--build <dir> -j 1 --target <t>"
param(
  [Parameter(Mandatory = $true)][string]$LogFile,
  [Parameter(Mandatory = $true)][string]$Exe,
  [string]$ArgLine = ''
)
$ErrorActionPreference = 'Stop'
if (-not ('AgentB.JobAcct' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace AgentB {
public static class JobAcct {
  [StructLayout(LayoutKind.Sequential)]
  public struct BasicAccounting {
    public long TotalUserTime; public long TotalKernelTime;
    public long ThisPeriodTotalUserTime; public long ThisPeriodTotalKernelTime;
    public uint TotalPageFaultCount; public uint TotalProcesses;
    public uint ActiveProcesses; public uint TotalTerminatedProcesses;
  }
  [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
  public static extern IntPtr CreateJobObjectW(IntPtr attrs, string name);
  [DllImport("kernel32.dll", SetLastError = true)]
  public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
  [DllImport("kernel32.dll", SetLastError = true)]
  public static extern bool QueryInformationJobObject(IntPtr job, int infoClass, out BasicAccounting info, int length, IntPtr returnLength);
  public static BasicAccounting Query(IntPtr job) {
    BasicAccounting a;
    if (!QueryInformationJobObject(job, 1, out a, Marshal.SizeOf(typeof(BasicAccounting)), IntPtr.Zero))
      throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
    return a;
  }
}
}
'@
}
$job = [AgentB.JobAcct]::CreateJobObjectW([IntPtr]::Zero, $null)
if ($job -eq [IntPtr]::Zero) { throw "CreateJobObject failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())" }
$self = [System.Diagnostics.Process]::GetCurrentProcess()
if (-not [AgentB.JobAcct]::AssignProcessToJobObject($job, $self.Handle)) {
  throw "AssignProcessToJobObject(self) failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
}
$a0 = [AgentB.JobAcct]::Query($job)
$start = Get-Date
"[run-job] start $($start.ToString('yyyy-MM-ddTHH:mm:ss')) : $Exe $ArgLine" | Out-File -FilePath $LogFile -Encoding utf8
$sw = [Diagnostics.Stopwatch]::StartNew()
cmd.exe /d /c "$Exe $ArgLine >> `"$LogFile`" 2>&1"
$rc = $LASTEXITCODE
$sw.Stop()
$a1 = [AgentB.JobAcct]::Query($job)
$user = ($a1.TotalUserTime - $a0.TotalUserTime) / 1e7
$kern = ($a1.TotalKernelTime - $a0.TotalKernelTime) / 1e7
$wall = $sw.Elapsed.TotalSeconds
$cpu = $user + $kern
$summary = "[run-job] end $((Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')) rc=$rc wall={0:N1}s cpu_user={1:N1}s cpu_kernel={2:N1}s cpu_total={3:N1}s avg_cores={4:N2} processes={5}" -f $wall, $user, $kern, $cpu, ($cpu / [Math]::Max($wall, 0.001)), ($a1.TotalProcesses - $a0.TotalProcesses)
$summary | Out-File -FilePath $LogFile -Append -Encoding utf8
$summary
exit $rc
