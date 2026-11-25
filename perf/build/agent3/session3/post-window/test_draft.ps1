# test_draft.ps1 - M3 post-window: dry-runs the draft s4b_check.py (this folder) on existing runs, at Below Normal,
# one process at a time. Read-only on run dirs; outputs to $env:TEMP\m3pw\<name>.txt. Run from the repo root.
$ErrorActionPreference = 'Continue'
$out = Join-Path $env:TEMP 'm3pw'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$env:PYTHONPATH = (Resolve-Path 'build\agent3\s4a').Path
$R = 'build\agent3\runs'
$L0 = "$R\20261122-210059-s4b-L0-off-level"
$tests = @(
    @('v0f-on-V0run', 's4bV0f', "$R\20261125-021419-s4b-V0-c1off-verify-level", $L0, 'C1 keep-watch|C1 verify'),
    @('07f-on-07rrun', 's4b07f', "$R\20261125-020440-s4b-07r-c1v-level", $L0, 'C1 keep-watch|C1 verify'),
    @('s33base-on-s4b03', 's33base', "$R\20261122-215230-w6-side3-p2fc-attract", "$R\20261122-140637-s4a-udiag-attract", ''),
    @('V0-unchanged', 's4bV0', "$R\20261125-021419-s4b-V0-c1off-verify-level", $L0, 'C1 keep-watch|C1 verify')
)
foreach ($t in $tests) {
    $a = @('-B', 'build\agent3\session3\post-window\s4b_check.py', '--row', $t[1], '--cand', $t[2], '--base', $t[3],
           '--out-dir', (Join-Path $out 'checks'))
    if ($t[4]) { $a += @('--allow-new', ('"' + $t[4] + '"')) }
    $f = Join-Path $out ($t[0] + '.txt')
    $p = Start-Process python -ArgumentList $a -NoNewWindow -PassThru -RedirectStandardOutput $f -RedirectStandardError ($f + '.err')
    try { $p.PriorityClass = 'BelowNormal' } catch { }
    $p.WaitForExit()
    "== $($t[0]) exit $($p.ExitCode)"
    Get-Content $f | Select-String 'PROOF|VERDICT' | ForEach-Object { $_.Line }
    Get-Content ($f + '.err') -Tail 5
}
