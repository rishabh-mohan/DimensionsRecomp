# M12 session 3: night gates + M6 logdiff kit on the 5 timed windows (read-only on the matrix dirs; outputs here).
$ErrorActionPreference = 'Continue'
$ws = '<workspace>'
Set-Location $ws
$out = Join-Path $ws 'build\agent12\session3\night'
$gateA = 'build\agent3\runs\20261125-022357-s4b-LV-p2fcv-level-long'
$side1 = 'build\agent3\runs\20261125-025013-f10b3-p2fc-level'
$wins = @(
  @{ id='0315'; tag='WC1'; args=@('--one-bin','--side',$side1,'--gate-a',$gateA); ref='s0' },
  @{ id='0359'; tag='W8a'; args=@('--one-bin'); ref='n0' },
  @{ id='0440'; tag='WC2'; args=@('--one-bin','--side',$side1,'--gate-a',$gateA); ref='s0' },
  @{ id='0519'; tag='W10'; args=@(); ref='s0' },
  @{ id='0551'; tag='WC3'; args=@('--one-bin','--side',$side1,'--gate-a',$gateA); ref='s0' }
)
foreach ($w in $wins) {
  $md = "build\agent8\matrix\20261125-$($w.id)"
  $t0 = Get-Date
  & powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\run_gates.ps1 $md @($w.args) --json "$out\gates-$($w.tag).json" *> "$out\gates-$($w.tag).txt"
  "$($w.tag) gates exit $LASTEXITCODE ($([int]((Get-Date)-$t0).TotalSeconds) s)" | Add-Content "$out\run-night.log"
}
foreach ($w in $wins) {
  $md = "build\agent8\matrix\20261125-$($w.id)"
  $t0 = Get-Date
  $p = Start-Process python -ArgumentList @('-B','build\agent6\w6\w6_kit.py',$md,'--ref',$w.ref,'--out',"$out\kit-$($w.tag)") -NoNewWindow -PassThru -RedirectStandardOutput "$out\kit-$($w.tag).txt" -RedirectStandardError "$out\kit-$($w.tag).err.txt"
  $null = $p.Handle
  try { $p.PriorityClass = 'BelowNormal' } catch {}
  $p.WaitForExit()
  "$($w.tag) kit exit $($p.ExitCode) ($([int]((Get-Date)-$t0).TotalSeconds) s)" | Add-Content "$out\run-night.log"
}
"DONE $(Get-Date -Format HH:mm:ss)" | Add-Content "$out\run-night.log"
