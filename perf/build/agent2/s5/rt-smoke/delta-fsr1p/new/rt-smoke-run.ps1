# rt-smoke-run.ps1 - S5 Phase 3 T2/F3 smoke on the two rexruntime test bins (M2), modelled on nops-smoke-run.ps1.
# One approval (RUN-RT-SMOKE.cmd) runs three FUNCTIONAL arms back to back (untimed: no perf verdicts, M10 P1/P2),
# harness\run-game.ps1 -Seconds 240 -GpuLog, attract-long.txt virtual-pad route, WM_CLOSE at 240 s (run-game closes
# only the game it started). Default order T2 F3A F3B:
#   T2   build\agent2\s5\devs5toml-bin    (MANIFEST pin 87DF5ED9, rt-bin/BIN-PINS-devs5toml.md)  harness toml,
#        -Cvar framerate_limit=60 (= the toml value; the devfinal2 refs ran with it). P1: one
#        "Config: present_effect = 'fsr' ... rejected (allowed: bilinear)" line, no new ERROR vs devfinal2.
#   F3A  build\agent2\s5\natives5fsr1p-bin (MANIFEST pin 15A92E4D, rt-bin/BIN-PINS-natives5fsr1p.md) harness toml
#        (present_effect='fsr'), -Cvar native_fps_limit=60 (as the nativefinal2 refs). P4: spatial_fsr_presented=1.
#   F3B  natives5fsr1p-bin with -Toml perf-bilinear.toml (sha256 pin $bilPin, F1: the harness toml with
#        present_effect='bilinear'), -Cvar native_fps_limit=60. P4: spatial_fsr_presented=0.
# Then rt_smoke_post.py (per-arm gates + FSR1-vs-bilinear side-by-side PNGs, in rt-smoke\post). Words (any order):
# dryrun, allowhidden, arms=T2,F3A,F3B (subset/order), noshots (no kit shots at all: no shot job, nothing on screen
# from the kit; for a matched manual capture. The post's two screenshot gates then FAIL by design).
#   shots   F3A F3B: a background job PNGs the game window (harness winhelper Shot, read-only) at 60 120 146 200 s
#           after the game process starts, into <run>\kit-shots\ (+ shots.txt). Same times in both arms, so the
#           post can pair them (FSR 1 left, bilinear right). T2 takes none. Only a game whose image is under the
#           kit's runs root is shot.
#   cold    every arm gets a fresh run dir; the kit never passes -UserDir or -SeedXenos.
#   dryrun  no game: verify-bins + preconditions (reported, not enforced), the real command lines, run-game -DryRun
#           for each arm (into rt-smoke\dryrun-runs, deleted afterwards), shot-job and hold-watch self-tests,
#           rt_smoke_post.py --selftest on reference runs (known values must come out). Exit 0 = commands OK.
# Real run: refuses (exit 3) on verify-bins FAIL / a MANIFEST not its pin / perf-bilinear.toml not its pin,
# WINDOW-HOLD.txt, WINDOW-GO.txt, a timed-window kit script running, day launcher state of waiting-for-quiet/running,
# a running game, an Agent 8 runner, or a hidden desktop; the same guards are re-checked before every arm. During an
# arm a hold watch polls WINDOW-HOLD.txt (2 s) and closes our game (image under the runs root) if it appears. After
# every arm: verify-bins + MANIFEST = pin on that arm's bin (hard-linked into the run dirs; a FAIL stops the kit and
# invalidates the results). try/finally cleanup stops our jobs, our game and our run-game only. Stops after an arm
# with exit != 0.
$ErrorActionPreference = 'Stop'
$words = @($args | ForEach-Object { "$_".ToLower().TrimStart('-') })
$DryRun = $words -contains 'dryrun'; $AllowHidden = $words -contains 'allowhidden'
$kit = $PSScriptRoot
$ws = (Resolve-Path (Join-Path $kit '..\..\..')).Path
$rg = Join-Path $ws 'harness\run-game.ps1'
$route = Join-Path $ws 'harness\routes\attract-long.txt'
$vb = Join-Path $ws 'build\agent2\session3\verify-bins.py'
$post = Join-Path $kit 'rt_smoke_post.py'
$out = Join-Path $kit 'rt-smoke'
$runsRoot = Join-Path $out $(if ($DryRun) { 'dryrun-runs' } else { 'runs' })
$Seconds = 240
$binToml = Join-Path $ws 'build\agent2\s5\devs5toml-bin'
$binFsr1 = Join-Path $ws 'build\agent2\s5\natives5fsr1p-bin'
$pins = @{   # MANIFEST.txt sha256 (rt-bin/BIN-PINS-devs5toml.md, rt-bin/BIN-PINS-natives5fsr1p.md)
    $binToml = '87DF5ED9E863ED773F2EFD545B906CB527FB6AA36653722F790AC19FF5E78702'
    $binFsr1 = '15A92E4DBFD634FC028DEE90DD8D18B77F90157A58E87E04FB7DFBB4A8BEAD90' }
