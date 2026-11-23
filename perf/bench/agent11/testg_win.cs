// Win32 helpers for bench/agent11/testg_driver.ps1 and testg_launch.ps1 (test G, task #19).
// Loaded with Add-Type by Windows PowerShell 5.1, so C# 5 only (no $"..", no => members, no ?.).
//   MainWindow, Describe  the game's largest visible top-level window
//   PostFocus             posts the focus messages SDL 3.5 handles: WM_NCACTIVATE, WM_ACTIVATE and
//                         WM_KILLFOCUS / WM_SETFOCUS. SDL's WIN_UpdateFocus (thirdparty/sdl3
//                         src/video/windows/SDL_windowsevents.c:324-333) only acts when
//                         GetForegroundWindow() agrees, so a posted focus gain is ignored while the
//                         desktop is locked (and a posted loss is ignored while the game is in front).
//   Ping, IsHung          SendMessageTimeout(WM_NULL, SMTO_ABORTIFHUNG): is the UI thread pumping?
//                         SetGuestPaused runs on that thread, so a stuck unpause silences it.
//   DesktopState          foreground window and input desktop (not accessible = locked)
//   LogTail               incremental, shared-read reader for game.log (survives rotation)
//   ContainsAscii         does a binary contain a cvar name (warns when a build lacks a cvar)
//   MiniDump              small dump (threads, stacks, handles) of a hung game
//   HardLink, CloseAll    run-dir mirror; WM_CLOSE to the game's windows
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

