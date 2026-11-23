# test-scrnsave.ps1: Agent 5, task #26. Tests the SCRNSAVE.EXE/StrictMode fix with SCRNSAVE.EXE missing (and present).
# Registry: only a scratch key, HKCU:\Software\Agent5-scrnsave-test\Desktop, created and deleted here. It never writes
# HKCU:\Control Panel\Desktop and never calls SystemParametersInfo: a fake [LdNight] class records the calls instead.
# No game, runner, launcher or build. -E2E also runs run-matrix.ps1 -PlanOnly (reads only, starts nothing) end to end,
# with Get-ItemProperty of 'HKCU:\Control Panel\Desktop' redirected to the scratch key (e2e-driver.ps1): -Set new uses
# copies of bench\agent8\run in build\agent5\sfx-base and build\agent5\sfx-new (deleted at the end); -Set installed uses
# bench\agent8\run itself. The negative controls always use base\ (the files before the fix).
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\scrnsave-fix\test-scrnsave.ps1 [-Set new|installed] [-E2E]
param([ValidateSet('new', 'installed')][string]$Set = 'new', [switch]$E2E)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$Base = Join-Path $Here 'base'
if ($Set -eq 'new') {
    $Files = [ordered]@{ matrix = Join-Path $Here 'new\run-matrix.ps1'; night = Join-Path $Here 'new\run-night.ps1'; day = Join-Path $Here 'new\day\run-day.ps1' }
} else {
    $Files = [ordered]@{ matrix = Join-Path $Repo 'bench\agent8\run\run-matrix.ps1'; night = Join-Path $Repo 'bench\agent5\launch\run-night.ps1'; day = Join-Path $Repo 'build\agent5\day-draft\run-day.ps1' }
}
$Old = [ordered]@{ matrix = Join-Path $Base 'run-matrix.ps1'; night = Join-Path $Base 'run-night.ps1'; day = Join-Path $Base 'run-day.ps1' }
$TestRoot = 'HKCU:\Software\Agent5-scrnsave-test'
$FakeDesk = "$TestRoot\Desktop"
$RealDesk = 'HKCU:\Control Panel\Desktop'
$Scr = 'C:\Windows\System32\Mystify.scr'
$Out = Join-Path $Here 'results'
$Stamp = Get-Date -Format 'HHmmss'
$CaseDir = Join-Path $Out "cases-$Set-$Stamp"
New-Item -ItemType Directory -Force -Path $Out, $CaseDir | Out-Null
$script:Results = New-Object System.Collections.Generic.List[string]
$script:Fails = 0
$script:LogLines = New-Object System.Collections.Generic.List[string]
$script:SsSaved = $null
$Inv = [Globalization.CultureInfo]::InvariantCulture
function Check([string]$Id, [bool]$Ok, [string]$Detail) {
    $line = "$(if ($Ok) { 'PASS' } else { 'FAIL' })  $Id  $Detail"
    $script:Results.Add($line); if (-not $Ok) { $script:Fails++ }
    Write-Host $line -ForegroundColor $(if ($Ok) { 'Green' } else { 'Red' })
}
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function Get-RealState {
    $k = Get-Item -LiteralPath $RealDesk
    try {
        $names = @($k.GetValueNames())
        $e = if ($names -contains 'SCRNSAVE.EXE') { "present '$($k.GetValue('SCRNSAVE.EXE'))' $($k.GetValueKind('SCRNSAVE.EXE'))" } else { 'absent' }
        $a = if ($names -contains 'ScreenSaveActive') { [string]$k.GetValue('ScreenSaveActive') } else { 'absent' }
        return "SCRNSAVE.EXE $e; ScreenSaveActive $a"
    } finally { $k.Close() }
}
function Reset-Key($Values) {   # ordered hashtable of string values; $null = no key at all
    if (Test-Path -LiteralPath $TestRoot) { Remove-Item -LiteralPath $TestRoot -Recurse -Force }
    if ($null -eq $Values) { return }
    New-Item -Path $FakeDesk -Force | Out-Null
    foreach ($k in $Values.Keys) { New-ItemProperty -LiteralPath $FakeDesk -Name $k -Value $Values[$k] -PropertyType String | Out-Null }
}
function Get-ExeState {
    if (-not (Test-Path -LiteralPath $FakeDesk)) { return 'no key' }
    $k = Get-Item -LiteralPath $FakeDesk
    try {
        if (@($k.GetValueNames()) -contains 'SCRNSAVE.EXE') { return "present '$($k.GetValue('SCRNSAVE.EXE'))' $($k.GetValueKind('SCRNSAVE.EXE'))" }
        return 'absent'
    } finally { $k.Close() }
}
function Get-FuncText([string]$Path, [string[]]$Names) {
    $tk = $null; $pe = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tk, [ref]$pe)
    if (@($pe).Count) { throw "$Path has parse errors" }
    $all = @($ast.FindAll({ param($x) $x -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true))
    $parts = foreach ($n in $Names) {
        $f = @($all | Where-Object { $_.Name -eq $n })
        if ($f.Count -ne 1) { throw "$Path defines function $n $($f.Count) times" }
        $f[0].Extent.Text
    }
    return ($parts -join "`n")
}
function Get-MatrixBlock([string]$Path) {
    $lines = [IO.File]::ReadAllLines($Path)
    $a = @(for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].StartsWith("`$scr = Get-ItemProperty -LiteralPath '$RealDesk'")) { $i } })
    $b = @(for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Contains("`$pre.Add('screensaver none')")) { $i } })
    if ($a.Count -ne 1 -or $b.Count -ne 1 -or $b[0] -le $a[0] -or ($b[0] - $a[0]) -gt 6) { throw "screensaver block not found in $Path" }
    $blk = ($lines[$a[0]..$b[0]] -join "`n")
    if (([regex]::Matches($blk, [regex]::Escape("'$RealDesk'"))).Count -ne 1) { throw "the block in $Path names the desktop key more than once" }
    return $blk.Replace("'$RealDesk'", "'$FakeDesk'")
}
function Invoke-MBlock([string]$Block, [string]$GetP) {
    $sb = [scriptblock]::Create("Set-StrictMode -Version 2`n$GetP`n`$pre = New-Object System.Collections.Generic.List[string]`n$Block`n`$pre.ToArray()")
    try { $r = @(& $sb); return @{ ok = $true; lines = @($r); err = '' } }
    catch { return @{ ok = $false; lines = @(); err = $_.Exception.Message } }
}

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
public static class LdNight {
    public static List<string> Calls = new List<string>();
    public static bool SystemParametersInfoW(uint uiAction, uint uiParam, IntPtr pvParam, uint fWinIni) { Calls.Add(uiAction + "," + uiParam + "," + fWinIni); return true; }
}
'@

