# safeorder_stage.ps1 - S3 proposal (Agent 1, 23:41): make pause_safe_order (task #17,
# Agent 12) default ON in DimensionsRecomp/rexglue-sdk/src/ui/rex_app.cpp. Text only:
# staging writes nothing outside build\agent11\safeorder. guest_suspend_guard stays OFF.
# Rationale: perf-notes/agent11-kernel.md, section "S3 proposal: pause_safe_order default ON".
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1          # stage + self-check
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1 -Check   # live still pristine?
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1 -Apply   # staged -> live
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1 -Revert  # pristine -> live
#
# -Apply / -Revert are for whoever lands it in S3, and only after Agent 10 rates it SAFE
# and Agent 1 says go (rex_app.cpp is Agent 12's #17 file). Same rules as
# exitfix_stage.ps1: Apply refuses unless the live file still equals the pristine hash
# and the staged copy equals HASHES.txt; Revert refuses unless live equals staged. Both
# stamp the live file's LastWriteTime with the copy time (Copy-Item keeps the source's).
# Stage: each edit target must occur exactly once; line endings and BOM are preserved;
# the diff comes from read-only "git diff --no-index" with headers rewritten to the repo
# path. Self-checks: newline style and BOM unchanged, only the expected lines differ,
# changed lines <= 100 columns, the new default present once, "default off" gone.
# Pure ASCII on purpose (PowerShell 5.1 reads BOM-less scripts as ANSI).
param([switch]$Apply, [switch]$Revert, [switch]$Check)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stage = Join-Path $root 'build\agent11\safeorder'
$pristineDir = Join-Path $stage 'pristine'
$hashFile = Join-Path $stage 'HASHES.txt'
$name = 'rex_app.cpp'
$liveRel = 'DimensionsRecomp\rexglue-sdk\src\ui\rex_app.cpp'
Set-Location $root

function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function NL([string]$s) { ($s -replace "`r`n", "`n").TrimEnd("`n") + "`n" }
# Copy-Item keeps the source's LastWriteTime (Agent 12, 00:03), so -Apply / -Revert stamp
# the live file with the copy time; otherwise ninja could keep an object built from the old
# text after the source copy was written. Content and hash are unchanged by this.
function Stamp-Now([string]$p) { (Get-Item -LiteralPath $p).LastWriteTime = Get-Date }

