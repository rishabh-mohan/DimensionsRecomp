<#
.SYNOPSIS
  Agent 6, S3 native fix (a): fix-a.patch (hunks 1+2) plus fix-a-commit.patch (hunk 3), applied to the live
  GAME repo (DimensionsRecomp\) as hash-guarded byte copies of the verified staged files. No git commands.

.DESCRIPTION
  -Check  (default) prints the staged, undo and live hashes and each live file's state
          (PRISTINE / APPLIED / OTHER). Writes nothing. Exit 0 if the staged and undo copies are good and
          every live file is PRISTINE or APPLIED, else 1.
  -Apply  Every guard passes before anything is written: staged copy at the after-hash, undo copy (orig\)
          at the before-hash, each live file at the before-hash. A live file already at the after-hash is
          left alone; any other hash stops the run with nothing written. Writes with WriteAllBytes, so the
          mtime becomes "now" and ninja recompiles the TU. Then it re-hashes. Exit 1 on any mismatch.
  -Revert The same guards in reverse: copies orig\ back over live files at the after-hash, then re-hashes.

  Targets (Agent 1, session 3, 02:01):
    rexlego\src\settings_registry.cpp     A3733700 -> 4EC71328  (fix-a + commit hunk, from new-commit\)
    rexlego\src\settings_preferences.cpp  C78112AA -> 9CBE6DBF  (fix-a, from new\; hunk 3 does not touch it)
  Written for Windows PowerShell 5.1:  powershell -NoProfile -File build\agent6\fix-a\apply_fix_a.ps1 -Check
#>
param([switch]$Check, [switch]$Apply, [switch]$Revert)
$ErrorActionPreference = 'Stop'
if (([int][bool]$Check + [int][bool]$Apply + [int][bool]$Revert) -gt 1) { throw 'use only one of -Check, -Apply, -Revert' }

$root  = '<workspace>'
$stage = Join-Path $root 'build\agent6\fix-a'
$map = @(
  [pscustomobject]@{ rel = 'rexlego\src\settings_registry.cpp'; src = 'new-commit'
    before = 'A37337001EBDC277B2B94D783939A47096423F0AE8962C8B879A6A60B4F8BA4B'
    after  = '4EC71328043FA6BA8C198D5AAFBFB7D0265CD1939ECE13D1CE11B6A7A48DB77D' }
  [pscustomobject]@{ rel = 'rexlego\src\settings_preferences.cpp'; src = 'new'
    before = 'C78112AA6E50F79D8E6154A37E47CC129C43EAD2E39EC066927374EFBF34B5F0'
    after  = '9CBE6DBF9CEDA62D61469235A828B84017340D356C166335BF53E9AB18565730' }
)
foreach ($m in $map) {
  $m | Add-Member -NotePropertyName live -NotePropertyValue (Join-Path $root ('DimensionsRecomp\' + $m.rel))
  $m | Add-Member -NotePropertyName new  -NotePropertyValue (Join-Path $stage ($m.src + '\' + $m.rel))
  $m | Add-Member -NotePropertyName orig -NotePropertyValue (Join-Path $stage ('orig\' + $m.rel))
}

function Get-Sha([string]$p) {
  if (Test-Path -LiteralPath $p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash } else { 'MISSING' }
}
function Get-State($m, [string]$h) {
  if ($h -eq $m.before) { 'PRISTINE' } elseif ($h -eq $m.after) { 'APPLIED' } else { 'OTHER' }
}
function Test-Staged {
  $bad = @()
  foreach ($m in $map) {
    $hn = Get-Sha $m.new; $ho = Get-Sha $m.orig
    '  staged {0,-10} {1,-37} {2}' -f $m.src, $m.rel, $(if ($hn -eq $m.after) { 'OK  ' + $hn } else { 'BAD ' + $hn })
    '  undo   {0,-10} {1,-37} {2}' -f 'orig', $m.rel, $(if ($ho -eq $m.before) { 'OK  ' + $ho } else { 'BAD ' + $ho })
    if ($hn -ne $m.after) { $bad += ('staged ' + $m.src + '\' + $m.rel) }
    if ($ho -ne $m.before) { $bad += ('orig\' + $m.rel) }
  }
  $script:stagedBad = $bad
}
function Show-Live([string]$tag) {
  $script:states = @{}
  foreach ($m in $map) {
    $h = Get-Sha $m.live; $s = Get-State $m $h; $script:states[$m.rel] = $s
    $f = Get-Item -LiteralPath $m.live
    '  {0,-6} DimensionsRecomp\{1,-37} {2,-8} {3,6} B  {4:MM-dd HH:mm:ss}  {5}' -f $tag, $m.rel, $s, $f.Length, $f.LastWriteTime, $h
  }
}

'== Agent 6 fix-a + fix-a-commit  {0:yyyy-MM-dd HH:mm:ss}  mode={1}' -f (Get-Date), $(if ($Apply) { 'Apply' } elseif ($Revert) { 'Revert' } else { 'Check' })
Test-Staged
Show-Live 'live'
if (-not $Apply -and -not $Revert) {
  if ($stagedBad.Count -or (@($states.Values) -contains 'OTHER')) { 'CHECK: FAIL'; exit 1 }
  'CHECK: OK'; exit 0
}

# Guards: all of them pass before the first write.
if ($stagedBad.Count) { throw ('guard: ' + ($stagedBad -join ', ') + ' not at the expected hash; nothing written') }
foreach ($m in $map) {
  if ($states[$m.rel] -eq 'OTHER') { throw ('guard: live ' + $m.rel + ' is at neither the before- nor the after-hash; nothing written') }
}
if ($Apply) { $from = 'PRISTINE'; $to = 'APPLIED'; $srcProp = 'new' } else { $from = 'APPLIED'; $to = 'PRISTINE'; $srcProp = 'orig' }
$todo = @($map | Where-Object { $states[$_.rel] -eq $from })
foreach ($m in $todo) {
  [IO.File]::WriteAllBytes($m.live, [IO.File]::ReadAllBytes($m.$srcProp))
  '  wrote  DimensionsRecomp\{0} from {1}\' -f $m.rel, $(if ($Apply) { $m.src } else { 'orig' })
}
if (-not $todo.Count) { '  nothing to do: every live file is already ' + $to }
Show-Live 'after'
$bad = @($map | Where-Object { $states[$_.rel] -ne $to })
if ($bad.Count) { 'RESULT: MISMATCH'; exit 1 }
'RESULT: OK, all ' + $to
exit 0
