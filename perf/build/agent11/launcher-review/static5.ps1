# static5.ps1 - read-only: would the launcher's arm rules (run-night.ps1 Test-Matrix) accept the native / W8-W9 style
# matrices? Prints per arm: bin, env keys, and each launcher rule that fails. Agent 11, task #10.
$ErrorActionPreference = 'Continue'
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch {}
Set-Location '<workspace>'
$OUTL = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $OUTL.Add($s) }
function Get-P($O, [string]$N) { if ($null -ne $O -and $O -is [System.Management.Automation.PSCustomObject]) { $pp = $O.PSObject.Properties[$N]; if ($null -ne $pp) { return $pp.Value } }; return $null }
$allowed = @('REX_TIMER_WAIT_BLOCKING', 'LEGO_GPU_WAIT_STATS')
W ('static5 ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$files = @(Get-ChildItem bench/agent8/run -File -Filter 'matrix*.json') + @(Get-ChildItem build/agent4 -Recurse -File -Filter 'matrix*.json' -ErrorAction SilentlyContinue) + @(Get-ChildItem build/agent5/w6-draft -Recurse -File -Filter 'matrix*.json' -ErrorAction SilentlyContinue)
foreach ($fi in $files) {
  $rel = $fi.FullName.Replace((Get-Location).Path + '\', '')
  try { $mx = [IO.File]::ReadAllText($fi.FullName) | ConvertFrom-Json } catch { W "PARSE-FAIL $rel"; continue }
  $arms = @(Get-P $mx 'arms')
  $bad = 0; $lines = New-Object System.Collections.Generic.List[string]
  foreach ($a in $arms) {
    $id = [string](Get-P $a 'id'); $bin = [string](Get-P $a 'bin'); $bn = $bin -replace '\\', '/'
    $why = @()
    if ($bn -notmatch '^build/agent2/([A-Za-z0-9][A-Za-z0-9_.-]*)-bin/?$' -or $bn -match '\.\.') { $why += 'bin-not-agent2' }
    $ev = Get-P $a 'env'; $keys = @()
    if ($null -ne $ev) { $keys = @($ev.PSObject.Properties | ForEach-Object Name); foreach ($k in $keys) { if ($allowed -cnotcontains $k) { $why += "env:$k" } } }
    if ([string](Get-P $a 'menu')) { $why += 'menu' }
    if ((Get-P $a 'profile') -eq $true) { $why += 'profile' }
    if (@(Get-P $a 'triggers' | Where-Object { $_ }).Count) { $why += 'triggers' }
    $tm = Get-P $a 'toml'; if ($null -ne $tm -and @($tm.PSObject.Properties).Count) { $why += 'toml' }
    if ([string](Get-P $a 'seed_cache')) { $why += 'seed_cache' }
    # v2: a driver is fine when it is a pinned runner file (run-night.ps1 Test-Matrix/Resolve-Driver: drivers\* are pinned).
    $dr = Get-P $a 'driver'
    if ($null -ne $dr) {
      $dp = if ($dr -is [string]) { $dr } else { [string](Get-P $dr 'script') }
      $full = Join-Path 'bench/agent8/run' $dp
      if (-not ($dp -match '^drivers[\\/][A-Za-z0-9_.-]+$' -and (Test-Path -LiteralPath $full -PathType Leaf))) { $why += "driver:$dp" }
    }
    $cv = Get-P $a 'cvars'; $cvk = if ($null -ne $cv -and $cv -is [System.Management.Automation.PSCustomObject]) { (@($cv.PSObject.Properties | ForEach-Object Name) -join ',') } else { '' }
    if ($why.Count) { $bad++ }
    $lines.Add(('   {0,-14} bin={1}  {2}{3}' -f $id, $bin, $(if ($why.Count) { 'REFUSE[' + ($why -join ' ') + ']' } else { 'ok' }), $(if ($cvk) { "  cvars=$cvk" } else { '' })))
  }
  W ('{0}  arms={1} refused={2} sys_csv={3}' -f $rel, $arms.Count, $bad, (Get-P $mx 'sys_csv'))
  foreach ($x in $lines) { W $x }
}
W ('end ' + (Get-Date -Format 'HH:mm:ss'))
[IO.File]::WriteAllLines((Join-Path (Get-Location) 'build/agent11/launcher-review/static5-out.txt'), $OUTL, (New-Object System.Text.UTF8Encoding($false)))
'static5 done: ' + $OUTL.Count + ' lines'
