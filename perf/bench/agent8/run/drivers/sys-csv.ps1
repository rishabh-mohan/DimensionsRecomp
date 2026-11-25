# sys-csv.ps1 - 1 s system-state log of the machine around a timing run: <RunDir>\sys.csv (Agent 8 helper, 2026-11-22).
# Started by run-timing.ps1 right after the game starts:
#   Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput <run>\sys.out.txt -RedirectStandardError <run>\sys.err.txt
#     -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',<this file>,'-GamePid',<pid>,'-RunDir',<run>
# Params: -GamePid <int> (required), -RunDir <existing dir> (required), -IntervalMs 1000, -MaxSec 3600,
#         -StopFile (default <RunDir>\sys.stop), -Out (default <RunDir>\sys.csv),
#         -ProcEvery 5 (2026-11-25: per-process snapshot every N ticks, 0 = off). New trailing sys.csv columns:
#         nongame_cores / game_cores (every row: GetSystemTimes busy cores minus the game's GetProcessTimes cores),
#         proc_nongame_cores, nongame_io_MBps, top_cpu "name:pid:cores;..." (top 5), top_io "name:pid:MBps;..." (top 3)
#         (snapshot rows only: one NtQuerySystemInformation(SystemProcessInformation) call, ~11 ms CPU), disk_MBps (every
#         row: PDH \PhysicalDisk(_Total)\Disk Bytes/sec, MB = 1e6 bytes).
# The sampling runs inside C# (LdSys.cs, compiled once to build\agent8\cache\LdSys-<sha256[0:8] of LdSys.cs>.dll, then
# only loaded): one row per tick on a Stopwatch schedule (tick k due at t0 + k*interval; a tick late by more than one
# interval is skipped and counted, no catch-up burst). Between ticks it waits on the game process handle and on a change
# notification of the stop file's folder, so a game exit or a new stop file is seen within milliseconds; the stop file is
# also checked once per tick (fallback when the notification is unavailable: waits of <= 250 ms, check at every wake).
# No child process, no window, read-only queries only (the one-time compile runs csc.exe via Add-Type, exactly like
# thread-cpu.ps1 does for LdNvml).
# Stops when the game exits (writes one last off-grid row with game_alive=0), when the stop file appears, or after
# -MaxSec (counted from the first tick). A stop file older than this process (left over from an earlier run) is deleted
# at start; one created after the start stops the driver. sys.csv: UTF-8 without BOM, CRLF, header first, flushed after
# every row, opened with FileShare.ReadWrite|Delete (read it with FileShare.ReadWrite while it runs).
# stdout (Say format "HH:mm:ss.fff +S.SSs msg"): "sys-csv: start ..." with the counter inventory, "sys-csv: timing ..."
# and as the LAST line "sys-csv: stop reason=<game_exit|stop_file|max_sec> rows=<n> skipped=<n> cpu_s=<own CPU s>
# wall_s=<own wall s> ...". cpu_s / loop_cpu_s come from GetProcessTimes (15.6 ms clock-tick sampled, includes the
# powershell.exe startup); cpu_cyc_s / loop_cyc_cpu_pct / steady_cpu_pct come from the cycle counters (QueryProcessCycleTime
# / TSC rate = tsc_mhz) and are the precise numbers. stderr: notes about partial failures (one per kind; a missing counter
# = blank cells).
# Exit: 0 any normal stop (also: game pid not running at start -> header only, reason game_exit); 1 init failure
# (compile/load failed, no PDH counter at all, sys.csv not creatable, unexpected error in the loop); 2 bad arguments.
# Uses .NET calls instead of cmdlets of the auto-loaded Utility / Management modules (shorter launch -> first row).
param(
    [string]$GamePid = '',
    [string]$RunDir = '',
    [string]$IntervalMs = '1000',
    [string]$MaxSec = '3600',
    [string]$StopFile = '',
    [string]$Out = '',
    [string]$ProcEvery = '5'
)
$q0 = [Diagnostics.Stopwatch]::GetTimestamp()   # t_s origin = script start (same origin as the +S.SSs of Say)
$sw = [Diagnostics.Stopwatch]::StartNew()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$inv = [Globalization.CultureInfo]::InvariantCulture
$stdout = [Console]::Out
function Say([string]$M) {
    $stdout.WriteLine([string]::Format($inv, '{0} +{1:0.00}s {2}', [DateTime]::Now.ToString('HH:mm:ss.fff', $inv), $sw.Elapsed.TotalSeconds, $M))
    $stdout.Flush()
}
function Note([string]$M) { try { [Console]::Error.WriteLine('sys-csv: ' + $M); [Console]::Error.Flush() } catch { } }
function Bad([string]$M) { Say "sys-csv: bad args: $M"; Note "bad args: $M"; exit 2 }
function F3([double]$X) { return $X.ToString('0.000', $inv) }
function Full([string]$P) { return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($P) }

