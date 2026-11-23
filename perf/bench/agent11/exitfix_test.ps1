# exitfix_test.ps1 - task #27 unit test (no game). Builds exit_test.cpp (/MD,
# like the game, and /MT) and exit_test_dll.cpp (/MD /LD) with cl, runs every
# mode once per CRT flavour (one child at a time, 10 s timeout each), and checks
# the exit code and the markers against the expected table below.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_test.ps1 [-NoBuild]
# Output: build\agent11\exitfix\test-<stamp>.txt (table + verdict) and one run
# dir per case under build\agent11\exitfix\test-<stamp>\. Exit 0 = every
# asserted cell matched. Columns marked (info) are recorded, not asserted.
# No CIM/WMI, no Get-Process: System.Diagnostics.Process only.
param([switch]$NoBuild)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$binRel = 'build\agent11\exitfix\bin'
$bin = Join-Path $root $binRel
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runRoot = Join-Path $root "build\agent11\exitfix\test-$stamp"
$report = "$runRoot.txt"
New-Item -ItemType Directory -Force -Path "$bin\md", "$bin\mt", "$bin\dll", $runRoot | Out-Null

function Native([string]$exe, [string[]]$argList) {
  $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  $o = & $exe @argList 2>&1
  $ErrorActionPreference = $old
  return , @($LASTEXITCODE, ($o | Out-String))
}

