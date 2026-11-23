# Agent 5: test helper for run-tests.ps1 -Group run (t-run-ctrlc). Sends Ctrl+C to the console of process -TargetPid (the
# launcher under test, which runs in its own hidden console) and to nothing else. It leaves its own console first,
# attaches to the target's console, and refuses (exit 13) if that is the console window it came from or if no window can
# be seen, so the Ctrl+C never reaches the tests' console or any other. It ignores the Ctrl+C itself.
# Exit: 0 sent, 11 attach failed, 12 send failed, 13 refused (same or unknown console), 14 setup failed.
param([Parameter(Mandatory = $true)][int]$TargetPid)
$ErrorActionPreference = 'Stop'
try {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class A5CtrlC {
    [DllImport("kernel32.dll", SetLastError = true)] public static extern bool FreeConsole();
    [DllImport("kernel32.dll", SetLastError = true)] public static extern bool AttachConsole(uint pid);
    [DllImport("kernel32.dll", SetLastError = true)] public static extern bool SetConsoleCtrlHandler(IntPtr handler, bool add);
    [DllImport("kernel32.dll", SetLastError = true)] public static extern bool GenerateConsoleCtrlEvent(uint ctrlEvent, uint processGroupId);
    [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
}
'@
} catch { "setup failed: $($_.Exception.Message)"; exit 14 }
$before = [A5CtrlC]::GetConsoleWindow()
"own console window $before; target pid $TargetPid"
[void][A5CtrlC]::FreeConsole()
if (-not [A5CtrlC]::AttachConsole([uint32]$TargetPid)) { $e = [Runtime.InteropServices.Marshal]::GetLastWin32Error(); "attach to the console of pid $TargetPid failed: error $e"; exit 11 }
$after = [A5CtrlC]::GetConsoleWindow()
"target console window $after"
if ($after -eq [IntPtr]::Zero -or $after -eq $before) {
    [void][A5CtrlC]::FreeConsole()
    "refused: the target console window is $(if ($after -eq [IntPtr]::Zero) { 'unknown' } else { 'the one this helper came from' }); nothing sent"
    exit 13
}
[void][A5CtrlC]::SetConsoleCtrlHandler([IntPtr]::Zero, $true)     # this process ignores the Ctrl+C it sends
$ok = [A5CtrlC]::GenerateConsoleCtrlEvent(0, 0)                    # 0 = CTRL_C_EVENT, to every process in that console
$e = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
Start-Sleep -Milliseconds 500
[void][A5CtrlC]::FreeConsole()
if (-not $ok) { "GenerateConsoleCtrlEvent failed: error $e"; exit 12 }
"Ctrl+C sent to the console of pid $TargetPid"
exit 0
