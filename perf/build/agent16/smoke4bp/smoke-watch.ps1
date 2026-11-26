# smoke-watch.ps1 - M16 S5 0.4c: game-window screenshots at fixed route marks for one smoke arm.
# Started (hidden window) by smoke-run.ps1 just before harness\run-game.ps1. Finds <RunsRoot>\<stamp>-<Tag>, tails its
# input.csv (written by run-game's vpad host as the route runs) and, when a 'mark' row with one of -Marks appears,
# captures the GAME WINDOW's client area only (CopyFromScreen of that rectangle; needs the visible desktop and the game
# window on top) as PNG into -OutDir\<arm>-<mark>.png (+ index.csv). Capture code as build\agent3\session3\s33-rows\row3\
# row3-watch.ps1 (M3), read-only reference. Exits when the game has gone for 5 s or at -Seconds + 240.
# -SelfTest: one synthetic PNG and the input.csv parser on -SelfTestCsv; no game, no capture. Exit 0 ok, 1 failed.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Arm,
    [string]$RunsRoot = '',
    [string]$Tag = '',
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Marks = 'idle-60,idle-120,idle-180',
    [int]$Seconds = 300,
    [double]$DelayS = 0.0,
    [switch]$SelfTest,
    [string]$SelfTestCsv = ''
)
$ErrorActionPreference = 'Stop'
$want = @($Marks.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$wlog = Join-Path $OutDir "watch-$Arm.log"
function Say([string]$s) { $l = "[watch $Arm $(Get-Date -Format HH:mm:ss.fff)] $s"; Write-Host $l; Add-Content -LiteralPath $wlog -Value $l }

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Imaging; using System.Runtime.InteropServices;
public static class M16Cap {
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
    public static void Save(Rectangle a, string path) {
        using (Bitmap b = new Bitmap(a.Width, a.Height, PixelFormat.Format24bppRgb)) {
            using (Graphics g = Graphics.FromImage(b)) g.CopyFromScreen(a.X, a.Y, 0, 0, a.Size, CopyPixelOperation.SourceCopy);
            b.Save(path, ImageFormat.Png);
        }
    }
    public static void Synthetic(string path) {
        using (Bitmap b = new Bitmap(320, 180, PixelFormat.Format24bppRgb)) { using (Graphics g = Graphics.FromImage(b)) g.Clear(Color.DarkSlateBlue); b.Save(path, ImageFormat.Png); }
    }
}
'@
[void][M16Cap]::SetProcessDPIAware()

function Read-Marks([string]$csv) {
    # returns the mark names in input.csv (t_s,line,cmd,args,...); opened shared, the vpad host keeps writing it
    try { $fs = [IO.File]::Open($csv, 'Open', 'Read', [IO.FileShare]'ReadWrite, Delete') } catch { return @() }
    try { $sr = New-Object IO.StreamReader($fs); $txt = $sr.ReadToEnd() } finally { $fs.Dispose() }
    @($txt -split "`r?`n" | ForEach-Object { $c = $_.Split(','); if ($c.Count -ge 4 -and $c[2] -eq 'mark') { $c[3] } })
}

if ($SelfTest) {
    $ok = $true
    $p = Join-Path $OutDir "selftest-$Arm.png"; [M16Cap]::Synthetic($p)
    if (-not (Test-Path -LiteralPath $p) -or (Get-Item -LiteralPath $p).Length -lt 100) { $ok = $false }
    $m = @(); if ($SelfTestCsv) { $m = Read-Marks $SelfTestCsv }
    $hit = @($want | Where-Object { $m -contains $_ })
    Say "SELFTEST png $((Get-Item -LiteralPath $p).Length) B; marks in csv $($m.Count); wanted $($want -join ',') found $($hit -join ',')"
    if ($SelfTestCsv -and $hit.Count -ne $want.Count) { $ok = $false }
    Remove-Item -LiteralPath $p -Force
    Say "SELFTEST $(if ($ok) { 'ok' } else { 'FAILED' })"; exit $(if ($ok) { 0 } else { 1 })
}

$start = Get-Date; $deadline = $start.AddSeconds($Seconds + 240)
$run = $null; $done = @{}; $seen = $false; $gone = $null; $idx = Join-Path $OutDir 'index.csv'
if (-not (Test-Path -LiteralPath $idx)) { Set-Content -LiteralPath $idx -Value 'file,time,mark,x,y,w,h,foreground' -Encoding ascii }
Say "watching $RunsRoot for *-$Tag; marks $($want -join ',')"
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
        foreach ($mk in (Read-Marks $csv)) {
            if ($want -notcontains $mk -or $done.ContainsKey($mk)) { continue }
            $done[$mk] = $true
            if ($DelayS -gt 0) { Start-Sleep -Milliseconds ([int]($DelayS * 1000)) }
            $h = $g[0].MainWindowHandle; $a = [M16Cap]::Area($h)
            $fg = ([M16Cap]::GetForegroundWindow() -eq $h)
            if ($a.IsEmpty -or $a.Width -le 0) { Say "mark $mk`: no game window area (minimised or hidden desktop): no shot"; continue }
            $name = "$Arm-$mk.png"
            try {
                [M16Cap]::Save($a, (Join-Path $OutDir $name))
                Add-Content -LiteralPath $idx -Value ('{0},{1},{2},{3},{4},{5},{6},{7}' -f $name, (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'), $mk, $a.X, $a.Y, $a.Width, $a.Height, $fg) -Encoding ascii
                Say "mark $mk`: saved $name ($($a.Width)x$($a.Height), game window foreground $fg)"
            } catch { Say "mark $mk`: capture failed: $($_.Exception.Message)" }
        }
    }
    if ($done.Count -ge $want.Count) { Say 'all marks captured'; break }
    Start-Sleep -Milliseconds 250
}
Say "watcher end: $($done.Count)/$($want.Count) marks handled"
exit 0
