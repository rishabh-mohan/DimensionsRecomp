<#
.SYNOPSIS
  Self-test for testg_session.ps1's opt-in 'default' run (the S3 pause_safe_order default-ON check).
  Starts no game: every testg_session.ps1 call uses -CheckOnly, which exits before the launcher.
  1. testg_session.ps1 parses with 0 errors.
  2. devoff2 (S2, default OFF) with -Only default -CheckOnly refuses: exit 2, "NOT STARTED: the 'default' run needs".
  3. The cvar descriptions are compiled into devoff2 at all (the old text is found; the marker is not).
  4. devoff2 -CheckOnly with no -Only still exits 0 (or 2 with "another game is running").
  5. Fake bins (text files named legodimensions.exe under build\agent11\selftest): with the marker the
     check passes; without it, -Only default and -Only testg-default refuse, -NoMarkerCheck and a plain
     -CheckOnly don't.
  6. The run filter, taken from the script's own AST: 'default' runs only when named.
  7. The post-run check, taken from the script's own AST, on fake run dirs.
  8. harness\legodimensions.toml (the launcher's -Toml) does not set pause_safe_order.
  Optional -Devoff3: also run step 2's call on that bin and expect the "carries" line.
  Writes build\agent11\selftest\default-<time>.txt. Exit 0 if every check passes, else 1.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_default_selftest.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_default_selftest.ps1 -Devoff3 build\agent2\devoff3-bin
#>
param([string]$Devoff3 = '')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$session = Join-Path $PSScriptRoot 'testg_session.ps1'
if (-not ('TestGWin' -as [type])) {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_win.cs'))) -Language CSharp
}
$st = Join-Path $root ('build\agent11\selftest\default-{0:yyyyMMdd-HHmmss}' -f (Get-Date))
New-Item -ItemType Directory -Force -Path $st | Out-Null
$report = "$st.txt"
$out = New-Object 'System.Collections.Generic.List[string]'
$fails = 0
function Say([string]$s) { $line = ('{0:HH:mm:ss} {1}' -f (Get-Date), $s); Write-Host $line; $out.Add($line) }
function Check([string]$name, [bool]$ok, [string]$detail) {
    $script:fails += [int](-not $ok)
    Say ('{0} {1}{2}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $(if ($detail) { " - $detail" } else { '' }))
}
function Session([string[]]$argList) {
    $ErrorActionPreference = 'Continue'
    $o = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $session @argList 2>&1 | ForEach-Object { "$_" })
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    foreach ($l in $o) { $out.Add("    | $l") }
    return @{ Code = $code; Text = ($o -join "`n") }
}
$marker = 'which can hang when the guest pauses'
$gameRunning = { @([Diagnostics.Process]::GetProcessesByName('legodimensions')).Count -gt 0 }

# 1. parse
$tk = $null; $er = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($session, [ref]$tk, [ref]$er)
Check 'parse' ($er.Count -eq 0) ("{0} errors{1}" -f $er.Count, $(if ($er.Count) { ': ' + (($er | ForEach-Object { "L$($_.Extent.StartLineNumber) $($_.Message)" }) -join '; ') } else { '' }))

# 2. devoff2 must refuse
$d2 = Join-Path $root 'build\agent2\devoff2-bin'
$r = Session @('-BinDir', $d2, '-Only', 'default', '-CheckOnly')
Check 'devoff2 -Only default -CheckOnly refuses' (($r.Code -eq 2) -and ($r.Text -match "NOT STARTED: the 'default' run needs")) "exit $($r.Code)"

# 3. the descriptions are compiled in
$old = 'the unpause resumes them first. Off: the original order'
$dll2 = Join-Path $d2 'rexruntime.dll'; $exe2 = Join-Path $d2 'legodimensions.exe'
$inDll = (Test-Path -LiteralPath $dll2) -and [TestGWin]::ContainsAscii($dll2, $old)
$inExe = [TestGWin]::ContainsAscii($exe2, $old)
Check 'devoff2 carries the old description' ($inDll -or $inExe) "rexruntime.dll $inDll, exe $inExe"
$mDll = (Test-Path -LiteralPath $dll2) -and [TestGWin]::ContainsAscii($dll2, $marker)
$mExe = [TestGWin]::ContainsAscii($exe2, $marker)
Check 'devoff2 lacks the marker' (-not ($mDll -or $mExe)) "rexruntime.dll $mDll, exe $mExe"

# 4. devoff2 -CheckOnly, no -Only
$r = Session @('-BinDir', $d2, '-CheckOnly')
if ($r.Code -eq 2 -and $r.Text -match 'another game is running') { Say 'SKIP devoff2 -CheckOnly: another game is running (expected exit 0 otherwise)' }
else { Check 'devoff2 -CheckOnly (no -Only) exits 0' (($r.Code -eq 0) -and ($r.Text -match 'check only: nothing started') -and ($r.Text -notmatch 'default-ON')) "exit $($r.Code)" }

# 5. fake bins
$names = 'pause_safe_order guest_suspend_guard debug_pause_cycle_ms debug_pause_cycle_count'
$fakeYes = Join-Path $st 'fake-marker'; $fakeNo = Join-Path $st 'fake-nomarker'
New-Item -ItemType Directory -Force -Path $fakeYes, $fakeNo | Out-Null
[IO.File]::WriteAllText((Join-Path $fakeYes 'legodimensions.exe'), "fake bin for testg_default_selftest.ps1, not a program: $names. Off: the original order, $marker")
[IO.File]::WriteAllText((Join-Path $fakeNo 'legodimensions.exe'), "fake bin for testg_default_selftest.ps1, not a program: $names. Off: the original order")
$busy = & $gameRunning
$cases = @(
    @{ Name = 'fake with marker, -Only default'; Args = @('-BinDir', $fakeYes, '-Only', 'default', '-CheckOnly'); Code = 0; Want = 'carries the pause_safe_order default-ON help text'; Not = 'NOT STARTED: the' }
    @{ Name = 'fake without marker, -Only default'; Args = @('-BinDir', $fakeNo, '-Only', 'default', '-CheckOnly'); Code = 2; Want = "NOT STARTED: the 'default' run needs"; Not = '' }
    @{ Name = 'fake without marker, -Only testg-default'; Args = @('-BinDir', $fakeNo, '-Only', 'testg-default', '-CheckOnly'); Code = 2; Want = "NOT STARTED: the 'default' run needs"; Not = '' }
    @{ Name = 'fake without marker, -Only b-off,default'; Args = @('-BinDir', $fakeNo, '-Only', 'b-off,default', '-CheckOnly'); Code = 2; Want = "NOT STARTED: the 'default' run needs"; Not = '' }
    @{ Name = 'fake without marker, -Only default -NoMarkerCheck'; Args = @('-BinDir', $fakeNo, '-Only', 'default', '-NoMarkerCheck', '-CheckOnly'); Code = 0; Want = 'check only: nothing started'; Not = 'default-ON' }
    @{ Name = 'fake without marker, no -Only'; Args = @('-BinDir', $fakeNo, '-CheckOnly'); Code = 0; Want = 'check only: nothing started'; Not = 'default-ON' }
)
foreach ($c in $cases) {
    $r = Session $c.Args
    if ($busy -and $c.Code -eq 0) {
        # A running game turns the expected exit 0 into exit 2 after the marker check.
        $ok = ($r.Code -eq 2) -and ($r.Text -match 'another game is running') -and (($c.Want -notmatch 'carries') -or ($r.Text -match [regex]::Escape($c.Want)))
        Check "$($c.Name) (a game is running, so exit 2 after the marker check)" $ok "exit $($r.Code)"
        continue
    }
    $ok = ($r.Code -eq $c.Code) -and ($r.Text -match [regex]::Escape($c.Want)) -and (-not $c.Not -or $r.Text -notmatch [regex]::Escape($c.Not))
    Check $c.Name $ok "exit $($r.Code)"
}

# 6. the run filter, from the script's AST
$runsAst = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq '$runs' }, $true)
$loop = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.ForEachStatementAst] -and $n.Variable.Extent.Text -eq '$r' -and $n.Condition.Extent.Text -eq '$runs' }, $true)
$s = $loop.Body.Statements
$filterOk = ($s.Count -ge 3) -and ($s[1].Extent.Text -match '\$Only\.Count') -and ($s[2].Extent.Text -match '\$r\.OptIn')
Check 'the loop starts with $short, the -Only filter, the OptIn filter' $filterOk ''
$code = "param([string[]]`$Only)`n" + $runsAst.Extent.Text + "`n`$picked = @()`nforeach (`$r in `$runs) {`n" + $s[0].Extent.Text + "`n" + $s[1].Extent.Text + "`n" + $s[2].Extent.Text + "`n`$picked += (`$r.Name -replace '^testg-', '')`n}`n`$picked -join ','"
$sb = [scriptblock]::Create($code)
foreach ($t in @(
        @{ Only = @(); Want = 'b-off,b-on,control' }
        @{ Only = @('default'); Want = 'default' }
        @{ Only = @('testg-default'); Want = 'default' }
        @{ Only = @('b-off', 'default'); Want = 'b-off,default' }
        @{ Only = @('control'); Want = 'control' }
        @{ Only = @('b-on'); Want = 'b-on' })) {
    $got = & $sb -Only $t.Only
    Check ("filter -Only '{0}' -> {1}" -f ($t.Only -join ','), $t.Want) ($got -eq $t.Want) "got '$got'"
}

