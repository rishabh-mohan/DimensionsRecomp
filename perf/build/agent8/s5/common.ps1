# Shared helpers for Agent 8's game runners (task #16): first-boot.ps1 and the timing runner.
# Dot-source:  . "$PSScriptRoot\common.ps1"
# Windows PowerShell 5.1 compatible. Never writes to harness/ or game/.
Set-StrictMode -Version 2

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path

function Resolve-RepoPath([string]$Path) {
    if ([IO.Path]::IsPathRooted($Path)) { return $Path }
    return (Join-Path $script:RepoRoot $Path)
}

# winhelper.cs is a read-only snapshot of Agent 3's harness/winhelper.cs (window list, WM_CLOSE, hardlink).
function Import-LdHelper {
    if (-not ('LdHarness' -as [type])) {
        Add-Type -Path (Join-Path $PSScriptRoot 'winhelper.cs') -ReferencedAssemblies System.Drawing
    }
}

$script:Inv = [Globalization.CultureInfo]::InvariantCulture
function Fmt([double]$Value, [int]$Digits) { return $Value.ToString('F' + $Digits, $script:Inv) }

$script:CompInfo = $null
function Get-FreeRamGB {
    if ($null -eq $script:CompInfo) {
        Add-Type -AssemblyName Microsoft.VisualBasic
        $script:CompInfo = New-Object Microsoft.VisualBasic.Devices.ComputerInfo
    }
    return [math]::Round($script:CompInfo.AvailablePhysicalMemory / 1GB, 2)
}

# Mirrors the files listed in <BinDir>\MANIFEST.txt into <RunsRoot>\<HHmm>-<Tag>[-rN].
# .exe/.dll/.map are hardlinked (same volume), everything else is copied. Sizes are checked
# against the manifest. Returns the run dir.
function New-RunDir {
    param([Parameter(Mandatory = $true)][string]$BinDir,
          [Parameter(Mandatory = $true)][string]$Tag,
          [string]$RunsRoot = 'build\agent8\runs')
    Import-LdHelper
    $bin = (Resolve-Path (Resolve-RepoPath $BinDir)).Path
    $manifest = Join-Path $bin 'MANIFEST.txt'
    if (-not (Test-Path -LiteralPath $manifest)) { throw "no MANIFEST.txt in $bin" }
    $entries = @()
    foreach ($line in Get-Content -LiteralPath $manifest) {
        if (-not $line -or $line.StartsWith('#')) { continue }
        $f = $line -split "`t"
        $entries += [pscustomobject]@{ Name = $f[0]; Size = [int64]$f[1] }
    }
    if ($entries.Count -eq 0) { throw "MANIFEST.txt in $bin lists no files" }
    $root = Resolve-RepoPath $RunsRoot
    $base = Join-Path $root ((Get-Date -Format 'HHmm') + '-' + $Tag)
    $run = $base
    $i = 2
    while (Test-Path -LiteralPath $run) { $run = "$base-r$i"; $i++ }
    New-Item -ItemType Directory -Force -Path $run | Out-Null
    foreach ($e in $entries) {
        $src = Join-Path $bin $e.Name
        $dst = Join-Path $run $e.Name
        if (-not (Test-Path -LiteralPath $src)) { throw "missing $src" }
        $len = (Get-Item -LiteralPath $src).Length
        if ($len -ne $e.Size) { throw "size mismatch for $($e.Name): $len vs manifest $($e.Size)" }
        $linked = $false
        if ($e.Name -match '\.(exe|dll|map)$') { $linked = [LdHarness]::HardLink($dst, $src) }
        if (-not $linked) { Copy-Item -LiteralPath $src -Destination $dst }
    }
    Copy-Item -LiteralPath $manifest -Destination (Join-Path $run 'MANIFEST.txt')
    return $run
}

