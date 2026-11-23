# Functional boot of a staged bin dir (task #16 step 1). Untimed: judge by the log and the process.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\first-boot.ps1 [-BinDir build\baseline-bin] [-Tag first] [-WatchSeconds 300] [-Cvar name=value] [-Env 'NAME=value;...'] [-StopWhenUnlocked]
# Mirrors <BinDir> into build\agent8\runs\<HHmm>-<Tag>, writes the toml with user_data_root = <run>\user,
# starts the game with the verified flags, samples the process every 1 s for -WatchSeconds (proc.csv),
# then WM_CLOSE, kill after -CloseTimeoutSec, and collects dumps / WER / events. Writes run.json.
# No SendInput, no screenshots. Does not start if free RAM < -MinFreeRamGB (exit 3).
# The game holds perf.csv open without read sharing, so the sampler records its SIZE (perf_csv_bytes);
# boot_report.py maps sizes to rows from the final file. The game is started with Start-Process, so it
# does not inherit this script's console/pipe handles, and a finally block closes it if the script fails.
param(
    [string]$BinDir = 'build\baseline-bin',
    [string]$Tag = 'first',
    [int]$WatchSeconds = 300,
    [int]$CloseTimeoutSec = 30,
    [double]$MinFreeRamGB = 6.0,
    [string[]]$Cvar = @(),
    [string]$Env = '',              # 'NAME=value;NAME2=value2' for the game; '<run>' expands to the run dir
    [switch]$StopWhenUnlocked,      # start only while the desktop is locked (LogonUI), and end the watch early once it unlocks
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\common.ps1"
. "$PSScriptRoot\timing-env.ps1"   # Get-BuildProcs: the same build-tool list as run-timing / run-matrix
Import-LdHelper

$free0 = Get-FreeRamGB
$run = New-RunDir -BinDir $BinDir -Tag $Tag
Write-RunToml -Run $run
$gameArgs = Get-GameArgs -Run $run -Cvar $Cvar
"run dir: $run"
"args: $($gameArgs -join ' ')"
"free RAM: $free0 GB"
function Test-DesktopLocked { [bool](Get-Process LogonUI -ErrorAction SilentlyContinue) }
$envSet = [ordered]@{}
foreach ($kv in ($Env -split ';')) {
    $kv = $kv.Trim()
    if (-not $kv) { continue }
    $i = $kv.IndexOf('=')
    if ($i -lt 1) { "bad -Env entry '$kv' (want NAME=value)"; exit 2 }
    $envSet[$kv.Substring(0, $i).Trim()] = $kv.Substring($i + 1).Replace('<run>', $run)
}
if ($envSet.Count -gt 0) { 'env: ' + (($envSet.Keys | ForEach-Object { "$_=$($envSet[$_])" }) -join ' ') }
if ($DryRun) { 'dry run: not starting'; exit 0 }
if ($free0 -lt $MinFreeRamGB) { "free RAM $free0 GB is under $MinFreeRamGB GB: not starting"; exit 3 }
if ($StopWhenUnlocked -and -not (Test-DesktopLocked)) { 'the desktop is unlocked (no LogonUI), so the user may start a timing matrix: not starting'; exit 5 }

$ncpu = [Environment]::ProcessorCount
$logC = New-LineCounter (Join-Path $run 'game.log')
$csvFi = New-Object IO.FileInfo (Join-Path $run 'perf.csv')
$procCsv = Join-Path $run 'proc.csv'
# Shared-read writer: readers never make a write fail.
$fs = New-Object IO.FileStream($procCsv, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite)
$writer = New-Object IO.StreamWriter($fs, (New-Object Text.UTF8Encoding $false))
$writer.AutoFlush = $true
# cpu_pct_machine is the GAME's CPU as a share of all logical CPUs (cpu_cores / ncpu), NOT machine load.
# sys_busy_pct is the whole machine (GetSystemTimes); other_cores = machine busy cores - game cores (builds,
# other agents, this sampler); build_procs = running build / codegen tools (timing-env.ps1 Get-BuildProcs) every 5 s.
$writer.WriteLine('t_s,alive,cpu_pct_machine,cpu_cores,cpu_s,ws_mb,peak_ws_mb,commit_mb,peak_commit_mb,threads,handles,responding,log_lines,log_bytes,perf_csv_bytes,free_ram_gb,windows,sys_busy_pct,other_cores,build_procs,note')

foreach ($k in @('LEGO_SAMPLE_PROFILE', 'LEGO_SAMPLE_PROFILE_TRIGGER')) { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
foreach ($k in $envSet.Keys) { Set-Item -Path "Env:$k" -Value $envSet[$k] }   # Start-Process hands this environment to the game
# Machine-wide CPU and build processes, so slow stretches can be laid against other load.
$buildNames = 'timing-env.ps1 Get-BuildProcs'   # one list for every runner (S3: clang++, rexglue*, codegen*, llvm-* ...)
$build0 = @(Get-BuildProcs | ForEach-Object { ($_ -split ':')[0] } | Group-Object | ForEach-Object { '{0} x{1}' -f $_.Name, $_.Count })
"build processes at start: $(if ($build0.Count) { $build0 -join ', ' } else { 'none' })"
$sysOk = $false; $prevSys = $null
try {
    Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public static class LdSysTimes{[DllImport("kernel32.dll")]static extern bool GetSystemTimes(out long idle,out long kernel,out long user);public static long[] Get(){long i,k,u;if(!GetSystemTimes(out i,out k,out u))return null;return new long[]{i,k,u};}}'
    $prevSys = [LdSysTimes]::Get(); $sysOk = $null -ne $prevSys
} catch { "machine CPU sampling unavailable: $($_.Exception.Message)" }
$start = Get-Date
$p = Start-Process -FilePath (Join-Path $run 'legodimensions.exe') -ArgumentList $gameArgs -WorkingDirectory $run -PassThru
$sw = [Diagnostics.Stopwatch]::StartNew()
$t0 = Get-Date   # proc.csv t_s is measured from here
$gamePid = $p.Id
$procStart = $null
try { $procStart = $p.StartTime.ToString('yyyy-MM-dd HH:mm:ss.fff') } catch { }
"started pid $gamePid at $($start.ToString('HH:mm:ss.fff')) (process StartTime $procStart)"
# agy runs each command on its own desktop (WinSta0\exebox-*): the game window lives there, invisible to the
# user and to other commands, so WM_CLOSE works only from this script. Recorded for the report.
$desk = ''
try {
    Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;using System.Text;public static class LdDesk{[DllImport("user32.dll")]static extern IntPtr GetThreadDesktop(uint t);[DllImport("kernel32.dll")]static extern uint GetCurrentThreadId();[DllImport("user32.dll",CharSet=CharSet.Unicode)]static extern bool GetUserObjectInformation(IntPtr h,int i,StringBuilder b,int n,out int need);public static string Name(){var b=new StringBuilder(256);int n;GetUserObjectInformation(GetThreadDesktop(GetCurrentThreadId()),2,b,512,out n);return b.ToString();}}'
    $desk = [LdDesk]::Name()
} catch { }

$prevCpu = 0.0; $prevT = 0.0
$peakWs = 0L; $peakCommit = 0L; $maxThreads = 0
$firstCsvBytesT = $null; $firstLogT = $null; $firstWindowT = $null
$dialogs = New-Object System.Collections.Generic.List[string]
$werSeen = $false; $notResponding = 0; $exitedEarly = $false; $sampleErrors = 0; $unlockedAt = $null
$sysSum = 0.0; $sysMax = 0.0; $otherSum = 0.0; $otherMax = 0.0; $sysN = 0; $buildMax = 0; $buildLast = ''
$windowDesc = @()
$close = $null
$tick = 0
try {
    while ($sw.Elapsed.TotalSeconds -lt $WatchSeconds) {
        $tick++
        $wait = [int](($tick * 1.0 - $sw.Elapsed.TotalSeconds) * 1000)
        if ($wait -gt 0) { [void]$p.WaitForExit($wait) }
        $t = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        if ($StopWhenUnlocked -and ($tick % 2) -eq 0 -and -not (Test-DesktopLocked)) {
            $unlockedAt = $t
            "desktop unlocked at $t s: ending the watch early so the user's timing matrix can start"
            break
        }
        try {
            $note = ''
            $csvFi.Refresh()
            $csvBytes = if ($csvFi.Exists) { $csvFi.Length } else { '' }
            if ($p.HasExited) {
                $exitedEarly = $true
                Update-LineCounter $logC
                $row = @((Fmt $t 2), 0, '', '', '', '', '', '', '', '', '', '', $logC.Lines, $logC.Bytes, $csvBytes,
                         (Fmt (Get-FreeRamGB) 2), '', '', '', '', 'exited')
                $writer.WriteLine($row -join ',')
                "process exited at $t s"
                break
            }
            $s = Get-ProcSample $p
            $dT = $t - $prevT
            $cores = if ($dT -gt 0) { ($s.cpu_s - $prevCpu) / $dT } else { 0 }
            $prevCpu = $s.cpu_s; $prevT = $t
            $sysPct = ''; $other = ''
            if ($sysOk) {
                $st = [LdSysTimes]::Get()
                if ($null -ne $st) {
                    $dTot = ($st[1] - $prevSys[1]) + ($st[2] - $prevSys[2])   # kernel time includes idle
                    if ($dTot -gt 0) {
                        $busy = [math]::Min(1.0, [math]::Max(0.0, 1.0 - ($st[0] - $prevSys[0]) / $dTot))
                        $oc = [math]::Max(0.0, $busy * $ncpu - $cores)
                        $sysPct = Fmt ($busy * 100) 1; $other = Fmt $oc 2
                        $sysSum += $busy * 100; $otherSum += $oc; $sysN++
                        if ($busy * 100 -gt $sysMax) { $sysMax = $busy * 100 }
                        if ($oc -gt $otherMax) { $otherMax = $oc }
                    }
                    $prevSys = $st
                }
            }
            if ($s.peak_ws -gt $peakWs) { $peakWs = $s.peak_ws }
            if ($s.peak_commit -gt $peakCommit) { $peakCommit = $s.peak_commit }
            if ($s.threads -gt $maxThreads) { $maxThreads = $s.threads }
            if ($s.responding -eq $false) { $notResponding++ }
            Update-LineCounter $logC
            if ($null -eq $firstLogT -and $logC.Lines -gt 0) { $firstLogT = $t }
            if ($null -eq $firstCsvBytesT -and $csvBytes -ne '' -and $csvBytes -gt 0) { $firstCsvBytesT = $t; $note = 'first perf.csv flush' }
            $nWin = ''; $nBuild = ''
            if (($tick % 5) -eq 1) {
                $windowDesc = @([LdHarness]::Describe($gamePid))
                $nWin = $windowDesc.Count
                $nBuild = @(Get-BuildProcs).Count; $buildLast = $nBuild
                if ($nBuild -gt $buildMax) { $buildMax = $nBuild }
                if ($null -eq $firstWindowT -and $windowDesc.Count -gt 0) { $firstWindowT = $t; $note = ($note + ' first window: ' + $windowDesc[0]).Trim() }
                foreach ($d in $windowDesc) {
                    if ($d.StartsWith('#32770') -and -not $dialogs.Contains($d)) { $dialogs.Add($d); "DIALOG at $t s: $d"; $note = ($note + ' dialog').Trim() }
                }
                if (-not $werSeen -and @(Get-WerFor $gamePid).Count -gt 0) { $werSeen = $true; "WerFault for pid $gamePid at $t s"; $note = ($note + ' WerFault').Trim() }
            }
            $row = @((Fmt $t 2), 1, (Fmt ($cores / $ncpu * 100) 1), (Fmt $cores 2), (Fmt $s.cpu_s 2), (Fmt ($s.ws / 1MB) 0),
                     (Fmt ($s.peak_ws / 1MB) 0), (Fmt ($s.commit / 1MB) 0), (Fmt ($s.peak_commit / 1MB) 0), $s.threads,
                     $s.handles, $s.responding, $logC.Lines, $logC.Bytes, $csvBytes, (Fmt (Get-FreeRamGB) 2), $nWin, $sysPct, $other, $nBuild,
                     ($note -replace ',', ';'))
            $writer.WriteLine($row -join ',')
            if (($tick % 30) -eq 0) { 't={0} s cpu={1:N2} cores ws={2:N0} MB commit={3:N0} MB threads={4} log={5} perf.csv={6} B machine={7}% other={8} cores builds={9}' -f $t, $cores, ($s.ws / 1MB), ($s.commit / 1MB), $s.threads, $logC.Lines, $csvBytes, $sysPct, $other, $buildLast }
        } catch {
            $sampleErrors++
            "sample error at $t s: $($_.Exception.Message)"
        }
    }
} finally {
    if (-not $p.HasExited) {
        try { $windowDesc = @([LdHarness]::Describe($gamePid)) } catch { }
        $close = Close-Game -P $p -TimeoutSec $CloseTimeoutSec
        "close: posted=$($close.wm_close_posted) wait=$($close.exit_wait_s) s killed=$($close.killed) exit=$($close.exit_code_hex)"
    }
    $writer.Dispose()
}
$exitCode = $null
if (-not $close) { try { $exitCode = $p.ExitCode } catch { } }
$end = Get-Date
Start-Sleep -Seconds 3
Update-LineCounter $logC
$csvFi.Refresh()
$artifacts = Save-CrashArtifacts -Run $run -Since $start.AddSeconds(-5)
$csvLines = $null
try { $csvLines = @(Get-Content -LiteralPath $csvFi.FullName).Count } catch { }

$code = if ($close) { $close.exit_code } else { $exitCode }
$summary = [ordered]@{
    run = $run; bin_dir = (Resolve-RepoPath $BinDir); args = $gameArgs; pid = $gamePid
    start = $start.ToString('yyyy-MM-dd HH:mm:ss.fff'); process_start = $procStart; proc_t0 = $t0.ToString('yyyy-MM-dd HH:mm:ss.fff')
    end = $end.ToString('yyyy-MM-dd HH:mm:ss.fff')
    perf_csv_mtime = $(if ($csvFi.Exists) { $csvFi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss.fff') } else { $null })
    runner_desktop = $desk
    watch_s = $WatchSeconds; exited_early = $exitedEarly
    exited_at_s = $(if ($exitedEarly) { [math]::Round($sw.Elapsed.TotalSeconds, 1) } else { $null })
    exit_code = $code; exit_code_hex = $(if ($null -ne $code) { '0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL) } else { $null })
    close = $close; peak_ws_mb = [math]::Round($peakWs / 1MB, 0); peak_commit_mb = [math]::Round($peakCommit / 1MB, 0)
    max_threads = $maxThreads; not_responding_samples = $notResponding; sample_errors = $sampleErrors
    first_log_line_s = $firstLogT; first_window_s = $firstWindowT; first_perf_csv_flush_s = $firstCsvBytesT
    log_lines = $logC.Lines; log_bytes = $logC.Bytes
    perf_csv_lines = $csvLines; perf_csv_bytes = $(if ($csvFi.Exists) { $csvFi.Length } else { $null })
    windows_at_end = $windowDesc; dialogs = $dialogs.ToArray(); werfault_seen = $werSeen
    artifacts = $artifacts; free_ram_gb_at_start = $free0; logical_cpus = $ncpu
    runner_session = (Get-Process -Id $PID).SessionId
    logonui_running = [bool](Get-Process LogonUI -ErrorAction SilentlyContinue)
    env = $envSet; stop_when_unlocked = [bool]$StopWhenUnlocked; unlocked_at_s = $unlockedAt
    build_procs_at_start = $build0; build_procs_max = $buildMax
    sys_busy_pct_mean = $(if ($sysN) { [math]::Round($sysSum / $sysN, 1) } else { $null }); sys_busy_pct_max = $(if ($sysN) { [math]::Round($sysMax, 1) } else { $null })
    other_cores_mean = $(if ($sysN) { [math]::Round($otherSum / $sysN, 2) } else { $null }); other_cores_max = $(if ($sysN) { [math]::Round($otherMax, 2) } else { $null })
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $run 'run.json') -Encoding utf8
'--- run.json ---'
Get-Content -LiteralPath (Join-Path $run 'run.json')
