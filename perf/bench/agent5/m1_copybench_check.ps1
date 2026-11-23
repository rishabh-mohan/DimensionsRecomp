# m1_copybench_check.ps1 (Agent 5, task #18) - the M1 correctness gate (Agent 10, b2r S33): one single-file
# build of bench\agent5\m1_copybench.cpp with the command in its header, then m1_copybench.exe --check-only.
# Functional only: the rate part never runs, so no GB/s is produced (the machine may be loaded).
# Runs at BelowNormal (clang++, link.exe and the exe inherit it), one process at a time, no project builds.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent5\m1_copybench_check.ps1 [-SkipBuild]
# Output: build\agent5\s4-m1\copybench-check-<stamp>.txt with the commands, the source and exe hashes, the build
# output, every line the check prints (one PASS/FAIL line per group of cases), its exit code and a RESULT line.
# Exit 0 = the build succeeded, the check exited 0, printed '# RESULT: PASS' and all 40 group lines say PASS
# (wb: 2 guards x (4 src misalignments + 7 large sizes); upload: 2 guards x (2 + 7)).
param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent5\s4-m1'
$report = Join-Path $stage ('copybench-check-{0:yyyyMMdd-HHmmss}.txt' -f (Get-Date))
$benchRel = 'bench\agent5\m1_copybench.cpp'
$exeRel = 'build\agent5\m1_copybench.exe'
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }
function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Invoke-Logged([string]$file, [string]$arguments) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $file; $psi.Arguments = $arguments; $psi.WorkingDirectory = $root
    $psi.UseShellExecute = $false; $psi.RedirectStandardError = $true; $psi.RedirectStandardOutput = $true
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = [Diagnostics.Process]::Start($psi)
    $e = $p.StandardError.ReadToEndAsync(); $o = $p.StandardOutput.ReadToEndAsync()
    $p.WaitForExit()
    $r = [pscustomobject]@{ Code = $p.ExitCode; Secs = $sw.Elapsed.TotalSeconds; Out = $o.Result; Err = $e.Result }
    $p.Dispose()
    return $r
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# m1_copybench_check (S4 M1 correctness gate, task #18)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("priority  $((Get-Process -Id $PID).PriorityClass) (inherited by clang++, link.exe and the exe)")
$lines.Add("bench     sha $(Sha (Join-Path $root $benchRel))  $benchRel")
$bad = 0

# 1. the build: the documented command, as is
if (-not $SkipBuild) {
    $clang = Join-Path $env:LEGO_LLVM 'bin\clang++.exe'
    $buildArgs = "-std=c++23 -O3 -march=x86-64-v2 -fno-strict-aliasing -fms-runtime-lib=dll $benchRel -o $exeRel"
    $b = Invoke-Logged $clang $buildArgs
    $text = ($b.Out + $b.Err)
    $nd = @($text -split "`r?`n" | Where-Object { $_ -match '(warning|error):' }).Count
    $lines.Add(('build     exit={0} {1,5:N1}s diagnostics={2}' -f $b.Code, $b.Secs, $nd))
    $lines.Add("          $clang $buildArgs")
    $text -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 40 | ForEach-Object { $lines.Add("    | $_") }
    if ($b.Code -ne 0) { $bad++ }
}

# 2. the check: part 1 only
$exe = Join-Path $root $exeRel
if (Test-Path -LiteralPath $exe) {
    $item = Get-Item -LiteralPath $exe
    $lines.Add(('exe       sha {0}  {1} B  {2}  (written {3:HH:mm:ss})' -f (Sha $exe), $item.Length, $exeRel, $item.LastWriteTime))
    $runArgs = '--check-only'
    $c = Invoke-Logged $exe $runArgs
    $lines.Add(('check     exit={0} {1,5:N1}s  {2} {3}' -f $c.Code, $c.Secs, $exeRel, $runArgs))
    ($c.Out + $c.Err) -split "`r?`n" | Where-Object { $_.Trim() } | ForEach-Object { $lines.Add("    | $_") }
    $out = @($c.Out -split "`r?`n")
    $result = @($out | Where-Object { $_ -match '^# RESULT: ' })
    $groups = @($out | Where-Object { $_ -match '^# check \S+ guard ' })
    $notPass = @($groups | Where-Object { $_ -notmatch ': PASS$' }).Count
    $lines.Add("groups    $($groups.Count) group lines (40 expected), $notPass not PASS")
    if ($c.Code -ne 0) { $bad++ }
    if ($result.Count -ne 1 -or $result[0] -notmatch '^# RESULT: PASS') { $bad++ }
    if ($groups.Count -ne 40 -or $notPass) { $bad++ }
    if (@($out | Where-Object { $_ -match '(GB/s|median_gbs)' }).Count) { $bad++; $lines.Add('rate      a rate line was printed (must not happen with --check-only)') }
} else {
    $bad++
    $lines.Add("exe       missing: $exeRel")
}
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
