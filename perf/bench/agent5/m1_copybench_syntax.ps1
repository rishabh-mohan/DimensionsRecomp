# m1_copybench_syntax.ps1 (Agent 5) - syntax-only clang of bench\agent5\m1_copybench.cpp, the S4 M1 microbench
# (NOTE.md test plan step 2). Flags: the SDK's Release language flags (-std=c++23 -O3 -march=x86-64-v2 -fno-char8_t
# -Wall -Wextra -Wno-unused-variable -fno-strict-aliasing -ffp-model=strict) plus -DNOMINMAX -DWIN32_LEAN_AND_MEAN.
# Also checks that the lines between HELPER-BEGIN and HELPER-END are, byte for byte, CopyToUploadBufferNonTemporal
# from build\agent5\s4-m1\new\shared_memory.cpp (the staged M1 file, which must match HASHES key 'staged').
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent5\m1_copybench_syntax.ps1
# One compile, single-threaded, writes no objects. Output: build\agent5\s4-m1\copybench-syntax-<stamp>.txt.
# Exit 0 = the staged file matches HASHES, the helper text matches, and the compile exits 0 with no diagnostics.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$stage = Join-Path $root 'build\agent5\s4-m1'
$report = Join-Path $stage ("copybench-syntax-{0:yyyyMMdd-HHmmss}.txt" -f (Get-Date))
$bench = Join-Path $root 'bench\agent5\m1_copybench.cpp'
$m1 = Join-Path $stage 'new\shared_memory.cpp'
if (-not $env:LEGO_LLVM -or -not $env:INCLUDE) { . (Join-Path $root 'env\devshell.ps1') 6>$null | Out-Null }
$clang = Join-Path $env:LEGO_LLVM 'bin\clang++.exe'
function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# m1_copybench_syntax (S4 M1 microbench)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$bad = 0

# 1. the staged M1 file and the helper text
$staged = $null
foreach ($l in [IO.File]::ReadAllLines((Join-Path $stage 'HASHES.txt'))) {
    if ($l -match '^staged\s+([0-9A-F]{64})\b') { $staged = $Matches[1] }
}
$m1sha = Sha $m1
if ($m1sha -eq $staged) { $lines.Add("m1 file   sha $m1sha = HASHES staged  $m1") }
else { $bad++; $lines.Add("m1 file   sha $m1sha MISMATCH: HASHES staged is $staged  $m1") }
$m = [IO.File]::ReadAllLines($m1)
$b = [IO.File]::ReadAllLines($bench)
$i0 = [Array]::FindIndex($m, [Predicate[string]] { param($x) $x.StartsWith('void CopyToUploadBufferNonTemporal(') })
$i1 = -1
if ($i0 -ge 0) { for ($k = $i0; $k -lt $m.Count; $k++) { if ($m[$k] -eq '}') { $i1 = $k; break } } }
$j0 = [Array]::FindIndex($b, [Predicate[string]] { param($x) $x.StartsWith('// ---- HELPER-BEGIN') })
$j1 = [Array]::FindIndex($b, [Predicate[string]] { param($x) $x.StartsWith('// ---- HELPER-END') })
if ($i0 -lt 0 -or $i1 -lt 0 -or $j0 -lt 0 -or $j1 -le ($j0 + 1)) {
    $bad++; $lines.Add('helper    the function in new\shared_memory.cpp or the bench markers were not found')
} else {
    $want = $m[$i0..$i1] -join "`n"
    $got = $b[($j0 + 1)..($j1 - 1)] -join "`n"
    $where = "bench L$($j0 + 2)-L$j1 vs new\shared_memory.cpp L$($i0 + 1)-L$($i1 + 1), $($i1 - $i0 + 1) lines"
    if ($want -ceq $got) { $lines.Add("helper    MATCH ($where)") }
    else { $bad++; $lines.Add("helper    DIFFERS ($where)") }
}

# 2. the compile
$flags = '-fsyntax-only -std=c++23 -O3 -march=x86-64-v2 -fno-char8_t -Wall -Wextra -Wno-unused-variable ' +
         '-fno-strict-aliasing -ffp-model=strict -DNOMINMAX -DWIN32_LEAN_AND_MEAN'
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $clang; $psi.Arguments = "$flags `"$bench`""; $psi.WorkingDirectory = $root
$psi.UseShellExecute = $false; $psi.RedirectStandardError = $true; $psi.RedirectStandardOutput = $true
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = [Diagnostics.Process]::Start($psi)
$e = $p.StandardError.ReadToEndAsync(); $o = $p.StandardOutput.ReadToEndAsync()
$p.WaitForExit()
$code = $p.ExitCode; $secs = $sw.Elapsed.TotalSeconds
$diag = $o.Result + $e.Result
$p.Dispose()
$nd = @($diag -split "`r?`n" | Where-Object { $_ -match '(warning|error):' }).Count
$lines.Add(('compile   exit={0} {1,5:N1}s diagnostics={2}  bench sha {3}' -f $code, $secs, $nd, (Sha $bench)))
$lines.Add("          $clang $flags $bench")
if ($code -ne 0) { $bad++ }
if ($nd) { $bad++ }
if ($diag.Trim()) { $diag -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 60 | ForEach-Object { $lines.Add("    | $_") } }
$lines.Add($(if ($bad) { "RESULT: FAIL ($bad problem(s))" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath $report -Value $lines -Encoding ascii
$lines | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
