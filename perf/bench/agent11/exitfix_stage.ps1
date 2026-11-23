# exitfix_stage.ps1 - task #27 (SDK exit-path fix): stage, apply or revert the
# two-file change that replaces CRT exit() with rex::FlushLogging() +
# std::_Exit(code) in HalReturnToFirmware (code 0) and XamShowDirtyDiscErrorUI
# (code 1). Rationale: perf-notes/agent11-kernel.md "### #27 exit-path fix".
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_stage.ps1          # stage
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_stage.ps1 -Apply   # staged -> live
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_stage.ps1 -Revert  # pristine -> live
#
# Stage : copies each live file to build\agent11\exitfix\pristine\ (refuses if
#         an earlier pristine copy differs from the live file), applies the exact
#         text edits below (each target must occur exactly once; line endings and
#         BOM are preserved), and writes build\agent11\exitfix\<file>, HASHES.txt
#         and exitfix.diff (read-only "git diff --no-index", headers rewritten to
#         the repo paths so the diff also applies with git apply from the root).
# Apply : refuses unless BOTH live files still equal their pristine hash and both
#         staged copies equal HASHES.txt; then copies staged -> live, stamps each
#         live file's LastWriteTime with the copy time (Copy-Item keeps the
#         source's), and verifies the hash.
# Revert: refuses unless both live files equal the staged hash; restores pristine
#         (same stamping).
# Writes nothing outside build\agent11\exitfix except the two live files on
# -Apply / -Revert. Pure ASCII on purpose (PowerShell 5.1 reads BOM-less
# scripts as ANSI).
param([switch]$Apply, [switch]$Revert)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stage = Join-Path $root 'build\agent11\exitfix'
$pristineDir = Join-Path $stage 'pristine'
$hashFile = Join-Path $stage 'HASHES.txt'
Set-Location $root

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function NL([string]$s) { ($s -replace "`r`n", "`n").TrimEnd("`n") + "`n" }

