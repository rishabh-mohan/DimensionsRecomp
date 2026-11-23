# stage_stamp_test.ps1 - checks that exitfix_stage.ps1 and safeorder_stage.ps1 stamp the live
# file's LastWriteTime with the copy time on -Apply / -Revert (Agent 12's catch, 00:03:
# Copy-Item keeps the source's LastWriteTime, so ninja could keep an object built from the old
# text). Runs byte-for-byte copies of both scripts in a sandbox under
# build\agent11\stamptest\<time>\ that mirrors the repo layout, so the real tree is never
# touched. Also shows the hazard itself: a bare Copy-Item keeps the old stamp.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\stage_stamp_test.ps1
# No game, no compile, one thread. Exit 0 = all checks pass.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$sb = Join-Path $root ("build\agent11\stamptest\{0:yyyyMMdd-HHmmss}" -f (Get-Date))
New-Item -ItemType Directory -Force -Path $sb | Out-Null
$lines = New-Object System.Collections.Generic.List[string]
$fail = 0
function Report([bool]$ok, [string]$what) {
  $s = $(if ($ok) { "PASS  $what" } else { "FAIL  $what" })
  $script:lines.Add($s); Write-Host $s
  if (-not $ok) { $script:fail++ }
}
function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Put([string]$src, [string]$rel) {
  $dst = Join-Path $sb $rel
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item -LiteralPath (Join-Path $root $src) -Destination $dst -Force
}
function Run([string]$script, [string]$mode) {
  $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  $o = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $sb "bench\agent11\$script") $mode 2>&1
  $code = $LASTEXITCODE
  $ErrorActionPreference = $old
  foreach ($l in @($o)) { $script:lines.Add("    | $l") }
  return $code
}
function Hashes([string]$file) {
  $h = @{}
  foreach ($l in Get-Content -LiteralPath $file) {
    if ($l -match '^(\S+)\s+(pristine|staged)\s+([0-9A-F]{64})$') { $h["$($Matches[1])|$($Matches[2])"] = $Matches[3] }
  }
  return $h
}

$lines.Add("# stage_stamp_test  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  sandbox $sb")

# 0. the hazard: a bare Copy-Item keeps the source's LastWriteTime
$a = Join-Path $sb 'hazard-src.txt'; $b = Join-Path $sb 'hazard-dst.txt'
Set-Content -LiteralPath $a -Value 'x' -Encoding ascii
$old = [datetime]'2026-11-21 21:01:00'
(Get-Item -LiteralPath $a).LastWriteTime = $old
Copy-Item -LiteralPath $a -Destination $b -Force
$bt = (Get-Item -LiteralPath $b).LastWriteTime
Report ($bt -eq $old) ("hazard: a bare Copy-Item keeps the source stamp (copy shows {0:yyyy-MM-dd HH:mm:ss})" -f $bt)

$sets = @(
  @{ Script = 'safeorder_stage.ps1'; Stage = 'build\agent11\safeorder'
     Files = @(@{ Name = 'rex_app.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\ui\rex_app.cpp' }) },
  @{ Script = 'exitfix_stage.ps1'; Stage = 'build\agent11\exitfix'
     Files = @(@{ Name = 'xboxkrnl_hal.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\kernel\xboxkrnl\xboxkrnl_hal.cpp' },
               @{ Name = 'xam_ui.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\kernel\xam\xam_ui.cpp' }) }
)
foreach ($set in $sets) {
  Put "bench\agent11\$($set.Script)" "bench\agent11\$($set.Script)"
  Put "$($set.Stage)\HASHES.txt" "$($set.Stage)\HASHES.txt"
  $h = Hashes (Join-Path $root "$($set.Stage)\HASHES.txt")
  foreach ($f in $set.Files) {
    Put "$($set.Stage)\$($f.Name)" "$($set.Stage)\$($f.Name)"
    Put "$($set.Stage)\pristine\$($f.Name)" "$($set.Stage)\pristine\$($f.Name)"
    # the sandbox live file starts pristine, with the pristine copy's (old) stamp
    Put "$($set.Stage)\pristine\$($f.Name)" $f.Live
  }
  foreach ($mode in '-Apply', '-Revert') {
    $kind = $(if ($mode -eq '-Apply') { 'staged' } else { 'pristine' })
    $t0 = (Get-Date).AddSeconds(-2)
    $code = Run $set.Script $mode
    Report ($code -eq 0) ("{0} {1}: exit {2}" -f $set.Script, $mode, $code)
    foreach ($f in $set.Files) {
      $p = Join-Path $sb $f.Live
      Report ((Sha $p) -eq $h["$($f.Name)|$kind"]) ("{0} {1}: {2} hash = {3}" -f $set.Script, $mode, $f.Name, $kind)
      $src = Join-Path $sb $(if ($kind -eq 'staged') { "$($set.Stage)\$($f.Name)" } else { "$($set.Stage)\pristine\$($f.Name)" })
      $lw = (Get-Item -LiteralPath $p).LastWriteTime
      Report ($lw -ge $t0) ("{0} {1}: {2} stamped with the copy time ({3:HH:mm:ss}; its source copy says {4:yyyy-MM-dd HH:mm:ss})" -f $set.Script, $mode, $f.Name, $lw, (Get-Item -LiteralPath $src).LastWriteTime)
    }
  }
}
$lines.Add($(if ($fail) { "RESULT: FAIL ($fail)" } else { 'RESULT: PASS' }))
Set-Content -LiteralPath (Join-Path $sb 'report.txt') -Value $lines -Encoding ascii
Write-Host $lines[$lines.Count - 1]
Write-Host "report: $(Join-Path $sb 'report.txt')"
if ($fail) { exit 1 }
exit 0
