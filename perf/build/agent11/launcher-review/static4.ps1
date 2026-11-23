# static4.ps1 - read-only cross-checks for the launcher review (Agent 11, task #10)
# Reads only. Writes build/agent11/launcher-review/static4-out.txt.
$ErrorActionPreference = 'Continue'
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch {}
Set-Location '<workspace>'
$OUTL = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $OUTL.Add($s) }

W ('static4 ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
foreach ($f in 'bench/agent5/launch/run-night.ps1','bench/agent5/launch/RUN-NIGHT.cmd','bench/agent5/launch/README.md','build/agent1/hold/hold-manager.ps1','build/agent8/w6-stage/promote-w6.ps1') {
  if (Test-Path $f) { $it = Get-Item $f; W ('{0}  {1,7}  {2:HH:mm:ss}  {3}' -f (Get-FileHash $f).Hash, $it.Length, $it.LastWriteTime, $f) } else { W "MISSING $f" }
}

W ''
W '=== hold-manager.ps1 (numbered) ==='
$num = 0
foreach ($ln in [IO.File]::ReadAllLines('build/agent1/hold/hold-manager.ps1')) { $num++; W ('{0,4}: {1}' -f $num, $ln) }

W ''
W '=== run-night.ps1 selected lines ==='
$pat = 'AllowedEnv|WINDOW-GO|WINDOW-HOLD|WINDOW-STOP|function |Set-Hold|Clear-Hold|07:30|06:45|00:00|TotalMinutes|AddMinutes|GoFile|HoldFile|StopFile|StatusDir|OutDir|Start-Window|Wait-Quiet|Invoke-Go|Close-Programs|copilot|roblox|chatgpt|wallpaper|taskmgr|REX_|LEGO_|Deadline|LatestStart|stimate'
Select-String -Path 'bench/agent5/launch/run-night.ps1' -Pattern $pat | ForEach-Object { W ('{0,4}: {1}' -f $_.LineNumber, $_.Line) }

W ''
W '=== run-night.ps1 GO parser (functions with Go in the name) ==='
$rn = [IO.File]::ReadAllLines('bench/agent5/launch/run-night.ps1')
for ($i = 0; $i -lt $rn.Length; $i++) {
  if ($rn[$i] -match '^\s*function\s+\S*Go\b' -or $rn[$i] -match '^\s*function\s+\S*-Go') {
    $j = $i
    do { W ('{0,4}: {1}' -f ($j + 1), $rn[$j]); $j++ } while ($j -lt $rn.Length -and $rn[$j] -notmatch '^\s*function\s')
  }
}

W ''
W '=== promote-w6.ps1 lines with GO (case-sensitive) +-3 ==='
if (Test-Path 'build/agent8/w6-stage/promote-w6.ps1') {
  Select-String -Path 'build/agent8/w6-stage/promote-w6.ps1' -Pattern 'GO' -CaseSensitive -Context 3,3 | ForEach-Object {
    foreach ($c in $_.Context.PreContext) { W ('      {0}' -f $c) }
    W ('{0,4}> {1}' -f $_.LineNumber, $_.Line)
    foreach ($c in $_.Context.PostContext) { W ('      {0}' -f $c) }
    W '      ---'
  }
}

W ''
W '=== README lines with GO (case-sensitive) ==='
Select-String -Path 'bench/agent5/launch/README.md' -Pattern '\bGO\b|WINDOW-GO|env|REX_|LEGO_' -CaseSensitive | ForEach-Object { W ('{0,4}: {1}' -f $_.LineNumber, $_.Line) }

W ''
W '=== env keys in matrix*.json (bench/agent8/run, build/agent2..8) ==='
function Get-EnvKeys($o, [string]$path) {
  if ($null -eq $o) { return }
  if ($o -is [System.Management.Automation.PSCustomObject]) {
    foreach ($p in $o.PSObject.Properties) {
      if ($p.Name -eq 'env' -and $p.Value -is [System.Management.Automation.PSCustomObject]) {
        foreach ($q in $p.Value.PSObject.Properties) { [pscustomobject]@{ Key = $q.Name; Val = [string]$q.Value; Path = "$path.env" } }
      } else { Get-EnvKeys $p.Value "$path.$($p.Name)" }
    }
  } elseif (($o -is [System.Collections.IEnumerable]) -and -not ($o -is [string])) {
    $k = 0; foreach ($e in $o) { Get-EnvKeys $e "$path[$k]"; $k++ }
  }
}
$allowed = @('REX_TIMER_WAIT_BLOCKING','LEGO_GPU_WAIT_STATS')
$roots = 'bench/agent8/run','build/agent8','build/agent5','build/agent4','build/agent3','build/agent2'
$rows = New-Object System.Collections.Generic.List[object]
foreach ($r in $roots) {
  if (-not (Test-Path $r)) { continue }
  Get-ChildItem $r -Recurse -File -Filter 'matrix*.json' -ErrorAction SilentlyContinue | ForEach-Object {
    $rel = $_.FullName.Replace((Get-Location).Path + '\', '')
    if ($rel -match '\\matrix\\\d{8}-\d{4}' -or $rel -match '\\runs\\') { return }
    try { $js = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json } catch { W "PARSE-FAIL $rel"; return }
    foreach ($e in (Get-EnvKeys $js '')) { $rows.Add([pscustomobject]@{ Key = $e.Key; Val = $e.Val; File = $rel }) }
  }
}
$rows | Group-Object Key | Sort-Object Name | ForEach-Object {
  $flag = if ($allowed -contains $_.Name) { 'allowed' } else { 'REFUSED' }
  W ('{0,-40} {1,-8} n={2,-3} vals={3}' -f $_.Name, $flag, $_.Count, (($_.Group | ForEach-Object Val | Select-Object -Unique) -join ','))
  foreach ($fl in ($_.Group | ForEach-Object File | Select-Object -Unique)) { W ('      {0}' -f $fl) }
}

W ''
W '=== S4-DRAFT env-like names (line numbers) ==='
Select-String -Path 'perf-notes/S4-DRAFT.md' -Pattern '(LEGO_GPU_WAIT_|LEGO_NATIVE_|REX_TIMER_)[A-Z0-9_]+' -AllMatches | ForEach-Object {
  $lnum = $_.LineNumber; foreach ($m in $_.Matches) { '{0}|{1}' -f $m.Value, $lnum }
} | Group-Object { $_.Split('|')[0] } | Sort-Object Name | ForEach-Object {
  W ('{0,-40} lines {1}' -f $_.Name, (($_.Group | ForEach-Object { $_.Split('|')[1] } | Select-Object -Unique) -join ','))
}

W ''
W '=== tracked-source names (git grep --threads 2) ==='
$gg = & git grep --threads 2 -h -o -E '(LEGO_GPU_WAIT_|LEGO_NATIVE_|REX_TIMER_)[A-Z0-9_]+' -- '*.cpp' '*.h' '*.hpp' '*.cc' '*.c' '*.inl' 2>$null
$gg | Group-Object | Sort-Object Name | ForEach-Object { W ('{0,5}  {1}' -f $_.Count, $_.Name) }

W ''
W ('end ' + (Get-Date -Format 'HH:mm:ss'))
[IO.File]::WriteAllLines((Join-Path (Get-Location) 'build/agent11/launcher-review/static4-out.txt'), $OUTL, (New-Object System.Text.UTF8Encoding($false)))
'static4 done: ' + $OUTL.Count + ' lines'
