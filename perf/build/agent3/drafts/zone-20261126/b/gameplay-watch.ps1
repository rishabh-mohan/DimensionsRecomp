# gameplay-watch.ps1 - M3 gameplay task: a game-window screenshot at EVERY route 'mark' of one arm.
# Started (hidden window) by gameplay-run.ps1 just before harness\run-game.ps1. Finds <RunsRoot>\<stamp>-<Tag> (created
# at/after its own start - 5 s), tails its input.csv (opened shared; run-game's vpad host keeps writing it) and, for every
# new 'mark' row, captures the GAME WINDOW's client area only (CopyFromScreen of that rectangle: needs the visible
# desktop and the game window on top; a mark while the game is NOT the foreground window is logged and skipped, so no
# other window's pixels are ever saved) as JPEG into -OutDir\<arm>-<nnn>-<mark>.jpg (nnn = mark number in the route) and
# appends index.csv (file,time,route_t_s,mark,x,y,w,h,foreground). Also a shot for every 'shot' row the prompt sidecar
# writes to <run>\toypad-events.csv (--led-shots: Toy Pad LED states) as -OutDir\<arm>-led-<nn>-<label>.jpg (index.csv
# mark 'led_<label>', route_t_s empty; gameplay_post.py's <arm>-<nnn>- mark lookup skips these). Capture code as M16's smoke-watch.ps1 /
# build\agent3\session3\s33-rows\row3\row3-watch.ps1 (read-only references). Exits when the game has been gone for 5 s or
# at -Seconds + 240. Touches no process; writes only -OutDir.
# -SelfTest: one synthetic JPEG + the input.csv mark parser on -SelfTestCsv (no game, no capture). Exit 0 ok, 1 failed.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Arm,
    [string]$RunsRoot = '',
    [string]$Tag = '',
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Seconds = 900,
    [int]$Quality = 85,
    [switch]$SelfTest,
    [string]$SelfTestCsv = ''
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$wlog = Join-Path $OutDir "watch-$Arm.log"
function Say([string]$s) { $l = "[watch $Arm $(Get-Date -Format HH:mm:ss.fff)] $s"; Write-Host $l; Add-Content -LiteralPath $wlog -Value $l }

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class M3GpCap {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    public static Rectangle Area(IntPtr h) {
        RECT r; if (h == IntPtr.Zero || IsIconic(h) || !GetClientRect(h, out r)) return Rectangle.Empty;
        POINT p = new POINT(); if (!ClientToScreen(h, ref p)) return Rectangle.Empty;
        return new Rectangle(p.X, p.Y, r.R - r.L, r.B - r.T);
    }
    static void SaveJpeg(Bitmap b, string path, long q) {
        ImageCodecInfo enc = null;
        foreach (ImageCodecInfo c in ImageCodecInfo.GetImageEncoders()) if (c.FormatID == ImageFormat.Jpeg.Guid) enc = c;
        EncoderParameters ps = new EncoderParameters(1);
        ps.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, q);
        b.Save(path, enc, ps);
    }
    public static void Save(Rectangle a, string path, long q) {
        using (Bitmap b = new Bitmap(a.Width, a.Height, PixelFormat.Format24bppRgb)) {
            using (Graphics g = Graphics.FromImage(b)) g.CopyFromScreen(a.X, a.Y, 0, 0, a.Size, CopyPixelOperation.SourceCopy);
            SaveJpeg(b, path, q);
        }
    }
    public static void Synthetic(string path, long q) {
        using (Bitmap b = new Bitmap(320, 180, PixelFormat.Format24bppRgb)) { using (Graphics g = Graphics.FromImage(b)) g.Clear(Color.DarkSlateBlue); SaveJpeg(b, path, q); }
    }
}
'@
[void][M3GpCap]::SetProcessDPIAware()

