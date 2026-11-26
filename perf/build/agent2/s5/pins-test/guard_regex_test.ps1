# guard_regex_test.ps1 (M2): static test of the D1 v2 timed-window guard predicate in nops-smoke-run.ps1 (no processes).
# The names are built by concatenation so no command line ever carries them.
param([string]$KitPs1 = 'nops-smoke-run.ps1')   # kit ps1 (in ..\) whose predicate text is checked; also rt-smoke-run.ps1
$w = 'window' + '-s5'; $m = 'run' + '-matrix'; $c = 'RUN-WINDOW' + '-S5'
function Hit($name, $cl) {
    $name -match '^(?i)(powershell|pwsh|cmd)\.exe$' -and (
        $cl -match '(?i)-File\s+"?[^"]*(window-s5|run-matrix)\.ps1' -or
        ($name -ieq 'cmd.exe' -and $cl -match '(?i)RUN-WINDOW-S5[^\s"]*\.cmd'))
}
$cases = @(
    @('powershell.exe', "powershell -NoProfile -ExecutionPolicy Bypass -File `"C:\ws\build\agent8\s5\$w.ps1`" -Go", $true),
    @('pwsh.exe', "pwsh -File C:\ws\harness\$m.ps1 -Arms a,b", $true),
    @('cmd.exe', "C:\WINDOWS\system32\cmd.exe /c `"`"C:\ws\build\agent8\s5\$c-go.cmd`" `"", $true),
    @('powershell.exe', "powershell -Command Select-String -Path C:\ws\build\agent8\s5\$w.ps1 -Pattern x", $false),
    @('powershell.exe', "powershell -Command git grep $c C:\ws\build\agent8\s5\$c.cmd", $false),
    @('python.exe', "python -File C:\ws\harness\$m.ps1", $false),
    @('Code.exe', "Code.exe C:\ws\build\agent8\s5\$w.ps1", $false),
    @('cmd.exe', "cmd /c findstr /s foo C:\ws\harness\$m.ps1", $false),
    @('powershell.exe', "powershell -File C:\ws\build\agent2\s5\nops-smoke-run.ps1 dryrun", $false),
    @('powershell.exe', "powershell -NoProfile -ExecutionPolicy Bypass -File `"C:\ws\build\agent2\s5\rt-smoke-run.ps1`" dryrun", $false)
)
$bad = 0
foreach ($k in $cases) {
    $got = [bool](Hit $k[0] $k[1])
    $ok = $got -eq $k[2]
    if (-not $ok) { $bad++ }
    '{0} want={1} got={2} {3}: {4}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $k[2], $got, $k[0], ($k[1] -replace [regex]::Escape($w), '<W>' -replace [regex]::Escape($m), '<M>' -replace [regex]::Escape($c), '<C>')
}
# the predicate in the kit must be the same text as Hit's
$kit = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot "..\$KitPs1")
foreach ($frag in @('''(?i)-File\s+"?[^"]*(window-s5|run-matrix)\.ps1''', '''(?i)RUN-WINDOW-S5[^\s"]*\.cmd''', '''^(?i)(powershell|pwsh|cmd)\.exe$''', '$_.Name -ieq ''cmd.exe''')) {
    if ($kit.Contains($frag)) { "PASS kit has $($frag -replace 'window-s5','<W>' -replace 'run-matrix','<M>' -replace 'RUN-WINDOW-S5','<C>')" } else { $bad++; "FAIL kit lacks a predicate fragment" }
}
if ($bad) { "GUARD REGEX TEST FAIL ($bad)"; exit 1 } else { 'GUARD REGEX TEST ALL PASS'; exit 0 }