public static class TestGWin
{
    delegate bool EnumProc(IntPtr h, IntPtr l);
    [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }

    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindow(IntPtr h);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", SetLastError = true)] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
    [DllImport("user32.dll", SetLastError = true)] static extern IntPtr SendMessageTimeout(IntPtr h, uint m, IntPtr w, IntPtr l, uint flags, uint timeoutMs, out IntPtr result);
    [DllImport("user32.dll")] static extern bool IsHungAppWindow(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", SetLastError = true)] static extern IntPtr OpenInputDesktop(uint flags, bool inherit, uint access);
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool GetUserObjectInformation(IntPtr h, int index, StringBuilder info, int lengthBytes, out int needed);
    [DllImport("user32.dll")] static extern bool CloseDesktop(IntPtr h);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool CreateHardLink(string newFile, string existing, IntPtr sa);
    [DllImport("dbghelp.dll", SetLastError = true)] static extern bool MiniDumpWriteDump(IntPtr process, uint pid, SafeFileHandle file, uint type, IntPtr exception, IntPtr userStream, IntPtr callback);

    const uint WM_NULL = 0x0000, WM_ACTIVATE = 0x0006, WM_SETFOCUS = 0x0007, WM_KILLFOCUS = 0x0008;
    const uint WM_CLOSE = 0x0010, WM_NCACTIVATE = 0x0086, SMTO_ABORTIFHUNG = 0x0002;

    static List<IntPtr> Windows(int pid)
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

    public static IntPtr MainWindow(int pid)
    {
        IntPtr best = IntPtr.Zero;
        long area = -1;
        foreach (IntPtr h in Windows(pid))
        {
            RECT r;
            GetWindowRect(h, out r);
            long a = (long)(r.R - r.L) * (r.B - r.T);
            if (a > area) { area = a; best = h; }
        }
        return best;
    }

    public static bool IsAlive(IntPtr h) { return h != IntPtr.Zero && IsWindow(h); }

    public static string Describe(IntPtr h)
    {
        if (!IsAlive(h)) return "no window";
        RECT r;
        GetWindowRect(h, out r);
        var t = new StringBuilder(256);
        GetWindowText(h, t, t.Capacity);
        var c = new StringBuilder(256);
        GetClassName(h, c, c.Capacity);
        return string.Format("0x{0:X} class={1} title='{2}' {3}x{4}, {5}{6}", h.ToInt64(), c, t, r.R - r.L, r.B - r.T,
            GetForegroundWindow() == h ? "foreground" : "not foreground", IsIconic(h) ? ", minimised" : "");
    }

    // Posts what a real focus switch delivers: losing = WM_NCACTIVATE(FALSE), WM_ACTIVATE(WA_INACTIVE),
    // WM_KILLFOCUS; gaining = WM_NCACTIVATE(TRUE), WM_ACTIVATE(WA_ACTIVE), WM_SETFOCUS.
    public static string PostFocus(IntPtr h, bool gain)
    {
        uint[] msgs = gain ? new uint[] { WM_NCACTIVATE, WM_ACTIVATE, WM_SETFOCUS }
                           : new uint[] { WM_NCACTIVATE, WM_ACTIVATE, WM_KILLFOCUS };
        var sb = new StringBuilder();
        foreach (uint m in msgs)
        {
            IntPtr w = (m == WM_NCACTIVATE || m == WM_ACTIVATE) ? new IntPtr(gain ? 1 : 0) : IntPtr.Zero;
            bool ok = PostMessage(h, m, w, IntPtr.Zero);
            if (sb.Length > 0) sb.Append(' ');
            sb.AppendFormat("0x{0:X4}:{1}", m, ok ? "ok" : ("error" + Marshal.GetLastWin32Error()));
        }
        return sb.ToString();
    }

    // Milliseconds until the window's thread answered WM_NULL; -1 if it did not answer within
    // timeoutMs, or Windows already treats it as hung (SMTO_ABORTIFHUNG returns at once then).
    public static int Ping(IntPtr h, int timeoutMs)
    {
        IntPtr res;
        var sw = Stopwatch.StartNew();
        IntPtr ok = SendMessageTimeout(h, WM_NULL, IntPtr.Zero, IntPtr.Zero, SMTO_ABORTIFHUNG, (uint)timeoutMs, out res);
        return ok == IntPtr.Zero ? -1 : (int)sw.ElapsedMilliseconds;
    }

    public static bool IsHung(IntPtr h) { return IsHungAppWindow(h); }

    public static string DesktopState()
    {
        string desk;
        IntPtr d = OpenInputDesktop(0, false, 0x0001);   // DESKTOP_READOBJECTS
        if (d == IntPtr.Zero)
            desk = "input desktop not accessible (error " + Marshal.GetLastWin32Error() + ": locked, or a secure desktop is up)";
        else
        {
            var sb = new StringBuilder(256);
            int needed;
            desk = GetUserObjectInformation(d, 2, sb, sb.Capacity * 2, out needed) ? "input desktop '" + sb + "'" : "input desktop open";
            CloseDesktop(d);
        }
        return string.Format("foreground window 0x{0:X}; {1}", GetForegroundWindow().ToInt64(), desk);
    }

    public static int CloseAll(int pid)
    {
        int n = 0;
        foreach (IntPtr h in Windows(pid)) if (PostMessage(h, WM_CLOSE, IntPtr.Zero, IntPtr.Zero)) n++;
        return n;
    }

    public static bool HardLink(string newFile, string existing) { return CreateHardLink(newFile, existing, IntPtr.Zero); }

    public static bool ContainsAscii(string path, string text)
    {
        byte[] needle = Encoding.ASCII.GetBytes(text);
        const int chunk = 8 << 20;
        var buf = new byte[chunk + needle.Length];
        using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
        {
            int carry = 0;
            while (true)
            {
                int n = fs.Read(buf, carry, chunk);
                if (n <= 0) return false;
                int total = carry + n, last = total - needle.Length, i = 0;
                while (i <= last)
                {
                    int k = Array.IndexOf<byte>(buf, needle[0], i, last - i + 1);
                    if (k < 0) break;
                    int j = 1;
                    while (j < needle.Length && buf[k + j] == needle[j]) j++;
                    if (j == needle.Length) return true;
                    i = k + 1;
                }
                carry = Math.Min(needle.Length - 1, total);
                Buffer.BlockCopy(buf, total - carry, buf, 0, carry);
            }
        }
    }

    // MiniDumpWithHandleData | MiniDumpWithUnloadedModules | MiniDumpWithThreadInfo: every thread's
    // stack plus the handle table, a few MB. There are no PDBs: resolve with legodimensions.map.
    public static string MiniDump(int pid, string path)
    {
        try
        {
            using (Process p = Process.GetProcessById(pid))
            using (var fs = new FileStream(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None))
            {
                bool ok = MiniDumpWriteDump(p.Handle, (uint)pid, fs.SafeFileHandle, 0x0004 | 0x0020 | 0x1000, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
                int err = Marshal.GetLastWin32Error();
                return ok ? ("written, " + fs.Length + " bytes") : ("failed, error 0x" + err.ToString("X8"));
            }
        }
        catch (Exception e) { return "failed: " + e.Message; }
    }

    // Complete lines appended to a log since the last call; a trailing partial line waits for its
    // newline. Opens with shared read/write/delete each time, so spdlog keeps writing and rotating.
    public sealed class LogTail
    {
        readonly string path;
        long pos;
        byte[] carry = new byte[0];

        public LogTail(string path, bool fromStart)
        {
            this.path = path;
            if (!fromStart && File.Exists(path)) pos = new FileInfo(path).Length;
        }

        public string[] Read()
        {
            var lines = new List<string>();
            if (!File.Exists(path)) return lines.ToArray();
            byte[] data;
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
            {
                long len = fs.Length;
                if (len < pos) { pos = 0; carry = new byte[0]; }   // rotated or truncated
                if (len == pos) return lines.ToArray();
                fs.Seek(pos, SeekOrigin.Begin);
                int want = (int)Math.Min(len - pos, 64L << 20);
                data = new byte[carry.Length + want];
                Buffer.BlockCopy(carry, 0, data, 0, carry.Length);
                int got = 0;
                while (got < want)
                {
                    int k = fs.Read(data, carry.Length + got, want - got);
                    if (k <= 0) break;
                    got += k;
                }
                pos += got;
                if (got < want) Array.Resize(ref data, carry.Length + got);
            }
            int start = 0;
            for (int i = 0; i < data.Length; i++)
            {
                if (data[i] != (byte)'\n') continue;
                int end = (i > start && data[i - 1] == (byte)'\r') ? i - 1 : i;
                lines.Add(Encoding.UTF8.GetString(data, start, end - start));
                start = i + 1;
            }
            carry = new byte[data.Length - start];
            Buffer.BlockCopy(data, start, carry, 0, carry.Length);
            return lines.ToArray();
        }
    }
}
