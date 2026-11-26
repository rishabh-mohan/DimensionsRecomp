# harness/run-game.ps1 - one functional run of Dimensions Recompiled from a build dir (Agent 3).
#   powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin
#     [-Seconds 120] [-Warmup 60] [-StatsWarmup 10] [-Tag t] [-Cvar 'k=v;k2=v2'] [-Arg 'x=1;y=2'] [-Env 'N=v;N2=v2']
#     [-Profile [-ProfileSeconds 30]] [-CloseTimeoutSec 60] [-UserDir d] [-Exe legodimensions.exe]
#     [-RunsRoot build\agent3\runs] [-AllowConcurrent] [-NoAnalyse] [-DryRun] [-GpuLog]
#     [-InputScript harness\routes\x.txt [-VPadDll build\agent3\vpad\xinput1_4.dll]] [-SeedXenos dir]
# -Warmup = seconds after launch before the profile trigger; -StatsWarmup = seconds after the FIRST
# FRAME that runstats.py drops (perf.csv/frames.csv start at the first frame, ~61 s after launch on OFF).
# Several -Cvar/-Arg/-Env items: separate with ';'. -Arg items get a '--' prefix if they have none.
# Run dir <RunsRoot>\<yyyyMMdd-HHmmss>-<Tag>: BinDir mirrored by hard links (native-environment.ini and
# legodimensions.toml are never copied), harness\legodimensions.toml next to the exe with
# user_data_root=<run>\user (or -UserDir) and -Cvar overrides. CWD = run dir. Args:
#   --log_file=<run>\game.log --log_flush_interval=1 --perf_log_csv=<run>\perf.csv
#   --native_settings_load=false --discord_rpc=false --audio_mute=true --pause_when_unfocused=false  (+ -Arg)
# Inherited LEGO_*/PLUME_* env vars are dropped; LEGO_NATIVE_FRAME_METRICS=<run>\frames.csv (native
# builds only write it); then -Env. Samples CPU/memory/file sizes every 1 s into samples.csv.
# -Profile: LEGO_SAMPLE_PROFILE=1 + LEGO_SAMPLE_PROFILE_TRIGGER=<run>\profile.trigger; the trigger is
# created at -Warmup s and deleted -ProfileSeconds later; waits for profile-*.bin to stop growing;
# writes profile-meta.json (profile_trigger_start/_end, epoch s) and runs analyze_profile.py --json
# (profile.json, profile.txt). PROFILE ONLY, NOT FOR TIMING.
# At -Seconds: WM_CLOSE to the game's windows (from this script), kill after -CloseTimeoutSec.
# Then: exit code, crash events (Application 1000/1001/1002/1026), *.dmp, run.json, runstats.py.
# -GpuLog: NVIDIA GPU 0 state from NVML (harness\nvml.cs) once per sampling pass into gpu.csv (pstate, clocks,
# temperature, power, utilization, clock-limit reasons); runstats.py summarises it from the first frame + -StatsWarmup.
# Agent-launched runs sit on a hidden desktop (run.json "desktop"): functional only, never timing.
# -InputScript f: drives the game with Agent 3's virtual XInput pad (harness\vpad, harness-only test tooling, user mode
# only; keyboard input cannot reach a game on a hidden desktop, see perf-notes\agent3-run-harness.md section 7). Copies
# -VPadDll (default build\agent3\vpad\xinput1_4.dll, from harness\vpad\build-vpad.ps1) into the run dir only (never into
# BinDir; refused if BinDir has its own), sets AGENT3_VPAD=<run>\vpad-state.bin, adds --input_backend=xinput, and runs
# the script's steps from the launch on (harness\vpad\vpadhost.cs has the commands). Each step goes to input.csv with
# the pad's call counters, perf.csv's size (perf_bytes) and the game.log position: the real game holds perf.csv
# unshared while it runs, so harness\route-report.ps1 maps the steps to scenes after the run. run.json gets an
# input_script block; a 'stop' step ends the run early. -DryRun -InputScript only checks the script.
# -SeedXenos d: copies the Xenos shader storage files in d (*.xsh, *.xpso; e.g. build\agent3\seed\devoff2-214) into
# <user>\cache\shaders\shareable before the launch: plain copies, never hard links (the game appends to them, so a run
# never writes into the seed); refused if a copy would overwrite a file. run.json seed_xenos: each file's size and sha256
# before the launch, its size after the run, and game.log's lines with 'storage' (warm-storage arm,
# perf-notes\agent6-attract-stalls.md section 7). The run is still FUNCTIONAL ONLY.
# Exit code: 0 ok, 1 crashed/exited early with an error, 2 bad arguments or refused.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BinDir,
    [int]$Seconds = 120,
    [int]$Warmup = 60,
    [double]$StatsWarmup = 10,
    [string]$Tag = 'run',
    [string[]]$Cvar = @(),
    [string[]]$Arg = @(),
    [Alias('Env')][string[]]$GameEnv = @(),
    [switch]$Profile,
    [int]$ProfileSeconds = 30,
    [int]$CloseTimeoutSec = 60,
    [string]$UserDir = '',
    [string]$Exe = 'legodimensions.exe',
    [string]$Toml = '',
    [string]$RunsRoot = '',
    [switch]$AllowConcurrent,
    [switch]$NoAnalyse,
    [switch]$DryRun,
    [switch]$GpuLog,
    [string]$InputScript = '',
    [string]$VPadDll = '',
    [string]$SeedXenos = ''
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not $Toml) { $Toml = Join-Path $PSScriptRoot 'legodimensions.toml' }
if (-not $RunsRoot) { $RunsRoot = Join-Path $repo 'build\agent3\runs' }
function Split-Items([string[]]$a) { @($a | ForEach-Object { $_ -split ';' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
function Epoch([datetime]$d) { [math]::Round(($d.ToUniversalTime() - [datetime]'1970-01-01').TotalSeconds, 3) }
function Sha([string]$p) { if (Test-Path -LiteralPath $p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash } else { $null } }
function Quote-Arg([string]$s) { if ($s -notmatch '[\s"]') { return $s }; '"' + ($s -replace '"', '\"') + '"' }

$BinDir = (Resolve-Path -LiteralPath $BinDir).Path
$src = Join-Path $BinDir $Exe
if (-not (Test-Path -LiteralPath $src)) { Write-Host "no $Exe in $BinDir"; exit 2 }
$Cvar = Split-Items $Cvar; $GameEnv = Split-Items $GameEnv
# -Arg items without a leading '-' get '--' (powershell -File would read '--x' as a parameter name).
$Arg = @(Split-Items $Arg | ForEach-Object { if ($_ -like '-*') { $_ } else { "--$_" } })
if ($Profile) { $Seconds = [math]::Max($Seconds, $Warmup + $ProfileSeconds + 5) }

# One game at a time.
$exeBase = [IO.Path]::GetFileNameWithoutExtension($Exe)
$others = @(Get-Process -Name @($exeBase, 'legodimensions') -ErrorAction SilentlyContinue | Sort-Object Id -Unique)
if ($others.Count -and -not $AllowConcurrent -and -not $DryRun) {
    Write-Host ("REFUSED: already running: " + (($others | ForEach-Object { "$($_.ProcessName) pid $($_.Id)" }) -join ', ') + ". One game at a time (ask Agent 1 for a slot), or -AllowConcurrent.")
    exit 2
}
# Agent 8's runners leave gaps with no game running between their runs (harness\guard.ps1).
. (Join-Path $PSScriptRoot 'guard.ps1')
if (-not $AllowConcurrent -and -not $DryRun) {
    $runners = @(Get-ActiveRunners)
    if ($runners.Count) { Write-Host "REFUSED: a timing or boot runner is active ($($runners -join '; ')). Wait for Agent 8's slot, or -AllowConcurrent."; exit 2 }
}

Add-Type -Path (Join-Path $PSScriptRoot 'winhelper.cs') -ReferencedAssemblies System.Drawing
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$run = Join-Path $RunsRoot "$stamp-$Tag"; $k = 2
while (Test-Path -LiteralPath $run) { $run = Join-Path $RunsRoot "$stamp-$Tag-$k"; $k++ }
New-Item -ItemType Directory -Force -Path $run | Out-Null

# Mirror BinDir (hard links; copy if that fails, e.g. another volume).
$linked = 0; $copied = 0
foreach ($f in Get-ChildItem -LiteralPath $BinDir -Recurse -File) {
    $rel = $f.FullName.Substring($BinDir.Length).TrimStart('\')
    if ($rel -match '^(legodimensions\.toml|native-environment\.ini|profile-.*\.bin|.*\.dmp)$' -or $rel -like 'logs\*') { continue }
    $dst = Join-Path $run $rel
    $dd = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dd)) { New-Item -ItemType Directory -Force -Path $dd | Out-Null }
    if ([LdHarness]::HardLink($dst, $f.FullName)) { $linked++ } else { Copy-Item -LiteralPath $f.FullName -Destination $dst; $copied++ }
}
$exePath = Join-Path $run $Exe
$mapPath = Join-Path $run ($exeBase + '.map')
if (-not (Test-Path -LiteralPath $mapPath)) { $mapPath = Join-Path $run 'legodimensions.map' }

# Toml next to the exe.
$user = if ($UserDir) { $UserDir } else { Join-Path $run 'user' }
New-Item -ItemType Directory -Force -Path $user | Out-Null
$user = (Resolve-Path -LiteralPath $user).Path
# -SeedXenos: warm Xenos shader storage. Plain copies, never hard links (the game appends to these files).
$seedInfo = $null
if ($SeedXenos) {
    if (-not (Test-Path -LiteralPath $SeedXenos -PathType Container)) { Write-Host "no seed dir $SeedXenos"; exit 2 }
    $SeedXenos = (Resolve-Path -LiteralPath $SeedXenos).Path
    $seedFiles = @(Get-ChildItem -LiteralPath $SeedXenos -File | Where-Object { $_.Extension -eq '.xsh' -or $_.Extension -eq '.xpso' })
    if (-not $seedFiles.Count) { Write-Host "no *.xsh or *.xpso in $SeedXenos"; exit 2 }
    $shareable = Join-Path $user 'cache\shaders\shareable'
    New-Item -ItemType Directory -Force -Path $shareable | Out-Null
    $seedList = @()
    foreach ($f in $seedFiles) {
        $dst = Join-Path $shareable $f.Name
        if (Test-Path -LiteralPath $dst) { Write-Host "REFUSED: $dst exists (-SeedXenos wants a fresh user dir)"; exit 2 }
        [IO.File]::Copy($f.FullName, $dst)
        [IO.File]::SetAttributes($dst, [IO.FileAttributes]::Normal)
        $seedList += [ordered]@{ name = $f.Name; source = $f.FullName; bytes = $f.Length; sha256 = (Sha $f.FullName); copy = $dst
            copy_sha256 = (Sha $dst); bytes_after = $null }
    }
    $seedInfo = [ordered]@{ note = 'warm Xenos shader storage copied in before the launch; FUNCTIONAL ONLY'; source_dir = $SeedXenos
        dir = $shareable; files = $seedList; storage_log = @() }
}
$tl = New-Object System.Collections.Generic.List[string]
$tl.AddRange([string[]][IO.File]::ReadAllLines($Toml))
function Set-Toml([string]$name, [string]$value) {
    if ($value -notmatch "^(true|false|-?\d+(\.\d+)?|'.*'|"".*""|\[.*\])$") { $value = "'$value'" }
    for ($i = 0; $i -lt $tl.Count; $i++) { if ($tl[$i] -match "^\s*$([regex]::Escape($name))\s*=") { $tl[$i] = "$name = $value"; return } }
    $tl.Add("$name = $value")
}
Set-Toml 'user_data_root' $user
$cvarMap = [ordered]@{}
foreach ($c in $Cvar) {
    $kv = $c -split '=', 2
    if ($kv.Count -ne 2 -or -not $kv[0].Trim()) { Write-Host "bad -Cvar '$c' (want name=value)"; exit 2 }
    Set-Toml $kv[0].Trim() $kv[1].Trim(); $cvarMap[$kv[0].Trim()] = $kv[1].Trim()
}
$tomlPath = Join-Path $run 'legodimensions.toml'
[IO.File]::WriteAllLines($tomlPath, $tl)
$tomlSha0 = Sha $tomlPath

# Command line and environment.
$log = Join-Path $run 'game.log'; $perf = Join-Path $run 'perf.csv'; $frames = Join-Path $run 'frames.csv'
$trigger = Join-Path $run 'profile.trigger'
# -InputScript: virtual XInput pad (harness\vpad; harness-only test tooling).
$inputInfo = $null; $inputArgs = @(); $padState = $null; $padDll = $null
if ($InputScript) {
    $InputScript = (Resolve-Path -LiteralPath $InputScript).Path
    if (-not $VPadDll) { $VPadDll = Join-Path $repo 'build\agent3\vpad\xinput1_4.dll' }
    if (-not (Test-Path -LiteralPath $VPadDll)) { Write-Host "no $VPadDll (build it: harness\vpad\build-vpad.ps1)"; exit 2 }
    if (Test-Path -LiteralPath (Join-Path $BinDir 'xinput1_4.dll')) { Write-Host "REFUSED: $BinDir has its own xinput1_4.dll"; exit 2 }
    Add-Type -Path (Join-Path $PSScriptRoot 'vpad\vpadhost.cs')
    $padDll = Join-Path $run 'xinput1_4.dll'; $padState = Join-Path $run 'vpad-state.bin'; $inputCsv = Join-Path $run 'input.csv'
    $e = if ($DryRun) { [Agent3Input]::Load($InputScript) } else { [Agent3Input]::Start($InputScript, $padState, $inputCsv, $log, $perf) }
    if ($e) { Write-Host "bad -InputScript: $e"; exit 2 }
    # A copy in the run dir only (the mirror above hard-links BinDir's files; this one is never linked back).
    Copy-Item -LiteralPath $VPadDll -Destination $padDll -Force
    if (-not @($Arg | Where-Object { $_ -like '--input_backend=*' }).Count) { $inputArgs = @('--input_backend=xinput') }
    $inputInfo = [ordered]@{ note = 'virtual XInput pad (harness\vpad), harness-only test tooling; FUNCTIONAL ONLY'
        script = $InputScript; script_sha256 = (Sha $InputScript); steps_total = [Agent3Input]::StepsTotal
        dll_source = $VPadDll; dll = $padDll; dll_sha256 = (Sha $padDll); state_file = $padState; input_csv = $inputCsv }
}
$argv = @("--log_file=$log", '--log_flush_interval=1', "--perf_log_csv=$perf", '--native_settings_load=false',
    '--discord_rpc=false', '--audio_mute=true', '--pause_when_unfocused=false') + $Arg + $inputArgs
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $exePath; $psi.WorkingDirectory = $run; $psi.UseShellExecute = $false
$psi.Arguments = ($argv | ForEach-Object { Quote-Arg $_ }) -join ' '
foreach ($key in @($psi.EnvironmentVariables.Keys)) { if ($key -match '^(LEGO_|PLUME_)') { $psi.EnvironmentVariables.Remove($key) } }
$envSet = [ordered]@{ LEGO_NATIVE_FRAME_METRICS = $frames }
if ($Profile) { $envSet['LEGO_SAMPLE_PROFILE'] = '1'; $envSet['LEGO_SAMPLE_PROFILE_TRIGGER'] = $trigger }
if ($padState) { $envSet['AGENT3_VPAD'] = $padState }
foreach ($e in $GameEnv) {
    $kv = $e -split '=', 2
    if ($kv.Count -ne 2) { Write-Host "bad -Env '$e' (want NAME=value; empty value removes)"; exit 2 }
    $envSet[$kv[0].Trim()] = $kv[1]
}
foreach ($key in @($envSet.Keys)) {
    if ($envSet[$key] -eq '') { $psi.EnvironmentVariables.Remove($key); $envSet.Remove($key) } else { $psi.EnvironmentVariables[$key] = $envSet[$key] }
}
$profiling = $psi.EnvironmentVariables.ContainsKey('LEGO_SAMPLE_PROFILE')
$desktop = [LdHarness]::DesktopName()
$mode = if ($profiling) { 'PROFILE ONLY, NOT FOR TIMING' } elseif ($desktop -ne 'Default') { "FUNCTIONAL ONLY (hidden desktop $desktop), NOT FOR TIMING" } else { 'FUNCTIONAL (interactive desktop)' }
Write-Host "run      $run"
Write-Host "mode     $mode"
Write-Host "command  $Exe $($psi.Arguments)"
Write-Host "env      $(($envSet.Keys | ForEach-Object { "$_=$($envSet[$_])" }) -join ' ')"
if ($inputInfo) { Write-Host "input    $InputScript ($($inputInfo.steps_total) steps); virtual pad $padDll" }
if ($seedInfo) { Write-Host "seed     $(@($seedInfo.files).Count) storage files from $($seedInfo.source_dir) -> $($seedInfo.dir)" }
if ($DryRun) {
    # Everything up to the launch (mirror, toml, command line, env), then stop: checks a bin dir without a game slot.
    [ordered]@{ harness = 'harness/run-game.ps1'; mode = 'DRY RUN, not launched'; desktop = $desktop; tag = $Tag; run_dir = $run
        bin_dir = $BinDir; exe = $exePath; exe_sha256 = (Sha $src); map = $(if (Test-Path -LiteralPath $mapPath) { $mapPath })
        files_linked = $linked; files_copied = $copied; cwd = $run; command_line = "$Exe $($psi.Arguments)"; env = $envSet
        cvars = $cvarMap; user_data_root = $user; toml_sha256 = $tomlSha0; input_script = $inputInfo; seed_xenos = $seedInfo } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $run 'run.json') -Encoding utf8
    Write-Host "dry run: not launched ($linked files linked, $copied copied; map $(if (Test-Path -LiteralPath $mapPath) { 'found' } else { 'MISSING' }))"
    exit 0
}

# Launch and watch.
$gpuOut = $null; $gpuNote = $null; $gpuDevice = $null
if ($GpuLog) {
    try {
        Add-Type -Path (Join-Path $PSScriptRoot 'nvml.cs')
        $gpuNote = [LdNvml]::Open()
        if (-not $gpuNote) {
            $gpuDevice = [LdNvml]::Name
            $gfs = New-Object IO.FileStream((Join-Path $run 'gpu.csv'), [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::Read)
            $gpuOut = New-Object IO.StreamWriter($gfs); $gpuOut.AutoFlush = $true
            $gpuOut.WriteLine('t_s,pstate,gr_mhz,mem_mhz,temp_c,power_w,util_gpu,util_mem,throttle')
        }
    } catch { $gpuNote = "NVML not available: $($_.Exception.Message)" }
    Write-Host "gpu log  $(if ($gpuOut) { "$gpuDevice (NVML) -> gpu.csv" } else { "off: $gpuNote" })"
}
$t0 = Get-Date
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = [Diagnostics.Process]::Start($psi)
$gamePid = $p.Id
if ($InputScript) { [Agent3Input]::Go($sw.Elapsed.TotalSeconds) }
$fs = New-Object IO.FileStream((Join-Path $run 'samples.csv'), [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$sOut = New-Object IO.StreamWriter($fs); $sOut.AutoFlush = $true
$sOut.WriteLine('t_s,cpu_s,ws_mb,private_mb,threads,handles,log_bytes,perf_csv_bytes,frames_csv_bytes,windows,note')
$peakWs = 0.0; $peakPriv = 0.0; $peakThreads = 0; $cpuLast = 0.0; $nSamples = 0
$trigOn = $null; $trigOff = $null; $binSize = -1; $binStable = 0; $binDone = $false
$werSeen = $false; $exitedEarly = $false; $lastWerCheck = -10; $werChecked = @{}; $lastInput = ''; $inputStop = $false
function Size([string]$p) { try { (New-Object IO.FileInfo($p)).Length } catch { 0 } }
function Mark([string]$what) { $n = Get-Date; [ordered]@{ what = $what; t_s = [math]::Round($sw.Elapsed.TotalSeconds, 3); epoch_s = (Epoch $n); wall = $n.ToString('o'); qpc = [Diagnostics.Stopwatch]::GetTimestamp() } }
while ($true) {
    $t = $sw.Elapsed.TotalSeconds
    if ($p.HasExited) { $exitedEarly = $true; break }
    $note = ''
    if ($Profile -and -not $trigOn -and $t -ge $Warmup) {
        [IO.File]::WriteAllText($trigger, "profile trigger $(Get-Date -Format o)"); $trigOn = Mark 'trigger created'; $note = 'profile trigger created'
    }
    # (- 0.5: the loop ticks on whole seconds and the trigger was made just after a tick, so a strict
    # comparison would delete it one tick, ~1 s, late.)
    if ($trigOn -and -not $trigOff -and $t -ge $trigOn.t_s + $ProfileSeconds - 0.5) {
        Remove-Item -LiteralPath $trigger -Force; $trigOff = Mark 'trigger deleted'; $note = 'profile trigger deleted'
    }
    if ($trigOff -and -not $binDone) {
        $b = Get-ChildItem -LiteralPath $run -Filter 'profile-*.bin' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($b) {
            if ($b.Length -gt 0 -and $b.Length -eq $binSize) { $binStable++ } else { $binStable = 0 }
            $binSize = $b.Length
            if ($binStable -ge 2) { $binDone = $true; $note = "profile written ($binSize bytes)" }
        }
        if (-not $binDone -and $t -ge $trigOff.t_s + 90) { $binDone = $true; $note = 'profile not complete 90 s after the trigger was deleted' }
    }
    if ($t - $lastWerCheck -ge 2) {
        # Get-Process is cheap; the WMI command-line lookup (seconds when the box is busy) runs once per new WerFault pid.
        $lastWerCheck = $t
        foreach ($w in @(Get-Process -Name WerFault, WerFaultSecure -ErrorAction SilentlyContinue)) {
            if ($werChecked.ContainsKey($w.Id)) { continue }
            $werChecked[$w.Id] = $true
            $cl = "$((Get-CimInstance Win32_Process -Filter "ProcessId=$($w.Id)" -ErrorAction SilentlyContinue).CommandLine)"
            if ($cl -match "-p $gamePid\b") { $werSeen = $true; $note = ($note + ' WerFault attached').Trim() }
        }
    }
    if ($InputScript) {
        $ist = [Agent3Input]::Status()
        if ($ist -ne $lastInput) { $note = ($note + " input $ist").Trim(); $lastInput = $ist }
        if ([Agent3Input]::StopRequested -and -not $inputStop) { $inputStop = $true; $note = ($note + ' input script stop').Trim() }
    }
    try {
        $p.Refresh()
        $cpuLast = $p.TotalProcessorTime.TotalSeconds
        $ws = $p.WorkingSet64 / 1MB; $pv = $p.PrivateMemorySize64 / 1MB; $th = $p.Threads.Count
        $peakWs = [math]::Max($peakWs, $ws); $peakPriv = [math]::Max($peakPriv, $pv); $peakThreads = [math]::Max($peakThreads, $th)
        $nw = [LdHarness]::Windows($gamePid).Count
        $sOut.WriteLine(('{0:F1},{1:F2},{2:F0},{3:F0},{4},{5},{6},{7},{8},{9},{10}' -f $t, $cpuLast, $ws, $pv, $th, $p.HandleCount, (Size $log), (Size $perf), (Size $frames), $nw, $note))
        $nSamples++
    } catch { $sOut.WriteLine(('{0:F1},,,,,,,,,,sample failed: {1}' -f $t, ($_.Exception.Message -replace ',', ';'))) }
    if ($gpuOut) { try { $gpuOut.WriteLine(('{0:F1},{1}' -f $t, [LdNvml]::Sample())) } catch { } }
    if ($werSeen) { break }
    if (($t -ge $Seconds -or $inputStop) -and (-not $trigOn -or $binDone)) { break }
    Start-Sleep -Milliseconds ([math]::Max(50, 1000 - ($sw.ElapsedMilliseconds % 1000)))
}
if ($trigOn -and -not $trigOff -and (Test-Path -LiteralPath $trigger)) { Remove-Item -LiteralPath $trigger -Force; $trigOff = Mark 'trigger deleted (late)' }
if ($InputScript) { [Agent3Input]::Halt() }

# Close: WM_CLOSE from this script (same desktop), then kill.
$closeMethod = 'exited'; $closeSec = $null; $windowsAtClose = @(); $closeSentS = $null
if (-not $p.HasExited) {
    $windowsAtClose = @([LdHarness]::Describe($gamePid))
    $c0 = $sw.Elapsed.TotalSeconds; $closeSentS = [math]::Round($c0, 2)
    if ([LdHarness]::CloseAll($gamePid) -eq 0) { $null = $p.CloseMainWindow() }
    if ($p.WaitForExit($CloseTimeoutSec * 1000)) { $closeMethod = 'wm_close' }
    else { try { $p.Kill() } catch { }; $null = $p.WaitForExit(15000); $closeMethod = 'killed' }
    $closeSec = [math]::Round($sw.Elapsed.TotalSeconds - $c0, 2)
}
if ($InputScript) { $fin = [Agent3Input]::Finish(); foreach ($key in @($fin.Keys)) { $inputInfo[$key] = $fin[$key] } }
$elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 2)
try { $cpuLast = $p.TotalProcessorTime.TotalSeconds } catch { }
$sOut.Close()
if ($gpuOut) { $gpuOut.Close(); [LdNvml]::Close() }
$exitCode = $null; try { $exitCode = $p.ExitCode } catch { }
$tomlSha1 = Sha $tomlPath
if ($seedInfo) {
    foreach ($sf in $seedInfo.files) { $sf.bytes_after = (Size $sf.copy) }
    if (Test-Path -LiteralPath $log) { $seedInfo.storage_log = @(Select-String -LiteralPath $log -Pattern 'storage' -SimpleMatch | Select-Object -First 12 | ForEach-Object { $_.Line.Trim() }) }
}

# Crash evidence.
$events = @()
try {
    $events = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; StartTime = $t0.AddSeconds(-2); Id = 1000, 1001, 1002, 1026 } -ErrorAction Stop |
        Where-Object { $_.Message -match [regex]::Escape($Exe) -or $_.Message -match "\b$gamePid\b" } |
        ForEach-Object { $m = $_.Message -replace '\s+', ' '; [ordered]@{ id = $_.Id; provider = $_.ProviderName; time = $_.TimeCreated.ToString('o'); summary = $m.Substring(0, [math]::Min(300, $m.Length)) } })
} catch { }
# (-Filter, not -Include: PS 5.1 ignores -Include with -LiteralPath and returned every file.)
$dumps = @(Get-ChildItem -LiteralPath $run -Recurse -Filter '*.dmp' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
$cd = Join-Path $env:LOCALAPPDATA 'CrashDumps'
if (Test-Path -LiteralPath $cd) { $dumps += @(Get-ChildItem -LiteralPath $cd -Filter "$Exe*.dmp" -File | Where-Object { $_.LastWriteTime -ge $t0 } | ForEach-Object { $_.FullName }) }

# Profile metadata and analysis.
$profileInfo = $null
if ($Profile) {
    $bins = @(Get-ChildItem -LiteralPath $run -Filter 'profile-*.bin' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    $profileInfo = [ordered]@{
        note = 'PROFILE ONLY, NOT FOR TIMING'
        profile_trigger_start = $(if ($trigOn) { $trigOn.epoch_s }); profile_trigger_end = $(if ($trigOff) { $trigOff.epoch_s })
        profile_trigger_start_wall = $(if ($trigOn) { $trigOn.wall }); profile_trigger_end_wall = $(if ($trigOff) { $trigOff.wall })
        qpc_frequency = [Diagnostics.Stopwatch]::Frequency
        qpc_trigger_start = $(if ($trigOn) { $trigOn.qpc }); qpc_trigger_end = $(if ($trigOff) { $trigOff.qpc })
        trigger_file = $trigger; profile_seconds_requested = $ProfileSeconds; profiles = $bins
        map = $(if (Test-Path -LiteralPath $mapPath) { $mapPath }); analysis = $null; rounds_per_s = $null; analysis_warning = $null
    }
    $metaPath = Join-Path $run 'profile-meta.json'
    $profileInfo | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $metaPath -Encoding ascii
    $an = Join-Path $repo 'DimensionsRecomp\tools\native-cpu\analyze_profile.py'
    if ($bins.Count -and -not $NoAnalyse -and (Test-Path -LiteralPath $an) -and $profileInfo.map) {
        $pj = Join-Path $run 'profile.json'; $pt = Join-Path $run 'profile.txt'; $al = Join-Path $run 'profile-analyse.log'
        $ErrorActionPreference = 'Continue'
        & python $an $bins[-1] $profileInfo.map --meta $metaPath --json -o $pj *> $al
        & python $an $bins[-1] $profileInfo.map --meta $metaPath -o $pt *>> $al
        $ErrorActionPreference = 'Stop'
        if (Test-Path -LiteralPath $pj) {
            $profileInfo.analysis = $pj
            try { $rj = Get-Content -LiteralPath $pj -Raw | ConvertFrom-Json; $profileInfo.rounds_per_s = $rj.duration.rounds_per_s } catch { }
            if ($null -eq $profileInfo.rounds_per_s -or $profileInfo.rounds_per_s -lt 250) { $profileInfo.analysis_warning = "rounds_per_s $($profileInfo.rounds_per_s) < 250: few samples, attribution only" }
        }
    }
    $profileInfo | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $metaPath -Encoding ascii
}

$runJson = [ordered]@{
    harness = 'harness/run-game.ps1'; mode = $mode; desktop = $desktop; tag = $Tag
    run_dir = $run; bin_dir = $BinDir; exe = $exePath; exe_sha256 = (Sha $src); map = $(if (Test-Path -LiteralPath $mapPath) { $mapPath })
    files_linked = $linked; files_copied = $copied; cwd = $run; command_line = "$Exe $($psi.Arguments)"; env = $envSet; cvars = $cvarMap
    user_data_root = $user; toml_sha256_before = $tomlSha0; toml_sha256_after = $tomlSha1; toml_rewritten = ($tomlSha0 -ne $tomlSha1)
    started = $t0.ToString('o'); started_epoch_s = (Epoch $t0); pid = $gamePid; seconds_requested = $Seconds; warmup_s = $Warmup
    elapsed_s = $elapsed; exited_early = $exitedEarly; exit_code = $exitCode
    exit_code_hex = $(if ($null -ne $exitCode) { '0x{0:X8}' -f $exitCode }); close_method = $closeMethod; close_seconds = $closeSec; close_sent_s = $closeSentS
    close_timeout = $CloseTimeoutSec; windows_at_close = $windowsAtClose; wer_seen = $werSeen; crash_events = $events; dumps = $dumps
    process = [ordered]@{ cpu_s = [math]::Round($cpuLast, 1); avg_cores = $(if ($elapsed -gt 0) { [math]::Round($cpuLast / $elapsed, 2) }); peak_ws_mb = [math]::Round($peakWs); peak_private_mb = [math]::Round($peakPriv); peak_threads = $peakThreads; samples = $nSamples }
    log_bytes = (Size $log); perf_csv_bytes = (Size $perf); frames_csv_bytes = (Size $frames)
    profile = $profileInfo; input_script = $inputInfo; seed_xenos = $seedInfo
    gpu_log = $(if ($GpuLog) { [ordered]@{ file = $(if ($gpuOut) { Join-Path $run 'gpu.csv' }); source = 'NVML (nvml.dll), GPU 0, once per 1 s sampling pass'; device = $gpuDevice; note = $gpuNote } })
}
$runJson | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $run 'run.json') -Encoding utf8

$ErrorActionPreference = 'Continue'
& python (Join-Path $PSScriptRoot 'runstats.py') $run --warmup $StatsWarmup --write
if ($profileInfo) {
    Write-Host "profile  $(if ($profileInfo.profiles.Count) { $profileInfo.profiles -join ', ' } else { 'NO profile-*.bin written' }); meta $(Join-Path $run 'profile-meta.json')"
    if ($profileInfo.analysis) { Write-Host "         analysis $($profileInfo.analysis); rounds/s $($profileInfo.rounds_per_s) $($profileInfo.analysis_warning)" }
    Write-Host '         PROFILE ONLY, NOT FOR TIMING'
}
if ($inputInfo) {
    Write-Host "input    steps $($inputInfo.steps_done)/$($inputInfo.steps_total) (last: $($inputInfo.last_step)); timeouts $($inputInfo.timeouts)$(if ($inputInfo.timeout_lines) { " (lines $($inputInfo.timeout_lines))" }); stopped by the script: $($inputInfo.stopped_by_script)$(if ($inputInfo.error) { "; ERROR $($inputInfo.error)" })"
    Write-Host "         pad loaded by pid $($inputInfo.dll_loaded_by_pid) from '$($inputInfo.dll_loaded_from)'; GetState $($inputInfo.pad_reads) calls ($($inputInfo.pad_active_reads) with input); keystrokes $($inputInfo.key_events) ($($inputInfo.key_calls) calls); $($inputInfo.input_csv)"
}
if ($seedInfo) {
    $parts = @(foreach ($sf in $seedInfo.files) {
        $x = "$($sf.name) $($sf.bytes) -> $($sf.bytes_after) B"
        if ($sf.name -like '*.xpso' -and $sf.bytes_after) { $x += " ($([math]::Floor(($sf.bytes - 12) / 72)) -> $([math]::Floor(($sf.bytes_after - 12) / 72)) pipelines, 72 B each)" }
        $x
    })
    Write-Host "seed     $($parts -join '; ')"
    foreach ($l in $seedInfo.storage_log) { Write-Host "         $l" }
}
if ($events.Count -or $dumps.Count -or $werSeen -or ($exitedEarly -and $exitCode -ne 0)) { exit 1 }
exit 0
