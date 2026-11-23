# test-day.ps1: Agent 5's tests of the day draft (run-day.ps1, launcher-ctl.ps1, RUN-DAY.cmd, STOP-LAUNCHER.cmd).
# Launchers run only as run-day.ps1 -DryRun (files in status-dryrun\<tag>\ next to it; fake runner, no game, no bench\agent8
# runner). The real-mode tests only check refusals: run-day.ps1 refuses on this hidden desktop before it changes anything,
# and RUN-DAY.cmd / STOP-LAUNCHER.cmd get an empty stdin, so they start nothing and write nothing. The REAL cases are
# skipped while a real launcher runs or when this is the user's own desktop (WinSta0\Default).
# Nothing is written under bench\agent5\launch or perf-notes\ (checked before/after).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File test-day.ps1 [-Only d-return,d-window] [-Name a]
param([string[]]$Only = @(), [string]$Name = 'all')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
if ($Only.Count -eq 1 -and $Only[0].Contains(',')) { $Only = $Only[0] -split ',' }
$D = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $D '..\..\..')).Path
$LT = Join-Path $Repo 'build\agent5\launch-test'
$Res = Join-Path $D 'results'; New-Item -ItemType Directory -Force -Path $Res | Out-Null
$Ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$Day = Join-Path $D 'run-day.ps1'; $Ctl = Join-Path $D 'launcher-ctl.ps1'
$Inv = [Globalization.CultureInfo]::InvariantCulture
$Empty = Join-Path $Res 'empty-stdin.txt'; [IO.File]::WriteAllText($Empty, '')
$script:Results = New-Object System.Collections.Generic.List[string]