$bilToml = Join-Path $ws 'build\agent2\s5\native-fsr1\perf-bilinear.toml'
$bilPin = 'FA47B1E31787B24D04B59E15F26D8B2ADFFC456B38E7DE24A2B5F80F24375B16'   # F1 (M10 P2)
New-Item -ItemType Directory -Force -Path (Join-Path $out 'logs'), (Join-Path $out 'post') | Out-Null
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$log = Join-Path $out "logs\rt-smoke-run-$(if ($DryRun) { 'dryrun-' })$stamp.txt"
function Say([string]$s) { $l = "[rt-smoke $(Get-Date -Format HH:mm:ss)] $s"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
$all = [ordered]@{
    T2 = [pscustomobject]@{ bin = $binToml; toml = ''; cvar = 'framerate_limit=60' }
    F3A = [pscustomobject]@{ bin = $binFsr1; toml = ''; cvar = 'native_fps_limit=60' }
    F3B = [pscustomobject]@{ bin = $binFsr1; toml = $bilToml; cvar = 'native_fps_limit=60' } }
$ShotArms = @(if ($words -notcontains 'noshots') { 'F3A'; 'F3B' }); $ShotTimes = @(60, 120, 146, 200)
$sel = @($words | Where-Object { $_ -like 'arms=*' } | ForEach-Object { $_.Substring(5).ToUpper() -split ',' } | Where-Object { $_ })
if (-not $sel.Count) { $sel = @($all.Keys) }
$bad = @($sel | Where-Object { -not $all.Contains($_) })
if ($bad.Count) { Write-Host "unknown arm(s): $($bad -join ',') (known: $($all.Keys -join ','))"; exit 2 }
$arms = @($sel | ForEach-Object { [pscustomobject]@{ arm = $_; tag = "s5rt-$($_.ToLower())"; bin = $all[$_].bin; toml = $all[$_].toml; cvar = $all[$_].cvar } })
$bins = @($arms | ForEach-Object { $_.bin } | Select-Object -Unique)
Say "S5 RT-SMOKE kit $(if ($DryRun) { 'DRY RUN (no game)' } else { 'REAL RUN' }); order $(($arms | ForEach-Object { $_.arm }) -join ' '); -Seconds $Seconds each; FUNCTIONAL, untimed (M10 P1/P2)"
Say "WS $ws"
Say "bins $($bins -join ' | '); shots $(if ($ShotArms.Count) { "in $($ShotArms -join ' ') at $($ShotTimes -join ' ') s" } else { 'NONE (noshots: manual capture)' }); fresh run dir per arm (no -UserDir/-SeedXenos)"

function Run-Logged([string]$exe, [string[]]$argv) {
    $ErrorActionPreference = 'Continue'   # native stderr through 2>&1 must not throw (PS 5.1)
    & $exe @argv 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -LiteralPath $log -Value $l }
    $LASTEXITCODE
}