# 7. the post-run check, from the script's AST
$optIf = $loop.Body.Find({ param($n) $n -is [System.Management.Automation.Language.IfStatementAst] -and $n.Clauses[0].Item1.Extent.Text -eq '$r.OptIn' }, $true)
Check 'the post-run OptIn check exists' ($null -ne $optIf) ''
if ($optIf) {
    $sb2 = [scriptblock]::Create("param(`$d, `$r)`nfunction Say([string]`$s) { Write-Output `$s }`n" + $optIf.Extent.Text)
    $lbl = @{ OptIn = $true; Label = 'default' }
    $runOk = Join-Path $st 'run-ok'; $runSet = Join-Path $st 'run-set'; $runTomlSet = Join-Path $st 'run-tomlset'; $runNoToml = Join-Path $st 'run-notoml'
    New-Item -ItemType Directory -Force -Path $runOk, $runSet, $runTomlSet, $runNoToml | Out-Null
    $okCmd = '"x\legodimensions.exe" --log_file=x\game.log --discord_rpc=false --native_settings_load=false --pause_when_unfocused=true --guest_suspend_guard=false --debug_pause_cycle_ms=1000 --debug_pause_cycle_count=50'
    $toml = [IO.File]::ReadAllText((Join-Path $root 'harness\legodimensions.toml'))
    foreach ($dd in $runOk, $runSet, $runTomlSet, $runNoToml) { Set-Content -LiteralPath (Join-Path $dd 'cmdline.txt') -Value $okCmd }
    Set-Content -LiteralPath (Join-Path $runSet 'cmdline.txt') -Value ($okCmd + ' --pause_safe_order=true')
    foreach ($dd in $runOk, $runSet) { [IO.File]::WriteAllText((Join-Path $dd 'legodimensions.toml'), $toml) }
    [IO.File]::WriteAllText((Join-Path $runTomlSet 'legodimensions.toml'), $toml + "`r`npause_safe_order = true`r`n")
    $g = (& $sb2 $runOk $lbl) -join ' '
    Check 'post-run: clean run dir' ($g -match 'do not set pause_safe_order, so the build default picked the order') $g
    $g = (& $sb2 $runSet $lbl) -join ' '
    Check 'post-run: cmdline sets it' ($g -match 'WARNING' -and $g -match 'cmdline.txt sets pause_safe_order') $g
    $g = (& $sb2 $runTomlSet $lbl) -join ' '
    Check 'post-run: toml sets it' ($g -match 'WARNING' -and $g -match 'legodimensions.toml sets pause_safe_order') $g
    $g = (& $sb2 $runNoToml $lbl) -join ' '
    Check 'post-run: toml missing' ($g -match 'WARNING' -and $g -match 'legodimensions.toml missing') $g
}

# 8. the launcher's toml
$lt = Join-Path $root 'harness\legodimensions.toml'
Check 'harness\legodimensions.toml does not set pause_safe_order' (-not ([IO.File]::ReadAllText($lt) -match 'pause_safe_order')) ''

# optional: devoff3
if ($Devoff3) {
    $b3 = $Devoff3; if (-not [IO.Path]::IsPathRooted($b3)) { $b3 = Join-Path $root $b3 }
    $r = Session @('-BinDir', $b3, '-Only', 'default', '-CheckOnly')
    Check 'devoff3 -Only default -CheckOnly carries the marker' ($r.Text -match 'carries the pause_safe_order default-ON help text') "exit $($r.Code)$(if ($r.Text -match 'another game is running') { ' (another game is running)' })"
}

Say ("RESULT: {0} ({1} failed)" -f $(if ($fails) { 'FAIL' } else { 'PASS' }), $fails)
Say "report: $report"
[IO.File]::WriteAllLines($report, $out)
exit [int]($fails -gt 0)
