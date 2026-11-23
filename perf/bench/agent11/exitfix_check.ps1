# exitfix_check.ps1 - task #27 source lint for the exit-path fix.
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_check.ps1            # staged copies
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_check.ps1 -Live      # live tree
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_check.ps1 -Pristine  # must FAIL
# Per file: (1) no CRT exit( call outside // comments; (2) #include <cstdlib>;
# (3) the export's last two statements are rex::FlushLogging(); std::_Exit(<code>);
# (4) the export still has all of its original REXKRNL_ERROR lines; (5) no
# "hard-exiting" text (bench\agent8 timing scripts treat that as the window-
# close cue); (6) the file hash equals HASHES.txt (staged hash for staged and
# live, pristine hash for -Pristine). Exit 0 = all checks pass, 1 = a check
# failed. -Pristine is the negative control: it is expected to exit 1.
param([switch]$Live, [switch]$Pristine)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$stage = Join-Path $root 'build\agent11\exitfix'
$specs = @(
  @{ Name = 'xboxkrnl_hal.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\kernel\xboxkrnl\xboxkrnl_hal.cpp'
     Func = 'void HalReturnToFirmware_entry('; Code = 0; Errors = 1 },
  @{ Name = 'xam_ui.cpp'; Live = 'DimensionsRecomp\rexglue-sdk\src\kernel\xam\xam_ui.cpp'
     Func = 'void XamShowDirtyDiscErrorUI_entry('; Code = 1; Errors = 7 }
)
$hashes = @{}
$hf = Join-Path $stage 'HASHES.txt'
if (Test-Path -LiteralPath $hf) {
  foreach ($l in Get-Content -LiteralPath $hf) {
    if ($l -match '^(\S+)\s+(pristine|staged)\s+([0-9A-F]{64})$') { $hashes["$($Matches[1])|$($Matches[2])"] = $Matches[3] }
  }
}
$what = 'staged'; if ($Live) { $what = 'live' }; if ($Pristine) { $what = 'pristine' }
$fail = 0
foreach ($s in $specs) {
  $path = Join-Path $stage $s.Name
  if ($Live) { $path = Join-Path $root $s.Live }
  if ($Pristine) { $path = Join-Path $stage "pristine\$($s.Name)" }
  $lines = @(Get-Content -LiteralPath $path)
  $code = @($lines | ForEach-Object { ($_ -replace '//.*$', '').TrimEnd() })
  $res = New-Object System.Collections.Generic.List[string]
  function Check([string]$name, [bool]$ok, [string]$detail) {
    if (-not $ok) { $script:fail++ }
    $res.Add(('  {0} {1}{2}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $(if ($detail) { " ($detail)" } else { '' })))
  }
  $exitHits = @(for ($i = 0; $i -lt $code.Count; $i++) { if ($code[$i] -cmatch '(?<![\w])exit\s*\(') { $i + 1 } })
  Check 'no CRT exit( call' ($exitHits.Count -eq 0) $(if ($exitHits.Count) { 'line ' + ($exitHits -join ',') } else { '' })
  Check '#include <cstdlib>' (@($lines | Where-Object { $_.Trim() -ceq '#include <cstdlib>' }).Count -ge 1) ''
  $start = -1
  for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].StartsWith($s.Func)) { $start = $i; break } }
  $end = -1
  if ($start -ge 0) { for ($i = $start + 1; $i -lt $lines.Count; $i++) { if ($lines[$i] -ceq '}') { $end = $i; break } } }
  if ($start -lt 0 -or $end -lt 0) {
    $fname = $s.Func.TrimEnd([char]40)
    Check "find $fname" $false 'function not found'
  } else {
    $stmts = @(for ($i = $start + 1; $i -lt $end; $i++) { $t = $code[$i].Trim(); if ($t) { $t } })
    $tail = @($stmts | Select-Object -Last 2) -join ' '
    $want = "rex::FlushLogging(); std::_Exit($($s.Code));"
    Check "ends with $want" ($tail -ceq $want) "last two: $tail"
    $nerr = @($stmts | Where-Object { $_ -cmatch '^REXKRNL_ERROR\(' }).Count
    Check "REXKRNL_ERROR lines kept ($($s.Errors))" ($nerr -eq $s.Errors) "found $nerr, lines $($start + 1)-$($end + 1)"
  }
  Check 'no "hard-exiting" text' (@($lines | Where-Object { $_ -match 'hard-exiting' }).Count -eq 0) ''
  $wantHash = $hashes["$($s.Name)|$(if ($Pristine) { 'pristine' } else { 'staged' })"]
  $have = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  Check 'hash matches HASHES.txt' ($wantHash -and $have -eq $wantHash) ('sha ' + $have.Substring(0, 12))
  Write-Host "$what $($s.Name): $path"
  $res | ForEach-Object { Write-Host $_ }
}
if ($fail) { Write-Host "exitfix_check ($what): $fail check(s) FAILED"; exit 1 }
Write-Host "exitfix_check ($what): all checks passed"
exit 0
