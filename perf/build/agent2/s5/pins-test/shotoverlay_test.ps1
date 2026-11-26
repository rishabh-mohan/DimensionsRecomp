# Offline test of the overlay screen copy in LdKitCap (extracted from rt-smoke-run.ps1 by AST). No game.
# A test form is made foreground; ScreenCopy must keep it foreground, create the ld-kit-compose overlay only during the
# copy (checked from a timer thread), destroy it afterwards, and write the PNG. Also the refusal paths.
param([string]$Kit = '<workspace>\build\agent2\s5\rt-smoke-run.ps1',
      [string]$Out = '<workspace>\build\agent2\s5\pins-test\overlay-test')
$ErrorActionPreference = 'Stop'
$t = $null; $e = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Kit, [ref]$t, [ref]$e)
"parse errors: $($e.Count)"
$hs = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.StringConstantExpressionAst] -and $n.StringConstantType -eq 'SingleQuotedHereString' -and $n.Value -match 'class LdKitCap' }, $true) | Select-Object -First 1
if (-not $hs) { 'LdKitCap here-string not found'; exit 1 }
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition $hs.Value
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices; using System.Threading;
public static class OvProbe {
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindowW(string cls, string name);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern int GetWindowLongW(IntPtr h, int i);
    public static volatile int Seen, ExStyle; public static volatile bool FgLost;
    // polls for the overlay from another thread while ScreenCopy runs; records its ex-style and any foreground change
    public static Thread Watch(IntPtr fg, int ms) {
        var th = new Thread(() => { var end = DateTime.Now.AddMilliseconds(ms);
            while (DateTime.Now < end) { IntPtr o = FindWindowW("Static", "ld-kit-compose");
                if (o != IntPtr.Zero) { Seen++; ExStyle = GetWindowLongW(o, -20); }
                if (GetForegroundWindow() != fg) FgLost = true; Thread.Sleep(20); } });
        th.IsBackground = true; th.Start(); return th; }
}
'@
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$bad = 0
function Check($name, $ok, $info) { "{0}  {1}  [{2}]" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $name, $info; if (-not $ok) { $script:bad++ } }
Check 'SettleMs default 500' ([LdKitCap]::SettleMs -eq 500) ([LdKitCap]::SettleMs)
Check 'ScreenCopy(0) refuses' ([LdKitCap]::ScreenCopy([IntPtr]::Zero, "$Out\x.png") -eq 'no window') ''
$f = New-Object System.Windows.Forms.Form
$f.Text = 'ld-overlay-test'; $f.StartPosition = 'Manual'; $f.Left = 100; $f.Top = 100; $f.Width = 640; $f.Height = 400
$f.BackColor = [System.Drawing.Color]::FromArgb(200, 40, 40)
$f.Show(); $f.Activate(); [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 300; [System.Windows.Forms.Application]::DoEvents()
$h = $f.Handle
$fgOk = ([OvProbe]::GetForegroundWindow() -eq $h)
"test form foreground on this desktop: $fgOk (desktop: $([Environment]::UserInteractive))"
if ($fgOk) {
    $png = "$Out\form-screen.png"; Remove-Item -LiteralPath $png -ErrorAction SilentlyContinue
    $th = [OvProbe]::Watch($h, 1500)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $r = try { [LdKitCap]::ScreenCopy($h, $png) } catch { "EXCEPTION $($_.Exception.InnerException.Message)" }
    $ms = $sw.ElapsedMilliseconds; $th.Join()
    Check 'ScreenCopy returns screen copy' ($r -eq 'screen copy') $r
    Check 'took >= SettleMs and < 2 s' ($ms -ge 500 -and $ms -lt 2000) "$ms ms"
    Check 'overlay seen during the copy' ([OvProbe]::Seen -gt 0) "polls $([OvProbe]::Seen)"
    $want = 0x80000 -bor 0x20 -bor 0x8 -bor 0x08000000 -bor 0x80
    Check 'overlay ex-style has layered|transparent|topmost|noactivate|toolwindow' ((([OvProbe]::ExStyle) -band $want) -eq $want) ('0x{0:X8}' -f [OvProbe]::ExStyle)
    Check 'overlay destroyed afterwards' ([OvProbe]::FindWindowW('Static', 'ld-kit-compose') -eq [IntPtr]::Zero) ''
    Check 'test form kept foreground throughout' (-not [OvProbe]::FgLost -and [OvProbe]::GetForegroundWindow() -eq $h) "lost $([OvProbe]::FgLost)"
    if (Test-Path -LiteralPath $png) {
        $nb = [LdKitCap]::NonBlack($png)
        $b = New-Object System.Drawing.Bitmap $png; $c = $b.GetPixel([int]($b.Width / 2), [int]($b.Height / 2)); $sz = "$($b.Width)x$($b.Height)"; $b.Dispose()
        Check 'PNG written, client non-black >= 2%' ($nb -ge 0.02) ('{0:N1}%, {1}, centre {2},{3},{4}' -f (100 * $nb), $sz, $c.R, $c.G, $c.B)
        Check 'centre pixel = form colour within 3 levels (alpha-1 overlay invisible)' ([Math]::Abs($c.R - 200) -le 3 -and [Math]::Abs($c.G - 40) -le 3 -and [Math]::Abs($c.B - 40) -le 3) "$($c.R),$($c.G),$($c.B)"
    } else { Check 'PNG written' $false $png }
    # not foreground -> refuses, no overlay
    $f.WindowState = 'Minimized'; [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 300
    $r2 = [LdKitCap]::ScreenCopy($h, "$Out\x2.png")
    Check 'not foreground -> refuses' ($r2 -eq 'not in front (no screen copy)') $r2
} else {
    # Hidden agent desktop: the foreground lock keeps the form from coming to front. Test the overlay mechanics on a
    # copy of LdKitCap whose foreground checks are stubbed true (LdKitCapT, test-only); foreground keeping = SKIP here
    # (the real run logs 'lost front ...' if it ever happens; the overlay has WS_EX_NOACTIVATE + SW_SHOWNOACTIVATE).
    'SKIP  foreground checks (hidden desktop); overlay mechanics on test-only LdKitCapT'
    $src = $hs.Value.Replace('class LdKitCap', 'class LdKitCapT').Replace('GetForegroundWindow() != h', 'h == new IntPtr(-7)')
    if ($src -eq $hs.Value -or $src.Contains('GetForegroundWindow() != h')) { Check 'test copy built' $false ''; exit 1 }
    Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition $src
    $png = "$Out\form-screen.png"; Remove-Item -LiteralPath $png -ErrorAction SilentlyContinue
    $th = [OvProbe]::Watch([OvProbe]::GetForegroundWindow(), 1500)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $r = try { [LdKitCapT]::ScreenCopy($h, $png) } catch { "EXCEPTION $($_.Exception.InnerException.Message)" }
    $ms = $sw.ElapsedMilliseconds; $th.Join()
    $hidden = ($r -eq 'EXCEPTION The handle is invalid')
    if ($hidden) { "SKIP  CopyFromScreen itself (hidden desktop: $r; same call as the rated kit, which wrote PNGs on the real desktop in the 02:29 run)" }
    else { Check 'ScreenCopy returns screen copy' ($r -eq 'screen copy') $r }
    Check 'took >= SettleMs and < 2 s' ($ms -ge 500 -and $ms -lt 2000) "$ms ms"
    Check 'overlay seen during the copy' ([OvProbe]::Seen -gt 0) "polls $([OvProbe]::Seen)"
    $want = 0x80000 -bor 0x20 -bor 0x8 -bor 0x08000000 -bor 0x80
    Check 'overlay ex-style has layered|transparent|topmost|noactivate|toolwindow' ((([OvProbe]::ExStyle) -band $want) -eq $want) ('0x{0:X8}' -f [OvProbe]::ExStyle)
    Check 'overlay destroyed afterwards (also after an exception)' ([OvProbe]::FindWindowW('Static', 'ld-kit-compose') -eq [IntPtr]::Zero) ''
    Check 'overlay did not change the foreground window' (-not [OvProbe]::FgLost) "lost $([OvProbe]::FgLost)"
    if ($hidden) { 'SKIP  PNG checks (hidden desktop)' }
    elseif (Test-Path -LiteralPath $png) {
        $nb = [LdKitCap]::NonBlack($png)
        $b = New-Object System.Drawing.Bitmap $png; $c = $b.GetPixel([int]($b.Width / 2), [int]($b.Height / 2)); $sz = "$($b.Width)x$($b.Height)"; $b.Dispose()
        Check 'PNG written, client non-black >= 2%' ($nb -ge 0.02) ('{0:N1}%, {1}, centre {2},{3},{4}' -f (100 * $nb), $sz, $c.R, $c.G, $c.B)
        Check 'centre pixel = form colour within 3 levels (alpha-1 overlay invisible)' ([Math]::Abs($c.R - 200) -le 3 -and [Math]::Abs($c.G - 40) -le 3 -and [Math]::Abs($c.B - 40) -le 3) "$($c.R),$($c.G),$($c.B)"
    } else { Check 'PNG written' $false $png }
    $r2 = [LdKitCap]::ScreenCopy($h, "$Out\x2.png")
    Check 'real LdKitCap, form not foreground -> refuses, no overlay' ($r2 -eq 'not in front (no screen copy)' -and [OvProbe]::FindWindowW('Static', 'ld-kit-compose') -eq [IntPtr]::Zero) $r2
}
$f.Close(); $f.Dispose()
"RESULT: $(if ($bad) { "FAIL ($bad)" } else { 'PASS' })"
exit [int]($bad -gt 0)
