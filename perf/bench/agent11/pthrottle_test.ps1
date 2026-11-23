# pthrottle_test.ps1 - S4 task #19 (host_execution_throttling_optout, default OFF): builds and
# runs bench\agent11\pthrottle_test.cpp, the read-back test for the staged change.
# 1. Checks the stage copies (build\agent11\pthrottle\stage, made by pthrottle_stage.ps1)
#    against HASHES.txt.
# 2. Copies the code under test VERBATIM out of the staged and the pristine copies:
#      include\rex\threading_timing.h  struct HostTimingConfig { ... };
#      threading_win.cpp block 1       timer_period_ms_ ... the opt-out function (anonymous
#                                      namespace in the source; wrapped in one here too)
#      threading_win.cpp block 2       ConfigureHostTiming and RestoreHostTiming
#    into build\agent11\pthrottle\gen\pthrottle_impl.inc as namespaces pristine_impl and
#    staged_impl, with #line directives so diagnostics point at the stage copies. Every marker
#    must be found exactly once, and the extracts are sanity-checked (old vs new function,
#    the new field only in the staged copies, no namespace inside any extract, ASCII only).
# 3. Compiles the test with cl (/W4, one source file, no /MP: single-threaded).
# 4. Runs it. The test starts one child process per configuration (the throttling state is per
#    process), one at a time, and reads the state back with GetProcessInformation.
# No game runs, no builds of the game or SDK, nothing in the live tree is read or written.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_test.ps1 [-NoRun]
# Output: build\agent11\pthrottle\test-<stamp>.txt (hashes, extracts, compile, test log).
# Exit code: the test's (0 = PASS, 1 = a check failed); 2 = stage copy or extract check
# failed; 3 = compile failed.
param([switch]$NoRun)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$base = Join-Path $root 'build\agent11\pthrottle'
$stage = Join-Path $base 'stage'
$gen = Join-Path $base 'gen'
$obj = Join-Path $base 'obj'
$runDir = Join-Path $base 'run'
$exe = Join-Path $base 'pthrottle_test.exe'
$src = Join-Path $root 'bench\agent11\pthrottle_test.cpp'
$stamp = '{0:yyyyMMdd-HHmmss}' -f (Get-Date)
$report = Join-Path $base "test-$stamp.txt"
$log = New-Object System.Collections.Generic.List[string]
function Say([string]$s) { $log.Add($s); Write-Host $s }
function Save() { Set-Content -LiteralPath $report -Value $log -Encoding ascii; Write-Host "report: $report" }
function Fail([string]$s, [int]$code) { Say "RESULT: FAIL ($s)"; Save; exit $code }
foreach ($d in $gen, $obj, $runDir) {
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}
Say "# pthrottle_test (S4 task #19)  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ---- 1. the stage copies must be the ones pthrottle_stage.ps1 recorded ----
$hashFile = Join-Path $stage 'HASHES.txt'
if (-not (Test-Path $hashFile)) { Fail 'no HASHES.txt: run bench\agent11\pthrottle_stage.ps1 first' 2 }
$want = @{}
foreach ($l in (Get-Content -LiteralPath $hashFile)) {
  if ($l -match '^(\S+)\s+(pristine|staged)\s+([0-9A-Fa-f]{64})\s*$') {
    $want["$($Matches[2])/$($Matches[1])"] = $Matches[3].ToUpper()
  }
}
$copies = [ordered]@{
  'pristine/threading_timing.h' = 'pristine\include\rex\threading_timing.h'
  'pristine/threading_win.cpp'  = 'pristine\threading_win.cpp'
  'staged/threading_timing.h'   = 'include\rex\threading_timing.h'
  'staged/threading_win.cpp'    = 'threading_win.cpp'
}
$texts = @{}
foreach ($k in $copies.Keys) {
  $path = Join-Path $stage $copies[$k]
  if (-not $want.ContainsKey($k)) { Fail "HASHES.txt has no line for $k" 2 }
  if (-not (Test-Path $path)) { Fail "missing stage copy $path" 2 }
  $h = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  if ($h -ne $want[$k]) { Fail "$k is $($h.Substring(0, 12)), HASHES.txt says $($want[$k].Substring(0, 12)): re-stage" 2 }
  Say ('stage copy {0,-28} sha256 {1}  matches HASHES.txt' -f $k, $h.Substring(0, 12))
  $texts[$k] = [IO.File]::ReadAllText($path).Replace("`r`n", "`n")
}

