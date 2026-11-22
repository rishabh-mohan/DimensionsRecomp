<#
.SYNOPSIS
  End-to-end self-test for rexlego/src/sample_profiler.cpp + analyze_profile.py.

.DESCRIPTION
  1. Builds build\agent8\profiler\profiler_selftest.exe (+ .map) from the UNCHANGED
     sample_profiler.cpp and selftest\profiler_selftest.cpp with clang-cl / lld-link,
     sequentially, lld-link /threads:1. Skipped when the outputs are up to date.
  2. Runs it with LEGO_SAMPLE_PROFILE=1 and LEGO_SAMPLE_PROFILE_TRIGGER=<file>; the exe
     records ~N s through the trigger file and writes profile-<tick>.bin next to itself.
  3. Analyses the profile (JSON) and checks the known hot spots, waits, guest naming,
     demangling, the optional LSPX trailer, and that every report mode runs.
  Copies the .bin, the reports and the JSON to bench\agent8\profiler\ (timestamped)
  and writes bench\agent8\profiler\selftest-latest.txt. Exit code 1 on any FAIL.

.EXAMPLE
  powershell -NoProfile -File DimensionsRecomp\tools\native-cpu\run_selftest.ps1
  powershell -NoProfile -File DimensionsRecomp\tools\native-cpu\run_selftest.ps1 -Rebuild -Seconds 3
#>
param(
    [switch]$Rebuild,
    [double]$Seconds = 3.0
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$root = (Resolve-Path (Join-Path $here '..\..\..')).Path
$out = Join-Path $root 'build\agent8\profiler'
$bench = Join-Path $root 'bench\agent8\profiler'
New-Item -ItemType Directory -Force $out, $bench | Out-Null

$srcProf = Join-Path $root 'DimensionsRecomp\rexlego\src\sample_profiler.cpp'
$srcTest = Join-Path $here 'selftest\profiler_selftest.cpp'
$objProf = Join-Path $out 'sample_profiler.obj'
$objTest = Join-Path $out 'profiler_selftest.obj'
$exe = Join-Path $out 'profiler_selftest.exe'
$map = Join-Path $out 'profiler_selftest.map'
$analyzer = Join-Path $here 'analyze_profile.py'
$cpu = [ordered]@{ build = 0.0; exe = 0.0; analysis = 0.0 }

function Test-Stale([string]$src, [string]$dst) {
    -not (Test-Path $dst) -or (Get-Item $src).LastWriteTimeUtc -gt (Get-Item $dst).LastWriteTimeUtc
}

# Runs a program, returns its exit code, adds its CPU time to $cpu[$bucket].
function Invoke-Tool([string]$bucket, [string]$file, [string[]]$argv, [string]$stdout = '') {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $file
    $psi.Arguments = ($argv | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' '
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = [bool]$stdout
    $p = [System.Diagnostics.Process]::Start($psi)
    if ($stdout) {
        $text = $p.StandardOutput.ReadToEnd()
        [IO.File]::WriteAllText($stdout, $text)
    }
    $p.WaitForExit()
    $script:cpu[$bucket] += $p.TotalProcessorTime.TotalSeconds
    return $p.ExitCode
}

# ---- toolchain + python ------------------------------------------------------------
. (Join-Path $root 'env\devshell.ps1') -Quiet
$py = $null
foreach ($cand in @('python', 'py')) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    $pre = if ($cand -eq 'py') { @('-3') } else { @() }
    & $cmd.Source @pre -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $cmd.Source; $pyPre = $pre; break }
}
if (-not $py) { throw 'Python 3.11+ not found (python / py -3)' }

