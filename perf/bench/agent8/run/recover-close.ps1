# Recovery for a first-boot run whose sampler died while the game kept running (task #16).
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\recover-close.ps1 -Run <run dir> [-SampleSeconds 10]
# Finds the game by its exe path in the run dir, appends -SampleSeconds more 1 s samples to proc.csv
# (t relative to the process start time), then WM_CLOSE / kill after 30 s, collects artifacts and
# writes run.json. Never touches any other process.
param(
    [Parameter(Mandatory = $true)][string]$Run,
    [int]$SampleSeconds = 10,
    [int]$CloseTimeoutSec = 30
)
$ErrorActionPreference = 'Continue'
. "$PSScriptRoot\common.ps1"
Import-LdHelper
$Run = (Resolve-Path (Resolve-RepoPath $Run)).Path
$exe = Join-Path $Run 'legodimensions.exe'
$p = Get-Process legodimensions -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe } | Select-Object -First 1
if (-not $p) { "no running game from $exe"; exit 2 }
$start = $p.StartTime
"pid $($p.Id) started $($start.ToString('HH:mm:ss.fff')), running $([math]::Round(((Get-Date) - $start).TotalSeconds)) s"
$procCsv = Join-Path $Run 'proc.csv'
$csvPath = Join-Path $Run 'perf.csv'
$logC = New-LineCounter (Join-Path $Run 'game.log')
$ncpu = [Environment]::ProcessorCount
$prev = Get-ProcSample $p
$prevT = ((Get-Date) - $start).TotalSeconds
$peakWs = $prev.peak_ws; $peakCommit = $prev.peak_commit; $maxThreads = $prev.threads
for ($i = 0; $i -lt $SampleSeconds; $i++) {
    if ($p.WaitForExit(1000)) { 'process exited during sampling'; break }
    $s = Get-ProcSample $p
    $t = ((Get-Date) - $start).TotalSeconds
    $cores = ($s.cpu_s - $prev.cpu_s) / ($t - $prevT)
    $prev = $s; $prevT = $t
    if ($s.peak_ws -gt $peakWs) { $peakWs = $s.peak_ws }
    if ($s.peak_commit -gt $peakCommit) { $peakCommit = $s.peak_commit }
    if ($s.threads -gt $maxThreads) { $maxThreads = $s.threads }
    Update-LineCounter $logC
    $fi = New-Object IO.FileInfo $csvPath; $fi.Refresh()
    $row = @((Fmt $t 2), 1, (Fmt ($cores / $ncpu * 100) 1), (Fmt $cores 2), (Fmt $s.cpu_s 2), (Fmt ($s.ws / 1MB) 0),
             (Fmt ($s.peak_ws / 1MB) 0), (Fmt ($s.commit / 1MB) 0), (Fmt ($s.peak_commit / 1MB) 0), $s.threads,
             $s.handles, $s.responding, $logC.Lines, $logC.Bytes, '', (Fmt (Get-FreeRamGB) 2), '',
             ('recovery sample; perf.csv bytes ' + $fi.Length))
    for ($k = 0; $k -lt 5; $k++) { try { Add-Content -LiteralPath $procCsv -Value ($row -join ',') -Encoding ascii -ErrorAction Stop; break } catch { Start-Sleep -Milliseconds 100 } }
    'sample t={0:N1} cores={1:N2} ws={2:N0} MB commit={3:N0} MB threads={4} responding={5} perf.csv={6} B' -f $t, $cores, ($s.ws / 1MB), ($s.commit / 1MB), $s.threads, $s.responding, $fi.Length
}
$windows = @([LdHarness]::Describe($p.Id))
"windows: $($windows -join ' || ')"
$wer = @(Get-WerFor $p.Id)
$close = Close-Game -P $p -TimeoutSec $CloseTimeoutSec
"close: posted=$($close.wm_close_posted) wait=$($close.exit_wait_s) s killed=$($close.killed) exit=$($close.exit_code_hex)"
$end = Get-Date
Start-Sleep -Seconds 3
Update-LineCounter $logC
$fi = New-Object IO.FileInfo $csvPath; $fi.Refresh()
$artifacts = Save-CrashArtifacts -Run $Run -Since $start.AddSeconds(-5)
$csvLines = 0
try { $csvLines = @(Get-Content -LiteralPath $csvPath).Count } catch { }
$summary = [ordered]@{
    run = $Run; start = $start.ToString('yyyy-MM-dd HH:mm:ss.fff'); end = $end.ToString('yyyy-MM-dd HH:mm:ss.fff')
    note = 'first-boot.ps1 sampler died (Add-Content on proc.csv hit a concurrent reader); recovered by recover-close.ps1'
    watch_s = [math]::Round(($end - $start).TotalSeconds, 0); exited_early = $false
    exit_code = $close.exit_code; exit_code_hex = $close.exit_code_hex; close = $close
    peak_ws_mb = [math]::Round($peakWs / 1MB, 0); peak_commit_mb = [math]::Round($peakCommit / 1MB, 0)
    max_threads_recovery_window = $maxThreads
    log_lines = $logC.Lines; log_bytes = $logC.Bytes; perf_csv_lines = $csvLines; perf_csv_bytes = $fi.Length
    windows_at_end = $windows; werfault_seen = ($wer.Count -gt 0); artifacts = $artifacts
    logical_cpus = $ncpu; runner_session = (Get-Process -Id $PID).SessionId
    logonui_running = [bool](Get-Process LogonUI -ErrorAction SilentlyContinue)
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Run 'run.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $Run 'run.json')