# ---- arguments (all strings, so a bad value is exit 2 and not a PowerShell binding error) ----
if ($args.Count) { Bad "unexpected argument(s): $($args -join ' ')" }
$pidN = 0
if (-not [int]::TryParse($GamePid.Trim(), [Globalization.NumberStyles]::None, $inv, [ref]$pidN) -or $pidN -le 0) { Bad "-GamePid '$GamePid' (need a positive integer)" }
if (-not $RunDir.Trim()) { Bad "-RunDir missing (need an existing directory)" }
$rd = ''
try { $rd = Full $RunDir } catch { Bad "-RunDir '$RunDir' ($($_.Exception.Message))" }
if (-not [IO.Directory]::Exists($rd)) { Bad "-RunDir '$RunDir' (need an existing directory)" }
$RunDir = $rd
$ivMs = 0
if (-not [int]::TryParse($IntervalMs.Trim(), [Globalization.NumberStyles]::None, $inv, [ref]$ivMs) -or $ivMs -lt 100 -or $ivMs -gt 600000) { Bad "-IntervalMs '$IntervalMs' (100..600000)" }
$maxS = 0.0
if (-not [double]::TryParse($MaxSec.Trim(), [Globalization.NumberStyles]::Float, $inv, [ref]$maxS) -or -not ($maxS -gt 0) -or $maxS -gt 1e7) { Bad "-MaxSec '$MaxSec' (> 0)" }
$procN = 0
if (-not [int]::TryParse($ProcEvery.Trim(), [Globalization.NumberStyles]::None, $inv, [ref]$procN) -or $procN -lt 0 -or $procN -gt 3600) { Bad "-ProcEvery '$ProcEvery' (0..3600)" }
$outPath = ''; $stopPath = ''
try {
    $outPath = if ($Out) { Full $Out } else { [IO.Path]::Combine($RunDir, 'sys.csv') }
    $stopPath = if ($StopFile) { Full $StopFile } else { [IO.Path]::Combine($RunDir, 'sys.stop') }
} catch { Bad "-Out / -StopFile: $($_.Exception.Message)" }
foreach ($f in @($outPath, $stopPath)) {
    $d = [IO.Path]::GetDirectoryName($f)
    if (-not $d -or -not [IO.Directory]::Exists($d)) { Bad "no directory for '$f'" }
}

# ---- LdSys: compile once into build\agent8\cache (content key), afterwards only load ----
$dllHow = ''; $dllName = ''
try {
    $cs = [IO.Path]::Combine($PSScriptRoot, 'LdSys.cs')
    # repo root = the nearest ancestor that holds build\agent8 (bench\agent8\run\drivers -> 4 up; also works from a staged copy)
    $repo = [IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot, '..\..\..\..'))
    $up = [IO.Directory]::GetParent($PSScriptRoot)
    while ($up) { if ([IO.Directory]::Exists([IO.Path]::Combine($up.FullName, 'build\agent8'))) { $repo = $up.FullName; break }; $up = $up.Parent }
    $cacheDir = [IO.Path]::Combine($repo, 'build\agent8\cache')
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $hash = $sha.ComputeHash([IO.File]::ReadAllBytes($cs)) } finally { $sha.Dispose() }
    $key = [BitConverter]::ToString($hash, 0, 4).Replace('-', '').ToLowerInvariant()
    $dll = [IO.Path]::Combine($cacheDir, "LdSys-$key.dll")
    $dllName = [IO.Path]::GetFileName($dll)
    if ([IO.File]::Exists($dll)) { $dllHow = 'cached' }
    else {
        [void][IO.Directory]::CreateDirectory($cacheDir)
        $tmp = [IO.Path]::Combine($cacheDir, ('LdSys-{0}.{1}.tmp.dll' -f $key, $PID))
        $c0 = $sw.Elapsed.TotalSeconds
        Add-Type -Path $cs -OutputAssembly $tmp -OutputType Library
        try { [IO.File]::Move($tmp, $dll); $dllHow = 'compiled' }
        catch {
            if (-not [IO.File]::Exists($dll)) { throw }
            $dllHow = 'compiled-lost-race'                  # another driver renamed its copy first: use that one
            try { [IO.File]::Delete($tmp) } catch { }
        }
        Say ('sys-csv: compiled {0} in {1} s ({2})' -f $dllName, (F3 ($sw.Elapsed.TotalSeconds - $c0)), $dllHow)
    }
    if (-not ('LdSys' -as [type])) { [void][Reflection.Assembly]::LoadFrom($dll) }
    if (-not ('LdSys' -as [type])) { throw "type LdSys not found after loading $dll" }
} catch {
    Say "sys-csv: init failed: LdSys compile/load: $($_.Exception.Message)"
    Note "init failed: LdSys compile/load: $($_.Exception.Message)"
    exit 1
}

# ---- stale stop file: older than this process = left over -> delete; newer = a real stop request ----
$stale = ''
try {
    if ([IO.File]::Exists($stopPath)) {
        $fi = [IO.FileInfo]::new($stopPath)
        $me = [LdSys]::OwnStartUtc()
        $ft = if ($fi.LastWriteTimeUtc -gt $fi.CreationTimeUtc) { $fi.LastWriteTimeUtc } else { $fi.CreationTimeUtc }
        if ($ft -lt $me) { [IO.File]::Delete($stopPath); $stale = ' stale_stop_file=removed' }
        else { $stale = ' stop_file_present_at_start=1' }
    }
} catch { $stale = ' stale_stop_file=not_removed'; Note "stale stop file not removed: $($_.Exception.Message)" }

