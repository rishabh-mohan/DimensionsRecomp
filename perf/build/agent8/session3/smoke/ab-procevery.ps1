# M8 smoke item 9: ProcEvery 0 vs 5 A/B (ABBA), temporary local default edit in drivers\sys-csv.ps1 L39, restored in finally.
$ErrorActionPreference = 'Stop'
$WS = '<workspace>'
Set-Location $WS
$drv = Join-Path $WS 'bench\agent8\run\drivers\sys-csv.ps1'
$want = 'F3F06AB013F2423E'
$smoke = Join-Path $WS 'build\agent8\session3\smoke'
if (-not (Get-FileHash $drv).Hash.StartsWith($want)) { throw 'sys-csv.ps1 not at the installed hash' }
$origBytes = [IO.File]::ReadAllBytes($drv)
$orig = [IO.File]::ReadAllText($drv)
$line5 = "[string]`$ProcEvery = '5'"
if (([regex]::Matches($orig, [regex]::Escape($line5))).Count -ne 1) { throw 'ProcEvery default line not unique' }
$p0 = $orig.Replace($line5, "[string]`$ProcEvery = '0'")
$seq = @(0, 5, 5, 0)
try {
    for ($i = 0; $i -lt $seq.Count; $i++) {
        if (Get-Process legodimensions -ErrorAction SilentlyContinue) { throw 'a game is running' }
        if (Test-Path (Join-Path $WS 'perf-notes\WINDOW-HOLD.txt')) { throw 'WINDOW-HOLD' }
        $k = $seq[$i]
        if ($k -eq 0) { [IO.File]::WriteAllText($drv, $p0) } else { [IO.File]::WriteAllBytes($drv, $origBytes) }
        $o = Join-Path $smoke ("ab-{0}-p{1}" -f ($i + 1), $k)
        "$(Get-Date -Format HH:mm:ss) run $($i + 1) ProcEvery=$k -> $o"
        $p = Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'bench\agent8\run\run-matrix.ps1', '-Matrix', (Join-Path $smoke 'matrix-smoke.json'),
            '-Quick', '-NoPrompt', '-Only', 's0', '-NoCold', '-WarmupRuns', '0', '-OutDir', $o -NoNewWindow -PassThru -RedirectStandardOutput "$o.console.txt" -RedirectStandardError "$o.console.err"
        $null = $p.Handle; $p.PriorityClass = 'BelowNormal'; $p.WaitForExit()
        "$(Get-Date -Format HH:mm:ss) run $($i + 1) exit $($p.ExitCode)"
    }
} finally {
    [IO.File]::WriteAllBytes($drv, $origBytes)
    $h = (Get-FileHash $drv).Hash
    "restored sys-csv.ps1: $h $(if ($h.StartsWith($want)) { 'OK' } else { 'MISMATCH' })"
}
