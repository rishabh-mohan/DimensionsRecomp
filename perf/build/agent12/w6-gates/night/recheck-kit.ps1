# recheck-kit.ps1 - Agent 12, task #24 (2026-11-23): after the G12 gap fix, re-run the kit's own checks one at a time
# at Below Normal: w6_env_record selftest, run_gates selftest, and the W5 and W4b fixtures (--expect).
# Read-only on build/agent8/matrix/** and build/agent1/**; writes the outputs next to the kit:
# out-envrec-selftest.txt, out-selftest.txt, out-w5.txt + gates-w5.json, out-w4b.txt + gates-w4b.json
# (stderr goes to night/err-<name>).
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\night\recheck-kit.ps1
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
Set-Location $repo
$k = 'build\agent12\w6-gates'
$py = (Get-Command python -ErrorAction Stop).Source
$env:PYTHONIOENCODING = 'utf-8'
$jobs = @(
    @{ n = 'out-envrec-selftest.txt'; a = @('-B', "$k\w6_env_record.py", '--selftest') },
    @{ n = 'out-selftest.txt'; a = @('-B', "$k\run_gates.py", '--selftest') },
    @{ n = 'out-w5.txt'; a = @('-B', "$k\run_gates.py", 'build\agent8\matrix\20261122-1756',
                               '--gate-log', 'build\agent1\w5\quiet-1731.log',
                               '--json', "$k\gates-w5.json", '--expect', "$k\fixture-w5.json") },
    @{ n = 'out-w4b.txt'; a = @('-B', "$k\run_gates.py", 'build\agent8\matrix\20261122-1541',
                                '--json', "$k\gates-w4b.json", '--expect', "$k\fixture-w4b.json") }
)
foreach ($j in $jobs) {
    if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { "HOLD EXISTS - stopping before $($j.n)"; break }
    $txt = Join-Path $k $j.n; $err = Join-Path $PSScriptRoot ("err-" + $j.n)
    $t0 = Get-Date
    $p = Start-Process -FilePath $py -ArgumentList $j.a -WorkingDirectory $repo -NoNewWindow -PassThru `
        -RedirectStandardOutput $txt -RedirectStandardError $err
    $null = $p.Handle   # cache the handle now, or ExitCode can come back empty
    try { $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal } catch { }
    $p.WaitForExit()
    "{0} {1}: exit {2} ({3:N0} s)" -f (Get-Date -Format HH:mm:ss), $j.n, $p.ExitCode, ((Get-Date) - $t0).TotalSeconds
    Select-String -Path $txt -Pattern '^(GATES|RECORD|EXPECT|SELFTEST)|^FAIL' | ForEach-Object { '  ' + $_.Line }
    if ((Get-Item $err).Length -gt 0) { '  stderr: ' + ((Get-Content $err -TotalCount 3) -join ' | ') }
}
