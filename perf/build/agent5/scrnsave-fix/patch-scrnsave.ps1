# patch-scrnsave.ps1: Agent 5, task #26. Stages the SCRNSAVE.EXE/StrictMode fix, plus Agent 10's day-draft condition 1
# and NITs N1-N3 (build\agent10\t27\day-draft-rating.md). It copies the current files to base\ (after checking their
# sha256), applies literal replacements to make new\ (each old text must occur exactly once), regenerates run-day.ps1
# with the new make-run-day.ps1 into new\day\, and writes scrnsave-fix.diff and hashes.txt.
# It writes only under this folder; the installed files are only read. One-shot: it refuses once the sources change.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\scrnsave-fix\patch-scrnsave.ps1
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$BaseDir = Join-Path $Here 'base'; $NewDir = Join-Path $Here 'new'; $DayDir = Join-Path $NewDir 'day'
$Src = [ordered]@{
    'run-matrix.ps1'   = @('bench\agent8\run\run-matrix.ps1', 'FEDCEB13AB46FE790598EEFD97B5EF5FF545D5D24FADFB3BA03B1CE1CA0CBB89')
    'run-night.ps1'    = @('bench\agent5\launch\run-night.ps1', '16B90FA8654FAC088FE5A1248DE1754918AACC7667A2126AD14723BFBF939B31')
    'README.md'        = @('bench\agent5\launch\README.md', '0058C8F61EEAA9F2529145B034433E2FB67344012D114E4103CE8E3A0EB43274')
    'make-run-day.ps1' = @('build\agent5\day-draft\make-run-day.ps1', '17413F8A566E79BF0721BF77DA64BACEA629DBAB7D70887A6AA75CBAA2827780')
    'run-day.ps1'      = @('build\agent5\day-draft\run-day.ps1', 'D86F6DE04B3EDA47A4811CD7139B9BEE21B43E0E368AAB4287143F45B8C59E98')
    'run-day.diff'     = @('build\agent5\day-draft\run-day.diff', '54E35C180DBF4B164DB86CC5B61D71952F132C7149E69D909634DAE0B60EC12F')
    'README-DAY.md'    = @('build\agent5\day-draft\README-DAY.md', '9D131EB14B89DBBBB642D0C40AA0103FB7742BD95B1BA143E7F8E6A8CE308FCB')
    'RUN-DAY.cmd'      = @('build\agent5\day-draft\RUN-DAY.cmd', '4B5489B4C1021038C44D2C97A18B19E675AB278CCC43D5CD1B11B21F5039CAD9')
}
foreach ($d in $BaseDir, $NewDir, $DayDir) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
$Utf8 = New-Object Text.UTF8Encoding $false
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
foreach ($n in $Src.Keys) {
    $p = Join-Path $Repo $Src[$n][0]; $h = Sha $p
    if ($h -ne $Src[$n][1]) { throw "$($Src[$n][0]) has sha256 $h, not $($Src[$n][1]); refusing" }
    if ($n -eq 'run-day.diff') { continue }   # sha checked, not copied: the old one names absolute paths (Agent 10's N1)
    Copy-Item -LiteralPath $p -Destination (Join-Path $BaseDir $n) -Force
}
$stale = Join-Path $BaseDir 'run-day.diff'; if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale -Force }
function Read-T([string]$P) {
    $t = [IO.File]::ReadAllText($P, $Utf8)
    if ($t.Contains("`r")) { throw "$P has CR characters (expected LF only)" }
    return $t
}
function Edit-One([string]$T, [string]$Old, [string]$New, [string]$What) {
    $Old = $Old -replace "`r`n", "`n"; $New = $New -replace "`r`n", "`n"
    $c = 0; $i = 0
    while (($i = $T.IndexOf($Old, $i, [StringComparison]::Ordinal)) -ge 0) { $c++; $i += $Old.Length }
    if ($c -ne 1) { throw "${What}: expected exactly one [$Old], found $c" }
    Write-Host "changed: $What"
    return $T.Replace($Old, $New)
}
function Write-T([string]$P, [string]$T) {
    if ($T.Contains("`r")) { throw "$P would get CR characters" }
    [IO.File]::WriteAllText($P, $T, $Utf8)
}