# ---- 2. extract the code under test ----
function Count-Of([string]$text, [string]$s) {
  $n = 0; $i = 0
  while (($i = $text.IndexOf($s, $i, [StringComparison]::Ordinal)) -ge 0) { $n++; $i += $s.Length }
  return $n
}
# The text from $from (found exactly once) up to $to. Inclusive: $to is the first match after
# $from and is kept. Otherwise $to must occur exactly once in the file and is left out.
function Cut([string]$text, [string]$from, [string]$to, [bool]$inclusive, [string]$what) {
  $n = Count-Of $text $from
  if ($n -ne 1) { Fail "$what : start marker '$from' found $n times, expected once" 2 }
  $i = $text.IndexOf($from, [StringComparison]::Ordinal)
  if (-not $inclusive) {
    $n = Count-Of $text $to
    if ($n -ne 1) { Fail "$what : end marker '$to' found $n times, expected once" 2 }
  }
  $j = $text.IndexOf($to, $i + $from.Length, [StringComparison]::Ordinal)
  if ($j -lt 0) { Fail "$what : end marker '$to' not found after the start marker" 2 }
  if ($inclusive) { $j += $to.Length }
  $body = $text.Substring($i, $j - $i).TrimEnd("`n")
  $first = $text.Substring(0, $i).Split("`n").Count
  return @{ Text = $body; Line = $first; Last = $first + $body.Split("`n").Count - 1 }
}
$cuts = @{}
foreach ($impl in 'pristine', 'staged') {
  $cuts["$impl/h"] = Cut $texts["$impl/threading_timing.h"] 'struct HostTimingConfig {' '};' $true "$impl header"
  $cuts["$impl/b1"] = Cut $texts["$impl/threading_win.cpp"] `
    '// Period of the timeBeginPeriod() request this process holds, 0 if none.' `
    '// One high-resolution waitable timer per thread for precise sleeps, created' $false "$impl block 1"
  $cuts["$impl/b2"] = Cut $texts["$impl/threading_win.cpp"] `
    'void ConfigureHostTiming(const HostTimingConfig& config) {' `
    'bool WaitUntilSuspended(Thread* thread) {' $false "$impl block 2"
}
foreach ($k in ($cuts.Keys | Sort-Object)) {
  Say ('extract {0,-12} lines {1}-{2}' -f $k, $cuts[$k].Line, $cuts[$k].Last)
}
function Need([bool]$ok, [string]$what) {
  if (-not $ok) { Fail "extract check: $what" 2 }
  Say "extract check ok: $what"
}
$ph = $cuts['pristine/h'].Text; $sh = $cuts['staged/h'].Text
$pb1 = $cuts['pristine/b1'].Text; $sb1 = $cuts['staged/b1'].Text
$pb2 = $cuts['pristine/b2'].Text; $sb2 = $cuts['staged/b2'].Text
Need ($sb1.Contains('bool OptOutOfPowerThrottling(ULONG control_mask) {') -and -not $sb1.Contains('KeepTimerResolutionInBackground')) 'staged block 1 has OptOutOfPowerThrottling(control_mask), not the old function'
Need ($pb1.Contains('bool KeepTimerResolutionInBackground() {') -and -not $pb1.Contains('OptOutOfPowerThrottling')) 'pristine block 1 has KeepTimerResolutionInBackground(), not the new function'
Need ($pb1.Contains('timer_period_ms_') -and $sb1.Contains('timer_period_ms_') -and $pb1.Contains('GetTimePeriodFn') -and $sb1.Contains('GetTimePeriodFn')) 'both blocks 1 hold timer_period_ms_ and GetTimePeriodFn'
Need ($pb2.Contains('void RestoreHostTiming() {') -and $sb2.Contains('void RestoreHostTiming() {')) 'both blocks 2 hold ConfigureHostTiming and RestoreHostTiming'
Need ($sh.Contains('keep_execution_speed_in_background') -and -not $ph.Contains('keep_execution_speed_in_background')) 'the new field is in the staged header only'
Need ($sb2.Contains('config.keep_execution_speed_in_background') -and -not $pb2.Contains('keep_execution_speed_in_background')) 'the new field is used in the staged block 2 only'
$nsHits = @($cuts.Keys | Where-Object { $cuts[$_].Text.Contains('namespace') })
Need ($nsHits.Count -eq 0) "no extract contains a namespace line ($($nsHits -join ', '))"
$wide = @($cuts.Keys | Where-Object { $cuts[$_].Text -match '[^\x00-\x7F]' })
Need ($wide.Count -eq 0) "every extract is ASCII ($($wide -join ', '))"

