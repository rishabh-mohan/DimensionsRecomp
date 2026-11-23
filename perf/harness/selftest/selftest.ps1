# harness/selftest/selftest.ps1 - end-to-end test of harness/run-game.ps1 with a fake exe (no game data).
#   powershell -NoProfile -ExecutionPolicy Bypass -File harness\selftest\selftest.ps1 [-Only normal,profile,crash,kill,input]
# Builds fakegame.cs into build\agent3\selftest-bin\fakedimensions.exe (csc of .NET Framework 4), writes
# a matching lld-style map, runs the cases into build\agent3\selftest-runs and checks run.json,
# summary.json and profile.json. The input case builds the virtual pad (harness\vpad\build-vpad.ps1) and
# drives the fake game with harness\routes\selftest-input.txt (-InputScript). Results:
# build\agent3\selftest-latest.txt; exit 1 on any FAIL.
param([string[]]$Only = @('normal', 'profile', 'crash', 'kill', 'input'), [switch]$Force)
$ErrorActionPreference = 'Stop'
$h = Split-Path -Parent $PSScriptRoot; $repo = Split-Path -Parent $h
# Never next to a game or one of Agent 8's runners (-Force overrides): the fake game costs CPU, and the crash case's
# WER dump lands in %LOCALAPPDATA%\CrashDumps, where a runner that collects new dumps picks it up (harness\guard.ps1).
. (Join-Path $h 'guard.ps1')
if (-not $Force) {
    $busy = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue | ForEach-Object { "legodimensions pid $($_.Id)" }) + @(Get-ActiveRunners)
    if ($busy.Count) { Write-Host "REFUSED: $($busy -join '; ') running. The self-test waits for a free machine (or -Force)."; exit 2 }
}
$bin = Join-Path $repo 'build\agent3\selftest-bin'; $runs = Join-Path $repo 'build\agent3\selftest-runs'
New-Item -ItemType Directory -Force -Path $bin, $runs | Out-Null
$exe = Join-Path $bin 'fakedimensions.exe'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $csc /nologo /target:winexe /r:System.Windows.Forms.dll /r:System.Drawing.dll "/out:$exe" (Join-Path $PSScriptRoot 'fakegame.cs')
if ($LASTEXITCODE) { throw 'csc failed' }
function Sym([long]$va, [string]$name, [string]$obj) { ' {0:x4}:{1:x8}       {2,-26} {3:x16}     {4}' -f $(if ($va) { 1 } else { 0 }), $(if ($va) { $va - 0x140001000 } else { 0 }), $name, $va, $obj }
$map = @(' fakedimensions', '', ' Timestamp is 00000000 (Thu Jan  1 00:00:00 1970)', '', ' Preferred load address is 0000000140000000', '',
    ' Start         Length     Name                   Class', ' 0001:00000000 00003000H .text                   CODE', '',
    '  Address         Publics by Value              Rva+Base               Lib:Object', '',
    (Sym 0 '__AbsoluteZero' '<absolute>'),
    (Sym 0x140001000 'sub_82000000' 'fake_recomp.0.cpp.obj'), (Sym 0x140001000 '__imp__sub_82000000' 'fake_recomp.0.cpp.obj'),
    (Sym 0x140002000 '?Present@FakeGame@@QEAAXXZ' 'fakegame.cpp.obj'), (Sym 0x140003000 '?Render@FakeGame@@QEAAXXZ' 'fakegame.cpp.obj'),
    '', ' entry point at         0001:00000000', '', ' Static symbols', '')
[IO.File]::WriteAllLines((Join-Path $bin 'fakedimensions.map'), [string[]]$map)

