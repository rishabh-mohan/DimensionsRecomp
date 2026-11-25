# Timing run of a staged bin dir (task #16). Warm-up, then a fixed measure window cut from the frames csv.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-timing.ps1 [-BinDir build\baseline-bin]
#       [-Tag timing] [-Warmup 60] [-Seconds 60] [-Cvar 'a=1;b=2'] [-Env 'NAME=v'] [-Toml 'key=rawToml']
#       [-CloseTimeoutSec 60] [-MinFreeRamGB 6] [-Profile [-ProfileSeconds 30]] [-RunsRoot build\agent8\runs]
#       [-WarmupFrom launch|firstframe] [-BootTimeoutSec 240] [-SettleSec 0] [-MenuText 'text' [-MenuSec 60]]
#       [-Driver script.ps1 [-DriverArgs 'a;b'] [-DriverTimeoutSec 120]] [-Frames perf|native]
#       [-SeedCache <run dir or dir> [-SeedRecipesOnly]] [-TriggerAtMeasure 'path;path']
#       [-SysCsv] [-MinWindowAfterFirstFrame 60] [-LightMs 4.5]
# With powershell -File, list items are separated with ';' (a ',' stays part of the value).
# Placeholder <run> = the run dir, in -Cvar/-Env/-Toml values, -DriverArgs and -TriggerAtMeasure (toml values get
# forward slashes, so a path inside a TOML "..." string needs no escaping); run.json keeps both forms.
# -TriggerAtMeasure creates each file (empty; a relative path is under the run dir) at the measure-start mark; the
# game deletes it. Close: WM_CLOSE, and any exit within -CloseTimeoutSec counts as a clean close (the real game
# hard-exits 0.3 s after WM_CLOSE, but its process can take ~33 s to go away); only after that, Kill.
# Mirrors <BinDir> into <RunsRoot>\<HHmm>-<Tag> and writes the toml exactly like first-boot.ps1, starts the game
# with the verified flags, samples the process and the frames-csv SIZE every 1 s (proc.csv; the game holds perf.csv
# without read sharing). -WarmupFrom launch (default) counts the warm-up from process start; firstframe counts it
# from the first frame signal (frames csv larger than its header; no signal within -BootTimeoutSec = problem
# 'no first frame'), then -SettleSec, then the optional -MenuText prompt with a -MenuSec countdown, then -Warmup.
# The window is marked at the end of the warm-up and -Seconds later (QPC + wall clock + csv bytes). An optional
# -Driver runs during the window with -GamePid/-RunDir. Closes with WM_CLOSE (kill after -CloseTimeoutSec; also in a
# finally block on Ctrl+C or error), collects crash artifacts, then cuts the window from the final csv
# (frame_summary.py). Writes run.json, frames.json, summary.txt. The profiler is OFF unless -Profile.
# Session 3 (window 4):
#   -SysCsv runs drivers\sys-csv.ps1 from the game start to its exit (sys.csv, 1 s: idle time, foreground, input
#   desktop, screensaver, CPU util/MHz, thermal, power) and summarises the window with sys_summary.py (sys.json).
#   -MinWindowAfterFirstFrame F: with -WarmupFrom firstframe the warm-up is raised so that settle + menu + warm-up
#   >= F; after the run, ff_to_window_s (first-frame signal to the start mark) < F - 0.5 adds window_before_floor.
#   Light phase: install_dat_fail = lines "FAILED: path='d:\INSTALL*.DAT'" in all game*.log (the log rotates at
#   5 MB; a normal boot has 34, window 3's light run 0); < 30 = light_phase. The share of window frames under
#   -LightMs ms (default 4.5) >= 0.6 with a normal marker = light_share_high.
#   run.json flags_excluding / flags_info / excluded: excluding = light_phase, window_before_floor and, on the
#   interactive desktop only, the sys flags input_during_window, not_foreground (game foreground for > 0 and < 99 %
#   of the window), on_battery, battery_saver, power_change, desktop_not_default, screensaver. Everything else is
#   info (light_share_high, never_foreground = 0 % foreground, thermal_passive, sample_gaps, short_window,
#   ticks_skipped, build_procs_warmup/window, install_marker_lost, sys_missing). Build tools seen in the window
#   (checked every 5 s) also make the run FUNCTIONAL ONLY (valid_timing false).
#   Dumps of other processes (<exe>.<pid>.dmp that is not legodimensions.exe.<this pid>) are foreign_crash_dumps,
#   not a problem.
# Exit codes: 0 ok, 1 run problem (died/hung/killed/no frames/no first frame/missing seed file), 3 not started (RAM).
param(
    [string]$BinDir = 'build\baseline-bin',
    [string]$Tag = 'timing',
    [int]$Warmup = 60,
    [int]$Seconds = 60,
    [string[]]$Cvar = @(),
    [string[]]$Env = @(),
    [string[]]$Toml = @(),
    [int]$CloseTimeoutSec = 60,
    [double]$MinFreeRamGB = 6.0,
    [switch]$Profile,
    [int]$ProfileSeconds = 30,
    [string]$RunsRoot = 'build\agent8\runs',
    [int]$StallSec = 10,
    [ValidateSet('launch', 'firstframe')][string]$WarmupFrom = 'launch',
    [int]$BootTimeoutSec = 240,
    [int]$SettleSec = 0,
    [string]$MenuText = '',
    [int]$MenuSec = 60,
    [string]$Driver = '',
    [string[]]$DriverArgs = @(),
    [int]$DriverTimeoutSec = 120,
    [ValidateSet('perf', 'native')][string]$Frames = 'perf',
    [string]$SeedCache = '',
    [switch]$SeedRecipesOnly,
    [string[]]$TriggerAtMeasure = @(),
    [switch]$SysCsv,
    [double]$MinWindowAfterFirstFrame = 0,
    [double]$LightMs = 4.5
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\common.ps1"
. "$PSScriptRoot\timing-env.ps1"
try { Import-LdHelper } catch { if (-not ('LdHarness' -as [type])) { throw } }
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Split-Items([string[]]$Items) {
    $o = @()
    foreach ($i in $Items) { foreach ($p in ($i -split ';')) { if ($p.Trim()) { $o += $p.Trim() } } }
    return , $o
}
function Get-Epoch { return [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0 }
function New-Mark([string]$Name, [string]$CsvPath) {
    $fi = New-Object IO.FileInfo $CsvPath
    $fi.Refresh()
    $q = [Diagnostics.Stopwatch]::GetTimestamp()
    return [ordered]@{ name = $Name; qpc = $q; epoch_s = (Get-Epoch); wall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
                       perf_csv_bytes = $(if ($fi.Exists) { $fi.Length } else { 0L }) }
}
function Beep-Safe([int]$Hz, [int]$Ms) { try { [console]::Beep($Hz, $Ms) } catch { } }
function Abs-Path([string]$P) { if ([IO.Path]::IsPathRooted($P)) { return $P } else { return (Join-Path $repoRoot $P) } }

$cvarRaw = Split-Items $Cvar
$Cvar = $cvarRaw
$trigRaw = Split-Items $TriggerAtMeasure
$envItems = Split-Items $Env
$tomlItems = Split-Items $Toml
$drvArgItems = Split-Items $DriverArgs
$envH = @{}
foreach ($e in $envItems) { $k, $v = $e -split '=', 2; $envH[$k.Trim()] = [string]$v }
$tomlH = @{}
foreach ($t in $tomlItems) { $k, $v = $t -split '=', 2; $tomlH[$k.Trim()] = [string]$v }
$ProfileSeconds = [math]::Max(1, [math]::Min($ProfileSeconds, $Seconds))
if ($WarmupFrom -eq 'launch' -and ($MenuText -or $SettleSec -gt 0)) { "note: -MenuText/-SettleSec need the first frame: using -WarmupFrom firstframe"; $WarmupFrom = 'firstframe' }
$fromFirst = $WarmupFrom -eq 'firstframe'
if ($BootTimeoutSec -le 0) { $BootTimeoutSec = 240 }
# Floor (session 3, Agent 1): the window starts >= -MinWindowAfterFirstFrame s after the first-frame signal.
$warmupAsked = $Warmup; $floorNote = $null
if ($MinWindowAfterFirstFrame -gt 0) {
    if ($fromFirst) {
        $preWarm = $SettleSec + $(if ($MenuText) { $MenuSec } else { 0 })
        $needWarm = [int][math]::Ceiling($MinWindowAfterFirstFrame - $preWarm)
        if ($Warmup -lt $needWarm) { $Warmup = $needWarm; $floorNote = "warm-up raised from $warmupAsked s to $Warmup s (settle + menu + warm-up >= $MinWindowAfterFirstFrame s after the first frame)" }
    } else { $floorNote = "warm-up from launch: the $MinWindowAfterFirstFrame s first-frame floor is only checked after the run" }
    if ($floorNote) { "note: $floorNote" }
}
# INSTALL markers in every game*.log (rotated at 5 MB: game.1.log is the older part). Never throws.
function Get-InstallMarker([string]$RunDir) {
    $r = [ordered]@{ files = @(); install_lines = $null; install_dat_fail = $null; boot_lines_found = $false; error = $null }
    try {
        $fs = @(Get-ChildItem -LiteralPath $RunDir -Filter 'game*.log' -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^game(\.\d+)?\.log$' } |
                Sort-Object @{ Expression = { if ($_.Name -match '^game\.(\d+)\.log$') { -[int]$Matches[1] } else { 0 } } })
        $r.files = @($fs | ForEach-Object { "$($_.Name) $($_.Length) B" })
        $il = 0; $df = 0; $first = $true
        foreach ($f in $fs) {
            $st = [IO.File]::Open($f.FullName, 'Open', 'Read', 'ReadWrite')
            try { $txt = (New-Object IO.StreamReader($st)).ReadToEnd() } finally { $st.Dispose() }
            $il += [regex]::Matches($txt, '(?m)^[^\r\n]*INSTALL').Count
            $df += [regex]::Matches($txt, "FAILED: path='d:\\INSTALL[^']*\.DAT'").Count
            if ($first -and $txt -match 'GPU route:|DXGI adapter|Direct3D 12 device') { $r.boot_lines_found = $true }
            $first = $false
        }
        if ($fs.Count) { $r.install_lines = $il; $r.install_dat_fail = $df } else { $r.error = 'no game*.log' }
    } catch { $r.error = $_.Exception.Message }
    return $r
}

# Seed cache: check before anything is created (a missing requested file = not started, exit 1).
$seedSrc = $null; $seedNames = @()
if ($SeedCache) {
    $sd = Abs-Path $SeedCache
    $isRun = (Test-Path -LiteralPath (Join-Path $sd 'run.json')) -or (Test-Path -LiteralPath (Join-Path $sd 'legodimensions.exe'))
    $seedSrc = if ($isRun) { Join-Path $sd 'cache' } else { $sd }
    $seedNames = if ($SeedRecipesOnly) { @('native-pso-recipes.bin') } else { @('native-pso.bin', 'native-pso-recipes.bin') }
    $missing = @($seedNames | Where-Object { -not (Test-Path -LiteralPath (Join-Path $seedSrc $_) -PathType Leaf) })
    if ($missing.Count) { "!!! SEED CACHE: missing $($missing -join ', ') in $seedSrc (from -SeedCache $SeedCache): game not started"; exit 1 }
}

$free0 = Get-FreeRamGB
if ($free0 -lt $MinFreeRamGB) { "free RAM $free0 GB is under $MinFreeRamGB GB: not starting"; exit 3 }
$run = New-RunDir -BinDir $BinDir -Tag $Tag -RunsRoot $RunsRoot
# <run> placeholder -> run dir (toml: forward slashes). The raw forms stay in run.json params.
function Expand-Run([string]$S, [string]$With) { if ([string]::IsNullOrEmpty($S)) { return $S }; return [regex]::Replace($S, '(?i)<run>', $With.Replace('$', '$$')) }
$runFwd = $run.Replace('\', '/')
$Cvar = @($cvarRaw | ForEach-Object { Expand-Run $_ $run })
foreach ($k in @($envH.Keys)) { $envH[$k] = Expand-Run $envH[$k] $run }
foreach ($k in @($tomlH.Keys)) { $tomlH[$k] = Expand-Run $tomlH[$k] $runFwd }
$drvArgItems = @($drvArgItems | ForEach-Object { Expand-Run $_ $run })
$trigItems = @($trigRaw | ForEach-Object { $x = Expand-Run $_ $run; if ([IO.Path]::IsPathRooted($x)) { $x } else { Join-Path $run $x } })
$mTriggers = New-Object System.Collections.Generic.List[object]
Write-RunToml -Run $run -Set $tomlH
$seed = $null
if ($SeedCache) {
    $cacheDir = Join-Path $run 'cache'
    New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
    $sf = @()
    foreach ($n in $seedNames) {
        $src = Get-Item -LiteralPath (Join-Path $seedSrc $n)
        Copy-Item -LiteralPath $src.FullName -Destination (Join-Path $cacheDir $n) -Force
        $sf += [ordered]@{ name = $n; source = $src.FullName; bytes = $src.Length; sha256 = (Get-FileHash -LiteralPath $src.FullName -Algorithm SHA256).Hash }
    }
    $seed = [ordered]@{ requested = $SeedCache; source_dir = $seedSrc; recipes_only = [bool]$SeedRecipesOnly; dest = $cacheDir; files = $sf }
}
$gameArgs = Get-GameArgs -Run $run -Cvar $Cvar
$trigger = Join-Path $run 'profile.trigger'
if ($Profile) { $envH['LEGO_SAMPLE_PROFILE'] = '1'; $envH['LEGO_SAMPLE_PROFILE_TRIGGER'] = $trigger }
$csvPath = if ($Frames -eq 'native') { Join-Path $run 'native-frames.csv' } else { Join-Path $run 'perf.csv' }
if ($Frames -eq 'native') { $envH['LEGO_NATIVE_FRAME_METRICS'] = $csvPath }
$csvName = Split-Path -Leaf $csvPath
# perf.csv header: 17 names + CRLF = 315 bytes (fflushed together with the first 60 rows).
$headerBytes = if ($Frames -eq 'perf') { 315L } else { 0L }
$profiling = $Profile -or $envH.ContainsKey('LEGO_SAMPLE_PROFILE')
$mode = if ($profiling) { 'PROFILE ONLY, NOT FOR TIMING' } else { 'TIMING' }
$desk = Get-DesktopName
"=== run-timing [$mode] ==="
"run dir: $run"
"args: $($gameArgs -join ' ')"
"env: $(($envH.Keys | Sort-Object | ForEach-Object { "$_=$($envH[$_])" }) -join ' ')"
"toml: $(($tomlH.Keys | Sort-Object | ForEach-Object { "$_ = $($tomlH[$_])" }) -join '; ')"
if ($seed) { "seed cache: $(($seed.files | ForEach-Object { "$($_.name) $($_.bytes) B" }) -join ', ') from $seedSrc" }
"frames: $csvName; desktop $desk$(if (-not (Test-TimingDesktop $desk)) { ' -> FUNCTIONAL ONLY (not the interactive desktop)' })"
if ($fromFirst) { "warm-up from the first frame (boot timeout $BootTimeoutSec s): settle $SettleSec s$(if ($MenuText) { ", menu step $MenuSec s" }), warm-up $Warmup s, window $Seconds s" }
else { "warm-up $Warmup s from launch, window $Seconds s" }
"$(if ($Profile) { "profile trigger for the first $ProfileSeconds s of the window; " })free RAM $free0 GB"

$ncpu = [Environment]::ProcessorCount
$logC = New-LineCounter (Join-Path $run 'game.log')
# proc.csv rows. A driver may tail proc.csv (thread-cpu.ps1 waits for "measure end"). Add-Content opens with
# FileShare.Write, so a concurrent reader made it throw (verify3, 23:35: "being used by another process" and
# "Stream was not readable"). File.AppendAllText shares Read; retry briefly anyway and never throw from here.
function Add-ProcRow([string]$Line) {
    for ($k = 0; $k -lt 40; $k++) {
        try { [IO.File]::AppendAllText($procCsv, $Line + "`r`n", [Text.Encoding]::ASCII); return } catch { Start-Sleep -Milliseconds 25 }
    }
    Write-Output '!!! proc.csv row dropped (file busy for 1 s)'
}
$procCsv = Join-Path $run 'proc.csv'
't_s,phase,alive,cpu_cores,cpu_s,ws_mb,peak_ws_mb,commit_mb,peak_commit_mb,threads,handles,responding,log_lines,perf_csv_bytes,free_ram_gb,note' |
    Set-Content -LiteralPath $procCsv -Encoding ascii

$qpcFreq = [Diagnostics.Stopwatch]::Frequency
$start = Get-Date
$startMark = New-Mark 'process_start' $csvPath
# Start-Process (ShellExecute: no inherited pipe handles). The child inherits this process's environment, so
# LEGO_SAMPLE_PROFILE* / LEGO_NATIVE_FRAME_METRICS are removed first and only -Env / -Profile / -Frames set them.
# Everything set here is restored right after the start (run-matrix.ps1 calls this script in-process).
foreach ($k in @('LEGO_SAMPLE_PROFILE', 'LEGO_SAMPLE_PROFILE_TRIGGER', 'LEGO_NATIVE_FRAME_METRICS')) { [Environment]::SetEnvironmentVariable($k, $null, 'Process') }
$envSaved = @{}
foreach ($k in $envH.Keys) { $envSaved[$k] = [Environment]::GetEnvironmentVariable($k, 'Process'); [Environment]::SetEnvironmentVariable($k, [string]$envH[$k], 'Process') }
$argLine = (($gameArgs | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' ')
try {
    $p = Start-Process -FilePath (Join-Path $run 'legodimensions.exe') -ArgumentList $argLine -WorkingDirectory $run -PassThru
} finally {
    foreach ($k in $envSaved.Keys) { [Environment]::SetEnvironmentVariable($k, $envSaved[$k], 'Process') }
}
$null = $p.Handle   # keep the handle so ExitCode stays readable after exit
$sw = [Diagnostics.Stopwatch]::StartNew()
$gamePid = $p.Id
"started pid $gamePid at $($start.ToString('HH:mm:ss.fff'))"
# sys.csv sampler (-SysCsv): from now until the game exits (or <run>\sys.stop appears).
$sysDrv = $null; $sysInfo = $null; $sysErr = $null
$sysCsvPath = Join-Path $run 'sys.csv'; $sysStop = Join-Path $run 'sys.stop'
if ($SysCsv) {
    $sysScript = Join-Path $PSScriptRoot 'drivers\sys-csv.ps1'
    $sArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $sysScript, '-GamePid', [string]$gamePid, '-RunDir', $run, '-StopFile', $sysStop, '-Out', $sysCsvPath)
    $sLine = (($sArgs | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' ')
    try {
        $sysDrv = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $sLine -WorkingDirectory $run -NoNewWindow -PassThru `
            -RedirectStandardOutput (Join-Path $run 'sys.out.txt') -RedirectStandardError (Join-Path $run 'sys.err.txt')
        $null = $sysDrv.Handle
        $sysInfo = [ordered]@{ script = $sysScript; pid = $sysDrv.Id; exit_code = $null; killed = $false; error = $null; stop_line = $null }
        "sys.csv sampler started: pid $($sysDrv.Id)"
    } catch {
        $sysDrv = $null
        $sysInfo = [ordered]@{ script = $sysScript; pid = $null; exit_code = $null; killed = $false; error = $_.Exception.Message; stop_line = $null }
        "!!! sys.csv sampler failed to start: $($_.Exception.Message)"
    }
}

$prevCpu = 0.0; $prevT = 0.0
$winCores = New-Object System.Collections.Generic.List[double]
$winPeakWs = 0L; $winPeakCommit = 0L; $lifePeakWs = 0L; $lifePeakCommit = 0L
$mStart = $null; $mEnd = $null; $trigOn = $null; $trigOff = $null
$exitedEarly = $false; $exitedAt = $null; $exitedPhase = $null
$notRespondingWin = 0; $notResponding = 0
$lastBytes = -1L; $lastGrowT = 0.0; $stalled = $false; $stallAt = $null; $maxNoGrowWin = 0.0
$dialogs = New-Object System.Collections.Generic.List[string]
$werSeen = $false; $windowDesc = @()
$problems = New-Object System.Collections.Generic.List[string]
$firstTick = $null; $firstFrameS = $null; $bootTimedOut = $false
$warmStart = if ($fromFirst) { $null } else { 0 }
$warmStartT = if ($fromFirst) { $null } else { 0.0 }
$startTick = if ($fromFirst) { -1 } else { $Warmup }
$endTick = if ($fromFirst) { -1 } else { $Warmup + $Seconds }
$menuAt = $null; $drv = $null; $drvInfo = $null; $envAtStart = $null; $envAtEnd = $null
$close = $null; $exitCode = $null; $closedOk = $false; $runErr = $null
$profiles = @()
$ffQpc = $null; $ffEpoch = $null; $ticksSkipped = 0; $ticksSkippedWin = 0
$bpWin = @{}; $bpWarm = @{}; $bpChecks = 0
$tick = 0
try {
    while ($true) {
        $tick++
        # A pass that ran long leaves the loop behind the clock: jump to the current second instead of running the
        # missed ticks back to back (caveat 1). The events below use -ge with guards, so none is lost.
        $el = $sw.Elapsed.TotalSeconds
        if ($el -ge ($tick + 1)) {
            $jump = [int][math]::Floor($el) - $tick
            if ($jump -gt 0) {
                $ticksSkipped += $jump; $tick += $jump
                if ($null -ne $mStart -and $null -eq $mEnd) { $ticksSkippedWin += $jump }
                "note: runner $jump s behind the clock at $([math]::Round($el, 2)) s: skipped to tick $tick"
            }
        }
        $wait = [int](($tick - $sw.Elapsed.TotalSeconds) * 1000)
        if ($wait -gt 0) { [void]$p.WaitForExit($wait) }
        $t = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        $fi = New-Object IO.FileInfo $csvPath; $fi.Refresh()
        $bytes = if ($fi.Exists) { $fi.Length } else { 0L }
        $note = ''
        if ($null -eq $firstTick -and $bytes -gt $headerBytes) {
            $firstTick = $tick; $firstFrameS = $t; $note = 'first frame signal'
            $ffQpc = [Diagnostics.Stopwatch]::GetTimestamp(); $ffEpoch = Get-Epoch
            if ($fromFirst) {
                # Count from the tick at or after (sample time - 0.3 s): a sample taken late in its tick (runner behind)
                # would otherwise start the window up to ~1 s before the floor and flag window_before_floor wrongly.
                $warmStart = [math]::Max($tick, [int][math]::Ceiling($t - 0.3)) + $SettleSec + $(if ($MenuText) { $MenuSec } else { 0 })
                $startTick = $warmStart + $Warmup; $endTick = $startTick + $Seconds
            }
            "first frame signal ($csvName $bytes B > header $headerBytes B) at $t s"
        }
        if ($null -eq $warmStart) { $phase = 'boot' }
        elseif ($tick -le $warmStart) { $phase = $(if ($MenuText -and $tick -gt ($firstTick + $SettleSec)) { 'menu' } else { 'settle' }) }
        elseif ($tick -le $startTick) { $phase = 'warmup' }
        else { $phase = 'measure' }
        if ($p.HasExited) {
            $exitedEarly = $true; $exitedAt = $t; $exitedPhase = $phase
            Update-LineCounter $logC
            $row = @((Fmt $t 2), $phase, 0, '', '', '', '', '', '', '', '', '', $logC.Lines, $bytes, (Fmt (Get-FreeRamGB) 2), 'exited')
            Add-ProcRow ($row -join ',')
            "!!! PROCESS EXITED at $t s during $phase"
            break
        }
        if ($fromFirst -and $null -eq $firstTick -and $t -ge $BootTimeoutSec) {
            $bootTimedOut = $true
            "!!! NO FIRST FRAME: $csvName not past its header within $BootTimeoutSec s"
            break
        }
        if ($MenuText -and $phase -eq 'menu' -and $null -eq $menuAt) {
            $menuAt = $t
            Write-Host ''
            Write-Host "  >>> MENU STEP ($MenuSec s): $MenuText  " -ForegroundColor Black -BackgroundColor Yellow
            Write-Host '  Do it now in the GAME window. Do not touch this console: the warm-up starts by itself.' -ForegroundColor Yellow
            Beep-Safe 880 200; Beep-Safe 1175 300
            $note = ($note + '; menu prompt').TrimStart('; ')
        }
        if ($phase -eq 'menu') {
            $rem = $warmStart - $tick
            if ($rem -gt 0 -and (($rem % 10) -eq 0 -or $rem -le 5)) { Write-Host "  menu: $rem s left" -ForegroundColor Yellow }
        }
        if ($fromFirst -and $null -ne $warmStart -and $null -eq $warmStartT -and $tick -ge $warmStart) {
            $warmStartT = $t
            if ($MenuText) { Write-Host "  >>> HANDS OFF NOW: warm-up $Warmup s, then measure $Seconds s  " -ForegroundColor Black -BackgroundColor Green; Beep-Safe 660 400 }
            "warm-up starts at $t s"
            $note = ($note + '; warm-up start').TrimStart('; ')
        }
        # marks first, before the slower process sampling
        if ($null -eq $mStart -and $startTick -ge 0 -and $tick -ge $startTick) {
            $mStart = New-Mark 'measure_start' $csvPath; $note = ($note + '; measure start').TrimStart('; ')
            if ($tick -ne $startTick) {
                # Late start mark (runner behind the clock): move the end with it so the window keeps its full length
                # (the frames cut takes -Seconds from the start mark; the game must still be running by then).
                $note += "; late by $($tick - $startTick) s"; $endTick = $tick + $Seconds
            }
            if ($Profile) {
                $q0 = [Diagnostics.Stopwatch]::GetTimestamp()
                [IO.File]::WriteAllText($trigger, "profile trigger $(Get-Date -Format o)")
                $trigOn = [ordered]@{ qpc_before = $q0; qpc = [Diagnostics.Stopwatch]::GetTimestamp(); epoch_s = (Get-Epoch)
                                      wall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff') }
                $note += '; profile trigger created'
            }
            foreach ($tf in $trigItems) {
                $q0 = [Diagnostics.Stopwatch]::GetTimestamp(); $tErr = $null
                try {
                    $pd = Split-Path -Parent $tf
                    if ($pd -and -not (Test-Path -LiteralPath $pd)) { New-Item -ItemType Directory -Force -Path $pd | Out-Null }
                    [IO.File]::WriteAllText($tf, '')
                } catch { $tErr = $_.Exception.Message; "!!! trigger $tf not created: $tErr" }
                $mTriggers.Add([ordered]@{ path = $tf; qpc_before = $q0; qpc = [Diagnostics.Stopwatch]::GetTimestamp(); epoch_s = (Get-Epoch)
                                           wall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'); t_s = $t; error = $tErr; exists_after_run = $null })
            }
            if ($trigItems.Count) { $note += "; $($trigItems.Count) trigger(s) created" }
            if ($Driver) {
                $drvFile = Abs-Path $Driver
                $dArgs = @()
                if ($drvFile -like '*.ps1') { $dExe = Join-Path $PSHOME 'powershell.exe'; $dArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $drvFile) } else { $dExe = $drvFile }
                $dArgs += @('-GamePid', [string]$gamePid, '-RunDir', $run) + $drvArgItems
                $dLine = (($dArgs | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' ')
                try {
                    $drv = Start-Process -FilePath $dExe -ArgumentList $dLine -WorkingDirectory $run -NoNewWindow -PassThru `
                        -RedirectStandardOutput (Join-Path $run 'driver.out.txt') -RedirectStandardError (Join-Path $run 'driver.err.txt')
                    $null = $drv.Handle
                    $drvInfo = [ordered]@{ path = $drvFile; args = $dArgs; pid = $drv.Id; start_s = $t; start_qpc = [Diagnostics.Stopwatch]::GetTimestamp()
                                           end_s = $null; exit_code = $null; killed = $false; error = $null }
                    "driver started: pid $($drv.Id) $drvFile"
                } catch { $drvInfo = [ordered]@{ path = $drvFile; args = $dArgs; error = $_.Exception.Message; exit_code = $null; killed = $false }; "!!! driver failed to start: $($_.Exception.Message)" }
                $note += '; driver'
            }
            $envAtStart = Get-TimingEnv
        }
        if ($Profile -and $null -ne $trigOn -and $null -eq $trigOff -and $tick -ge ($startTick + $ProfileSeconds)) {
            $q0 = [Diagnostics.Stopwatch]::GetTimestamp()
            Remove-Item -LiteralPath $trigger -Force
            $trigOff = [ordered]@{ qpc_before = $q0; qpc = [Diagnostics.Stopwatch]::GetTimestamp(); epoch_s = (Get-Epoch)
                                   wall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff') }
            $note = ($note + '; profile trigger deleted').TrimStart('; ')
        }
        if ($null -eq $mEnd -and $null -ne $mStart -and $endTick -ge 0 -and $tick -ge $endTick) { $mEnd = New-Mark 'measure_end' $csvPath; $note = ($note + '; measure end').TrimStart('; '); $envAtEnd = Get-TimingEnv }
        # Build tools in the warm-up and the window (Get-BuildProcs, ~26 ms), every 5 s; the marks check them too.
        if (($tick % 5) -eq 3 -and ($phase -eq 'warmup' -or $phase -eq 'measure')) {
            $bpChecks++
            foreach ($bpn in @(Get-BuildProcs)) { if ($phase -eq 'measure') { $bpWin[$bpn] = 1 } else { $bpWarm[$bpn] = 1 } }
        }
        if ($bytes -ne $lastBytes) { $lastBytes = $bytes; $lastGrowT = $t }
        $s = $null
        try { $s = Get-ProcSample $p } catch { }
        if ($null -eq $s) { $tick--; continue }   # exited between the checks: the next pass records it
        $dCpu = $s.cpu_s - $prevCpu; $dT = $t - $prevT
        $cores = if ($dT -gt 0) { $dCpu / $dT } else { 0 }
        $prevCpu = $s.cpu_s; $prevT = $t
        if ($s.peak_ws -gt $lifePeakWs) { $lifePeakWs = $s.peak_ws }
        if ($s.peak_commit -gt $lifePeakCommit) { $lifePeakCommit = $s.peak_commit }
        if ($s.responding -eq $false) { $notResponding++ }
        if ($phase -eq 'measure') {
            $winCores.Add($cores)
            if ($s.ws -gt $winPeakWs) { $winPeakWs = $s.ws }
            if ($s.commit -gt $winPeakCommit) { $winPeakCommit = $s.commit }
            if ($s.responding -eq $false) { $notRespondingWin++; "!!! NOT RESPONDING at $t s" }
            $noGrow = $t - $lastGrowT
            if ($noGrow -gt $maxNoGrowWin) { $maxNoGrowWin = $noGrow }
            if (-not $stalled -and $noGrow -ge $StallSec) {
                $stalled = $true; $stallAt = $t; "!!! $csvName HAS NOT GROWN FOR $([math]::Round($noGrow, 1)) s at $t s (hang?)"
                $note = ($note + '; frames csv stalled').TrimStart('; ')
            }
        }
        Update-LineCounter $logC
        if (($tick % 5) -eq 1) {
            $windowDesc = @([LdHarness]::Describe($gamePid))
            foreach ($d in $windowDesc) {
                if ($d.StartsWith('#32770') -and -not $dialogs.Contains($d)) { $dialogs.Add($d); "!!! DIALOG at $t s: $d"; $note = ($note + '; dialog').TrimStart('; ') }
            }
            if (-not $werSeen -and @(Get-WerFor $gamePid).Count -gt 0) { $werSeen = $true; "!!! WerFault for pid $gamePid at $t s"; $note = ($note + '; WerFault').TrimStart('; ') }
        }
        $row = @((Fmt $t 2), $phase, 1, (Fmt $cores 2), (Fmt $s.cpu_s 2), (Fmt ($s.ws / 1MB) 0), (Fmt ($s.peak_ws / 1MB) 0),
                 (Fmt ($s.commit / 1MB) 0), (Fmt ($s.peak_commit / 1MB) 0), $s.threads, $s.handles, $s.responding,
                 $logC.Lines, $bytes, (Fmt (Get-FreeRamGB) 2), ($note -replace ',', ';'))
        Add-ProcRow ($row -join ',')
        if (($tick % 10) -eq 0 -or $tick -eq $startTick -or $tick -eq $endTick) {
            "t=$t s $phase cpu=$(Fmt $cores 2) cores ws=$(Fmt ($s.ws/1MB) 0) MB commit=$(Fmt ($s.commit/1MB) 0) MB $csvName=$bytes B log=$($logC.Lines)$(if ($note) { " [$note]" })"
        }
        if ($null -ne $mEnd -and $tick -ge $endTick) { break }
    }

    # Driver: wait for it (it was started at the window start).
    if ($drv) {
        if (-not $drv.HasExited) { "waiting for the driver (pid $($drv.Id), up to $DriverTimeoutSec s)" }
        if (-not $drv.WaitForExit([math]::Max(1, $DriverTimeoutSec) * 1000)) { try { $drv.Kill() } catch { }; $drvInfo.killed = $true; [void]$drv.WaitForExit(5000) }
        try { $drvInfo.exit_code = $drv.ExitCode } catch { }
        $drvInfo.end_s = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        "driver: exit $($drvInfo.exit_code)$(if ($drvInfo.killed) { ' (KILLED after the timeout)' })"
    }

    # Profile: make sure the trigger is gone and wait for the .bin before closing (the game writes it).
    if ($Profile) {
        if ($null -eq $trigOff -and (Test-Path -LiteralPath $trigger)) {
            $q0 = [Diagnostics.Stopwatch]::GetTimestamp()
            Remove-Item -LiteralPath $trigger -Force
            $trigOff = [ordered]@{ qpc_before = $q0; qpc = [Diagnostics.Stopwatch]::GetTimestamp(); epoch_s = (Get-Epoch)
                                   wall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'); note = 'deleted after the loop' }
        }
        if ($null -ne $trigOn -and -not $p.HasExited) {
            $waitSw = [Diagnostics.Stopwatch]::StartNew(); $lastSize = -1L; $stable = 0
            while ($waitSw.Elapsed.TotalSeconds -lt 30 -and -not $p.HasExited) {
                $bins = @(Get-ChildItem -LiteralPath $run -Filter 'profile-*.bin' -ErrorAction SilentlyContinue)
                $size = 0L; foreach ($b in $bins) { $size += $b.Length }   # no Measure-Object: StrictMode throws on empty input
                if ($bins.Count -gt 0 -and $size -eq $lastSize) { $stable++ } else { $stable = 0 }
                $lastSize = $size
                if ($stable -ge 2) { break }
                Start-Sleep -Milliseconds 500
            }
        }
    }

    if (-not $exitedEarly) {
        $windowDesc = @([LdHarness]::Describe($gamePid))
        $close = Close-GameTimed -P $p -TimeoutSec $CloseTimeoutSec
        "close: posted=$($close.wm_close_posted) exit seen after $($close.exit_seen_s) s killed=$($close.killed)$(if ($close.kill_error) { " kill error: $($close.kill_error)" }) exit=$($close.exit_code_hex)"
    } else {
        try { $exitCode = $p.ExitCode } catch { }
    }
    $closedOk = $true
} catch {
    $runErr = "$($_.Exception.Message) (run-timing.ps1 line $($_.InvocationInfo.ScriptLineNumber))"
    Write-Host "!!! runner error: $runErr" -ForegroundColor Red
    $problems.Add("RUNNER ERROR: $runErr")
} finally {
    if (-not $closedOk) {
        if ($drv -and -not $drv.HasExited) { try { $drv.Kill() } catch { } }
        if ($p -and -not $p.HasExited) {
            Write-Host "!!! error or interrupt: closing the game (pid $gamePid; WM_CLOSE, up to $CloseTimeoutSec s, then kill)" -ForegroundColor Red
            try { $close = Close-GameTimed -P $p -TimeoutSec $CloseTimeoutSec } catch { try { $p.Kill() } catch { } }
        }
        if ($Profile -and (Test-Path -LiteralPath $trigger)) { Remove-Item -LiteralPath $trigger -Force -ErrorAction SilentlyContinue }
    }
}
$end = Get-Date
Start-Sleep -Seconds 2
Update-LineCounter $logC
$artifacts = @()
try { $artifacts = Save-CrashArtifacts -Run $run -Since $start.AddSeconds(-5) } catch { $problems.Add("crash artifact scan failed: $($_.Exception.Message)") }
foreach ($mt in $mTriggers) { $mt.exists_after_run = Test-Path -LiteralPath $mt.path }
$code = if ($close) { $close.exit_code } else { $exitCode }

# sys.csv sampler: it ends by itself when the game exits; the stop file covers the rest. Then summarise the window.
$sysSum = $null
if ($SysCsv) {
    if ($sysDrv) {
        if (-not $sysDrv.HasExited) { try { [IO.File]::WriteAllText($sysStop, "stop $(Get-Date -Format o)") } catch { } }
        if (-not $sysDrv.WaitForExit(10000)) { try { $sysDrv.Kill() } catch { }; $sysInfo.killed = $true; [void]$sysDrv.WaitForExit(3000) }
        try { $sysInfo.exit_code = $sysDrv.ExitCode } catch { }
        $sysOutTxt = Join-Path $run 'sys.out.txt'
        if (Test-Path -LiteralPath $sysOutTxt) {
            $sysStopLines = @(Get-Content -LiteralPath $sysOutTxt -ErrorAction SilentlyContinue | Where-Object { $_ -match '(^|\s)sys-csv: stop ' })
            if ($sysStopLines.Count) { $sysInfo.stop_line = [string]$sysStopLines[-1] }
        }
        "sys.csv sampler: exit $($sysInfo.exit_code)$(if ($sysInfo.killed) { ' (KILLED after 10 s)' })$(if ($sysInfo.stop_line) { '; ' + $sysInfo.stop_line })"
    }
    if (-not (Test-Path -LiteralPath $sysCsvPath)) { $sysErr = $(if ($sysInfo -and $sysInfo.error) { "sampler did not start: $($sysInfo.error)" } else { 'no sys.csv' }) }
    elseif ($null -eq $mStart -or $null -eq $mEnd) { $sysErr = 'no complete window' }
    else {
        $sysJson = Join-Path $run 'sys.json'
        $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $ssOut = & python (Join-Path $PSScriptRoot 'sys_summary.py') --csv $sysCsvPath --start-epoch ([string]$mStart.epoch_s) --end-epoch ([string]$mEnd.epoch_s) --out $sysJson 2>&1 | Out-String
        $ssCode = $LASTEXITCODE
        $ErrorActionPreference = $eap
        if ($ssCode -eq 0 -and (Test-Path -LiteralPath $sysJson)) { $sysSum = Get-Content -LiteralPath $sysJson -Raw | ConvertFrom-Json }
        else { $sysErr = "sys_summary.py exit $($ssCode): $($ssOut.Trim())" }
    }
    if ($sysErr) { "!!! sys.csv: $sysErr" }
}

# Profile artifacts and analyser metadata.
$profileMeta = $null
if ($Profile) {
    $profiles = @(Get-ChildItem -LiteralPath $run -Filter 'profile-*.bin' -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    $mapPath = Join-Path $run 'legodimensions.map'
    if (-not (Test-Path -LiteralPath $mapPath)) {
        $srcMap = Join-Path (Resolve-RepoPath $BinDir) 'legodimensions.map'
        if (Test-Path -LiteralPath $srcMap) { Copy-Item -LiteralPath $srcMap -Destination $mapPath }
    }
    $profileMeta = [ordered]@{
        note = 'PROFILE ONLY, NOT FOR TIMING (the baseline sampler holds timeBeginPeriod(1) for the whole run once LEGO_SAMPLE_PROFILE is set)'
        profile_trigger_start = $(if ($trigOn) { $trigOn.epoch_s } else { $null })
        profile_trigger_end = $(if ($trigOff) { $trigOff.epoch_s } else { $null })
        profile_trigger_start_wall = $(if ($trigOn) { $trigOn.wall } else { $null })
        profile_trigger_end_wall = $(if ($trigOff) { $trigOff.wall } else { $null })
        qpc_frequency = $qpcFreq
        qpc_trigger_start = $(if ($trigOn) { $trigOn.qpc } else { $null })
        qpc_trigger_end = $(if ($trigOff) { $trigOff.qpc } else { $null })
        trigger_file = $trigger; profile_seconds_requested = $ProfileSeconds
        profiles = $profiles; map = $(if (Test-Path -LiteralPath $mapPath) { $mapPath } else { $null })
        run_dir = $run
    }
    $profileMeta | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $run 'profile-meta.json') -Encoding ascii
    "profiles: $(if ($profiles.Count) { $profiles -join ', ' } else { 'NONE WRITTEN' })"
    if ($profiles.Count) {
        "analyse: python DimensionsRecomp\tools\native-cpu\analyze_profile.py `"$($profiles[0])`" `"$mapPath`" --meta `"$(Join-Path $run 'profile-meta.json')`""
    }
}

# Frame window from the final frames csv.
$fsum = $null
$framesJson = Join-Path $run 'frames.json'
$fsArgs = @((Join-Path $PSScriptRoot 'frame_summary.py'), $csvPath, '--json', $framesJson, '--label', $mode, '--quiet', '--light-ms', [string]$LightMs)
if ($null -ne $mStart) {
    $fsArgs += @('--start-bytes', [string]$mStart.perf_csv_bytes, '--seconds', [string]$Seconds)
    if ($null -ne $mEnd) { $fsArgs += @('--end-bytes', [string]$mEnd.perf_csv_bytes) }
}
if (Test-Path -LiteralPath $csvPath) {
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $fsOut = & python @fsArgs 2>&1 | Out-String
    $fsCode = $LASTEXITCODE
    $ErrorActionPreference = $eap
    if ($fsCode -eq 0 -and (Test-Path -LiteralPath $framesJson)) {
        $fsum = Get-Content -LiteralPath $framesJson -Raw | ConvertFrom-Json
    } else { $problems.Add("frame_summary.py failed (exit $fsCode): $($fsOut.Trim())") }
} else { $problems.Add("no $csvName") }

# Light phase (INSTALL marker in all game*.log), first frame to window, and the run flags (session 3).
$inst = Get-InstallMarker $run
$shareLight = $null; $shareBins = $null
if ($fsum -and $fsum.PSObject.Properties['share_lt_light']) { $shareLight = $fsum.share_lt_light }
if ($fsum -and $fsum.PSObject.Properties['share_lt_light_bins_10s']) { $shareBins = $fsum.share_lt_light_bins_10s }
$lightPhase = $null
if ($null -ne $inst.install_dat_fail -and $inst.boot_lines_found) { $lightPhase = $inst.install_dat_fail -lt 30 }
$light = [ordered]@{ install_lines = $inst.install_lines; install_dat_fail = $inst.install_dat_fail; boot_lines_found = $inst.boot_lines_found
                     log_files = $inst.files; error = $inst.error; light_ms = $LightMs; share_lt_light = $shareLight
                     share_lt_light_bins_10s = $shareBins; light_phase = $lightPhase
                     rule = 'light_phase = install_dat_fail < 30 (a normal boot has 34; needs the boot lines); light_share_high = share_lt_light >= 0.6 (info)' }
$ffToWin = $null
if ($null -ne $ffQpc -and $null -ne $mStart) { $ffToWin = [math]::Round(($mStart.qpc - $ffQpc) / [double]$qpcFreq, 2) }
$onTimingDesk = Test-TimingDesktop $desk
$flagsEx = New-Object System.Collections.Generic.List[string]
$flagsInfo = New-Object System.Collections.Generic.List[string]
if ($lightPhase -eq $true) { $flagsEx.Add('light_phase') }
if ($null -eq $lightPhase) { $flagsInfo.Add('install_marker_lost') }
if ($null -ne $shareLight -and $shareLight -ge 0.6 -and $lightPhase -ne $true) { $flagsInfo.Add('light_share_high') }
if ($MinWindowAfterFirstFrame -gt 0 -and $null -ne $mStart -and ($null -eq $ffToWin -or $ffToWin -lt ($MinWindowAfterFirstFrame - 0.5))) { $flagsEx.Add('window_before_floor') }
if ($ticksSkippedWin -gt 0) { $flagsInfo.Add('ticks_skipped') }
if ($bpWarm.Count) { $flagsInfo.Add('build_procs_warmup') }
if ($bpWin.Count) { $flagsInfo.Add('build_procs_window') }
$sysExcluding = @('input_during_window', 'not_foreground', 'on_battery', 'battery_saver', 'power_change', 'desktop_not_default', 'screensaver')
if ($SysCsv) {
    if ($null -ne $sysSum -and $sysSum.PSObject.Properties['flags']) {
        foreach ($sf0 in @($sysSum.flags)) {
            $sfName = [string]$sf0
            if ($sfName -eq 'not_foreground' -and $sysSum.window.fg_game_share -eq 0) { $sfName = 'never_foreground' }
            if ($onTimingDesk -and $sysExcluding -contains $sfName) { $flagsEx.Add($sfName) } else { $flagsInfo.Add($sfName) }
        }
    } else { $flagsInfo.Add('sys_missing') }
}
$excluded = $flagsEx.Count -gt 0

# Verdict.
if ($bootTimedOut) { $problems.Add("NO FIRST FRAME within $BootTimeoutSec s ($csvName never grew past its header)") }
if ($exitedEarly) { $problems.Add("PROCESS EXITED during $exitedPhase at $exitedAt s (exit $(if ($null -ne $code) { '0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL) } else { '?' }))") }
if ($stalled) { $problems.Add("FRAMES CSV STALLED: no growth for >= $StallSec s at $stallAt s (max $([math]::Round($maxNoGrowWin, 1)) s)") }
if ($notRespondingWin -gt 0) { $problems.Add("NOT RESPONDING in $notRespondingWin window samples") }
if ($close -and $close.killed) { $problems.Add("KILLED: no exit $CloseTimeoutSec s after WM_CLOSE") }
if ($close -and -not $close.exited) { $problems.Add("PROCESS STILL RUNNING after WM_CLOSE + kill$(if ($close.kill_error) { ": $($close.kill_error)" })") }
if ($close -and -not $close.killed -and $close.wm_close_posted -eq 0) { $problems.Add('no window got WM_CLOSE') }
if ($null -ne $code -and $code -ne 0) { $problems.Add("exit code $('0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL))") }
if ($dialogs.Count -gt 0) { $problems.Add("dialogs: $($dialogs -join ' | ')") }
if ($werSeen) { $problems.Add('WerFault seen') }
# Dumps named <exe>.<pid>.dmp of another process (or another pid) are foreign: listed, not a problem.
$ownArt = New-Object System.Collections.Generic.List[string]; $foreignArt = New-Object System.Collections.Generic.List[string]
foreach ($artItem in @($artifacts)) {
    $artBase = [IO.Path]::GetFileName([string]$artItem)
    if ($artBase -match '^(?<exe>.+?)\.(?<pid>\d+)\.dmp$' -and ($Matches['exe'] -ne 'legodimensions.exe' -or [int64]$Matches['pid'] -ne [int64]$gamePid)) { $foreignArt.Add([string]$artItem) }
    else { $ownArt.Add([string]$artItem) }
}
if ($ownArt.Count -gt 0) { $problems.Add("crash artifacts: $($ownArt -join ', ')") }
if ($foreignArt.Count -gt 0) { "note: foreign crash dumps (not this game): $($foreignArt -join ', ')" }
if ($null -eq $mStart -and -not $bootTimedOut) { $problems.Add('NO MEASURE WINDOW (did not reach the end of the warm-up)') }
if ($drvInfo) {
    if ($drvInfo.error) { $problems.Add("driver did not start: $($drvInfo.error)") }
    elseif ($drvInfo.killed) { $problems.Add("DRIVER KILLED: still running $DriverTimeoutSec s after the window") }
    elseif ($null -ne $drvInfo.exit_code -and $drvInfo.exit_code -ne 0) { $problems.Add("driver exit $($drvInfo.exit_code)") }
}
if ($fsum) {
    if ($fsum.frames -eq 0) { $problems.Add('NO FRAMES in the window') }
    elseif ($fsum.window.short) { $problems.Add("SHORT WINDOW: only $($fsum.window_s) s of frames after the start mark") }
    if (-not $fsum.header_ok) { $problems.Add("$csvName header unexpected") }
}
if ($profiling) { $problems.Add('PROFILE ONLY, NOT FOR TIMING') }
$status = if ($problems.Count -eq 0) { 'OK' } elseif ($profiling -and $problems.Count -eq 1) { 'PROFILE' } else { 'PROBLEM' }

# Timing validity of the environment (interactive desktop, no lock screen, no builds at the window marks).
$validWhy = New-Object System.Collections.Generic.List[string]
if ($profiling) { $validWhy.Add('profiler on') }
if (-not (Test-TimingDesktop $desk)) { $validWhy.Add("desktop $desk is not WinSta0\Default") }
if ($null -eq $envAtStart -or $null -eq $envAtEnd) { $validWhy.Add('no complete window') }
if (($null -ne $envAtStart -and $envAtStart.logonui) -or ($null -ne $envAtEnd -and $envAtEnd.logonui)) { $validWhy.Add('LogonUI running (locked?)') }
$bp = @(); if ($null -ne $envAtStart) { $bp += $envAtStart.build_procs }; if ($null -ne $envAtEnd) { $bp += $envAtEnd.build_procs }; $bp += @($bpWin.Keys)
$bp = @($bp | Where-Object { $_ } | Sort-Object -Unique)
if ($bp.Count) { $validWhy.Add("build processes: $($bp -join ' ')") }
$validTiming = $validWhy.Count -eq 0

$winCpuMean = $null; $winCpuMax = $null; $winWall = $null
if ($mStart -and $mEnd) {
    $winWall = ($mEnd.qpc - $mStart.qpc) / [double]$qpcFreq
}
if ($winCores.Count -gt 0) {
    $winCpuMean = ($winCores | Measure-Object -Average).Average
    $winCpuMax = ($winCores | Measure-Object -Maximum).Maximum
}

# summary.txt
$L = New-Object System.Collections.Generic.List[string]
$L.Add("=== run-timing summary [$mode] status $status ===")
$L.Add("run      $run")
$L.Add("bin      $(Resolve-RepoPath $BinDir); tag $Tag; warm-up $Warmup s from $WarmupFrom; window $Seconds s; frames $csvName; logical CPUs $ncpu")
$L.Add("cvars    $($Cvar -join ' ')")
$L.Add("env      $(($envH.Keys | Sort-Object | ForEach-Object { "$_=$($envH[$_])" }) -join ' ')")
$L.Add("toml     $(($tomlH.Keys | Sort-Object | ForEach-Object { "$_ = $($tomlH[$_])" }) -join '; ')")
if ($seed) { $L.Add("seed     $(($seed.files | ForEach-Object { "$($_.name) $($_.bytes) B sha256 $($_.sha256.Substring(0, 12))" }) -join '; ') from $seedSrc") }
$L.Add("boot     first frame signal at $(if ($null -ne $firstFrameS) { "$firstFrameS s" } else { 'NEVER' })$(if ($fromFirst -and $null -ne $warmStartT) { "; warm-up started at $warmStartT s (settle $SettleSec s$(if ($MenuText) { ", menu $MenuSec s from $menuAt s" }))" })")
$L.Add("floor    first-frame signal to the start mark $(if ($null -ne $ffToWin) { "$ffToWin s" } else { '-' }) (floor $MinWindowAfterFirstFrame s$(if ($floorNote) { "; $floorNote" })); runner ticks skipped $ticksSkipped ($ticksSkippedWin in the window); build-tool checks $bpChecks$(if ($bpWarm.Count) { "; warm-up: $(@($bpWarm.Keys | Sort-Object) -join ' ')" })$(if ($bpWin.Count) { "; window: $(@($bpWin.Keys | Sort-Object) -join ' ')" })")
$L.Add("phase    INSTALL lines $(if ($null -ne $inst.install_lines) { $inst.install_lines } else { '-' }), INSTALL*.DAT fails $(if ($null -ne $inst.install_dat_fail) { $inst.install_dat_fail } else { '-' }) ($(@($inst.files) -join ', ')$(if (-not $inst.boot_lines_found) { '; BOOT LINES NOT FOUND' })$(if ($inst.error) { "; $($inst.error)" })); window share < $LightMs ms $(if ($null -ne $shareLight) { Fmt $shareLight 3 } else { '-' }); $(if ($lightPhase -eq $true) { 'LIGHT PHASE (excluded)' } elseif ($lightPhase -eq $false) { 'normal phase' } else { 'phase unknown' })")
$L.Add("timing   $(if ($validTiming) { 'VALID environment (WinSta0\Default, no LogonUI, no build processes at the window marks or in the 5 s checks)' } else { 'FUNCTIONAL ONLY: ' + ($validWhy -join '; ') })")
if ($SysCsv) {
    if ($null -ne $sysSum -and $sysSum.PSObject.Properties['summary']) { $L.Add("sys      $($sysSum.summary)") } else { $L.Add("sys      MISSING: $sysErr") }
    if ($sysInfo) { $L.Add("sampler  pid $($sysInfo.pid) exit $($sysInfo.exit_code)$(if ($sysInfo.killed) { ' KILLED' })$(if ($sysInfo.error) { " error: $($sysInfo.error)" }); $($sysInfo.stop_line)") }
}
$L.Add("flags    $(if ($excluded) { 'EXCLUDED: ' + ($flagsEx -join ', ') } else { 'no excluding flag' })$(if ($flagsInfo.Count) { '; info: ' + ($flagsInfo -join ', ') })")
if ($foreignArt.Count) { $L.Add("note     foreign crash dumps (not this game, not a problem): $($foreignArt -join ', ')") }
if ($profiling) { $L.Add('!!! PROFILE ONLY, NOT FOR TIMING: the frame numbers below are not timing results') }
if ($fsum -and $fsum.frames -gt 0) {
    $w = $fsum.window
    $L.Add("frames   $($fsum.frames) frames over $(Fmt $fsum.window_s 3) s (summed frame times) = $(Fmt $fsum.mean_fps 2) fps mean")
    $L.Add("frame ms median $(Fmt $fsum.median_ms 3)$(if ($fsum.PSObject.Properties['p95_ms']) { "  p95 $(Fmt $fsum.p95_ms 3)" })  p99 $(Fmt $fsum.p99_ms 3)  p99.9 $(Fmt $fsum.p99_9_ms 3)  max $(Fmt $fsum.max_ms 3)  >33 ms $($fsum.over_33ms)  >100 ms $($fsum.over_100ms)  (nearest-rank)")
    $sb0 = if ($mStart) { "$($mStart.perf_csv_bytes) B" } else { 'NO START MARK: whole file' }
    $L.Add("window   $csvName rows $($w.first_row)..$($w.first_row + $w.rows - 1): start = rows on disk at the start mark ($sb0), end by $($w.end_by)$(if ($w.short) { ' (SHORT)' }); $($w.zero_rows) zero rows left out")
    if ($null -ne $w.rows_by_end_bytes) {
        $L.Add("align    rows on disk by the end mark: $($w.rows_by_end_bytes) ($($mEnd.perf_csv_bytes) B) vs $($w.rows) by the seconds cut: $('{0:+0;-0;0}' -f $w.end_bytes_minus_seconds_rows) rows; wall between marks $(Fmt $winWall 3) s. Each mark lags the true frame by the unflushed rows (perf.csv: 0-59, 60-row flush), so expect |diff| <= 59 plus jitter.")
    }
} elseif ($fsum) {
    $L.Add("frames   NONE in the window ($csvName $($fsum.rows_total) rows, $($fsum.file_bytes) B)")
}
if ($null -ne $winCpuMean) {
    $L.Add("process  window cpu mean $(Fmt $winCpuMean 2) cores, max $(Fmt $winCpuMax 2) cores (1 s samples, $($winCores.Count)); peak working set $(Fmt ($winPeakWs / 1MB) 0) MB, peak commit $(Fmt ($winPeakCommit / 1MB) 0) MB (window samples); lifetime peaks $(Fmt ($lifePeakWs / 1MB) 0) / $(Fmt ($lifePeakCommit / 1MB) 0) MB")
}
if ($drvInfo) { $L.Add("driver   $($drvInfo.path): exit $($drvInfo.exit_code)$(if ($drvInfo.killed) { ' KILLED' }); output driver.out.txt / driver.err.txt") }
if ($mTriggers.Count) { $L.Add("triggers $(($mTriggers | ForEach-Object { "$($_.path) at $($_.t_s) s$(if ($_.error) { " ERROR $($_.error)" })$(if ($_.exists_after_run) { ' (still there after the run)' })" }) -join '; ')") }
if ($close) { $L.Add("close    WM_CLOSE posted to $($close.wm_close_posted) window(s) at $($close.wm_close_post_wall), exit seen after $($close.exit_seen_s) s, killed $($close.killed)$(if ($close.kill_error) { ", kill error: $($close.kill_error)" }), exit $($close.exit_code_hex)") }
else { $L.Add("close    process exited by itself at $exitedAt s, exit $(if ($null -ne $code) { '0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL) } else { '?' })") }
if ($Profile) { $L.Add("profile  $(if ($profiles.Count) { $profiles -join ', ' } else { 'NO profile-*.bin written' }); meta $(Join-Path $run 'profile-meta.json')") }
foreach ($pr in $problems) { $L.Add("!!! $pr") }
$L | Set-Content -LiteralPath (Join-Path $run 'summary.txt') -Encoding utf8

$runJson = [ordered]@{
    mode = $mode; status = $status; problems = $problems.ToArray()
    valid_timing = $validTiming; valid_timing_why = $validWhy.ToArray()
    run = $run; bin_dir = (Resolve-RepoPath $BinDir); tag = $Tag
    runner_error = $runErr; measure_triggers = $mTriggers.ToArray(); placeholder_run = $run
    params = [ordered]@{ warmup_s = $Warmup; seconds = $Seconds; cvar = $cvarRaw; env = $envItems; toml = $tomlItems; trigger_at_measure = $trigRaw
                         close_timeout_s = $CloseTimeoutSec; min_free_ram_gb = $MinFreeRamGB; profile = [bool]$Profile
                         profile_seconds = $ProfileSeconds; runs_root = $RunsRoot; stall_s = $StallSec
                         warmup_from = $WarmupFrom; boot_timeout_s = $BootTimeoutSec; settle_s = $SettleSec
                         menu_text = $MenuText; menu_s = $MenuSec; driver = $Driver; driver_args = $drvArgItems
                         driver_timeout_s = $DriverTimeoutSec; frames = $Frames; seed_cache = $SeedCache; seed_recipes_only = [bool]$SeedRecipesOnly
                         sys_csv = [bool]$SysCsv; min_window_after_ff_s = $MinWindowAfterFirstFrame; light_ms = $LightMs; warmup_requested_s = $warmupAsked }
    args = $gameArgs; env_set = $envH; toml_set = $tomlH
    frames_csv = $csvPath; frames_csv_header_bytes = $headerBytes
    first_frame_signal_s = $firstFrameS; boot_s = $firstFrameS; no_first_frame = $bootTimedOut
    menu_prompt_at_s = $menuAt; warmup_start_s = $warmStartT
    qpc_frequency = $qpcFreq; process_start_mark = $startMark; measure_start = $mStart; measure_end = $mEnd
    window_wall_s = $winWall
    timing_env = [ordered]@{ desktop = $desk; at_measure_start = $envAtStart; at_measure_end = $envAtEnd }
    start = $start.ToString('yyyy-MM-dd HH:mm:ss.fff'); end = $end.ToString('yyyy-MM-dd HH:mm:ss.fff')
    pid = $gamePid; exited_early = $exitedEarly; exited_at_s = $exitedAt; exited_phase = $exitedPhase
    close = $close; exit_code = $code
    exit_code_hex = $(if ($null -ne $code) { '0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL) } else { $null })
    window_cpu_cores_mean = $winCpuMean; window_cpu_cores_max = $winCpuMax; window_cpu_samples = $winCores.Count
    window_peak_ws_mb = [math]::Round($winPeakWs / 1MB, 0); window_peak_commit_mb = [math]::Round($winPeakCommit / 1MB, 0)
    lifetime_peak_ws_mb = [math]::Round($lifePeakWs / 1MB, 0); lifetime_peak_commit_mb = [math]::Round($lifePeakCommit / 1MB, 0)
    not_responding_samples = $notResponding; not_responding_window_samples = $notRespondingWin
    perf_csv_stalled = $stalled; perf_csv_stall_at_s = $stallAt; perf_csv_max_no_growth_window_s = $maxNoGrowWin
    dialogs = $dialogs.ToArray(); werfault_seen = $werSeen; windows_at_end = $windowDesc; artifacts = $artifacts
    log_lines = $logC.Lines; free_ram_gb_at_start = $free0; logical_cpus = $ncpu
    seed_cache = $seed; driver = $drvInfo
    profile_trigger_on = $trigOn; profile_trigger_off = $trigOff; profiles = $profiles; profile_meta = $profileMeta
    frames = $fsum
    ff_signal_epoch_s = $ffEpoch; ff_to_window_s = $ffToWin; min_window_after_ff_s = $MinWindowAfterFirstFrame; warmup_raised = $floorNote
    ticks_skipped = $ticksSkipped; ticks_skipped_window = $ticksSkippedWin
    build_procs_window = @($bpWin.Keys | Sort-Object); build_procs_warmup = @($bpWarm.Keys | Sort-Object); build_proc_checks = $bpChecks
    light = $light; sys = $sysSum; sys_sampler = $sysInfo; sys_error = $sysErr
    flags = @(@($flagsEx) + @($flagsInfo)); flags_excluding = $flagsEx.ToArray(); flags_info = $flagsInfo.ToArray(); excluded = $excluded
    foreign_crash_dumps = $foreignArt.ToArray(); on_timing_desktop = $onTimingDesk
    runner_session = (Get-Process -Id $PID).SessionId
    logonui_running = [bool](Get-Process LogonUI -ErrorAction SilentlyContinue)
}
$runJson | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $run 'run.json') -Encoding utf8
''
$L
if ($status -eq 'PROBLEM') { exit 1 }
exit 0