# ---- build (1 thread, incremental) ------------------------------------------------
$cflags = @('/nologo', '/O2', '/EHsc', '/std:c++20', '/D_CRT_SECURE_NO_WARNINGS', '/c')
foreach ($pair in @(@($srcProf, $objProf), @($srcTest, $objTest))) {
    if ($Rebuild -or (Test-Stale $pair[0] $pair[1])) {
        Write-Host "compile $(Split-Path -Leaf $pair[0])"
        $rc = Invoke-Tool 'build' (Get-Command clang-cl).Source ($cflags + @($pair[0], "/Fo$($pair[1])"))
        if ($rc) { throw "clang-cl failed ($rc): $($pair[0])" }
    }
}
if ($Rebuild -or (Test-Stale $objProf $exe) -or (Test-Stale $objTest $exe)) {
    Write-Host 'link profiler_selftest.exe'
    $rc = Invoke-Tool 'build' (Get-Command lld-link).Source @('/nologo', '/threads:1', "/MAP:$map", "/OUT:$exe",
        $objProf, $objTest, 'psapi.lib', 'winmm.lib', 'user32.lib', 'kernel32.lib')
    if ($rc) { throw "lld-link failed ($rc)" }
}

# ---- run ------------------------------------------------------------------------------
$trigger = Join-Path $out 'selftest.trigger'
$roles = Join-Path $out 'selftest-roles.json'
Remove-Item $trigger, $roles -ErrorAction SilentlyContinue
$env:LEGO_SAMPLE_PROFILE = '1'
$env:LEGO_SAMPLE_PROFILE_TRIGGER = $trigger
try {
    Write-Host "run profiler_selftest.exe ($Seconds s recording)"
    $rc = Invoke-Tool 'exe' $exe @($roles, "$Seconds")
} finally {
    Remove-Item Env:LEGO_SAMPLE_PROFILE, Env:LEGO_SAMPLE_PROFILE_TRIGGER -ErrorAction SilentlyContinue
}
if ($rc -ne 0 -or -not (Test-Path $roles)) { throw "profiler_selftest.exe failed (exit $rc)" }
$r = Get-Content $roles -Raw | ConvertFrom-Json
$bin = $r.profile
if (-not $bin -or -not (Test-Path $bin)) { throw "no profile produced ($bin)" }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$pfx = Join-Path $bench "selftest-$stamp"
Copy-Item $bin "$pfx.bin"
Copy-Item $roles "$pfx-roles.json"

function Invoke-Analyzer([string[]]$argv, [string]$stdout = '') {
    $rc = Invoke-Tool 'analysis' $py ($pyPre + @($analyzer) + $argv) $stdout
    if ($rc) { throw "analyze_profile.py $($argv -join ' ') failed ($rc)" }
}
Invoke-Analyzer @($bin, $map, '--json', '--top', '40', '-o', "$pfx-summary.json")
Invoke-Analyzer @($bin, $map, '-o', "$pfx-summary.txt")
Invoke-Analyzer @($bin, $map, '--focus', '^lsp_selftest_hot$', '--json', '-o', "$pfx-focus.json")
Invoke-Analyzer @($bin, $map, '--folded', '--folded-thread', '-o', "$pfx-folded.txt")
Invoke-Analyzer @($bin, $map, '--by', 'module', '--include-waits', '-o', "$pfx-modules.txt")
Invoke-Analyzer @($bin, $map, '--by', 'module', '--json', '-o', "$pfx-modules.json")
Invoke-Analyzer @($bin, $map, '--fold-guest', '--json', '-o', "$pfx-foldguest.json")
Invoke-Analyzer @('--diff', $bin, $map, $bin, $map, '--json', '-o', "$pfx-diff.json")

$S = Get-Content "$pfx-summary.json" -Raw | ConvertFrom-Json
$F = Get-Content "$pfx-focus.json" -Raw | ConvertFrom-Json
$M = Get-Content "$pfx-modules.json" -Raw | ConvertFrom-Json
$G = Get-Content "$pfx-foldguest.json" -Raw | ConvertFrom-Json
$D = Get-Content "$pfx-diff.json" -Raw | ConvertFrom-Json
$folded = Get-Content "$pfx-folded.txt"