# ---- init: game handle, power poller, CPU sets, PDH counters (+ the first collect) ----
try { [LdSys]::ProcEvery = $procN; [LdSys]::Init($pidN, $ivMs) } catch {
    Say "sys-csv: init failed: $($_.Exception.Message)"; Note "init failed: $($_.Exception.Message)"; exit 1
}
$L = [LdSys]
if ($L::GameGone) {
    Say ([string]::Format($inv, 'sys-csv: start pid={0} game_running=0 (gone before the first sample) dll={1}({2}) out={3} stop_file={4}{5}',
        $pidN, $dllName, $dllHow, $outPath, $stopPath, $stale))
} else {
    if ($L::CountersOk -eq 0) {
        Say "sys-csv: init failed: no PDH counter could be opened ($($L::Failed))"; Note "init failed: no PDH counter could be opened ($($L::Failed))"; exit 1
    }
    if ($L::Failed) { Note "counters failed at init: $($L::Failed)" }
    Say ([string]::Format($inv, 'sys-csv: start pid={0} interval_ms={1} max_s={2} dll={3}({4}) init_ms={5:0} init_parts_ms=[{6}] P=[{7}] E=[{8}] classes={9} lp_freq=[{10}] tz=[{11}] counters={12}/{13} failed=[{14}] overlay_api={15} game_wait={16} own_desktop={17} input_desktop={18} out={19} stop_file={20}{21} proc=[{22}]',
        $pidN, $ivMs, $maxS, $dllName, $dllHow, $L::InitMs, $L::InitParts, $L::PList, $L::EList, $L::ClassInfo, $L::LpFreq, $L::Zones,
        $L::CountersOk, $L::CountersTotal, $L::Failed, [int]$L::OverlayApi, $(if ($L::GamePolled) { 'poll' } else { 'handle' }),
        $L::OwnDesktop, $L::InputDesktopAtInit, $outPath, $stopPath, $stale, $L::ProcInfo))
}

# ---- the loop (blocking, inside C#) ----
try { [LdSys]::Run($outPath, $stopPath, $ivMs, $maxS, $q0) } catch {
    $m = $_.Exception.Message
    if ($_.Exception.InnerException) { $m = $_.Exception.InnerException.Message }
    Note "sampling failed: $m"
    Say ([string]::Format($inv, 'sys-csv: stop reason=error rows={0} skipped={1} cpu_s={2} wall_s={3} error={4}',
        $L::Rows, $L::Skipped, (F3 ($L::OwnCpuS())), (F3 ($L::OwnWallS())), ($m -replace '\s+', '_')))
    exit 1
}
$cpu = $L::OwnCpuS(); $wall = $L::OwnWallS(); $cyc = $L::OwnCpuCycS()
Say ([string]::Format($inv, 'sys-csv: timing first_sample_ms={0} sample_ms={1} sample_ms_max={2} sample_cpu_ms={3} parts_first_ms=[{4}] parts_mean_ms=[{5}] parts_max_ms=[{6}] parts_cpu_first_ms=[{7}] parts_cpu_mean_ms=[{8}] {9} stop_watch={10} wakes={11} stop_checks={12} steady_cpu_pct_by_thread=[{13}] proc_snaps={14} proc_fails={15} procs={16} {17}',
    (F3 $L::FirstSampleMs), (F3 $L::SampleMsMean), (F3 $L::SampleMsMax), $L::SampleCpuMs(), $L::PartsFirstMs(), $L::PartsMeanMs(), $L::PartsMaxMs(),
    $L::PartsCpuFirstMs(), $L::PartsCpuMeanMs(), $L::PollStats(), $L::StopWatch, $L::Wakes, $L::StopChecks, $L::SteadyByThread, $L::ProcSnaps, $L::ProcFails, $L::ProcCount, $L::ProcStats()))
Say ([string]::Format($inv, 'sys-csv: stop reason={0} rows={1} skipped={2} cpu_s={3} wall_s={4} cpu_pct={5} cpu_cyc_s={6} loop_s={7} loop_cpu_s={8} loop_cpu_pct={9} loop_cyc_cpu_pct={10} steady_cpu_pct={11} tsc_mhz={12} sample_ms={13} sample_ms_max={14} first_row_s={15} first_row_t_s={16}',
    $L::Reason, $L::Rows, $L::Skipped, (F3 $cpu), (F3 $wall), (F3 $(if ($wall -gt 0) { $cpu / $wall * 100 } else { 0 })), (F3 $cyc),
    (F3 $L::LoopS), (F3 $L::LoopCpuS), (F3 $(if ($L::LoopS -gt 0) { $L::LoopCpuS / $L::LoopS * 100 } else { 0 })), (F3 $L::LoopCycCpuPct),
    (F3 $L::SteadyCpuPct), $L::TscMhz, (F3 $L::SampleMsMean), (F3 $L::SampleMsMax), (F3 $L::FirstRowS), (F3 $L::FirstRowT)))
exit 0