$rg = Join-Path $h 'run-game.ps1'
$results = New-Object System.Collections.Generic.List[string]
function Check([string]$name, [bool]$ok, $detail) {
    $line = '{0}  {1}{2}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $(if ($null -ne $detail -and "$detail") { ": $detail" } else { '' })
    $results.Add($line); Write-Host $line
}
function RunCase([string]$tag, [string[]]$extra) {
    $t = Get-Date
    # 'Continue': stderr lines (e.g. the CLR's unhandled-exception text from the crash case) must not stop the test.
    $ErrorActionPreference = 'Continue'
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $rg -BinDir $bin -Exe fakedimensions.exe -RunsRoot $runs -Tag $tag -AllowConcurrent @extra 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $out | ForEach-Object { "   | $_" } | Write-Host
    $dir = Get-ChildItem -LiteralPath $runs -Directory | Where-Object { $_.Name -like "*-$tag" -and $_.CreationTime -ge $t.AddSeconds(-2) } | Sort-Object CreationTime | Select-Object -Last 1
    $o = [ordered]@{ code = $code; dir = $null; run = $null; sum = $null; secs = [math]::Round(((Get-Date) - $t).TotalSeconds, 1) }
    if ($dir) {
        $o.dir = $dir.FullName
        $rj = Join-Path $dir.FullName 'run.json'; $sj = Join-Path $dir.FullName 'summary.json'
        if (Test-Path $rj) { $o.run = Get-Content $rj -Raw | ConvertFrom-Json }
        if (Test-Path $sj) { $o.sum = Get-Content $sj -Raw | ConvertFrom-Json }
    }
    [pscustomobject]$o
}

