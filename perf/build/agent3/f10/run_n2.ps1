# run_n2.ps1 - Agent 3, task #23: the f10 tables for n = 2 per set (f10a, f10a2, f10b, f10b2 + last night's loaded runs).
# Each script runs at BelowNormal; outputs go to build\agent3\f10\ (the n = 1 outputs are kept as *.n1.*).
# Usage (repo root): powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\f10\run_n2.ps1
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
Set-Location (Resolve-Path (Join-Path $here '..\..\..')).Path
$R = 'build\agent3\runs'
$runs = [ordered]@{
    f10a  = "$R\20261123-055810-f10a-m1-sfl-level";   f10a2 = "$R\20261123-063244-f10a2-m1-sfl-level"
    f10b  = "$R\20261123-060847-f10b-p2fc-level";     f10b2 = "$R\20261123-064014-f10b2-p2fc-level"
    gateB = "$R\20261122-222313-w6-gateB-p2fc-level"; gateA = "$R\20261122-210906-w6-gateA-p2fcv-level"
    s4b20 = "$R\20261122-221447-s4b-20-m1-level";     s4b24 = "$R\20261122-220520-s4b-24-w6-c1"
    w6s3  = "$R\20261122-215230-w6-side3-p2fc-attract"; s4b23 = "$R\20261122-213421-s4b-23-w6-p2fi-level"
}
function L([string[]]$names) { @($names | ForEach-Object { "$_=$($runs[$_])" }) }
function Run([string]$name, [string[]]$a) {
    $out = Join-Path $here "$name.out.txt"; $err = Join-Path $here "$name.err.txt"
    $p = Start-Process -FilePath python -ArgumentList (@('-B') + $a) -NoNewWindow -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    $null = $p.Handle; try { $p.PriorityClass = 'BelowNormal' } catch { }
    $p.WaitForExit()
    "$name exit $($p.ExitCode) ($((Get-Item $out).Length) B out, $((Get-Item $err).Length) B err)"
}
foreach ($f in 'f10-table.md', 'f10.json', 'f10.out.txt', 'sync.out.txt', 'align.out.txt', 'cine.out.txt') {
    $s = Join-Path $here $f; $d = $s -replace '\.(md|json|txt)$', '.n1.$1'
    if ((Test-Path $s) -and -not (Test-Path $d)) { Copy-Item $s $d }
}
Run 'f10' (@("$here\f10_results.py", '--json', "$here\f10.json", '--md', "$here\f10-table.md") + (L 'f10a', 'f10a2', 'f10b', 'f10b2', 'gateB', 'gateA', 's4b20', 's4b24', 'w6s3', 's4b23'))
Run 'sync' (@("$here\sync_profile.py") + (L 'f10a', 'f10a2', 'f10b', 'f10b2', 'gateB', 'gateA', 's4b23'))
Run 'align' (@("$here\align.py", '--min-ms', '700') + (L 's4b20', 'f10a', 'f10a2', 's4b24', 'gateB', 'f10b', 'f10b2'))
Run 'cine' (@("$here\cine.py") + (L 'f10a', 'f10a2', 's4b20', 'f10b', 'f10b2', 'gateB'))
