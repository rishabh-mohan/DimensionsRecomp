# S3T-12 item 3 (N6) test: baseline (w6-gates) vs patched copy (w6-gates-n6), one at a time, Below Normal.
# Outputs only into build/agent12/session3/n6/ (--json too). Read-only on build/agent8/matrix and build/agent1.
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
Set-Location $repo
$out = 'build\agent12\session3\n6'
$py = (Get-Command python -ErrorAction Stop).Source
$env:PYTHONIOENCODING = 'utf-8'
$jobs = @()
foreach ($k in @('w6-gates', 'w6-gates-n6')) {
    $kd = "build\agent12\$k"
    $jobs += @{ n = "$k-selftest.txt"; a = @('-B', "$kd\run_gates.py", '--selftest') }
    $jobs += @{ n = "$k-w5.txt"; a = @('-B', "$kd\run_gates.py", 'build\agent8\matrix\20261122-1756',
                                       '--gate-log', 'build\agent1\w5\quiet-1731.log',
                                       '--json', "$out\$k-gates-w5.json", '--expect', "$kd\fixture-w5.json") }
    $jobs += @{ n = "$k-w4b.txt"; a = @('-B', "$kd\run_gates.py", 'build\agent8\matrix\20261122-1541',
                                        '--json', "$out\$k-gates-w4b.json", '--expect', "$kd\fixture-w4b.json") }
}
foreach ($j in $jobs) {
    if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { "HOLD EXISTS - stopping before $($j.n)"; break }
    $txt = Join-Path $out $j.n; $err = Join-Path $out ("err-" + $j.n)
    $p = Start-Process -FilePath $py -ArgumentList $j.a -WorkingDirectory $repo -NoNewWindow -PassThru `
        -RedirectStandardOutput $txt -RedirectStandardError $err
    $null = $p.Handle
    try { $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal } catch { }
    $p.WaitForExit()
    "{0}: exit {1}" -f $j.n, $p.ExitCode
    Select-String -Path $txt -Pattern '^(GATES|RECORD|EXPECT|SELFTEST)|^FAIL|launcher window log' | ForEach-Object { '  ' + $_.Line }
    if ((Get-Item $err).Length -gt 0) { '  stderr: ' + ((Get-Content $err -TotalCount 3) -join ' | ') }
}