function Read-Marks([string]$csv) {
    # [t_s, label] of every 'mark' row of input.csv (t_s,line,cmd,args,result,...), in file order
    try { $fs = [IO.File]::Open($csv, 'Open', 'Read', [IO.FileShare]'ReadWrite, Delete') } catch { return @() }
    try { $sr = New-Object IO.StreamReader($fs); $txt = $sr.ReadToEnd() } finally { $fs.Dispose() }
    @($txt -split "`r?`n" | ForEach-Object { $c = $_.Split(','); if ($c.Count -ge 5 -and $c[2] -eq 'mark') { , @($c[0], $c[3]) } })
}
function Safe([string]$s) { ($s -replace '[^A-Za-z0-9._-]', '_') }
function Read-Shots([string]$csv) {
    # labels of the 'shot' rows of the prompt sidecar's toypad-events.csv (wall,t_sidecar,game_ts,kind,detail) in the
    # complete lines added since the last call (byte offset $script:tpPos: the file is read once, not every poll)
    try { $fs = [IO.File]::Open($csv, 'Open', 'Read', [IO.FileShare]'ReadWrite, Delete') } catch { return @() }
    try {
        if ($fs.Length -le $script:tpPos) { return @() }
        $null = $fs.Seek($script:tpPos, 'Begin'); $buf = New-Object byte[] ($fs.Length - $script:tpPos)
        $n = $fs.Read($buf, 0, $buf.Length)
    } finally { $fs.Dispose() }
    if ($n -le 0) { return @() }
    $end = [Array]::LastIndexOf($buf, [byte]10, $n - 1); if ($end -lt 0) { return @() }
    $script:tpPos += $end + 1
    @([Text.Encoding]::UTF8.GetString($buf, 0, $end + 1) -split "`r?`n" | ForEach-Object { $c = $_.Split(',', 5); if ($c.Count -eq 5 -and $c[3] -eq 'shot') { $c[4] } })
}
$script:tpPos = 0

if ($SelfTest) {
    $ok = $true
    $p = Join-Path $OutDir "selftest-$Arm.jpg"; [M3GpCap]::Synthetic($p, $Quality)
    if (-not (Test-Path -LiteralPath $p) -or (Get-Item -LiteralPath $p).Length -lt 100) { $ok = $false }
    $len = if (Test-Path -LiteralPath $p) { (Get-Item -LiteralPath $p).Length } else { 0 }
    $m = @(); if ($SelfTestCsv) { $m = @(Read-Marks $SelfTestCsv) }
    $first = if ($m.Count) { "$($m[0][1])@$($m[0][0])" } else { '-' }
    $last = if ($m.Count) { "$($m[-1][1])@$($m[-1][0])" } else { '-' }
    Say "SELFTEST jpg $len B; marks in csv $($m.Count) (first $first, last $last); names e.g. $Arm-001-$(Safe $(if ($m.Count) { $m[0][1] } else { 'x' })).jpg"
    if ($SelfTestCsv -and $m.Count -lt 3) { $ok = $false }
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
    $tp = Join-Path $OutDir "selftest-$Arm-toypad-events.csv"
    Set-Content -LiteralPath $tp -Encoding ascii -Value @('wall,t_sidecar,game_ts,kind,detail', '05:25:41.306,1.00,05:25:41.300,zone-t0,pad 3 lit FF 00 18 speed 15 after the prompts',
        '05:25:41.307,1.01,05:25:41.300,shot,zone-t0', '05:27:26.820,2.00,05:27:26.818,alert,"pad 1 lit FF 00 00 speed 18: state 1, starts"', '05:27:31.830,3.00,,shot,alert1-plus05s')
    $sh = @(Read-Shots $tp); Remove-Item -LiteralPath $tp -Force
    Say "SELFTEST led shot rows $($sh.Count) ($($sh -join ' ')); names e.g. $Arm-led-01-$(Safe $(if ($sh.Count) { $sh[0] } else { 'x' })).jpg"
    if (($sh -join ' ') -ne 'zone-t0 alert1-plus05s') { $ok = $false }
    Say "SELFTEST $(if ($ok) { 'ok' } else { 'FAILED' })"; exit $(if ($ok) { 0 } else { 1 })
}

