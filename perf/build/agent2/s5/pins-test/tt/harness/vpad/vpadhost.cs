// harness/vpad/vpadhost.cs - Agent 3's input-script runner for harness/run-game.ps1 -InputScript.
// Harness-only test tooling (perf-notes/agent3-run-harness.md section 7). It creates the 4 KiB pad state file that
// the virtual pad (harness/vpad/xinput1_4.c, copied into the run dir) maps, runs the script on a background thread
// and logs each step to input.csv with the pad's call counters, the perf.csv scene (median draw calls and vertices
// over the last 30 frames) and the game.log position, so a blind route can be followed afterwards.
// Script: one command per line; '#' starts a comment; "double quotes" group an argument (a regex).
//   wait_first_frame [timeout_s=240]       perf.csv has a frame row (or is over 1 KiB while the game holds it unshared)
//   wait_perf_rows N [timeout_s=60]        perf.csv has N frame rows
//   wait_log "regex" [timeout_s=60]        a game.log line after the previous wait_log match matches
//   wait_scene DRAWS VERTICES [timeout_s=60]  the perf.csv scene (median draws and vertices of the last 30 frames) is this
//   wait_change [timeout_s=30]             the scene differs from the one at the last mark
//   (wait_perf_rows, wait_scene and wait_change need a readable perf.csv. The real game opens it unshared, so there they
//   return "n/a: ..." at once instead of waiting: use sleeps, and the perf_bytes column to find the scene afterwards.)
//   sleep S
//   press BTN[+BTN] [count=1] [hold_ms=200] [gap_ms=600]
//   hold BTN[+BTN] MS
//   stick L|R X Y MS                       -32768..32767; back to the centre after MS
//   trigger L|R V MS                       0..255
//   connect MASK                           bit n = slot n (slot 0 is connected from the start)
//   mark LABEL...                          an input.csv row with the scene at this point
//   stop                                   end the run now (the harness closes the game as usual)
// A timed-out wait is logged as TIMEOUT and the script goes on. Buttons: A B X Y START BACK UP DOWN LEFT RIGHT LB RB
// LS RS GUIDE, joined with '+'. Only slot 0 is driven. C# 5 (Windows PowerShell 5.1 Add-Type).
// Start() begins with ResetRun(), so one PowerShell process can run several scripts in turn (Agent 8's run-matrix.ps1
// calls run-timing.ps1 in-process). Before it, a second Start() in the same process ran no steps (abort stayed set)
// and reported the first run's counters.
using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

public static class Agent3Input
{
    public const int Magic = 0x31444150, FileSize = 4096;
    const int OffVersion = 4, OffConnected = 8, OffDllPid = 12, OffReads = 16, OffActive = 32, OffCaps = 48, OffKeyCalls = 52,
        OffKeyEvents = 56, OffSetCalls = 60, OffEnableCalls = 64, OffMaps = 88, OffSlot0 = 128, OffDllPath = 192;
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateFileW(string name, uint access, uint share, IntPtr sa, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr CreateFileMappingW(IntPtr file, IntPtr sa, uint protect, uint sizeHigh, uint sizeLow, IntPtr name);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr MapViewOfFile(IntPtr mapping, uint access, uint offsetHigh, uint offsetLow, UIntPtr bytes);
    [DllImport("kernel32.dll")] static extern bool UnmapViewOfFile(IntPtr address);
    [DllImport("kernel32.dll")] static extern bool FlushViewOfFile(IntPtr address, UIntPtr bytes);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);

    sealed class Step { public int Line; public string Cmd, Text; public string[] A; }

