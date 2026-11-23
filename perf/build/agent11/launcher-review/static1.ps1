# Agent 11, run-2 task #10: read-only static checks of bench\agent5\launch\ (launcher review). Writes nothing outside
# build\agent11\launcher-review\. Output: static1-out.txt next to this file.
$ErrorActionPreference = 'Continue'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $repo
$out = Join-Path $PSScriptRoot 'static1-out.txt'
$OUTL = New-Object System.Collections.Generic.List[string]
function W([string]$s) { $OUTL.Add($s) }
W "static1 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
foreach ($f in @('bench\agent5\launch\run-night.ps1', 'bench\agent5\launch\RUN-NIGHT.cmd', 'bench\agent5\launch\README.md')) {
    $b = [IO.File]::ReadAllBytes($f)
    $lf = 0; $cr = 0; $na = 0; foreach ($x in $b) { if ($x -eq 10) { $lf++ } elseif ($x -eq 13) { $cr++ } elseif ($x -gt 127) { $na++ } }
    W ("{0}: {1} B, LF {2}, CR {3}, non-ASCII {4}, first bytes {5}, sha256 {6}, mtime {7}" -f $f, $b.Length, $lf, $cr, $na, (($b[0..2] | % { '{0:X2}' -f $_ }) -join ' '), (Get-FileHash $f -Algorithm SHA256).Hash, (Get-Item $f).LastWriteTime.ToString('HH:mm:ss'))
}
W '--- PS 5.1 parse of run-night.ps1'
$tok = $null; $err = $null
[void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo 'bench\agent5\launch\run-night.ps1'), [ref]$tok, [ref]$err)
W "parse errors: $(@($err).Count) (PowerShell $($PSVersionTable.PSVersion))"
foreach ($e in @($err)) { W "  $($e.Extent.StartLineNumber): $($e.Message)" }
W '--- RUN-NIGHT.cmd'
Get-Content 'bench\agent5\launch\RUN-NIGHT.cmd' | % { W "  | $_" }
W '--- README grep (HOLD|manager|00:00|06:45|07:30|Agent 1|screensaver|close|GO file|who)'
$i = 0; foreach ($l in (Get-Content 'bench\agent5\launch\README.md')) { $i++; if ($l -match 'HOLD|manager|00:00|06:45|07:30|Agent 1\b|screensaver|Screensaver|clos|who |W9|BACKOFF|env') { W ("  {0,4}: {1}" -f $i, $l) } }
W '--- SESSION2 L2560-2580, L2695-2720 (LF-split)'
$s2 = [IO.File]::ReadAllText((Join-Path $repo 'perf-notes\SESSION2.md')) -split "`n"
W "SESSION2 LF lines: $($s2.Count - 1)"
foreach ($r in @(@(2560, 2580), @(2695, 2720), @(2779, 2830))) { for ($k = $r[0]; $k -le [math]::Min($r[1], $s2.Count); $k++) { W ("  {0,4}: {1}" -f $k, $s2[$k - 1].TrimEnd("`r")) } ; W '  ...' }
W '--- S4-DRAFT grep (W6|W7|W8|W9|W10|BACKOFF|SPIN_US|C1 ON|seed)'
$i = 0; foreach ($l in (Get-Content 'perf-notes\S4-DRAFT.md')) { $i++; if ($l -match '\bW(6|7|8a?|8b|9|10)\b.*(arm|env|Q ?=|cvar|toml|C1|verify|#\d)|BACKOFF|SPIN_US') { W ("  {0,4}: {1}" -f $i, $(if ($l.Length -gt 400) { $l.Substring(0, 400) + ' [...]' } else { $l })) } }
W '--- bench\agent8\run listing'
Get-ChildItem 'bench\agent8\run' -File | Sort-Object Name | % { W ("  {0,-48} {1,8} {2}" -f $_.Name, $_.Length, $_.LastWriteTime.ToString('MM-dd HH:mm')) }
if (Test-Path 'bench\agent8\run\drivers') { Get-ChildItem 'bench\agent8\run\drivers' -File -Recurse | % { W ("  drivers\{0,-40} {1,8}" -f $_.Name, $_.Length) } }
Get-ChildItem 'bench\agent8\run' -Directory | % { W "  [dir] $($_.Name)" }
W '--- dot-sourcing / file reads in the runner .ps1 files'
foreach ($f in @(Get-ChildItem 'bench\agent8\run' -Filter *.ps1 -File -Recurse)) {
    $i = 0; foreach ($l in (Get-Content $f.FullName)) { $i++; if ($l -match '^\s*\.\s+[\$"''(]|Join-Path \$PSScriptRoot|Add-Type .*-Path|Import-Module|harness\\|\.toml|nvml') { W ("  {0}:{1}: {2}" -f $f.Name, $i, $(if ($l.Length -gt 220) { $l.Substring(0, 220) + ' [...]' } else { $l.Trim() })) } }
}
W '--- arm fields read by run-matrix.ps1 (Get-P / .field patterns)'
$rm = Get-Content 'bench\agent8\run\run-matrix.ps1'
$fields = @{}
foreach ($l in $rm) { foreach ($m in [regex]::Matches($l, "(?:Get-(?:P|Prop|Field|ArmProp|Val)\w*\s+\`$\w+\s+'([a-z_0-9]+)')|(?:\`$(?:arm|a|A|Arm)\.([a-z_0-9]+))")) { $n = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }; $fields[$n] = 1 + [int]$fields[$n] } }
W ("  fields: " + ((@($fields.Keys | Sort-Object) | % { "$_($($fields[$_]))" }) -join ' '))
$i = 0; foreach ($l in $rm) { $i++; if ($l -match 'param\(|\[string\[\]\]\$Only|\$Only\b.*-split|PlanOnly|ColdShared|NoPrompt|^estimate|estimate ') { W ("  run-matrix:{0}: {1}" -f $i, $(if ($l.Length -gt 200) { $l.Substring(0, 200) + ' [...]' } else { $l.Trim() })) } }
W '--- exe hashing / env clearing in the runner'
foreach ($f in @(Get-ChildItem 'bench\agent8\run' -Filter *.ps1 -File)) {
    $i = 0; foreach ($l in (Get-Content $f.FullName)) { $i++; if ($l -match 'Get-FileHash|MANIFEST|REX_TIMER|LEGO_GPU|SetEnvironmentVariable|\$env:(REX|LEGO)|Remove-Item\s+env:') { W ("  {0}:{1}: {2}" -f $f.Name, $i, $(if ($l.Length -gt 200) { $l.Substring(0, 200) + ' [...]' } else { $l.Trim() })) } }
}
W '--- matrix json files in bench\agent8\run: arm ids, bins, env keys, launcher-rule fields'
foreach ($j in @(Get-ChildItem 'bench\agent8\run' -Filter *.json -File | Sort-Object Name)) {
    try { $mx = Get-Content $j.FullName -Raw | ConvertFrom-Json } catch { W "  $($j.Name): not JSON"; continue }
    $arms = @($mx.PSObject.Properties['arms'] | % { $_.Value })
    if (-not $arms.Count) { W "  $($j.Name): no arms"; continue }
    $parts = foreach ($a in $arms) {
        $p = $a.PSObject.Properties
        $id = [string]$p['id'].Value
        $bin = if ($p['bin']) { [string]$p['bin'].Value } else { '-' }
        $env = if ($p['env'] -and $p['env'].Value) { (@($p['env'].Value.PSObject.Properties | % { $_.Name }) -join '+') } else { '' }
        $extra = @($p | % { $_.Name } | ? { @('id', 'bin', 'env') -notcontains $_ }) -join ','
        $flag = @()
        if ($id -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$') { $flag += 'ID!' }
        if (($bin -replace '\\', '/') -notmatch '^build/agent2/[A-Za-z0-9][A-Za-z0-9_.-]*-bin/?$') { $flag += 'BIN!' }
        if ($env) { foreach ($k in ($env -split '\+')) { if (@('REX_TIMER_WAIT_BLOCKING', 'LEGO_GPU_WAIT_STATS') -cnotcontains $k) { $flag += "ENV!$k" } } }
        if ($p['menu'] -and [string]$p['menu'].Value) { $flag += 'MENU!' }
        if ($p['profile'] -and $p['profile'].Value -eq $true) { $flag += 'PROFILE!' }
        if ($p['triggers'] -and @($p['triggers'].Value | ? { $_ }).Count) { $flag += 'TRIG!' }
        if ($p['toml'] -and $p['toml'].Value -and @($p['toml'].Value.PSObject.Properties).Count) { $flag += 'TOML!' }
        if ($p['seed_cache'] -and [string]$p['seed_cache'].Value) { $flag += 'SEED!' }
        "$id[$($bin -replace '^build[\\/]agent2[\\/]', '')$(if ($env) { "; env $env" })$(if ($extra) { "; $extra" })]$(if ($flag.Count) { ' ' + ($flag -join ' ') })"
    }
    $top = @($mx.PSObject.Properties | % { $_.Name } | ? { $_ -ne 'arms' }) -join ','
    W "  $($j.Name) ($($j.LastWriteTime.ToString('MM-dd HH:mm')); top: $top): $($parts -join ' | ')"
}
W '--- HOLD manager (who writes/removes perf-notes\WINDOW-HOLD.txt)'
foreach ($d in @('build\agent1', 'bench\agent1', 'perf-notes')) {
    if (Test-Path $d) { Get-ChildItem $d -File -Recurse -Include *.ps1, *.py, *.cmd -ErrorAction SilentlyContinue | ? { $_.Length -lt 2MB } | % { $hit = Select-String -LiteralPath $_.FullName -Pattern 'WINDOW-HOLD' -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 3; foreach ($h in $hit) { W ("  {0}:{1}: {2}" -f $_.FullName.Substring($repo.Length + 1), $h.LineNumber, $h.Line.Trim().Substring(0, [math]::Min(200, $h.Line.Trim().Length))) } } }
}
$i = 0; foreach ($l in $s2) { $i++; if ($l -match 'HOLD manager|hold manager|task-135') { W ("  SESSION2 {0}: {1}" -f $i, $(if ($l.Length -gt 300) { $l.Substring(0, 300) + ' [...]' } else { $l.TrimEnd("`r") })) } }
W '--- launch-test results (Agent 5)'
if (Test-Path 'build\agent5\launch-test') { Get-ChildItem 'build\agent5\launch-test' -Recurse -File | Sort-Object LastWriteTime | Select-Object -Last 25 | % { W ("  {0,-70} {1,8} {2}" -f $_.FullName.Substring($repo.Length + 1), $_.Length, $_.LastWriteTime.ToString('HH:mm:ss')) } }
W '--- machine: inactivity-lock policy, screensaver, running close-list processes'
$pol = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -ErrorAction SilentlyContinue
W "  InactivityTimeoutSecs: $(if ($pol -and $pol.PSObject.Properties['InactivityTimeoutSecs']) { $pol.InactivityTimeoutSecs } else { 'not set' })"
$dk = Get-ItemProperty 'HKCU:\Control Panel\Desktop'
W "  ScreenSaveActive=$($dk.ScreenSaveActive) SCRNSAVE.EXE=$(if ($dk.PSObject.Properties['SCRNSAVE.EXE']) { $dk.'SCRNSAVE.EXE' } else { 'absent' }) ScreenSaverIsSecure=$(if ($dk.PSObject.Properties['ScreenSaverIsSecure']) { $dk.ScreenSaverIsSecure } else { 'absent' })"
$names = @('ChatGPT', 'Copilot', 'Microsoft.Copilot', 'Roblox', 'RobloxPlayerBeta', 'RobloxPlayerLauncher', 'RobloxStudioBeta', 'RobloxStudioLauncherBeta', 'Taskmgr', 'wallpaper32', 'wallpaper64', 'webwallpaper32', 'webwallpaper64', 'ui32', 'ui64')
foreach ($p in [Diagnostics.Process]::GetProcesses()) { if ($names -contains $p.ProcessName -or $p.ProcessName -match 'copilot|chatgpt|roblox|wallpaper') { $path = ''; try { $path = $p.MainModule.FileName } catch { $path = '(path not readable)' }; W "  running: $($p.ProcessName) pid $($p.Id) $path" } }
[IO.File]::WriteAllLines($out, $OUTL)
"wrote $out ($($OUTL.Count) lines)"