$results = New-Object System.Collections.Generic.List[object]
function Add-Check([string]$name, [bool]$ok, [string]$detail) {
    $results.Add([pscustomobject]@{ Result = $(if ($ok) { 'PASS' } else { 'FAIL' }); Check = $name; Detail = $detail })
}
function Get-Thread($json, $tid) { $json.threads | Where-Object { $_.tid -eq [int64]$tid } | Select-Object -First 1 }
function Ratio($a, $b) { if ($b) { [double]$a / [double]$b } else { 0.0 } }

$tm = Get-Thread $S $r.main
$tg = Get-Thread $S $r.guest
$tw = Get-Thread $S $r.waiter
$ts = Get-Thread $S $r.sleeper

# (1) main thread busy leaf in lsp_selftest_hot
$hot = @($tm.top_self | Where-Object { $_.name -eq 'lsp_selftest_hot' })[0]
$x = Ratio $hot.samples $tm.busy
Add-Check 'main: busy leaf in lsp_selftest_hot >= 80%' ($x -ge 0.8) ('{0}/{1} = {2:p1}' -f $hot.samples, $tm.busy, $x)

# (2) guest thread self in sub_8200BEEF, guest 0x8200BEEF, category guest
$ge = @($tg.top_self | Where-Object { $_.guest_addr -eq '0x8200BEEF' })[0]
$x = Ratio $ge.samples $tg.busy
$ok = ($x -ge 0.8) -and ($ge.name -like 'sub_8200BEEF*') -and ($ge.category -eq 'guest')
Add-Check 'guest: self in sub_8200BEEF [guest 0x8200BEEF] >= 80%' $ok ('"{0}" cat={1}: {2}/{3} = {4:p1}' -f $ge.name, $ge.category, $ge.samples, $tg.busy, $x)
# Hook detection is checked on the map itself: sub_8200CAFE runs only every 16th loop
# iteration, so it may get no samples when the machine is busy and the sample rate drops.
$rcH = Invoke-Tool 'analysis' $py ($pyPre + @((Join-Path $PSScriptRoot 'selftest\map_hooks.py'), $map, '0x8200CAFE')) "$pfx-hooks.json"
$H = if ($rcH -eq 0) { Get-Content "$pfx-hooks.json" -Raw | ConvertFrom-Json } else { $null }
$hk = @($H.entries | Where-Object { $_.kind -eq 'hooked original' })[0]
$hh = @($H.entries | Where-Object { $_.kind -eq 'hook' })[0]
Add-Check 'map: hook / hooked original of 0x8200CAFE detected' ([bool]$hk -and [bool]$hh) ('"{0}" {1} ({2}), "{3}" {4} ({5})' -f $hk.name, $hk.rva, $hk.kind, $hh.name, $hh.rva, $hh.kind)

# (3) waiter + sleeper classified waiting
$xw = Ratio $tw.waiting $tw.samples
$xs = Ratio $ts.waiting $ts.samples
Add-Check 'waiter: >= 90% waiting' ($xw -ge 0.9) ('{0}/{1} = {2:p1}' -f $tw.waiting, $tw.samples, $xw)
Add-Check 'sleeper: >= 90% waiting' ($xs -ge 0.9) ('{0}/{1} = {2:p1}' -f $ts.waiting, $ts.samples, $xs)
Add-Check 'demangle: waiter role is selftest::Waiter' ($tw.role -like 'selftest::Waiter*') ('role="{0}", sleeper role="{1}"' -f $tw.role, $ts.role)

# (4) inclusive + focus
$outer = @($tm.top_inclusive | Where-Object { $_.name -eq 'lsp_selftest_outer' })[0]
$x = Ratio $outer.samples $tm.busy
Add-Check 'main: lsp_selftest_outer inclusive >= 80% of busy' ($x -ge 0.8) ('{0}/{1} = {2:p1}' -f $outer.samples, $tm.busy, $x)
$fc = @($F.focus.callers | Where-Object { $_.name -eq 'lsp_selftest_outer' })[0]
Add-Check '--focus lsp_selftest_hot: caller lsp_selftest_outer' ([bool]$fc) ('caller {0} samples ({1}% of focus {2})' -f $fc.samples, $fc.pct, $F.focus.inclusive)

