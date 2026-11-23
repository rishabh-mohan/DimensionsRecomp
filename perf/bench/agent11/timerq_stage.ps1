# timerq_stage.ps1 - S3 task #10 (Agent 1, 02:01): the TimerQueue lead. Stages an OFF-by-default
# cvar, timer_queue_precise_wait, in DimensionsRecomp/rexglue-sdk/src/core/timer_queue.cpp.
# Text only: staging writes nothing outside build\agent11\timerq\stage.
# Why: perf-notes/agent11-kernel.md, section "S3 TimerQueue (task #10 lead)". With the default
# phased spin wait the 1 ms KeTimeStampBundle timer keeps the timer thread 52-62% busy in the game.
# The cvar adds a third wait mode next to the REX_TIMER_WAIT_BLOCKING opt-in: the condition
# variable until 20 ms before the deadline, then SleepPrecise (high-resolution waitable timer)
# slices of at most 1 ms. It is chosen once, on the first QueueTimer call (after cvars are
# applied), before that call publishes; off, every path is the one the live code takes.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage.ps1          # stage + self-check
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage.ps1 -Check   # live still pristine?
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage.ps1 -Apply   # staged -> live
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage.ps1 -Revert  # pristine -> live
#
# -Apply / -Revert are for whoever lands it, and only after Agent 10 rates it SAFE and Agent 1
# says go. Same rules as safeorder_stage.ps1: Apply refuses unless the live file still equals the
# pristine hash and the staged copy equals HASHES.txt; Revert refuses unless live equals staged.
# Both stamp the live file's LastWriteTime with the copy time (Copy-Item keeps the source's).
# Stage: each edit target must occur exactly once; line endings and BOM are preserved; the diff
# comes from read-only "git diff --no-index" with headers rewritten to the repo path.
# Self-checks: newline style and BOM unchanged, the expected diff shape, added lines <= 100
# columns, the cvar defined once with default false, no blocking_ left, the env var still read
# once, live file untouched. Tests: timerq_syntax.ps1 (clang, exact flags) and
# timerq_stage_bench.ps1 (bench_timerq.exe linked against the staged copy).
# Pure ASCII on purpose (PowerShell 5.1 reads BOM-less scripts as ANSI).
param([switch]$Apply, [switch]$Revert, [switch]$Check)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stage = Join-Path $root 'build\agent11\timerq\stage'
$pristineDir = Join-Path $stage 'pristine'
$hashFile = Join-Path $stage 'HASHES.txt'
$name = 'timer_queue.cpp'
$liveRel = 'DimensionsRecomp\rexglue-sdk\src\core\timer_queue.cpp'
Set-Location $root

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function NL([string]$s) { ($s -replace "`r`n", "`n").TrimEnd("`n") + "`n" }
# Copy-Item keeps the source's LastWriteTime (Agent 12, 00:03), so -Apply / -Revert stamp
# the live file with the copy time; otherwise ninja could keep an object built from the old
# text after the source copy was written. Content and hash are unchanged by this.
function Stamp-Now([string]$p) { (Get-Item -LiteralPath $p).LastWriteTime = Get-Date }

