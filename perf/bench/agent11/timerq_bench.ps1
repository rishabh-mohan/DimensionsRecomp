<#
.SYNOPSIS
  Agent 11, S3 task #10 lead: why rex::thread::TimerQueue uses 52-62% of a core (window 3).
  Builds bench_timerq.exe (it links the LIVE rexglue-sdk src/core/timer_queue.cpp, unmodified)
  and runs it: the P/E masks, the disruptorplus spin_wait costs per logical processor, then one
  1 ms recurring timer (as xboxkrnl_module.cpp's KeTimeStampBundle timer) in the default spin
  wait and with REX_TIMER_WAIT_BLOCKING=1, at the OS default timer resolution and at 1 ms,
  then the spin wait pinned to the P cores and to the E cores.
  No game. One busy thread at a time (<= 2 threads), single-threaded cl.
  Log: build\agent11\timerq\results-<time>.txt
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_bench.ps1
#>
param(
  [int]$Seconds = 10,
  [switch]$NoBuild,
  [switch]$SkipMasks,
  [switch]$IgnoreGame,   # run even while a legodimensions process is up (default: wait for it)
  [int]$MaxWaitMin = 20
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$out = Join-Path $root 'build\agent11\timerq'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$exe = Join-Path $out 'bench_timerq.exe'
$log = Join-Path $out ('results-{0:yyyyMMdd-HHmmss}.txt' -f (Get-Date))
function Say([string]$s) { Write-Host $s; Add-Content -Path $log -Value $s -Encoding ascii }

$sdk = 'DimensionsRecomp\rexglue-sdk'
$tq = Join-Path $root "$sdk\src\core\timer_queue.cpp"
$hash = (Get-FileHash $tq -Algorithm SHA256).Hash.Substring(0, 12)
$cpuName = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name.Trim()
Say ('# timerq_bench {0:yyyy-MM-dd HH:mm:ss}  {1}  timer_queue.cpp {2}  seconds {3}' -f (Get-Date), $cpuName, $hash, $Seconds)

if (-not $NoBuild) {
  . (Join-Path $root 'env\devshell.ps1') -Quiet
  $o = & cl /nologo /O2 /std:c++20 /EHsc /W3 /DNDEBUG /DNOMINMAX `
    /I bench\agent11\timerq_shim /I "$sdk\include" /I "$sdk\thirdparty\disruptorplus\include" `
    bench\agent11\bench_timerq.cpp "$sdk\src\core\timer_queue.cpp" `
    "/Fe:$exe" "/Fo:$out\" winmm.lib 2>&1
  $code = $LASTEXITCODE
  $o | ForEach-Object { Say "[cl] $_" }
  if ($code -ne 0) { Say "BUILD FAILED (cl exit $code)"; exit 1 }
  Say "built $exe"
}

function Wait-NoGame {
  if ($IgnoreGame) { return $true }
  $deadline = (Get-Date).AddMinutes($MaxWaitMin)
  $said = $false
  while (Get-Process legodimensions* -ErrorAction SilentlyContinue) {
    if (-not $said) { Say ('# {0:HH:mm:ss} a legodimensions process is running (Agent 8''s slot): waiting' -f (Get-Date)); $said = $true }
    if ((Get-Date) -gt $deadline) { Say "# still running after $MaxWaitMin min: stopping here"; return $false }
    Start-Sleep -Seconds 5
  }
  if ($said) { Say ('# {0:HH:mm:ss} game gone, continuing' -f (Get-Date)) }
  return $true
}

function Invoke-Bench([string]$label, [string[]]$benchArgs, [bool]$blocking = $false) {
  if (-not (Wait-NoGame)) { return $false }
  $bat = Get-CimInstance Win32_Battery | Select-Object -First 1
  $load = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
  $busy = (Get-Process cl, link, ninja, cmake, clang*, lld* -ErrorAction SilentlyContinue | Measure-Object).Count
  Say ''
  Say ('## {0}  [{1:HH:mm:ss}  AC={2}  charge={3}%  CPU load {4}%  compiler/linker processes {5}]  bench_timerq {6}{7}' -f `
      $label, (Get-Date), ($bat.BatteryStatus -eq 2), $bat.EstimatedChargeRemaining, $load, $busy, ($benchArgs -join ' '),
      $(if ($blocking) { '  (REX_TIMER_WAIT_BLOCKING=1)' } else { '' }))
  if ($blocking) { $env:REX_TIMER_WAIT_BLOCKING = '1' } else { Remove-Item Env:REX_TIMER_WAIT_BLOCKING -ErrorAction SilentlyContinue }
  try {
    $o = & $exe @benchArgs 2>&1
    $code = $LASTEXITCODE
  } finally {
    Remove-Item Env:REX_TIMER_WAIT_BLOCKING -ErrorAction SilentlyContinue
  }
  $o | ForEach-Object { Say "$_" }
  if ($code -ne 0) { Say "(exit $code)" }
  return $true
}

$ok = Invoke-Bench 'P/E classes' @('classes')
$masks = @{}
if ($ok) {
  $line = (Get-Content $log | Where-Object { $_ -match '^P 0x([0-9a-f]+) E 0x([0-9a-f]+)' } | Select-Object -Last 1)
  if ($line -match '^P 0x([0-9a-f]+) E 0x([0-9a-f]+)') { $masks.P = $Matches[1]; $masks.E = $Matches[2] }
}
if ($ok) { $ok = Invoke-Bench 'spin_wait costs' @('spin', '300') }
foreach ($tbp in 0, 1) {
  foreach ($blk in $false, $true) {
    if ($ok) {
      $ok = Invoke-Bench ("1 ms timer, {0}, timeBeginPeriod {1}" -f $(if ($blk) { 'blocking' } else { 'spin' }), $tbp) `
        @('run', "$Seconds", "$tbp") $blk
    }
  }
}
if (-not $SkipMasks -and $masks.Count -eq 2) {
  foreach ($k in 'P', 'E') {
    if ($ok -and $masks[$k] -ne '0') {
      $ok = Invoke-Bench ("1 ms timer, spin, timeBeginPeriod 0, {0} cores only" -f $k) @('run', "$Seconds", '0', $masks[$k]) $false
    }
  }
}
Say ''
Say ('# done {0:HH:mm:ss}  log {1}' -f (Get-Date), $log)
