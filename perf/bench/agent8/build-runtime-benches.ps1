<#
  Builds and runs the agent8 runtime microbenches (old vs new):
    cheat_engine (TakeResults cache, freeze thread, destructor, per-row cost),
    discord_presence (thread wake-ups, Stop latency),
    native_atomics (Enabled() check on the hot hooks).

  From the repo root:
    powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\build-runtime-benches.ps1
  Options: -Runs 5  -TakeBudgetMs 150  -NoBuild  -NoRun  -Targets cheat_old,cheat_new,discord_old,discord_new,atomics

  Everything goes to build\agent8\bench\{obj,bin,logs}; the parsed summary is
  logs\summary.txt (+ logs\summary.md). The real sources are compiled
  unchanged from DimensionsRecomp\rexlego\src against bench\agent8\stubs.

  CPU budget: builds are sequential and single-threaded (lld /threads:1);
  runs use at most 2 busy threads (cheat 'take': scan worker + waiting driver;
  atomics contended: 2 workers). The freeze/discord runs are four processes at
  once but sleep almost the whole time (that is what they measure).
#>
param(
  [int]$Runs = 5,
  [double]$TakeBudgetMs = 150,
  [string[]]$Targets = @('cheat_old', 'cheat_new', 'discord_old', 'discord_new', 'atomics'),
  [switch]$NoBuild,
  [switch]$NoRun
)
$ErrorActionPreference = 'Continue'
# powershell -File passes "-Targets a,b" as one string; split it.
$Targets = @($Targets | ForEach-Object { $_ -split ',' } | Where-Object { $_ })

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
. (Join-Path $Root 'env\devshell.ps1') -Quiet

$Out = Join-Path $Root 'build\agent8\bench'
$Obj = Join-Path $Out 'obj'
$Bin = Join-Path $Out 'bin'
$Logs = Join-Path $Out 'logs'
New-Item -ItemType Directory -Force -Path $Obj, $Bin, $Logs | Out-Null

$B = Join-Path $Root 'bench\agent8'
$Src = Join-Path $Root 'DimensionsRecomp\rexlego\src'
$Fmt = Join-Path $Root 'DimensionsRecomp\rexglue-sdk\thirdparty\fmt\include'
$Stubs = Join-Path $B 'stubs'

# The game's flags (rexlego/CMakeLists.txt: -O3 -march=x86-64-v3, C++23) plus
# the SDK's WIN32_LEAN_AND_MEAN / NOMINMAX.
$CxxFlags = @('-O3', '-std=c++23', '-march=x86-64-v3', '-DNOMINMAX', '-DWIN32_LEAN_AND_MEAN',
  '-D_CRT_SECURE_NO_WARNINGS', '-Wall', "-I$Stubs")
$LinkFlags = @('-fuse-ld=lld', '-Wl,/threads:1')
$BuildLog = Join-Path $Logs 'build.log'

function Invoke-Tool([string]$What, [string]$Exe, [string[]]$ArgList) {
  Write-Host "[build] $What"
  Add-Content -Path $BuildLog -Value ("> $Exe " + ($ArgList -join ' '))
  $output = @(& $Exe @ArgList 2>&1 | ForEach-Object { "$_" })
  $code = $LASTEXITCODE
  if ($output.Count) { $output | Add-Content -Path $BuildLog; $output | Write-Host }
  if ($code -ne 0) { throw "FAILED ($code): $What" }
}

function Invoke-Compile([string]$What, [string]$Source, [string]$Object, [string[]]$Extra = @()) {
  $a = @($CxxFlags) + @($Extra | Where-Object { $_ }) + @('-c', $Source, '-o', $Object)
  Invoke-Tool $What 'clang++' $a
}

function Invoke-Link([string]$What, [string[]]$Objects, [string]$Exe) {
  Invoke-Tool $What 'clang++' (@($LinkFlags) + $Objects + @('-o', $Exe))
}

# The discord objects must call bench_CreateFileA (no_real_discord.h), never the
# real CreateFileA: Discord is running here and must not be connected to.
function Assert-NoRealCreateFile([string]$Object) {
  $syms = @(& llvm-nm $Object 2>&1 | ForEach-Object { "$_" })
  if ($LASTEXITCODE -ne 0) { throw "llvm-nm failed on $Object" }
  $bad = @($syms | Where-Object { $_ -match '\s(__imp_)?CreateFile[AW2]?\s*$' })
  $good = @($syms | Where-Object { $_ -match '\sbench_CreateFileA\s*$' })
  if ($bad.Count -or -not $good.Count) {
    throw "SAFETY: $Object references the real CreateFile ($($bad -join '; ')) or not bench_CreateFileA"
  }
  $line = "[build] safety ok: $([IO.Path]::GetFileName($Object)) references bench_CreateFileA only"
  Write-Host $line
  Add-Content -Path $BuildLog -Value $line
}

