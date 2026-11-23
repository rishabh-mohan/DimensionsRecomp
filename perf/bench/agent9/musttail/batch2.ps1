# Batch-2 driver for Agent 10's ask C: chain -> textcheck -> alltu -> heavy, in that order.
# It holds NO CPU slot itself: every compile takes ONE Agent 9 slot for itself (slot1.ps1, same
# rules as cpu2.ps1; waits while bench/agent9/QUIET exists); textcheck (no compile, ~2 min of
# hashing) runs as one step in one slot.
#   powershell -NoProfile -File bench/agent9/musttail/batch2.ps1 [-From textcheck|alltu|heavy] *> bench/agent9/musttail/batch2.log
param([string]$From = 'chain')
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
. (Join-Path $here 'slot1.ps1')
function Write-Stamp([string]$s) { Write-Host ('[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $s) }
$steps = @('chain', 'textcheck', 'alltu', 'heavy')
if ($steps -notcontains $From) { Write-Error "batch2.ps1: -From must be one of $($steps -join ', ')"; exit 2 }
foreach ($step in $steps[([array]::IndexOf($steps, $From))..($steps.Count - 1)]) {
  Write-Stamp "$step start"
  $ps1 = Join-Path $here "$step.ps1"
  $log = Join-Path $here "$step.log"
  if ($step -eq 'textcheck') { Invoke-InSlot { & powershell -NoProfile -ExecutionPolicy Bypass -File $ps1 *> $log } }
  else { & powershell -NoProfile -ExecutionPolicy Bypass -File $ps1 *> $log }
  Write-Stamp "$step exit=$LASTEXITCODE"
}
