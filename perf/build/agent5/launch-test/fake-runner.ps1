# Agent 5: fake "runner" for run-night.ps1 -DryRun -FakeRunner tests (group 'run'). It starts no game and runs nothing
# from bench\agent8. It prints a line every second, writes one stderr line, and can start one hidden child powershell
# that only sleeps (its pid goes to <Dir>\fake-child.pid), so a test can check that the launcher kills the whole tree.
# Settings come from the environment (set by run-tests.ps1): A5_FAKE_SECONDS (default 3), A5_FAKE_CODE (default 0),
# A5_FAKE_CHILD (seconds the child sleeps; 0 = no child).
param([string]$Dir = '.')
$ErrorActionPreference = 'Stop'
function EnvInt([string]$N, [int]$D) { $v = [Environment]::GetEnvironmentVariable($N); if ($v -match '^\d+$') { return [int]$v }; return $D }
$sec = EnvInt 'A5_FAKE_SECONDS' 3; $code = EnvInt 'A5_FAKE_CODE' 0; $child = EnvInt 'A5_FAKE_CHILD' 0
"fake runner pid $PID starting (seconds $sec, exit $code, child $child s)"
[IO.File]::WriteAllText((Join-Path $Dir 'fake-runner.pid'), "$PID")
if ($child -gt 0) {
    $c = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList "-NoProfile -NonInteractive -Command Start-Sleep -Seconds $child" -WindowStyle Hidden -PassThru
    [IO.File]::WriteAllText((Join-Path $Dir 'fake-child.pid'), "$($c.Id)")
    "fake child pid $($c.Id)"
}
"out dir: $Dir\fake-out"
[Console]::Error.WriteLine('fake runner stderr line')
for ($i = 1; $i -le $sec; $i++) { "fake run tick $i"; Start-Sleep -Seconds 1 }
"fake runner done"
exit $code