if (-not $NoBuild) {
  . (Join-Path $root 'env\devshell.ps1') -Quiet
  $common = @('/nologo', '/O2', '/std:c++20', '/EHsc', '/W3')
  $builds = @(
    @('exit_test_md.exe', @('/MD', 'bench\agent11\exit_test.cpp', "/Fe:$binRel\exit_test_md.exe", "/Fo:$binRel\md\")),
    @('exit_test_mt.exe', @('/MT', 'bench\agent11\exit_test.cpp', "/Fe:$binRel\exit_test_mt.exe", "/Fo:$binRel\mt\")),
    @('exit_test_dll.dll', @('/MD', '/LD', 'bench\agent11\exit_test_dll.cpp', "/Fe:$binRel\exit_test_dll.dll", "/Fo:$binRel\dll\"))
  )
  foreach ($b in $builds) {
    $r = Native 'cl' ($common + $b[1])
    if ($r[0] -ne 0) { Write-Host $r[1]; throw "build failed: $($b[0])" }
    if ($r[1] -match 'warning') { Write-Host $r[1] }
    Write-Host "built $($b[0])"
  }
}

# expected: 1 = marker present, 0 = absent; log -1 = (info)
$modes = [ordered]@{
  'exit0'          = @{ code = 0; atexit = 1; static = 1; raced = 1; dll = 1; dllraced = 0; log = 1 }
  'exit1'          = @{ code = 1; atexit = 1; static = 1; raced = 1; dll = 1; dllraced = 0; log = 1 }
  '_Exit0'         = @{ code = 0; atexit = 0; static = 0; raced = 0; dll = 1; dllraced = 0; log = 1 }
  '_Exit1'         = @{ code = 1; atexit = 0; static = 0; raced = 0; dll = 1; dllraced = 0; log = 1 }
  '_Exit1_noflush' = @{ code = 1; atexit = 0; static = 0; raced = 0; dll = 1; dllraced = 0; log = -1 }
  'terminate1'     = @{ code = 1; atexit = 0; static = 0; raced = 0; dll = 0; dllraced = 0; log = 1 }
}
$dll = Join-Path $bin 'exit_test_dll.dll'
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add(('{0,-4} {1,-15} {2,5} {3,7} {4,8} {5,6} {6,6} {7,6} {8,4} {9,8} {10,4} {11,10} {12,4} {13,4}  {14}' -f `
  'crt', 'mode', 'code', 'wall_ms', 'exit_ms', 'atexit', 'static', 'raced', 'dll', 'dllraced', 'log', 'csv(info)', 'ret', 'tmo', 'verdict'))
$bad = 0
foreach ($crt in 'md', 'mt') {
  $exe = Join-Path $bin "exit_test_$crt.exe"
  if (-not (Test-Path -LiteralPath $exe)) { throw "missing $exe (run without -NoBuild)" }
  foreach ($mode in $modes.Keys) {
    $exp = $modes[$mode]
    $dir = Join-Path $runRoot "$crt-$mode"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $psi.Arguments = "$mode `"$dir`" `"$dll`""
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = [Diagnostics.Process]::Start($psi)
    $done = $p.WaitForExit(10000)
    if (-not $done) { try { $p.Kill() } catch { }; [void]$p.WaitForExit(5000) }
    $wall = $sw.Elapsed.TotalMilliseconds
    $code = 'timeout'; $exitMs = ''
    if ($done) {
      $code = $p.ExitCode
      $f = Join-Path $dir 'exit_call.txt'
      if (Test-Path -LiteralPath $f) {
        $t0 = [long]([IO.File]::ReadAllText($f).Trim())
        $exitMs = '{0:N1}' -f (($p.ExitTime.ToFileTimeUtc() - $t0) / 10000.0)
      }
    }
    $p.Dispose()
    $has = { param($n) [int](Test-Path -LiteralPath (Join-Path $dir $n)) }
    $got = @{
      atexit = & $has 'atexit.marker'; static = & $has 'static_dtor.marker'; raced = & $has 'dtor_raced.marker'
      dll = & $has 'dll_dtor.marker'; dllraced = & $has 'dll_dtor_raced.marker'
      ret = & $has 'returned.marker'; tmo = & $has 'main_timeout.marker'
    }
    $logText = ''; $lf = Join-Path $dir 'log.txt'; if (Test-Path -LiteralPath $lf) { $logText = [IO.File]::ReadAllText($lf) }
    $csvText = ''; $cf = Join-Path $dir 'csv.txt'; if (Test-Path -LiteralPath $cf) { $csvText = [IO.File]::ReadAllText($cf) }
    $got.log = [int]($logText -match 'requesting process exit')
    $got.csv = [int]($csvText -match '16\.6')
    $miss = @()
    if ("$code" -ne "$($exp.code)") { $miss += "code=$code want $($exp.code)" }
    foreach ($k in 'atexit', 'static', 'raced', 'dll', 'dllraced', 'log') {
      if ($exp[$k] -ge 0 -and $got[$k] -ne $exp[$k]) { $miss += "$k=$($got[$k]) want $($exp[$k])" }
    }
    if ($got.ret) { $miss += 'exit call returned' }
    if ($got.tmo) { $miss += 'main timeout' }
    $verdict = 'ok'; if ($miss.Count) { $verdict = 'MISMATCH: ' + ($miss -join '; '); $bad++ }
    $logCell = "$($got.log)"; if ($exp.log -lt 0) { $logCell += '(i)' }
    $rows.Add(('{0,-4} {1,-15} {2,5} {3,7:N0} {4,8} {5,6} {6,6} {7,6} {8,4} {9,8} {10,4} {11,10} {12,4} {13,4}  {14}' -f `
      $crt, $mode, $code, $wall, $exitMs, $got.atexit, $got.static, $got.raced, $got.dll, $got.dllraced, $logCell, $got.csv, $got.ret, $got.tmo, $verdict))
  }
}
$head = @(
  "# exitfix_test (task #27)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  host $env:COMPUTERNAME",
  '# Each case: exit_test.exe <mode> from a non-main thread while a heartbeat thread runs and one thread is blocked.',
  '# 1 = marker present. raced = heartbeat still running during the EXE static destructor (the #27 hazard).',
  '# dll = exit_test_dll.dll static destructor ran (DLL_PROCESS_DETACH). exit_ms = process exit time - exit call time.',
  '# csv = unflushed FILE* row survived (info; perf.csv stand-in). (i) = informational cell.',
  ''
)
$tail = @('', $(if ($bad) { "RESULT: FAIL ($bad mismatching case(s))" } else { 'RESULT: PASS (all asserted cells match)' }))
Set-Content -LiteralPath $report -Value ($head + $rows + $tail) -Encoding ascii
($head + $rows + $tail) | ForEach-Object { Write-Host $_ }
Write-Host "report: $report"
if ($bad) { exit 1 }
exit 0
