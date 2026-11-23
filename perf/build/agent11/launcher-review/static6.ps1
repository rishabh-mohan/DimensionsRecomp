# static6.ps1 - read-only replica of a run-night.ps1 version's Test-Matrix arm rules (Agent 11, task #10).
# The env and driver allowlists are read from the launcher file given (so each snapshot is checked by its own rules).
# Driver rule by version: v2 = any pinned drivers\* file (string or {script}); v3 = the $AllowedDrivers list, drivers[/\]<name>.ps1;
# CD64BC93 on = a plain string '^drivers/([A-Za-z0-9_-]+\.ps1)$' (case-sensitive, forward slash only) naming a file in drivers\.
# Not replicated: "directly in bench\agent8\run", the pins and the GO sha (W6 candidates outside bench are copied there by promote-w6).
# 21:18 edit: tolerant list parse ([type] / $script: prefixes), list counts, the CD64 driver rule.
param([string]$Launcher = 'bench/agent5/launch/run-night.ps1', [string]$Out = '')
$ErrorActionPreference = 'Continue'
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch {}
Set-Location '<workspace>'
$OUTL = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $OUTL.Add($s) }
function Get-P($O, [string]$N) { if ($null -ne $O -and $O -is [System.Management.Automation.PSCustomObject]) { $pp = $O.PSObject.Properties[$N]; if ($null -ne $pp) { return $pp.Value } }; return $null }
$lsrc = [IO.File]::ReadAllText((Resolve-Path $Launcher).Path)
$lsha = (Get-FileHash $Launcher).Hash
function Get-List([string]$Var) {
  $m = [regex]::Match($lsrc, '(?m)^\s*(?:\[[^\]]+\]\s*)?\$(?:script:)?' + $Var + '\s*=\s*@\(([^)]*)\)')
  if (-not $m.Success) { return $null }
  return ,@([regex]::Matches($m.Groups[1].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
}
$allowedEnv = Get-List 'AllowedEnv'
$allowedDrv = Get-List 'AllowedDrivers'
$cd64Rx = '''^drivers/([A-Za-z0-9_-]+\.ps1)$'''
$drvRule = if ($null -ne $allowedDrv) { 'v3-list' } elseif ($lsrc.Contains($cd64Rx)) { 'cd64-plain' } else { 'v2-any' }
W ('static6 ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' launcher=' + $Launcher + ' sha=' + $lsha)
W ('AllowedEnv=' + $(if ($null -eq $allowedEnv) { '(NOT FOUND: every env key is refused)' } else { ($allowedEnv -join ',') + ' (' + $allowedEnv.Count + ' keys)' }))
W ('DriverRule=' + $drvRule + $(switch ($drvRule) { 'v3-list' { ' AllowedDrivers=' + ($allowedDrv -join ',') } 'cd64-plain' { ' (plain string, forward slash, case-sensitive, any file in drivers\)' } default { ' (any pinned drivers\* file, string or {script})' } }))
W ('drivers dir: ' + ((Get-ChildItem bench/agent8/run/drivers -File | ForEach-Object Name) -join ', '))
$files = @(Get-ChildItem bench/agent8/run -File -Filter 'matrix*.json') +
         @(Get-ChildItem build/agent4, build/agent5, build/agent8/w6-stage, build/agent8/w8w9 -Recurse -File -Filter 'matrix*.json' -ErrorAction SilentlyContinue)
$drvUse = @{}; $keyUse = @{}; $nFiles = 0; $nOkFiles = 0
foreach ($fi in $files) {
  $nFiles++
  $rel = $fi.FullName.Replace((Get-Location).Path + '\', '')
  try { $mx = [IO.File]::ReadAllText($fi.FullName) | ConvertFrom-Json } catch { W "PARSE-FAIL $rel"; continue }
  $arms = @(Get-P $mx 'arms')
  $bad = 0; $lines = New-Object System.Collections.Generic.List[string]
  foreach ($a in $arms) {
    $id = [string](Get-P $a 'id'); $bin = [string](Get-P $a 'bin'); $bn = $bin -replace '\\', '/'
    $why = @()
    if ($bn -notmatch '^build/agent2/([A-Za-z0-9][A-Za-z0-9_.-]*)-bin/?$' -or $bn -match '\.\.') { $why += 'bin-not-agent2' }
    else { $bd = 'build/agent2/' + $Matches[1] + '-bin'; foreach ($need in @('MANIFEST.txt', 'legodimensions.exe')) { if (-not (Test-Path -LiteralPath (Join-Path $bd $need) -PathType Leaf)) { $why += "bin-missing:$need" } } }
    $ev = Get-P $a 'env'
    if ($null -ne $ev) {
      if ($ev -isnot [System.Management.Automation.PSCustomObject]) { $why += 'env-not-object' }
      else { foreach ($pp in $ev.PSObject.Properties) { $keyUse[$pp.Name] = 1 + [int]$keyUse[$pp.Name]; if ($allowedEnv -cnotcontains $pp.Name) { $why += ('env:' + $pp.Name) } } }
    }
    if ([string](Get-P $a 'menu')) { $why += 'menu' }
    if ((Get-P $a 'profile') -eq $true) { $why += 'profile' }
    if (@(Get-P $a 'triggers' | Where-Object { $_ }).Count) { $why += 'triggers' }
    $tm = Get-P $a 'toml'; if ($null -ne $tm -and @($tm.PSObject.Properties).Count) { $why += 'toml' }
    if ([string](Get-P $a 'seed_cache')) { $why += 'seed_cache' }
    $dr = Get-P $a 'driver'
    if ($null -ne $dr) {
      $dtxt = if ($dr -is [string]) { $dr } else { ($dr | ConvertTo-Json -Compress -Depth 4) }
      $drvUse[$dtxt] = 1 + [int]$drvUse[$dtxt]
      $okDrv = $false
      if ($drvRule -eq 'v2-any') {
        $dp = if ($dr -is [string]) { $dr } else { [string](Get-P $dr 'script') }
        $okDrv = ($dp -match '^drivers[\\/][A-Za-z0-9_.-]+$' -and (Test-Path -LiteralPath (Join-Path 'bench/agent8/run' $dp) -PathType Leaf))
      } elseif ($drvRule -eq 'cd64-plain') {
        if ($dr -is [string] -and $dr -cmatch '^drivers/([A-Za-z0-9_-]+\.ps1)$') { $okDrv = Test-Path -LiteralPath (Join-Path 'bench/agent8/run/drivers' $Matches[1]) -PathType Leaf }
      } elseif ($dr -is [string] -and $dr -cmatch '^drivers[/\\]([A-Za-z0-9_-]+\.ps1)$' -and $allowedDrv -contains $Matches[1]) {
        $okDrv = Test-Path -LiteralPath (Join-Path 'bench/agent8/run/drivers' $Matches[1]) -PathType Leaf
      }
      if (-not $okDrv) { $why += "driver:$dtxt" }
    }
    if ($why.Count) { $bad++ }
    $lines.Add(('   {0,-14} bin={1}  {2}' -f $id, $bin, $(if ($why.Count) { 'REFUSE[' + ($why -join ' ') + ']' } else { 'ok' })))
  }
  if ($bad -eq 0) { $nOkFiles++ }
  W ('{0}  sha={1} arms={2} refused={3} sys_csv={4}' -f $rel, (Get-FileHash $fi.FullName).Hash.Substring(0,8), $arms.Count, $bad, (Get-P $mx 'sys_csv'))
  foreach ($x in $lines) { W $x }
}
W '--- driver values used (count)'; foreach ($k in ($drvUse.Keys | Sort-Object)) { W ("   {0}  x{1}" -f $k, $drvUse[$k]) }
W '--- env keys used (count)'; foreach ($k in ($keyUse.Keys | Sort-Object)) { W ("   {0}  x{1}{2}" -f $k, $keyUse[$k], $(if ($allowedEnv -ccontains $k) { '  (allowed)' } else { '' })) }
W ("files={0} fully-accepted={1}  end {2}" -f $nFiles, $nOkFiles, (Get-Date -Format 'HH:mm:ss'))
if (-not $Out) { $Out = 'build/agent11/launcher-review/static6-out-' + $lsha.Substring(0,8) + '.txt' }
[IO.File]::WriteAllLines((Join-Path (Get-Location) $Out), $OUTL, (New-Object System.Text.UTF8Encoding($false)))
'static6 done: ' + $OUTL.Count + ' lines -> ' + $Out