    // Incremental reader of a file another process is appending to.
    sealed class Tail
    {
        readonly string path;
        long pos;
        readonly StringBuilder part = new StringBuilder();
        public long Lines, Bytes;
        public bool Locked; // the last Read() found the file but could not open it (the game opens perf.csv unshared)
        public Tail(string p) { path = p; }
        public List<string> Read()
        {
            var lines = new List<string>();
            if (string.IsNullOrEmpty(path)) return lines;
            try
            {
                using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
                {
                    Locked = false;
                    long len = fs.Length;
                    if (len < pos) { pos = 0; part.Length = 0; }
                    if (len == pos) return lines;
                    fs.Seek(pos, SeekOrigin.Begin);
                    var buf = new byte[(int)Math.Min(len - pos, 4 << 20)];
                    int n = fs.Read(buf, 0, buf.Length);
                    pos += n;
                    Bytes = pos;
                    part.Append(Encoding.UTF8.GetString(buf, 0, n));
                }
            }
            catch (FileNotFoundException) { return lines; }
            catch (DirectoryNotFoundException) { return lines; }
            catch (IOException) { Locked = File.Exists(path); return lines; }
            catch (UnauthorizedAccessException) { return lines; }
            string s = part.ToString();
            int start = 0, nl;
            while ((nl = s.IndexOf('\n', start)) >= 0) { lines.Add(s.Substring(start, nl - start).TrimEnd('\r')); start = nl + 1; Lines++; }
            part.Length = 0;
            part.Append(s, start, s.Length - start);
            return lines;
        }
    }

