# run-night-gates.ps1 - Agent 12, task #24 (2026-11-23): run_gates.py on the 7 night matrix dirs, one at a time.
# Read-only on build/agent8/matrix/** and build/agent3/runs/**; writes only out-*.txt, err-*.txt and gates-*.json here.
# python runs at Below Normal, one process at a time; stops before the next window if perf-notes/WINDOW-HOLD.txt exists.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\night\run-night-gates.ps1 [<dir id> ...]
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
Set-Location $repo
$here = $PSScriptRoot
$kit = 'build\agent12\w6-gates\run_gates.py'
$h = (Get-FileHash $kit -Algorithm SHA256).Hash
"run_gates.py SHA-256 $h; in HASHES.txt: " + [bool](Select-String -Path 'build\agent12\w6-gates\HASHES.txt' -Pattern $h -SimpleMatch -Quiet)
# W6's G4/G5 inputs: Agent 3's side runs and gate A from 2026-11-22 (G4 PASS 4/4 at 22:04).
$sides = @('--side', 'build\agent3\runs\20261122-212406-w6-side1-p2f',
           '--side', 'build\agent3\runs\20261122-211914-w6-side2-p2fc',
           '--side', 'build\agent3\runs\20261122-215230-w6-side3-p2fc-attract',
           '--gate-a', 'build\agent3\runs\20261122-210906-w6-gateA-p2fcv-level')
$jobs = @(
    @{ w = 'W6';  d = '20261123-0009'; a = @('--one-bin') + $sides },
    @{ w = 'W9';  d = '20261123-0108'; a = @('--one-bin') },
    @{ w = 'W5b'; d = '20261123-0155'; a = @('--one-bin') },
    @{ w = 'W4c'; d = '20261123-0239'; a = @() },            # compares two bins: no --one-bin
    @{ w = 'W6';  d = '20261123-0313'; a = @('--one-bin') + $sides },
    @{ w = 'W9';  d = '20261123-0401'; a = @('--one-bin') },
    @{ w = 'W5b'; d = '20261123-0451'; a = @('--one-bin') }
)
if ($args.Count) { $jobs = @($jobs | Where-Object { $args -contains $_.d }) }
$py = (Get-Command python -ErrorAction Stop).Source
$env:PYTHONIOENCODING = 'utf-8'
foreach ($j in $jobs) {
    if (Test-Path 'perf-notes\WINDOW-HOLD.txt') { "HOLD EXISTS - stopping before $($j.d)"; break }
    $tag = "$($j.w)-$($j.d)"
    $txt = Join-Path $here "out-$tag.txt"; $err = Join-Path $here "err-$tag.txt"; $json = Join-Path $here "gates-$tag.json"
    $argv = @('-B', $kit, "build\agent8\matrix\$($j.d)") + $j.a + @('--json', $json)
    $t0 = Get-Date
    $p = Start-Process -FilePath $py -ArgumentList $argv -WorkingDirectory $repo -NoNewWindow -PassThru `
        -RedirectStandardOutput $txt -RedirectStandardError $err
    $null = $p.Handle   # cache the handle now, or ExitCode can come back empty
    try { $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal } catch { }
    $p.WaitForExit()
    "{0} {1}: exit {2} ({3:N0} s)" -f (Get-Date -Format HH:mm:ss), $tag, $p.ExitCode, ((Get-Date) - $t0).TotalSeconds
    Select-String -Path $txt -Pattern '^(GATES|RECORD):' | ForEach-Object { '  ' + $_.Line }
    if ((Get-Item $err).Length -gt 0) { '  stderr: ' + ((Get-Content $err -TotalCount 3) -join ' | ') }
}
