# Agent 2 - compile-one -SyntaxOnly sweep over every rexlego/src TU in a compile DB (default build/dev).
# Validates exactly what other agents run. Results: build/agent2/c1-sweep/summary.txt (+ per-TU logs).
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\dev-c1-sweep.ps1 [-Jobs 6] [-Db <json>]
param([int]$Jobs = 6, [string]$Db = '<workspace>\build\dev\compile_commands.json')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
$out = "$R\build\agent2\c1-sweep"
New-Item -ItemType Directory -Force $out | Out-Null
$ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.Web.Extensions
$ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$ser.MaxJsonLength = [int]::MaxValue
$entries = $ser.DeserializeObject([IO.File]::ReadAllText($Db))
$srcs = @($entries | ForEach-Object { [string]$_['file'] } | Where-Object { $_ -match '[\\/]rexlego[\\/]src[\\/].+\.(cpp|cc|cxx)$' } | Sort-Object -Unique)
$sw = [Diagnostics.Stopwatch]::StartNew()
$queue = New-Object System.Collections.Queue; $srcs | ForEach-Object { $queue.Enqueue($_) }
$running = @(); $results = New-Object System.Collections.Generic.List[string]
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
    while ($queue.Count -gt 0 -and $running.Count -lt $Jobs) {
        $s = $queue.Dequeue()
        $rel = ($s -replace '/', '\')
        $name = ($rel -replace '^.*[\\/]rexlego[\\/]src[\\/]', '') -replace '[\\/]', '__'
        $p = Start-Process -FilePath powershell -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput "$out\$name.log" -RedirectStandardError "$out\$name.err" `
            -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$R\env\compile-one.ps1`"", "`"$rel`"",
                            '-OutDir', "`"$R\build\agent2\obj-dev`"", '-Db', "`"$Db`"", '-SyntaxOnly')
        $null = $p.Handle   # cache the handle, or ExitCode is null after exit (PS 5.1)
        $running += [pscustomobject]@{ P = $p; Name = $name; T = [Diagnostics.Stopwatch]::StartNew() }
    }
    Start-Sleep -Milliseconds 500
    $still = @()
    foreach ($job in $running) {   # NOT $r: PowerShell names are case-insensitive ($r is $R)
        if ($job.P.HasExited) {
            $job.P.WaitForExit(); $code = $job.P.ExitCode
            $first = ''
            if ($code -ne 0) {
                $first = (Get-Content "$out\$($job.Name).log", "$out\$($job.Name).err" -ErrorAction SilentlyContinue |
                    Select-String -Pattern 'error' | Select-Object -First 1).Line
            }
            $results.Add(("{0}`texit={1}`t{2:N1}s`t{3}" -f $job.Name, $code, $job.T.Elapsed.TotalSeconds, $first))
        } else { $still += $job }
    }
    $running = $still
}
$bad = @($results | Where-Object { $_ -notmatch "`texit=0`t" })
$hdr = "# compile-one -SyntaxOnly sweep, DB=$Db, $($srcs.Count) TUs, jobs=$Jobs, wall={0:N1}s, failures=$($bad.Count), $(Get-Date -Format HH:mm:ss)" -f $sw.Elapsed.TotalSeconds
@($hdr) + ($results | Sort-Object) | Out-File -Encoding utf8 "$out\summary.txt"
$hdr
$bad
exit $bad.Count