$start = Get-Date; $deadline = $start.AddSeconds($Seconds + 240)
$run = $null; $handled = 0; $tpHandled = 0; $seen = $false; $gone = $null; $idx = Join-Path $OutDir 'index.csv'; $shots = 0
if (-not (Test-Path -LiteralPath $idx)) { Set-Content -LiteralPath $idx -Value 'file,time,route_t_s,mark,x,y,w,h,foreground' -Encoding ascii }
Say "watching $RunsRoot for *-$Tag; every mark"
while ((Get-Date) -lt $deadline) {
    if (-not $run) {
        $d = @(Get-ChildItem -LiteralPath $RunsRoot -Directory -Filter "*-$Tag*" -ErrorAction SilentlyContinue | Where-Object { $_.CreationTime -ge $start.AddSeconds(-5) } | Sort-Object CreationTime)
        if ($d.Count) { $run = $d[-1].FullName; Say "run dir $run" } else { Start-Sleep -Milliseconds 500; continue }
    }
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object { try { $_.Path -like "$run\*" } catch { $false } })
    if ($g.Count) { $seen = $true; $gone = $null } elseif ($seen -and -not $gone) { $gone = Get-Date }
    if ($gone -and ((Get-Date) - $gone).TotalSeconds -ge 5) { Say 'game exited'; break }
    $csv = Join-Path $run 'input.csv'
    if ($g.Count -and (Test-Path -LiteralPath $csv)) {
        $all = @(Read-Marks $csv)
        while ($handled -lt $all.Count) {
            $mk = $all[$handled]; $handled++
            $h = $g[0].MainWindowHandle; $a = [M3GpCap]::Area($h)
            $fg = ([M3GpCap]::GetForegroundWindow() -eq $h)
            if ($a.IsEmpty -or $a.Width -le 0) { Say "mark $handled $($mk[1]): no game window area (minimised or hidden desktop): no shot"; continue }
            # S1: CopyFromScreen would save whatever covers the game window; shoot only while the game is foreground
            if (-not $fg) { Say "mark $handled $($mk[1]) (route $($mk[0]) s): game not foreground: no shot"; continue }
            $name = '{0}-{1:000}-{2}.jpg' -f $Arm, $handled, (Safe $mk[1])
            try {
                [M3GpCap]::Save($a, (Join-Path $OutDir $name), $Quality); $shots++
                Add-Content -LiteralPath $idx -Value ('{0},{1},{2},{3},{4},{5},{6},{7},{8}' -f $name, (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'), $mk[0], (Safe $mk[1]), $a.X, $a.Y, $a.Width, $a.Height, $fg) -Encoding ascii
                Say "mark $handled $($mk[1]) (route $($mk[0]) s): saved $name ($($a.Width)x$($a.Height), foreground $fg)"
            } catch { Say "mark $handled $($mk[1]): capture failed: $($_.Exception.Message)" }
        }
        # Toy Pad LED states the prompt sidecar asks for (--led-shots: zone cues, the speed-18 state +5/+30/+60 s)
        $new = @(Read-Shots (Join-Path $run 'toypad-events.csv'))
        foreach ($lb in $new) {
            $tpHandled++
            $h = $g[0].MainWindowHandle; $a = [M3GpCap]::Area($h); $fg = ([M3GpCap]::GetForegroundWindow() -eq $h)
            if ($a.IsEmpty -or $a.Width -le 0 -or -not $fg) { Say "led shot $tpHandled $lb`: no game window area or game not foreground: no shot"; continue }
            $name = '{0}-led-{1:00}-{2}.jpg' -f $Arm, $tpHandled, (Safe $lb)
            try {
                [M3GpCap]::Save($a, (Join-Path $OutDir $name), $Quality); $shots++
                Add-Content -LiteralPath $idx -Value ('{0},{1},,{2},{3},{4},{5},{6},{7}' -f $name, (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'), (Safe "led:$lb"), $a.X, $a.Y, $a.Width, $a.Height, $fg) -Encoding ascii
                Say "led shot $tpHandled $lb`: saved $name ($($a.Width)x$($a.Height))"
            } catch { Say "led shot $tpHandled $lb`: capture failed: $($_.Exception.Message)" }
        }
    }
    Start-Sleep -Milliseconds 250
}
Say "watcher end: $handled marks seen, $tpHandled led shot requests, $shots shots"
exit 0
