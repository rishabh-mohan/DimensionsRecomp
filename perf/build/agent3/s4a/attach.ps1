# attach.ps1 - Agent 3 S4a sidecar (task #5). Waits for the game that run-game.ps1 launches under -RunsRoot
# (process path under -RunsRoot, started at or after -NotBefore), then:
#   - starts Agent 8's bench\agent8\run\drivers\sys-csv.ps1 -GamePid <pid> -RunDir <run> (stdout/stderr ->
#     <run>\sys.out.txt / sys.err.txt) ONLY if its LdSys DLL is already cached (build\agent8\cache is a W4b input:
#     never let it compile there); read-only use of Agent 8's files;
#   - samples per-thread CPU into <run>\threads-s4a.csv (S4aThreads.cs, DLL cached in build\agent3\s4a\cache);
#   - writes <run>\attach-s4a.txt. Ends when the game exits. Functional runs only, never timing.
param(
    [string]$RunsRoot = 'build\agent3\runs',
    [string]$NotBefore = '',
    [int]$FindTimeoutSec = 120,
    [int]$ThreadIntervalMs = 2000,
    [switch]$NoSys
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $repo
$root = (Resolve-Path $RunsRoot).Path
$nb = if ($NotBefore) { [datetime]::Parse($NotBefore) } else { (Get-Date).AddSeconds(-5) }
$log = New-Object System.Collections.Generic.List[string]
function Say([string]$m) { $s = (Get-Date -Format 'HH:mm:ss.fff') + ' ' + $m; $log.Add($s); Write-Host $s }

$p = $null
$t0 = Get-Date
while (-not $p -and ((Get-Date) - $t0).TotalSeconds -lt $FindTimeoutSec) {
    $p = Get-Process legodimensions -ErrorAction SilentlyContinue | Where-Object {
        try { $_.Path -like "$root\*" -and $_.StartTime -ge $nb.AddSeconds(-2) } catch { $false } } | Select-Object -First 1
    if (-not $p) { Start-Sleep -Milliseconds 250 }
}
if (-not $p) { Say "attach: no game under $root started after $nb within $FindTimeoutSec s"; exit 1 }
$rd = Split-Path -Parent $p.Path
Say "attach: pid $($p.Id) run $rd started $($p.StartTime.ToString('HH:mm:ss.fff'))"

$sys = $null
if (-not $NoSys) {
    $cs = Join-Path $repo 'bench\agent8\run\drivers\LdSys.cs'
    $key = (Get-FileHash -LiteralPath $cs -Algorithm SHA256).Hash.Substring(0, 8).ToLower()
    $dll = Join-Path $repo "build\agent8\cache\LdSys-$key.dll"
    if (Test-Path -LiteralPath $dll) {
        $sys = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $rd 'sys.out.txt') `
            -RedirectStandardError (Join-Path $rd 'sys.err.txt') -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            (Join-Path $repo 'bench\agent8\run\drivers\sys-csv.ps1'), '-GamePid', "$($p.Id)", '-RunDir', $rd)
        $null = $sys.Handle   # keep the handle so ExitCode is readable after the exit
        Say "attach: sys-csv.ps1 pid $($sys.Id) (LdSys-$key.dll cached)"
    } else { Say "attach: SKIP sys.csv: LdSys-$key.dll not cached (would compile into build\agent8\cache, a W4b input)" }
}

$tcs = Join-Path $PSScriptRoot 'S4aThreads.cs'
$tkey = (Get-FileHash -LiteralPath $tcs -Algorithm SHA256).Hash.Substring(0, 8).ToLower()
$cacheDir = Join-Path $PSScriptRoot 'cache'
$tdll = Join-Path $cacheDir "S4aThreads-$tkey.dll"
try {
    if (-not ('S4aThreads' -as [type])) {
        if (-not (Test-Path -LiteralPath $tdll)) {
            New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
            $tmp = Join-Path $cacheDir "S4aThreads-$tkey.$PID.tmp.dll"
            Add-Type -Path $tcs -OutputAssembly $tmp -OutputType Library
            try { Move-Item -LiteralPath $tmp -Destination $tdll } catch { Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue }
        }
        [void][Reflection.Assembly]::LoadFrom($tdll)
    }
    $out = Join-Path $rd 'threads-s4a.csv'
    $rc = [S4aThreads]::Run($p.Id, $out, $ThreadIntervalMs, 3600)
    Say ("attach: threads rc={0} reason={1} ticks={2} rows={3} max_threads={4}" -f $rc, [S4aThreads]::Reason, [S4aThreads]::Ticks, [S4aThreads]::Rows, [S4aThreads]::MaxThreads)
} catch { Say "attach: thread sampler failed: $($_.Exception.Message)"; try { $p.WaitForExit() } catch { } }

if ($sys) {
    if (-not $sys.WaitForExit(30000)) { Say 'attach: sys-csv still running 30 s after the game exit; stop file'; New-Item -ItemType File -Force -Path (Join-Path $rd 'sys.stop') | Out-Null; [void]$sys.WaitForExit(10000) }
    Say "attach: sys-csv exited $(if ($sys.HasExited) { $sys.ExitCode } else { 'NO' })"
}
[IO.File]::WriteAllLines((Join-Path $rd 'attach-s4a.txt'), $log)
exit 0
