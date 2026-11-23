# Scratch helper for the testg_dump.ps1 test: names its own thread, then sleeps (dumped and killed by
# the caller). Harmless.
Add-Type -Namespace TestGDumpTest -Name K -MemberDefinition @'
[DllImport("kernel32.dll", CharSet = CharSet.Unicode)] public static extern int SetThreadDescription(IntPtr h, string d);
[DllImport("kernel32.dll")] public static extern IntPtr GetCurrentThread();
'@
[void][TestGDumpTest.K]::SetThreadDescription([TestGDumpTest.K]::GetCurrentThread(), 'testg-named-thread')
Start-Sleep -Seconds 60