# (5) other modes
$fl = @($folded | Where-Object { $_ -match 'lsp_selftest_outer;lsp_selftest_hot \d+$' })
Add-Check '--folded has outer;hot stacks' ($fl.Count -gt 0) ('{0} lines, {1} with outer;hot' -f $folded.Count, $fl.Count)
$me = @($M.modules_self | Where-Object { $_.module -eq 'profiler_selftest.exe' })[0]
Add-Check '--by module lists profiler_selftest.exe' ([bool]$me) ('{0} busy samples ({1}%)' -f $me.samples, $me.pct)
$gg = Get-Thread $G $r.guest
Add-Check '--fold-guest folds sub_8200BEEF into guest' ($gg.top_self[0].name -eq 'guest [folded]') ('top self "{0}" {1}' -f $gg.top_self[0].name, $gg.top_self[0].samples)
Add-Check '--diff self vs self: all deltas 0' ([double]$D.max_abs_delta_self -eq 0.0) ('max |delta| = {0} {1}' -f $D.max_abs_delta_self, $D.unit)

# (6) LSPX trailer (only if the sampler on disk writes one)
$expectTrailer = [bool](Select-String -Path $srcProf -Pattern 'LSPX' -Quiet)
if ($expectTrailer) {
    $t = $S.trailer
    $ok = $t -and $t.timer_mode -eq 1 -and $t.rounds -gt 0 -and $S.duration.seconds -gt 0 -and $S.duration.source -eq 'trailer'
    Add-Check 'trailer: parsed, timer_mode 1, rounds > 0, duration > 0' $ok ('timer_mode={0} rounds={1} duration={2:n3}s observer_effect={3}' -f $t.timer_mode, $t.rounds, $S.duration.seconds, $S.timer_observer_effect)
    $names = @(@($tm, 'selftest-main'), @($tg, 'selftest-guest'), @($tw, 'selftest-waiter'), @($ts, 'selftest-sleeper'))
    $bad = @($names | Where-Object { $_[0].name -ne $_[1] } | ForEach-Object { "$($_[0].tid)='$($_[0].name)'" })
    Add-Check 'trailer: thread names map to the right tids' ($bad.Count -eq 0) $(if ($bad.Count) { 'mismatch: ' + ($bad -join ', ') } else { 'main/guest/waiter/sleeper ok' })
} else {
    $results.Add([pscustomobject]@{ Result = 'SKIP'; Check = 'trailer checks'; Detail = 'sampler on disk writes no LSPX trailer (legacy)' })
}

# ---- report ----------------------------------------------------------------------------
$fails = @($results | Where-Object { $_.Result -eq 'FAIL' }).Count
$rate = Ratio $S.duration.rounds $S.duration.seconds
$lines = @()
$lines += "profiler self-test $stamp : $(if ($fails) { "FAIL ($fails)" } else { 'PASS' })"
$lines += "profile: $pfx.bin ($($S.samples) samples, $($S.threads_seen) threads, duration $($S.duration.seconds) s [$($S.duration.source)], rounds $($S.duration.rounds), ~$([math]::Round($rate)) rounds/s)"
$lines += "threads: main=$($r.main) guest=$($r.guest) waiter=$($r.waiter) sleeper=$($r.sleeper)"
$lines += $results | ForEach-Object { '{0}  {1}: {2}' -f $_.Result, $_.Check, $_.Detail }
$lines += ('cpu seconds: build {0:n1}, exe {1:n1}, analysis {2:n1} (total {3:n1})' -f $cpu.build, $cpu.exe, $cpu.analysis, ($cpu.build + $cpu.exe + $cpu.analysis))
$lines += "reports: $pfx-*.json / *.txt"
$lines | ForEach-Object { Write-Host $_ }
[IO.File]::WriteAllLines((Join-Path $bench 'selftest-latest.txt'), [string[]]$lines)
[IO.File]::WriteAllLines("$pfx-result.txt", [string[]]$lines)
Remove-Item $bin -ErrorAction SilentlyContinue   # the copy in bench\ is kept
if ($fails) { exit 1 }
exit 0
