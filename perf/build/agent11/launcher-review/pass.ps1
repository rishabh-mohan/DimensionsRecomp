# pass.ps1 - read-only formal-pass helper (Agent 11, task #10).
# Snapshots bench/agent5/launch/{run-night.ps1,RUN-NIGHT.cmd,README.md} into build/agent11/launcher-review/p-<HHmm>-<sha8>/,
# byte + CRLF + PS 5.1 parse checks, diffs against previous snapshots, a grep per review item, then static6 on the snapshot.
param([string]$PrevPs1 = 'build/agent11/launcher-review/v3-163D7659/run-night.ps1',
      [string]$PrevCmd = 'build/agent11/launcher-review/v2-924321AE/RUN-NIGHT.cmd',
      [string]$PrevReadme = '')
$ErrorActionPreference = 'Continue'
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch {}
Set-Location '<workspace>'
$R = 'build/agent11/launcher-review'
$OUTL = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $OUTL.Add($s) }
$srcs = @('run-night.ps1', 'RUN-NIGHT.cmd', 'README.md')
$bytes = @{}; $sha = @{}
foreach ($n in $srcs) {
  $b = [IO.File]::ReadAllBytes((Join-Path (Get-Location) "bench/agent5/launch/$n")); $bytes[$n] = $b
  $sha[$n] = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b)).Replace('-', '')
}
$tag = 'p-' + (Get-Date -Format 'HHmm') + '-' + $sha['run-night.ps1'].Substring(0, 8)
$D = "$R/$tag"; New-Item -ItemType Directory -Force $D | Out-Null
foreach ($n in $srcs) { [IO.File]::WriteAllBytes((Join-Path (Get-Location) "$D/$n"), $bytes[$n]) }
W ('pass ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' -> ' + $D)
foreach ($n in $srcs) {
  $fi = Get-Item "bench/agent5/launch/$n"; $h2 = (Get-FileHash $fi.FullName).Hash; $b = $bytes[$n]; $t = [Text.Encoding]::UTF8.GetString($b)
  W ('{0,-14} {1} {2,6} B mtime {3:HH:mm:ss} LF={4} CR={5} nonASCII={6} BOM={7}{8}' -f $n, $sha[$n], $b.Length, $fi.LastWriteTime,
     ($t.Split("`n").Count - 1), ($t.Split("`r").Count - 1), @($b | Where-Object { $_ -gt 127 }).Count,
     ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB), $(if ($h2 -ne $sha[$n]) { '  CHANGED DURING COPY -> ' + $h2 } else { '' }))
}
$c = [Text.Encoding]::ASCII.GetString($bytes['RUN-NIGHT.cmd']); W ('RUN-NIGHT.cmd bare LF=' + ([regex]::Matches($c, '(?<!\r)\n')).Count)
$tok = $null; $err = $null
[void][Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) "$D/run-night.ps1"), [ref]$tok, [ref]$err)
W ('ParseFile errors=' + $err.Count + $(if ($err.Count) { ' first: ' + $err[0].Message + ' @L' + $err[0].Extent.StartLineNumber } else { '' }))
# 21:58 fix: a missing previous file is reported (git diff then printed nothing, which looked like "no change").
foreach ($pv in @(@($PrevPs1, 'run-night.ps1', 'diff-run-night.txt'), @($PrevCmd, 'RUN-NIGHT.cmd', 'diff-cmd.txt'), @($PrevReadme, 'README.md', 'diff-readme.txt'))) {
  if (-not $pv[0]) { continue }
  if (-not (Test-Path -LiteralPath $pv[0] -PathType Leaf)) { W ('PREV MISSING: ' + $pv[0] + ' (no ' + $pv[2] + ')'); continue }
  W ($pv[2] + ' against ' + $pv[0] + ' ' + (Get-FileHash $pv[0]).Hash.Substring(0, 8))
  & git diff --no-index -U3 -- $pv[0] "$D/$($pv[1])" 2>$null | Out-File -Encoding utf8 "$D/$($pv[2])"
}
foreach ($f in @(Get-ChildItem $D -Filter 'diff-*.txt')) { W ($f.Name + ' ' + $f.Length + ' B, +' + @(Get-Content $f.FullName | Where-Object { $_ -match '^\+[^+]' }).Count + '/-' + @(Get-Content $f.FullName | Where-Object { $_ -match '^-[^-]' }).Count) }
$items = [ordered]@{
  'A10-5 driver'   = 'AllowedDrivers|drivers\[/|\^drivers/|Resolve-Driver'
  'A10-6 14h'      = 'MaxRunHours'
  'A10-7 recheck'  = "Close-Programs 'window start'|Test-LogonUI\)|function Start-Window"
  'A10-8 PassThru' = 'Start-Process|PassThru|WaitForExit|taskkill|Kill\(|function Stop-Tree|StopNow'
  'F1 env'         = '^\s*\$AllowedEnv|without REX_|AllowedEnv -join|ENV-KEYS'
  'F3 06:45'       = '06:45|LatestStart|Get-LatestStart|NoStartAfter'
  'F4 00:00'       = 'NotBefore'
  'F5 apps'        = 'copilotapp|Windows10Universal|MicrosoftOfficeHub|ROBLOXCORPORATION|CopilotRx|CloseByPath'
  'hooks'          = 'hookNames|usedHooks|FakeRunner \)|-not \$FakeRunner'
  'args refuse'    = 'args\.Count'
}
foreach ($k in $items.Keys) {
  W ('--- ' + $k)
  Select-String -Path "$D/run-night.ps1" -Pattern $items[$k] | ForEach-Object { W ('   L' + $_.LineNumber + ': ' + $_.Line.Trim().Substring(0, [Math]::Min(170, $_.Line.Trim().Length))) }
}
W '--- README items'
Select-String -Path "$D/README.md" -Pattern 'again|06:45|00:00|17:30|14 h|REX_|LEGO_|ENV-KEYS|driver|Copilot|Roblox|STOP|smoke|FakeRunner|GraceMinutes|StartBy' | ForEach-Object { W ('   R' + $_.LineNumber + ': ' + $_.Line.Trim().Substring(0, [Math]::Min(170, $_.Line.Trim().Length))) }
W '--- RUN-NIGHT.cmd'
foreach ($ln in ($c -split "`r`n")) { if ($ln.Trim()) { W ('   ' + $ln) } }
& powershell -NoProfile -ExecutionPolicy Bypass -File "$R/static6.ps1" -Launcher "$D/run-night.ps1" -Out "$D/static6-out.txt" | Out-Null
foreach ($ln in @(Get-Content "$D/static6-out.txt" | Where-Object { $_ -match '^(Allowed|DriverRule|files=)|refused=[1-9]' })) { W ('static6: ' + $ln) }
W ('end ' + (Get-Date -Format 'HH:mm:ss'))
[IO.File]::WriteAllLines((Join-Path (Get-Location) "$D/pass.txt"), $OUTL, (New-Object System.Text.UTF8Encoding($false)))
'pass done -> ' + $D + '/pass.txt (' + $OUTL.Count + ' lines)'