# ---- the edits (old text -> new text), LF here; converted to the file's newline ----
$edits = @(
  # A: includes and the cvar
  @((NL @'
#include <rex/assert.h>
#include <rex/thread.h>
#include <rex/thread/timer_queue.h>

namespace dp = disruptorplus;
'@), (NL @'
#include <rex/assert.h>
#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/thread.h>
#include <rex/thread/timer_queue.h>

// Default off (behavior changes ship off until rated SAFE). perf-notes/agent11-kernel.md,
// "S3 TimerQueue" (task #10), has the measurements and the tests.
REXCVAR_DEFINE_BOOL(timer_queue_precise_wait, false, "Runtime",
                    "Host timer thread: sleep until the next timer is due (a condition variable, "
                    "then high-resolution sleeps). Off: the phased spin wait, which keeps a core "
                    "about half busy with the 1 ms KeTimeStampBundle timer")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace dp = disruptorplus;
'@)),
  # B: the mode, its constructor and the one-way selection
  @((NL @'
  struct Stopped {};

  TimerWaitStrategy() : blocking_(std::getenv("REX_TIMER_WAIT_BLOCKING") != nullptr) {}

'@), (NL @'
  struct Stopped {};

  // kSpin: the default phased spin. kBlocking (REX_TIMER_WAIT_BLOCKING): the
  // condition variable, whose timeouts end on an OS timer tick. kPrecise
  // (timer_queue_precise_wait): the condition variable, then high-resolution
  // sleeps for the last stretch before each deadline.
  enum class Mode { kSpin, kBlocking, kPrecise };

  TimerWaitStrategy()
      : mode_(std::getenv("REX_TIMER_WAIT_BLOCKING") != nullptr ? Mode::kBlocking : Mode::kSpin) {}

  // This queue starts during static initialization, before cvars are parsed.
  // The first QueueTimer call, which startup makes after applying the command
  // line, environment and config, picks the precise wait. The switch is one-way
  // and precedes that call's publication: publishers read the mode after the
  // call_once, and the consumer notifies only after consuming a later
  // publication, so no notify a blocked waiter needs is ever skipped as kSpin.
  void SelectMode() {
    std::call_once(mode_selected_, [this] {
      if (REXCVAR_GET(timer_queue_precise_wait)) {
        mode_.store(Mode::kPrecise, std::memory_order_release);
        REXLOG_INFO("TimerQueue: precise wait (timer_queue_precise_wait)");
      }
    });
  }

'@)),
  # C: untimed wait
  @((NL @'
      const std::atomic<dp::sequence_t>* const sequences[]) {
    if (!blocking_) {
'@), (NL @'
      const std::atomic<dp::sequence_t>* const sequences[]) {
    if (spinning()) {
'@)),
  # D: relative timeout
  @((NL @'
      const std::chrono::duration<Rep, Period>& timeout) {
    if (!blocking_) {
'@), (NL @'
      const std::chrono::duration<Rep, Period>& timeout) {
    if (spinning()) {
'@)),
  # E: deadline wait, mode read once
  @((NL @'
      const std::chrono::time_point<Clock, Duration>& deadline) {
    if (!blocking_) {
'@), (NL @'
      const std::chrono::time_point<Clock, Duration>& deadline) {
    const Mode mode = mode_.load(std::memory_order_acquire);
    if (mode == Mode::kSpin) {
'@)),
  # F: deadline wait, the precise branch
  @((NL @'
      cv_.wait(lock, ready);
    } else {
      cv_.wait_until(lock, deadline, ready);
    }
'@), (NL @'
      cv_.wait(lock, ready);
    } else if (mode == Mode::kPrecise) {
      WaitPrecise(lock, deadline, ready);
    } else {
      cv_.wait_until(lock, deadline, ready);
    }
'@)),
  # G: publishers notify in both waiting modes
  @((NL @'
  void signal_all_when_blocking() {
    if (!blocking_) {
'@), (NL @'
  void signal_all_when_blocking() {
    if (spinning()) {
'@)),
  # H: the precise wait and the members
  @((NL @'
 private:
  void ThrowIfStopped() const {
    if (stopped()) throw Stopped{};
  }

  const bool blocking_;
  std::atomic<bool> stopped_{false};
'@), (NL @'
 private:
  // Condition variable timeouts end on an OS timer tick (15.625 ms unless the
  // process raised the timer resolution), which fires a 1 ms timer in bursts.
  // Wait on it until kPreciseWindow before the deadline, then sleep the rest in
  // high-resolution slices of at most kPreciseSlice. A publication or Stop()
  // during a slice is seen when the slice ends.
  static constexpr std::chrono::milliseconds kPreciseWindow{20};
  static constexpr std::chrono::microseconds kPreciseSlice{1000};

  template <typename Clock, typename Duration, typename Ready>
  void WaitPrecise(std::unique_lock<std::mutex>& lock,
                   const std::chrono::time_point<Clock, Duration>& deadline, const Ready& ready) {
    while (!ready()) {
      const auto now = Clock::now();
      if (now >= deadline) {
        return;
      }
      if (deadline - now > kPreciseWindow) {
        cv_.wait_until(lock, deadline - kPreciseWindow, ready);
        continue;
      }
      const auto remaining = std::chrono::ceil<std::chrono::microseconds>(deadline - now);
      lock.unlock();
      SleepPrecise(std::min(remaining, kPreciseSlice));
      lock.lock();
    }
  }

  bool spinning() const { return mode_.load(std::memory_order_acquire) == Mode::kSpin; }

  void ThrowIfStopped() const {
    if (stopped()) throw Stopped{};
  }

  std::atomic<Mode> mode_;
  std::once_flag mode_selected_;
  std::atomic<bool> stopped_{false};
'@)),
  # I: QueueTimer selects the mode before it publishes
  @((NL @'
    if (wait_strategy_.stopped()) return {};
    auto wait_item_weak = std::weak_ptr<WaitItem>(wait_item);
'@), (NL @'
    if (wait_strategy_.stopped()) return {};
    // Before this call publishes: see TimerWaitStrategy::SelectMode.
    wait_strategy_.SelectMode();
    auto wait_item_weak = std::weak_ptr<WaitItem>(wait_item);
'@))
)

function Read-Text([string]$p) {
  $b = [IO.File]::ReadAllBytes($p)
  $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
  $off = 0; if ($bom) { $off = 3 }
  $t = (New-Object Text.UTF8Encoding($false, $true)).GetString($b, $off, $b.Length - $off)
  return @{ Text = $t; Bom = $bom; Crlf = $t.Contains("`r`n") }
}
function Write-Text([string]$p, [string]$t, [bool]$bom) {
  [IO.File]::WriteAllText($p, $t, (New-Object Text.UTF8Encoding($bom)))
}
function Read-Hashes {
  if (-not (Test-Path -LiteralPath $hashFile)) { throw "no $hashFile - stage first" }
  $h = @{}
  foreach ($l in Get-Content -LiteralPath $hashFile) {
    if ($l -match '^(\S+)\s+(pristine|staged)\s+([0-9A-F]{64})$') { $h[$Matches[2]] = $Matches[3] }
  }
  if (-not $h['pristine'] -or -not $h['staged']) { throw "HASHES.txt lacks the pristine/staged lines" }
  return $h
}
function Count([string]$t, [string]$s) { ([regex]::Matches($t, [regex]::Escape($s))).Count }

$live = Join-Path $root $liveRel
$pr = Join-Path $pristineDir $name
$st = Join-Path $stage $name

if ($Apply -or $Revert -or $Check) {
  if ((@($Apply, $Revert, $Check) | Where-Object { $_ }).Count -gt 1) { throw 'use one of -Apply, -Revert, -Check' }
  $h = Read-Hashes
  if ((Sha $pr) -ne $h['pristine']) { throw "pristine copy changed: $pr" }
  if ((Sha $st) -ne $h['staged']) { throw "staged copy changed: $st" }
  $ls = Sha $live
  $state = if ($ls -eq $h['pristine']) { 'pristine' } elseif ($ls -eq $h['staged']) { 'staged (applied)' } else { 'CHANGED since staging' }
  if ($Check) {
    Write-Host ("live {0}: sha {1} = {2}; LastWriteTime {3:yyyy-MM-dd HH:mm:ss}" -f $liveRel, $ls.Substring(0, 12), $state, (Get-Item -LiteralPath $live).LastWriteTime)
    if ($state -like 'CHANGED*') { exit 1 }
    exit 0
  }
  if ($Apply) {
    if ($ls -eq $h['staged']) { Write-Host "already applied: $liveRel"; exit 0 }
    if ($ls -ne $h['pristine']) { throw "live file changed since staging (sha $ls): $liveRel - re-stage deliberately" }
    Copy-Item -LiteralPath $st -Destination $live -Force
    Stamp-Now $live
    if ((Sha $live) -ne $h['staged']) { throw "copy verification failed: $live" }
    Write-Host ("applied: {0} <- {1} (LastWriteTime {2:HH:mm:ss})" -f $live, $st, (Get-Item -LiteralPath $live).LastWriteTime)
  } else {
    if ($ls -eq $h['pristine']) { Write-Host "already pristine: $liveRel"; exit 0 }
    if ($ls -ne $h['staged']) { throw "live file is neither staged nor pristine (sha $ls): $liveRel" }
    Copy-Item -LiteralPath $pr -Destination $live -Force
    Stamp-Now $live
    if ((Sha $live) -ne $h['pristine']) { throw "copy verification failed: $live" }
    Write-Host ("reverted: {0} <- {1} (LastWriteTime {2:HH:mm:ss})" -f $live, $pr, (Get-Item -LiteralPath $live).LastWriteTime)
  }
  exit 0
}

# ---- stage ----
New-Item -ItemType Directory -Force -Path $pristineDir | Out-Null
$ls = Sha $live
if ((Test-Path -LiteralPath $pr) -and ((Sha $pr) -ne $ls)) {
  throw "live $liveRel differs from the earlier pristine copy $pr; delete build\agent11\timerq\stage\pristine to re-stage deliberately"
}
Copy-Item -LiteralPath $live -Destination $pr -Force
$r = Read-Text $live
$text = $r.Text
$nl = "`n"; if ($r.Crlf) { $nl = "`r`n" }
foreach ($e in $edits) {
  $old = $e[0].Replace("`n", $nl); $new = $e[1].Replace("`n", $nl)
  $n = Count $text $old
  if ($n -ne 1) { throw "${name}: edit target found $n times (need exactly 1):`n$old" }
  $text = $text.Replace($old, $new)
}
Write-Text $st $text $r.Bom
$relP = "build/agent11/timerq/stage/pristine/$name"; $relS = "build/agent11/timerq/stage/$name"
$tmp = Join-Path $stage "$name.diff.tmp"
$oldEap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& git --no-optional-locks diff --no-index --no-color "--output=$tmp" -- $relP $relS 2>&1 | Out-Null
$ErrorActionPreference = $oldEap
if (-not (Test-Path -LiteralPath $tmp)) { throw "git diff produced no output" }
$repoPath = $liveRel.Replace('\', '/')
$d = [IO.File]::ReadAllText($tmp)
$d = $d.Replace("a/$relP", "a/$repoPath").Replace("b/$relS", "b/$repoPath")
Remove-Item -LiteralPath $tmp
$diffPath = Join-Path $stage 'timerq.diff'
[IO.File]::WriteAllText($diffPath, $d, (New-Object Text.UTF8Encoding($false)))
$hashLines = @(
  ("# S3 task #10: timer_queue_precise_wait (default off), staged {0:yyyy-MM-dd HH:mm:ss} by bench\agent11\timerq_stage.ps1" -f (Get-Date)),
  ('{0} pristine {1}' -f $name, (Sha $pr)),
  ('{0} staged {1}' -f $name, (Sha $st)),
  ('timerq.diff sha256 {0}' -f (Sha $diffPath))
)
Set-Content -LiteralPath $hashFile -Value $hashLines -Encoding ascii

# ---- self-checks ----
$fail = 0
function Report([bool]$ok, [string]$what) {
  if ($ok) { Write-Host "PASS  $what" } else { Write-Host "FAIL  $what"; $script:fail++ }
}
$s = Read-Text $st
$p = Read-Text $pr
Report ($s.Bom -eq $r.Bom) ("BOM unchanged ({0})" -f $(if ($r.Bom) { 'BOM' } else { 'no BOM' }))
Report ($s.Crlf -eq $r.Crlf) ("newline style unchanged ({0})" -f $(if ($r.Crlf) { 'CRLF' } else { 'LF' }))
if (-not $r.Crlf) { Report (-not $s.Text.Contains("`r")) 'no CR introduced' }
$dl = $d -split "`n"
$minus = @($dl | Where-Object { $_ -match '^-' -and $_ -notmatch '^---' })
$plus = @($dl | Where-Object { $_ -match '^\+' -and $_ -notmatch '^\+\+\+' })
$hunks = @($dl | Where-Object { $_ -match '^@@' })
# A +10; B -1 +23; C/D/G -1 +1 each; E -1 +2; F +2; H -1 +31; I +2 => -6 / +73
Report (($minus.Count -eq 6) -and ($plus.Count -eq 73)) ("diff has the expected -6/+73 lines (got -{0}/+{1})" -f $minus.Count, $plus.Count)
Report ($hunks.Count -ge 6 -and $hunks.Count -le 9) ("diff has 6-9 hunks (got {0})" -f $hunks.Count)
$long = @($plus | Where-Object { ($_.Length - 1) -gt 100 })
Report ($long.Count -eq 0) ("added lines <= 100 columns (longest {0})" -f (($plus | ForEach-Object { $_.Length - 1 } | Measure-Object -Maximum).Maximum))
Report ((Count $s.Text 'REXCVAR_DEFINE_BOOL(timer_queue_precise_wait, false, "Runtime",') -eq 1) 'cvar timer_queue_precise_wait defined once, default false'
Report ((Count $s.Text '.lifecycle(rex::cvar::Lifecycle::kInitOnly);') -eq 1) 'cvar is kInitOnly'
Report ((Count $s.Text 'blocking_') -eq 0) ('no blocking_ left (pristine had {0})' -f (Count $p.Text 'blocking_'))
Report ((Count $p.Text 'if (!blocking_) {') -eq 4) 'pristine had the 4 "if (!blocking_)" branches'
Report (((Count $s.Text 'if (spinning()) {') -eq 3) -and ((Count $s.Text 'if (mode == Mode::kSpin) {') -eq 1)) 'the 4 branches now test for kSpin (3 spinning(), 1 mode)'
Report ((Count $s.Text 'std::getenv("REX_TIMER_WAIT_BLOCKING") != nullptr') -eq 1) 'REX_TIMER_WAIT_BLOCKING still read once, same test'
Report ((Count $s.Text 'wait_strategy_.SelectMode();') -eq 1) 'QueueTimer calls SelectMode once'
Report ((Count $s.Text 'std::call_once(mode_selected_') -eq 1) 'selection runs under std::call_once'
Report ((Count $s.Text 'WaitPrecise(lock, deadline, ready);') -eq 1) 'precise branch only in the deadline wait'
$po = $p.Text -split "`n"; $so = $s.Text -split "`n"
Report (($so.Count - $po.Count) -eq 67) ("staged file is 67 lines longer ({0} -> {1})" -f $po.Count, $so.Count)
Report ((Sha $live) -eq (Sha $pr)) 'live file untouched (equals pristine)'
Write-Host ("staged {0}: pristine {1} -> staged {2}; diff {3}" -f $name, (Sha $pr).Substring(0, 12), (Sha $st).Substring(0, 12), (Sha $diffPath).Substring(0, 12))
Write-Host "wrote $hashFile and $diffPath"
if ($fail) { Write-Host "RESULT: FAIL ($fail)"; exit 1 }
Write-Host 'RESULT: PASS'
exit 0
