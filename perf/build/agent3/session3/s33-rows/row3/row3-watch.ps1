# row3-watch.ps1 - #33 row 3 watcher for one arm (M3). Started by row3-run.ps1 just before harness\run-game.ps1.
# Finds the arm's run dir (<RunsRoot>\<stamp>-<Tag>), tails its game.log, prints 'ARM <X> FIRST FRAME' and
# 'ARM <X> FIRST 3D FRAME' hints, writes the wall-clock screenshot schedule to <OutDir>\live\<arm>.txt (for manual
# `computer-cli screenshot` calls) and, unless -NoAuto, captures the GAME WINDOW's client area only (not the rest of
# the desktop) as JPEG at the row3-schedule.json windows into <OutDir>\shots\auto\<arm>\ (+ index.csv).
#   FF  = the first slow-frame line in game.log (slow_frame_log_ms=1 logs every frame).
#   A3D = the first slow-frame line with 'new >= 15' more than 60 s after FF (= row3_log.events 'first-3d').
# -SelfTestRun <run dir>: replays that run's game*.log through the same parser (no capture, no game), prints FF, A3D
# and the schedule, and encodes one synthetic JPEG. Exit 0 ok, 1 failed.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Arm,
    [string]$RunsRoot = '',
    [string]$Tag = '',
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Seconds = 540,
    [switch]$NoAuto,
    [int]$Quality = 85,
    [string]$SelfTestRun = ''
)
$ErrorActionPreference = 'Stop'
$ARM = $Arm.ToUpper()
$sched = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'row3-schedule.json') -Raw | ConvertFrom-Json
$maxFps = [int]$sched.max_fps
$logDir = Join-Path $OutDir 'logs'; New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$wlog = Join-Path $logDir "watch-$Arm-$(Get-Date -Format yyyyMMdd-HHmmss).txt"
function Say([string]$s) { $l = "[row3 $ARM $(Get-Date -Format HH:mm:ss.fff)] $s"; Write-Host $l; Add-Content -LiteralPath $wlog -Value $l }

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Imaging; using System.IO; using System.Runtime.InteropServices;
public static class Row3Cap {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    static ImageCodecInfo jpg; static EncoderParameters ep;
    public static void Init(long q) {
        foreach (ImageCodecInfo c in ImageCodecInfo.GetImageEncoders()) if (c.MimeType == "image/jpeg") jpg = c;
        ep = new EncoderParameters(1); ep.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, q);
    }
    public static Rectangle Area(IntPtr h) {
        RECT r; if (h == IntPtr.Zero || IsIconic(h) || !GetClientRect(h, out r)) return Rectangle.Empty;
        POINT p = new POINT(); if (!ClientToScreen(h, ref p)) return Rectangle.Empty;
        return new Rectangle(p.X, p.Y, r.R - r.L, r.B - r.T);
    }
    public static byte[] Grab(Rectangle a) {
        if (a.Width <= 0 || a.Height <= 0) return null;
        using (Bitmap b = new Bitmap(a.Width, a.Height, PixelFormat.Format24bppRgb)) {
            using (Graphics g = Graphics.FromImage(b)) g.CopyFromScreen(a.X, a.Y, 0, 0, a.Size, CopyPixelOperation.SourceCopy);
            return Enc(b);
        }
    }
    public static byte[] Enc(Bitmap b) { using (MemoryStream ms = new MemoryStream()) { b.Save(ms, jpg, ep); return ms.ToArray(); } }
    public static byte[] Synthetic(int w, int h) {
        using (Bitmap b = new Bitmap(w, h, PixelFormat.Format24bppRgb)) { using (Graphics g = Graphics.FromImage(b)) g.Clear(Color.DarkSlateBlue); return Enc(b); }
    }
}
'@
[void][Row3Cap]::SetProcessDPIAware()
[Row3Cap]::Init($Quality)

