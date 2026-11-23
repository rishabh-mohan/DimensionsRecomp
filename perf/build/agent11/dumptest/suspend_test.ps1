# Scratch test for testg_dump.ps1: start a hidden ping, suspend its main thread (as the runtime does
# to guest threads), dump it with TestGWin.MiniDump, kill it, then analyze. Harmless.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Add-Type -TypeDefinition ([IO.File]::ReadAllText("$root\bench\agent11\testg_win.cs")) -Language CSharp
Add-Type -Namespace TestGDumpTest -Name T -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr OpenThread(uint access, bool inherit, uint tid);
[DllImport("kernel32.dll", SetLastError = true)] public static extern uint SuspendThread(IntPtr h);
[DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
'@
$dmp = Join-Path $PSScriptRoot 'fresh\suspended.dmp'
$p = Start-Process -FilePath "$env:SystemRoot\System32\PING.EXE" -ArgumentList '-n 60 127.0.0.1' -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 3
$p.Refresh()
$tid = [uint32]$p.Threads[0].Id
$h = [TestGDumpTest.T]::OpenThread(0x0002, $false, $tid)
"suspend tid ${tid}: previous count " + [TestGDumpTest.T]::SuspendThread($h) + ", again: " + [TestGDumpTest.T]::SuspendThread($h)
"dump: " + [TestGWin]::MiniDump($p.Id, $dmp)
[void][TestGDumpTest.T]::CloseHandle($h)
$p.Kill(); [void]$p.WaitForExit(5000); "pid $($p.Id) exited: $($p.HasExited)"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'bench\agent11\testg_dump.ps1') -Dump $dmp | Select-String -Pattern '^=== SUMMARY' -Context 0,4 | ForEach-Object { $_.Line; $_.Context.PostContext }
