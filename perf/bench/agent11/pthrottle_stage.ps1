# pthrottle_stage.ps1 - S4 staging, task #19 (Agent 1, 04:07): an OFF-by-default cvar,
# host_execution_throttling_optout, that opts the process out of Windows execution speed
# throttling (PROCESS_POWER_THROTTLING_EXECUTION_SPEED, EcoQoS) at startup, through the
# SetProcessInformation(ProcessPowerThrottling) call the SDK already makes for
# host_timer_throttling_optout. Three files in DimensionsRecomp/rexglue-sdk:
#   include/rex/threading_timing.h  HostTimingConfig::keep_execution_speed_in_background
#   src/core/threading_win.cpp      KeepTimerResolutionInBackground() becomes
#                                   OptOutOfPowerThrottling(control_mask); ConfigureHostTiming
#                                   passes both opt-outs in ONE call (each call replaces the
#                                   whole state: probed 04:11, 0x4 then 0x1 reads back 0x1)
#   src/system/runtime.cpp          the cvar (default false) and the config line
# Off, nothing changes: no new call, and with only host_timer_throttling_optout on, the call
# (ControlMask 0x4, StateMask 0) and the log lines are the live ones. On with the timer flag,
# a failed combined call (Windows 10 rejects the timer flag) is retried with 0x1 alone.
# Why: perf-notes/agent11-kernel.md, "S4 staging (task #19)" (the slow state of the
# hidden-desktop runs: E cores at minimum clock, the EcoQoS hypothesis).
# Text only: staging writes nothing outside build\agent11\pthrottle\stage.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1          # stage + self-check
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1 -Check   # live still pristine?
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1 -Apply   # staged -> live
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1 -Revert  # pristine -> live
#
# -Apply / -Revert are for whoever lands it, and only after Agent 10 rates it SAFE and Agent 1
# says go (S4 candidate). Same rules as exitfix_stage.ps1: Apply refuses unless EVERY live file
# still equals its pristine hash (or is already applied) and every staged copy equals
# HASHES.txt; Revert refuses unless every live file equals its staged hash (or is already
# pristine). Both check all three files before copying any, and stamp each copied live file's
# LastWriteTime with the copy time (Copy-Item keeps the source's).
# Stage: each edit target must occur exactly once; line endings and BOM are preserved; the diff
# comes from read-only "git diff --no-index" with headers rewritten to the repo paths.
# Layout: build\agent11\pthrottle\stage\{include\rex\threading_timing.h, threading_win.cpp,
# runtime.cpp} and the same under stage\pristine\ (the include\ trees are the -I roots that
# pthrottle_syntax.ps1 puts first). Tests: pthrottle_syntax.ps1 (clang, exact flags) and
# pthrottle_test.ps1 (the staged functions compiled into a test exe that reads the process
# state back with GetProcessInformation).
# Pure ASCII on purpose (PowerShell 5.1 reads BOM-less scripts as ANSI).
param([switch]$Apply, [switch]$Revert, [switch]$Check)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stage = Join-Path $root 'build\agent11\pthrottle\stage'
$pristineDir = Join-Path $stage 'pristine'
$hashFile = Join-Path $stage 'HASHES.txt'
Set-Location $root

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function NL([string]$s) { ($s -replace "`r`n", "`n").TrimEnd("`n") + "`n" }
# Copy-Item keeps the source's LastWriteTime (Agent 12, 00:03), so -Apply / -Revert stamp
# the live file with the copy time; otherwise ninja could keep an object built from the old
# text after the source copy was written. Content and hash are unchanged by this.
function Stamp-Now([string]$p) { (Get-Item -LiteralPath $p).LastWriteTime = Get-Date }