if ($Only -contains 'normal') {
    $gpuArgs = @(); if (Test-Path -LiteralPath "$env:SystemRoot\System32\nvml.dll") { $gpuArgs = @('-GpuLog') }
    $c = RunCase 'normal' (@('-Seconds', '12', '-Warmup', '2', '-StatsWarmup', '2', '-Cvar', 'fullscreen=false;selftest_key=hello world') + $gpuArgs)
    Check 'normal: exit 0, closed by WM_CLOSE, exit code 0' ($c.code -eq 0 -and $c.run.close_method -eq 'wm_close' -and $c.run.exit_code -eq 0) "code $($c.code), $($c.run.close_method), exit $($c.run.exit_code_hex), $($c.secs) s"
    Check 'normal: verdict RUNNING from the DXGI adapter marker + perf.csv' ($c.sum.verdict -eq 'RUNNING' -and $c.sum.log.markers.dxgi_adapter.adapter -eq 'Harness Fake Adapter') $c.sum.verdict
    Check 'normal: perf.csv parsed (frames measured, p99 present)' ($c.sum.perf.frames_measured -gt 100 -and $null -ne $c.sum.perf.p99_ms) "measured $($c.sum.perf.frames_measured), median $($c.sum.perf.median_ms) ms, p99 $($c.sum.perf.p99_ms) ms"
    Check 'normal: frames.csv written via LEGO_NATIVE_FRAME_METRICS' ($c.sum.frames.frames_total -gt 100) $c.sum.frames.frames_total
    $log = Get-Content (Join-Path $c.dir 'game.log') -Raw
    Check 'normal: command line reached the exe (log_flush_interval, perf_log_csv, CWD = run dir)' ($log -match '--log_flush_interval=1' -and $log -match [regex]::Escape("--perf_log_csv=$($c.dir)\perf.csv") -and $log -match [regex]::Escape("cwd=$($c.dir)")) ''
    $toml = Get-Content (Join-Path $c.dir 'legodimensions.toml') -Raw
    Check 'normal: toml user_data_root + -Cvar override/append' ($toml -match [regex]::Escape("user_data_root = '$($c.dir)\user'") -and $toml -match "selftest_key = 'hello world'" -and $toml -match 'fullscreen = false') ''
    Check 'normal: toml not rewritten, files hard-linked, >= 8 samples' (-not $c.run.toml_rewritten -and $c.run.files_linked -ge 2 -and $c.run.process.samples -ge 8) "linked $($c.run.files_linked), samples $($c.run.process.samples), desktop $($c.run.desktop), mode '$($c.run.mode)'"
    if ($gpuArgs) {
        Check 'normal: -GpuLog gpu.csv from NVML, summarised after the first frame' ($c.sum.gpu.samples_total -ge 8 -and $c.sum.gpu.samples -ge 3 -and $null -ne $c.sum.gpu.gr_mhz_median -and $null -ne $c.run.close_sent_s) "device '$($c.run.gpu_log.device)', $($c.sum.gpu.samples_total) samples, $($c.sum.gpu.samples) from $($c.sum.gpu.window_from_s) s (first frame $($c.sum.first_frame_s) s), util median $($c.sum.gpu.util_median) %, clock $($c.sum.gpu.gr_mhz_median) MHz, $($c.sum.gpu.pstate_mode), close sent at $($c.run.close_sent_s) s, note '$($c.run.gpu_log.note)'"
    }
}
if ($Only -contains 'profile') {
    $c = RunCase 'profile' @('-Seconds', '6', '-Warmup', '3', '-Profile', '-ProfileSeconds', '4', '-StatsWarmup', '1')
    $pm = if ($c.dir -and (Test-Path (Join-Path $c.dir 'profile-meta.json'))) { Get-Content (Join-Path $c.dir 'profile-meta.json') -Raw | ConvertFrom-Json }
    Check 'profile: exit 0, PROFILE ONLY mode' ($c.code -eq 0 -and $c.run.mode -eq 'PROFILE ONLY, NOT FOR TIMING') "code $($c.code), $($c.secs) s"
    Check 'profile: env set, trigger removed, profile-*.bin written' ($c.run.env.LEGO_SAMPLE_PROFILE -eq '1' -and -not (Test-Path (Join-Path $c.dir 'profile.trigger')) -and @($pm.profiles).Count -eq 1) (@($pm.profiles) -join ', ')
    $win = if ($pm) { $pm.profile_trigger_end - $pm.profile_trigger_start }
    Check 'profile: profile-meta.json trigger window ~4 s (epoch seconds)' ($win -ge 3.5 -and $win -le 5.5) "window $win s"
    $pj = if ($pm.analysis) { Get-Content $pm.analysis -Raw | ConvertFrom-Json }
    Check 'profile: analyser ran (profile.json): top self = sub_82000000 guest' ($pj -and $pj.top_self[0].name -match 'sub_82000000' -and $pj.top_self[0].category -eq 'guest') $(if ($pj) { "$($pj.top_self[0].name) ($($pj.top_self[0].category)), rounds/s $($pj.duration.rounds_per_s), duration $($pj.duration.seconds) s from $($pj.duration.source)" })
    Check 'profile: thread names from the LSPX trailer' ($pj -and (@($pj.threads | Where-Object { $_.name -eq 'fake-main' }).Count -eq 1)) ''
}
if ($Only -contains 'crash') {
    $c = RunCase 'crash' @('-Seconds', '25', '-Warmup', '2', '-Arg', 'fake_crash_after=4', '-CloseTimeoutSec', '10')
    Check 'crash: exit 1, verdict CRASHED' ($c.code -eq 1 -and $c.sum.verdict -eq 'CRASHED') "code $($c.code), verdict $($c.sum.verdict), exited_early $($c.run.exited_early), wer $($c.run.wer_seen), exit $($c.run.exit_code_hex), close $($c.run.close_method), $($c.secs) s"
    Check 'crash: crash evidence (events or WER)' (@($c.run.crash_events).Count -gt 0 -or $c.run.wer_seen) ((@($c.run.crash_events) | ForEach-Object { "$($_.id) $($_.provider)" }) -join '; ')
}
if ($Only -contains 'kill') {
    $c = RunCase 'kill' @('-Seconds', '5', '-Warmup', '1', '-Arg', 'fake_ignore_close', '-CloseTimeoutSec', '4')
    Check 'kill: WM_CLOSE ignored -> killed after the timeout' ($c.run.close_method -eq 'killed' -and $c.run.close_seconds -ge 4) "close $($c.run.close_method) after $($c.run.close_seconds) s, windows at close: $(@($c.run.windows_at_close) -join ' / ')"
}
if ($Only -contains 'input') {
    # Virtual XInput pad: build a self-test copy, check that a bad script is refused, then drive the fake game with a
    # route. The gate copy (build\agent3\vpad\xinput1_4.dll, whose sha256 the B-gate runs record) must stay as it is.
    $ErrorActionPreference = 'Continue'
    $gateDll = Join-Path $repo 'build\agent3\vpad\xinput1_4.dll'
    $gateHash = if (Test-Path $gateDll) { (Get-FileHash -LiteralPath $gateDll -Algorithm SHA256).Hash } else { 'none' }
    $stVpad = Join-Path $repo 'build\agent3\selftest-bin\vpad'; $stDll = Join-Path $stVpad 'xinput1_4.dll'
    $bo = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $h 'vpad\build-vpad.ps1') -OutDir $stVpad -Force 2>&1 | ForEach-Object { "$_" }; $bcode = $LASTEXITCODE
    $bad = Join-Path $runs 'bad-route.txt'
    [IO.File]::WriteAllLines($bad, [string[]]@('wait_first_frame', 'press A+Q'))
    $bout = & powershell -NoProfile -ExecutionPolicy Bypass -File $rg -BinDir $bin -Exe fakedimensions.exe -RunsRoot $runs -Tag inputbad -AllowConcurrent -DryRun -InputScript $bad 2>&1 | ForEach-Object { "$_" }; $badCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $bo | ForEach-Object { "   | $_" } | Write-Host
    Check 'input: build-vpad.ps1 -OutDir -Force built the self-test xinput1_4.dll (clang-cl, no CRT)' ($bcode -eq 0 -and (Test-Path $stDll) -and ($bo -join ' ') -match 'built ') "code $bcode, $stDll"
    Check 'input: a bad script is refused before the launch (exit 2, file:line)' ($badCode -eq 2 -and ($bout -join ' ') -match 'bad -InputScript: bad-route\.txt:2: bad button') "code $badCode, $(@($bout | Where-Object { $_ -match 'InputScript' }) -join ' ')"
    $c = RunCase 'input' @('-Seconds', '40', '-Warmup', '2', '-StatsWarmup', '1', '-InputScript', (Join-Path $h 'routes\selftest-input.txt'), '-VPadDll', $stDll)
    $in = $c.run.input_script
    Check 'input: exit 0, every step ran, the script ended the run, WM_CLOSE' ($c.code -eq 0 -and $in.steps_total -gt 0 -and $in.steps_done -eq $in.steps_total -and $in.stopped_by_script -and -not $in.error -and $c.run.close_method -eq 'wm_close' -and $c.secs -lt 40) "code $($c.code), steps $($in.steps_done)/$($in.steps_total), stopped $($in.stopped_by_script), error '$($in.error)', close $($c.run.close_method), $($c.secs) s"
    Check 'input: the game loaded the run-dir xinput1_4.dll; none in the bin dir; --input_backend=xinput, AGENT3_VPAD' ($null -ne $in -and $in.dll_loaded_by_pid -eq $c.run.pid -and $in.dll_loaded_from -eq (Join-Path $c.dir 'xinput1_4.dll') -and $in.dll_maps -eq 1 -and -not (Test-Path (Join-Path $bin 'xinput1_4.dll')) -and $c.run.command_line -match '--input_backend=xinput' -and $c.run.env.AGENT3_VPAD -eq (Join-Path $c.dir 'vpad-state.bin')) "pid $($in.dll_loaded_by_pid) (game $($c.run.pid)), maps $($in.dll_maps), from '$($in.dll_loaded_from)'"
    $glog = if ($c.dir) { @(Get-Content (Join-Path $c.dir 'game.log')) } else { @() }
    $pad = @($glog | ForEach-Object { if ($_ -match 'fake xinput: result 0 buttons (0x[0-9A-F]{4}) lx -?\d+ ly (-?\d+)') { "$($Matches[1])/$($Matches[2])" } })
    $want = '0x0000/0 0x1000/0 0x0000/0 0x0010/0 0x0000/0 0x0002/0 0x0000/0 0x0002/0 0x0000/0 0x2000/0 0x0000/0 0x0000/-32767 0x0000/0'
    Check 'input: XInputGetState saw the presses, stick and releases in order' (($pad -join ' ') -eq $want -and $in.pad_reads -gt 100 -and $in.pad_active_reads -gt 0) "$($pad -join ' '); reads $($in.pad_reads) ($($in.pad_active_reads) with input)"
    $keys = @($glog | ForEach-Object { if ($_ -match 'fake xinput: key (0x[0-9A-F]{4}) flags (\d)') { "$($Matches[1])/$($Matches[2])" } })
    $wantK = '0x5800/1 0x5800/2 0x5814/1 0x5814/2 0x5811/1 0x5811/2 0x5811/1 0x5811/2 0x5801/1 0x5801/2'
    Check 'input: XInputGetKeystroke handed out the key-down/key-up events in order' (($keys -join ' ') -eq $wantK -and $in.key_events -eq 10) "$($keys -join ' '); key_events $($in.key_events) ($($in.key_calls) calls)"
    $rows = if ($c.dir -and (Test-Path (Join-Path $c.dir 'input.csv'))) { @(Import-Csv (Join-Path $c.dir 'input.csv')) } else { @() }
    $wc = @($rows | Where-Object { $_.cmd -eq 'wait_change' }); $done = @($rows | Where-Object { $_.cmd -eq 'mark' -and $_.args -eq 'done' })
    Check 'input: input.csv: waits ok, wait_scene/wait_change saw the A press change the scene, 1 TIMEOUT (on purpose)' (
        @($rows | Where-Object { $_.cmd -eq 'wait_first_frame' -and $_.result -like 'ok*' }).Count -eq 1 -and
        @($rows | Where-Object { $_.cmd -eq 'wait_scene' -and $_.result -like 'ok*' }).Count -eq 2 -and
        $wc.Count -eq 1 -and $wc[0].result -like 'ok*900/120000 -> 910/120001*' -and
        @($rows | Where-Object { $_.result -like 'TIMEOUT*' }).Count -eq 1 -and $in.timeouts -eq 1 -and
        $done.Count -eq 1 -and [int]$done[0].scene_draws -eq 910 -and [int]$done[0].pad_reads -gt 0 -and $rows[-1].cmd -eq 'end') "$($rows.Count) rows; wait_change '$(if ($wc) { $wc[0].result })'; timeouts $($in.timeouts) (line $($in.timeout_lines)); 'done' draws $(if ($done) { $done[0].scene_draws })"
    $gateAfter = if (Test-Path $gateDll) { (Get-FileHash -LiteralPath $gateDll -Algorithm SHA256).Hash } else { 'none' }
    Check 'input: the gate DLL build\agent3\vpad\xinput1_4.dll is unchanged; the run used the self-test copy' ($gateAfter -eq $gateHash -and $in.dll_sha256 -eq (Get-FileHash -LiteralPath $stDll -Algorithm SHA256).Hash) "gate $($gateHash.Substring(0, [Math]::Min(16, $gateHash.Length))) -> $($gateAfter.Substring(0, [Math]::Min(16, $gateAfter.Length))); run dll $("$($in.dll_sha256)".Substring(0, [Math]::Min(16, "$($in.dll_sha256)".Length)))"
}
$fails = @($results | Where-Object { $_ -like 'FAIL*' }).Count
$results.Insert(0, "harness self-test $(Get-Date -Format s): $($results.Count - $fails) passed, $fails failed")
[IO.File]::WriteAllLines((Join-Path $repo 'build\agent3\selftest-latest.txt'), [string[]]$results)
Write-Host $results[0]
if ($fails) { exit 1 }