# Copies harness/legodimensions.toml next to the exe with user_data_root = <run>\user.
# -Set adds or replaces top-level keys (values are raw TOML, e.g. @{ framerate_limit = '0' }).
# game_data_root and update_data_root are left as they are (game/disc, game/tu23, read-only).
function Write-RunToml {
    param([Parameter(Mandatory = $true)][string]$Run, [hashtable]$Set = @{})
    $src = Join-Path $script:RepoRoot 'harness\legodimensions.toml'
    $text = [IO.File]::ReadAllText($src)
    $user = Join-Path $Run 'user'
    New-Item -ItemType Directory -Force -Path $user | Out-Null
    $kv = [ordered]@{ user_data_root = "'$user'" }
    foreach ($k in $Set.Keys) { $kv[$k] = [string]$Set[$k] }
    foreach ($k in $kv.Keys) {
        $pattern = '(?m)^' + [regex]::Escape($k) + '[ \t]*=[^\r\n]*'
        $line = "$k = " + $kv[$k]
        if ([regex]::IsMatch($text, $pattern)) {
            $text = [regex]::Replace($text, $pattern, $line.Replace('$', '$$'))
        } else {
            $text = $text.TrimEnd() + "`n" + $line + "`n"
        }
    }
    [IO.File]::WriteAllText((Join-Path $Run 'legodimensions.toml'), $text, (New-Object Text.UTF8Encoding $false))
    Copy-Item -LiteralPath $src -Destination (Join-Path $Run 'legodimensions.toml.orig')
}

# The verified first-boot flags; -Cvar adds name=value pairs as --name=value.
function Get-GameArgs {
    param([Parameter(Mandatory = $true)][string]$Run, [string[]]$Cvar = @())
    $a = @("--log_file=$(Join-Path $Run 'game.log')",
           "--perf_log_csv=$(Join-Path $Run 'perf.csv')",
           '--native_settings_load=false', '--discord_rpc=false', '--audio_mute=true',
           '--pause_when_unfocused=false')
    foreach ($c in $Cvar) { if ($c) { $a += ('--' + $c.TrimStart('-')) } }
    return , $a
}