# ---- the edits (old text -> new text), LF here; converted to the file's newline ----
$files = @(
  @{
    Name  = 'threading_timing.h'
    Rel   = 'include\rex\threading_timing.h'
    Live  = 'DimensionsRecomp\rexglue-sdk\include\rex\threading_timing.h'
    Edits = @(
      # H1: the config field (leading comma: a lone pair would be flattened into 2 strings)
      , @((NL @'
  // Keep honouring the request while the window is occluded or minimized
  // (Windows 11 EcoQoS: PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION).
  bool keep_timer_resolution_in_background = false;
'@), (NL @'
  // Keep honouring the request while the window is occluded or minimized
  // (Windows 11 EcoQoS: PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION).
  bool keep_timer_resolution_in_background = false;
  // Opt out of execution speed throttling (PROCESS_POWER_THROTTLING_EXECUTION_SPEED),
  // which Windows may apply to a process without a focused window: efficiency
  // cores and low clock speeds (EcoQoS).
  bool keep_execution_speed_in_background = false;
'@))
    )
  },
  @{
    Name  = 'threading_win.cpp'
    Rel   = 'threading_win.cpp'
    Live  = 'DimensionsRecomp\rexglue-sdk\src\core\threading_win.cpp'
    Edits = @(
      # W1: the flag, spelled out like the timer flag
      @((NL @'
constexpr ULONG kPowerThrottlingIgnoreTimerResolution = 0x4;
constexpr int kProcessPowerThrottlingClass = 4;
'@), (NL @'
constexpr ULONG kPowerThrottlingIgnoreTimerResolution = 0x4;
constexpr int kProcessPowerThrottlingClass = 4;
// PROCESS_POWER_THROTTLING_EXECUTION_SPEED (EcoQoS), likewise.
constexpr ULONG kPowerThrottlingExecutionSpeed = 0x1;
'@)),
      # W2: the opt-out takes the mask
      @((NL @'
// Windows 11 ignores the timer resolution a process requested while its
// windows are minimized or occluded (EcoQoS); ask it to always honour ours.
bool KeepTimerResolutionInBackground() {
'@), (NL @'
// Windows 11 ignores the timer resolution a process requested while its
// windows are minimized or occluded (EcoQoS); ask it to always honour ours.
// Each call replaces the whole throttling state, so `control_mask` carries
// every mechanism to opt out of (controlled and off).
bool OptOutOfPowerThrottling(ULONG control_mask) {
'@)),
      # W3: ... and sets it, StateMask still 0
      @((NL @'
  state.ControlMask = kPowerThrottlingIgnoreTimerResolution;
  state.StateMask = 0;  // Controlled and off: never ignore our request.
'@), (NL @'
  state.ControlMask = control_mask;
  state.StateMask = 0;  // Controlled and off: no throttling by these mechanisms.
'@)),
      # W4: one call for both opt-outs; the execution speed one alone, or as the fallback
      @((NL @'
void ConfigureHostTiming(const HostTimingConfig& config) {
  bool background_optout = false;
  if (config.keep_timer_resolution_in_background) {
    background_optout = KeepTimerResolutionInBackground();
    if (!background_optout) {
'@), (NL @'
void ConfigureHostTiming(const HostTimingConfig& config) {
  bool background_optout = false;
  bool execution_optout = false;
  if (config.keep_timer_resolution_in_background) {
    // Both opt-outs in one call: each call replaces the whole throttling state.
    ULONG mask = kPowerThrottlingIgnoreTimerResolution;
    if (config.keep_execution_speed_in_background) {
      mask |= kPowerThrottlingExecutionSpeed;
    }
    background_optout = OptOutOfPowerThrottling(mask);
    execution_optout = background_optout && config.keep_execution_speed_in_background;
    if (!background_optout) {
'@)),
      @((NL @'
      spdlog::debug("Timer resolution power throttling opt-out failed (0x{:08X})", GetLastError());
    }
  }
  const uint32_t period = config.timer_resolution_ms;
'@), (NL @'
      spdlog::debug("Timer resolution power throttling opt-out failed (0x{:08X})", GetLastError());
    }
  }
  if (config.keep_execution_speed_in_background) {
    // On its own, or again on its own if the call above failed: Windows 10
    // rejects the timer flag but has execution speed throttling.
    if (!execution_optout) {
      execution_optout = OptOutOfPowerThrottling(kPowerThrottlingExecutionSpeed);
    }
    if (execution_optout) {
      spdlog::info("Execution speed power throttling opt-out on");
    } else {
      spdlog::warn("Execution speed power throttling opt-out failed (0x{:08X})", GetLastError());
    }
  }
  const uint32_t period = config.timer_resolution_ms;
'@))
    )
  },
  @{
    Name  = 'runtime.cpp'
    Rel   = 'runtime.cpp'
    Live  = 'DimensionsRecomp\rexglue-sdk\src\system\runtime.cpp'
    Edits = @(
      # R1: the cvar, default off
      @((NL @'
REXCVAR_DEFINE_BOOL(host_timer_throttling_optout, false, "Runtime",
                    "Keep the host timer resolution while the window is minimized or occluded");
'@), (NL @'
REXCVAR_DEFINE_BOOL(host_timer_throttling_optout, false, "Runtime",
                    "Keep the host timer resolution while the window is minimized or occluded");
// Default off (behavior changes ship off until rated SAFE); perf-notes/agent11-kernel.md,
// "S4 staging (task #19)", has the tests.
REXCVAR_DEFINE_BOOL(host_execution_throttling_optout, false, "Runtime",
                    "Opt out of Windows execution speed throttling (EcoQoS), which may run the "
                    "game on efficiency cores at low clock speeds while it has no focused window");
'@)),
      # R2: into the startup config
      @((NL @'
    timing.keep_timer_resolution_in_background = REXCVAR_GET(host_timer_throttling_optout);
'@), (NL @'
    timing.keep_timer_resolution_in_background = REXCVAR_GET(host_timer_throttling_optout);
    timing.keep_execution_speed_in_background = REXCVAR_GET(host_execution_throttling_optout);
'@))
    )
  }
)

function Read-Text([string]$p) {
  $b = [IO.File]::ReadAllBytes($p)
  $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
  $off = 0; if ($bom) { $off = 3 }
  $t = (New-Object Text.UTF8Encoding($false, $true)).GetString($b, $off, $b.Length - $off)
  return @{ Text = $t; Bom = $bom; Crlf = $t.Contains("`r`n") }
}
function Write-Text([string]$p, [string]$t, [bool]$bom) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $p) | Out-Null
  [IO.File]::WriteAllText($p, $t, (New-Object Text.UTF8Encoding($bom)))
}
function Read-Hashes {
  if (-not (Test-Path -LiteralPath $hashFile)) { throw "no $hashFile - stage first" }
  $h = @{}
  foreach ($l in Get-Content -LiteralPath $hashFile) {
    if ($l -match '^(\S+)\s+(pristine|staged)\s+([0-9A-F]{64})$') { $h["$($Matches[1])|$($Matches[2])"] = $Matches[3] }
  }
  return $h
}
function Count([string]$t, [string]$s) { ([regex]::Matches($t, [regex]::Escape($s))).Count }
function Paths($f) {
  return @{
    Live = (Join-Path $root $f.Live)
    Pr   = (Join-Path $pristineDir $f.Rel)
    St   = (Join-Path $stage $f.Rel)
  }
}

if ($Apply -or $Revert -or $Check) {
  if ((@($Apply, $Revert, $Check) | Where-Object { $_ }).Count -gt 1) { throw 'use one of -Apply, -Revert, -Check' }
  $h = Read-Hashes
  $todo = @()
  $changed = 0
  foreach ($f in $files) {
    $p = Paths $f
    $hp = $h["$($f.Name)|pristine"]; $hs = $h["$($f.Name)|staged"]
    if (-not $hp -or -not $hs) { throw "HASHES.txt has no entry for $($f.Name)" }
    if ((Sha $p.Pr) -ne $hp) { throw "pristine copy changed: $($p.Pr)" }
    if ((Sha $p.St) -ne $hs) { throw "staged copy changed: $($p.St)" }
    $ls = Sha $p.Live
    $state = if ($ls -eq $hp) { 'pristine' } elseif ($ls -eq $hs) { 'staged (applied)' } else { 'CHANGED since staging' }
    if ($Check) {
      Write-Host ("live {0}: sha {1} = {2}; LastWriteTime {3:yyyy-MM-dd HH:mm:ss}" -f $f.Live, $ls.Substring(0, 12), $state, (Get-Item -LiteralPath $p.Live).LastWriteTime)
      if ($state -like 'CHANGED*') { $changed++ }
      continue
    }
    if ($Apply) {
      if ($ls -eq $hs) { Write-Host "already applied: $($f.Live)"; continue }
      if ($ls -ne $hp) { throw "live file changed since staging (sha $ls): $($f.Live) - re-stage deliberately; nothing was copied" }
      $todo += , @($p.St, $p.Live, $hs)
    } else {
      if ($ls -eq $hp) { Write-Host "already pristine: $($f.Live)"; continue }
      if ($ls -ne $hs) { throw "live file is neither staged nor pristine (sha $ls): $($f.Live); nothing was copied" }
      $todo += , @($p.Pr, $p.Live, $hp)
    }
  }
  if ($Check) { if ($changed) { exit 1 }; exit 0 }
  foreach ($t in $todo) {
    Copy-Item -LiteralPath $t[0] -Destination $t[1] -Force
    Stamp-Now $t[1]
    if ((Sha $t[1]) -ne $t[2]) { throw "copy verification failed: $($t[1])" }
    Write-Host ("{0}: {1} <- {2} (LastWriteTime {3:HH:mm:ss})" -f $(if ($Apply) { 'applied' } else { 'reverted' }), $t[1], $t[0], (Get-Item -LiteralPath $t[1]).LastWriteTime)
  }
  exit 0
}

# ---- stage ----
New-Item -ItemType Directory -Force -Path $pristineDir | Out-Null
foreach ($f in $files) {
  $p = Paths $f
  if ((Test-Path -LiteralPath $p.Pr) -and ((Sha $p.Pr) -ne (Sha $p.Live))) {
    throw "live $($f.Live) differs from the earlier pristine copy $($p.Pr); delete build\agent11\pthrottle\stage\pristine to re-stage deliberately"
  }
}
$hashLines = @("# S4 task #19: host_execution_throttling_optout (default off), staged {0:yyyy-MM-dd HH:mm:ss} by bench\agent11\pthrottle_stage.ps1" -f (Get-Date))
$diff = New-Object Text.StringBuilder
$orig = @{}
foreach ($f in $files) {
  $p = Paths $f
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $p.Pr) | Out-Null
  Copy-Item -LiteralPath $p.Live -Destination $p.Pr -Force
  $r = Read-Text $p.Live
  $orig[$f.Name] = $r
  $text = $r.Text
  $nl = "`n"; if ($r.Crlf) { $nl = "`r`n" }
  foreach ($e in $f.Edits) {
    $old = $e[0].Replace("`n", $nl); $new = $e[1].Replace("`n", $nl)
    $n = Count $text $old
    if ($n -ne 1) { throw "$($f.Name): edit target found $n times (need exactly 1):`n$old" }
    $text = $text.Replace($old, $new)
  }
  Write-Text $p.St $text $r.Bom
  $hashLines += ('{0} pristine {1}' -f $f.Name, (Sha $p.Pr))
  $hashLines += ('{0} staged {1}' -f $f.Name, (Sha $p.St))
  # unified diff via read-only git; rewrite the headers to the repo path
  $relP = "build/agent11/pthrottle/stage/pristine/$($f.Rel.Replace('\', '/'))"
  $relS = "build/agent11/pthrottle/stage/$($f.Rel.Replace('\', '/'))"
  $tmp = Join-Path $stage "$($f.Name).diff.tmp"
  $oldEap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  & git --no-optional-locks diff --no-index --no-color "--output=$tmp" -- $relP $relS 2>&1 | Out-Null
  $ErrorActionPreference = $oldEap
  if (-not (Test-Path -LiteralPath $tmp)) { throw "git diff produced no output for $($f.Name)" }
  $repoPath = $f.Live.Replace('\', '/')
  $d = [IO.File]::ReadAllText($tmp)
  $d = $d.Replace("a/$relP", "a/$repoPath").Replace("b/$relS", "b/$repoPath")
  [void]$diff.Append($d)
  Remove-Item -LiteralPath $tmp
}
$diffPath = Join-Path $stage 'pthrottle.diff'
[IO.File]::WriteAllText($diffPath, $diff.ToString(), (New-Object Text.UTF8Encoding($false)))
$hashLines += ('pthrottle.diff sha256 {0}' -f (Sha $diffPath))
Set-Content -LiteralPath $hashFile -Value $hashLines -Encoding ascii

# ---- self-checks ----
$fail = 0
function Report([bool]$ok, [string]$what) {
  if ($ok) { Write-Host "PASS  $what" } else { Write-Host "FAIL  $what"; $script:fail++ }
}
$stx = @{}; $ptx = @{}   # (PowerShell names are case-insensitive: not $S / $P next to $s / $p)
foreach ($f in $files) {
  $p = Paths $f
  $r = $orig[$f.Name]
  $s = Read-Text $p.St
  $stx[$f.Name] = $s.Text; $ptx[$f.Name] = (Read-Text $p.Pr).Text
  Report (($s.Bom -eq $r.Bom) -and ($s.Crlf -eq $r.Crlf)) ("{0}: BOM and newline style unchanged ({1}, {2})" -f $f.Name, $(if ($r.Bom) { 'BOM' } else { 'no BOM' }), $(if ($r.Crlf) { 'CRLF' } else { 'LF' }))
  if (-not $r.Crlf) { Report (-not $s.Text.Contains("`r")) "$($f.Name): no CR introduced" }
  Report ((Sha $p.Live) -eq (Sha $p.Pr)) "$($f.Name): live file untouched (equals pristine)"
}
$d = $diff.ToString()
$dl = $d -split "`n"
$minus = @($dl | Where-Object { $_ -match '^-' -and $_ -notmatch '^---' })
$plus = @($dl | Where-Object { $_ -match '^\+' -and $_ -notmatch '^\+\+\+' })
$hunks = @($dl | Where-Object { $_ -match '^@@' })
# h: H1 +4. win: W1 +2; W2 -1 +3; W3 -2 +2; W4 -1 +20. runtime: R1 +5; R2 +1. => -4 / +37
Report (($minus.Count -eq 4) -and ($plus.Count -eq 37)) ("diff has the expected -4/+37 lines (got -{0}/+{1})" -f $minus.Count, $plus.Count)
Report (($hunks.Count -ge 4) -and ($hunks.Count -le 8)) ("diff has 4-8 hunks (got {0})" -f $hunks.Count)
Report ((@($dl | Where-Object { $_ -match '^diff --git ' })).Count -eq 3) 'diff covers the 3 files'
$long = @($plus | Where-Object { ($_.Length - 1) -gt 100 })
Report ($long.Count -eq 0) ("added lines <= 100 columns (longest {0})" -f (($plus | ForEach-Object { $_.Length - 1 } | Measure-Object -Maximum).Maximum))
$na = @($plus | Where-Object { $_ -match '[^\x00-\x7F]' })
Report ($na.Count -eq 0) 'added lines are ASCII'
$lineDelta = @{ 'threading_timing.h' = 4; 'threading_win.cpp' = 23; 'runtime.cpp' = 6 }
foreach ($k in $lineDelta.Keys) {
  $dn = ($stx[$k] -split "`n").Count - ($ptx[$k] -split "`n").Count
  Report ($dn -eq $lineDelta[$k]) ("{0} is {1} lines longer (got {2})" -f $k, $lineDelta[$k], $dn)
}
$rt = $stx['runtime.cpp']; $tw = $stx['threading_win.cpp']; $th = $stx['threading_timing.h']
$ptw = $ptx['threading_win.cpp']
Report ((Count $rt 'REXCVAR_DEFINE_BOOL(host_execution_throttling_optout, false, "Runtime",') -eq 1) 'cvar host_execution_throttling_optout defined once, default false'
Report ((Count $rt 'host_execution_throttling_optout') -eq 2) 'cvar used only by its definition and the one REXCVAR_GET'
Report ((Count $rt 'timing.keep_execution_speed_in_background = REXCVAR_GET(host_execution_throttling_optout);') -eq 1) 'Runtime::Setup passes it into HostTimingConfig'
Report ((Count $rt 'REXCVAR_DEFINE_BOOL(host_timer_throttling_optout, false, "Runtime",') -eq 1) 'host_timer_throttling_optout unchanged (default false)'
Report ((Count $th 'bool keep_execution_speed_in_background = false;') -eq 1) 'HostTimingConfig field defaults to false'
Report ((Count $tw 'constexpr ULONG kPowerThrottlingExecutionSpeed = 0x1;') -eq 1) 'kPowerThrottlingExecutionSpeed = 0x1 defined once'
Report (((Count $tw 'constexpr ULONG kPowerThrottlingIgnoreTimerResolution = 0x4;') -eq 1) -and ((Count $tw 'constexpr int kProcessPowerThrottlingClass = 4;') -eq 1)) 'timer flag and information class constants unchanged'
Report (((Count $tw 'KeepTimerResolutionInBackground') -eq 0) -and ((Count $ptw 'KeepTimerResolutionInBackground') -eq 2)) 'KeepTimerResolutionInBackground gone (pristine: definition + 1 call)'
Report ((Count $tw 'OptOutOfPowerThrottling(') -eq 3) 'OptOutOfPowerThrottling: definition + 2 calls'
Report (((Count $tw 'state.StateMask = 0;') -eq 1) -and ((Count $tw 'StateMask = ') -eq 1)) 'StateMask is only ever set to 0 (opt-outs only)'
Report ((Count $tw 'state.ControlMask = control_mask;') -eq 1) 'ControlMask comes from the caller'
Report ((Count $tw 'set_process_information(GetCurrentProcess(), kProcessPowerThrottlingClass, &state,') -eq 1) 'still one SetProcessInformation call site, on the own process'
Report ((Count $tw 'keep_execution_speed_in_background') -eq 3) 'the new field is read 3 times, all in ConfigureHostTiming'
$hostLine = 'spdlog::info("Host timer resolution set to {} ms (background opt-out {})", period,'
Report (((Count $tw $hostLine) -eq 1) -and ((Count $ptw $hostLine) -eq 1)) 'the "Host timer resolution set to" line the A/B harness greps is unchanged'
Report ((Count $tw 'background_optout ? "on" : "off");') -eq 1) '... and still reports the timer opt-out only'
$dbgLine = 'spdlog::debug("Timer resolution power throttling opt-out failed (0x{:08X})", GetLastError());'
Report (((Count $tw $dbgLine) -eq 1) -and ((Count $ptw $dbgLine) -eq 1)) 'the timer opt-out debug line is unchanged'
Report ((Count $tw 'spdlog::info("Execution speed power throttling opt-out on");') -eq 1) 'new info line when the opt-out is on'
Report ((Count $tw 'spdlog::warn("Execution speed power throttling opt-out failed (0x{:08X})", GetLastError());') -eq 1) 'new warn line when it fails'
foreach ($f in $files) {
  $p = Paths $f
  Write-Host ("staged {0}: pristine {1} -> staged {2}" -f $f.Name, (Sha $p.Pr).Substring(0, 12), (Sha $p.St).Substring(0, 12))
}
Write-Host ("diff {0} (-{1}/+{2}, {3} hunks); wrote {4}" -f (Sha $diffPath).Substring(0, 12), $minus.Count, $plus.Count, $hunks.Count, $hashFile)
if ($fail) { Write-Host "RESULT: FAIL ($fail)"; exit 1 }
Write-Host 'RESULT: PASS'
exit 0