$real0 = Get-RealState
$hdr = "test-scrnsave -Set $Set$(if ($E2E) { ' -E2E' }) at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); real desktop key: $real0"
Write-Host $hdr
$hashLines = @(foreach ($k in $Files.Keys) { "  $k $(Sha $Files[$k])  $($Files[$k].Substring($Repo.Length + 1))" }) + @(foreach ($k in $Old.Keys) { "  old $k $(Sha $Old[$k])" })
$hashLines | ForEach-Object { Write-Host $_ }
$sandboxes = New-Object System.Collections.Generic.List[string]
try {
    # ---------- S: static checks ----------
    foreach ($k in $Files.Keys) {
        $tk = $null; $pe = $null; [void][System.Management.Automation.Language.Parser]::ParseFile($Files[$k], [ref]$tk, [ref]$pe)
        $bytes = [IO.File]::ReadAllBytes($Files[$k]); $bad = @($bytes | Where-Object { $_ -gt 126 -or $_ -eq 13 }).Count
        Check "s-parse-$k" (@($pe).Count -eq 0 -and $bad -eq 0) "parse errors $(@($pe).Count), non-ASCII or CR bytes $bad"
    }
    $mt = [IO.File]::ReadAllText($Files.matrix)
    $plain = @([regex]::Matches($mt, '\$scr\.(?!PSObject)') | ForEach-Object { $_.Value }).Count
    Check 's-matrix-reads' ($plain -eq 0 -and $mt.Contains("[string](Get-P `$scr 'SCRNSAVE.EXE' '')")) "plain `$scr.<name> reads left: $plain"
    foreach ($k in 'night', 'day') {
        $txt = [IO.File]::ReadAllText($Files[$k])
        $rm = @([regex]::Matches($txt, 'Remove-ItemProperty')).Count
        $setNone = Get-FuncText $Files[$k] @('Set-ScreensaverNone'); $rest = Get-FuncText $Files[$k] @('Restore-Screensaver')
        Check "s-$k-remove" ($rm -eq 1 -and -not $setNone.Contains('Remove-ItemProperty') -and $rest.Contains('Remove-ItemProperty') -and $setNone.Contains("-Name 'SCRNSAVE.EXE' -Value '' -Type String")) "Remove-ItemProperty $rm time(s), only in Restore-Screensaver; Set-ScreensaverNone sets ''"
    }
    $dayText = [IO.File]::ReadAllText($Files.day); $n8 = (Sha $Files.night).Substring(0, 8)
    $marks = @(([IO.File]::ReadAllLines($Files.day)) | Where-Object { $_.Contains('# DAY:') }).Count
    $same = (Get-FuncText $Files.night @('Save-Screensaver', 'Set-ScreensaverNone', 'Restore-Screensaver')) -eq (Get-FuncText $Files.day @('Save-Screensaver', 'Set-ScreensaverNone', 'Restore-Screensaver'))
    Check 's-day-same' ($same -and $marks -eq 7 -and $dayText.Contains("made from run-night.ps1 (sha $n8) by make-run-day.ps1")) "run-day.ps1: screensaver functions identical to run-night.ps1 $same; '# DAY:' lines $marks; header names $n8"
    $dh = @([IO.File]::ReadAllLines((Join-Path (Split-Path -Parent $Files.day) 'run-day.diff')) | Where-Object { $_ -match '^(diff --git |--- |\+\+\+ )' })
    $dabs = @($dh | Where-Object { $_ -match '[A-Za-z]:[\\/]|\\\\|"' })
    Check 's-day-diff-relative' ($dh.Count -eq 3 -and $dabs.Count -eq 0) "run-day.diff next to run-day.ps1: header lines $($dh.Count), with an absolute or quoted path $($dabs.Count): $(if ($dh.Count) { $dh[0] })"

    # ---------- M: run-matrix.ps1's screensaver block, under StrictMode 2, on the scratch key ----------
    $mx = @{ new = Get-MatrixBlock $Files.matrix; old = Get-MatrixBlock $Old.matrix }
    $gp = @{ new = Get-FuncText $Files.matrix @('Get-P'); old = Get-FuncText $Old.matrix @('Get-P') }
    $mcases = [ordered]@{
        'm-missing'      = @{ v = [ordered]@{ ScreenSaveActive = '0'; ScreenSaveTimeOut = '120' }; want = '^screensaver none$' }
        'm-empty'        = @{ v = [ordered]@{ ScreenSaveActive = '0'; 'SCRNSAVE.EXE' = '' }; want = '^screensaver none$' }
        'm-active'       = @{ v = [ordered]@{ ScreenSaveActive = '1'; 'SCRNSAVE.EXE' = $Scr; ScreenSaveTimeOut = '300'; ScreenSaverIsSecure = '1' }; want = '^screensaver Mystify\.scr after 300 s, LOCKS on resume: ' }
        'm-active-bare'  = @{ v = [ordered]@{ ScreenSaveActive = '1'; 'SCRNSAVE.EXE' = $Scr }; want = '^screensaver Mystify\.scr after \? s: ' }
        'm-off'          = @{ v = [ordered]@{ ScreenSaveActive = '0'; 'SCRNSAVE.EXE' = $Scr }; want = '^screensaver none$' }
        'm-no-values'    = @{ v = [ordered]@{}; want = '^screensaver none$' }
        'm-no-key'       = @{ v = $null; want = '^screensaver none$' }
    }
    foreach ($id in $mcases.Keys) {
        Reset-Key $mcases[$id].v
        $r = Invoke-MBlock $mx.new $gp.new
        Check $id ($r.ok -and $r.lines.Count -eq 1 -and $r.lines[0] -match $mcases[$id].want) "new block: $(if ($r.ok) { $r.lines -join ' | ' } else { 'THREW ' + $r.err })"
    }
    foreach ($id in 'm-empty', 'm-active', 'm-off') {
        Reset-Key $mcases[$id].v
        $a = Invoke-MBlock $mx.old $gp.old; $b = Invoke-MBlock $mx.new $gp.new
        Check "$id-same" ($a.ok -and $b.ok -and (($a.lines -join '|') -ceq ($b.lines -join '|'))) "old and new blocks print the same line: $(if ($a.ok) { $a.lines -join ' | ' } else { 'old THREW ' + $a.err })"
    }
    Reset-Key $mcases['m-missing'].v
    $a = Invoke-MBlock $mx.old $gp.old
    Check 'm-old-missing-throws' ((-not $a.ok) -and $a.err -match 'cannot be found') "control, old block with SCRNSAVE.EXE missing: $(if ($a.ok) { 'did NOT throw: ' + ($a.lines -join ' | ') } else { 'threw: ' + $a.err })"

    # ---------- N/D: the launchers' Save/Set/Restore functions on the scratch key, fake SystemParametersInfo ----------
    $lcases = [ordered]@{
        'missing' = @{ v = [ordered]@{ ScreenSaveActive = '0'; ScreenSaveTimeOut = '120' }; set = "present '' String"; restore = 'absent'; spi = '17,0,3;17,0,3' }
        'empty'   = @{ v = [ordered]@{ ScreenSaveActive = '0'; 'SCRNSAVE.EXE' = '' }; set = "present '' String"; restore = "present '' String"; spi = '17,0,3;17,0,3' }
        'active'  = @{ v = [ordered]@{ ScreenSaveActive = '1'; 'SCRNSAVE.EXE' = $Scr; ScreenSaveTimeOut = '300'; ScreenSaverIsSecure = '1' }; set = "present '' String"; restore = "present '$Scr' String"; spi = '17,0,3;17,1,3' }
    }
    $fnames = @('Now', 'Ts', 'Add-Text', 'Set-Text', 'Get-P', 'Save-Screensaver', 'Set-ScreensaverNone', 'Restore-Screensaver')
    function Test-Launcher([string]$Label, [string]$Path, $Cases, [bool]$Control) {
        function Log([string]$Msg, [string]$Color = 'Gray') { $script:LogLines.Add("[$Color] $Msg") }
        . ([scriptblock]::Create((Get-FuncText $Path $fnames)))
        $DeskKey = $FakeDesk
        foreach ($id in $Cases.Keys) {
            $c = $Cases[$id]
            Reset-Key $c.v
            $StatusDir = Join-Path $CaseDir "$Label-$id"; New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
            $SsFile = Join-Path $StatusDir 'screensaver-saved.txt'
            $script:SsSaved = $null; [LdNight]::Calls.Clear(); $script:LogLines.Clear()
            $DryRun = $false
            Set-ScreensaverNone
            $s1 = Get-ExeState; $c1 = [LdNight]::Calls -join ';'
            $pn = Invoke-MBlock $mx.new $gp.new; $po = Invoke-MBlock $mx.old $gp.old
            Restore-Screensaver
            $s2 = Get-ExeState; $c2 = [LdNight]::Calls -join ';'
            $saved = [IO.File]::ReadAllText($SsFile)
            $warn = @($script:LogLines | Where-Object { $_ -match '!!!' -and $_ -notmatch 'a policy sets' })
            Set-Content -LiteralPath (Join-Path $StatusDir 'log.txt') -Value $script:LogLines -Encoding ASCII
            if ($Control) {
                Check "$Label-$id" ($s1 -eq 'absent' -and $c1 -eq '17,0,3' -and -not $po.ok -and $po.err -match 'cannot be found' -and $pn.ok -and $s2 -eq $c.restore) "control, old launcher: after Set-ScreensaverNone SCRNSAVE.EXE $s1 (the 23:47 removal); old run-matrix block $(if ($po.ok) { 'did NOT throw' } else { 'threw (the 00:03:40 refusal)' }); new block $(if ($pn.ok) { 'ok: ' + ($pn.lines -join ' | ') } else { 'THREW ' + $pn.err }); after restore $s2"
                continue
            }
            Check "$Label-$id-set" ($s1 -eq $c.set -and $c1 -eq '17,0,3' -and $saved -match "SCRNSAVE\.EXE present=$(if ($c.v.Contains('SCRNSAVE.EXE')) { 'True' } else { 'False' })") "after Set-ScreensaverNone: SCRNSAVE.EXE $s1; SPI calls $c1"
            Check "$Label-$id-plan" ($pn.ok -and $pn.lines.Count -eq 1 -and $pn.lines[0] -eq 'screensaver none' -and $po.ok) "while set: new run-matrix block $(if ($pn.ok) { $pn.lines -join ' | ' } else { 'THREW ' + $pn.err }); old block $(if ($po.ok) { 'ok too (the value is there)' } else { 'THREW ' + $po.err })"
            Check "$Label-$id-restore" ($s2 -eq $c.restore -and $c2 -eq $c.spi -and $saved -match '(?m)^restored ' -and $null -eq $script:SsSaved -and $warn.Count -eq 0) "after Restore-Screensaver: SCRNSAVE.EXE $s2 (want $($c.restore)); SPI calls $c2; 'restored' line $($saved -match '(?m)^restored '); warnings $($warn.Count)"
        }
        if ($Control) { return }
        # dry run: nothing is changed, the saved file gets a dry-run 'restored' line
        Reset-Key $Cases['missing'].v
        $StatusDir = Join-Path $CaseDir "$Label-dry"; New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
        $SsFile = Join-Path $StatusDir 'screensaver-saved.txt'
        $script:SsSaved = $null; [LdNight]::Calls.Clear(); $script:LogLines.Clear()
        $DryRun = $true
        Set-ScreensaverNone; $s1 = Get-ExeState
        Restore-Screensaver; $s2 = Get-ExeState
        $saved = [IO.File]::ReadAllText($SsFile)
        Check "$Label-dry" ($s1 -eq 'absent' -and $s2 -eq 'absent' -and [LdNight]::Calls.Count -eq 0 -and $saved -match '(?m)^restored .*dry run') "dry run: SCRNSAVE.EXE $s1 then $s2; SPI calls $([LdNight]::Calls.Count)"
    }
    Test-Launcher 'night' $Files.night $lcases $false
    Test-Launcher 'day' $Files.day $lcases $false
    Test-Launcher 'old-night' $Old.night ([ordered]@{ 'empty' = $lcases['empty'] }) $true

    # ---------- E: run-matrix.ps1 -PlanOnly end to end (the launcher's arguments), Desktop key redirected ----------
    if ($E2E) {
        function New-Sandbox([string]$Name, [string]$MatrixScript) {
            $sb = Join-Path $Repo "build\agent5\$Name"
            if (Test-Path -LiteralPath $sb) { Remove-Item -LiteralPath $sb -Recurse -Force }
            New-Item -ItemType Directory -Force -Path $sb | Out-Null
            $rd = Join-Path $Repo 'bench\agent8\run'
            Get-ChildItem -LiteralPath $rd -File | Where-Object { $_.Name -ne 'run-matrix.ps1' } | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $sb }
            Copy-Item -LiteralPath (Join-Path $rd 'drivers') -Destination (Join-Path $sb 'drivers') -Recurse
            Copy-Item -LiteralPath $MatrixScript -Destination (Join-Path $sb 'run-matrix.ps1')
            $sandboxes.Add($sb)
            return $sb
        }
        function Invoke-E2E([string]$Dir) {
            $o = @(& (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Here 'e2e-driver.ps1') -Target (Join-Path $Dir 'run-matrix.ps1') -Matrix (Join-Path $Dir 'matrix-window6.json') -Only 's0,p2,p2f,p2fc' -Repeats 5 -FakeDesk $FakeDesk 2>&1 | ForEach-Object { "$_" })
            return $o
        }
        if ($Set -eq 'new') { $dirs = [ordered]@{ old = New-Sandbox 'sfx-base' $Old.matrix; new = New-Sandbox 'sfx-new' $Files.matrix } }
        else { $dirs = [ordered]@{ old = New-Sandbox 'sfx-base' $Old.matrix; new = Join-Path $Repo 'bench\agent8\run' } }
        $ecases = [ordered]@{
            'e2e-old-missing' = @{ dir = 'old'; v = $lcases['missing'].v }
            'e2e-new-missing' = @{ dir = 'new'; v = $lcases['missing'].v }
            'e2e-new-empty'   = @{ dir = 'new'; v = $lcases['empty'].v }
            'e2e-new-active'  = @{ dir = 'new'; v = $lcases['active'].v }
        }
        foreach ($id in $ecases.Keys) {
            Reset-Key $ecases[$id].v
            $o = Invoke-E2E $dirs[$ecases[$id].dir]
            Set-Content -LiteralPath (Join-Path $CaseDir "$id.txt") -Value @($o | ForEach-Object { $_.Replace($Repo, '<repo>') }) -Encoding ASCII   # no user folder in the results
            $redir = @($o | Where-Object { $_ -match '^E2E-REDIRECTS=(\d+)$' } | ForEach-Object { [int]($_ -replace '^E2E-REDIRECTS=', '') })
            $hits = if ($redir.Count) { $redir[0] } else { 0 }
            $exit = @($o | Where-Object { $_ -match '^E2E-EXIT=' }) -join ''
            $threw = @($o | Where-Object { $_ -match '^E2E-THREW=' }) -join ''
            $scrLine = @($o | Where-Object { $_ -match '^screensaver ' }) -join ' | '
            $est = @($o | Where-Object { $_ -match '^estimate ' }) -join ' | '
            $what = "$($dirs[$ecases[$id].dir].Substring($Repo.Length + 1))\run-matrix.ps1: $(if ($threw) { $threw } else { $exit }); desktop-key reads redirected $hits; $scrLine; $est"
            switch ($id) {
                'e2e-old-missing' { Check $id ($hits -eq 1 -and $threw -match 'cannot be found') "control: $what" }
                'e2e-new-active'  { Check $id ($hits -eq 1 -and $exit -eq 'E2E-EXIT=0' -and $scrLine -match '^screensaver Mystify\.scr after 300 s, LOCKS on resume' -and ($o -contains 'PlanOnly: nothing started.')) $what }
                default           { Check $id ($hits -eq 1 -and $exit -eq 'E2E-EXIT=0' -and $scrLine -eq 'screensaver none' -and ($o -contains 'PlanOnly: nothing started.')) $what }
            }
        }
    }
} finally {
    if (Test-Path -LiteralPath $TestRoot) { Remove-Item -LiteralPath $TestRoot -Recurse -Force }
    foreach ($sb in $sandboxes) { if (Test-Path -LiteralPath $sb) { Remove-Item -LiteralPath $sb -Recurse -Force } }
}
$real1 = Get-RealState
Check 'real-untouched' ($real1 -eq $real0 -and -not (Test-Path -LiteralPath $TestRoot)) "real desktop key before: $real0; after: $real1; scratch key removed $(-not (Test-Path -LiteralPath $TestRoot)); sandboxes removed $(@($sandboxes | Where-Object { Test-Path -LiteralPath $_ }).Count -eq 0)"
$pass = $script:Results.Count - $script:Fails
$sum = Join-Path $Out "summary-$Set-$Stamp.txt"
Set-Content -LiteralPath $sum -Value (@($hdr) + $hashLines + @($script:Results) + @("$pass/$($script:Results.Count) PASS")) -Encoding ASCII
Write-Host "$pass/$($script:Results.Count) PASS (summary: $($sum.Substring($Repo.Length + 1)))"
if ($script:Fails) { exit 1 } else { exit 0 }