# Starts the game from the run dir. LEGO_SAMPLE_PROFILE* are removed unless -Env sets them,
# so the profiler is OFF by default.
function Start-Game {
    param([Parameter(Mandatory = $true)][string]$Run,
          [Parameter(Mandatory = $true)][string[]]$GameArgs,
          [hashtable]$Env = @{})
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = Join-Path $Run 'legodimensions.exe'
    $psi.Arguments = (($GameArgs | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' ')
    $psi.WorkingDirectory = $Run
    $psi.UseShellExecute = $false
    foreach ($k in @('LEGO_SAMPLE_PROFILE', 'LEGO_SAMPLE_PROFILE_TRIGGER')) {
        if ($psi.EnvironmentVariables.ContainsKey($k)) { $psi.EnvironmentVariables.Remove($k) }
    }
    foreach ($k in $Env.Keys) { $psi.EnvironmentVariables[$k] = [string]$Env[$k] }
    return [System.Diagnostics.Process]::Start($psi)
}

# Incremental line counter for a file another process keeps open (game.log, perf.csv).
function New-LineCounter([string]$Path) { return @{ Path = $Path; Offset = [int64]0; Lines = [int64]0; Bytes = [int64]0 } }
function Update-LineCounter([hashtable]$S) {
    if (-not (Test-Path -LiteralPath $S.Path)) { return }
    try {
        $fs = [IO.File]::Open($S.Path, [IO.FileMode]::Open, [IO.FileAccess]::Read,
                              ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        try {
            if ($fs.Length -lt $S.Offset) { $S.Offset = 0; $S.Lines = 0 }
            [void]$fs.Seek($S.Offset, [IO.SeekOrigin]::Begin)
            $buf = New-Object byte[] 1048576
            while (($n = $fs.Read($buf, 0, $buf.Length)) -gt 0) {
                $chunk = [Text.Encoding]::ASCII.GetString($buf, 0, $n)
                $S.Lines += ($chunk.Length - $chunk.Replace("`n", '').Length)
                $S.Offset += $n
            }
            $S.Bytes = $S.Offset
        } finally { $fs.Dispose() }
    } catch { }
}

# One process sample. Commit = private bytes (PagefileUsage).
function Get-ProcSample($P) {
    $P.Refresh()
    # Counters first, Responding last: Responding is a SendMessageTimeout (up to 5 s) and read first it skewed
    # cpu_s against the sample's time stamp (run 1928-first, t=3 s: 16 "cores" on a 12-CPU machine).
    $o = [pscustomobject]@{
        cpu_s = $P.TotalProcessorTime.TotalSeconds
        ws = $P.WorkingSet64; peak_ws = $P.PeakWorkingSet64
        commit = $P.PrivateMemorySize64; peak_commit = $P.PeakPagedMemorySize64
        threads = $P.Threads.Count; handles = $P.HandleCount; responding = $null
    }
    try { $o.responding = $P.Responding } catch { }
    return $o
}

# WerFault processes reporting on this pid ("-p <pid>"). Process list first, WMI only when a WerFault exists: the
# WMI query costs ~1 s (03:25, 1051-2140 ms) and in window 3 (20261122-0013) it blocked the runner for 35-61 s at
# a time on every 5th tick (0018-d0-r1: 46, 40 and 50 s in the window), which made the matrix 63 min, not 49.
function Get-WerFor([int]$GamePid) {
    $ids = New-Object System.Collections.Generic.List[int]
    foreach ($n in 'WerFault', 'WerFaultSecure') {
        foreach ($wp in [Diagnostics.Process]::GetProcessesByName($n)) { $ids.Add($wp.Id); $wp.Dispose() }
    }
    if ($ids.Count -eq 0) { return @() }
    $flt = (@($ids | ForEach-Object { "ProcessId=$_" }) -join ' OR ')
    $w = @(Get-CimInstance Win32_Process -Filter $flt -OperationTimeoutSec 5 -ErrorAction SilentlyContinue |
           Where-Object { $_.CommandLine -match ("-p\s+" + $GamePid + "(\s|$)") })
    return $w
}

# WM_CLOSE to every visible top-level window (retried once at 5 s if none was found),
# then Kill after TimeoutSec.
function Close-Game {
    param([Parameter(Mandatory = $true)]$P, [int]$TimeoutSec = 30)
    Import-LdHelper
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $posted = 0
    if (-not $P.HasExited) { $posted = [LdHarness]::CloseAll($P.Id) }
    $exited = $P.WaitForExit(5000)
    if (-not $exited -and $posted -eq 0) { $posted = [LdHarness]::CloseAll($P.Id) }
    if (-not $exited) { $exited = $P.WaitForExit([math]::Max(0, $TimeoutSec * 1000 - 5000)) }
    $killed = $false
    if (-not $exited) {
        try { $P.Kill(); $killed = $true } catch { }
        [void]$P.WaitForExit(15000)
    }
    $code = $null
    try { $code = $P.ExitCode } catch { }
    return [pscustomobject]@{
        wm_close_posted = $posted; exit_wait_s = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        killed = $killed; exit_code = $code
        exit_code_hex = $(if ($null -ne $code) { '0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL) } else { $null })
    }
}

# Copies dumps (CrashDumps, run dir tree) and WER reports newer than $Since into the run dir,
# and writes Application-log events that mention legodimensions to events.txt.
function Save-CrashArtifacts {
    param([Parameter(Mandatory = $true)][string]$Run, [Parameter(Mandatory = $true)][datetime]$Since)
    $found = @()
    $dirs = @((Join-Path $env:LOCALAPPDATA 'CrashDumps'), $Run)
    foreach ($d in $dirs) {
        if (-not (Test-Path -LiteralPath $d)) { continue }
        foreach ($f in @(Get-ChildItem -LiteralPath $d -Recurse -Filter *.dmp -ErrorAction SilentlyContinue |
                         Where-Object { $_.LastWriteTime -ge $Since })) {
            if ($f.DirectoryName -ne $Run) { Copy-Item -LiteralPath $f.FullName -Destination $Run }
            $found += $f.FullName
        }
    }
    $wer = @((Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportArchive'),
             (Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportQueue'),
             (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\WER\ReportArchive'),
             (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\WER\ReportQueue'))
    foreach ($d in $wer) {
        if (-not (Test-Path -LiteralPath $d)) { continue }
        foreach ($r in @(Get-ChildItem -LiteralPath $d -Directory -ErrorAction SilentlyContinue |
                         Where-Object { $_.Name -like '*legodimensions*' -and $_.LastWriteTime -ge $Since })) {
            Copy-Item -LiteralPath $r.FullName -Destination (Join-Path $Run ('wer-' + $r.Name)) -Recurse
            $found += $r.FullName
        }
    }
    try {
        $ev = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; StartTime = $Since } -ErrorAction Stop |
                Where-Object { $_.Message -match 'legodimensions' })
        if ($ev.Count -gt 0) {
            $ev | Format-List TimeCreated, ProviderName, Id, LevelDisplayName, Message | Out-String -Width 4096 |
                Set-Content -LiteralPath (Join-Path $Run 'events.txt') -Encoding utf8
            $found += "events.txt ($($ev.Count) events)"
        }
    } catch { }
    return , $found
}