# ---------- 1. run-matrix.ps1 (Agent 8's): the screensaver values through Get-P (PSObject.Properties) ----------
$t = Read-T (Join-Path $BaseDir 'run-matrix.ps1')
$o = @'
$scrExe = if ($scr) { [string]$scr.'SCRNSAVE.EXE' } else { '' }
'@
$n = @'
$scrExe = [string](Get-P $scr 'SCRNSAVE.EXE' '')   # via PSObject.Properties: a missing value is '' (a plain read throws under StrictMode: W6 GO refused 00:03:40)
'@
$t = Edit-One $t $o $n 'run-matrix L417: SCRNSAVE.EXE through Get-P'
$o = @'
if ($scr -and [string]$scr.ScreenSaveActive -eq '1' -and $scrExe) {
'@
$n = @'
if ([string](Get-P $scr 'ScreenSaveActive' '') -eq '1' -and $scrExe) {
'@
$t = Edit-One $t $o $n 'run-matrix L418: ScreenSaveActive through Get-P'
$o = @'
after $($scr.ScreenSaveTimeOut) s$(if ([string]$scr.ScreenSaverIsSecure -eq '1') { ', LOCKS on resume' })
'@
$n = @'
after $(Get-P $scr 'ScreenSaveTimeOut' '?') s$(if ([string](Get-P $scr 'ScreenSaverIsSecure' '') -eq '1') { ', LOCKS on resume' })
'@
$t = Edit-One $t $o $n 'run-matrix L419: ScreenSaveTimeOut and ScreenSaverIsSecure through Get-P'
Write-T (Join-Path $NewDir 'run-matrix.ps1') $t

# ---------- 2. run-night.ps1: set SCRNSAVE.EXE to '' (never remove it); restore puts back 'missing' too ----------
$t = Read-T (Join-Path $BaseDir 'run-night.ps1')
$o = @'
    if ($script:SsSaved.has_exe) { Remove-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' -ErrorAction SilentlyContinue }
'@
$n = @'
    try { Set-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' -Value '' -Type String } catch { Log "!!! could not set SCRNSAVE.EXE to '': $($_.Exception.Message)" 'Yellow' }   # '' is (None); never removed: run-matrix.ps1 L417 threw on a missing value (GO refused 00:03:40)
'@
$t = Edit-One $t $o $n 'Set-ScreensaverNone: SCRNSAVE.EXE set to empty instead of removed'
$o = @'
SCRNSAVE.EXE $(if ($k.PSObject.Properties['SCRNSAVE.EXE']) { 'present' } else { 'absent' }))"
'@
$n = @'
SCRNSAVE.EXE $(if ($k.PSObject.Properties['SCRNSAVE.EXE']) { "'$($k.'SCRNSAVE.EXE')'" } else { 'absent' }))"
'@
$t = Edit-One $t $o $n 'Set-ScreensaverNone: the log line shows the value'
$o = @'
        if ($script:SsSaved.has_exe) { Set-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' -Value $script:SsSaved.exe }
'@
$n = @'
        if ($script:SsSaved.has_exe) { Set-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' -Value $script:SsSaved.exe }
        elseif ($null -ne (Get-ItemProperty -LiteralPath $DeskKey).PSObject.Properties['SCRNSAVE.EXE']) { Remove-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' }   # it was missing at the start: missing again
'@
$t = Edit-One $t $o $n 'Restore-Screensaver: a value that was missing at the start is removed again'
Write-T (Join-Path $NewDir 'run-night.ps1') $t
$NightSha = Sha (Join-Path $NewDir 'run-night.ps1'); $N8 = $NightSha.Substring(0, 8)

# ---------- 3. README.md (night): the screensaver row and the hand-restore note ----------
$t = Read-T (Join-Path $BaseDir 'README.md')
$o = @'
| Screensaver | sets it to "(None)" when it starts | yes. It was already "(None)" when I checked at 19:37 |
'@
$n = @'
| Screensaver | sets it to "(None)" when it starts: screensaver off, SCRNSAVE.EXE set to empty. (Before 23 Nov it deleted SCRNSAVE.EXE, and that made the runner refuse a window.) | yes, exactly as it was, also when SCRNSAVE.EXE was missing. It was already "(None)" when I checked at 19:37 |
'@
$t = Edit-One $t $o $n 'README: screensaver row'
$o = @'
     - "ScreenSaveActive=0" plus an empty SCRNSAVE.EXE means "(None)". In that case there is nothing to do.
'@
$n = @'
     - "ScreenSaveActive=0" plus an empty or missing SCRNSAVE.EXE (`present=False`) means "(None)". In that case there is nothing to do.
'@
$t = Edit-One $t $o $n 'README: hand restore'
Write-T (Join-Path $NewDir 'README.md') $t

# ---------- 4. make-run-day.ps1: the new night sha (condition 1), repo-relative paths in run-day.diff (N1) ----------
$t = Read-T (Join-Path $BaseDir 'make-run-day.ps1')
$t = Edit-One $t '# sha256 16B90FA8... (the reviewed night launcher).' "# sha256 $N8... (the reviewed night launcher 16B90FA8 plus the SCRNSAVE.EXE fix, build\agent5\scrnsave-fix)." 'make-run-day: header comment'
$t = Edit-One $t "`$Want = '16B90FA8654FAC088FE5A1248DE1754918AACC7667A2126AD14723BFBF939B31'" "`$Want = '$NightSha'" 'make-run-day: source sha'
$t = Edit-One $t 'made from run-night.ps1 (sha 16B90FA8) by make-run-day.ps1' "made from run-night.ps1 (sha $N8) by make-run-day.ps1" 'make-run-day: run-day.ps1 header'
$o = @'
$d = @(& git -c core.autocrlf=false diff --no-index --no-color -- $Source $Out | ForEach-Object { [string]$_ })
'@
$n = @'
# Paths relative to $Repo, so the diff names no user folder (Agent 10's N1); a path outside $Repo stays as it is.
$rel = @(foreach ($p in $Source, $Out) { $f = (Resolve-Path -LiteralPath $p).Path; if ($f.StartsWith($Repo + '\', [StringComparison]::OrdinalIgnoreCase)) { $f.Substring($Repo.Length + 1).Replace('\', '/') } else { $f } })
Push-Location -LiteralPath $Repo
try { $d = @(& git -c core.autocrlf=false diff --no-index --no-color -- $rel[0] $rel[1] | ForEach-Object { [string]$_ }) } finally { Pop-Location }
'@
$t = Edit-One $t $o $n 'make-run-day: run-day.diff with repo-relative paths (N1)'
Write-T (Join-Path $NewDir 'make-run-day.ps1') $t
Copy-Item -LiteralPath (Join-Path $NewDir 'make-run-day.ps1') -Destination (Join-Path $DayDir 'make-run-day.ps1') -Force
foreach ($f in 'run-day.ps1', 'run-day.diff') { $p = Join-Path $DayDir $f; if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force } }
& (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -File (Join-Path $DayDir 'make-run-day.ps1') -Source (Join-Path $NewDir 'run-night.ps1')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $DayDir 'run-day.ps1'))) { throw "make-run-day.ps1 failed (exit $LASTEXITCODE)" }
$hdrs = @([IO.File]::ReadAllLines((Join-Path $DayDir 'run-day.diff')) | Where-Object { $_ -match '^(diff --git |--- |\+\+\+ )' })
$abs = @($hdrs | Where-Object { $_ -match '[A-Za-z]:[\\/]|\\\\|"' })
if ($hdrs.Count -ne 3 -or $abs.Count) { throw "new\day\run-day.diff: $($hdrs.Count) header lines, $($abs.Count) with an absolute or quoted path" }
Write-Host "run-day.diff header paths are relative: $($hdrs[0])"

# ---------- 5. README-DAY.md: the new source sha, N2 (L57) and a note ----------
$t = Read-T (Join-Path $BaseDir 'README-DAY.md')
$t = Edit-One $t '| run-day.ps1 | made from run-night.ps1 16B90FA8 by make-run-day.ps1;' "| run-day.ps1 | made from run-night.ps1 $N8 (16B90FA8 plus the SCRNSAVE.EXE fix) by make-run-day.ps1;" 'README-DAY: run-day.ps1 row'
$t = Edit-One $t 'It refuses unless the source sha is 16B90FA8 and' "It refuses unless the source sha is $N8 and" 'README-DAY: make-run-day.ps1 row'
$t = Edit-One $t 'and writes run-day.diff |' 'and writes run-day.diff (paths relative to the repo) |' 'README-DAY: make-run-day.ps1 row, N1'
$o = 'STOP-LAUNCHER works from any folder; it always asks first.'
$n = "STOP-LAUNCHER always asks first. Use the installed copy in ``bench\agent5\day\``: a copy in another folder can't read a day launcher's state (it looks in ``<own folder>\status\``), so it says the state is unknown and asks."
$t = Edit-One $t $o $n 'README-DAY: L57, use the installed STOP-LAUNCHER (N2)'
$o = "Agents 10 and 11 review next.`n"
$n = "Agents 10 and 11 review next.`n`n**SCRNSAVE.EXE fix (task #26, 23 Nov):** at 00:03:40 the night launcher refused the W6 GO: its Set-ScreensaverNone had deleted SCRNSAVE.EXE, and run-matrix.ps1 -PlanOnly then threw under StrictMode. run-day.ps1 is now made from run-night.ps1 $N8, which sets SCRNSAVE.EXE to '' instead of deleting it and, at the end, puts back the saved state, also 'missing'. run-matrix.ps1 reads the value through PSObject.Properties. This is condition 1 of Agent 10's rating (SAFE-IF, ``build\agent10\t27\day-draft-rating.md``). Also from that rating: run-day.diff has repo-relative paths (N1), the STOP-LAUNCHER line above (N2) and RUN-DAY.cmd's exit-2 line (N3). Diff and tests: ``build\agent5\scrnsave-fix\``.`n"
$t = Edit-One $t $o $n 'README-DAY: SCRNSAVE.EXE note'
Write-T (Join-Path $NewDir 'README-DAY.md') $t

# ---------- 6. RUN-DAY.cmd (CRLF): the exit-2 line (N3) ----------
$p = Join-Path $BaseDir 'RUN-DAY.cmd'
$t = [IO.File]::ReadAllText($p, $Utf8)
$cnt = { param($s) @(([regex]::Matches($s, "`r")).Count, ([regex]::Matches($s, "`n")).Count, ([regex]::Matches($s, "`r`n")).Count) -join ',' }
$before = & $cnt $t
$o = 'if "%RC%"=="2" echo The day launcher did not start: the reason is in red above. Nothing was changed.'
$n = 'if "%RC%"=="2" echo The day launcher did not start: the reason is in red above. It changed nothing; a night launcher that RUN-DAY stopped above stays stopped.'
$c = 0; $i = 0; while (($i = $t.IndexOf($o, $i, [StringComparison]::Ordinal)) -ge 0) { $c++; $i += $o.Length }
if ($c -ne 1) { throw "RUN-DAY.cmd: expected exactly one [$o], found $c" }
$t = $t.Replace($o, $n); Write-Host 'changed: RUN-DAY.cmd L25, exit-2 message (N3)'
if ((& $cnt $t) -ne $before) { throw 'RUN-DAY.cmd: the line endings changed' }
foreach ($ch in $t.ToCharArray()) { if ([int]$ch -gt 126) { throw 'RUN-DAY.cmd: non-ASCII character' } }
[IO.File]::WriteAllText((Join-Path $NewDir 'RUN-DAY.cmd'), $t, $Utf8)

# ---------- 7. the diff and the hashes ----------
$pairs = @(@('base/run-matrix.ps1', 'new/run-matrix.ps1'), @('base/run-night.ps1', 'new/run-night.ps1'), @('base/README.md', 'new/README.md'),
           @('base/make-run-day.ps1', 'new/make-run-day.ps1'), @('base/run-day.ps1', 'new/day/run-day.ps1'),
           @('base/README-DAY.md', 'new/README-DAY.md'), @('base/RUN-DAY.cmd', 'new/RUN-DAY.cmd'))
# run-day.diff is left out on purpose: the old one names absolute paths (N1). new\day\run-day.diff is the regenerated one.
Push-Location $Here
$ErrorActionPreference = 'Continue'
$all = New-Object System.Collections.Generic.List[string]
foreach ($p in $pairs) { foreach ($l in @(& git -c core.autocrlf=false diff --no-index --no-color -- $p[0] $p[1])) { $all.Add([string]$l) } }
$ErrorActionPreference = 'Stop'
Pop-Location
Write-T (Join-Path $Here 'scrnsave-fix.diff') (($all -join "`n") + "`n")
$hl = New-Object System.Collections.Generic.List[string]
$hl.Add("hashes written $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') by patch-scrnsave.ps1 (sha256, path relative to build\agent5\scrnsave-fix)")
foreach ($f in @(Get-ChildItem -LiteralPath $BaseDir -File) + @(Get-ChildItem -LiteralPath $NewDir -File) + @(Get-ChildItem -LiteralPath $DayDir -File)) {
    $hl.Add("$(Sha $f.FullName)  $($f.FullName.Substring($Here.Length + 1))")
}
$hl.Add("$(Sha (Join-Path $Here 'scrnsave-fix.diff'))  scrnsave-fix.diff")
Write-T (Join-Path $Here 'hashes.txt') (($hl -join "`n") + "`n")
$hl | ForEach-Object { Write-Host $_ }
Write-Host "diff: $($all.Count) lines"
