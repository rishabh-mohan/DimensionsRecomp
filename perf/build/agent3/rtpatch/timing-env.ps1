# Timing-validity helpers, dot-sourced by run-timing.ps1 and run-matrix.ps1 (kept out of common.ps1).
#   Get-DesktopName   "WinSta0\Default" on the interactive desktop; agent run_command sessions give WinSta0\exebox-*
#   Test-LogonUI      LogonUI.exe running (lock screen / logon UI up)
#   Get-BuildProcs    running build / codegen tools as "name:pid" (patterns: Get-BuildProcPatternText; clangd not counted)
#   Get-TimingEnv     the three above in one ordered dictionary
#   Get-PowerInfo     AC or battery (Win32_Battery)
if (-not ('LdDesk' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class LdDesk {
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint threadId);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] static extern IntPtr GetProcessWindowStation();
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool GetUserObjectInformationW(IntPtr hObj, int nIndex, StringBuilder pvInfo, int nLength, out int lpnLengthNeeded);
    static string Name(IntPtr h) {
        if (h == IntPtr.Zero) return null;
        var sb = new StringBuilder(256); int need;
        return GetUserObjectInformationW(h, 2, sb, sb.Capacity * 2, out need) ? sb.ToString() : null;   // 2 = UOI_NAME
    }
    public static string Desktop() { return Name(GetThreadDesktop(GetCurrentThreadId())); }
    public static string Station() { return Name(GetProcessWindowStation()); }
}
'@
}
function Get-DesktopName { try { return "$([LdDesk]::Station())\$([LdDesk]::Desktop())" } catch { return '?' } }
function Test-TimingDesktop([string]$Name) { return $Name -like '*\Default' }
function Test-LogonUI { return [bool](Get-Process -Name LogonUI -ErrorAction SilentlyContinue) }
# Build / codegen tools whose CPU use makes a timing run invalid, matched on the process name (no .exe), any case.
# S3 rule (Agent 1, 02:15): the old fixed list missed tools; wildcards now cover clang++ / clang-scan-deps, every lld
# and llvm-* tool, rexglue* and Agent 2's codegen-frozen / codegen-frozen2. Not counted: clangd (the VS Code C++
# language server stays up all day) and clang-format (format-on-save, well under a second).
function Get-BuildProcRegex {
    return @('^(clang.*|lld.*|ld\.lld.*|llvm-.*|ninja.*|cmake.*|dxc.*|cl|link|lib|mt|rc|msbuild.*|rexglue.*|codegen.*|sccache.*|ccache.*|rustc|cargo)$',
             '^(clangd.*|clang-format.*)$')
}
function Get-BuildProcPatternText { return 'clang* (not clangd/clang-format), lld*, ld.lld, llvm-*, ninja, cmake, dxc*, cl, link, lib, mt, rc, msbuild, rexglue*, codegen*, sccache, ccache, rustc, cargo' }
function Test-BuildProcName([string]$Name) { $r = Get-BuildProcRegex; return ($Name -match $r[0]) -and ($Name -notmatch $r[1]) }
function Get-BuildProcs {
    # foreach over one process snapshot (~3x faster than a Where-Object pipeline; this runs at the window marks)
    $r = Get-BuildProcRegex; $inc = $r[0]; $exc = $r[1]
    $hits = foreach ($p in [Diagnostics.Process]::GetProcesses()) { $n = $p.ProcessName; if ($n -match $inc -and $n -notmatch $exc) { $p } }
    return @($hits | Sort-Object ProcessName, Id | ForEach-Object { "$($_.ProcessName):$($_.Id)" })
}
function Get-TimingEnv {
    $b = @(Get-BuildProcs)
    return [ordered]@{ desktop = (Get-DesktopName); logonui = (Test-LogonUI); build_procs = $b; build_proc_count = $b.Count
                       wall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff') }
}
function Get-PowerInfo {
    $bat = @(Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue)
    if ($bat.Count -eq 0) { return [ordered]@{ ac = $true; text = 'AC (no battery: desktop PC)' } }
    $st = [int]$bat[0].BatteryStatus; $ch = $bat[0].EstimatedChargeRemaining
    # BatteryStatus: 1 discharging, 2 on AC, 3 full, 4/5 low/critical, 6-9 charging, 11 partially charged
    $ac = @(2, 3, 6, 7, 8, 9, 11) -contains $st
    return [ordered]@{ ac = $ac; text = "$(if ($ac) { 'AC' } else { 'ON BATTERY' }) (Win32_Battery status $st, charge $ch %)" }
}

# Close with WM_CLOSE (needs [LdHarness] from winhelper.cs: Import-LdHelper) and wait up to TimeoutSec. Any exit
# after WM_CLOSE counts as a clean close: the real game logs 'hard-exiting' 0.3 s after WM_CLOSE, but its process
# can take ~33 s to terminate (ExitProcess teardown), hence the 60 s default. Only after the timeout: Kill. A failed
# Kill (access denied while the process is already terminating) is kept in kill_error, and the exit is then
# awaited for 60 s more. Same fields as Close-Game in common.ps1, plus post time, exit_seen_s, kill_error, exited, clean.
function Close-GameTimed {
    param([Parameter(Mandatory = $true)]$P, [int]$TimeoutSec = 60)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $posted = 0; $postS = $null; $postWall = $null; $repostS = $null
    if (-not $P.HasExited) {
        $posted = [LdHarness]::CloseAll($P.Id); $postS = [math]::Round($sw.Elapsed.TotalSeconds, 3)
        $postWall = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    }
    $exited = $P.WaitForExit(5000)
    if (-not $exited -and $posted -eq 0) { $posted = [LdHarness]::CloseAll($P.Id); $repostS = [math]::Round($sw.Elapsed.TotalSeconds, 2) }
    if (-not $exited) { $exited = $P.WaitForExit([math]::Max(0, $TimeoutSec * 1000 - 5000)) }
    $exitSeen = if ($exited) { [math]::Round($sw.Elapsed.TotalSeconds, 2) } else { $null }
    $killed = $false; $killErr = $null; $killAt = $null
    if (-not $exited) {
        $killAt = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        try { $P.Kill(); $killed = $true } catch { $killErr = $_.Exception.Message }
        if ($P.WaitForExit(60000)) { $exitSeen = [math]::Round($sw.Elapsed.TotalSeconds, 2) }
    }
    $isGone = $false; try { $isGone = $P.HasExited } catch { }
    $code = $null
    if ($isGone) { try { $code = $P.ExitCode } catch { } }
    return [pscustomobject]@{
        wm_close_posted = $posted; wm_close_post_s = $postS; wm_close_post_wall = $postWall; wm_close_repost_s = $repostS
        exit_wait_s = [math]::Round($sw.Elapsed.TotalSeconds, 2); exit_seen_s = $exitSeen; timeout_s = $TimeoutSec
        killed = $killed; kill_at_s = $killAt; kill_error = $killErr; exited = $isGone
        clean = ($posted -gt 0 -and -not $killed -and $isGone)
        exit_code = $code
        exit_code_hex = $(if ($null -ne $code) { '0x{0:X8}' -f ([int64]$code -band 0xFFFFFFFFL) } else { $null })
    }
}
