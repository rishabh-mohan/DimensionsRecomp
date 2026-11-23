# static7.ps1 - read-only check of the overnight GO lines under run-night.ps1's own rules (Agent 11, task #10, 22:40).
# Replicates Parse-Go (L225-243), Test-Matrix's arm rules (L253-299: every arm of the file, plus only= ids) and
# Get-MatrixWarnings (L322-327). Adds: each copy's sha vs the GO (promoted copy in bench\agent8\run, draft in
# build\agent8\w-followup), the MANIFEST.txt sha16 of each bin vs PROPOSAL.md, a no-C1 scan (Agent 10's rule), the
# runs/min formula, and each only= arm compared with the same arm id in the window that cleared it.
# Not replicated: Test-Pinned for drivers, Get-Plan (-PlanOnly is NOT run: it can refuse queue launches), the deadline.
param([string]$Launcher = 'bench/agent5/launch/run-night.ps1', [string]$Out = '')
$ErrorActionPreference = 'Continue'
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch {}
Set-Location '<workspace>'
$OUTL = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $OUTL.Add($s) }
function Get-P($x, [string]$n) { if ($null -ne $x -and $x -is [System.Management.Automation.PSCustomObject]) { $pp = $x.PSObject.Properties[$n]; if ($null -ne $pp) { return $pp.Value } }; return $null }
function Canon($v) {
  if ($null -eq $v) { return 'null' }
  if ($v -is [System.Management.Automation.PSCustomObject]) { return '{' + ((@($v.PSObject.Properties) | Sort-Object Name | ForEach-Object { $_.Name + ':' + (Canon $_.Value) }) -join ',') + '}' }
  if ($v -is [array]) { return '[' + ((@($v) | ForEach-Object { Canon $_ }) -join ',') + ']' }
  return (ConvertTo-Json -InputObject $v -Compress)
}
function KV($ob) { if ($null -eq $ob) { return '-' }; if ($ob -is [System.Management.Automation.PSCustomObject]) { return ((@($ob.PSObject.Properties) | ForEach-Object { $_.Name + '=' + $_.Value }) -join ';') }; return (Canon $ob) }
$lsrc = [IO.File]::ReadAllText((Resolve-Path $Launcher).Path); $lsha = (Get-FileHash $Launcher).Hash
function Get-List([string]$Var) {
  $m = [regex]::Match($lsrc, '(?m)^\s*(?:\[[^\]]+\]\s*)?\$(?:script:)?' + $Var + '\s*=\s*@\(([^)]*)\)')
  if (-not $m.Success) { return $null }
  return ,@([regex]::Matches($m.Groups[1].Value, "'([^']*)'") | ForEach-Object { $_.Groups[1].Value })
}
$allowedEnv = Get-List 'AllowedEnv'; $allowedDrv = Get-List 'AllowedDrivers'
W ('static7 ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' launcher=' + $Launcher + ' sha=' + $lsha)
W ('AllowedEnv (' + @($allowedEnv).Count + '): ' + ($allowedEnv -join ','))
W ('AllowedDrivers (' + @($allowedDrv).Count + '): ' + ($allowedDrv -join ','))
$manExp = @{ 'devoff4b' = 'DE11A914079D7DF7'; 'devoff4' = '16DCC9399239E577'; 'devoff2' = 'B87DC2D2CA22379F'; 'devoffB' = '8709476FF4778768' }
$manCache = @{}
function Get-Man16([string]$bin) {
  $bn = $bin -replace '\\', '/'
  if ($bn -notmatch '^build/agent2/([A-Za-z0-9][A-Za-z0-9_.-]*)-bin/?$') { return '-' }
  $nm = $Matches[1]
  if (-not $manCache.ContainsKey($nm)) {
    $mf = 'build/agent2/' + $nm + '-bin/MANIFEST.txt'
    $manCache[$nm] = if (Test-Path -LiteralPath $mf -PathType Leaf) { (Get-FileHash -LiteralPath $mf).Hash.Substring(0, 16) } else { 'NO-MANIFEST' }
  }
  $h = $manCache[$nm]; $e = $manExp[$nm]
  return $h + $(if ($null -eq $e) { '' } elseif ($e -eq $h) { '(=PROPOSAL)' } else { '(PROPOSAL says ' + $e + ')' })
}
function Test-Arm($a) {
  $why = New-Object System.Collections.Generic.List[string]
  $bin = [string](Get-P $a 'bin'); $bn = $bin -replace '\\', '/'
  if ($bn -notmatch '^build/agent2/([A-Za-z0-9][A-Za-z0-9_.-]*)-bin/?$' -or $bn -match '\.\.') { $why.Add('bin-not-agent2') }
  else { $bd = 'build/agent2/' + $Matches[1] + '-bin'; foreach ($need in 'MANIFEST.txt', 'legodimensions.exe') { if (-not (Test-Path -LiteralPath (Join-Path $bd $need) -PathType Leaf)) { $why.Add("bin-missing:$need") } } }
  $ev = Get-P $a 'env'
  if ($null -ne $ev) { if ($ev -isnot [System.Management.Automation.PSCustomObject]) { $why.Add('env-not-object') } else { foreach ($pp in $ev.PSObject.Properties) { if ($allowedEnv -cnotcontains $pp.Name) { $why.Add('env:' + $pp.Name) } } } }
  if ([string](Get-P $a 'menu')) { $why.Add('menu') }
  if ((Get-P $a 'profile') -eq $true) { $why.Add('profile') }
  if (@(Get-P $a 'triggers' | Where-Object { $_ }).Count) { $why.Add('triggers') }
  $tm = Get-P $a 'toml'; if ($null -ne $tm -and @($tm.PSObject.Properties).Count) { $why.Add('toml') }
  if ([string](Get-P $a 'seed_cache')) { $why.Add('seed_cache') }
  $dr = Get-P $a 'driver'
  if ($null -ne $dr) {
    $ok = $false
    if ($dr -is [string] -and $dr -cmatch '^drivers/([A-Za-z0-9_-]+\.ps1)$') { $dn = $Matches[1]; $ok = ($allowedDrv -ccontains $dn) -and (Test-Path -LiteralPath (Join-Path 'bench/agent8/run/drivers' $dn) -PathType Leaf) }
    if (-not $ok) { $why.Add('driver:' + $(if ($dr -is [string]) { $dr } else { Canon $dr })) }
  }
  return , $why
}
function Parse-GoR([string]$Text) {
  $g = @{ ok = $false; why = New-Object System.Collections.Generic.List[string]; id = ''; json = ''; sha = ''; only = @(); repeats = 0 }
  $t = @($Text.Trim() -split '\s+')
  if ($t.Count -ne 6) { $g.why.Add("6 tokens needed, it has $($t.Count)"); return $g }
  $idRx = '[A-Za-z0-9][A-Za-z0-9_.-]{0,31}'
  if ($t[0] -cne 'GO') { $g.why.Add('first token') }
  if ($t[1] -notmatch "^$idRx$") { $g.why.Add('window id') } else { $g.id = $t[1] }
  if ($t[2] -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.json$' -or $t[2] -match '\.\.') { $g.why.Add('matrix name') } else { $g.json = $t[2] }
  if ($t[3] -notmatch '^[0-9A-Fa-f]{64}$') { $g.why.Add('sha256') } else { $g.sha = $t[3].ToUpperInvariant() }
  if ($t[4] -cnotmatch "^only=$idRx(,$idRx)*$") { $g.why.Add('only=') } else { $g.only = @($t[4].Substring(5) -split ','); if (@($g.only | Select-Object -Unique).Count -ne $g.only.Count) { $g.why.Add('only= lists an arm twice') } }
  if ($t[5] -cnotmatch '^repeats=([1-9]|1[0-9]|20)$') { $g.why.Add('repeats') } else { $g.repeats = [int]$t[5].Substring(8) }
  $g.ok = ($g.why.Count -eq 0); return $g
}
$gos = @(
  'GO W6 matrix-window6.json E50D791B6C38638F718A1AF65EB15EAF543A78AC8EA50B69DD1CC96AB7C9A0D2 only=s0,p2,p2f,p2fc repeats=5',
  'GO W9 matrix-window9.json CE0AD75792B47D59876C864B39797CD877404F911D12F92E6CC9C4351D747610 only=off,q0,q125,q250,q500 repeats=4',
  'GO W5b matrix-window5b.json 23575AAAE9DCBB85C9965AC8A3A8794916FFA881C09C656A6512C7EE462D5F76 only=d11,d11t,d11p repeats=6',
  'GO W4c matrix-window4c.json E2E3E4DAAF7D30C7B8B2D28D21911E6EACDA5260963F9B99095EE70C09022396 only=d0,B repeats=6',
  'GO W8a matrix-window8a.json A06E5E3AAEE25B079532DE8BFC9134D7462B5F842ECB9FADA19B6FD8DD8A475E only=n0,mc repeats=6',
  'GO W8a4 matrix-window8a4.json 56BE00D8131981A735CC40142980316F9E834D0B51F103A143BA6105AA5DA1D1 only=n4,n4mc repeats=6')
$ref = @{ 'W5b' = 'bench/agent8/run/matrix-window5-s3d.json'; 'W4c' = 'bench/agent8/run/matrix-window4.json' }
foreach ($line in $gos) {
  $g = Parse-GoR $line
  W ''; W ('=== ' + $line)
  W ('  Parse-Go: ' + $(if ($g.ok) { 'ok' } else { 'REFUSE ' + ($g.why -join '; ') }))
  $use = $null
  foreach ($loc in 'bench/agent8/run', 'build/agent8/w-followup') {
    $p = $loc + '/' + $g.json
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { W ('  ' + $p + ': not there' + $(if ($loc -eq 'bench/agent8/run') { ' (not promoted yet; the launcher reads only this folder)' } else { '' })); continue }
    $h = (Get-FileHash -LiteralPath $p).Hash
    W ('  ' + $p + ': ' + $(if ($h -eq $g.sha) { 'sha = GO' } else { 'sha MISMATCH ' + $h.Substring(0, 8) }) + ', ' + (Get-Item -LiteralPath $p).LastWriteTime.ToString('HH:mm:ss') + $(if ($loc -eq 'bench/agent8/run') { ' (promoted)' } else { ' (draft)' }))
    if ($null -eq $use -and $h -eq $g.sha) { $use = $p }
  }
  if ($null -eq $use) { W '  no copy has the GO sha: arms not checked'; continue }
  $mx = [IO.File]::ReadAllText((Resolve-Path $use).Path) | ConvertFrom-Json
  $arms = @(Get-P $mx 'arms'); $ids = @($arms | ForEach-Object { [string](Get-P $_ 'id') })
  W ('  file arms (' + $arms.Count + '): ' + ($ids -join ',') + '; sys_csv=' + (Get-P $mx 'sys_csv') + $(if ((Get-P $mx 'sys_csv') -ne $true) { ' WARNING: no sys.json' } else { '' }) + '; other top keys: ' + ((@($mx.PSObject.Properties | Where-Object { 'arms', 'sys_csv' -notcontains $_.Name } | ForEach-Object { $_.Name + '=' + (Canon $_.Value) })) -join ' '))
  foreach ($oa in $g.only) { if ($ids -cnotcontains $oa) { W ("  REFUSE only=: no arm '" + $oa + "'") } }
  $rx = $null; if ($ref.ContainsKey($g.id) -and (Test-Path $ref[$g.id])) { $rx = [IO.File]::ReadAllText((Resolve-Path $ref[$g.id]).Path) | ConvertFrom-Json }
  $nBad = 0
  foreach ($a in $arms) {
    $id = [string](Get-P $a 'id'); $why = Test-Arm $a; if ($why.Count) { $nBad++ }
    $c1 = if ((Canon $a) -match '(?i)keep_watch|physical_protect') { ' C1!' } else { '' }
    $other = (@($a.PSObject.Properties | Where-Object { 'id', 'bin', 'env', 'cvars' -notcontains $_.Name } | ForEach-Object { $_.Name + '=' + (Canon $_.Value) }) -join ' ')
    W ('  {0} {1,-6} {2} man={3} env[{4}] cvars[{5}] other[{6}]{7} -> {8}' -f $(if ($g.only -ccontains $id) { '*' } else { ' ' }), $id, (Get-P $a 'bin'), (Get-Man16 ([string](Get-P $a 'bin'))), (KV (Get-P $a 'env')), (KV (Get-P $a 'cvars')), $other, $c1, $(if ($why.Count) { 'REFUSE[' + ($why -join ' ') + ']' } else { 'ok' }))
    if ($null -ne $rx -and $g.only -ccontains $id) {
      $ra = @(@(Get-P $rx 'arms') | Where-Object { [string](Get-P $_ 'id') -ceq $id })
      if ($ra.Count -ne 1) { W ('      vs ' + $ref[$g.id] + ': ' + $ra.Count + ' arms with id ' + $id) }
      else {
        $diffs = @(); $names = @(@($a.PSObject.Properties | ForEach-Object Name) + @($ra[0].PSObject.Properties | ForEach-Object Name) | Sort-Object -Unique)
        foreach ($pn in $names) { $x1 = Canon (Get-P $a $pn); $x2 = Canon (Get-P $ra[0] $pn); if ($x1 -cne $x2) { $diffs += ($pn + ': ' + $x2 + ' -> ' + $x1) } }
        W ('      vs ' + $ref[$g.id] + ' arm ' + $id + ': ' + $(if ($diffs.Count) { 'DIFF ' + ($diffs -join ' || ') } else { 'identical' }))
      }
    }
  }
  W ('  arm rules: ' + $(if ($nBad) { "$nBad arm(s) REFUSED (Test-Matrix checks every arm of the file)" } else { 'all ' + $arms.Count + ' arms pass' }))
  $A = $g.only.Count; $R = $g.repeats
  W ('  runs = 1 + {0} x {1} = {2}; min = 1.70 + 2.14 x {3} = {4:N1}' -f $A, $R, (1 + $A * $R), ($A * $R), (1.70 + 2.14 * $A * $R))
}
W ''; W '--- every matrix in build/agent8/w-followup (replica sanity: the negative tests should be refused)'
foreach ($fi in @(Get-ChildItem build/agent8/w-followup -Recurse -File -Filter '*.json')) {
  $rel = $fi.FullName.Replace((Get-Location).Path + '\', '')
  try { $mx = [IO.File]::ReadAllText($fi.FullName) | ConvertFrom-Json } catch { W ('  PARSE-FAIL ' + $rel); continue }
  $arms = @(Get-P $mx 'arms'); $bad = @()
  foreach ($a in $arms) { $why = Test-Arm $a; if ($why.Count) { $bad += ([string](Get-P $a 'id') + '[' + ($why -join ' ') + ']') } }
  W ('  {0} sha={1} arms={2} refused={3} {4}' -f $rel, (Get-FileHash $fi.FullName).Hash.Substring(0, 8), $arms.Count, $bad.Count, ($bad -join ' '))
}
W ('end ' + (Get-Date -Format 'HH:mm:ss'))
if (-not $Out) { $Out = 'build/agent11/launcher-review/static7-out-' + (Get-Date -Format 'HHmm') + '.txt' }
[IO.File]::WriteAllLines((Join-Path (Get-Location) $Out), $OUTL, (New-Object System.Text.UTF8Encoding($false)))
'static7 done: ' + $OUTL.Count + ' lines -> ' + $Out