# ---- the edits (old text -> new text), LF here; converted to the file's newline ----
$files = @(
  @{
    Name  = 'xboxkrnl_hal.cpp'
    Live  = 'DimensionsRecomp\rexglue-sdk\src\kernel\xboxkrnl\xboxkrnl_hal.cpp'
    Edits = @(
      @((NL @'
#include <rex/kernel/xboxkrnl/private.h>
#include <rex/logging.h>
'@), (NL @'
#include <cstdlib>

#include <rex/kernel/xboxkrnl/private.h>
#include <rex/logging.h>
'@)),
      @((NL @'
  // TODO(benvank): diediedie much more gracefully
  // Not sure how to blast back up the stack in LLVM without exceptions, though.
  REXKRNL_ERROR("Game requested shutdown via HalReturnToFirmware");
  exit(0);
}
'@), (NL @'
  // There is no dashboard to return to, so hard-exit the way ReXApp::OnClosing
  // does: flush the logs, then std::_Exit. CRT exit() would run the EXE's
  // atexit handlers and static destructors on this guest thread while the
  // other threads keep running. OnShutdown would tear down the runtime this
  // thread runs on, and KernelState::TerminateTitle() never returns to a guest
  // caller, so neither is used.
  REXKRNL_ERROR("Game requested shutdown via HalReturnToFirmware");
  rex::FlushLogging();
  std::_Exit(0);
}
'@))
    )
  },
  @{
    Name  = 'xam_ui.cpp'
    Live  = 'DimensionsRecomp\rexglue-sdk\src\kernel\xam\xam_ui.cpp'
    Edits = @(
      @((NL @'
#include <rex/logging.h>
#include <rex/runtime.h>
'@), (NL @'
#include <cstdlib>

#include <rex/logging.h>
#include <rex/runtime.h>
'@)),
      @((NL @'
  // This is death, and should never return.
  // TODO(benvanik): cleaner exit.
  exit(1);
}
'@), (NL @'
  // This is death, and should never return. Any dialog above was shown
  // synchronously (overlapped 0) and has been closed by now. Hard-exit the way
  // ReXApp::OnClosing does (flush the logs, then std::_Exit) instead of CRT
  // exit(), which would run the EXE's atexit handlers and static destructors
  // on this guest thread while the other threads keep running.
  rex::FlushLogging();
  std::_Exit(1);
}
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

if ($Apply -or $Revert) {
  if ($Apply -and $Revert) { throw 'use -Apply or -Revert, not both' }
  $h = Read-Hashes
  $todo = @()
  foreach ($f in $files) {
    $live = Join-Path $root $f.Live
    $pr = Join-Path $pristineDir $f.Name
    $st = Join-Path $stage $f.Name
    $hp = $h["$($f.Name)|pristine"]; $hs = $h["$($f.Name)|staged"]
    if (-not $hp -or -not $hs) { throw "HASHES.txt has no entry for $($f.Name)" }
    if ((Sha $pr) -ne $hp) { throw "pristine copy changed: $pr" }
    if ((Sha $st) -ne $hs) { throw "staged copy changed: $st" }
    $ls = Sha $live
    if ($Apply) {
      if ($ls -eq $hs) { Write-Host "already applied: $($f.Live)"; continue }
      if ($ls -ne $hp) { throw "live file changed since staging (sha $ls): $($f.Live) - re-stage deliberately" }
      $todo += , @($st, $live, $hs)
    } else {
      if ($ls -eq $hp) { Write-Host "already pristine: $($f.Live)"; continue }
      if ($ls -ne $hs) { throw "live file is neither staged nor pristine (sha $ls): $($f.Live)" }
      $todo += , @($pr, $live, $hp)
    }
  }
  foreach ($t in $todo) {
    Copy-Item -LiteralPath $t[0] -Destination $t[1] -Force
    # Copy-Item keeps the source's LastWriteTime (Agent 12, 00:03). Stamp the live file with
    # the copy time, or ninja could keep an object built from the old text after the source
    # copy was written. Content and hash are unchanged by this.
    (Get-Item -LiteralPath $t[1]).LastWriteTime = Get-Date
    if ((Sha $t[1]) -ne $t[2]) { throw "copy verification failed: $($t[1])" }
    Write-Host ("{0}: {1} <- {2} (LastWriteTime {3:HH:mm:ss})" -f $(if ($Apply) { 'applied' } else { 'reverted' }), $t[1], $t[0], (Get-Item -LiteralPath $t[1]).LastWriteTime)
  }
  exit 0
}

# ---- stage ----
New-Item -ItemType Directory -Force -Path $pristineDir | Out-Null
$hashLines = @("# task #27 exit-path fix, staged {0:yyyy-MM-dd HH:mm:ss} by bench\agent11\exitfix_stage.ps1" -f (Get-Date))
$diff = New-Object Text.StringBuilder
foreach ($f in $files) {
  $live = Join-Path $root $f.Live
  $pr = Join-Path $pristineDir $f.Name
  $st = Join-Path $stage $f.Name
  $ls = Sha $live
  if ((Test-Path -LiteralPath $pr) -and ((Sha $pr) -ne $ls)) {
    throw "live $($f.Live) differs from the earlier pristine copy $pr; delete build\agent11\exitfix\pristine to re-stage deliberately"
  }
  Copy-Item -LiteralPath $live -Destination $pr -Force
  $r = Read-Text $live
  $text = $r.Text
  $nl = "`n"; if ($r.Crlf) { $nl = "`r`n" }
  foreach ($e in $f.Edits) {
    $old = $e[0].Replace("`n", $nl); $new = $e[1].Replace("`n", $nl)
    $n = ([regex]::Matches($text, [regex]::Escape($old))).Count
    if ($n -ne 1) { throw "$($f.Name): edit target found $n times (need exactly 1):`n$old" }
    $text = $text.Replace($old, $new)
  }
  Write-Text $st $text $r.Bom
  $hashLines += ('{0} pristine {1}' -f $f.Name, (Sha $pr))
  $hashLines += ('{0} staged {1}' -f $f.Name, (Sha $st))
  # unified diff via read-only git; rewrite the headers to the repo path
  $relP = "build/agent11/exitfix/pristine/$($f.Name)"; $relS = "build/agent11/exitfix/$($f.Name)"
  $tmp = Join-Path $stage "$($f.Name).diff.tmp"
  $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  & git --no-optional-locks diff --no-index --no-color "--output=$tmp" -- $relP $relS 2>&1 | Out-Null
  $ErrorActionPreference = $old
  if (-not (Test-Path -LiteralPath $tmp)) { throw "git diff produced no output for $($f.Name)" }
  $repoPath = $f.Live.Replace('\', '/')
  $d = [IO.File]::ReadAllText($tmp)
  $d = $d.Replace("a/$relP", "a/$repoPath").Replace("b/$relS", "b/$repoPath")
  [void]$diff.Append($d)
  Remove-Item -LiteralPath $tmp
  Write-Host ("staged {0}: pristine {1} -> staged {2}" -f $f.Name, (Sha $pr).Substring(0, 12), (Sha $st).Substring(0, 12))
}
Set-Content -LiteralPath $hashFile -Value $hashLines -Encoding ascii
[IO.File]::WriteAllText((Join-Path $stage 'exitfix.diff'), $diff.ToString(), (New-Object Text.UTF8Encoding($false)))
Write-Host "wrote $hashFile and $(Join-Path $stage 'exitfix.diff')"
