# launcher-ctl.ps1: Agent 5's helper for RUN-DAY.cmd (-Mode day) and STOP-LAUNCHER.cmd (-Mode stop). Plain description:
# README-DAY.md next to this file. It never starts a launcher or a game itself. It writes only perf-notes\WINDOW-STOP.txt
# (to stop a running launcher; removed again if the launcher ended without reading it) and -OutFile. It deletes a STOP
# file only after asking (an old one with no launcher running, or one still there after the stop).
#  -Mode day : runs only from bench\agent5\day\ (the installed copy, next to RUN-DAY.cmd and run-day.ps1) and on AC power;
#              otherwise it changes nothing. It asks your return time (HH:mm, at least 90 min and less than 14 h away),
#              shows the day session's end (return time - 15 min) and asks Y/N. A launcher that is still running (night
#              or day) is stopped first with the STOP file: without a question only while it waits between windows; if a
#              window is running or about to start, or its state is unknown, it says so and asks first. Then it writes the
#              end time ('yyyy-MM-dd HH:mm') to -OutFile. Exit 0: RUN-DAY.cmd starts run-day.ps1 -StopAt <that>. Exit 1:
#              nothing.
#  -Mode stop: if a launcher is running, it warns (a running window is killed and its numbers are lost), asks a reason and
#              Y/N, writes the STOP file with the reason and waits until the launcher has ended. Exit 0 ended or nothing
#              to stop, 1 not stopped.
# Tests: -DryRunTag <tag> looks at <LaunchDir>\status-dryrun\<tag>\ (the files of a launcher started with -DryRun
# -DryRunTag <tag>; LaunchDir default: this folder) instead of perf-notes\ and status\; it skips the folder check, and
# the AC check only prints. -ReturnTime (tries, comma-separated), -Answer (one Y/N letter per question, in order),
# -Reason and -WaitMinutes replace the questions; refused without -DryRunTag.
param(
    [ValidateSet('day', 'stop')][string]$Mode = 'day',
    [string]$OutFile = '',
    [string]$DryRunTag = '',
    [string]$LaunchDir = '',
    [string]$ReturnTime = '',
    [string]$Answer = '',
    [string]$Reason = '',
    [double]$WaitMinutes = 5
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
if ($args.Count) { Write-Host "refused: unknown argument(s) '$($args -join ' ')'" -ForegroundColor Red; exit 1 }
$Inv = [Globalization.CultureInfo]::InvariantCulture
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$hooks = @($PSBoundParameters.Keys | Where-Object { @('LaunchDir', 'ReturnTime', 'Answer', 'Reason', 'WaitMinutes') -contains $_ })
if ($hooks.Count -and -not $DryRunTag) { Write-Host "refused: $((@($hooks | ForEach-Object { '-' + $_ })) -join ' ') only work together with -DryRunTag" -ForegroundColor Red; exit 1 }
$Test = [bool]$DryRunTag
if ($Test) {
    if ($DryRunTag -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$') { Write-Host "refused: -DryRunTag '$DryRunTag' must be 1-32 of A-Z a-z 0-9 _ . -" -ForegroundColor Red; exit 1 }
    if (-not $LaunchDir) { $LaunchDir = $PSScriptRoot } elseif (-not [IO.Path]::IsPathRooted($LaunchDir)) { $LaunchDir = Join-Path $Repo $LaunchDir }
    $Base = Join-Path $LaunchDir "status-dryrun\$DryRunTag"
    $StopFile = Join-Path $Base 'WINDOW-STOP.txt'
    $StatusDirs = @(@{ dir = $Base; what = "the dry-run launcher '$DryRunTag'" })
    $MutexName = "Local\Agent5RunNight-dry-$DryRunTag"
} else {
    $StopFile = Join-Path $Repo 'perf-notes\WINDOW-STOP.txt'
    $StatusDirs = @(@{ dir = (Join-Path $Repo 'bench\agent5\launch\status'); what = 'the night launcher' },
                    @{ dir = (Join-Path $PSScriptRoot 'status'); what = 'the day launcher' })
    $MutexName = 'Local\Agent5RunNight-real'     # the same name in run-night.ps1 and run-day.ps1: only one runs at a time
}
$script:AnsIx = 0

function Ts([datetime]$T) { return $T.ToString('yyyy-MM-dd HH:mm:ss', $Inv) }
function Ask-YN([string]$Q) {
    if ($Test) {
        $a = 'N'; if ($script:AnsIx -lt $Answer.Length) { $a = [string]$Answer[$script:AnsIx] }; $script:AnsIx++
        Write-Host "$Q (Y/N): $a   [test answer]"
        return ($a -ieq 'Y')
    }
    for ($k = 0; $k -lt 3; $k++) {
        $r = Read-Host "$Q (Y/N)"
        if ($null -eq $r) { return $false }
        $r = $r.Trim()
        if ($r -ieq 'Y' -or $r -ieq 'yes') { return $true }
        if ($r -ieq 'N' -or $r -ieq 'no') { return $false }
        Write-Host 'Please type Y or N.'
    }
    Write-Host 'No answer: taken as N.'
    return $false
}
# The return time: HH:mm, the next time the clock shows it; at least 90 min and less than 14 h from now. 3 tries.
function Read-Return {
    $tries = @(); if ($Test) { $tries = @($ReturnTime -split ',' | ForEach-Object { $_.Trim() }) }
    for ($k = 0; $k -lt 3; $k++) {
        if ($Test) { $s = ''; if ($k -lt $tries.Count) { $s = $tries[$k] }; Write-Host "When are you back? (HH:mm): $s   [test answer]" }
        else { $s = Read-Host 'When are you back? (HH:mm on the 24-hour clock, e.g. 17:30)'; if ($null -eq $s) { $s = '' }; $s = $s.Trim() }
        if ($s -eq '') { Write-Host 'No time given.'; return $null }
        if ($s -notmatch '^([01]?[0-9]|2[0-3]):([0-5][0-9])$') { Write-Host "'$s' is not a time like 17:30." -ForegroundColor Yellow; continue }
        $now = Get-Date
        $t = $now.Date.AddHours([int]$Matches[1]).AddMinutes([int]$Matches[2])
        if ($t -le $now) { $t = $t.AddDays(1) }
        $min = ($t - $now).TotalMinutes
        if ($min -lt 90) { Write-Host ("{0} is only {1:0} min from now: a day session needs at least 90 min." -f $t.ToString('ddd HH:mm', $Inv), [math]::Floor($min)) -ForegroundColor Yellow; continue }
        if ($min -ge 14 * 60) { Write-Host ("{0} is {1:0.0} h from now: it must be less than 14 h away." -f $t.ToString('ddd HH:mm', $Inv), ($min / 60)) -ForegroundColor Yellow; continue }
        return $t
    }
    Write-Host 'No usable time after 3 tries.'
    return $null
}
function Test-Alive {
    $m = $null
    try { if ([System.Threading.Mutex]::TryOpenExisting($MutexName, [ref]$m)) { $m.Dispose(); return $true } }
    catch [System.UnauthorizedAccessException] { return $true }
    return $false
}
function Read-State([string]$Dir) {
    $f = Join-Path $Dir 'state.txt'
    if (-not (Test-Path -LiteralPath $f)) { return $null }
    $lines = $null
    for ($k = 0; $k -lt 10 -and $null -eq $lines; $k++) { try { $lines = [IO.File]::ReadAllLines($f) } catch { Start-Sleep -Milliseconds 100 } }
    if ($null -eq $lines) { return $null }
    $h = @{ file = $f; time = (Get-Item -LiteralPath $f).LastWriteTime; name = '?'; pid = 0 }
    foreach ($line in $lines) { if ($line -match '^(\S+)\s+(.*)$') { $h[$Matches[1]] = $Matches[2].Trim() } }
    if ($h.ContainsKey('state')) { $h.name = ($h['state'] -split ' ')[0] }
    if ($h.ContainsKey('mode') -and $h['mode'] -match 'launcher pid (\d+)') { $h.pid = [int]$Matches[1] }
    return $h
}
# The running launcher's state: the newest state.txt that is not ended and whose launcher pid is alive.
function Get-Launcher {
    $best = $null
    foreach ($sd in $StatusDirs) {
        $s = Read-State $sd.dir
        if (-not $s) { continue }
        $s.what = $sd.what
        if (@('ended', 'refused-at-start') -contains $s.name) { continue }
        if ($s.pid -and -not (Get-Process -Id $s.pid -ErrorAction SilentlyContinue)) { continue }
        if (-not $best -or $s.time -gt $best.time) { $best = $s }
    }
    return $best
}
function Get-K($S, [string]$K) { if ($S -and $S.ContainsKey($K)) { return $S[$K] }; return '?' }
function Describe($S) {
    if (-not $S) { return 'a launcher is running (its state file was not found)' }
    switch ($S.name) {
        'running' { return "$($S.what) (pid $($S.pid)) is RUNNING timing window $(Get-K $S 'window') since $(Get-K $S 'started'), expected to end about $(Get-K $S 'est_end')" }
        'waiting-for-quiet' { return "$($S.what) (pid $($S.pid)) accepted window $(Get-K $S 'window') at $(Get-K $S 'accepted') and is waiting for the PC to be quiet; nothing has been measured yet" }
        'waiting-for-go' { return "$($S.what) (pid $($S.pid)) is waiting between windows; no window is running" }
        default { return "$($S.what) (pid $($S.pid)) is in state '$($S.name)'" }
    }
}
function Is-State($S, [string]$N) { return [bool]($S -and $S.name -eq $N) }
# AC power as run-day.ps1 checks it at start: AC if the power line is online or there is no system battery.
function Get-Power {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        $p = [System.Windows.Forms.SystemInformation]::PowerStatus
        $line = [int]$p.PowerLineStatus; $flag = [int]$p.BatteryChargeStatus
        $what = if ($line -eq 1) { 'AC' } elseif ($flag -eq 128) { 'AC (no battery)' } elseif ($line -eq 0) { 'ON BATTERY' } else { 'UNKNOWN' }
        return @{ ac = (($line -eq 1) -or ($flag -eq 128)); text = "$what (power line $line, battery flag $flag)" }
    } catch { return @{ ac = $false; text = "UNKNOWN ($($_.Exception.Message))" } }
}
# Day mode, before the STOP: no question only while the launcher waits between windows. $true = go on.
function Confirm-Stop($S) {
    if (Is-State $S 'waiting-for-go') { Write-Host ('Stopping: ' + (Describe $S) + '.'); return $true }
    if (Is-State $S 'running') {
        Write-Host ('A timing window is running: ' + (Describe $S) + '.') -ForegroundColor Yellow
        Write-Host 'Stopping the launcher now kills this window, and its numbers are lost.' -ForegroundColor Yellow
        return (Ask-YN 'Stop the window and the launcher now?')
    }
    if (Is-State $S 'waiting-for-quiet') {
        Write-Host ('A window is about to start: ' + (Describe $S) + '.') -ForegroundColor Yellow
        Write-Host 'Stopping the launcher now cancels it (nothing is lost; the agents can run it later).' -ForegroundColor Yellow
        return (Ask-YN 'Cancel it and stop the launcher now?')
    }
    Write-Host ('Its state is unknown (' + (Describe $S) + '): a window may be running, and stopping would lose it.') -ForegroundColor Yellow
    return (Ask-YN 'Stop the launcher anyway?')
}
function Read-Stop { $t = ''; try { $t = ([IO.File]::ReadAllText($StopFile)).Trim() } catch { }; return $t }
# Writes the STOP file (never over an existing one) and waits until the launcher's mutex is gone. $true = it ended.
function Stop-Launcher([string]$StopText) {
    $mine = $false
    if (Test-Path -LiteralPath $StopFile) { Write-Host "A STOP file is already there ('$(Read-Stop)'); it is left as it is." }
    else {
        try {
            $fs = [IO.File]::Open($StopFile, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try { $b = (New-Object Text.UTF8Encoding $false).GetBytes($StopText + "`r`n"); $fs.Write($b, 0, $b.Length) } finally { $fs.Dispose() }
            $mine = $true
            Write-Host "Wrote $StopFile : $StopText"
        } catch {
            if (-not (Test-Path -LiteralPath $StopFile)) { Write-Host "Could not write $StopFile : $($_.Exception.Message)" -ForegroundColor Red; return $false }
            Write-Host "A STOP file appeared meanwhile ('$(Read-Stop)'); it is left as it is."
        }
    }
    Write-Host "Waiting for the launcher to end (up to $WaitMinutes min) ..."
    $t0 = Get-Date; $next = 15
    while (Test-Alive) {
        $sec = ((Get-Date) - $t0).TotalSeconds
        if ($sec -ge $WaitMinutes * 60) {
            Write-Host "The launcher has not ended after $WaitMinutes min. The STOP file stays, so it ends as soon as it can. If it does not, click in its window and press Ctrl+C (not the X: closing the window skips its clean-up; see README-DAY.md)." -ForegroundColor Red
            return $false
        }
        if ($sec -ge $next) { Write-Host ("  still running after {0:0} s ..." -f $sec); $next += 15 }
        Start-Sleep -Milliseconds 500
    }
    Write-Host 'The launcher has ended.' -ForegroundColor Green
    if ($mine -and (Test-Path -LiteralPath $StopFile) -and (Read-Stop) -eq $StopText) {
        Remove-Item -LiteralPath $StopFile -Force; Write-Host 'Removed the STOP file again (the launcher ended without reading it).'
    }
    return $true
}

$tag = ''; if ($Test) { $tag = " (TEST, dry-run tag $DryRunTag)" }
if ($Mode -eq 'day') {
    Write-Host ''; Write-Host "Day session: Agent 5's launcher runs timing windows while you are away$tag" -ForegroundColor Cyan; Write-Host ''
    if (-not $Test -and $PSScriptRoot -notlike '*\bench\agent5\day') { Write-Host "This RUN-DAY.cmd is in $PSScriptRoot. The day session runs only from bench\agent5\day\ (the installed copy). Nothing was changed." -ForegroundColor Red; exit 1 }
    $miss = @(@('RUN-DAY.cmd', 'run-day.ps1') | Where-Object { -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $_)) })
    if ($miss.Count) { Write-Host "Missing next to launcher-ctl.ps1: $($miss -join ', '). Nothing was changed." -ForegroundColor Red; exit 1 }
    $pw = Get-Power
    Write-Host "Power: $($pw.text)"
    if (-not $pw.ac) {
        if ($Test) { Write-Host '(test: a real day session would stop here)' }
        else { Write-Host 'The PC is not on AC power: plug it in, then run RUN-DAY.cmd again. Nothing was changed.' -ForegroundColor Red; exit 1 }
    }
    if (Test-Alive) {
        Write-Host ('Now: ' + (Describe (Get-Launcher)) + '.')
        Write-Host 'It is stopped before the day session starts (unless it is just waiting for a window, you are asked first).'
    } elseif (Test-Path -LiteralPath $StopFile) {
        Write-Host "An old STOP file is there: $StopFile ('$(Read-Stop)'). No launcher is running, and a new one refuses to start while this file exists."
        if (-not (Ask-YN 'Delete it?')) { Write-Host 'Nothing was changed.'; exit 1 }
        Remove-Item -LiteralPath $StopFile -Force; Write-Host 'Deleted.'
    }
    $ret = Read-Return
    if (-not $ret) { exit 1 }
    $end = $ret.AddMinutes(-15)
    Write-Host ''
    Write-Host ("  now:                   {0}" -f (Get-Date).ToString('ddd HH:mm', $Inv))
    Write-Host ("  you are back at:       {0}" -f $ret.ToString('ddd HH:mm', $Inv))
    Write-Host ("  the day session ends:  {0}  (15 min before; a window starts only if it can end 10 min before this)" -f $end.ToString('ddd HH:mm', $Inv))
    Write-Host ''
    if (-not (Ask-YN 'Start the day session?')) { Write-Host 'Nothing was changed.'; exit 1 }
    if ((Get-Date) -ge $end.AddMinutes(-60)) { Write-Host 'Too late now: less than 1 h is left before the end time. Nothing was changed.' -ForegroundColor Yellow; exit 1 }
    if (Test-Alive) {
        $s = Get-Launcher
        if (-not (Confirm-Stop $s)) {
            if (Is-State $s 'running') { Write-Host "Nothing was changed. You can run RUN-DAY.cmd again after the window ends (about $(Get-K $s 'est_end'))." } else { Write-Host 'Nothing was changed.' }
            exit 1
        }
        $s2 = Get-Launcher
        if ((Is-State $s2 'running') -and -not (Is-State $s 'running')) {
            Write-Host ('A window has just started: ' + (Describe $s2) + '. Stopping now loses it.') -ForegroundColor Yellow
            if (-not (Ask-YN 'Stop anyway?')) { Write-Host 'Nothing was changed.'; exit 1 }
        }
        $why = "day session until $($end.ToString('yyyy-MM-dd HH:mm', $Inv)) (back at $($ret.ToString('HH:mm', $Inv)))"
        if (-not (Stop-Launcher "STOP $(Ts (Get-Date)) by RUN-DAY.cmd: $why")) { Write-Host 'The day session was not started. Run RUN-DAY.cmd again once the old launcher has ended.'; exit 1 }
    }
    if (Test-Path -LiteralPath $StopFile) {
        Write-Host "A STOP file is there: $StopFile ('$(Read-Stop)'); the day launcher would refuse to start while it exists."
        if (-not (Ask-YN 'Delete it and go on?')) { Write-Host 'The day session was not started.'; exit 1 }
        Remove-Item -LiteralPath $StopFile -Force
    }
    if ((Get-Date) -ge $end.AddMinutes(-60)) { Write-Host 'Too late now: less than 1 h is left before the end time. The day session was not started.' -ForegroundColor Yellow; exit 1 }
    if (-not $OutFile) { Write-Host 'no -OutFile given: the day session was not started' -ForegroundColor Red; exit 1 }
    [IO.File]::WriteAllText($OutFile, $end.ToString('yyyy-MM-dd HH:mm', $Inv) + "`r`n", (New-Object Text.ASCIIEncoding))
    exit 0
}