# ---- the edits (old text -> new text), LF here; converted to the file's newline ----
$edits = @(
  @((NL @'
REXCVAR_DEFINE_BOOL(pause_safe_order, false, "UI/Window",
                    "Pause and unpause the guest without allocating, logging, taking the object "
                    "table lock or waiting on the audio workers while guest threads are stopped: "
                    "the pause keeps the threads it suspended and the unpause resumes them first. "
                    "Off: the original order");
'@), (NL @'
REXCVAR_DEFINE_BOOL(pause_safe_order, true, "UI/Window",
                    "Pause and unpause the guest without allocating, logging, taking the object "
                    "table lock or waiting on the audio workers while guest threads are stopped: "
                    "the pause keeps the threads it suspended and the unpause resumes them first. "
                    "Off: the original order, which can hang when the guest pauses");
'@)),
  @((NL @'
  // pause_safe_order (default off; task #17 in perf-notes/agent12-io-memory.md). The pause
  // picks the path and its unpause follows it, so turning the cvar on or off while the guest
  // is paused cannot strand a thread.
'@), (NL @'
  // pause_safe_order (default on; task #17 in perf-notes/agent12-io-memory.md). The original
  // order below can deadlock: in test G (#23, perf-notes/agent11-kernel.md) the audio pause
  // waited on a worker stuck in a guest callback that needed the just-suspended guest threads.
  // The pause picks the path and its unpause follows it, so turning the cvar on or off while
  // the guest is paused cannot strand a thread.
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
  throw "live $liveRel differs from the earlier pristine copy $pr; delete build\agent11\safeorder\pristine to re-stage deliberately"
}
Copy-Item -LiteralPath $live -Destination $pr -Force
$r = Read-Text $live
$text = $r.Text
$nl = "`n"; if ($r.Crlf) { $nl = "`r`n" }
$expectMinus = 0; $expectPlus = 0
foreach ($e in $edits) {
  $old = $e[0].Replace("`n", $nl); $new = $e[1].Replace("`n", $nl)
  $n = ([regex]::Matches($text, [regex]::Escape($old))).Count
  if ($n -ne 1) { throw "${name}: edit target found $n times (need exactly 1):`n$old" }
  $text = $text.Replace($old, $new)
}
Write-Text $st $text $r.Bom
$relP = "build/agent11/safeorder/pristine/$name"; $relS = "build/agent11/safeorder/$name"
$tmp = Join-Path $stage "$name.diff.tmp"
$oldEap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& git --no-optional-locks diff --no-index --no-color "--output=$tmp" -- $relP $relS 2>&1 | Out-Null
$ErrorActionPreference = $oldEap
if (-not (Test-Path -LiteralPath $tmp)) { throw "git diff produced no output" }
$repoPath = $liveRel.Replace('\', '/')
$d = [IO.File]::ReadAllText($tmp)
$d = $d.Replace("a/$relP", "a/$repoPath").Replace("b/$relS", "b/$repoPath")
Remove-Item -LiteralPath $tmp
$diffPath = Join-Path $stage 'safeorder.diff'
[IO.File]::WriteAllText($diffPath, $d, (New-Object Text.UTF8Encoding($false)))
$hashLines = @(
  ("# S3 proposal: pause_safe_order default ON, staged {0:yyyy-MM-dd HH:mm:ss} by bench\agent11\safeorder_stage.ps1" -f (Get-Date)),
  ('{0} pristine {1}' -f $name, (Sha $pr)),
  ('{0} staged {1}' -f $name, (Sha $st)),
  ('safeorder.diff sha256 {0}' -f (Sha $diffPath))
)
Set-Content -LiteralPath $hashFile -Value $hashLines -Encoding ascii

# ---- self-checks ----
$fail = 0
function Report([bool]$ok, [string]$what) {
  if ($ok) { Write-Host "PASS  $what" } else { Write-Host "FAIL  $what"; $script:fail++ }
}
$s = Read-Text $st
Report ($s.Bom -eq $r.Bom) ("BOM unchanged ({0})" -f $(if ($r.Bom) { 'BOM' } else { 'no BOM' }))
Report ($s.Crlf -eq $r.Crlf) ("newline style unchanged ({0})" -f $(if ($r.Crlf) { 'CRLF' } else { 'LF' }))
if (-not $r.Crlf) { Report (-not $s.Text.Contains("`r")) 'no CR introduced' }
$dl = $d -split "`n"
$minus = @($dl | Where-Object { $_ -match '^-' -and $_ -notmatch '^---' })
$plus = @($dl | Where-Object { $_ -match '^\+' -and $_ -notmatch '^\+\+\+' })
# hunk 1: 2 changed lines (default, description tail); hunk 2: the 3-line comment becomes 5
Report (($minus.Count -eq 5) -and ($plus.Count -eq 7)) ("diff has the expected -5/+7 lines (got -{0}/+{1})" -f $minus.Count, $plus.Count)
$hunks = @($dl | Where-Object { $_ -match '^@@' })
Report ($hunks.Count -eq 2) ("diff has 2 hunks (got {0})" -f $hunks.Count)
$long = @($plus | Where-Object { ($_.Length - 1) -gt 100 })
Report ($long.Count -eq 0) ("added lines <= 100 columns (longest {0})" -f (($plus | ForEach-Object { $_.Length - 1 } | Measure-Object -Maximum).Maximum))
Report (([regex]::Matches($s.Text, [regex]::Escape('REXCVAR_DEFINE_BOOL(pause_safe_order, true, "UI/Window",'))).Count -eq 1) 'new default "pause_safe_order, true" present exactly once'
Report (-not $s.Text.Contains('pause_safe_order, false')) 'old default gone'
Report (-not $s.Text.Contains('(default off;')) 'comment no longer says "default off"'
$po = (Read-Text $pr).Text -split "`n"; $so = $s.Text -split "`n"
Report (($so.Count - $po.Count) -eq 2) ("staged file is 2 lines longer ({0} -> {1})" -f $po.Count, $so.Count)
Report ((Sha $live) -eq (Sha $pr)) 'live file untouched (equals pristine)'
Write-Host ("staged {0}: pristine {1} -> staged {2}; diff {3}" -f $name, (Sha $pr).Substring(0, 12), (Sha $st).Substring(0, 12), (Sha $diffPath).Substring(0, 12))
Write-Host "wrote $hashFile and $diffPath"
if ($fail) { Write-Host "RESULT: FAIL ($fail)"; exit 1 }
Write-Host 'RESULT: PASS'
exit 0
