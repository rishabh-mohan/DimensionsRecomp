// S4aThreads.cs - Agent 3 (S4a task #5): read-only per-thread CPU sampler for one game process.
// One row per live thread per tick: t_s,epoch_s,tid,name,cpu_ms,kernel_ms,user_ms,cycles.
// Opens threads with THREAD_QUERY_LIMITED_INFORMATION only (GetThreadTimes, QueryThreadCycleTime,
// GetThreadDescription); stops when the process exits or after maxSec. Functional runs only, never timing.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

public static class S4aThreads {
    const uint THREAD_QUERY_LIMITED_INFORMATION = 0x0800;
    const uint PROCESS_QUERY_LIMITED_INFORMATION = 0x1000;
    const uint SYNCHRONIZE = 0x00100000;
    const uint TH32CS_SNAPTHREAD = 0x00000004;
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenThread(uint access, bool inherit, uint tid);
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetThreadTimes(IntPtr h, out long c, out long e, out long k, out long u);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool QueryThreadCycleTime(IntPtr h, out ulong cycles);
    [DllImport("kernel32.dll", SetLastError = true)] static extern int GetThreadDescription(IntPtr h, out IntPtr desc);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);
    [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr h, uint ms);
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint pid);
    [StructLayout(LayoutKind.Sequential)]
    struct THREADENTRY32 { public uint dwSize, cntUsage, th32ThreadID, th32OwnerProcessID; public int tpBasePri, tpDeltaPri; public uint dwFlags; }
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool Thread32First(IntPtr s, ref THREADENTRY32 te);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool Thread32Next(IntPtr s, ref THREADENTRY32 te);

    class T { public IntPtr H; public string Name = ""; public long Creation; }

    public static int Rows, Ticks, MaxThreads;
    public static string Reason = "";

    static string ReadName(IntPtr h) {
        IntPtr d;
        try {
            if (GetThreadDescription(h, out d) >= 0 && d != IntPtr.Zero) {
                string s = Marshal.PtrToStringUni(d) ?? "";
                LocalFree(d);
                return s.Replace(',', ';').Replace('\r', ' ').Replace('\n', ' ');
            }
        } catch (EntryPointNotFoundException) { }
        return "";
    }

    public static int Run(int pid, string outPath, int intervalMs, double maxSec) {
        IntPtr ph = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, false, (uint)pid);
        if (ph == IntPtr.Zero) { Reason = "open_process_failed"; return 1; }
        var map = new Dictionary<uint, T>();
        var inv = CultureInfo.InvariantCulture;
        var epoch0 = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        var sw = Stopwatch.StartNew();
        using (var fs = new FileStream(outPath, FileMode.Create, FileAccess.Write, FileShare.ReadWrite | FileShare.Delete))
        using (var w = new StreamWriter(fs, new UTF8Encoding(false))) {
            w.WriteLine("t_s,epoch_s,tid,name,cpu_ms,kernel_ms,user_ms,cycles");
            long k = 0;
            var seen = new HashSet<uint>();
            while (true) {
                double epoch = (DateTime.UtcNow - epoch0).TotalSeconds;
                double t = sw.Elapsed.TotalSeconds;
                IntPtr snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
                int n = 0;
                if (snap != new IntPtr(-1)) {
                    var te = new THREADENTRY32();
                    te.dwSize = (uint)Marshal.SizeOf(typeof(THREADENTRY32));
                    seen.Clear();
                    if (Thread32First(snap, ref te)) {
                        do {
                            if (te.th32OwnerProcessID != (uint)pid) continue;
                            uint tid = te.th32ThreadID;
                            T th;
                            if (!map.TryGetValue(tid, out th)) {
                                th = new T();
                                th.H = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, false, tid);
                                map[tid] = th;
                            }
                            if (th.H == IntPtr.Zero) continue;
                            long c, e, kt, ut; ulong cyc = 0;
                            if (!GetThreadTimes(th.H, out c, out e, out kt, out ut)) continue;
                            if (th.Creation != 0 && th.Creation != c) {   // tid reused by a new thread
                                CloseHandle(th.H);
                                th = new T();
                                th.H = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, false, tid);
                                map[tid] = th;
                                if (th.H == IntPtr.Zero || !GetThreadTimes(th.H, out c, out e, out kt, out ut)) continue;
                            }
                            th.Creation = c;
                            QueryThreadCycleTime(th.H, out cyc);
                            if (th.Name.Length == 0 || k % 10 == 0) th.Name = ReadName(th.H);
                            w.Write(t.ToString("0.000", inv)); w.Write(',');
                            w.Write(epoch.ToString("0.000", inv)); w.Write(',');
                            w.Write(tid.ToString(inv)); w.Write(',');
                            w.Write(th.Name); w.Write(',');
                            w.Write(((kt + ut) / 10000.0).ToString("0.000", inv)); w.Write(',');
                            w.Write((kt / 10000.0).ToString("0.000", inv)); w.Write(',');
                            w.Write((ut / 10000.0).ToString("0.000", inv)); w.Write(',');
                            w.WriteLine(cyc.ToString(inv));
                            n++; Rows++;
                        } while (Thread32Next(snap, ref te));
                    }
                    CloseHandle(snap);
                }
                if (n > MaxThreads) MaxThreads = n;
                w.Flush();
                k++; Ticks++;
                if (t > maxSec) { Reason = "max_sec"; break; }
                long wait = k * (long)intervalMs - sw.ElapsedMilliseconds;
                if (wait < 0) wait = 0;
                if (WaitForSingleObject(ph, (uint)wait) == 0) { Reason = "game_exit"; break; }
            }
        }
        foreach (var th in map.Values) if (th.H != IntPtr.Zero) CloseHandle(th.H);
        CloseHandle(ph);
        return 0;
    }
}