# -Mode stop
Write-Host ''; Write-Host "Stop Agent 5's launcher (night or day)$tag" -ForegroundColor Cyan; Write-Host ''
if (-not (Test-Alive)) {
    Write-Host 'No launcher is running: nothing to stop. Nothing was changed.'
    if (Test-Path -LiteralPath $StopFile) { Write-Host "Note: $StopFile exists ('$(Read-Stop)'); a launcher started now refuses to start until it is deleted." }
    exit 0
}
$s = Get-Launcher
Write-Host ('Now: ' + (Describe $s) + '.')
Write-Host 'Warning: if a timing window is running when the launcher stops, the window is killed and its numbers are lost.' -ForegroundColor Yellow
if (Is-State $s 'running') { Write-Host 'A window IS running now: stopping loses it.' -ForegroundColor Yellow }
elseif (Is-State $s 'waiting-for-quiet') { Write-Host 'A window was accepted but has not started: stopping cancels it (nothing measured is lost).' -ForegroundColor Yellow }
elseif (Is-State $s 'waiting-for-go') { Write-Host 'No window is running now, so nothing is lost.' }
else { Write-Host 'Its state is unknown: a window may be running, and stopping would lose it.' -ForegroundColor Yellow }
if ($Test) { $r = $Reason; Write-Host "Why are you stopping it? (one line): $r   [test answer]" }
else { $r = Read-Host "Why are you stopping it? (one line; Enter = 'stopped by the user')" }
if ($null -eq $r) { $r = '' }
$r = ($r -replace '[\x00-\x1F]+', ' ').Trim()
if ($r.Length -gt 200) { $r = $r.Substring(0, 200) }
if (-not $r) { $r = 'stopped by the user' }
$q = 'Stop the launcher anyway?'
if (Is-State $s 'running') { $q = 'Stop the launcher now and lose this window?' } elseif ((Is-State $s 'waiting-for-go') -or (Is-State $s 'waiting-for-quiet')) { $q = 'Stop the launcher now?' }
if (-not (Ask-YN $q)) { Write-Host 'Nothing was changed.'; exit 1 }
$s2 = Get-Launcher
if ((Is-State $s2 'running') -and -not (Is-State $s 'running')) {
    Write-Host ('A window has just started: ' + (Describe $s2) + '. Stopping now loses it.') -ForegroundColor Yellow
    if (-not (Ask-YN 'Stop anyway?')) { Write-Host 'Nothing was changed.'; exit 1 }
}
if (-not (Test-Alive)) { Write-Host 'The launcher has already ended. Nothing was changed.'; exit 0 }
if (Stop-Launcher "STOP $(Ts (Get-Date)) by STOP-LAUNCHER.cmd: $r") { exit 0 }
exit 1