if (-not $NoBuild) {
  Set-Content -Path $BuildLog -Value ("BUILD " + (Get-Date -Format s) + " " + ((& clang++ --version 2>&1 | Select-Object -First 1) -join ''))
  $cheat = Join-Path $B 'cheat'
  $discord = Join-Path $B 'discord'
  if ($Targets -contains 'cheat_old') {
    Invoke-Compile 'cheat_engine.cpp (old copy)' (Join-Path $cheat 'old\cheat_engine.cpp') (Join-Path $Obj 'cheat_engine_old.o')
    Invoke-Compile 'bench_cheat.cpp (old)' (Join-Path $cheat 'bench_cheat.cpp') (Join-Path $Obj 'bench_cheat_old.o') @('-DBENCH_OLD')
    Invoke-Link 'bench_cheat_old.exe' @((Join-Path $Obj 'cheat_engine_old.o'), (Join-Path $Obj 'bench_cheat_old.o')) (Join-Path $Bin 'bench_cheat_old.exe')
  }
  if ($Targets -contains 'cheat_new') {
    Invoke-Compile 'cheat_engine.cpp (current source)' (Join-Path $Src 'cheat_engine.cpp') (Join-Path $Obj 'cheat_engine_new.o') @("-I$Src")
    Invoke-Compile 'bench_cheat.cpp (new)' (Join-Path $cheat 'bench_cheat.cpp') (Join-Path $Obj 'bench_cheat_new.o') @("-I$Src")
    Invoke-Link 'bench_cheat_new.exe' @((Join-Path $Obj 'cheat_engine_new.o'), (Join-Path $Obj 'bench_cheat_new.o')) (Join-Path $Bin 'bench_cheat_new.exe')
  }
  $discordFlags = @("-I$Src", "-I$Fmt", '-DFMT_HEADER_ONLY', '-include', (Join-Path $discord 'no_real_discord.h'))
  if ($Targets -contains 'discord_old') {
    Invoke-Compile 'discord_presence.cpp (old copy)' (Join-Path $discord 'old\discord_presence.cpp') (Join-Path $Obj 'discord_presence_old.o') $discordFlags
    Assert-NoRealCreateFile (Join-Path $Obj 'discord_presence_old.o')
    Invoke-Compile 'bench_discord.cpp (old)' (Join-Path $discord 'bench_discord.cpp') (Join-Path $Obj 'bench_discord_old.o') @("-I$Src", '-DBENCH_OLD')
    Invoke-Link 'bench_discord_old.exe' @((Join-Path $Obj 'discord_presence_old.o'), (Join-Path $Obj 'bench_discord_old.o')) (Join-Path $Bin 'bench_discord_old.exe')
  }
  if ($Targets -contains 'discord_new') {
    Invoke-Compile 'discord_presence.cpp (current source)' (Join-Path $Src 'discord_presence.cpp') (Join-Path $Obj 'discord_presence_new.o') $discordFlags
    Assert-NoRealCreateFile (Join-Path $Obj 'discord_presence_new.o')
    Invoke-Compile 'bench_discord.cpp (new)' (Join-Path $discord 'bench_discord.cpp') (Join-Path $Obj 'bench_discord_new.o') @("-I$Src")
    Invoke-Link 'bench_discord_new.exe' @((Join-Path $Obj 'discord_presence_new.o'), (Join-Path $Obj 'bench_discord_new.o')) (Join-Path $Bin 'bench_discord_new.exe')
  }
  if ($Targets -contains 'atomics') {
    Invoke-Compile 'bench_atomics.cpp' (Join-Path $B 'atomics\bench_atomics.cpp') (Join-Path $Obj 'bench_atomics.o')
    Invoke-Link 'bench_atomics.exe' @((Join-Path $Obj 'bench_atomics.o')) (Join-Path $Bin 'bench_atomics.exe')
  }
}

if ($NoRun) { return }

$LoadLog = Join-Path $Logs 'load.txt'
Get-ChildItem -Path $Logs -Filter '*.txt' | Remove-Item -ErrorAction SilentlyContinue