    static readonly List<Step> steps = new List<Step>();
    static readonly Dictionary<string, int> Btn = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase) {
        { "A", 0x1000 }, { "B", 0x2000 }, { "X", 0x4000 }, { "Y", 0x8000 }, { "START", 0x0010 }, { "BACK", 0x0020 },
        { "UP", 0x0001 }, { "DOWN", 0x0002 }, { "LEFT", 0x0004 }, { "RIGHT", 0x0008 }, { "LB", 0x0100 }, { "RB", 0x0200 },
        { "LS", 0x0040 }, { "RS", 0x0080 }, { "GUIDE", 0x0400 } };
    static readonly object padLock = new object();
    static IntPtr file = IntPtr.Zero, map = IntPtr.Zero, view = IntPtr.Zero;
    static StreamWriter csv;
    static Thread worker;
    static Stopwatch clock;
    static double t0;
    static volatile bool abort;
    static Tail logTail = new Tail(null), perfTail = new Tail(null);
    static readonly List<string> logLines = new List<string>();
    static int logCursor;
    static bool perfHeaderSeen;
    static long perfRows, lastPollMs = -1000;
    static readonly long[] ringDraws = new long[30], ringVerts = new long[30];
    static long ringN;
    static int curLine, padButtons, padLt, padRt, padLx, padLy, padRx, padRy;
    static volatile string current = "not started";
    // The real game opens perf.csv unshared (rexglue-sdk core/perf/counter.cpp: OpenFile "w" = _wfopen_s), so while it
    // runs only the file size can be read (GetFileAttributesEx needs no share access); the scene waits then return n/a.
    static string perfPath;
    static bool perfLockedSeen;
    static long PerfBytes() { try { return string.IsNullOrEmpty(perfPath) ? 0 : new FileInfo(perfPath).Length; } catch (Exception) { return 0; } }
    static string NoLiveScene() { return perfTail.Locked && perfRows == 0 ? "n/a: perf.csv is locked by the game (no live scene)" : null; }

    public static volatile bool StopRequested;
    public static volatile int StepsDone;
    public static int Timeouts;
    public static string TimeoutLines = "", Error;
    public static int StepsTotal { get { return steps.Count; } }
    public static string Status() { return current; }

    // ---- script ----
    public static string Load(string scriptPath)
    {
        steps.Clear();
        string[] lines = File.ReadAllLines(scriptPath);
        for (int i = 0; i < lines.Length; i++)
        {
            List<string> t = Tokens(lines[i]);
            string where = Path.GetFileName(scriptPath) + ":" + (i + 1).ToString(Inv) + ": ";
            if (t == null) return where + "unterminated quote";
            if (t.Count == 0) continue;
            var st = new Step { Line = i + 1, Cmd = t[0].ToLowerInvariant(), A = t.GetRange(1, t.Count - 1).ToArray(), Text = lines[i].Trim() };
            string err = Check(st);
            if (err != null) return where + err;
            steps.Add(st);
        }
        return steps.Count == 0 ? Path.GetFileName(scriptPath) + ": no steps" : null;
    }

    static List<string> Tokens(string line)
    {
        var t = new List<string>();
        var sb = new StringBuilder();
        bool quoted = false, any = false;
        foreach (char ch in line)
        {
            if (quoted) { if (ch == '"') quoted = false; else sb.Append(ch); continue; }
            if (ch == '"') { quoted = true; any = true; continue; }
            if (ch == '#') break;
            if (char.IsWhiteSpace(ch)) { if (any) { t.Add(sb.ToString()); sb.Length = 0; any = false; } continue; }
            sb.Append(ch);
            any = true;
        }
        if (quoted) return null;
        if (any) t.Add(sb.ToString());
        return t;
    }

    static string Check(Step s)
    {
        string[] a = s.A;
        switch (s.Cmd)
        {
            case "wait_first_frame": return Count(a, 0, 1) ?? Num(a, 0, false);
            case "wait_perf_rows": return Count(a, 1, 2) ?? Int(a, 0, 1, int.MaxValue) ?? Num(a, 1, false);
            case "wait_log":
                if (Count(a, 1, 2) != null) return Count(a, 1, 2);
                try { new Regex(a[0]); } catch (ArgumentException e) { return "bad regex: " + e.Message; }
                return Num(a, 1, false);
            case "sleep": return Count(a, 1, 1) ?? Num(a, 0, true);
            case "wait_scene": return Count(a, 2, 3) ?? Int(a, 0, 0, int.MaxValue) ?? Int(a, 1, 0, int.MaxValue) ?? Num(a, 2, false);
            case "wait_change": return Count(a, 0, 1) ?? Num(a, 0, false);
            case "press": return Count(a, 1, 4) ?? Mask(a[0]) ?? Int(a, 1, 1, 1000) ?? Int(a, 2, 1, 60000) ?? Int(a, 3, 0, 60000);
            case "hold": return Count(a, 2, 2) ?? Mask(a[0]) ?? Int(a, 1, 1, 600000);
            case "stick": return Count(a, 4, 4) ?? Side(a[0]) ?? Int(a, 1, -32768, 32767) ?? Int(a, 2, -32768, 32767) ?? Int(a, 3, 1, 600000);
            case "trigger": return Count(a, 3, 3) ?? Side(a[0]) ?? Int(a, 1, 0, 255) ?? Int(a, 2, 1, 600000);
            case "connect": return Count(a, 1, 1) ?? Int(a, 0, 0, 15);
            case "mark": return Count(a, 1, 99);
            case "stop": return Count(a, 0, 0);
        }
        return "unknown command '" + s.Cmd + "'";
    }
    static string Count(string[] a, int min, int max)
    {
        return a.Length < min || a.Length > max ? string.Format(Inv, "wants {0}..{1} arguments, has {2}", min, max, a.Length) : null;
    }
    static string Int(string[] a, int i, int min, int max)
    {
        int v;
        if (i >= a.Length) return null;
        return int.TryParse(a[i], NumberStyles.Integer, Inv, out v) && v >= min && v <= max ? null
            : string.Format(Inv, "argument {0} '{1}' is not an integer in {2}..{3}", i + 1, a[i], min, max);
    }
    static string Num(string[] a, int i, bool required)
    {
        double v;
        if (i >= a.Length) return required ? "missing number" : null;
        return double.TryParse(a[i], NumberStyles.Float, Inv, out v) && v >= 0 ? null : string.Format(Inv, "argument {0} '{1}' is not a number >= 0", i + 1, a[i]);
    }
    static string Mask(string s)
    {
        int m;
        return ParseMask(s, out m) ? null : "bad button(s) '" + s + "' (A B X Y START BACK UP DOWN LEFT RIGHT LB RB LS RS GUIDE, joined with +)";
    }
    static string Side(string s) { return string.Equals(s, "L", StringComparison.OrdinalIgnoreCase) || string.Equals(s, "R", StringComparison.OrdinalIgnoreCase) ? null : "want L or R, not '" + s + "'"; }
    static bool ParseMask(string s, out int m)
    {
        m = 0;
        foreach (string p in s.Split('+')) { int b; if (!Btn.TryGetValue(p.Trim(), out b)) return false; m |= b; }
        return m != 0;
    }
    static int I(string[] a, int i, int dflt) { return i < a.Length ? int.Parse(a[i], NumberStyles.Integer, Inv) : dflt; }
    static double D(string[] a, int i, double dflt) { return i < a.Length ? double.Parse(a[i], NumberStyles.Float, Inv) : dflt; }

    // ---- state file ----
    static string OpenState(string path)
    {
        file = CreateFileW(path, 0xC0000000u, 7u, IntPtr.Zero, 2u /* CREATE_ALWAYS */, 0x80u, IntPtr.Zero);
        if (file == new IntPtr(-1)) { file = IntPtr.Zero; return "CreateFileW(" + path + ") failed: " + Marshal.GetLastWin32Error(); }
        map = CreateFileMappingW(file, IntPtr.Zero, 0x04u, 0, (uint)FileSize, IntPtr.Zero);
        if (map == IntPtr.Zero) return "CreateFileMappingW failed: " + Marshal.GetLastWin32Error();
        view = MapViewOfFile(map, 0x0006u, 0, 0, new UIntPtr((uint)FileSize));
        if (view == IntPtr.Zero) return "MapViewOfFile failed: " + Marshal.GetLastWin32Error();
        Marshal.WriteInt32(view, OffVersion, 1);
        Marshal.WriteInt32(view, OffConnected, 1);
        Thread.MemoryBarrier();
        Marshal.WriteInt32(view, 0, Magic);
        return null;
    }
    static int R(int off) { return view == IntPtr.Zero ? -1 : Marshal.ReadInt32(view, off); }

    // Seqlock write of slot 0 (harness/vpad/xinput1_4.c ReadSlot).
    static void WritePad()
    {
        IntPtr s = view + OffSlot0;
        int seq = Marshal.ReadInt32(s);
        Marshal.WriteInt32(s, seq + 1);
        Thread.MemoryBarrier();
        Marshal.WriteInt16(s, 4, (short)padButtons);
        Marshal.WriteByte(s, 6, (byte)padLt);
        Marshal.WriteByte(s, 7, (byte)padRt);
        Marshal.WriteInt16(s, 8, (short)padLx);
        Marshal.WriteInt16(s, 10, (short)padLy);
        Marshal.WriteInt16(s, 12, (short)padRx);
        Marshal.WriteInt16(s, 14, (short)padRy);
        Thread.MemoryBarrier();
        Marshal.WriteInt32(s, seq + 2);
    }
    static void SetButtons(int m) { lock (padLock) { padButtons = m; WritePad(); } }
    static void SetStick(bool left, int x, int y) { lock (padLock) { if (left) { padLx = x; padLy = y; } else { padRx = x; padRy = y; } WritePad(); } }
    static void SetTrigger(bool left, int v) { lock (padLock) { if (left) padLt = v; else padRt = v; WritePad(); } }

    // ---- run ----
    public static string Start(string scriptPath, string statePath, string inputCsv, string gameLog, string perfCsv)
    {
        string e = ResetRun();
        if (e != null) return e;
        e = Load(scriptPath);
        if (e != null) return e;
        e = OpenState(statePath);
        if (e != null) return e;
        logTail = new Tail(gameLog);
        perfTail = new Tail(perfCsv);
        perfPath = perfCsv;
        csv = new StreamWriter(new FileStream(inputCsv, FileMode.Create, FileAccess.Write, FileShare.Read));
        csv.AutoFlush = true;
        csv.WriteLine("t_s,line,cmd,args,result,pad_reads,pad_active_reads,key_calls,key_events,perf_rows,perf_bytes,scene_draws,scene_vertices,log_lines,log_bytes");
        return null;
    }

    // Per-run state back to that of a fresh process: stops a step thread that is still alive, releases the files of a
    // run that never got to Finish() and clears every per-run field. Start() calls it first (a no-op in a fresh process).
    public static string ResetRun()
    {
        abort = true;
        if (worker != null && worker.IsAlive && !worker.Join(5000)) return "the previous script thread is still running 5 s after the stop";
        worker = null;
        if (csv != null) { try { csv.Close(); } catch (Exception) { } csv = null; }
        if (view != IntPtr.Zero) { UnmapViewOfFile(view); view = IntPtr.Zero; }
        if (map != IntPtr.Zero) { CloseHandle(map); map = IntPtr.Zero; }
        if (file != IntPtr.Zero) { CloseHandle(file); file = IntPtr.Zero; }
        lock (padLock) { padButtons = padLt = padRt = padLx = padLy = padRx = padRy = 0; }
        clock = null; t0 = 0;
        logTail = new Tail(null); perfTail = new Tail(null); perfPath = null;
        logLines.Clear(); logCursor = 0;
        perfHeaderSeen = false; perfRows = 0; lastPollMs = -1000; perfLockedSeen = false;
        Array.Clear(ringDraws, 0, ringDraws.Length); Array.Clear(ringVerts, 0, ringVerts.Length); ringN = 0;
        curLine = 0; markDraws = markVerts = -1;
        StopRequested = false; StepsDone = 0; Timeouts = 0; TimeoutLines = ""; Error = null;
        current = "not started";
        abort = false;
        return null;
    }

    public static void Go(double startS)
    {
        t0 = startS;
        clock = Stopwatch.StartNew();
        Row(0, "start", "", "slot 0 connected; " + steps.Count.ToString(Inv) + " steps");
        worker = new Thread(Run) { IsBackground = true, Name = "agent3-input" };
        worker.Start();
    }

    static double T() { return clock == null ? 0 : t0 + clock.Elapsed.TotalSeconds; }

    static void Run()
    {
        try
        {
            for (int i = 0; i < steps.Count && !abort; i++)
            {
                Step st = steps[i];
                curLine = st.Line;
                current = string.Format(Inv, "{0}/{1} L{2} {3}", i + 1, steps.Count, st.Line, Trunc(st.Text, 60)).Replace(',', ';');
                string result = Exec(st);
                Row(st.Line, st.Cmd, string.Join(" ", st.A), result);
                if (!abort) StepsDone = i + 1;
            }
            current = abort ? "halted" : "done";
        }
        catch (Exception ex)
        {
            Error = ex.GetType().Name + ": " + ex.Message;
            current = "error";
            try { Row(curLine, "error", "", Error); } catch (Exception) { }
        }
        finally
        {
            lock (padLock) { padButtons = padLt = padRt = padLx = padLy = padRx = padRy = 0; if (view != IntPtr.Zero) WritePad(); }
        }
    }

    static long markDraws = -1, markVerts = -1; // the scene at the last mark (wait_change)

    static string Exec(Step s)
    {
        string[] a = s.A;
        switch (s.Cmd)
        {
            case "wait_first_frame": return WaitFor(delegate { return perfRows >= 1 || PerfBytes() > 1024; }, D(a, 0, 240), null);
            case "wait_scene":
                {
                    long d = I(a, 0, 0), v = I(a, 1, 0);
                    return WaitFor(delegate { return ringN >= 30 && Median(ringDraws) == d && Median(ringVerts) == v; }, D(a, 2, 60), null, true);
                }
            case "wait_change":
                {
                    long d0 = markDraws, v0 = markVerts;
                    var hit = new string[1];
                    return WaitFor(delegate
                    {
                        long d = Median(ringDraws), v = Median(ringVerts);
                        if (ringN == 0 || (d == d0 && v == v0)) return false;
                        hit[0] = string.Format(Inv, "{0}/{1} -> {2}/{3}", d0, v0, d, v);
                        return true;
                    }, D(a, 0, 30), hit, true);
                }
            case "wait_perf_rows": { long n = I(a, 0, 1); return WaitFor(delegate { return perfRows >= n; }, D(a, 1, 60), null, true); }
            case "wait_log":
                {
                    var re = new Regex(a[0]);
                    var hit = new string[1];
                    return WaitFor(delegate
                    {
                        for (; logCursor < logLines.Count; logCursor++)
                            if (re.IsMatch(logLines[logCursor])) { hit[0] = logLines[logCursor]; logCursor++; return true; }
                        return false;
                    }, D(a, 1, 60), hit);
                }
            case "sleep": Sleep(D(a, 0, 0)); return "ok";
            case "press":
                {
                    int m; ParseMask(a[0], out m);
                    int count = I(a, 1, 1), hold = I(a, 2, 200), gap = I(a, 3, 600), k;
                    for (k = 0; k < count && !abort; k++) { SetButtons(m); Sleep(hold / 1000.0); SetButtons(0); Sleep(gap / 1000.0); }
                    return string.Format(Inv, "ok x{0}", k);
                }
            case "hold": { int m; ParseMask(a[0], out m); SetButtons(m); Sleep(I(a, 1, 0) / 1000.0); SetButtons(0); return "ok"; }
            case "stick":
                {
                    bool left = string.Equals(a[0], "L", StringComparison.OrdinalIgnoreCase);
                    SetStick(left, I(a, 1, 0), I(a, 2, 0)); Sleep(I(a, 3, 0) / 1000.0); SetStick(left, 0, 0);
                    return "ok";
                }
            case "trigger":
                {
                    bool left = string.Equals(a[0], "L", StringComparison.OrdinalIgnoreCase);
                    SetTrigger(left, I(a, 1, 0)); Sleep(I(a, 2, 0) / 1000.0); SetTrigger(left, 0);
                    return "ok";
                }
            case "connect": Marshal.WriteInt32(view, OffConnected, I(a, 0, 1)); return "ok";
            case "mark": Poll(true); markDraws = Median(ringDraws); markVerts = Median(ringVerts); return "mark";
            case "stop": StopRequested = true; return "stop requested";
        }
        return "unknown";
    }

    static string WaitFor(Func<bool> cond, double timeoutS, string[] hit, bool needsScene = false)
    {
        var w = Stopwatch.StartNew();
        while (!abort)
        {
            Poll(true);
            if (needsScene && NoLiveScene() != null) return NoLiveScene();
            if (cond())
            {
                string ok = string.Format(Inv, "ok after {0:F1} s", w.Elapsed.TotalSeconds);
                return hit != null && hit[0] != null ? ok + ": " + Trunc(hit[0], 160) : ok;
            }
            if (w.Elapsed.TotalSeconds >= timeoutS)
            {
                Timeouts++;
                TimeoutLines += curLine.ToString(Inv) + " ";
                return string.Format(Inv, "TIMEOUT after {0:F1} s", w.Elapsed.TotalSeconds);
            }
            Thread.Sleep(50);
        }
        return "aborted";
    }

    static void Sleep(double s)
    {
        var w = Stopwatch.StartNew();
        while (!abort)
        {
            double left = s * 1000 - w.Elapsed.TotalMilliseconds;
            if (left <= 0) return;
            Poll(false);
            Thread.Sleep((int)Math.Max(1, Math.Min(20, left)));
        }
    }

    // Reads what the game appended to perf.csv and game.log (at most every 100 ms unless forced).
    static void Poll(bool force)
    {
        long now = clock == null ? 0 : clock.ElapsedMilliseconds;
        if (!force && now - lastPollMs < 100) return;
        lastPollMs = now;
        foreach (string line in perfTail.Read())
        {
            if (!perfHeaderSeen) { perfHeaderSeen = true; if (line.StartsWith("frame_time_us", StringComparison.Ordinal)) continue; }
            string[] f = line.Split(',');
            long dc, vx;
            if (f.Length < 5 || !long.TryParse(f[2], NumberStyles.Integer, Inv, out dc)) continue;
            long.TryParse(f[4], NumberStyles.Integer, Inv, out vx);
            ringDraws[ringN % 30] = dc;
            ringVerts[ringN % 30] = vx;
            ringN++;
            perfRows++;
        }
        if (perfTail.Locked) perfLockedSeen = true;
        List<string> fresh = logTail.Read();
        if (fresh.Count > 0)
        {
            logLines.AddRange(fresh);
            if (logLines.Count > 200000) { int drop = logLines.Count - 200000; logLines.RemoveRange(0, drop); logCursor = Math.Max(0, logCursor - drop); }
        }
    }

    static long Median(long[] ring)
    {
        int k = (int)Math.Min(ringN, ring.Length);
        if (k == 0) return -1;
        var c = new long[k];
        Array.Copy(ring, c, k);
        Array.Sort(c);
        return c[k / 2];
    }

    static void Row(int line, string cmd, string args, string result)
    {
        if (csv == null) return;
        Poll(true);
        lock (csv)
            csv.WriteLine(string.Join(",", new string[] {
                T().ToString("F2", Inv), line.ToString(Inv), cmd, Q(args), Q(result),
                R(OffReads).ToString(Inv), R(OffActive).ToString(Inv), R(OffKeyCalls).ToString(Inv), R(OffKeyEvents).ToString(Inv),
                perfRows.ToString(Inv), PerfBytes().ToString(Inv), Median(ringDraws).ToString(Inv), Median(ringVerts).ToString(Inv),
                logTail.Lines.ToString(Inv), logTail.Bytes.ToString(Inv) }));
    }
    static string Q(string s)
    {
        s = (s ?? "").Replace('\n', ' ').Replace('\r', ' ');
        return s.IndexOfAny(new[] { ',', '"' }) < 0 ? s : "\"" + s.Replace("\"", "\"\"") + "\"";
    }
    static string Trunc(string s, int n) { return s.Length <= n ? s : s.Substring(0, n) + "..."; }

    // End of the run's sampling loop: stop the steps, release everything (the game is still running).
    public static void Halt()
    {
        abort = true;
        if (worker != null && worker.IsAlive) worker.Join(5000);
        lock (padLock) { padButtons = padLt = padRt = padLx = padLy = padRx = padRy = 0; if (view != IntPtr.Zero) WritePad(); }
    }

    // After the game has exited: final counters for run.json, last input.csv row, unmap.
    public static OrderedDictionary Finish()
    {
        var d = new OrderedDictionary();
        d["steps_total"] = steps.Count;
        d["steps_done"] = StepsDone;
        d["last_step"] = current;
        d["timeouts"] = Timeouts;
        d["timeout_lines"] = TimeoutLines.Trim();
        d["stopped_by_script"] = StopRequested;
        d["error"] = Error;
        if (view != IntPtr.Zero)
        {
            d["dll_loaded_by_pid"] = R(OffDllPid);
            d["dll_loaded_from"] = Marshal.PtrToStringUni(view + OffDllPath);
            d["dll_maps"] = R(OffMaps);
            d["pad_reads"] = R(OffReads);
            d["pad_active_reads"] = R(OffActive);
            d["caps_calls"] = R(OffCaps);
            d["key_calls"] = R(OffKeyCalls);
            d["key_events"] = R(OffKeyEvents);
            d["set_state_calls"] = R(OffSetCalls);
            d["enable_calls"] = R(OffEnableCalls);
        }
        Row(0, "end", "", string.Format(Inv, "steps {0}/{1}; timeouts {2}", StepsDone, steps.Count, Timeouts));
        d["perf_rows_seen"] = perfRows;
        d["perf_locked"] = perfLockedSeen;
        d["perf_bytes_at_end"] = PerfBytes();
        d["log_lines_seen"] = logTail.Lines;
        if (csv != null) { csv.Close(); csv = null; }
        if (view != IntPtr.Zero) { FlushViewOfFile(view, UIntPtr.Zero); UnmapViewOfFile(view); view = IntPtr.Zero; }
        if (map != IntPtr.Zero) { CloseHandle(map); map = IntPtr.Zero; }
        if (file != IntPtr.Zero) { CloseHandle(file); file = IntPtr.Zero; }
        return d;
    }
}