# --- preconditions ---
$fail = @(); $refuse = @()
foreach ($p in @($rg, $route, $vb, $post, $bilToml, (Join-Path $ws 'build\agent2\final\check-defaults.py'), (Join-Path $ws 'harness\runstats.py'))) {
    if (-not (Test-Path -LiteralPath $p)) { $fail += "missing $p" }
}
if ($fail.Count) { $fail | ForEach-Object { Say "FAIL $_" }; exit 2 }
$bh = (Get-FileHash -LiteralPath $bilToml -Algorithm SHA256).Hash
Say "perf-bilinear.toml sha256 $($bh.Substring(0,16)) $(if ($bh -eq $bilPin) { '= pin (F1)' } else { 'NOT the pin ' + $bilPin })"
if ($bh -ne $bilPin) { $refuse += 'perf-bilinear.toml sha256 is not the pin' }
foreach ($b in $bins) {
    if (-not (Test-Path -LiteralPath (Join-Path $b 'MANIFEST.txt'))) { $refuse += "bin not staged: $b\MANIFEST.txt missing"; continue }
    $rc = Run-Logged 'python' @('-B', $vb, $b)
    if ($rc -ne 0) { $refuse += "verify-bins FAIL for $b (exit $rc)" }
    $ms = (Get-FileHash -LiteralPath (Join-Path $b 'MANIFEST.txt') -Algorithm SHA256).Hash
    Say "MANIFEST sha256 $($ms.Substring(0,16)) $(if ($ms -eq $pins[$b]) { '= pin' } else { 'NOT the pin ' + $pins[$b] }) ($b)"
    if ($ms -ne $pins[$b]) { $refuse += "MANIFEST sha256 of $b is not the pin" }
}
$hold = Join-Path $ws 'perf-notes\WINDOW-HOLD.txt'
$go = Join-Path $ws 'perf-notes\WINDOW-GO.txt'
$stateFile = Join-Path $ws 'bench\agent5\day\status\state.txt'
if (Test-Path -LiteralPath $stateFile) { Say "day launcher: $((Get-Content -LiteralPath $stateFile -TotalCount 1))" }
. (Join-Path $ws 'harness\guard.ps1')
Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
$desk = [LdHarness]::DesktopName()
Say "desktop $desk $(if ($desk -eq 'Default') { '(interactive: visible)' } else { '(hidden: not visible to the user)' })"
function Get-Refusals {
    # checked at the start and again before every arm (as the nops kit: + WINDOW-GO and the timed-window kits)
    $r = @()
    if (Test-Path -LiteralPath $hold) { $r += "WINDOW-HOLD.txt present: $((Get-Content -LiteralPath $hold -TotalCount 1))" }
    if (Test-Path -LiteralPath $go) { $r += "WINDOW-GO.txt present: $((Get-Content -LiteralPath $go -TotalCount 1))" }
    if (Test-Path -LiteralPath $stateFile) {
        $st = (Get-Content -LiteralPath $stateFile -TotalCount 1)
        if ($st -match '(?i)waiting-for-quiet|\brunning\b') { $r += "day launcher busy ($st)" }
    }
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
    if ($g.Count) { $r += "a game is running (pid $(($g | ForEach-Object Id) -join ','))" }
    $runners = @(Get-ActiveRunners)
    if ($runners.Count) { $r += "Agent 8 runner active: $($runners -join '; ')" }
    # The timed-window kit scripts only in the form M3 launches them (M10 D1 v2): powershell/pwsh with -File <path to the
    # window or matrix .ps1>, or cmd.exe running the window .cmd. A grep/editor/python command line that merely contains
    # the full path does not refuse the kit.
    $win = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $_.ProcessId -ne $PID -and $_.Name -match '^(?i)(powershell|pwsh|cmd)\.exe$' -and (
                $_.CommandLine -match '(?i)-File\s+"?[^"]*(window-s5|run-matrix)\.ps1' -or
                ($_.Name -ieq 'cmd.exe' -and $_.CommandLine -match '(?i)RUN-WINDOW-S5[^\s"]*\.cmd')) })
    if ($win.Count) { $r += "timed-window kit running (pid $(($win | ForEach-Object ProcessId) -join ','))" }
    if ($desk -ne 'Default' -and -not $AllowHidden) { $r += "not on the interactive desktop ($desk)" }
    $r
}
$refuse += @(Get-Refusals)
if ($refuse.Count) {
    $refuse | ForEach-Object { Say "$(if ($DryRun) { 'note (a real run would refuse)' } else { 'REFUSED' }): $_" }
    if (-not $DryRun) { exit 3 }
}