# --- log parsing (same rules as row3_log.py) ---
$reSlow = [regex]'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\][^\r\n]*?slow frame #(\d+): [\d.]+ ms[^\r\n]*?, new (\d+)'
$script:FF = $null; $script:A3D = $null; $script:A3Dest = $false
function Handle-Line([string]$ln) {
    if ($script:A3D -or $ln.IndexOf('slow frame #') -lt 0) { return }
    $m = $reSlow.Match($ln); if (-not $m.Success) { return }
    $t = [datetime]::ParseExact($m.Groups[1].Value, 'yyyy-MM-dd HH:mm:ss.fff', [Globalization.CultureInfo]::InvariantCulture)
    if (-not $script:FF) { $script:FF = $t; return }
    if ([int]$m.Groups[3].Value -ge 15 -and ($t - $script:FF).TotalSeconds -gt 60) { $script:A3D = $t }
}
function Wall-Schedule {
    foreach ($w in $sched.windows) {
        $from = $script:A3D.AddSeconds([double]$w.from)
        $to = if ($w.kind -eq 'burst') { $script:A3D.AddSeconds([double]$w.to) } else { $from.AddSeconds(0.65) }
        [pscustomobject]@{ name = $w.name; kind = $w.kind; from = $from; to = $to; rel = [double]$w.from; note = $w.note; stills = 0 }
    }
}
function Write-Live([string]$run) {
    $lines = @("arm $Arm  run $run", "FF  $($script:FF.ToString('HH:mm:ss.fff')) (first slow-frame line)",
        "A3D $($script:A3D.ToString('HH:mm:ss.fff')) (FF+$('{0:N2}' -f ($script:A3D - $script:FF).TotalSeconds) s)$(if ($script:A3Dest) { ' ESTIMATED: no first-3D line by FF+' + $sched.a3d_fallback_ff_s + ' s' })",
        "screenshot schedule (wall clock; for manual 'computer-cli screenshot', save as shots\$Arm-<n>.png):")
    $n = 1
    foreach ($w in $script:wins) { $lines += ('  {0,2} {1,-18} {2,-5} {3} .. {4}  A3D{5:+0.0;-0.0}  {6}' -f $n, $w.name, $w.kind, $w.from.ToString('HH:mm:ss.f'), $w.to.ToString('HH:mm:ss.f'), $w.rel, $w.note); $n++ }
    $d = Join-Path $OutDir 'live'; New-Item -ItemType Directory -Force -Path $d | Out-Null
    Set-Content -LiteralPath (Join-Path $d "$Arm.txt") -Value $lines -Encoding utf8
    $lines | ForEach-Object { Say $_ }
}

if ($SelfTestRun) {
    $files = @(Get-ChildItem -LiteralPath $SelfTestRun -Filter 'game*.log' | Sort-Object { if ($_.Name -match 'game\.(\d+)\.log') { -[int]$Matches[1] } else { 0 } })
    foreach ($f in $files) { foreach ($ln in [IO.File]::ReadLines($f.FullName)) { Handle-Line $ln; if ($script:A3D) { break } }; if ($script:A3D) { break } }
    $jpg = [Row3Cap]::Synthetic(640, 360)
    if (-not $script:FF -or -not $script:A3D -or -not $jpg -or $jpg.Length -lt 100) { Say "SELFTEST FAIL: FF $script:FF A3D $script:A3D jpeg $($jpg.Length) B"; exit 1 }
    $script:wins = @(Wall-Schedule)
    Say "SELFTEST replay of $SelfTestRun ($(($files | ForEach-Object Name) -join ','))"
    Write-Live $SelfTestRun
    Say "SELFTEST ok: FF+$('{0:N2}' -f ($script:A3D - $script:FF).TotalSeconds) s to A3D; $($script:wins.Count) windows; synthetic JPEG $($jpg.Length) B"
    exit 0
}

# --- live mode ---
$start = Get-Date; $deadline = $start.AddSeconds($Seconds + 240)
$run = $null; $off = 0L; $partial = ''; $lastPoll = [datetime]::MinValue
$hwnd = [IntPtr]::Zero; $area = [Drawing.Rectangle]::Empty; $lastArea = [datetime]::MinValue
$ring = New-Object System.Collections.Generic.List[object]
$phase = 'wait-run'; $seenGame = $false; $goneSince = $null; $nextCap = [datetime]::MinValue
$shotDir = Join-Path $OutDir "shots\auto\$Arm"; $idx = Join-Path $shotDir 'index.csv'; $seq = 0; $capErr = 0; $saved = 0
Say "watching $RunsRoot for *-$Tag (auto capture $(if ($NoAuto) { 'OFF' } else { "ON, game window only, <= $maxFps fps" }))"

function Poll-Log {
    $p = Join-Path $run 'game.log'
    if (-not (Test-Path -LiteralPath $p)) { return }
    try { $fs = [IO.File]::Open($p, 'Open', 'Read', [IO.FileShare]'ReadWrite, Delete') } catch { return }
    try {
        if ($fs.Length -lt $script:off) { $script:off = 0L; $script:partial = '' }   # rotated to game.1.log
        if ($fs.Length -eq $script:off) { return }
        [void]$fs.Seek($script:off, 'Begin')
        $buf = New-Object byte[] ($fs.Length - $script:off); $n = $fs.Read($buf, 0, $buf.Length); $script:off += $n
        $text = $script:partial + [Text.Encoding]::UTF8.GetString($buf, 0, $n)
        $cut = $text.LastIndexOf("`n")
        if ($cut -lt 0) { $script:partial = $text; return }
        $script:partial = $text.Substring($cut + 1)
        foreach ($ln in $text.Substring(0, $cut).Split("`n")) { Handle-Line $ln }
    } finally { $fs.Dispose() }
}
function Find-Window {
    $g = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue | Where-Object { try { $_.Path -like "$run\*" } catch { $false } })
    if ($g.Count) { $script:seenGame = $true; $script:goneSince = $null; $script:hwnd = $g[0].MainWindowHandle; $script:area = [Row3Cap]::Area($script:hwnd) }
    elseif ($script:seenGame -and -not $script:goneSince) { $script:goneSince = Get-Date }
}
function Grab {
    $now = Get-Date
    if ($area.IsEmpty) { $script:capErr++; return $null }
    try { $b = [Row3Cap]::Grab($area) } catch { $script:capErr++; if ($script:capErr -le 3) { Say "capture failed: $($_.Exception.Message)" }; return $null }
    [pscustomobject]@{ t = $now; b = $b }
}
function Save-Shot($s, [string]$win) {
    if (-not $s) { return }
    if (-not (Test-Path -LiteralPath $shotDir)) { New-Item -ItemType Directory -Force -Path $shotDir | Out-Null; Set-Content -LiteralPath $idx -Value 'file,time,a3d_s,window' -Encoding ascii }
    $script:seq++
    $rel = ($s.t - $script:A3D).TotalSeconds
    $name = '{0}_{1:0000}_{2}_A{3:+000.000;-000.000}.jpg' -f $Arm, $script:seq, $win, $rel
    [IO.File]::WriteAllBytes((Join-Path $shotDir $name), $s.b)
    Add-Content -LiteralPath $idx -Value ('{0},{1},{2:0.000},{3}' -f $name, $s.t.ToString('yyyy-MM-dd HH:mm:ss.fff'), $rel, $win) -Encoding ascii
    $script:saved++
}