function Want([string]$N) { return (-not $Only.Count -or $Only -contains $N) }
function Check([string]$T, [bool]$Ok, [string]$What) {
    $l = "$(if ($Ok) { 'PASS' } else { 'FAIL' })  $T  $What"; $script:Results.Add($l); Write-Host $l -ForegroundColor $(if ($Ok) { 'Green' } else { 'Red' })
}
function Hold-Check { if (Test-Path (Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt')) { throw 'perf-notes\WINDOW-HOLD.txt exists (a timed window): tests stopped' } }
function Snap {
    $a = @(foreach ($n in 'WINDOW-GO.txt', 'WINDOW-HOLD.txt', 'WINDOW-STOP.txt') { "$n=$(Test-Path (Join-Path $Repo "perf-notes\$n"))" })
    $a += 'launch=' + ((@(Get-ChildItem (Join-Path $Repo 'bench\agent5\launch') -Recurse -File -Force | ForEach-Object { "$($_.FullName):$($_.Length):$($_.LastWriteTimeUtc.Ticks)" })) -join ';').GetHashCode()
    return ($a -join ' | ')
}
function Real-Alive { $m = $null; if ([System.Threading.Mutex]::TryOpenExisting('Local\Agent5RunNight-real', [ref]$m)) { $m.Dispose(); return $true }; return $false }
Add-Type -TypeDefinition ('using System; using System.Runtime.InteropServices; using System.Text; public static class A5DayDesk { ' +
    '[DllImport("user32.dll")] static extern IntPtr GetProcessWindowStation(); ' +
    '[DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint threadId); ' +
    '[DllImport("kernel32.dll")] static extern uint GetCurrentThreadId(); ' +
    '[DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern bool GetUserObjectInformationW(IntPtr hObj, int nIndex, StringBuilder pvInfo, int nLength, out int lpnLengthNeeded); ' +
    'static string Name(IntPtr h) { var sb = new StringBuilder(256); int need; return GetUserObjectInformationW(h, 2, sb, sb.Capacity * 2, out need) ? sb.ToString() : null; } ' +
    'public static string Desktop() { return Name(GetProcessWindowStation()) + "\\" + Name(GetThreadDesktop(GetCurrentThreadId())); } }')
# The REAL cases rely on "refused on this hidden desktop": skip them on the user's own desktop (or if the check fails).
function User-Desk { try { return ([A5DayDesk]::Desktop() -ieq 'WinSta0\Default') } catch { return $true } }
$UserDesk = User-Desk
function HM([double]$Min) { return (Get-Date).AddMinutes($Min).ToString('HH:mm', $Inv) }
function Next([string]$Hm) { $n = Get-Date; $t = $n.Date.Add([datetime]::ParseExact($Hm, 'HH:mm', $Inv).TimeOfDay); if ($t -le $n) { $t = $t.AddDays(1) }; return $t }
function EndFor([string]$Hm) { return (Next $Hm).AddMinutes(-15).ToString('yyyy-MM-dd HH:mm', $Inv) }
function OutIs([string]$F, [string]$W) { return ((Test-Path $F) -and (([IO.File]::ReadAllText($F)).Trim() -eq $W)) }
function Start-Ps([string]$N, [string]$File, [string]$ArgLine) {
    $o = Join-Path $Res "$N-out.txt"; $e = Join-Path $Res "$N-err.txt"
    $p = Start-Process -FilePath $File -ArgumentList $ArgLine -PassThru -WindowStyle Hidden -RedirectStandardOutput $o -RedirectStandardError $e -RedirectStandardInput $Empty
    $null = $p.Handle
    return $p
}
function Finish($P, [string]$N, [int]$Sec) {
    $done = $P.WaitForExit($Sec * 1000)
    if (-not $done) { try { $P.Kill() } catch { }; [void]$P.WaitForExit(5000) }
    $txt = ''
    foreach ($f in @("$N-out.txt", "$N-err.txt")) { $pp = Join-Path $Res $f; if (Test-Path $pp) { $t = [IO.File]::ReadAllText($pp); if ($t) { $txt += $t } } }
    $code = 'TIMEOUT'; if ($done) { $code = "$($P.ExitCode)" }
    return @{ code = $code; text = $txt }
}
function Ctl([string]$N, [string]$ArgLine, [int]$Sec = 240) { return (Finish (Start-Ps $N $Ps "-NoProfile -ExecutionPolicy Bypass -File `"$Ctl`" $ArgLine") $N $Sec) }
function SD([string]$Tag) { return (Join-Path $D "status-dryrun\$Tag") }
function Start-Day([string]$Tag, [string]$More) {
    $sd = SD $Tag; if (Test-Path $sd) { Remove-Item -Recurse -Force $sd }
    return (Start-Ps "$Tag-launcher" $Ps "-NoProfile -ExecutionPolicy Bypass -File `"$Day`" -DryRun -DryRunTag $Tag -SkipStartChecks -PollSeconds 1 $More")
}
function Log-Text([string]$Tag) { $f = Join-Path (SD $Tag) 'log.txt'; try { if (Test-Path $f) { return [IO.File]::ReadAllText($f) } } catch { }; return '' }
function Wait-Log([string]$Tag, [string]$Rx, [int]$Sec) {
    $t0 = Get-Date; while (((Get-Date) - $t0).TotalSeconds -lt $Sec) { if ((Log-Text $Tag) -match $Rx) { return $true }; Start-Sleep -Milliseconds 500 }; return $false
}
function Wait-State([string]$Tag, [string]$S, [int]$Sec) {
    $f = Join-Path (SD $Tag) 'state.txt'; $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $Sec) { try { if ((Test-Path $f) -and ([IO.File]::ReadAllText($f) -match "(?m)^state\s+$S ")) { return $true } } catch { }; Start-Sleep -Milliseconds 500 }
    return $false
}
function Kill-Left($P) { if ($P -and -not $P.HasExited) { try { $P.Kill() } catch { } } }
function Copy-Real-Status([string]$To) {
    $st = Join-Path $D 'status'
    if (Test-Path $st) { $dst = Join-Path $Res $To; if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }; Copy-Item -Recurse $st $dst; Remove-Item -Recurse -Force $st }
}

$TestStart = Get-Date
$before = Snap
$shaGood = (Get-FileHash (Join-Path $LT 't-good.json') -Algorithm SHA256).Hash
$GoGood = "GO T1 t-good.json $shaGood only=base,s0 repeats=1"
$Hm3 = HM 180
Write-Host "test-day $Name at $(Get-Date -Format 'HH:mm:ss'); run-day.ps1 $((Get-FileHash $Day).Hash.Substring(0, 8)); launcher-ctl.ps1 $((Get-FileHash $Ctl).Hash.Substring(0, 8)); return time for most tests $Hm3 (end $(EndFor $Hm3)); user desktop: $UserDesk"

# ---------- launcher-ctl day mode, no launcher: the return-time rules ----------
if (Want 'd-return') {
    Hold-Check
    $o = Join-Path $Res 'd-return.out'; Remove-Item $o -ErrorAction SilentlyContinue
    $r = Ctl 'd-return-1' "-Mode day -DryRunTag d-return -OutFile `"$o`" -ReturnTime `"25:00,$(HM 30),$(HM 900)`""
    Check 'd-return-1' ($r.code -eq '1' -and $r.text -match "'25:00' is not a time" -and $r.text -match 'only \d+ min from now: a day session needs at least 90 min' -and $r.text -match 'h from now: it must be less than 14 h away' -and $r.text -match 'No usable time after 3 tries' -and -not (Test-Path $o)) "25:00, now+30 min and now+15 h refused, nothing started (exit $($r.code))"
    $r = Ctl 'd-return-2' "-Mode day -DryRunTag d-return -OutFile `"$o`" -ReturnTime $Hm3 -Answer N"
    Check 'd-return-2' ($r.code -eq '1' -and $r.text -match 'Start the day session\? \(Y/N\): N' -and $r.text -match 'Nothing was changed' -and -not (Test-Path $o)) "now+3 h, answer N: nothing started (exit $($r.code))"
    $h100 = HM 100
    $r = Ctl 'd-return-3' "-Mode day -DryRunTag d-return -OutFile `"$o`" -ReturnTime `"$(HM 80),$h100`" -Answer Y"
    Check 'd-return-3' ($r.code -eq '0' -and $r.text -match 'at least 90 min' -and (OutIs $o (EndFor $h100))) "now+80 min refused, then now+100 min ($h100) accepted: end $(EndFor $h100) (exit $($r.code))"
    Remove-Item $o -ErrorAction SilentlyContinue
    $r = Ctl 'd-return-4' "-Mode day -DryRunTag d-return -OutFile `"$o`" -ReturnTime $Hm3 -Answer Y"
    Check 'd-return-4' ($r.code -eq '0' -and $r.text -match 'the day session ends:' -and $r.text -match '(?m)^Power: ' -and (OutIs $o (EndFor $Hm3))) "now+3 h ($Hm3), answer Y: -StopAt = return - 15 min = $(EndFor $Hm3); power check shown (exit $($r.code))"
    Remove-Item $o -ErrorAction SilentlyContinue
    $r = Ctl 'd-return-5' "-Mode day -OutFile `"$o`" -Answer Y"
    Check 'd-return-5' ($r.code -eq '1' -and $r.text -match 'only work together with -DryRunTag' -and -not (Test-Path $o)) "test hooks without -DryRunTag are refused (exit $($r.code))"
}

# ---------- an old STOP file and no launcher ----------
if (Want 'd-stale') {
    Hold-Check
    $sd = SD 'd-stale'; New-Item -ItemType Directory -Force -Path $sd | Out-Null; $sf = Join-Path $sd 'WINDOW-STOP.txt'
    [IO.File]::WriteAllText($sf, "STOP old test file`r`n")
    $o = Join-Path $Res 'd-stale.out'; Remove-Item $o -ErrorAction SilentlyContinue
    $r = Ctl 'd-stale-1' "-Mode day -DryRunTag d-stale -OutFile `"$o`" -Answer N"
    Check 'd-stale-1' ($r.code -eq '1' -and $r.text -match 'An old STOP file is there' -and (Test-Path $sf) -and -not (Test-Path $o)) "old STOP file, answer N: kept, nothing started (exit $($r.code))"
    $r = Ctl 'd-stale-2' "-Mode day -DryRunTag d-stale -OutFile `"$o`" -ReturnTime $Hm3 -Answer YY"
    Check 'd-stale-2' ($r.code -eq '0' -and -not (Test-Path $sf) -and (OutIs $o (EndFor $Hm3))) "old STOP file, answer Y: deleted, then the day session (exit $($r.code))"
    Remove-Item $o -ErrorAction SilentlyContinue
}

# ---------- stop mode with no launcher ----------
if (Want 'd-none') {
    Hold-Check
    $r = Ctl 'd-none' '-Mode stop -DryRunTag d-none'
    Check 'd-none' ($r.code -eq '0' -and $r.text -match 'No launcher is running: nothing to stop' -and -not (Test-Path (Join-Path (SD 'd-none') 'WINDOW-STOP.txt'))) "no launcher: 'nothing to stop', no STOP file written (exit $($r.code))"
}

# ---------- a launcher whose state is unknown (its mutex is held, no state.txt): both modes ask ----------
if (Want 'd-unknown') {
    Hold-Check
    $sd = SD 'd-unknown'; if (Test-Path $sd) { Remove-Item -Recurse -Force $sd }
    $mx = 'Local\Agent5RunNight-dry-d-unknown'
    $hold = Start-Ps 'd-unknown-holder' $Ps "-NoProfile -Command `"`$m = New-Object System.Threading.Mutex(`$true, '$mx'); Start-Sleep -Seconds 120`""
    try {
        $t0 = Get-Date; $up = $false
        while (-not $up -and ((Get-Date) - $t0).TotalSeconds -lt 20) { $m = $null; if ([System.Threading.Mutex]::TryOpenExisting($mx, [ref]$m)) { $m.Dispose(); $up = $true } else { Start-Sleep -Milliseconds 200 } }
        $o = Join-Path $Res 'd-unknown.out'; Remove-Item $o -ErrorAction SilentlyContinue
        $sf = Join-Path $sd 'WINDOW-STOP.txt'
        $r = Ctl 'd-unknown-1' "-Mode day -DryRunTag d-unknown -OutFile `"$o`" -ReturnTime $Hm3 -Answer YN"
        Check 'd-unknown-1' ($up -and $r.code -eq '1' -and $r.text -match 'Its state is unknown' -and $r.text -match 'Stop the launcher anyway\? \(Y/N\): N' -and $r.text -match 'Nothing was changed' -and -not (Test-Path $sf) -and -not (Test-Path $o)) "RUN-DAY with a launcher in an unknown state asks first; N: no STOP, nothing started (exit $($r.code))"
        $r = Ctl 'd-unknown-2' "-Mode stop -DryRunTag d-unknown -Reason x -Answer N"
        Check 'd-unknown-2' ($up -and $r.code -eq '1' -and $r.text -match 'Its state is unknown: a window may be running' -and $r.text -notmatch 'No window is running now' -and $r.text -match 'Stop the launcher anyway\? \(Y/N\): N' -and -not (Test-Path $sf)) "STOP-LAUNCHER with an unknown state does not say 'nothing is lost' and asks; N: nothing written (exit $($r.code))"
    } finally { Kill-Left $hold }
}

# ---------- real mode, refusals only (no real launcher may be running) ----------
if (Want 'd-real') {
    Hold-Check
    if ((Real-Alive) -or $UserDesk) { Check 'd-real' $false "SKIPPED: a real launcher holds Local\Agent5RunNight-real, or this is the user's desktop ($UserDesk)" }
    else {
        Copy-Real-Status 'd-real-old-status'
        $r = Finish (Start-Ps 'd-real-1' $Ps "-NoProfile -ExecutionPolicy Bypass -File `"$Day`"") 'd-real-1' 60
        Check 'd-real-1' ($r.code -eq '2' -and $r.text -match 'refused: run-day.ps1 needs -StopAt' -and -not (Test-Path (Join-Path $D 'status'))) "run-day.ps1 without -StopAt: refused, exit $($r.code)"
        $r = Finish (Start-Ps 'd-real-2' $Ps "-NoProfile -ExecutionPolicy Bypass -File `"$Day`" -StopAt 7pm") 'd-real-2' 60
        Check 'd-real-2' ($r.code -eq '2' -and $r.text -match 'refused: run-day.ps1 needs -StopAt') "run-day.ps1 -StopAt 7pm: refused, exit $($r.code)"
        $dl = (Next $Hm3).ToString('yyyy-MM-dd HH:mm:ss', $Inv)
        $r = Finish (Start-Ps 'd-real-3' $Ps "-NoProfile -ExecutionPolicy Bypass -File `"$Day`" -StopAt $Hm3") 'd-real-3' 120
        $lg = ''; $lf = Join-Path $D 'status\log.txt'; if (Test-Path $lf) { $lg = [IO.File]::ReadAllText($lf) }
        Check 'd-real-3' ($r.code -eq '2' -and $lg -match 'launcher start: REAL' -and $lg -match [regex]::Escape("ends at $dl; latest window start $dl; a window still running at $dl is stopped") -and $lg -match "START REFUSED: this is desktop '[^']*', not the user's own desktop" -and $lg -notmatch 'dry-run hooks') "REAL run-day.ps1 -StopAt $Hm3 accepted as the end time (ends at $dl, latest start $dl) and refused on this desktop, exit $($r.code)"
        Copy-Real-Status 'd-real-3-status'
        $night = Join-Path $Repo 'bench\agent5\launch\run-night.ps1'
        # The night launcher's status\ exists once it has run for real (since 22 Nov 23:47), so compare it before/after.
        $ns = Join-Path $Repo 'bench\agent5\launch\status'
        $nsFp = { if (Test-Path $ns) { (@(Get-ChildItem $ns -Recurse -File -Force | ForEach-Object { "$($_.FullName):$($_.Length):$($_.LastWriteTimeUtc.Ticks)" })) -join ';' } else { '<none>' } }
        $ns0 = & $nsFp
        $r = Finish (Start-Ps 'd-real-4' $Ps "-NoProfile -ExecutionPolicy Bypass -File `"$night`" -StopAt $Hm3") 'd-real-4' 60
        Check 'd-real-4' ($r.code -eq '2' -and $r.text -match 'refused: -StopAt only work together with -DryRun' -and ((& $nsFp) -eq $ns0)) "REAL run-night.ps1 -StopAt is still refused as a test hook and bench\agent5\launch\status is unchanged, exit $($r.code)"
    }
}

# ---------- RUN-DAY.cmd plumbing: a copy with test answers; run-day.ps1 then refuses on this desktop ----------
if (Want 'd-cmd') {
    Hold-Check
    if ((Real-Alive) -or $UserDesk) { Check 'd-cmd' $false "SKIPPED: a real launcher is running, or this is the user's desktop ($UserDesk)" }
    else {
        Copy-Real-Status 'd-cmd-old-status'
        $src = [IO.File]::ReadAllText((Join-Path $D 'RUN-DAY.cmd'))
        $a = '"%~dp0launcher-ctl.ps1" -Mode day -OutFile "%DAYF%"'
        if (-not $src.Contains($a)) { throw 'RUN-DAY.cmd: the launcher-ctl line was not found' }
        $t = $src.Replace($a, "`"$D\launcher-ctl.ps1`" -Mode day -OutFile `"%DAYF%`" -DryRunTag d-cmd -ReturnTime $Hm3 -Answer Y").Replace('%~dp0', "$D\")
        $tc = Join-Path $Res 'RUN-DAY-test.cmd'; [IO.File]::WriteAllText($tc, $t, (New-Object Text.ASCIIEncoding))
        $r = Finish (Start-Ps 'd-cmd' "$env:SystemRoot\System32\cmd.exe" "/c `"$tc`"") 'd-cmd' 120
        $lg = ''; $lf = Join-Path $D 'status\log.txt'; if (Test-Path $lf) { $lg = [IO.File]::ReadAllText($lf) }
        $e = EndFor $Hm3
        Check 'd-cmd' ($r.code -eq '2' -and $r.text -match [regex]::Escape("Starting the day launcher. It ends at $e.") -and $r.text -match 'The day launcher did not start' -and $lg -match [regex]::Escape("ends at $($e):00; latest window start $($e):00") -and $lg -match 'START REFUSED') "RUN-DAY.cmd passes return - 15 min ($e) to run-day.ps1 -StopAt; it refuses on this desktop; exit $($r.code)"
        Copy-Real-Status 'd-cmd-status'
    }
}

# ---------- the real RUN-DAY.cmd and STOP-LAUNCHER.cmd with an empty stdin: nothing started, nothing written ----------
if (Want 'd-cmd-nul') {
    Hold-Check
    if (Real-Alive) { Check 'd-cmd-nul' $false 'SKIPPED: a real launcher is running' }
    else {
        $r = Finish (Start-Ps 'd-cmd-nul' "$env:SystemRoot\System32\cmd.exe" "/c `"$D\RUN-DAY.cmd`"") 'd-cmd-nul' 90
        Check 'd-cmd-nul' ($r.code -eq '1' -and $r.text -match 'runs only from bench\\agent5\\day' -and $r.text -match 'Nothing was started' -and -not (Test-Path (Join-Path $D 'status')) -and -not (Test-Path (Join-Path $Repo 'perf-notes\WINDOW-STOP.txt'))) "the real RUN-DAY.cmd in day-draft refuses (it runs only from bench\agent5\day\): nothing started, nothing written (exit $($r.code))"
        $r = Finish (Start-Ps 'd-stopcmd-none' "$env:SystemRoot\System32\cmd.exe" "/c `"$D\STOP-LAUNCHER.cmd`"") 'd-stopcmd-none' 90
        Check 'd-stopcmd-none' ($r.code -eq '0' -and $r.text -match 'No launcher is running: nothing to stop' -and -not (Test-Path (Join-Path $Repo 'perf-notes\WINDOW-STOP.txt'))) "STOP-LAUNCHER.cmd with no launcher: nothing to stop, no STOP file (exit $($r.code))"
    }
}

# ---------- a launcher waiting between windows: RUN-DAY stops it without asking ----------
if (Want 'd-between') {
    Hold-Check
    $p = Start-Day 'd-between' "-StopAt $Hm3"
    try {
        $ok = Wait-Log 'd-between' 'waiting for .*WINDOW-GO\.txt' 120
        $o = Join-Path $Res 'd-between.out'; Remove-Item $o -ErrorAction SilentlyContinue
        $r = Ctl 'd-between-ctl' "-Mode day -DryRunTag d-between -OutFile `"$o`" -ReturnTime $Hm3 -Answer Y -WaitMinutes 3"
        $ex = $p.WaitForExit(60000); $lg = Log-Text 'd-between'; $e = EndFor $Hm3
        Check 'd-between' ($ok -and $r.code -eq '0' -and $r.text -match 'is waiting between windows' -and $r.text -notmatch 'Stop the window' -and $r.text -match 'The launcher has ended' -and $ex -and $lg -match ("STOP file seen \(waiting for a GO\): 'STOP [0-9: -]+ by RUN-DAY\.cmd: day session until " + [regex]::Escape("$e (back at $Hm3)'")) -and $lg -match 'launcher end: STOP file, exit 0' -and -not (Test-Path (Join-Path (SD 'd-between') 'WINDOW-STOP.txt')) -and (OutIs $o $e)) "waiting launcher stopped by RUN-DAY's STOP (no question), ended exit 0, STOP consumed, -StopAt $e (ctl exit $($r.code))"
        Remove-Item $o -ErrorAction SilentlyContinue
    } finally { Kill-Left $p }
}

# ---------- STOP-LAUNCHER on a waiting launcher: N keeps it, Y stops it with the reason ----------
if (Want 'd-stop') {
    Hold-Check
    $p = Start-Day 'd-stop' "-StopAt $Hm3"
    try {
        $ok = Wait-Log 'd-stop' 'waiting for .*WINDOW-GO\.txt' 120
        $r = Ctl 'd-stop-n' "-Mode stop -DryRunTag d-stop -Reason `"test reason d-stop`" -Answer N"
        Check 'd-stop-n' ($ok -and $r.code -eq '1' -and $r.text -match 'No window is running now, so nothing is lost' -and $r.text -match 'its numbers are lost' -and $r.text -match 'Nothing was changed' -and -not (Test-Path (Join-Path (SD 'd-stop') 'WINDOW-STOP.txt')) -and -not $p.HasExited) "answer N: no STOP file, launcher still running (exit $($r.code))"
        $r = Ctl 'd-stop-y' "-Mode stop -DryRunTag d-stop -Reason `"test reason d-stop`" -Answer Y -WaitMinutes 3"
        $ex = $p.WaitForExit(60000); $lg = Log-Text 'd-stop'
        Check 'd-stop-y' ($r.code -eq '0' -and $r.text -match 'The launcher has ended' -and $ex -and $lg -match "STOP file seen \(waiting for a GO\): 'STOP [0-9: -]+ by STOP-LAUNCHER\.cmd: test reason d-stop'" -and $lg -match 'launcher end: STOP file, exit 0') "answer Y: STOP with the reason line, launcher ended exit 0 (ctl exit $($r.code))"
    } finally { Kill-Left $p }
}

# ---------- run-day.ps1 -StopAt: a GO that cannot end 10 min before the end time is refused ----------
if (Want 'd-dl') {
    Hold-Check
    $hm = HM 12
    $p = Start-Day 'd-dl' "-StopAt $hm -SampleSeconds 1 -MatrixDir `"$LT`" -GateFixture `"$LT\gate-quiet.json`" -MaxGo 1"
    try {
        $ok = Wait-Log 'd-dl' 'waiting for .*WINDOW-GO\.txt' 120
        [IO.File]::WriteAllText((Join-Path (SD 'd-dl') 'WINDOW-GO.txt'), $GoGood + "`r`n")
        $ex = $p.WaitForExit(240000); $lg = Log-Text 'd-dl'
        Check 'd-dl' ($ok -and $ex -and $p.ExitCode -eq 0 -and $lg -match 'deadline: estimate \d+ min \+ 10 min would end after' -and $lg -notmatch 'GO ACCEPTED') "-StopAt $hm (12 min): the 7-min GO is refused for the end time; launcher exit $(if ($ex) { $p.ExitCode } else { 'still running' })"
    } finally { Kill-Left $p }
}

# ---------- a window running: RUN-DAY and STOP-LAUNCHER ask first; Y kills the window ----------
if (Want 'd-window') {
    Hold-Check
    $env:A5_FAKE_SECONDS = '900'; $env:A5_FAKE_CHILD = '900'
    try { $p = Start-Day 'd-window' "-StopAt $Hm3 -SampleSeconds 1 -MatrixDir `"$LT`" -GateFixture `"$LT\gate-quiet.json`" -FakeRunner `"$LT\fake-runner.ps1`" -MaxGo 1" }
    finally { Remove-Item Env:\A5_FAKE_SECONDS, Env:\A5_FAKE_CHILD -ErrorAction SilentlyContinue }
    $childPid = 0
    try {
        $ok = Wait-Log 'd-window' 'waiting for .*WINDOW-GO\.txt' 120
        [IO.File]::WriteAllText((Join-Path (SD 'd-window') 'WINDOW-GO.txt'), $GoGood + "`r`n")
        $run = Wait-State 'd-window' 'running' 300
        Start-Sleep -Seconds 3
        $cf = @(Get-ChildItem (SD 'd-window') -Recurse -Filter 'fake-child.pid' -ErrorAction SilentlyContinue)
        if ($cf.Count) { $childPid = [int]([IO.File]::ReadAllText($cf[0].FullName).Trim()) }
        $pins = ''; $pf = Join-Path (SD 'd-window') 'pins.txt'; if (Test-Path $pf) { $pins = [IO.File]::ReadAllText($pf) }
        Check 'd-window-0' ($ok -and $run -and (Log-Text 'd-window') -match 'GO ACCEPTED: window T1' -and $pins -match 'RUN-DAY\.cmd' -and $pins -match 'run-day\.ps1' -and $pins -notmatch 'RUN-NIGHT') "run-day.ps1 -StopAt $Hm3 accepted the GO and runs the (fake) window; pins.txt has run-day.ps1 + RUN-DAY.cmd (child pid $childPid)"
        $o = Join-Path $Res 'd-window.out'; Remove-Item $o -ErrorAction SilentlyContinue
        $sf = Join-Path (SD 'd-window') 'WINDOW-STOP.txt'
        $r = Ctl 'd-window-1' "-Mode day -DryRunTag d-window -OutFile `"$o`" -ReturnTime $Hm3 -Answer YN"
        Check 'd-window-1' ($r.code -eq '1' -and $r.text -match 'is RUNNING timing window T1 since' -and $r.text -match 'kills this window, and its numbers are lost' -and $r.text -match 'Stop the window and the launcher now\? \(Y/N\): N' -and $r.text -match 'Nothing was changed' -and -not (Test-Path $sf) -and -not (Test-Path $o) -and -not $p.HasExited -and (Wait-State 'd-window' 'running' 1)) "RUN-DAY during a window says so and asks; N: no STOP, window keeps running (exit $($r.code))"
        $r = Ctl 'd-window-2' "-Mode stop -DryRunTag d-window -Reason x -Answer N"
        Check 'd-window-2' ($r.code -eq '1' -and $r.text -match 'A window IS running now: stopping loses it' -and $r.text -match 'its numbers are lost' -and $r.text -match 'Stop the launcher now and lose this window\? \(Y/N\): N' -and -not (Test-Path $sf) -and -not $p.HasExited) "STOP-LAUNCHER during a window warns the numbers are lost; N: nothing written (exit $($r.code))"
        $r = Ctl 'd-window-3' "-Mode day -DryRunTag d-window -OutFile `"$o`" -ReturnTime $Hm3 -Answer YY -WaitMinutes 3"
        $ex = $p.WaitForExit(90000); $lg = Log-Text 'd-window'
        $childGone = ($childPid -eq 0) -or -not (Get-Process -Id $childPid -ErrorAction SilentlyContinue)
        Check 'd-window-3' ($r.code -eq '0' -and $r.text -match 'The launcher has ended' -and $ex -and $lg -match "STOP file seen \(while window T1 was running\): 'STOP [0-9: -]+ by RUN-DAY\.cmd: day session until" -and $lg -match 'runner stopped: yes' -and $lg -notmatch 'NOT killed|could not kill|runner stopped: NO' -and $childGone -and $childPid -ne 0 -and -not (Test-Path $sf) -and (OutIs $o (EndFor $Hm3))) "Y: window killed (runner + child $childPid), launcher ended, STOP consumed, -StopAt $(EndFor $Hm3) (ctl exit $($r.code))"
        Remove-Item $o -ErrorAction SilentlyContinue
    } finally { Kill-Left $p; if ($childPid) { Stop-Process -Id $childPid -Force -ErrorAction SilentlyContinue } }
}

$after = Snap
Check 'real-files' ($before -eq $after) "perf-notes GO/HOLD/STOP and bench\agent5\launch unchanged ($after)"
$left = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CreationDate -ge $TestStart -and ($_.CommandLine -match '-File\s+"?[^"]*\\day-draft\\(run-day|launcher-ctl)\.ps1' -or $_.CommandLine -match '-File\s+"?[^"]*\\fake-runner\.ps1' -or $_.CommandLine -match 'Start-Sleep -Seconds 900' -or $_.CommandLine -match 'Agent5RunNight-dry-d-unknown') })
Check 'leftovers' ($left.Count -eq 0) "processes left from the tests: $($left.Count) $(@($left | ForEach-Object { $_.ProcessId }) -join ',')"
$sum = Join-Path $Res "summary-$Name-$(Get-Date -Format 'HHmmss').txt"
$pass = @($script:Results | Where-Object { $_.StartsWith('PASS') }).Count
$lines = @("test-day $Name, ended $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); run-day.ps1 $((Get-FileHash $Day).Hash); launcher-ctl.ps1 $((Get-FileHash $Ctl).Hash)") + $script:Results + @("$pass/$($script:Results.Count) PASS")
[IO.File]::WriteAllText($sum, ($lines -join "`r`n") + "`r`n")
Write-Host "$pass/$($script:Results.Count) PASS; summary $sum"
if ($pass -ne $script:Results.Count) { exit 1 }
exit 0