$rgArgs = { param($a, $root, $dry)
    $x = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $rg, '-BinDir', $a.bin, '-Seconds', "$Seconds", '-GpuLog', '-Tag', $a.tag, '-RunsRoot', $root, '-InputScript', $route)
    if ($a.toml) { $x += @('-Toml', $a.toml) }
    if ($a.cvar) { $x += @('-Cvar', $a.cvar) }
    if ($dry) { $x += '-DryRun' }; $x }
function Cmd-Line($a, [string]$root) { 'powershell ' + ((& $rgArgs $a $root $false | ForEach-Object { if ("$_" -match '[\s;]') { "`"$_`"" } else { "$_" } }) -join ' ') }

# Screenshot job: waits for a legodimensions process started after $t0 whose image lives under $runsRoot (run-game
# hard-links the exe into the run dir; never a foreign game), then PNGs its window at the given seconds after its
# start into <its run dir>\kit-shots\. Read-only: it never closes, focuses or sends input to anything.
# Screen-copy fallback (M10 delta): the native present (flip model, tearing) gives PrintWindow a black client, and
# winhelper's IsBlack is fooled by the title bar and the fps counter. So the job measures the client non-black share
# itself; under 5% and with the game window in front, it also copies that window rect from the screen into
# shot-NNNs-screen.png (nothing covers it then). The post picks per time by pixels (>= 2% non-black), not by label.
# Overlay delta (M10 re-rate): a foreground flip/tearing window that nothing overlaps gets independent flip, so a plain
# screen copy is black too (20261126-022923 run). For the screen copy only, the job shows a click-through, no-activate,
# topmost layered window at alpha 1/255 over the game window rect for ~0.5 s (forces DWM composition, as computer-cli's
# red border does), copies the rect, then destroys it. Game keeps foreground; checked before and after the copy.
$shotJob = { param($ws, $t0, $times, $timeout, $runsRoot)
    Add-Type -Path (Join-Path $ws 'harness\winhelper.cs') -ReferencedAssemblies System.Drawing
    Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class LdKitCap
{
    [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] struct MSG { public IntPtr hwnd; public uint message; public IntPtr wParam, lParam; public uint time; public int x, y; }
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr CreateWindowExW(uint ex, string cls, string name, uint style, int x, int y, int w, int h, IntPtr parent, IntPtr menu, IntPtr inst, IntPtr param);
    [DllImport("user32.dll")] static extern bool SetLayeredWindowAttributes(IntPtr h, uint key, byte alpha, uint flags);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] static extern bool DestroyWindow(IntPtr h);
    [DllImport("user32.dll")] static extern bool PeekMessageW(out MSG m, IntPtr h, uint a, uint b, uint remove);
    [DllImport("user32.dll")] static extern bool TranslateMessage(ref MSG m);
    [DllImport("user32.dll")] static extern IntPtr DispatchMessageW(ref MSG m);
    // WS_EX_LAYERED | WS_EX_TRANSPARENT (click-through) | WS_EX_TOPMOST | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW; WS_POPUP
    const uint OV_EX = 0x80000 | 0x20 | 0x8 | 0x08000000 | 0x80, OV_STYLE = 0x80000000;
    public static int SettleMs = 500;  // ~30 frames at 60 fps for DWM to leave independent flip
    static void Pump(int ms)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew(); MSG m;
        while (sw.ElapsedMilliseconds < ms)
        {
            while (PeekMessageW(out m, IntPtr.Zero, 0, 0, 1)) { TranslateMessage(ref m); DispatchMessageW(ref m); }
            System.Threading.Thread.Sleep(10);
        }
    }
    // share of a 96x96 sample grid below the title bar with R+G+B > 24
    public static double NonBlack(string path)
    {
        using (var b = new Bitmap(path))
        {
            int y0 = Math.Min(40, b.Height / 4), h = b.Height - y0, n = 0;
            for (int y = 0; y < 96; y++)
                for (int x = 0; x < 96; x++)
                {
                    Color c = b.GetPixel(b.Width * x / 96 + b.Width / 192, y0 + h * y / 96 + h / 192);
                    if (c.R + c.G + c.B > 24) n++;
                }
            return n / (96.0 * 96.0);
        }
    }
    // copy the foreground window's rect from the screen; only if h is the foreground window (then nothing opaque covers
    // it). A click-through, no-activate alpha-1/255 overlay over the rect forces DWM composition during the copy.
    public static string ScreenCopy(IntPtr h, string path)
    {
        if (h == IntPtr.Zero) return "no window";
        if (GetForegroundWindow() != h) return "not in front (no screen copy)";
        RECT r;
        if (!GetWindowRect(h, out r)) return "no window rect";
        int w = r.R - r.L, ht = r.B - r.T;
        if (w <= 0 || ht <= 0) return "empty window";
        IntPtr ov = CreateWindowExW(OV_EX, "STATIC", "ld-kit-compose", OV_STYLE, r.L, r.T, w, ht, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
        if (ov == IntPtr.Zero) return "no overlay window (no screen copy)";
        try
        {
            SetLayeredWindowAttributes(ov, 0, 1, 2);  // LWA_ALPHA, alpha 1/255
            ShowWindow(ov, 4);                        // SW_SHOWNOACTIVATE
            Pump(SettleMs);
            if (GetForegroundWindow() != h) return "lost front during settle (no screen copy)";
            using (var bmp = new Bitmap(w, ht, PixelFormat.Format32bppArgb))
            {
                using (var g = Graphics.FromImage(bmp)) g.CopyFromScreen(r.L, r.T, 0, 0, new Size(w, ht));
                if (GetForegroundWindow() != h) return "lost front during copy (discarded)";
                bmp.Save(path, ImageFormat.Png);
            }
        }
        finally { DestroyWindow(ov); }
        return "screen copy";
    }
}
'@
    $rr = [IO.Path]::GetFullPath($runsRoot).TrimEnd('\') + '\'
    $deadline = (Get-Date).AddSeconds($timeout); $p = $null
    while (-not $p -and (Get-Date) -lt $deadline) {
        $p = Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object {
            $x = try { $_.Path } catch { '' }; $_.StartTime -ge $t0 -and $x -and $x.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) } | Select-Object -First 1
        if (-not $p) { Start-Sleep -Milliseconds 500 }
    }
    if (-not $p) { 'shots: no game process'; return }
    $dir = Join-Path (Split-Path -Parent $p.Path) 'kit-shots'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    foreach ($s in $times) {
        $wait = ($p.StartTime.AddSeconds($s) - (Get-Date)).TotalMilliseconds
        if ($wait -gt 0) { Start-Sleep -Milliseconds ([int]$wait) }
        if ($p.HasExited) { "shots: game exited before $s s"; break }
        $f = Join-Path $dir ('shot-{0:000}s.png' -f $s)
        $how = [LdHarness]::Shot($p.Id, $f)
        $nb = if (Test-Path -LiteralPath $f) { [LdKitCap]::NonBlack($f) } else { -1 }
        $l = 'shot {0} s (at {1:N1} s) pid {2}: {3} -> {4} (client non-black {5:N1}%)' -f $s, ((Get-Date) - $p.StartTime).TotalSeconds, $p.Id, $how, $f, (100 * $nb)
        Add-Content -LiteralPath (Join-Path $dir 'shots.txt') -Value $l; $l
        if ($nb -lt 0.05) {
            $fs = Join-Path $dir ('shot-{0:000}s-screen.png' -f $s)
            $p.Refresh()
            $sc = [LdKitCap]::ScreenCopy($p.MainWindowHandle, $fs)
            $nb2 = if ($sc -eq 'screen copy' -and (Test-Path -LiteralPath $fs)) { [LdKitCap]::NonBlack($fs) } else { -1 }
            $l = 'shot {0} s (at {1:N1} s) pid {2}: fallback {3} -> {4} (client non-black {5:N1}%)' -f $s, ((Get-Date) - $p.StartTime).TotalSeconds, $p.Id, $sc, $fs, (100 * $nb2)
            Add-Content -LiteralPath (Join-Path $dir 'shots.txt') -Value $l; $l
        }
    }
}
# Hold watch: during an arm, polls WINDOW-HOLD.txt every 2 s; when it appears, WM_CLOSE to our game (image under
# $runsRoot only), then a forced stop after 15 s if it is still there. run-game then returns and the kit stops.
$holdJob = { param($hold, $runsRoot, $maxS)
    $rr = [IO.Path]::GetFullPath($runsRoot).TrimEnd('\') + '\'
    $end = (Get-Date).AddSeconds($maxS)
    while ((Get-Date) -lt $end) {
        if (Test-Path -LiteralPath $hold) {
            $ps = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object {
                    $x = try { $_.Path } catch { '' }; $x -and $x.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) })
            if (-not $ps.Count) { 'hold: WINDOW-HOLD.txt appeared; no game of ours running'; return }
            foreach ($p in $ps) { [void]$p.CloseMainWindow(); "hold: WINDOW-HOLD.txt appeared; WM_CLOSE to our game pid $($p.Id)" }
            Start-Sleep -Seconds 15
            foreach ($p in $ps) { if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; "hold: our game pid $($p.Id) still running after 15 s: stopped" } }
            return
        }
        Start-Sleep -Seconds 2
    }
}
# Abort/error cleanup, from the finally block: only what this script started. Our game = a legodimensions.exe whose
# image lives under $runsRoot; our run-game = a child powershell of this process running run-game.ps1.
function Stop-Ours {
    foreach ($jn in @('shotJ', 'holdJ')) {
        $jj = Get-Variable -Scope Script -Name $jn -ValueOnly -ErrorAction SilentlyContinue
        if ($jj) { Stop-Job $jj -ErrorAction SilentlyContinue; Remove-Job $jj -Force -ErrorAction SilentlyContinue; Set-Variable -Scope Script -Name $jn -Value $null; Say "cleanup: $jn stopped" }
    }
    if (-not $script:armActive) { return }
    $rr = [IO.Path]::GetFullPath($runsRoot).TrimEnd('\') + '\'
    foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='legodimensions.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($rr, [StringComparison]::OrdinalIgnoreCase) })) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: closed our game pid $($p.ProcessId) ($($p.ExecutablePath))"
    }
    foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.ParentProcessId -eq $PID -and $_.CommandLine -match 'run-game\.ps1' })) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Say "cleanup: stopped our run-game pid $($p.ProcessId)"
    }
    $script:armActive = $false
}
function Check-Bin([string]$b, [string]$when) {
    # the pinned bin is hard-linked into every run dir, so re-check it (MANIFEST = pin, verify-bins) after each arm
    $rc = Run-Logged 'python' @('-B', $vb, $b)
    $ms = (Get-FileHash -LiteralPath (Join-Path $b 'MANIFEST.txt') -Algorithm SHA256).Hash
    $ok = ($rc -eq 0 -and $ms -eq $pins[$b])
    Say "bin check $when ($b): verify-bins exit $rc, MANIFEST $($ms.Substring(0,16)) $(if ($ms -eq $pins[$b]) { '= pin' } else { 'NOT the pin' }) -> $(if ($ok) { 'OK' } else { 'FAIL' })"
    $ok
}

if ($DryRun) {
    $badn = 0
    foreach ($a in $arms) {
        if (-not (Test-Path -LiteralPath (Join-Path $a.bin 'legodimensions.exe'))) { Say "ARM $($a.arm): bin not staged, run-game -DryRun skipped (FAIL)"; $badn++; continue }
        Say "ARM $($a.arm) COMMAND (real run): $(Cmd-Line $a (Join-Path $out 'runs'))"
        $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $true)
        Say "ARM $($a.arm) run-game -DryRun exit $rc"; if ($rc -ne 0) { $badn++ }
    }
    # The screenshot job must load winhelper and give up cleanly when no game starts (t0 in the future).
    $j = Start-Job -ScriptBlock $shotJob -ArgumentList $ws, (Get-Date).AddHours(1), @(1), 3, $runsRoot
    $jo = @(Receive-Job -Job $j -Wait -AutoRemoveJob -ErrorAction Continue 2>&1 | ForEach-Object { "$_" })
    Say "shot job self-test: $($jo -join ' | ')"
    if (($jo -join ' ') -ne 'shots: no game process') { Say 'shot job self-test FAIL'; $badn++ }
    # The hold watch must see a hold file and close nothing when no game of ours runs (a scratch file, not WINDOW-HOLD).
    $fh = Join-Path $out "logs\holdtest-$stamp.txt"; Set-Content -LiteralPath $fh -Value 'hold self-test' -Encoding ascii
    $j = Start-Job -ScriptBlock $holdJob -ArgumentList $fh, $runsRoot, 10
    $jo = @(Receive-Job -Job $j -Wait -AutoRemoveJob -ErrorAction Continue 2>&1 | ForEach-Object { "$_" })
    Remove-Item -LiteralPath $fh -Force
    Say "hold watch self-test: $($jo -join ' | ')"
    if (($jo -join ' ') -ne 'hold: WINDOW-HOLD.txt appeared; no game of ours running') { Say 'hold watch self-test FAIL'; $badn++ }
    # Post self-test (parse only, no gates) on reference runs: T2 = devfinal2 ship60-r1, F3A/F3B = nativefinal2
    # nat60-r1/r2 (native-frames.csv), SBS = the nops-smoke T1/T2 kit-shots (side-by-side PNGs into a scratch dir).
    $mx = Join-Path $ws 'build\agent8\s5\matrix\20261125-1804\runs'
    $nr = Join-Path $kit 'nops-smoke\runs'
    $st = Join-Path $out "logs\post-selftest-$stamp.txt"
    $sbs = Join-Path $out "logs\sbs-selftest-$stamp"
    $rc = Run-Logged 'python' @('-B', $post, '--selftest', "T2=$mx\1815-ship60-r1", "F3A=$mx\1820-nat60-r1", "F3B=$mx\1835-nat60-r2",
        "SBS=$nr\20261125-201249-s5nops-t1,$nr\20261125-201719-s5nops-t2", '--sbs-dir', $sbs, '--out', $st)
    Say "rt_smoke_post.py --selftest exit $rc"
    foreach ($needle in @('T2 present_effect reject lines: 0', 'F3A frames: 14092 rows (native-frames.csv), spatial_fsr_presented=1 on 0',
            'F3B frames: ', 'side-by-side 060s: ', 'side-by-side 200s: ', 'ref error/critical kinds: 0')) {
        if ($rc -ne 0 -or -not (Select-String -LiteralPath $st -SimpleMatch -Quiet -Pattern $needle)) { Say "selftest needle FAIL: $needle"; $badn++ }
    }
    if (Test-Path -LiteralPath $sbs) { Remove-Item -LiteralPath $sbs -Recurse -Force; Say 'sbs self-test dir removed' }
    if (Test-Path -LiteralPath $runsRoot) {
        $rp = @(Get-ChildItem -LiteralPath $runsRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($rp.Count) { Say "dryrun-runs has reparse points: NOT deleted"; $badn++ } else { Remove-Item -LiteralPath $runsRoot -Recurse -Force; Say "dryrun-runs removed" }
    }
    Say "DRY RUN $(if ($badn) { "FAILED ($badn)" } else { 'ALL PASS' })"
    exit $(if ($badn) { 1 } else { 0 })
}

# --- real run ---
$results = @()
$first = $true
$stop = ''
$shotJ = $null; $holdJ = $null; $armActive = $false
try {
foreach ($a in $arms) {
    if (-not $first) { Say 'settle 20 s between arms'; Start-Sleep -Seconds 20 }
    $first = $false
    $ref = @(Get-Refusals)
    if ($ref.Count) { $stop = "refused before arm $($a.arm): $($ref -join '; ')"; Say "REFUSED: $stop"; break }
    Say "ARM $($a.arm) START $(Get-Date -Format HH:mm:ss): $(Cmd-Line $a $runsRoot)"
    $t0 = Get-Date
    if ($ShotArms -contains $a.arm) { $shotJ = Start-Job -ScriptBlock $shotJob -ArgumentList $ws, $t0.AddSeconds(-2), $ShotTimes, 180, $runsRoot }
    $holdJ = Start-Job -ScriptBlock $holdJob -ArgumentList $hold, $runsRoot, ($Seconds + 600)
    $armActive = $true
    $rc = Run-Logged 'powershell' (& $rgArgs $a $runsRoot $false)
    $armActive = $false
    if ($shotJ) {
        if (-not (Wait-Job -Job $shotJ -Timeout 30)) { Stop-Job -Job $shotJ }
        Receive-Job -Job $shotJ -ErrorAction Continue 2>&1 | ForEach-Object { Say "ARM $($a.arm) $_" }
        Remove-Job -Job $shotJ -Force; $shotJ = $null
    }
    Stop-Job -Job $holdJ
    $ho = @(Receive-Job -Job $holdJ -ErrorAction Continue 2>&1 | ForEach-Object { "$_" })
    Remove-Job -Job $holdJ -Force; $holdJ = $null
    $ho | ForEach-Object { Say "ARM $($a.arm) $_" }
    $run = @(Get-ChildItem -LiteralPath $runsRoot -Directory -Filter "*-$($a.tag)*" | Where-Object { $_.CreationTime -ge $t0.AddSeconds(-5) } | Sort-Object CreationTime | Select-Object -Last 1)
    $runDir = if ($run.Count) { $run[0].FullName } else { '?' }
    Say "ARM $($a.arm) DONE: run-game exit $rc, run $runDir"
    $results += [pscustomobject]@{ arm = $a.arm; rc = $rc; run = $runDir }
    if ($ho.Count) { $stop = "WINDOW-HOLD.txt during arm $($a.arm)"; Say "STOP: $stop (no further arm)"; break }
    if (-not (Check-Bin $a.bin "after arm $($a.arm)")) { $stop = "bin check FAIL after arm $($a.arm) (results invalid)"; Say "STOP: $stop"; break }
    if ($rc -ne 0) { $stop = "arm $($a.arm) exit $rc"; Say "ARM $($a.arm) exit ${rc}: stopping (no further arm)"; break }
}
} catch { Say "ERROR: $($_.Exception.Message)"; if (-not $stop) { $stop = "error: $($_.Exception.Message)" } } finally { Stop-Ours }
if ($stop) { Say "stopped: $stop" }
$postOut = Join-Path $out "post\rt-smoke-post-$stamp.txt"
$postArgs = @('-B', $post, '--out', $postOut, '--sbs-dir', (Join-Path $out "post\sbs-$stamp"))
foreach ($r in $results) { if ($r.run -ne '?') { $postArgs += @("--$($r.arm)", $r.run) } }
$prc = if ($postArgs.Count -gt 6) { Run-Logged 'python' $postArgs } else { 2 }
Say "rt_smoke_post.py exit $prc (report $postOut)"
Say "RT-SMOKE DONE: $(($results | ForEach-Object { "$($_.arm) exit $($_.rc) $($_.run)" }) -join '; '); post $(if ($prc -eq 0) { 'ALL PASS' } else { "FAIL (exit $prc)" })$(if ($stop) { "; stopped: $stop" })"
exit $(if ($stop -or @($results | Where-Object { $_.rc -ne 0 }).Count -or $results.Count -lt $arms.Count -or $prc -ne 0) { 1 } else { 0 })