while ((Get-Date) -lt $deadline) {
    $now = Get-Date
    if ($phase -eq 'wait-run') {
        $d = @(Get-ChildItem -LiteralPath $RunsRoot -Directory -Filter "*-$Tag*" -ErrorAction SilentlyContinue | Where-Object { $_.CreationTime -ge $start.AddSeconds(-5) } | Sort-Object CreationTime)
        if ($d.Count) { $run = $d[-1].FullName; Say "run dir $run"; $phase = 'wait-ff' } else { Start-Sleep -Milliseconds 250; continue }
    }
    if (($now - $lastPoll).TotalMilliseconds -ge 200) {
        $hadFF = [bool]$script:FF; $hadA3D = [bool]$script:A3D
        Poll-Log; $lastPoll = $now
        if (-not $hadFF -and $script:FF) { Say "ARM $ARM FIRST FRAME at $($script:FF.ToString('HH:mm:ss.fff'))" }
        if (-not $hadA3D -and $script:A3D) { Say "ARM $ARM FIRST 3D FRAME at $($script:A3D.ToString('HH:mm:ss.fff')) (FF+$('{0:N2}' -f ($script:A3D - $script:FF).TotalSeconds) s)" }
    }
    if (($now - $lastArea).TotalSeconds -ge 2) { Find-Window; $lastArea = $now }
    if ($goneSince -and ($now - $goneSince).TotalSeconds -ge 5) { Say 'game exited'; break }
    if ($phase -eq 'wait-ff' -and $script:FF) { $phase = 'preroll' }
    if ($phase -eq 'preroll') {
        $ffs = ($now - $script:FF).TotalSeconds
        if (-not $script:A3D -and $ffs -ge [double]$sched.a3d_fallback_ff_s) { $script:A3D = $script:FF.AddSeconds([double]$sched.a3d_estimate_ff_s); $script:A3Dest = $true; Say "no first-3D line by FF+$($sched.a3d_fallback_ff_s) s: A3D ESTIMATED as FF+$($sched.a3d_estimate_ff_s)" }
        if ($script:A3D) {
            $script:wins = @(Wall-Schedule); Write-Live $run
            $keep = @($ring | Where-Object { $_.t -ge $script:A3D.AddSeconds(-0.5) }); foreach ($s in $keep) { Save-Shot $s $script:wins[0].name }
            if ($ring.Count) { Say "pre-roll: $($ring.Count) frames held, $($keep.Count) saved from A3D-0.5 s" }
            $ring.Clear(); $phase = 'sched'
        } elseif (-not $NoAuto -and $ffs -ge [double]$sched.preroll_from_ff_s -and $now -ge $nextCap) {
            $s = Grab; $nextCap = $now.AddMilliseconds(1000 / $maxFps)
            if ($s) { $ring.Add($s); while ($ring.Count -and ($now - $ring[0].t).TotalSeconds -gt 3.0) { $ring.RemoveAt(0) } }
        }
    }
    if ($phase -eq 'sched') {
        if (-not $NoAuto) {
            foreach ($w in $script:wins) {
                if ($now -lt $w.from -or $now -gt $w.to) { continue }
                if ($w.kind -eq 'burst' -and $now -ge $nextCap) { Save-Shot (Grab) $w.name; $nextCap = $now.AddMilliseconds(1000 / $maxFps) }
                if ($w.kind -eq 'still' -and $w.stills -lt 3 -and $now -ge $w.from.AddSeconds(0.3 * $w.stills)) { Save-Shot (Grab) $w.name; $w.stills++ }
            }
        }
        if ($now -gt ($script:wins | ForEach-Object { $_.to } | Sort-Object | Select-Object -Last 1)) { Say 'schedule done'; $phase = 'done' }
    }
    if ($phase -eq 'done' -and -not $seenGame) { break }
    Start-Sleep -Milliseconds $(if ($phase -eq 'sched' -or $phase -eq 'preroll') { 5 } else { 100 })
}
Say "watcher end: phase $phase; saved $saved JPEG(s) to $shotDir; capture errors $capErr"
exit 0
