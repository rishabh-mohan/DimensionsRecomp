// Win32 helpers for harness/run-game.ps1, loaded with Add-Type (C# 5, no newer syntax).
//   Windows/Describe  visible top-level windows of a process (dialog text for #32770 message boxes)
//   Shot              PNG of the game window: PrintWindow(PW_RENDERFULLCONTENT); if that comes back
//                     black, a screen copy, but only while the game window is in front, so other
//                     windows on the desktop are never captured
//   CloseAll          WM_CLOSE to every visible window of the process (the game's close button path)
//   Press             one key chord through SendInput, by default only while the game is in front
//                     (the MnK driver ignores keys unless the window has focus)
//   HardLink          CreateHardLink, used to mirror large binaries into the run dir
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

public static class LdHarness
{
    delegate bool EnumProc(IntPtr h, IntPtr l);
    [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Sequential)] struct MOUSEINPUT { public int dx, dy; public uint data, flags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Explicit)] struct UNION { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)] struct INPUT { public uint type; public UNION u; }

    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr p, EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint f);
    [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll", SetLastError = true)] static extern uint SendInput(uint n, INPUT[] i, int size);
    [DllImport("user32.dll")] static extern uint MapVirtualKey(uint c, uint t);
    [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr v);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool CreateHardLink(string f, string e, IntPtr sa);

    static LdHarness()
    {
        // Physical pixels for window rects and captures on a scaled display.
        try { SetProcessDpiAwarenessContext(new IntPtr(-4)); } catch { try { SetProcessDPIAware(); } catch { } }
    }

    public static bool HardLink(string newFile, string existing) { return CreateHardLink(newFile, existing, IntPtr.Zero); }

    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint tid);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern bool GetUserObjectInformation(IntPtr h, int index, StringBuilder info, int len, out int needed);

    // Name of this thread's desktop: "Default" on the user's interactive desktop; agent commands run on
    // a hidden one (e.g. exebox-*), where frame times are not timing results.
    public static string DesktopName()
    {
        var s = new StringBuilder(256);
        int n;
        return GetUserObjectInformation(GetThreadDesktop(GetCurrentThreadId()), 2, s, s.Capacity * 2, out n) ? s.ToString() : "?";
    }

    static string Text(IntPtr h) { var s = new StringBuilder(512); GetWindowText(h, s, s.Capacity); return s.ToString(); }
    static string Class(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, s.Capacity); return s.ToString(); }

    public static List<IntPtr> Windows(int pid)
    {
        var list = new List<IntPtr>();
        EnumWindows(delegate(IntPtr h, IntPtr l)
        {
            uint p;
            GetWindowThreadProcessId(h, out p);
            if (p == (uint)pid && IsWindowVisible(h)) list.Add(h);
            return true;
        }, IntPtr.Zero);
        return list;
    }

    static IntPtr MainWindow(int pid)
    {
        IntPtr best = IntPtr.Zero;
        long area = -1;
        foreach (var h in Windows(pid))
        {
            RECT r;
            GetWindowRect(h, out r);
            long a = (long)(r.R - r.L) * (r.B - r.T);
            if (a > area) { area = a; best = h; }
        }
        return best;
    }

    public static bool IsForeground(int pid)
    {
        uint p;
        GetWindowThreadProcessId(GetForegroundWindow(), out p);
        return p == (uint)pid;
    }

    // One line per window: class|title|WxH|fg/bg/min|dialog text
    public static string[] Describe(int pid)
    {
        var o = new List<string>();
        IntPtr fg = GetForegroundWindow();
        foreach (var h in Windows(pid))
        {
            RECT r;
            GetWindowRect(h, out r);
            string cls = Class(h), extra = "";
            if (cls == "#32770")
            {
                var parts = new List<string>();
                EnumChildWindows(h, delegate(IntPtr c, IntPtr l)
                {
                    string t = Text(c);
                    if (t.Length > 0) parts.Add(t.Replace("\r", " ").Replace("\n", " "));
                    return true;
                }, IntPtr.Zero);
                extra = string.Join(" / ", parts.ToArray());
            }
            o.Add(string.Format("{0}|{1}|{2}x{3}|{4}|{5}", cls, Text(h), r.R - r.L, r.B - r.T,
                h == fg ? "fg" : (IsIconic(h) ? "min" : "bg"), extra));
        }
        return o.ToArray();
    }

    public static string Shot(int pid, string path)
    {
        IntPtr h = MainWindow(pid);
        if (h == IntPtr.Zero) return "no window";
        if (IsIconic(h)) return "window minimised";
        RECT r;
        GetWindowRect(h, out r);
        int w = r.R - r.L, ht = r.B - r.T;
        if (w <= 0 || ht <= 0) return "empty window";
        using (var bmp = new Bitmap(w, ht, PixelFormat.Format32bppArgb))
        {
            using (var g = Graphics.FromImage(bmp))
            {
                IntPtr dc = g.GetHdc();
                try { PrintWindow(h, dc, 2); } finally { g.ReleaseHdc(dc); }
            }
            string how = "printwindow";
            if (IsBlack(bmp))
            {
                if (GetForegroundWindow() == h)
                {
                    using (var g = Graphics.FromImage(bmp)) g.CopyFromScreen(r.L, r.T, 0, 0, new Size(w, ht));
                    how = IsBlack(bmp) ? "screen copy (black)" : "screen copy";
                }
                else how = "printwindow (black; no screen copy because the game window was not in front)";
            }
            bmp.Save(path, ImageFormat.Png);
            return how;
        }
    }

    static bool IsBlack(Bitmap b)
    {
        for (int y = 0; y < 16; y++)
            for (int x = 0; x < 16; x++)
            {
                Color c = b.GetPixel(b.Width * x / 16 + b.Width / 32, b.Height * y / 16 + b.Height / 32);
                if (c.R > 8 || c.G > 8 || c.B > 8) return false;
            }
        return true;
    }

    public static int CloseAll(int pid)
    {
        int n = 0;
        foreach (var h in Windows(pid)) if (PostMessage(h, 0x0010, IntPtr.Zero, IntPtr.Zero)) n++;
        return n;
    }

    static readonly Dictionary<string, int> Vk = BuildVk();

    static Dictionary<string, int> BuildVk()
    {
        var d = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase)
        {
            {"Return", 0x0D}, {"Enter", 0x0D}, {"Escape", 0x1B}, {"Esc", 0x1B}, {"Space", 0x20}, {"Tab", 0x09},
            {"Backspace", 0x08}, {"Left", 0x25}, {"Up", 0x26}, {"Right", 0x27}, {"Down", 0x28}, {"Home", 0x24},
            {"End", 0x23}, {"PageUp", 0x21}, {"PageDown", 0x22}, {"Insert", 0x2D}, {"Delete", 0x2E},
            {"Shift", 0x10}, {"Ctrl", 0x11}, {"Alt", 0x12}, {"Plus", 0xBB}, {"Minus", 0xBD}, {"Grave", 0xC0}
        };
        for (char c = 'A'; c <= 'Z'; c++) d[c.ToString()] = c;
        for (char c = '0'; c <= '9'; c++) d[c.ToString()] = c;
        for (int i = 1; i <= 24; i++) d["F" + i] = 0x6F + i;
        return d;
    }

    static INPUT Key(int vk, bool up)
    {
        var i = new INPUT();
        i.type = 1;
        i.u.ki.wVk = (ushort)vk;
        i.u.ki.wScan = (ushort)MapVirtualKey((uint)vk, 0);
        bool ext = (vk >= 0x21 && vk <= 0x28) || vk == 0x2D || vk == 0x2E;
        i.u.ki.dwFlags = (up ? 2u : 0u) | (ext ? 1u : 0u);
        return i;
    }

    // Presses one chord such as "Return" or "Shift+Tab" for holdMs. Unless force is set, it is sent
    // only when the game window is in front, so keys never land in another application.
    public static string Press(int pid, string chord, int holdMs, bool force)
    {
        var vks = new List<int>();
        foreach (var k in chord.Split('+'))
        {
            int v;
            if (!Vk.TryGetValue(k.Trim(), out v)) return "unknown key '" + k + "'";
            vks.Add(v);
        }
        if (!force && !IsForeground(pid)) return "skipped (game window not in front)";
        int size = Marshal.SizeOf(typeof(INPUT));
        var down = new List<INPUT>();
        var up = new List<INPUT>();
        foreach (var v in vks) down.Add(Key(v, false));
        for (int j = vks.Count - 1; j >= 0; j--) up.Add(Key(vks[j], true));
        uint a = SendInput((uint)down.Count, down.ToArray(), size);
        Thread.Sleep(holdMs);
        uint b = SendInput((uint)up.Count, up.ToArray(), size);
        return (a == down.Count && b == up.Count) ? "sent" : "SendInput failed (error " + Marshal.GetLastWin32Error() + ")";
    }
}