function Get-LoadLine([string]$Tag) {
  $cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
  $procs = @(Get-Process -Name 'clang*', 'ninja', 'cl', 'lld*', 'link', 'rustc', 'cargo' -ErrorAction SilentlyContinue)
  "LOAD $Tag time=$(Get-Date -Format 'HH:mm:ss') cpu_load_pct=$cpu compiler_procs=$($procs.Count)"
}

function Start-Bench([string]$Name, [string]$Exe, [string[]]$Arguments) {
  $p = Start-Process -FilePath (Join-Path $Bin $Exe) -ArgumentList $Arguments -NoNewWindow -PassThru `
    -RedirectStandardOutput (Join-Path $Logs "$Name.out.txt") -RedirectStandardError (Join-Path $Logs "$Name.err.txt")
  $null = $p.Handle  # keeps ExitCode readable after exit
  $p | Add-Member -NotePropertyName BenchName -NotePropertyValue $Name
  return $p
}

function Wait-Bench($p, [int]$TimeoutSec = 180) {
  if (-not $p.WaitForExit($TimeoutSec * 1000)) {
    Write-Warning "$($p.BenchName) timed out; killing"
    $p.Kill()
    $p.WaitForExit()
  }
  $line = "RUN $($p.BenchName) exit=$($p.ExitCode) cpu_s=$([math]::Round($p.TotalProcessorTime.TotalSeconds, 2)) wall_s=$([math]::Round(($p.ExitTime - $p.StartTime).TotalSeconds, 2))"
  Write-Host $line
  Add-Content -Path $LoadLog -Value $line
}

$cpuName = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
Add-Content -Path $LoadLog -Value "MACHINE $cpuName logical=$([Environment]::ProcessorCount) start=$(Get-Date -Format s) runs=$Runs take_budget_ms=$TakeBudgetMs"

# 1. native_atomics: LEGO_NATIVE_ATOMICS semantics.
foreach ($mode in 'unset', '0', '1') {
  Wait-Bench (Start-Bench "atomics_verify_$mode" 'bench_atomics.exe' @('verify', $mode))
}

# 2. cheat_engine TakeResults: old/new interleaved, alternating order, never concurrent.
for ($r = 1; $r -le $Runs; $r++) {
  $order = if ($r % 2) { @('old', 'new') } else { @('new', 'old') }
  foreach ($v in $order) {
    Add-Content -Path $LoadLog -Value (Get-LoadLine "cheat_take_${v}_r$r")
    Wait-Bench (Start-Bench "cheat_take_${v}_r$r" "bench_cheat_$v.exe" @('take', "$TakeBudgetMs"))
  }
}

# 3. native_atomics timing (5 interleaved rounds inside one process).
Add-Content -Path $LoadLog -Value (Get-LoadLine 'atomics_time')
Wait-Bench (Start-Bench 'atomics_time' 'bench_atomics.exe' @('time', '5', '20000000', '1000000'))

# 4. Idle-dominated wake-up benches, launch order alternating per run.
for ($r = 1; $r -le $Runs; $r++) {
  Add-Content -Path $LoadLog -Value (Get-LoadLine "idle_group_r$r")
  $jobs = @(
    @("cheat_freeze_old_r$r", 'bench_cheat_old.exe', @('freeze')),
    @("cheat_freeze_new_r$r", 'bench_cheat_new.exe', @('freeze')),
    @("discord_old_r$r", 'bench_discord_old.exe', @('10', '10')),
    @("discord_new_r$r", 'bench_discord_new.exe', @('10', '10')))
  if ($r % 2 -eq 0) { [array]::Reverse($jobs) }
  $procs = foreach ($j in $jobs) { Start-Bench $j[0] $j[1] $j[2] }
  foreach ($p in $procs) { Wait-Bench $p }
}
Add-Content -Path $LoadLog -Value (Get-LoadLine 'end')

# 5. Summary: median/min/max over every RESULT line per (bench, variant, key).
$inv = [Globalization.CultureInfo]::InvariantCulture
$results = @{}
$units = @{}
$checks = New-Object System.Collections.Generic.List[string]
foreach ($f in Get-ChildItem -Path $Logs -Filter '*.out.txt') {
  foreach ($line in Get-Content $f.FullName) {
    if ($line -match '^RESULT (\S+) (\S+) (\S+) (\S+) (\S+)') {
      $k = "$($Matches[1])|$($Matches[2])|$($Matches[3])"
      if (-not $results.ContainsKey($k)) {
        $results[$k] = New-Object System.Collections.Generic.List[double]
        $units[$k] = $Matches[5]
      }
      $results[$k].Add([double]::Parse($Matches[4], $inv))
    } elseif ($line -match '^CHECK (\S+) (\S+) (\S+) (PASS|FAIL) ?(.*)$') {
      $checks.Add("$($Matches[4]) $($Matches[1]) $($Matches[2]) $($Matches[3]) [$($f.BaseName -replace '\.out$','')] $($Matches[5])")
    }
  }
}

function Get-Stat($list) {
  $s = @($list | Sort-Object)
  $n = $s.Count
  $med = if ($n % 2) { $s[[int][math]::Floor($n / 2)] } else { ($s[$n / 2 - 1] + $s[$n / 2]) / 2 }
  [pscustomobject]@{ Median = $med; Min = $s[0]; Max = $s[$n - 1]; N = $n }
}

$summary = New-Object System.Collections.Generic.List[string]
$md = New-Object System.Collections.Generic.List[string]
$summary.Add("SUMMARY $(Get-Date -Format s) runs=$Runs (median / min / max over all RESULT lines)")
$md.Add('| bench | variant | metric | median | min | max | n | unit |')
$md.Add('|---|---|---|---:|---:|---:|---:|---|')
$stats = @{}
foreach ($k in ($results.Keys | Sort-Object)) {
  $st = Get-Stat $results[$k]
  $stats[$k] = $st
  $p = $k.Split('|')
  $summary.Add(('{0,-8} {1,-8} {2,-32} median={3,-12:G6} min={4,-12:G6} max={5,-12:G6} n={6,-4} {7}' -f $p[0], $p[1], $p[2], $st.Median, $st.Min, $st.Max, $st.N, $units[$k]))
  $md.Add(('| {0} | {1} | {2} | {3:G4} | {4:G4} | {5:G4} | {6} | {7} |' -f $p[0], $p[1], $p[2], $st.Median, $st.Min, $st.Max, $st.N, $units[$k]))
}

$summary.Add('')
$summary.Add('TakeResults(200) per frame at 60 fps (median per call x 60):')
$md.Add('')
$md.Add('| scenario | old ns/call | new ns/call | old/new | old ms per second @60fps | new ms per second @60fps | old % of 16.67 ms frame | new % of frame |')
$md.Add('|---|---:|---:|---:|---:|---:|---:|---:|')
foreach ($id in 'a', 'b', 'c', 'd') {
  $o = $stats["cheat|old|take200_ns_$id"]; $n = $stats["cheat|new|take200_ns_$id"]
  if ($o -and $n) {
    $ratio = $o.Median / [math]::Max($n.Median, 1e-9)
    $summary.Add(('  {0}: old {1:G6} ns  new {2:G6} ns  ratio {3:N1}x  old {4:N3} ms/s ({5:N3}% of frame)  new {6:N4} ms/s ({7:N5}% of frame)' -f $id, $o.Median, $n.Median, $ratio, ($o.Median * 60 / 1e6), ($o.Median / 16.6667e6 * 100), ($n.Median * 60 / 1e6), ($n.Median / 16.6667e6 * 100)))
    $md.Add(('| {0} | {1:G4} | {2:G4} | {3:N0}x | {4:N3} | {5:N4} | {6:N3}% | {7:N5}% |' -f $id, $o.Median, $n.Median, $ratio, ($o.Median * 60 / 1e6), ($n.Median * 60 / 1e6), ($o.Median / 16.6667e6 * 100), ($n.Median / 16.6667e6 * 100)))
  }
}

$pass = @($checks | Where-Object { $_.StartsWith('PASS') }).Count
$fail = @($checks | Where-Object { $_.StartsWith('FAIL') })
$summary.Add('')
$summary.Add("CHECKS pass=$pass fail=$($fail.Count)")
foreach ($c in $fail) { $summary.Add("  $c") }
$summary.Add('Distinct checks (name: pass/total):')
$groups = $checks | ForEach-Object { $t = $_.Split(' '); [pscustomobject]@{ Name = "$($t[1]) $($t[2]) $($t[3])"; Pass = ($t[0] -eq 'PASS') } } | Group-Object Name | Sort-Object Name
foreach ($g in $groups) { $summary.Add(('  {0}: {1}/{2}' -f $g.Name, @($g.Group | Where-Object { $_.Pass }).Count, $g.Count)) }

$summary | Set-Content -Path (Join-Path $Logs 'summary.txt')
$md | Set-Content -Path (Join-Path $Logs 'summary.md')
$summary | Write-Host
Write-Host "logs: $Logs"