$incName = 'build/agent11/pthrottle/gen/pthrottle_impl.inc'
$incPath = Join-Path $gen 'pthrottle_impl.inc'
$inc = New-Object System.Collections.Generic.List[string]
function Add-Cut([string]$file, $c) {
  $inc.Add(('#line {0} "{1}"' -f $c.Line, $file))
  foreach ($x in $c.Text.Split("`n")) { $inc.Add($x) }
  $inc.Add(('#line {0} "{1}"' -f ($inc.Count + 2), $incName))
}
$inc.Add("// GENERATED by bench/agent11/pthrottle_test.ps1 ($stamp); do not edit. Verbatim extracts")
$inc.Add('// from build/agent11/pthrottle/stage, checked against HASHES.txt; #line points at them.')
foreach ($impl in 'pristine', 'staged') {
  $rel = $(if ($impl -eq 'pristine') { 'build/agent11/pthrottle/stage/pristine' } else { 'build/agent11/pthrottle/stage' })
  $inc.Add("namespace ${impl}_impl {")
  $inc.Add("// $rel/include/rex/threading_timing.h sha256 $($want["$impl/threading_timing.h"].Substring(0, 12))")
  Add-Cut "$rel/include/rex/threading_timing.h" $cuts["$impl/h"]
  $inc.Add("// $rel/threading_win.cpp sha256 $($want["$impl/threading_win.cpp"].Substring(0, 12))")
  $inc.Add('namespace {')
  Add-Cut "$rel/threading_win.cpp" $cuts["$impl/b1"]
  $inc.Add('}  // namespace')
  Add-Cut "$rel/threading_win.cpp" $cuts["$impl/b2"]
  $inc.Add("}  // namespace ${impl}_impl")
}
[IO.File]::WriteAllText($incPath, (($inc -join "`n") + "`n"), (New-Object System.Text.ASCIIEncoding))
Say ('generated {0} ({1} lines, sha256 {2})' -f $incName, $inc.Count, (Get-FileHash -LiteralPath $incPath -Algorithm SHA256).Hash.Substring(0, 12))

# ---- 3. compile (one source file, no /MP) ----
if (Test-Path $exe) { Remove-Item -LiteralPath $exe -Force }
. (Join-Path $root 'env\devshell.ps1') -Quiet -Jobs 1
$old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$ver = @(& cl 2>&1 | ForEach-Object { "$_" } | Where-Object { $_.Trim() })
$clArgs = @('/nologo', '/O2', '/std:c++20', '/EHsc', '/W4', '/DNDEBUG', "/I$gen", $src,
  "/Fe:$exe", ('/Fo:' + (Join-Path $obj 'pthrottle_test.obj')))
$clOut = @(& cl @clArgs 2>&1 | ForEach-Object { "$_" })
$clCode = $LASTEXITCODE
$ErrorActionPreference = $old
if ($ver.Count) { Say "compiler: $($ver[0])" }
Say "compile: cl $($clArgs -join ' ')"
$clOut | Where-Object { $_.Trim() } | ForEach-Object { Say "  | $_" }
$warnings = @($clOut | Where-Object { $_ -match ': warning [A-Z]+\d+' })
$errors = @($clOut | Where-Object { $_ -match ': (fatal )?error [A-Z]+\d+' })
Say ('compile exit {0}: {1} warning(s), {2} error(s)' -f $clCode, $warnings.Count, $errors.Count)
if ($clCode -ne 0 -or -not (Test-Path $exe)) { Fail "compile failed (exit $clCode)" 3 }
if ($NoRun) { Say 'RESULT: compiled (-NoRun)'; Save; exit 0 }

# ---- 4. run ----
Say "run: $exe $runDir"
$ErrorActionPreference = 'Continue'
$testOut = @(& $exe $runDir 2>&1 | ForEach-Object { "$_" })
$testCode = $LASTEXITCODE
$ErrorActionPreference = $old
$testOut | ForEach-Object { Say $_ }
Say "test exit code $testCode"
Save
exit $testCode
