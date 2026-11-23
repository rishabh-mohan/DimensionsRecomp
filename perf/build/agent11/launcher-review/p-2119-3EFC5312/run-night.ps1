# run-night.ps1: Agent 5's overnight launcher (task #4, old #27). Plain description: README.md next to this file.
# The user starts it once (RUN-NIGHT.cmd) on the unlocked desktop. It waits for perf-notes\WINDOW-GO.txt:
#   GO <window-id> <matrix json in bench\agent8\run\> <sha256 of that json> only=<arm,arm,...> repeats=<n>
# checks it, waits for a quiet machine, then runs ONLY the pinned bench\agent8\run\run-matrix.ps1 with that json
# (-Only -Repeats -ColdShared -NoPrompt). It deletes every GO it reads. It exits at 07:30 or when
# perf-notes\WINDOW-STOP.txt appears.
# -DryRun: everything happens in bench\agent5\launch\status-dryrun\[<tag>\] (GO, HOLD, STOP, status). It never touches
# the real GO/HOLD/STOP files, never closes apps, never changes the screensaver or the keep-awake state, and never
# starts a matrix: it prints the command it would run. It does run run-matrix.ps1 -PlanOnly (reads only, starts no
# game) for the estimate. The test hooks below work only with -DryRun.
# Exit: 0 normal end (07:30, STOP, -MaxGo), 2 refused at start, 3 launcher error.
param(
    [switch]$DryRun,
    [string]$DryRunTag = '',          # dry-run hooks from here on (refused without -DryRun)
    [double]$SampleSeconds = 60,      # one gate sample per interval = one "1-min average"
    [double]$GiveUpMinutes = 120,
    [double]$StrictMinutes = 30,
    [string]$StopAt = '',             # 'HH:mm' (next one) or 'yyyy-MM-dd HH:mm'; default 07:30
    [string]$MatrixDir = '',          # where the GO's json is looked up; default bench\agent8\run
    [double]$PollSeconds = 15,
    [int]$MaxGo = 0,                  # exit after this many GO files (0 = no limit)
    [string]$GateFixture = '',        # json with simulated gate samples (see README, "Tests")
    [string]$StartBy = '',            # latest window start, like -StopAt; default 06:45 (with -StopAt: the -StopAt time)
    [double]$GraceMinutes = 15,       # a window still running this long after the end time is stopped (runner tree killed)
    [string]$FakeRunner = '',         # runs this script instead of the runner (tests the run, STOP and end-time handling)
    [switch]$SkipStartChecks          # dry run only: start checks are logged but do not refuse
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
# No [CmdletBinding()]: a mistyped parameter (e.g. -DryRunn) would land in $args and run REAL mode, so refuse it.
if ($args.Count) { Write-Host "refused: unknown argument(s) '$($args -join ' ')'. README.md lists the parameters." -ForegroundColor Red; exit 2 }

$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$RunDir = Join-Path $Repo 'bench\agent8\run'
$RunMatrix = Join-Path $RunDir 'run-matrix.ps1'
$PsExe = Join-Path $PSHOME 'powershell.exe'
$Inv = [Globalization.CultureInfo]::InvariantCulture
# Env keys an arm may set (exact case), from build/agent8/w8w9/ENV-KEYS-F1.txt (sha256 D1AE6D57...), approved by Agent 1 at 21:14.
# All of them are also removed from the runner's own environment before it starts.
$AllowedEnv = @('REX_TIMER_WAIT_BLOCKING', 'LEGO_GPU_WAIT_STATS', 'LEGO_GPU_WAIT_BACKOFF_US', 'LEGO_GPU_WAIT_SPIN_US',
                'LEGO_NATIVE_FRAME_METRICS', 'LEGO_NATIVE_SHADER_MISS_CACHE', 'LEGO_NATIVE_THREADED', 'LEGO_NATIVE_PREPARE_THREADS',
                'LEGO_NATIVE_SNAPSHOT_STATE', 'LEGO_NATIVE_FULL_DRAW_PREPARATION', 'LEGO_NATIVE_CHAIN_PRIORITY')
$MaxRunHours = 14     # refuse to start when the end (07:30) is further away than this, i.e. when started after 07:30
$LatestStartTime = 6.75   # 06:45: no window starts at or after this time on the morning of the end time
$GateProcs = @('MsMpEng', 'OfficeClickToRun', 'CrossDeviceService')
# The runner's build list (timing-env.ps1 Get-BuildProcRegex) plus legodimensions; clangd / clang-format excluded.
$BuildInc = '^(clang.*|lld.*|ld\.lld.*|llvm-.*|ninja.*|cmake.*|dxc.*|cl|link|lib|mt|rc|msbuild.*|rexglue.*|codegen.*|sccache.*|ccache.*|rustc|cargo|legodimensions)$'
$BuildExc = '^(clangd.*|clang-format.*)$'
# The only programs it closes (process names, any case), only in this user's session. Roblox Studio is left alone (it
# can hold unsaved work): "Roblox" here means the player and the Store app.
$CloseNames = @('ChatGPT', 'Copilot', 'Microsoft.Copilot', 'copilotapphost', 'copilotapp_proxy', 'Roblox', 'RobloxPlayerBeta',
                'RobloxPlayerLauncher', 'Windows10Universal', 'Taskmgr', 'wallpaper32', 'wallpaper64', 'webwallpaper32', 'webwallpaper64')
# These names are closed only when the exe path matches, because other programs use the same names (any Store app can
# run as Windows10Universal.exe): the Copilot apps, the Store Roblox app, Wallpaper Engine's ui32/ui64.
$CopilotRx = '\\WindowsApps\\Microsoft\.(Copilot|Windows\.Ai\.Copilot)_'
$OfficeHubRx = '\\WindowsApps\\Microsoft\.MicrosoftOfficeHub_'
$CloseByPath = @{ 'Copilot' = $CopilotRx; 'Microsoft.Copilot' = $CopilotRx; 'copilotapphost' = $OfficeHubRx; 'copilotapp_proxy' = $OfficeHubRx
                  'Windows10Universal' = '\\WindowsApps\\ROBLOXCORPORATION\.ROBLOX_'; 'ui32' = 'wallpaper_engine'; 'ui64' = 'wallpaper_engine' }
$MinRamGB = 6.0; $MinDiskGB = 6.0; $QuietCores = 0.1; $RelaxMaxCores = 1.2; $RelaxSpread = 0.2; $DeadlineSlackMin = 10

# ---------- mode, paths, hooks ----------
$hookNames = @('DryRunTag', 'SampleSeconds', 'GiveUpMinutes', 'StrictMinutes', 'StopAt', 'MatrixDir', 'PollSeconds', 'MaxGo', 'GateFixture', 'StartBy', 'GraceMinutes', 'FakeRunner', 'SkipStartChecks')
$usedHooks = @($PSBoundParameters.Keys | Where-Object { $hookNames -contains $_ })
if ($usedHooks.Count -and -not $DryRun) { Write-Host "refused: $((@($usedHooks | ForEach-Object { '-' + $_ })) -join ' ') only work together with -DryRun" -ForegroundColor Red; exit 2 }
if ($DryRun) {
    if ($DryRunTag -and $DryRunTag -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$') { Write-Host "refused: -DryRunTag '$DryRunTag' must be 1-32 of A-Z a-z 0-9 _ . -" -ForegroundColor Red; exit 2 }
    $Base = Join-Path $PSScriptRoot 'status-dryrun'; if ($DryRunTag) { $Base = Join-Path $Base $DryRunTag }
    $StatusDir = $Base
    $GoFile = Join-Path $Base 'WINDOW-GO.txt'; $HoldFile = Join-Path $Base 'WINDOW-HOLD.txt'; $StopFile = Join-Path $Base 'WINDOW-STOP.txt'
    $MutexName = 'Local\Agent5RunNight-dry-' + $(if ($DryRunTag) { $DryRunTag } else { 'default' })
} else {
    $StatusDir = Join-Path $PSScriptRoot 'status'
    $GoFile = Join-Path $Repo 'perf-notes\WINDOW-GO.txt'; $HoldFile = Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt'
    $StopFile = Join-Path $Repo 'perf-notes\WINDOW-STOP.txt'
    $MutexName = 'Local\Agent5RunNight-real'
}
$MatrixDirEff = if ($MatrixDir) { (Resolve-Path -LiteralPath $(if ([IO.Path]::IsPathRooted($MatrixDir)) { $MatrixDir } else { Join-Path $Repo $MatrixDir })).Path.TrimEnd('\') } else { $RunDir }
New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
$LogFile = Join-Path $StatusDir 'log.txt'
$StateFile = Join-Path $StatusDir 'state.txt'
$script:WinLog = $null

function Now { return (Get-Date) }
function Ts([datetime]$T) { return $T.ToString('yyyy-MM-dd HH:mm:ss', $Inv) }
# For the final clean-up: one failing step must not skip the others.
function Try-Step([string]$Name, [scriptblock]$Do) { try { & $Do } catch { try { Log "!!! $($Name) failed: $($_.Exception.Message)" 'Red' } catch { } } }
function Add-Text([string]$Path, [string]$Text) {
    for ($k = 0; $k -lt 20; $k++) { try { [IO.File]::AppendAllText($Path, $Text + "`r`n", (New-Object Text.UTF8Encoding $false)); return } catch { Start-Sleep -Milliseconds 100 } }
}
function Set-Text([string]$Path, [string]$Text) {
    for ($k = 0; $k -lt 20; $k++) { try { [IO.File]::WriteAllText($Path, $Text + "`r`n", (New-Object Text.UTF8Encoding $false)); return } catch { Start-Sleep -Milliseconds 100 } }
}
function Log([string]$Msg, [string]$Color = 'Gray') {
    $line = "$(Ts (Now)) $(if ($DryRun) { '[dry] ' })$Msg"
    Write-Host $line -ForegroundColor $Color
    Add-Text $LogFile $line
    if ($script:WinLog) { Add-Text $script:WinLog $line }
}
$script:State = @{ state = 'starting'; since = (Ts (Now)) }
function Set-State([string]$S, [hashtable]$Extra = @{}) {
    if ($S -ne $script:State.state) { $script:State = @{ state = $S; since = (Ts (Now)) } }
    foreach ($k in $Extra.Keys) { $script:State[$k] = [string]$Extra[$k] }
    $L = New-Object System.Collections.Generic.List[string]
    $L.Add("state      $($script:State.state) (since $($script:State.since))")
    $L.Add("heartbeat  $(Ts (Now))")
    $L.Add("mode       $(if ($DryRun) { "DRY RUN ($StatusDir)" } else { 'REAL' }); launcher pid $PID; deadline $(if ($script:Deadline) { Ts $script:Deadline } else { '?' })")
    foreach ($k in @($script:State.Keys | Where-Object { @('state', 'since') -notcontains $_ } | Sort-Object)) { $L.Add(('{0,-10} {1}' -f $k, $script:State[$k])) }
    Set-Text $StateFile ($L -join "`r`n")
}

# ---------- desktop, lock, power (same calls as the runner's timing-env.ps1) ----------
if (-not ('LdNight' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class LdNight {
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint threadId);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] static extern IntPtr GetProcessWindowStation();
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool GetUserObjectInformationW(IntPtr hObj, int nIndex, StringBuilder pvInfo, int nLength, out int lpnLengthNeeded);
    [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
    [DllImport("user32.dll", SetLastError = true)] public static extern bool SystemParametersInfoW(uint uiAction, uint uiParam, IntPtr pvParam, uint fWinIni);
    static string Name(IntPtr h) {
        if (h == IntPtr.Zero) return null;
        var sb = new StringBuilder(256); int need;
        return GetUserObjectInformationW(h, 2, sb, sb.Capacity * 2, out need) ? sb.ToString() : null;
    }
    public static string Desktop() { return Name(GetProcessWindowStation()) + "\\" + Name(GetThreadDesktop(GetCurrentThreadId())); }
    [DllImport("kernel32.dll")] static extern IntPtr GetStdHandle(int n);
    [DllImport("kernel32.dll")] static extern bool GetConsoleMode(IntPtr h, out uint m);
    [DllImport("kernel32.dll")] static extern bool SetConsoleMode(IntPtr h, uint m);
    // A click in a console with Quick Edit on pauses all output, which would stall the launcher and the runner.
    public static string NoQuickEdit() {
        IntPtr h = GetStdHandle(-10); uint m;
        if (!GetConsoleMode(h, out m)) return "no console input";
        if ((m & 0x40) == 0) return "already off";
        return SetConsoleMode(h, (m & ~0x40u) | 0x80u) ? "turned off" : "could not be turned off";
    }
    [StructLayout(LayoutKind.Sequential)]
    public struct PowerStatus { public byte ACLineStatus, BatteryFlag, BatteryLifePercent, SystemStatusFlag; public uint BatteryLifeTime, BatteryFullLifeTime; }
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetSystemPowerStatus(out PowerStatus s);
    // "ACLineStatus BatteryFlag BatteryLifePercent" from GetSystemPowerStatus, or "failed <win32 error>".
    public static string Power() {
        PowerStatus s;
        if (!GetSystemPowerStatus(out s)) return "failed " + Marshal.GetLastWin32Error();
        return s.ACLineStatus + " " + s.BatteryFlag + " " + s.BatteryLifePercent;
    }
}
'@
}
function Get-DesktopName { try { return [LdNight]::Desktop() } catch { return '?' } }
function Test-LogonUI { return [bool](Get-Process -Name LogonUI -ErrorAction SilentlyContinue) }
# GetSystemPowerStatus: on AC only if ACLineStatus = 1 (online) or BatteryFlag = 128 (no system battery). A failed
# query or an unknown state (255) counts as not on AC, so the start check and the gate refuse.
function Get-Power {
    $r = ''; try { $r = [LdNight]::Power() } catch { $r = "failed ($($_.Exception.Message))" }
    if ($r -match '^(\d+) (\d+) (\d+)$') { $line = [int]$Matches[1]; $flag = [int]$Matches[2]; $pct = [int]$Matches[3] }
    else { return @{ ac = $false; text = "UNKNOWN (GetSystemPowerStatus $r)" } }
    $ac = ($line -eq 1) -or ($flag -eq 128)
    $what = if ($line -eq 1) { 'AC' } elseif ($flag -eq 128) { 'AC (no battery)' } elseif ($line -eq 0) { 'ON BATTERY' } else { 'UNKNOWN' }
    return @{ ac = $ac; text = "$what (ACLineStatus $line, BatteryFlag $flag, battery $(if ($pct -eq 255) { '?' } else { $pct }) %)" }
}
function Get-RamGB { Add-Type -AssemblyName Microsoft.VisualBasic; return [math]::Round((New-Object Microsoft.VisualBasic.Devices.ComputerInfo).AvailablePhysicalMemory / 1GB, 2) }
function Get-DiskGB { return [math]::Round((New-Object IO.DriveInfo 'C').AvailableFreeSpace / 1GB, 2) }
# $PathRx is only set by a dry-run test fixture ("builds_path"): count only build processes whose exe path matches, so a
# test sees its own dummy ninja.exe and not other agents' builds. The real launcher always passes ''.
function Get-BuildProcs([string]$PathRx = '') {
    $hits = foreach ($p in [Diagnostics.Process]::GetProcesses()) {
        $n = $p.ProcessName
        if ($n -match $BuildInc -and $n -notmatch $BuildExc) {
            if ($PathRx) { $path = ''; try { $path = $p.MainModule.FileName } catch { }; if ($path -notmatch $PathRx) { continue } }
            "$($n):$($p.Id)"
        }
    }
    return @($hits | Sort-Object)
}

# ---------- pins: the runner and everything it loads, plus this launcher ----------
function Get-PinFiles {
    $f = New-Object System.Collections.Generic.List[string]
    $f.Add($PSCommandPath); $f.Add((Join-Path $PSScriptRoot 'RUN-NIGHT.cmd'))
    foreach ($n in @('run-matrix.ps1', 'run-timing.ps1', 'common.ps1', 'timing-env.ps1', 'winhelper.cs')) { $f.Add((Join-Path $RunDir $n)) }
    foreach ($x in @(Get-ChildItem -LiteralPath $RunDir -File | Where-Object { $_.Extension -eq '.py' -or $_.Extension -eq '.cs' })) { $f.Add($x.FullName) }
    $drv = Join-Path $RunDir 'drivers'
    if (Test-Path -LiteralPath $drv) { foreach ($x in @(Get-ChildItem -LiteralPath $drv -File -Recurse)) { $f.Add($x.FullName) } }
    # Read by the runner from outside bench\agent8\run: the game's toml template and NVML (drivers\thread-cpu.ps1).
    $f.Add((Join-Path $Repo 'harness\legodimensions.toml')); $f.Add((Join-Path $Repo 'harness\nvml.cs'))
    return @($f | Sort-Object -Unique)
}
function Get-Pins {
    $h = [ordered]@{}
    foreach ($p in (Get-PinFiles)) {
        $rel = if ($p.StartsWith($Repo, [StringComparison]::OrdinalIgnoreCase)) { $p.Substring($Repo.Length + 1) } else { $p }
        if (Test-Path -LiteralPath $p -PathType Leaf) { $h[$rel] = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash } else { $h[$rel] = 'MISSING' }
    }
    return $h
}
function Compare-Pins($A, $B) {
    $d = New-Object System.Collections.Generic.List[string]
    foreach ($k in $A.Keys) { if (-not $B.Contains($k)) { $d.Add("$k gone") } elseif ($A[$k] -ne $B[$k]) { $d.Add("$k changed ($($A[$k].Substring(0, [math]::Min(8, $A[$k].Length))) -> $($B[$k].Substring(0, [math]::Min(8, $B[$k].Length))))") } }
    foreach ($k in $B.Keys) { if (-not $A.Contains($k)) { $d.Add("$k new") } }
    return , $d
}
function Test-Pinned([string]$Path) {
    try { $full = [IO.Path]::GetFullPath($Path) } catch { return $false }
    foreach ($p in (Get-PinFiles)) { if ([string]::Equals($p, $full, [StringComparison]::OrdinalIgnoreCase)) { return $true } }
    return $false
}

# ---------- the GO file ----------
function Read-Text([string]$Path) {
    $b = [IO.File]::ReadAllBytes($Path)
    if ($b.Length -gt 4096) { return $null }
    if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { return [Text.Encoding]::UTF8.GetString($b, 3, $b.Length - 3) }
    if ($b.Length -ge 2 -and $b[0] -eq 0xFF -and $b[1] -eq 0xFE) { return [Text.Encoding]::Unicode.GetString($b, 2, $b.Length - 2) }
    if ($b.Length -ge 2 -and $b[0] -eq 0xFE -and $b[1] -eq 0xFF) { return [Text.Encoding]::BigEndianUnicode.GetString($b, 2, $b.Length - 2) }
    return [Text.Encoding]::UTF8.GetString($b)
}
# Strict: one non-empty line of exactly 6 tokens.
function Parse-Go([string]$Text) {
    $g = @{ ok = $false; why = New-Object System.Collections.Generic.List[string]; raw = ''; id = ''; json = ''; sha = ''; only = @(); repeats = 0 }
    if ($null -eq $Text) { $g.why.Add('GO file is larger than 4 KB'); return $g }
    $lines = @($Text -split "`r?`n" | Where-Object { $_.Trim() })
    if ($lines.Count -ne 1) { $g.why.Add("GO file must hold exactly one line, it has $($lines.Count)"); if ($lines.Count) { $g.raw = $lines[0].Trim() }; return $g }
    $g.raw = $lines[0].Trim()
    $t = @($g.raw -split '\s+')
    if ($t.Count -ne 6) { $g.why.Add("GO line must have 6 tokens, it has $($t.Count)"); return $g }
    $idRx = '[A-Za-z0-9][A-Za-z0-9_.-]{0,31}'
    if ($t[0] -cne 'GO') { $g.why.Add("first token must be GO, not '$($t[0])'") }
    if ($t[1] -notmatch "^$idRx$") { $g.why.Add("window id '$($t[1])' must be 1-32 of A-Z a-z 0-9 _ . -") } else { $g.id = $t[1] }
    if ($t[2] -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.json$' -or $t[2] -match '\.\.') { $g.why.Add("matrix '$($t[2])' must be a plain .json file name (no folder)") } else { $g.json = $t[2] }
    if ($t[3] -notmatch '^[0-9A-Fa-f]{64}$') { $g.why.Add('sha256 must be 64 hex digits') } else { $g.sha = $t[3].ToUpperInvariant() }
    if ($t[4] -cnotmatch "^only=$idRx(,$idRx)*$") { $g.why.Add("'$($t[4])' must be only=<arm>[,<arm>...]") }
    else { $g.only = @($t[4].Substring(5) -split ','); if (@($g.only | Select-Object -Unique).Count -ne $g.only.Count) { $g.why.Add('only= lists an arm twice') } }
    if ($t[5] -cnotmatch '^repeats=([1-9]|1[0-9]|20)$') { $g.why.Add("'$($t[5])' must be repeats=<1-20>") } else { $g.repeats = [int]$t[5].Substring(8) }
    $g.ok = ($g.why.Count -eq 0)
    return $g
}

# ---------- the matrix named by the GO ----------
function Get-P($O, [string]$N) { if ($null -ne $O -and $O -is [System.Management.Automation.PSCustomObject]) { $pp = $O.PSObject.Properties[$N]; if ($null -ne $pp) { return $pp.Value } }; return $null }
function Resolve-Driver([string]$P) {
    if ([IO.Path]::IsPathRooted($P)) { return $P }
    foreach ($b in @($MatrixDirEff, $RunDir, $Repo)) { $c = Join-Path $b $P; if (Test-Path -LiteralPath $c -PathType Leaf) { return (Resolve-Path -LiteralPath $c).Path } }
    return (Join-Path $Repo $P)
}
# Every arm in the file is checked, not only the -Only ones. Returns the list of reasons to refuse (empty = ok).
function Test-Matrix($Go, [string]$Path) {
    $why = New-Object System.Collections.Generic.List[string]
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { $why.Add("matrix $($Go.json) not found in $MatrixDirEff"); return , $why }
    if (-not [string]::Equals((Split-Path -Parent ([IO.Path]::GetFullPath($Path))).TrimEnd('\'), $MatrixDirEff, [StringComparison]::OrdinalIgnoreCase)) { $why.Add("matrix is not directly in $MatrixDirEff"); return , $why }
    $sha = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    if ($sha -ne $Go.sha) { $why.Add("sha256 mismatch: the GO says $($Go.sha), the file is $sha"); return , $why }
    try { $mx = [IO.File]::ReadAllText($Path) | ConvertFrom-Json } catch { $why.Add("matrix is not valid JSON: $($_.Exception.Message)"); return , $why }
    $arms = @(Get-P $mx 'arms')
    if ($arms.Count -eq 0 -or $null -eq $arms[0]) { $why.Add('matrix has no arms'); return , $why }
    $ids = @()
    foreach ($a in $arms) {
        $id = [string](Get-P $a 'id'); $ids += $id
        $bin = [string](Get-P $a 'bin')
        $bn = $bin -replace '\\', '/'
        if ($bn -notmatch '^build/agent2/([A-Za-z0-9][A-Za-z0-9_.-]*)-bin/?$' -or $bn -match '\.\.') { $why.Add("arm '$id': bin '$bin' is not build/agent2/<name>-bin") }
        else {
            $bd = Join-Path $Repo ('build\agent2\' + $Matches[1] + '-bin')
            foreach ($need in @('MANIFEST.txt', 'legodimensions.exe')) { if (-not (Test-Path -LiteralPath (Join-Path $bd $need) -PathType Leaf)) { $why.Add("arm '$id': $bin has no $need") } }
        }
        $ev = Get-P $a 'env'
        if ($null -ne $ev) {
            if ($ev -isnot [System.Management.Automation.PSCustomObject]) { $why.Add("arm '$id': env is not an object") }
            else { foreach ($pp in $ev.PSObject.Properties) { if ($AllowedEnv -cnotcontains $pp.Name) { $why.Add("arm '$id': env key '$($pp.Name)' is not allowed (only $($AllowedEnv -join ', '))") } } }
        }
        # Launcher rule (unattended, pinned inputs only): no menu prompt, no profiler, no triggers, no toml edits, no seed cache.
        if ([string](Get-P $a 'menu')) { $why.Add("arm '$id': menu needs a person at the PC") }
        if ((Get-P $a 'profile') -eq $true) { $why.Add("arm '$id': profile runs are not timing runs") }
        if (@(Get-P $a 'triggers' | Where-Object { $_ }).Count) { $why.Add("arm '$id': triggers are not allowed here") }
        $tm = Get-P $a 'toml'; if ($null -ne $tm -and @($tm.PSObject.Properties).Count) { $why.Add("arm '$id': toml edits are not allowed here") }
        if ([string](Get-P $a 'seed_cache')) { $why.Add("arm '$id': seed_cache is not allowed here") }
        $dr = Get-P $a 'driver'
        if ($null -ne $dr) {
            # Only a plain string "drivers/<name>.ps1" (letters, digits, _ and -) that resolves to that file in
            # bench\agent8\run\drivers (pinned), with no args: any other runner file as a driver could start a game, bin,
            # env or matrix that was never checked. The {script, args} form is refused.
            $okDrv = $false
            if ($dr -is [string] -and $dr -cmatch '^drivers/([A-Za-z0-9_-]+\.ps1)$') {
                $want = Join-Path (Join-Path $RunDir 'drivers') $Matches[1]; $fp = ''; try { $fp = [IO.Path]::GetFullPath((Resolve-Driver $dr)) } catch { }
                $okDrv = [string]::Equals($fp, $want, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $want -PathType Leaf) -and (Test-Pinned $want)
            }
            if (-not $okDrv) { $why.Add("arm '$id': driver must be a plain string drivers/<name>.ps1 (no args, no {script, args}) naming a file in bench\agent8\run\drivers (it is '$(if ($dr -is [string]) { $dr } else { ConvertTo-Json -InputObject $dr -Compress -Depth 4 })')") }
        }
    }
    foreach ($o in $Go.only) { if ($ids -cnotcontains $o) { $why.Add("only=: no arm '$o' in $($Go.json)") } }
    return , $why
}
# -NonInteractive: if the runner ever asked for input it would fail at once instead of waiting all night (run-matrix.ps1
# asks only without -Matrix or without -NoPrompt).
function Get-RunnerArgs([string]$Path, $Go) {
    return @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $RunMatrix, '-Matrix', $Path, '-Only', ($Go.only -join ','), '-Repeats', [string]$Go.repeats, '-ColdShared', '-NoPrompt')
}
# sha256 of legodimensions.exe and MANIFEST.txt in the bins of the only= arms (paths already checked by Test-Matrix).
# Logged when the GO is accepted and compared again right before the start.
function Get-BinHashes($Go, [string]$Path) {
    $h = [ordered]@{}
    $mx = [IO.File]::ReadAllText($Path) | ConvertFrom-Json
    foreach ($a in @(Get-P $mx 'arms')) {
        if ($Go.only -cnotcontains [string](Get-P $a 'id')) { continue }
        $bn = (([string](Get-P $a 'bin')) -replace '\\', '/').TrimEnd('/')
        foreach ($f in @('legodimensions.exe', 'MANIFEST.txt')) {
            $k = "$bn/$f"; if ($h.Contains($k)) { continue }
            $p = Join-Path $Repo (($bn -replace '/', '\') + '\' + $f)
            $h[$k] = if (Test-Path -LiteralPath $p -PathType Leaf) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash } else { 'MISSING' }
        }
    }
    return $h
}
# Not reasons to refuse: logged as WARN in the window log.
function Get-MatrixWarnings([string]$Path) {
    $w = New-Object System.Collections.Generic.List[string]
    try { $mx = [IO.File]::ReadAllText($Path) | ConvertFrom-Json } catch { return , $w }
    if ((Get-P $mx 'sys_csv') -ne $true) { $w.Add('the matrix has no "sys_csv": true, so the runs write no sys.json (no system data for this window)') }
    return , $w
}
# run-matrix.ps1 -PlanOnly: reads the matrix, writes nothing, starts nothing. Gives the runner's own estimate.
function Get-Plan([string]$Path, $Go) {
    $r = @{ ok = $false; why = ''; min = 0; runs = 0; lines = @() }
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $r.lines = @(& $PsExe @(Get-RunnerArgs $Path $Go) -PlanOnly 2>&1 | ForEach-Object { "$_" }); $code = $LASTEXITCODE } finally { $ErrorActionPreference = $old }
    $est = @($r.lines | Where-Object { $_ -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min' })
    $bad = @($r.lines | Where-Object { $_ -match '^!!! (ERROR|SKIPPED ARM|MATRIX ERROR)' -or $_ -match '^\s+SKIP ' })
    if ($code -ne 0) { $r.why = "run-matrix.ps1 -PlanOnly exit $code" }
    elseif ($bad.Count) { $r.why = "run-matrix.ps1 -PlanOnly: $($bad -join ' / ')" }
    elseif (-not $est.Count) { $r.why = 'run-matrix.ps1 -PlanOnly printed no estimate line' }
    else { [void]($est[0] -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min'); $r.runs = [int]$Matches[1]; $r.min = [int]$Matches[2]; $r.ok = $true }
    return $r
}

# ---------- the quiet gate ----------
# One sample per interval. CPU of MsMpEng / OfficeClickToRun / CrossDeviceService = kernel+user time from CIM
# Win32_Process (readable for protected processes too), summed over the processes of that name, as cores over the
# interval since the previous sample. A process that cannot be read fails the gate; a process that is not running
# counts as 0. The first sample after a GO is the baseline (no CPU figure).
$script:Fixture = $null; $script:FixtureIx = 0
function Get-CpuRaw {
    $flt = (@($GateProcs | ForEach-Object { "Name='$_.exe'" }) -join ' OR ')
    $raw = @{ t = (Get-Date).ToUniversalTime(); procs = @{}; err = $null }
    try {
        foreach ($w in @(Get-CimInstance -ClassName Win32_Process -Filter $flt -OperationTimeoutSec 20 -ErrorAction Stop)) {
            $n = [IO.Path]::GetFileNameWithoutExtension([string]$w.Name)
            if ($null -eq $w.KernelModeTime -or $null -eq $w.UserModeTime) { $raw.err = "$n pid $($w.ProcessId) unreadable"; continue }
            $raw.procs["$n|$($w.ProcessId)"] = @{ name = $n; ticks = [double]$w.KernelModeTime + [double]$w.UserModeTime; created = $w.CreationDate }
        }
    } catch { $raw.err = "CIM Win32_Process failed: $($_.Exception.Message)" }
    return $raw
}
function Get-Cores($Prev, $Cur) {
    $c = @{}; foreach ($n in $GateProcs) { $c[$n] = 0.0 }
    $dt = ($Cur.t - $Prev.t).TotalSeconds * 1e7
    if ($dt -le 0) { return $null }
    foreach ($k in $Cur.procs.Keys) {
        $p = $Cur.procs[$k]
        if ($Prev.procs.ContainsKey($k)) { $c[$p.name] += [math]::Max(0, $p.ticks - $Prev.procs[$k].ticks) / $dt }
        elseif ($p.created -and $p.created.ToUniversalTime() -gt $Prev.t) { $c[$p.name] += $p.ticks / $dt }   # started inside the interval: all its CPU is in it
        else { return $null }   # running before but missing from the previous query: no figure for this interval
    }
    return $c
}
# A fixture field that is absent, null or 'real' means: measure it on this PC. (Reads the property directly: an empty
# array such as "builds": [] must stay a simulated "no build processes", and Get-P would unroll it to $null.)
function Use-Real($Fx, [string]$N) {
    if ($null -eq $Fx -or $Fx -isnot [System.Management.Automation.PSCustomObject]) { return $true }
    $pp = $Fx.PSObject.Properties[$N]
    if ($null -eq $pp -or $null -eq $pp.Value) { return $true }
    return ($pp.Value -is [string] -and $pp.Value -eq 'real')
}
function Get-Sample($Prev) {
    $s = @{ t = Now; cores = $null; raw = $null; builds = @(); ram = 0.0; disk = 0.0; logonui = $false; ac = $true; err = New-Object System.Collections.Generic.List[string] }
    $fx = $null
    if ($script:Fixture) { $all = @($script:Fixture.samples); $fx = $all[[math]::Min($script:FixtureIx, $all.Count - 1)]; $script:FixtureIx++ }
    if (-not (Use-Real $fx 'cpu')) {
        $fc = Get-P $fx 'cpu'
        if ($script:FixtureIx -gt 1) { $s.cores = @{}; foreach ($n in $GateProcs) { $v = Get-P $fc $n; $s.cores[$n] = if ($null -eq $v) { 0.0 } elseif ([string]$v -eq 'unreadable') { $null } else { [double]$v } } }
    } else {
        $s.raw = Get-CpuRaw
        if ($s.raw.err) { $s.err.Add($s.raw.err) }
        if ($Prev -and $Prev.raw -and -not $s.raw.err -and -not $Prev.raw.err) { $s.cores = Get-Cores $Prev.raw $s.raw }
    }
    $s.builds = @(if (Use-Real $fx 'builds') { Get-BuildProcs ([string](Get-P $fx 'builds_path')) } else { Get-P $fx 'builds' | Where-Object { $_ } })
    $s.ram = if (Use-Real $fx 'ram_gb') { Get-RamGB } else { [double](Get-P $fx 'ram_gb') }
    $s.disk = if (Use-Real $fx 'disk_gb') { Get-DiskGB } else { [double](Get-P $fx 'disk_gb') }
    $s.logonui = if (Use-Real $fx 'logonui') { Test-LogonUI } else { [bool](Get-P $fx 'logonui') }
    $s.ac = if (Use-Real $fx 'ac') { (Get-Power).ac } else { [bool](Get-P $fx 'ac') }
    return $s
}
function Fmt-Cores($C) { if ($null -eq $C) { return 'n/a' }; return (@($GateProcs | ForEach-Object { "$_ $(if ($null -eq $C[$_]) { 'unreadable' } else { $C[$_].ToString('0.00', $Inv) })" }) -join ', ') }
# The last 3 samples (3 consecutive 1-min averages) must all have a CPU figure and all be clean. Strict: every process
# < 0.1 core. From StrictMinutes after the GO: MsMpEng may instead be <= 1.2 cores in all 3 if they are within 0.2 core
# of each other (relaxed). The other conditions never relax.
function Test-Gate($Samples, [double]$MinSinceGo) {
    $g = @{ pass = $false; relaxed = $false; why = New-Object System.Collections.Generic.List[string]; text = '' }
    $last = @($Samples | Select-Object -Last 3)
    $cur = $Samples[$Samples.Count - 1]
    if ($cur.builds.Count) { $g.why.Add("build/game processes: $($cur.builds -join ' ')") }
    if ($cur.ram -lt $MinRamGB) { $g.why.Add("available RAM $($cur.ram) GB < $MinRamGB") }
    if ($cur.disk -lt $MinDiskGB) { $g.why.Add("free on C: $($cur.disk) GB < $MinDiskGB") }
    if ($cur.logonui) { $g.why.Add('LogonUI is running (locked)') }
    if (-not $cur.ac) { $g.why.Add('not on AC power') }
    foreach ($e in $cur.err) { $g.why.Add($e) }
    $withCpu = @($last | Where-Object { $null -ne $_.cores }).Count
    if ($last.Count -lt 3 -or $withCpu -lt 3) { $g.why.Add("$withCpu of 3 consecutive one-minute CPU averages so far"); return $g }
    # Sample 3 is $cur, checked above. Samples 1-2: report build processes only when they differ from the current ones.
    $curB = $cur.builds -join ' '
    for ($i = 0; $i -lt 2; $i++) {
        $s = $last[$i]
        if ($s.builds.Count -and ($s.builds -join ' ') -ne $curB) { $g.why.Add("sample $($i+1): build/game processes $($s.builds -join ' ')") }
        if ($s.ram -lt $MinRamGB -or $s.disk -lt $MinDiskGB -or $s.logonui -or -not $s.ac -or $s.err.Count) { $g.why.Add("sample $($i+1): RAM/disk/lock/power/read error not clean") }
    }
    foreach ($n in @('OfficeClickToRun', 'CrossDeviceService')) {
        $v = @($last | ForEach-Object { $_.cores[$n] })
        if (@($v | Where-Object { $null -eq $_ -or $_ -ge $QuietCores }).Count) { $g.why.Add("$n not < $QuietCores core in all 3 ($((@($v | ForEach-Object { if ($null -eq $_) { 'unreadable' } else { $_.ToString('0.00', $Inv) } })) -join '/'))") }
    }
    $m = @($last | ForEach-Object { $_.cores['MsMpEng'] })
    $mt = (@($m | ForEach-Object { if ($null -eq $_) { 'unreadable' } else { $_.ToString('0.00', $Inv) } })) -join '/'
    $g.text = "MsMpEng $mt, OfficeClickToRun $((@($last | ForEach-Object { if ($null -eq $_.cores['OfficeClickToRun']) { 'n/a' } else { $_.cores['OfficeClickToRun'].ToString('0.00', $Inv) } })) -join '/'), CrossDeviceService $((@($last | ForEach-Object { if ($null -eq $_.cores['CrossDeviceService']) { 'n/a' } else { $_.cores['CrossDeviceService'].ToString('0.00', $Inv) } })) -join '/')"
    $mStrict = -not @($m | Where-Object { $null -eq $_ -or $_ -ge $QuietCores }).Count
    if (-not $mStrict) {
        $ok = -not @($m | Where-Object { $null -eq $_ }).Count
        $mRelax = $ok -and $MinSinceGo -ge $StrictMinutes -and -not @($m | Where-Object { $_ -gt $RelaxMaxCores }).Count -and ((($m | Measure-Object -Maximum).Maximum - ($m | Measure-Object -Minimum).Minimum) -le $RelaxSpread + 1e-9)
        if ($mRelax) { $g.relaxed = $true }
        elseif ($MinSinceGo -lt $StrictMinutes) { $g.why.Add("MsMpEng not < $QuietCores core in all 3 ($mt; strict gate for the first $StrictMinutes min)") }
        else { $g.why.Add("MsMpEng not < $QuietCores, and not <= $RelaxMaxCores within $RelaxSpread of each other ($mt)") }
    }
    $g.pass = ($g.why.Count -eq 0)
    return $g
}

# ---------- screensaver, keep-awake, programs ----------
$DeskKey = 'HKCU:\Control Panel\Desktop'
$script:SsSaved = $null; $script:Awake = $false
$SsFile = Join-Path $StatusDir 'screensaver-saved.txt'
function Save-Screensaver {
    # A saved file without a 'restored' line comes from a launcher that did not finish (window closed?). It holds the
    # user's real settings: keep it under another name instead of overwriting it with the (None) state.
    if ((Test-Path -LiteralPath $SsFile) -and -not (Select-String -LiteralPath $SsFile -Pattern '^restored ' -Quiet)) {
        $keep = Join-Path $StatusDir "screensaver-saved-unrestored-$((Now).ToString('yyyyMMdd-HHmmss')).txt"
        Move-Item -LiteralPath $SsFile -Destination $keep -Force
        Log "!!! the last launcher did not restore the screensaver; its saved values are kept in $keep (restore them by hand)" 'Yellow'
    }
    $pol = Get-ItemProperty -LiteralPath 'HKCU:\Software\Policies\Microsoft\Windows\Control Panel\Desktop' -ErrorAction SilentlyContinue
    if ($pol -and ($pol.PSObject.Properties['ScreenSaveActive'] -or $pol.PSObject.Properties['SCRNSAVE.EXE'])) { Log '!!! a policy sets the screensaver: the launcher cannot change it' 'Yellow' }
    $k = Get-ItemProperty -LiteralPath $DeskKey
    $hasExe = $null -ne $k.PSObject.Properties['SCRNSAVE.EXE']
    $script:SsSaved = @{ active = [string](Get-P $k 'ScreenSaveActive'); has_exe = $hasExe; exe = $(if ($hasExe) { [string]$k.'SCRNSAVE.EXE' } else { '' }) }
    Set-Text $SsFile ("saved $(Ts (Now)) from $DeskKey by launcher pid $PID`r`nScreenSaveActive=$($script:SsSaved.active)`r`nSCRNSAVE.EXE present=$hasExe value='$($script:SsSaved.exe)'")
    return "ScreenSaveActive=$($script:SsSaved.active), SCRNSAVE.EXE $(if ($hasExe) { "'$($script:SsSaved.exe)'" } else { 'absent' })"
}
function Set-ScreensaverNone {
    $was = Save-Screensaver
    if ($DryRun) { Log "screensaver: would set (None) (now $was) and restore it at the end"; return }
    [void][LdNight]::SystemParametersInfoW(0x0011, 0, [IntPtr]::Zero, 3)     # SPI_SETSCREENSAVEACTIVE FALSE, update ini + broadcast
    if ($script:SsSaved.has_exe) { Remove-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' -ErrorAction SilentlyContinue }
    $k = Get-ItemProperty -LiteralPath $DeskKey
    Log "screensaver: set to (None) (was $was; now ScreenSaveActive=$([string](Get-P $k 'ScreenSaveActive')), SCRNSAVE.EXE $(if ($k.PSObject.Properties['SCRNSAVE.EXE']) { 'present' } else { 'absent' }))"
}
function Restore-Screensaver {
    if ($null -eq $script:SsSaved) { return }
    if ($DryRun) { Add-Text $SsFile "restored $(Ts (Now)) (dry run: nothing had been changed)"; $script:SsSaved = $null; return }
    try {
        if ($script:SsSaved.has_exe) { Set-ItemProperty -LiteralPath $DeskKey -Name 'SCRNSAVE.EXE' -Value $script:SsSaved.exe }
        [void][LdNight]::SystemParametersInfoW(0x0011, $(if ($script:SsSaved.active -eq '1') { 1 } else { 0 }), [IntPtr]::Zero, 3)
        $k = Get-ItemProperty -LiteralPath $DeskKey
        Log "screensaver: restored (ScreenSaveActive=$([string](Get-P $k 'ScreenSaveActive')), SCRNSAVE.EXE $(if ($k.PSObject.Properties['SCRNSAVE.EXE']) { "'$($k.'SCRNSAVE.EXE')'" } else { 'absent' }))"
        Add-Text $SsFile "restored $(Ts (Now))"
        $script:SsSaved = $null
    } catch { Log "!!! screensaver restore failed: $($_.Exception.Message); saved values: $SsFile" 'Red' }
}
function Set-Awake([bool]$On) {
    if ($DryRun) { if ($On) { Log 'keep-awake: would request SetThreadExecutionState(continuous+system+display) until the end' }; return }
    if ($On) {
        [void][LdNight]::SetThreadExecutionState([uint32]2147483651)
        $st = [LdNight]::SetThreadExecutionState([uint32]2147483651)
        $script:Awake = ($st -eq [uint32]2147483651)
        Log "keep-awake: $(if ($script:Awake) { 'ON (continuous+system+display)' } else { "FAILED (0x$('{0:X8}' -f $st))" })" $(if ($script:Awake) { 'Gray' } else { 'Yellow' })
    } elseif ($script:Awake) { [void][LdNight]::SetThreadExecutionState([uint32]2147483648); $script:Awake = $false; Log 'keep-awake: released' }
}
function Close-Programs([string]$When) {
    # One try/catch per program: a program that cannot be closed (Task Manager runs elevated, so even waiting for it can
    # be denied) is logged and left running. It never stops the window.
    $found = @()
    try {
        $left = New-Object System.Collections.Generic.List[string]
        $mySess = [Diagnostics.Process]::GetCurrentProcess().SessionId
        $found = @(foreach ($p in [Diagnostics.Process]::GetProcesses()) {
            $n = $p.ProcessName; $sess = -1; try { $sess = $p.SessionId } catch { }
            if ($sess -ne $mySess) { continue }     # this user's session only
            if ($CloseByPath.ContainsKey($n)) {
                $path = ''; try { $path = $p.MainModule.FileName } catch { }
                if (-not $path) { try { $path = [string](Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$($p.Id)" -OperationTimeoutSec 10 -ErrorAction Stop).ExecutablePath } catch { } }
                if ($path -and $path -match $CloseByPath[$n]) { $p }
                elseif ($CloseNames -contains $n) { $left.Add("$n pid $($p.Id) ($(if ($path) { $path } else { 'path unknown' }); closed only from a path matching '$($CloseByPath[$n])')") }
            }
            elseif ($CloseNames -contains $n) { $p }
        })
    } catch { Log "programs ($When): could not list the processes ($($_.Exception.Message)); going on" 'Yellow'; return }
    foreach ($x in $left) { Log "programs ($When): left alone: $x" }
    if (-not $found.Count) { Log "programs ($When): none running (ChatGPT, Copilot app, Roblox player or Store app, Task Manager, Wallpaper Engine)"; return }
    foreach ($p in $found) {
        $tag = "pid $($p.Id)"; try { $tag = "$($p.ProcessName) pid $($p.Id)" } catch { }
        if ($DryRun) { Log "programs ($When): would close $tag"; continue }
        try {
            try { [void]$p.CloseMainWindow() } catch { }
            if ($p.WaitForExit(10000)) { Log "programs ($When): $tag closed" }
            else { $p.Kill(); [void]$p.WaitForExit(5000); Log "programs ($When): $tag closed (killed after 10 s)" }
        } catch {
            $gone = $false; try { $gone = $p.HasExited } catch { }
            if ($gone) { Log "programs ($When): $tag closed" }
            else { Log "programs ($When): could not close $tag ($($_.Exception.Message)); elevated? left running, going on" 'Yellow' }
        }
    }
}

# ---------- HOLD and STOP ----------
# The launcher writes the HOLD file only when there is none, with a marker (window id, launcher pid, token), and deletes
# it only while its marker is still in it. A HOLD that is not ours is never replaced or deleted, and while one exists the
# quiet gate fails ("foreign HOLD"). Agent 1's hold manager takes the HOLD over once the runner has made its matrix
# folder and removes it when summary.md appears, so finding nothing of ours at the end is normal.
$script:HoldToken = $null
function Get-HoldState {
    if (-not (Test-Path -LiteralPath $HoldFile)) { return @{ kind = 'none'; text = '' } }
    $txt = ''; try { $txt = ([IO.File]::ReadAllText($HoldFile)).Trim() } catch { $txt = "(unreadable: $($_.Exception.Message))" }
    if ($script:HoldToken -and $txt.Contains($script:HoldToken)) { return @{ kind = 'ours'; text = $txt } }
    $one = $txt -replace '\s+', ' '; if ($one.Length -gt 160) { $one = $one.Substring(0, 160) + '...' }
    return @{ kind = 'foreign'; text = $one }
}
# Writes a new HOLD (CreateNew: never over an existing file). $true = written and read back; $false = a HOLD file was
# there first. Throws if no HOLD could be written.
function Set-Hold([string]$WindowId) {
    $tok = [guid]::NewGuid().ToString('N')
    $text = "HOLD window $WindowId by Agent 5's overnight launcher (bench\agent5\launch\run-night.ps1), pid $PID, since $(Ts (Now)), token $tok"
    $bytes = (New-Object Text.UTF8Encoding $false).GetBytes($text + "`r`n")
    $err = 'unknown'
    for ($k = 0; $k -lt 10; $k++) {
        if (Test-Path -LiteralPath $HoldFile) { return $false }
        $fs = $null
        try { $fs = [IO.FileStream]::new($HoldFile, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read) }
        catch { $err = $_.Exception.Message; Start-Sleep -Milliseconds 200; continue }
        $ok = $false
        try { $fs.Write($bytes, 0, $bytes.Length); $fs.Flush(); $ok = $true } catch { $err = $_.Exception.Message } finally { $fs.Dispose() }
        if ($ok) { break }
        try { Remove-Item -LiteralPath $HoldFile -Force } catch { }     # our own half-written file
        Start-Sleep -Milliseconds 200
    }
    $back = ''; try { $back = [IO.File]::ReadAllText($HoldFile) } catch { }
    if (-not $back.Contains($tok)) { if (Test-Path -LiteralPath $HoldFile) { return $false }; throw "the HOLD file $HoldFile could not be written ($err)" }
    $script:HoldToken = $tok
    Log "HOLD written: $HoldFile"
    return $true
}
# At GO acceptance, at every gate sample and right before the start: '' when the HOLD is ours (a new one is written when
# there is none), else the reason the window must wait.
function Sync-Hold([string]$WindowId) {
    $st = Get-HoldState
    if ($st.kind -eq 'ours') { return '' }
    if ($st.kind -eq 'none') {
        if ($script:HoldToken) { Log 'the HOLD file was removed by someone else before the window started: it is written again' 'Yellow'; $script:HoldToken = $null }
        if (Set-Hold $WindowId) { return '' }
        $st = Get-HoldState
        if ($st.kind -eq 'none') { return 'the HOLD file came and went while it was being written' }
    }
    if ($script:HoldToken) { Log "this window's HOLD was replaced by someone else's ('$($st.text)'): it is left as it is" 'Yellow'; $script:HoldToken = $null }
    return "foreign HOLD ('$($st.text)')"
}
function Clear-Hold {
    if (-not $script:HoldToken) { return }
    try {
        $st = Get-HoldState
        if ($st.kind -eq 'ours') {
            # A reader that opened the file without delete sharing can make one try fail: retry, but stop as soon as it
            # is no longer ours (the hold manager may take it over meanwhile).
            $err = ''
            for ($k = 0; $k -lt 5; $k++) {
                try { Remove-Item -LiteralPath $HoldFile -Force -ErrorAction Stop; $err = ''; break } catch { $err = $_.Exception.Message; Start-Sleep -Milliseconds 500 }
                if ((Get-HoldState).kind -ne 'ours') { break }
            }
            $st2 = Get-HoldState
            if ($st2.kind -eq 'none') { Log 'HOLD removed' }
            elseif ($st2.kind -eq 'ours') { Log "!!! HOLD remove failed after 5 tries ($err): delete $HoldFile by hand" 'Red' }
            else { Log "HOLD is not this window's any more (the hold manager took it over): left as it is" }
        }
        elseif ($st.kind -eq 'none') { Log 'HOLD already gone (the hold manager removed it)' }
        else { Log "HOLD is not this window's any more (the hold manager took it over): left as it is" }
    } catch { Log "!!! HOLD remove failed: $($_.Exception.Message)" 'Red' }
    $script:HoldToken = $null
}
function Test-Stop { return (Test-Path -LiteralPath $StopFile) }
function Use-Stop([string]$Where) {
    $txt = ''; try { $txt = ([IO.File]::ReadAllText($StopFile)).Trim() } catch { }
    try { Remove-Item -LiteralPath $StopFile -Force } catch { }
    Log "STOP file seen ($Where): '$txt'; it is deleted (consumed) and the launcher ends" 'Yellow'
}
function Read-When([string]$S, [string]$Name) {
    $n = Now; $d = [datetime]::MinValue
    if ([datetime]::TryParseExact($S, 'yyyy-MM-dd HH:mm', $Inv, 'None', [ref]$d)) { return $d }
    if ([datetime]::TryParseExact($S, 'HH:mm', $Inv, 'None', [ref]$d)) { $d = $n.Date.Add($d.TimeOfDay); if ($d -le $n) { $d = $d.AddDays(1) }; return $d }
    throw "$Name '$S' is not HH:mm or yyyy-MM-dd HH:mm"
}
function Get-Deadline {
    if ($StopAt) { return (Read-When $StopAt '-StopAt') }
    $n = Now; $d = $n.Date.AddHours(7.5); if ($d -le $n) { $d = $d.AddDays(1) }; return $d
}
# The latest window start: 06:45 on the morning of the end time. Dry-run tests: -StartBy, else the -StopAt time.
function Get-LatestStart {
    $l = if ($StartBy) { Read-When $StartBy '-StartBy' } elseif ($StopAt) { $script:Deadline } else { $script:Deadline.Date.AddHours($LatestStartTime) }
    if ($l -gt $script:Deadline) { $l = $script:Deadline }
    return $l
}

# ---------- one GO ----------
$script:GoCount = 0; $script:StopNow = $false; $script:Stuck = ''
$script:GoReadAt = $null
function Write-LastGo([string]$Raw, [string]$Verdict) { Set-Text (Join-Path $StatusDir 'last-go.txt') ("read     $(if ($script:GoReadAt) { Ts $script:GoReadAt } else { '?' })`r`nline     $Raw`r`nverdict  $Verdict`r`ndecided  $(Ts (Now))") }
function Write-LastResult([string]$Text) { Set-Text (Join-Path $StatusDir 'last-result.txt') ("written  $(Ts (Now))`r`n" + $Text) }
function Refuse([string]$Raw, [string]$Why, [string]$Stage = 'GO') {
    Log "$Stage REFUSED: $Why" 'Red'
    if ($Stage -eq 'GO') { Write-LastGo $Raw "REFUSED: $Why" }
    Write-LastResult "GO       $Raw`r`nresult   REFUSED ($Stage): $Why"
}
function Write-GateLine([string]$Text) {
    $line = "$((Now).ToString('HH:mm:ss', $Inv)) quiet gate: $Text"     # format agreed with Agent 12 (w6_env_record.py)
    $script:GateLine = $line
    Write-Host $line -ForegroundColor Cyan; Add-Text $LogFile $line; if ($script:WinLog) { Add-Text $script:WinLog $line }
    Add-Text (Join-Path $StatusDir 'gate.txt') $line
}
function Wait-Quiet($Go, $Plan, [datetime]$Accepted) {
    $samples = New-Object System.Collections.Generic.List[object]
    $script:FixtureIx = 0
    $script:Fixture = if ($GateFixture) { [IO.File]::ReadAllText((Resolve-Path -LiteralPath $GateFixture).Path) | ConvertFrom-Json } else { $null }
    if ($script:Fixture) { Log "gate: simulated samples from $GateFixture (fields set to 'real' use this PC)" 'Yellow' }
    $next = Now; $g = $null
    while ($true) {
        if (Test-Stop) { return 'stop' }
        $now = Now; $since = ($now - $Accepted).TotalMinutes; $mins = [int][math]::Floor($since)
        $last = if ($g -and $g.text) { $g.text } else { 'no CPU figures yet' }
        # The gate line keeps the format agreed with Agent 12; the last reason goes to the GATE REFUSED line and last-result.txt.
        $lastWhy = if ($g -and $g.why -and $g.why.Count) { $g.why -join '; ' } else { 'no sample yet' }
        if ($since -ge $GiveUpMinutes) { Write-GateLine "GAVE UP ($last; after $mins min; window not started)"; return "gave up: the quiet gate did not pass in $GiveUpMinutes min (last wait: $lastWhy)" }
        if ($now.AddMinutes($Plan.min + $DeadlineSlackMin) -gt $script:Deadline) { Write-GateLine "DEADLINE ($last; after $mins min; window not started)"; return "deadline: $($Plan.min) + $DeadlineSlackMin min no longer ends by $(Ts $script:Deadline) (last wait: $lastWhy)" }
        if ($now -ge $script:LatestStart) { Write-GateLine "DEADLINE ($last; after $mins min; window not started)"; return "latest start: no window starts at or after $(Ts $script:LatestStart) (last wait: $lastWhy)" }
        if ($now -ge $next) {
            # The HOLD must be ours: it is written if there is none; a foreign one fails this sample.
            $hw = ''; try { $hw = Sync-Hold $Go.id } catch { $hw = "the HOLD file could not be written ($($_.Exception.Message))" }
            $prev = if ($samples.Count) { $samples[$samples.Count - 1] } else { $null }
            $s = Get-Sample $prev; $samples.Add($s)
            $g = Test-Gate $samples $since
            if ($hw) { $g.why.Insert(0, $hw); $g.pass = $false }
            $verdict = if ($g.pass) { if ($g.relaxed) { 'PASS (relaxed)' } else { 'PASS' } } else { 'wait: ' + ($g.why -join '; ') }
            Log "gate $($samples.Count) (+$([math]::Round($since, 1)) min): cpu $(Fmt-Cores $s.cores); builds $(if ($s.builds.Count) { $s.builds -join ' ' } else { 'none' }); RAM $($s.ram) GB; C: $($s.disk) GB; LogonUI $($s.logonui); AC $($s.ac) -> $verdict"
            Set-State 'waiting-for-quiet' @{ window = $Go.id; gate = $verdict; accepted = (Ts $Accepted) }
            if ($g.pass) {
                if ($g.relaxed) {
                    Write-GateLine "RELAXED ($($g.text); after $mins min)"
                    Log "relaxed gate: MsMpEng accepted at <= $RelaxMaxCores cores within $RelaxSpread of each other after the $StrictMinutes-min strict phase; values $($g.text)" 'Yellow'
                    Set-Text (Join-Path $StatusDir 'relaxed-gate.txt') "relaxed gate $(Ts (Now)), window $($Go.id): $($g.text) (strict phase $StrictMinutes min, MsMpEng <= $RelaxMaxCores, spread <= $RelaxSpread)"
                } else { Write-GateLine "STRICT ($($g.text))" }
                return 'start'
            }
            $next = $next.AddSeconds($SampleSeconds); if ($next -lt (Now)) { $next = Now }
        }
        Start-Sleep -Milliseconds 500
    }
}
function Start-Window($Go, [string]$MPath, $Plan, [string]$WTag) {
    # Programs are closed first, so that the last checks come right before the runner starts.
    Close-Programs 'window start'
    # Real mode: the matrix json stays open from the last checks until the runner ends. Others may read it; nobody may
    # change or delete it.
    $lock = $null
    if (-not $DryRun) { try { $lock = [IO.File]::Open($MPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read) } catch { Refuse $Go.raw "the matrix json could not be opened for the run: $($_.Exception.Message)" 'START'; return } }
    try { Start-WindowLocked $Go $MPath $Plan $WTag } finally { if ($lock) { $lock.Dispose() } }
}
function Start-WindowLocked($Go, [string]$MPath, $Plan, [string]$WTag) {
    $why = New-Object System.Collections.Generic.List[string]
    $diff = Compare-Pins $script:Pins (Get-Pins); if ($diff.Count) { $why.Add("pinned files changed since the start: $($diff -join '; ')") }
    $mw = Test-Matrix $Go $MPath; foreach ($w in $mw) { $why.Add($w) }
    if (-not $mw.Count) { $bd = Compare-Pins $Go.bins (Get-BinHashes $Go $MPath); if ($bd.Count) { $why.Add("bin files changed since the GO: $($bd -join '; ')") } }
    if ((Now).AddMinutes($Plan.min + $DeadlineSlackMin) -gt $script:Deadline) { $why.Add("deadline: $($Plan.min) + $DeadlineSlackMin min would end after $(Ts $script:Deadline)") }
    if ((Now) -ge $script:LatestStart) { $why.Add("latest start: no window starts at or after $(Ts $script:LatestStart)") }
    # The session checks again (the last gate sample may be a minute old).
    $soft = New-Object System.Collections.Generic.List[string]
    $desk = Get-DesktopName; if ($desk -ine 'WinSta0\Default') { $soft.Add("this is desktop '$desk', not the user's own desktop WinSta0\Default") }
    if (Test-LogonUI) { $soft.Add('the PC is locked (LogonUI is running)') }
    $pw = Get-Power; if (-not $pw.ac) { $soft.Add("not on AC power: $($pw.text)") }
    if ($soft.Count -and $DryRun -and $SkipStartChecks) { Log "last checks would refuse: $($soft -join '; ') (ignored: -DryRun -SkipStartChecks)" 'Yellow' }
    else { foreach ($w in $soft) { $why.Add($w) } }
    $hw = ''; try { $hw = Sync-Hold $Go.id } catch { $hw = "the HOLD file could not be written ($($_.Exception.Message))" }
    if ($hw) { $why.Add($hw) }
    if ($why.Count) { Refuse $Go.raw ($why -join '; ') 'START'; return }
    Log "bins unchanged since the GO ($($Go.bins.Count) files)"
    foreach ($k in $AllowedEnv) { if ($null -ne [Environment]::GetEnvironmentVariable($k, 'Process')) { [Environment]::SetEnvironmentVariable($k, $null, 'Process'); Log "removed $k from the environment" } }
    $pc = 'n/a'; try { $pc = ((@(& powercfg.exe /getactivescheme) | ForEach-Object { "$_".Trim() } | Where-Object { $_ }) -join ' ') } catch { }
    Log "power scheme at the start: $pc"
    $rArgs = Get-RunnerArgs $MPath $Go
    $cmd = "`"$PsExe`" " + (Join-Args $rArgs)
    if ($DryRun) {
        Log "DRY RUN, would start window $($Go.id) now, without $($AllowedEnv -join ' / ') in its environment:" 'Cyan'
        Log "  $cmd" 'Cyan'
        if (-not $FakeRunner) {
            Write-LastResult "GO       $($Go.raw)`r`nresult   DRY RUN: would have started (estimate $($Plan.min) min)`r`ngate     $($script:GateLine)`r`ncommand  $cmd"
            return
        }
        $rArgs = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', (Resolve-Path -LiteralPath $FakeRunner).Path, '-Dir', $StatusDir)
        $cmd = "`"$PsExe`" " + (Join-Args $rArgs)
        Log 'DRY RUN with -FakeRunner: the fake runner below runs instead (tests the run, STOP and end-time handling)' 'Yellow'
    }
    $rlog = Join-Path $StatusDir "runner-$WTag.txt"
    Add-Text $rlog "launcher: window $($Go.id), GO '$($Go.raw)'; $($script:GateLine)"
    $t0 = Now
    Set-State 'running' @{ window = $Go.id; started = (Ts $t0); est_end = (Ts $t0.AddMinutes($Plan.min)); runner_log = $rlog }
    Log "window $($Go.id) START (estimate $($Plan.min) min, about $($t0.AddMinutes($Plan.min).ToString('HH:mm', $Inv))): $cmd" 'Green'
    $run = @{ code = $null; killed = '' }
    try { $run = Invoke-Runner (Join-Args $rArgs) $rlog $WTag $t0 } catch { Log "!!! runner call failed: $($_.Exception.Message)" 'Red' }
    $code = $run.code
    $mins = [math]::Round(((Now) - $t0).TotalMinutes, 1)
    $od = @(Get-Content -LiteralPath $rlog -ErrorAction SilentlyContinue | Where-Object { $_ -match '^out dir: ' } | Select-Object -Last 1)
    $outDir = if ($od.Count) { $od[0].Substring(9) } else { '(none: the runner started no run)' }
    # Each check on its own: a failure here must not lose the END line or last-result.txt.
    $susp = @()
    try { $after = Compare-Pins $script:Pins (Get-Pins); if ($after.Count) { $susp += "pinned files changed during the run: $($after -join '; ')" } } catch { $susp += "the pins could not be checked after the run ($($_.Exception.Message))" }
    try { $jsonNow = (Get-FileHash -LiteralPath $MPath -Algorithm SHA256).Hash; if ($jsonNow -ne $Go.sha) { $susp += "matrix json changed during the run ($jsonNow)" } } catch { $susp += "the matrix json could not be hashed after the run ($($_.Exception.Message))" }
    try { $bd = Compare-Pins $Go.bins (Get-BinHashes $Go $MPath); if ($bd.Count) { $susp += "bin files changed during the run: $($bd -join '; ')" } } catch { $susp += "the bin files could not be hashed after the run ($($_.Exception.Message))" }
    $meaning = if ($run.killed) { "stopped early: $($run.killed); the runner and everything it started were killed" } else { switch ($code) { 0 { 'all runs OK' } 1 { 'some run not OK' } 2 { 'matrix/preflight error, nothing or not all started' } default { 'unknown' } } }
    Log "window $($Go.id) END: runner exit $code ($meaning) after $mins min; out dir $outDir$(if ($susp.Count) { '; SUSPECT: ' + ($susp -join '; ') })" $(if ($code -eq 0 -and -not $susp.Count -and -not $run.killed) { 'Green' } else { 'Yellow' })
    Write-LastResult "GO       $($Go.raw)`r`nresult   runner exit $code ($meaning)`r`nstarted  $(Ts $t0)`r`nminutes  $mins`r`nout dir  $outDir`r`nrunner   $rlog`r`nkilled   $(if ($run.killed) { $run.killed } else { 'no' })`r`nsuspect  $(if ($susp.Count) { $susp -join '; ' } else { 'no (pins, matrix and bins unchanged)' })"
    if ($run.killed -eq 'STOP file') { Use-Stop "while window $($Go.id) was running"; $script:StopNow = $true }
}

# ---------- the runner process ----------
function Join-Args([string[]]$A) { return ((@($A) | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' ') }
# New complete lines of a file that a child process is writing: they go to the console and to the runner log.
function Read-Tail($T, [string]$RLog, [bool]$Final) {
    $new = ''
    if (Test-Path -LiteralPath $T.path) {
        $fs = [IO.File]::Open($T.path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]'ReadWrite, Delete')
        try {
            if ($fs.Length -gt $T.pos) {
                [void]$fs.Seek($T.pos, [IO.SeekOrigin]::Begin)
                $buf = New-Object byte[] ([int][math]::Min($fs.Length - $T.pos, 16MB))
                $n = $fs.Read($buf, 0, $buf.Length); $T.pos += $n
                $new = $T.enc.GetString($buf, 0, $n)
            }
        } finally { $fs.Dispose() }
    }
    $parts = @(($T.rest + $new) -split "`r?`n")
    $T.rest = $parts[$parts.Count - 1]
    $lines = @(if ($parts.Count -gt 1) { $parts[0..($parts.Count - 2)] })
    if ($Final -and $T.rest) { $lines += $T.rest; $T.rest = '' }
    foreach ($l in $lines) { Add-Text $RLog $l; Write-Host $l }
}
# Kills the runner's whole process tree (run-timing, the game, the drivers) and logs it. Real mode also kills a
# legodimensions from build\agent2 that started during the window in this session but is no longer in the tree.
function Stop-Tree($P, [string]$Why, [datetime]$Since) {
    $ErrorActionPreference = 'Continue'
    Log "!!! $($Why): the runner (pid $($P.Id)) and every process it started are killed now (taskkill /T /F)" 'Yellow'
    try { $o = @(& (Join-Path $env:SystemRoot 'System32\taskkill.exe') /PID $P.Id /T /F 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ }); Log "taskkill: $($o -join ' / ')" } catch { Log "!!! taskkill failed: $($_.Exception.Message)" 'Red' }
    try { if (-not $P.WaitForExit(15000)) { $P.Kill(); [void]$P.WaitForExit(5000) } } catch { }
    if (-not $DryRun) {
        $mySess = [Diagnostics.Process]::GetCurrentProcess().SessionId; $binRoot = (Join-Path $Repo 'build\agent2') + '\'
        foreach ($g in @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)) {
            try {
                $path = ''; try { $path = [string]$g.MainModule.FileName } catch { }
                if ($g.SessionId -eq $mySess -and $g.StartTime -ge $Since -and $path.StartsWith($binRoot, [StringComparison]::OrdinalIgnoreCase)) {
                    $g.Kill(); [void]$g.WaitForExit(10000); Log "killed legodimensions pid $($g.Id) ($path), left over from the window" 'Yellow'
                }
            } catch { Log "!!! could not kill legodimensions pid $($g.Id): $($_.Exception.Message)" 'Red' }
        }
    }
    $gone = $false; try { $gone = $P.HasExited } catch { }
    Log "runner stopped: $(if ($gone) { 'yes' } else { "NO, pid $($P.Id) is still running" })" $(if ($gone) { 'Gray' } else { 'Red' })
}
# Starts the runner with Start-Process (its output goes to runner-<tag>.out.txt / .err.txt and, as it comes, to this
# console and runner-<tag>.txt) and waits for it. Every second: a STOP file, or the end time + GraceMinutes passing,
# stops the window at once (Stop-Tree). If the launcher itself fails while the runner runs, the runner is stopped too:
# it never runs unwatched. Returns @{ code; killed }.
function Invoke-Runner([string]$ArgLine, [string]$RLog, [string]$Tag, [datetime]$T0) {
    $outF = Join-Path $StatusDir "runner-$Tag.out.txt"; $errF = Join-Path $StatusDir "runner-$Tag.err.txt"
    $p = Start-Process -FilePath $PsExe -ArgumentList $ArgLine -WorkingDirectory ((Get-Location -PSProvider FileSystem).ProviderPath) -NoNewWindow -PassThru -RedirectStandardOutput $outF -RedirectStandardError $errF
    [void]$p.Handle     # keeps ExitCode readable (Windows PowerShell 5.1)
    $r = @{ code = $null; killed = '' }
    $hardEnd = $script:Deadline.AddMinutes($GraceMinutes)
    Log "runner pid $($p.Id); a STOP file, or $(Ts $hardEnd) (end time + $GraceMinutes min), stops it and everything it started"
    $tails = @(@{ path = $outF; pos = [long]0; rest = ''; enc = [Console]::OutputEncoding }, @{ path = $errF; pos = [long]0; rest = ''; enc = [Console]::OutputEncoding })
    $tailErr = $false
    try {
        while ($true) {
            $done = $p.WaitForExit(1000)
            foreach ($t in $tails) { try { Read-Tail $t $RLog $done } catch { if (-not $tailErr) { $tailErr = $true; Log "!!! runner output could not be read ($($_.Exception.Message)); it is still in $outF and $errF" 'Yellow' } } }
            if ($done) { break }
            $why = ''
            if (Test-Stop) { $why = 'STOP file' } elseif ((Now) -ge $hardEnd) { $why = "end time $(Ts $script:Deadline) + $GraceMinutes min passed" }
            if ($why) {
                $r.killed = $why; Stop-Tree $p $why $T0
                foreach ($t in $tails) { try { Read-Tail $t $RLog $true } catch { } }
                break
            }
        }
    } finally {
        $alive = $false; try { $alive = -not $p.HasExited } catch { }
        if ($alive) { if (-not $r.killed) { $r.killed = 'launcher error while the runner was running' }; Stop-Tree $p $r.killed $T0 }
    }
    try { if ($p.WaitForExit(5000)) { $r.code = $p.ExitCode } } catch { }
    return $r
}
function Invoke-Go {
    $fi = Get-Item -LiteralPath $GoFile -ErrorAction SilentlyContinue
    if (-not $fi -or $fi -isnot [IO.FileInfo]) { return }
    $sig = "$($fi.LastWriteTimeUtc.Ticks)|$($fi.Length)"
    if ($script:Stuck -eq $sig) { return }    # a GO we already read but could not delete
    $t1 = $null; $t2 = $null
    try { $t1 = Read-Text $GoFile; Start-Sleep -Seconds 1; $t2 = Read-Text $GoFile } catch { Log "GO file not readable yet: $($_.Exception.Message)"; return }
    if ($t1 -cne $t2) { Log 'GO file is still being written: read again at the next poll'; return }
    $script:GoReadAt = Now
    $delErr = ''
    try { Remove-Item -LiteralPath $GoFile -Force -ErrorAction Stop; $script:Stuck = '' } catch { $script:Stuck = $sig; $delErr = $_.Exception.Message }
    $script:GoCount++
    $go = Parse-Go $t2
    # Every GO it uses is deleted: one that cannot be deleted is refused, and ignored until the file changes.
    if ($delErr) { Log "GO read: '$($go.raw)'"; Refuse $go.raw "the GO file could not be deleted ($delErr): it is not used, and it is ignored until it changes (delete it by hand)"; return }
    Log "GO read and deleted: '$($go.raw)'"
    if (-not $go.ok) { Refuse $go.raw ($go.why -join '; '); return }
    $diff = Compare-Pins $script:Pins (Get-Pins)
    if ($diff.Count) { Refuse $go.raw "pinned files changed since the start: $($diff -join '; ')"; return }
    $mPath = Join-Path $MatrixDirEff $go.json
    $why = Test-Matrix $go $mPath
    if ($why.Count) { Refuse $go.raw ($why -join '; '); return }
    $plan = Get-Plan $mPath $go
    if (-not $plan.ok) { Refuse $go.raw $plan.why; return }
    if ((Now).AddMinutes($plan.min + $DeadlineSlackMin) -gt $script:Deadline) { Refuse $go.raw "deadline: estimate $($plan.min) min + $DeadlineSlackMin min would end after $(Ts $script:Deadline)"; return }
    if ($script:GoReadAt -ge $script:LatestStart) { Refuse $go.raw "latest start: the GO was read at $(Ts $script:GoReadAt), at or after the latest window start $(Ts $script:LatestStart)"; return }
    $accepted = Now
    $wTag = "$($go.id)-$($accepted.ToString('HHmm'))"
    $script:WinLog = Join-Path $StatusDir "window-$wTag.log"
    try {
        $hw = ''
        try { $hw = Sync-Hold $go.id } catch { Refuse $go.raw "the HOLD file could not be written: $($_.Exception.Message)"; return }
        try { $go.bins = Get-BinHashes $go $mPath } catch { Refuse $go.raw "the bin files could not be hashed: $($_.Exception.Message)"; return }
        Log "GO ACCEPTED: window $($go.id): $($go.json) (sha256 ok), only=$($go.only -join ','), repeats=$($go.repeats); runner estimate $($plan.runs) runs, about $($plan.min) min" 'Green'
        Write-LastGo $go.raw "ACCEPTED at $(Ts $accepted) (estimate $($plan.runs) runs, about $($plan.min) min)"
        if ($hw) { Log "$($hw): it is not replaced, and the quiet gate fails until it is gone" 'Yellow' }
        foreach ($k in $go.bins.Keys) { Log "bin $k sha256 $($go.bins[$k])" }
        foreach ($x in (Get-MatrixWarnings $mPath)) { Log "WARN: $x" 'Yellow' }
        foreach ($l in @($plan.lines | Where-Object { $_ -match 'FUNCTIONAL ONLY' })) { Log "WARN: run-matrix.ps1 -PlanOnly says: $($l.Trim())" 'Yellow' }
        foreach ($l in $plan.lines) { Add-Text $script:WinLog "  plan| $l" }
        Close-Programs 'GO accepted'
        $r = Wait-Quiet $go $plan $accepted
        if ($r -eq 'stop') { Use-Stop 'waiting for the quiet gate'; $script:StopNow = $true; Write-LastResult "GO       $($go.raw)`r`nresult   NOT STARTED: STOP file while waiting for the quiet gate"; return }
        if ($r -ne 'start') { Refuse $go.raw $r 'GATE'; return }
        Start-Window $go $mPath $plan $wTag
    } finally {
        Clear-Hold
        $script:WinLog = $null
    }
}

# ---------- main: start checks (nothing is changed before they pass), then GO files until 07:30 or STOP ----------
function Refuse-Start([string]$Why) {
    Log "START REFUSED: $Why" 'Red'
    Set-State 'refused-at-start' @{ reason = $Why }
    Write-Host "`r`nThe launcher did not start: $Why`r`nNothing was changed. README.md explains the start checks." -ForegroundColor Red
}
$script:Deadline = $null; $script:LatestStart = $null; $script:Pins = $null; $script:GateLine = ''
$exitCode = 0; $begun = $false; $endHow = 'interrupted (Ctrl+C?) before a normal end'
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$haveMutex = $false
try { $haveMutex = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $haveMutex = $true }
if (-not $haveMutex) {
    # Another launcher owns the status files: only append to the log, do not touch its state.txt.
    $line = "$(Ts (Now)) START REFUSED (pid $PID): another launcher is already running ($MutexName); this one ends without changing anything"
    Write-Host $line -ForegroundColor Red; Add-Text $LogFile $line
    $mutex.Dispose(); exit 2
}
try {
    Log "launcher start: $(if ($DryRun) { "DRY RUN, files in $StatusDir" } else { 'REAL' }); pid $PID; PowerShell $($PSVersionTable.PSVersion); repo $Repo" 'Cyan'
    if ($usedHooks.Count) { Log "dry-run hooks: $((@($usedHooks | ForEach-Object { "-$_ $($PSBoundParameters[$_])" })) -join ' ')" 'Yellow' }
    $script:Deadline = Get-Deadline
    $script:LatestStart = Get-LatestStart
    $why = New-Object System.Collections.Generic.List[string]
    $desk = Get-DesktopName; $locked = Test-LogonUI; $pw = Get-Power
    Log "start checks: desktop '$desk'; LogonUI $(if ($locked) { 'RUNNING (locked)' } else { 'not running' }); power $($pw.text); ends at $(Ts $script:Deadline); latest window start $(Ts $script:LatestStart); a window still running at $(Ts $script:Deadline.AddMinutes($GraceMinutes)) is stopped"
    $soft = New-Object System.Collections.Generic.List[string]
    if ($desk -ine 'WinSta0\Default') { $soft.Add("this is desktop '$desk', not the user's own desktop WinSta0\Default") }
    if ($locked) { $soft.Add('the PC is locked (LogonUI is running)') }
    if (-not $pw.ac) { $soft.Add("not on AC power: $($pw.text)") }
    if ($soft.Count -and $DryRun -and $SkipStartChecks) { Log "start checks would refuse: $($soft -join '; ') (ignored: -DryRun -SkipStartChecks)" 'Yellow' }
    else { foreach ($w in $soft) { $why.Add($w) } }
    if (Test-Stop) { $why.Add("$StopFile exists: delete it first") }
    if (($script:Deadline - (Now)).TotalHours -gt $MaxRunHours) { $why.Add("it would run until $(Ts $script:Deadline), more than $MaxRunHours h from now (it is past 07:30): start it in the evening") }
    $script:Pins = Get-Pins
    $miss = @($script:Pins.Keys | Where-Object { $script:Pins[$_] -eq 'MISSING' })
    if ($miss.Count) { $why.Add("pinned file(s) missing: $($miss -join ', ')") }
    if ($why.Count) { Refuse-Start ($why -join '; '); $exitCode = 2; $endHow = 'refused at start' }
    else {
        $begun = $true
        Set-Text (Join-Path $StatusDir 'pins.txt') ("pinned $(Ts (Now)) by launcher pid $PID; any change refuses the next window`r`n" + ((@($script:Pins.Keys | ForEach-Object { "$($script:Pins[$_])  $_" })) -join "`r`n"))
        Log "pinned $($script:Pins.Count) files (status: pins.txt)"
        $left = @(Get-ChildItem Env: | Where-Object { $_.Name -match '^(REX_|LEGO_)' -and $AllowedEnv -notcontains $_.Name } | Sort-Object Name | ForEach-Object { $v = [string]$_.Value; if ($v.Length -gt 80) { $v = $v.Substring(0, 80) + '...' }; "$($_.Name)='$v'" })
        if ($left.Count) { Log "environment: other REX_*/LEGO_* variables (passed on to the runner as they are): $($left -join ', ')" 'Yellow' } else { Log 'environment: no other REX_*/LEGO_* variables' }
        foreach ($k in $AllowedEnv) { $v = [Environment]::GetEnvironmentVariable($k, 'Process'); if ($null -ne $v) { [Environment]::SetEnvironmentVariable($k, $null, 'Process'); Log "removed $k='$v' from the launcher's environment (arms set it through the matrix only)" 'Yellow' } }
        if ($DryRun) { Log 'console Quick Edit: not changed in a dry run' }
        else { $qe = 'n/a'; try { $qe = [LdNight]::NoQuickEdit() } catch { }; Log "console Quick Edit: $qe (a click in this window must not pause it)" }
        Set-ScreensaverNone
        Set-Awake $true
        Set-State 'waiting-for-go' @{ go_file = $GoFile; gos_read = 0 }
        if ((Now) -ge $script:LatestStart) { Log "!!! the latest window start $(Ts $script:LatestStart) has passed: every GO is refused; the launcher still ends at $(Ts $script:Deadline)" 'Yellow' }
        Log "waiting for $GoFile (checked every $PollSeconds s) until $(Ts $script:Deadline), or until $StopFile appears" 'Cyan'
        while ($true) {
            if (Test-Stop) { Use-Stop 'waiting for a GO'; $endHow = 'STOP file'; break }
            if ((Now) -ge $script:Deadline) { Log "it is $(Ts $script:Deadline): the launcher ends" 'Cyan'; $endHow = 'deadline'; break }
            if (Test-Path -LiteralPath $GoFile -PathType Leaf) {
                try { Invoke-Go }
                catch {
                    # One bad GO must not end the night: log it, drop it, keep waiting. (Invoke-Go's finally clears the HOLD.)
                    Log "!!! error while handling a GO (line $($_.InvocationInfo.ScriptLineNumber)): $($_.Exception.Message); this GO is dropped" 'Red'
                    Write-LastResult "result   LAUNCHER ERROR while handling a GO: $($_.Exception.Message)"
                }
                if ($script:StopNow) { $endHow = 'STOP file'; break }
                if (Test-Stop) { Use-Stop 'after a GO'; $endHow = 'STOP file'; break }
                if ($MaxGo -gt 0 -and $script:GoCount -ge $MaxGo) { Log "-MaxGo $MaxGo reached: the launcher ends"; $endHow = '-MaxGo'; break }
            }
            Set-State 'waiting-for-go' @{ go_file = $GoFile; gos_read = $script:GoCount }
            $until = (Now).AddSeconds($PollSeconds)
            while ((Now) -lt $until -and -not (Test-Stop)) { Start-Sleep -Milliseconds 500 }
        }
    }
} catch {
    $exitCode = 3; $endHow = 'launcher error'
    Log "!!! launcher error at line $($_.InvocationInfo.ScriptLineNumber): $($_.Exception.Message)" 'Red'
} finally {
    # Each step on its own, so that one failure doesn't skip the others; the screensaver first.
    Try-Step 'screensaver restore' { Restore-Screensaver }
    Try-Step 'HOLD clear' { Clear-Hold }
    Try-Step 'keep-awake release' { Set-Awake $false }
    $script:WinLog = $null
    Try-Step 'state' { if ($begun -or $exitCode -eq 3) { Set-State 'ended' @{ exit = $exitCode; how = $endHow } } }
    if ($haveMutex) { try { $mutex.ReleaseMutex() } catch { } }
    $mutex.Dispose()
}
Log "launcher end: $endHow, exit $exitCode"
exit $exitCode
