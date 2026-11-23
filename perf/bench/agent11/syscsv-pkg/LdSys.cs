// LdSys.cs - 1 s system-state sampler behind bench\agent8\run\drivers\sys-csv.ps1 (Agent 8 helper, 2026-11-22).
// sys-csv.ps1 compiles this file ONCE to build\agent8\cache\LdSys-<first 8 hex of SHA256(this file)>.dll and later only
// loads it. Windows PowerShell 5.1 Add-Type = CodeDom csc = C# 5: no $"", no ?., no =>, no out var.
// Read-only queries only: PDH (PdhAddEnglishCounterW = locale-safe paths), user32 input / foreground / input desktop /
// screensaver state, GetSystemPowerStatus, active power scheme + effective power-mode overlay. No child process, no
// window, no setting is changed. The sampling loop (Run) is one blocking call on a Stopwatch schedule: tick k is due at
// t0 + k*interval; a tick late by more than one interval is skipped (counted, no catch-up burst). Between ticks the thread
// waits on the game process handle + a change notification of the stop file's folder (game exit / new stop file seen at
// once); the stop file is checked after a notification and once per tick (fallback without the notification: waits of
// <= 250 ms, check at every wake). The power scheme / overlay RPCs (slow: up to ~1 s per call) run on one background
// thread; rows carry its latest completed values.
// pkg_w,pp0_w,pp1_w,dram_w (last 4 columns, added 2026-11-22 by Agent 11): RAPL power in W of the package / cores (PP0) /
// graphics (PP1) / DRAM, the mean over the last interval, from PDH \Energy Meter(*)\Power (mW; instances
// RAPL_Package<n>_PKG/_PP0/_PP1/_DRAM, summed over packages; _Total and other channels ignored). Blank cells when the
// counterset is missing (e.g. non-Intel or a VM: counters=5/6, failed=[power:0x...]) or a channel has no valid value.
// Purpose: tell a PL1 (package power limit) clamp apart from other causes of the E-core ~550 MHz slow state.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

public static class LdSys
{
    public const string Header = "t_s,epoch_s,wall,idle_s,fg_pid,fg_game,game_alive,input_desktop,screensaver," +
        "cpu_util_pct,cpu_perf_pct,base_mhz,eff_mhz,p_eff_mhz,e_eff_mhz,p_util_pct,e_util_pct," +
        "tz_passive_min_pct,tz_temp_max_c,ac,batt_saver,batt_pct,scheme,overlay,pkg_w,pp0_w,pp1_w,dram_w";

    // ---- results, read by sys-csv.ps1 after Init / Run ----
    public static bool GameGone;          // the game pid was not running at Init (-> header only, reason game_exit)
    public static bool GamePolled;        // no waitable handle (access denied): existence polled once per tick
    public static int CountersOk;         // PDH counters added successfully (of CountersTotal)
    public static int CountersTotal;
    public static string Failed = "";     // "name:0xSTATUS" / "name:no_data" of PDH counters that failed at Init
    public static string PList = "";      // logical processors of the highest EfficiencyClass, "0,1,2,3" ("g:n" if group > 0)
    public static string EList = "";      // all other logical processors ("" when every class is equal)
    public static string ClassInfo = "";  // "P=1,E=0" / "all=0" (not hybrid) / "unknown:<why>"
    public static string Zones = "";      // thermal zone instance names, ";"-separated
    public static string LpFreq = "";     // distinct per-LP Processor Frequency values at Init, e.g. "P:1700,E:1200"
    public static bool OverlayApi;        // powrprof!PowerGetEffectiveOverlayScheme exported
    public static double InitMs;
    public static string Reason = "";     // game_exit | stop_file | max_sec
    public static int Rows;
    public static long Skipped;
    public static double LoopS, LoopCpuS; // wall / own-process CPU seconds of the sampling loop only
    public static double SampleMsMean;    // mean wall ms per sample (collect + all reads + write + flush)
    public static double FirstRowS = -1;  // seconds from driver process creation until the first data row was flushed
    public static double FirstRowT = -1;  // t_s of the first data row
    public static double SampleMsMax;     // max wall ms of one sample (rows after the first)
    public static double FirstSampleMs;   // wall ms of the first sample (includes JIT / first-call costs)
    // CPU: GetProcessTimes (OwnCpuS, LoopCpuS) is sampled at the 15.6 ms clock tick - too coarse for a ~1 ms-per-second
    // load. The *Cyc* / Steady values use QueryProcessCycleTime / QueryThreadCycleTime (TSC cycles) divided by the TSC rate.
    public static double TscMhz;          // HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0 ~MHz (the TSC rate), 0 = unknown
    public static double SteadyCpuPct = -1; // own-process CPU % of one core, end of the first sample -> end of the loop (cycles; ticks if TscMhz = 0)
    public static double SteadyTickCpuPct = -1; // the same from GetProcessTimes
    public static double LoopCycCpuPct = -1;    // own-process CPU % of one core over the whole loop (cycles)
    public static string OwnDesktop = ""; // window station \ desktop of this process (GetForegroundWindow is NULL when not the input desktop)
    public static string InputDesktopAtInit = "";
    public static string StopWatch = "";  // notify (folder change notification) | poll (no notification) | poll(lost) (notification failed later)
    public static long Wakes, StopChecks; // waits between ticks / File.Exists checks of the stop file inside the loop

    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    const long UnixEpochTicks = 621355968000000000L;

    // ---- PDH ----
    // cpu_util_pct / cpu_perf_pct / base_mhz are the "_Total" instance of the (*) counters below: a query that also holds
    // the single \Processor Information(_Total)\... counters collects the counterset twice (+0.4-0.7 ms CPU per row on the
    // test machine, ~40 % of the whole collect). Same counter instance, same values.
    const uint PDH_FMT = 0x00000200u | 0x00008000u;          // PDH_FMT_DOUBLE | PDH_FMT_NOCAP100 (perf/utility go > 100)
    const uint PDH_MORE_DATA = 0x800007D2u;
    const int C_UTIL_ALL = 0, C_PERF_ALL = 1, C_FREQ_ALL = 2, C_TZ_PASSIVE = 3, C_TZ_TEMP = 4, C_POWER = 5, NC = 6;
    const string TOTAL = "_Total";
    static readonly string[] CNames = { "util", "perf", "freq", "tz_passive", "tz_temp", "power" };
    static readonly string[] CPaths = {
        @"\Processor Information(*)\% Processor Utility",
        @"\Processor Information(*)\% Processor Performance",
        @"\Processor Information(*)\Processor Frequency",
        @"\Thermal Zone Information(*)\% Passive Limit",
        @"\Thermal Zone Information(*)\Temperature",
        @"\Energy Meter(*)\Power" };
    static IntPtr query = IntPtr.Zero;
    static readonly IntPtr[] counters = new IntPtr[NC];
    static IntPtr arrBuf = IntPtr.Zero;
    static uint arrBufSize;
    static long preQpc;

    [DllImport("pdh.dll", CharSet = CharSet.Unicode)] static extern uint PdhOpenQueryW(string dataSource, IntPtr userData, out IntPtr query);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode)] static extern uint PdhAddEnglishCounterW(IntPtr query, string path, IntPtr userData, out IntPtr counter);
    [DllImport("pdh.dll")] static extern uint PdhCollectQueryData(IntPtr query);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode)] static extern uint PdhGetFormattedCounterArrayW(IntPtr counter, uint format, ref uint bufferSize, out uint itemCount, IntPtr buffer);
    [DllImport("pdh.dll")] static extern uint PdhCloseQuery(IntPtr query);

    // ---- kernel32 / user32 / powrprof ----
    const uint SYNCHRONIZE = 0x00100000u, PROCESS_QUERY_LIMITED_INFORMATION = 0x1000u;
    const uint WAIT_OBJECT_0 = 0, WAIT_TIMEOUT = 0x102;
    const int ERROR_ACCESS_DENIED = 5, ERROR_MORE_DATA = 234;
    const uint DESKTOP_READOBJECTS = 0x0001;
    const int UOI_NAME = 2;
    const uint SPI_GETSCREENSAVERRUNNING = 0x0072;

    [StructLayout(LayoutKind.Sequential)] struct LASTINPUTINFO { public uint cbSize; public uint dwTime; }
    [StructLayout(LayoutKind.Sequential)] struct SYSTEM_POWER_STATUS
    {
        public byte ACLineStatus; public byte BatteryFlag; public byte BatteryLifePercent; public byte SystemStatusFlag;
        public uint BatteryLifeTime; public uint BatteryFullLifeTime;
    }
    [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate uint OverlayFn(out Guid overlay);

    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr h, uint ms);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern bool GetProcessTimes(IntPtr h, out long creation, out long exit, out long kernel, out long user);
    [DllImport("kernel32.dll")] static extern uint GetTickCount();
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetSystemCpuSetInformation(IntPtr info, uint length, out uint returned, IntPtr process, uint flags);
    [DllImport("kernel32.dll")] static extern bool GetSystemPowerStatus(out SYSTEM_POWER_STATUS s);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern IntPtr LoadLibraryW(string name);
    [DllImport("kernel32.dll", CharSet = CharSet.Ansi, ExactSpelling = true, SetLastError = true)] static extern IntPtr GetProcAddress(IntPtr module, string name);
    [DllImport("user32.dll")] static extern bool GetLastInputInfo(ref LASTINPUTINFO lii);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll", SetLastError = true)] static extern IntPtr OpenInputDesktop(uint flags, bool inherit, uint access);
    [DllImport("user32.dll", SetLastError = true)] static extern bool CloseDesktop(IntPtr h);
    [DllImport("user32.dll", SetLastError = true)] static extern bool GetUserObjectInformationW(IntPtr obj, int index, IntPtr info, uint length, out uint needed);
    [DllImport("user32.dll", SetLastError = true)] static extern bool SystemParametersInfoW(uint action, uint uiParam, ref int pvParam, uint winIni);
    [DllImport("user32.dll")] static extern IntPtr GetProcessWindowStation();   // returned handles must not be closed
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint threadId);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentThread();
    [DllImport("kernel32.dll")] static extern bool QueryThreadCycleTime(IntPtr thread, out ulong cycles);
    [DllImport("kernel32.dll")] static extern bool QueryProcessCycleTime(IntPtr process, out ulong cycles);
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenThread(uint access, bool inherit, uint threadId);
    const uint THREAD_QUERY_LIMITED_INFORMATION = 0x0800u;
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern IntPtr FindFirstChangeNotificationW(string path, bool watchSubtree, uint filter);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool FindNextChangeNotification(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool FindCloseChangeNotification(IntPtr h);
    [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForMultipleObjects(uint count, IntPtr[] handles, bool waitAll, uint ms);
    const uint FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001u, WAIT_FAILED = 0xFFFFFFFFu;
    static readonly IntPtr INVALID_HANDLE_VALUE = new IntPtr(-1);
    [DllImport("powrprof.dll")] static extern uint PowerGetActiveScheme(IntPtr userRootPowerKey, out IntPtr activePolicyGuid);
    [DllImport("powrprof.dll")] static extern uint PowerReadFriendlyName(IntPtr rootPowerKey, ref Guid scheme, IntPtr subGroup, IntPtr setting, IntPtr buffer, ref uint bufferSize);

    // ---- state ----
    static int gamePid;
    static IntPtr hGame = IntPtr.Zero;
    static long originQpc;
    static long createdFt;                                    // own process creation FILETIME (UTC)
    static readonly Dictionary<int, int> lpClass = new Dictionary<int, int>();   // group*1000+index -> EfficiencyClass
    static readonly Dictionary<string, int> nameSet = new Dictionary<string, int>(); // PDH instance -> 1 P, 0 E, -1 skip
    static int maxClass = -1;
    static bool hybrid;
    static OverlayFn overlayFn;
    static IntPtr textBuf = IntPtr.Zero;                       // 1 KB scratch for the desktop name
    static Guid lastScheme;
    static string lastSchemeName;
    static readonly HashSet<string> noted = new HashSet<string>();
    static readonly StringBuilder sb = new StringBuilder(512);
    static readonly List<string> names = new List<string>(32);
    static readonly List<double> vals = new List<double>(32);
    static readonly Dictionary<string, double> freqBy = new Dictionary<string, double>();
    static long sampleTicks, sampleMaxTicks, firstSampleTicks, qAfterFirst;
    static double cpuAfterFirst;
    // Per-part wall time of Sample (diagnostics for the "timing" line of sys-csv.ps1). The first sample is kept apart.
    const int P_COLLECT = 0, P_USER = 1, P_DESK = 2, P_PDH = 3, P_PWR = 4, P_WRITE = 5, NP = 6;
    static readonly string[] PNames = { "collect", "user", "desk", "pdh", "pwr", "write" };
    static readonly long[] partTicks = new long[NP], partMax = new long[NP], partFirst = new long[NP];
    static readonly long[] partCyc = new long[NP], partCycFirst = new long[NP];     // sampling-thread cycles per part
    static ulong markCyc, pcAfterFirst;
    static long sampleCyc, sampleCycMax, firstSampleCyc;
    static int samplerTid;
    static volatile int pollerTid;
    static Dictionary<int, ulong> thrAfterFirst;
    public static string SteadyByThread = "";   // steady CPU % of one core split by thread: sampler / poller / other (PowerShell, CLR) / exited

    static long Mark(int part, long since)
    {
        long now = Stopwatch.GetTimestamp();
        ulong cy = ThreadCyc();
        long d = now - since, dc = (long)(cy - markCyc);
        markCyc = cy;
        if (Rows == 0) { partFirst[part] += d; partCycFirst[part] += dc; }
        else { partTicks[part] += d; partCyc[part] += dc; if (d > partMax[part]) partMax[part] = d; }
        return now;
    }
    static string PartsStr(long[] a, long div, double unitsPerMs)
    {
        var b = new StringBuilder();
        for (int i = 0; i < NP; i++)
        {
            if (i > 0) b.Append(',');
            b.Append(PNames[i]).Append(':').Append((div > 0 && unitsPerMs > 0 ? a[i] / unitsPerMs / div : 0.0).ToString("0.00", Inv));
        }
        return b.ToString();
    }
    static double QpcPerMs { get { return Stopwatch.Frequency / 1000.0; } }
    static double CycPerMs { get { return TscMhz * 1000.0; } }
    public static string PartsFirstMs() { return PartsStr(partFirst, Rows > 0 ? 1 : 0, QpcPerMs); }
    public static string PartsMeanMs() { return PartsStr(partTicks, Rows - 1, QpcPerMs); }
    public static string PartsMaxMs() { return PartsStr(partMax, Rows > 1 ? 1 : 0, QpcPerMs); }
    public static string PartsCpuFirstMs() { return PartsStr(partCycFirst, Rows > 0 ? 1 : 0, CycPerMs); }
    public static string PartsCpuMeanMs() { return PartsStr(partCyc, Rows - 1, CycPerMs); }
    // CPU ms of the sampling thread per sample: first/mean/max (mean and max over the rows after the first)
    public static string SampleCpuMs()
    {
        double u = CycPerMs;
        if (u <= 0) return "";
        return string.Format(Inv, "{0:0.00}/{1:0.00}/{2:0.00}", Rows > 0 ? firstSampleCyc / u : 0.0, Rows > 1 ? sampleCyc / u / (Rows - 1) : 0.0, sampleCycMax / u);
    }

    // ---- power poller. PowerGetActiveScheme / PowerGetEffectiveOverlayScheme are RPCs into the power service that took
    // 0.04-1.1 s per call on the test machine (overlay ~0.9 s every time), far too slow for the sampling thread. They run on
    // a background thread (one round per max(interval, 1 s)); each row uses the latest completed values, blank when the last
    // completed round is older than max(5 s, 3 intervals). ----
    static Thread pollThread;
    static volatile bool pollStop;
    static readonly ManualResetEvent pollReady = new ManualResetEvent(false), pollWake = new ManualResetEvent(false);
    static volatile string pollScheme, pollOverlay;
    static long pollDoneQpc;                                  // Interlocked
    static int pollPeriodMs = 1000;
    static long staleTicks = long.MaxValue;
    public static long PollRounds;
    static long pollSchemeTicks, pollOverlayTicks, pollSchemeMax, pollOverlayMax;
    static long pollSchemeCyc, pollOverlayCyc, pollSchemeCycMax, pollOverlayCycMax;   // poller-thread cycles per call

    static void PollLoop()
    {
        pollerTid = (int)GetCurrentThreadId();
        long freq = Stopwatch.Frequency;
        while (!pollStop)
        {
            long a = Stopwatch.GetTimestamp(); ulong ca = ThreadCyc();
            string s = "";
            try { s = SchemeName(); } catch (Exception ex) { NoteOnce("scheme", "scheme: " + ex.Message); }
            long b = Stopwatch.GetTimestamp(); ulong cb = ThreadCyc();
            string o = "";
            try { o = OverlayName(); } catch (Exception ex) { NoteOnce("overlay", "overlay: " + ex.Message); }
            long c = Stopwatch.GetTimestamp(); ulong cc = ThreadCyc();
            pollScheme = s; pollOverlay = o;
            Interlocked.Exchange(ref pollDoneQpc, c);
            pollSchemeTicks += b - a; if (b - a > pollSchemeMax) pollSchemeMax = b - a;
            pollOverlayTicks += c - b; if (c - b > pollOverlayMax) pollOverlayMax = c - b;
            long dS = (long)(cb - ca), dO = (long)(cc - cb);
            pollSchemeCyc += dS; if (dS > pollSchemeCycMax) pollSchemeCycMax = dS;
            pollOverlayCyc += dO; if (dO > pollOverlayCycMax) pollOverlayCycMax = dO;
            PollRounds++;
            pollReady.Set();
            long spent = (c - a) * 1000 / freq;
            pollWake.WaitOne((int)Math.Max(100, pollPeriodMs - spent));
        }
    }

    public static string PollStats()
    {
        double f = 1000.0 / Stopwatch.Frequency, cy = TscMhz > 0 ? 1.0 / (TscMhz * 1000.0) : 0.0;
        long n = PollRounds;
        return string.Format(Inv, "poll_rounds={0} poll_scheme_ms={1:0.0}/{2:0.0} poll_overlay_ms={3:0.0}/{4:0.0} poll_scheme_cpu_ms={5:0.00}/{6:0.00} poll_overlay_cpu_ms={7:0.00}/{8:0.00}",
            n, n > 0 ? pollSchemeTicks * f / n : 0.0, pollSchemeMax * f, n > 0 ? pollOverlayTicks * f / n : 0.0, pollOverlayMax * f,
            n > 0 ? pollSchemeCyc * cy / n : 0.0, pollSchemeCycMax * cy, n > 0 ? pollOverlayCyc * cy / n : 0.0, pollOverlayCycMax * cy);
    }

    public static string InitParts = "";
    static void IPart(StringBuilder b, string name, ref long t)
    {
        long now = Stopwatch.GetTimestamp();
        if (b.Length > 0) b.Append(',');
        b.Append(name).Append(':').Append(((now - t) * 1000.0 / Stopwatch.Frequency).ToString("0", Inv));
        t = now;
    }

    // Partial failures: one stderr note per distinct key, never fatal.
    static void NoteOnce(string key, string msg)
    {
        lock (noted) { if (!noted.Add(key)) return; }
        try { Console.Error.WriteLine("sys-csv: note: " + msg); Console.Error.Flush(); } catch { }
    }

    static string Clean(string s)
    {
        if (s == null) return "";
        var b = new StringBuilder(s.Length);
        foreach (char c in s) b.Append((c == ',' || c == '"' || c == '\r' || c == '\n' || c == '\t' || c < ' ') ? ' ' : c);
        return b.ToString().Trim();
    }

    public static double OwnCpuS()
    {
        long c, e, k, u;
        return GetProcessTimes(GetCurrentProcess(), out c, out e, out k, out u) ? (k + u) / 1e7 : -1;
    }
    public static double OwnWallS()
    {
        long c, e, k, u;
        if (!GetProcessTimes(GetCurrentProcess(), out c, out e, out k, out u)) return -1;
        return (DateTime.UtcNow.ToFileTimeUtc() - c) / 1e7;
    }
    public static DateTime OwnStartUtc()
    {
        long c, e, k, u;
        return GetProcessTimes(GetCurrentProcess(), out c, out e, out k, out u) ? DateTime.FromFileTimeUtc(c) : DateTime.UtcNow;
    }
    static ulong ThreadCyc() { ulong c; return QueryThreadCycleTime(GetCurrentThread(), out c) ? c : 0; }
    static ulong ProcCyc() { ulong c; return QueryProcessCycleTime(GetCurrentProcess(), out c) ? c : 0; }
    // Whole-process CPU seconds from the cycle counter (precise), -1 when the TSC rate is unknown.
    public static double OwnCpuCycS() { ulong c = ProcCyc(); return TscMhz > 0 && c > 0 ? c / (TscMhz * 1e6) : -1; }
    static void ReadTscMhz()
    {
        try
        {
            object v = Microsoft.Win32.Registry.GetValue(@"HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\CentralProcessor\0", "~MHz", null);
            if (v is int && (int)v > 0) TscMhz = (int)v;
        }
        catch (Exception ex) { NoteOnce("tsc", "~MHz not readable (cycle-based CPU numbers unavailable): " + ex.Message); }
    }
    // Cycle counts of every thread of this process (diagnostics; one snapshot after the first sample, one at the end).
    static Dictionary<int, ulong> ThreadCycles()
    {
        var d = new Dictionary<int, ulong>();
        try
        {
            using (var p = Process.GetCurrentProcess())
                foreach (ProcessThread t in p.Threads)
                {
                    IntPtr h = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, false, (uint)t.Id);
                    if (h == IntPtr.Zero) continue;
                    ulong c;
                    if (QueryThreadCycleTime(h, out c)) d[t.Id] = c;
                    CloseHandle(h);
                }
        }
        catch (Exception ex) { NoteOnce("threads", "thread cycle snapshot: " + ex.Message); }
        return d;
    }
    static string ByThread(Dictionary<int, ulong> a, Dictionary<int, ulong> b, ulong procDelta, double cycPerPct)
    {
        double sampler = 0, poller = 0, other = 0, sum = 0;
        int nOther = 0;
        foreach (KeyValuePair<int, ulong> kv in b)
        {
            ulong c0;
            double d = a.TryGetValue(kv.Key, out c0) ? (kv.Value >= c0 ? (double)(kv.Value - c0) : 0.0) : (double)kv.Value;
            sum += d;
            if (kv.Key == samplerTid) sampler += d;
            else if (kv.Key == pollerTid) poller += d;
            else if (d > 0) { other += d; nOther++; }
        }
        double gone = procDelta > sum ? procDelta - sum : 0.0;
        return string.Format(Inv, "sampler:{0:0.000},poller:{1:0.000},other:{2:0.000}({3}_threads),exited:{4:0.000}",
            sampler / cycPerPct, poller / cycPerPct, other / cycPerPct, nOther, gone / cycPerPct);
    }

    // ---- Init: game handle, power poller start, CPU sets, PDH query (+ one collect so the first row has rates) ----
    public static void Init(int pid, int intervalMs)
    {
        long i0 = Stopwatch.GetTimestamp(), it = i0;
        var ip = new StringBuilder();
        gamePid = pid;
        GameGone = false; GamePolled = false;
        createdFt = OwnStartUtc().ToFileTimeUtc();
        ReadTscMhz();
        hGame = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, false, pid);
        if (hGame == IntPtr.Zero)
        {
            int err = Marshal.GetLastWin32Error();
            if (err == ERROR_ACCESS_DENIED)
            {
                hGame = OpenProcess(SYNCHRONIZE, false, pid);
                if (hGame == IntPtr.Zero) { GamePolled = true; NoteOnce("open", "OpenProcess(" + pid + ") access denied: game existence polled once per tick"); }
            }
            else GameGone = true;                              // ERROR_INVALID_PARAMETER: no such process
        }
        else if (WaitForSingleObject(hGame, 0) == WAIT_OBJECT_0) GameGone = true;
        IPart(ip, "proc", ref it);
        if (GameGone) { InitParts = ip.ToString(); InitMs = (Stopwatch.GetTimestamp() - i0) * 1000.0 / Stopwatch.Frequency; return; }

        // power poller first: its first round (slow RPCs) overlaps the PDH setup below
        try
        {
            IntPtr mod = LoadLibraryW("powrprof.dll");
            IntPtr fp = mod == IntPtr.Zero ? IntPtr.Zero : GetProcAddress(mod, "PowerGetEffectiveOverlayScheme");
            if (fp != IntPtr.Zero) { overlayFn = (OverlayFn)Marshal.GetDelegateForFunctionPointer(fp, typeof(OverlayFn)); OverlayApi = true; }
        }
        catch (Exception ex) { NoteOnce("overlay-init", "overlay export: " + ex.Message); }
        try
        {
            pollPeriodMs = Math.Max(1000, intervalMs);
            pollStop = false; pollReady.Reset(); pollWake.Reset();
            pollThread = new Thread(PollLoop);
            pollThread.IsBackground = true;
            pollThread.Name = "LdSys-power";
            pollThread.Start();
        }
        catch (Exception ex) { pollReady.Set(); NoteOnce("poll-start", "power poller not started (scheme/overlay blank): " + ex.Message); }
        IPart(ip, "poll_start", ref it);

        ReadCpuSets();
        IPart(ip, "cpusets", ref it);

        var failed = new List<string>();
        CountersTotal = NC; CountersOk = 0;
        uint rc = PdhOpenQueryW(null, IntPtr.Zero, out query);
        IPart(ip, "pdh_open", ref it);
        if (rc != 0) { query = IntPtr.Zero; failed.Add("PdhOpenQuery:0x" + rc.ToString("X8", Inv)); }
        else
        {
            for (int i = 0; i < NC; i++)
            {
                IntPtr c;
                rc = PdhAddEnglishCounterW(query, CPaths[i], IntPtr.Zero, out c);
                if (rc == 0) { counters[i] = c; CountersOk++; }
                else { counters[i] = IntPtr.Zero; failed.Add(CNames[i] + ":0x" + rc.ToString("X8", Inv)); }
            }
            IPart(ip, "pdh_add", ref it);
            PdhCollectQueryData(query);
            IPart(ip, "pdh_collect", ref it);
        }
        preQpc = Stopwatch.GetTimestamp();

        // Raw (non-rate) counters already have data after one collect: list instances, flag empty sets.
        var zones = new List<string>();
        if (counters[C_TZ_TEMP] != IntPtr.Zero)
        {
            if (ReadArray(counters[C_TZ_TEMP]) > 0) zones.AddRange(names); else failed.Add("tz_temp:no_data");
        }
        if (counters[C_TZ_PASSIVE] != IntPtr.Zero)
        {
            if (ReadArray(counters[C_TZ_PASSIVE]) > 0) { foreach (string z in names) if (!zones.Contains(z)) zones.Add(z); }
            else failed.Add("tz_passive:no_data");
        }
        Zones = string.Join(";", zones.ToArray());
        if (counters[C_FREQ_ALL] != IntPtr.Zero)
        {
            int n = ReadArray(counters[C_FREQ_ALL]);
            if (n <= 0) failed.Add("freq:no_data");
            else
            {
                var seen = new List<string>();
                bool total = false;
                for (int i = 0; i < n; i++)
                {
                    if (names[i] == TOTAL) total = true;
                    int set = SetOf(names[i]);
                    if (set < 0) continue;
                    string s = (set == 1 ? "P:" : "E:") + vals[i].ToString("0", Inv);
                    if (!seen.Contains(s)) seen.Add(s);
                }
                LpFreq = string.Join(",", seen.ToArray());
                if (!total) failed.Add("freq:no__Total_instance");
            }
        }
        Failed = string.Join(" ", failed.ToArray());
        IPart(ip, "reads", ref it);

        textBuf = Marshal.AllocHGlobal(1024);
        try { OwnDesktop = ObjName(GetProcessWindowStation()) + "\\" + ObjName(GetThreadDesktop(GetCurrentThreadId())); } catch { OwnDesktop = "?"; }
        try { InputDesktopAtInit = InputDesktop(); } catch { InputDesktopAtInit = "?"; }
        IPart(ip, "desk", ref it);
        InitParts = ip.ToString();
        InitMs = (Stopwatch.GetTimestamp() - i0) * 1000.0 / Stopwatch.Frequency;
    }

    static void ReadCpuSets()
    {
        lpClass.Clear(); nameSet.Clear();
        uint len = 0;
        try
        {
            GetSystemCpuSetInformation(IntPtr.Zero, 0, out len, IntPtr.Zero, 0);
            if (len == 0) { ClassInfo = "unknown:GetSystemCpuSetInformation_err_" + Marshal.GetLastWin32Error(); return; }
            IntPtr buf = Marshal.AllocHGlobal((int)len);
            try
            {
                if (!GetSystemCpuSetInformation(buf, len, out len, IntPtr.Zero, 0)) { ClassInfo = "unknown:GetSystemCpuSetInformation_err_" + Marshal.GetLastWin32Error(); return; }
                int off = 0;
                while (off + 8 <= (int)len)
                {
                    int size = Marshal.ReadInt32(buf, off);
                    int type = Marshal.ReadInt32(buf, off + 4);
                    if (size < 8) break;
                    if (type == 0 && size >= 20)           // CpuSetInformation: Id@8 Group@12 LogicalProcessorIndex@14 EfficiencyClass@18
                    {
                        int group = (ushort)Marshal.ReadInt16(buf, off + 12);
                        int lp = Marshal.ReadByte(buf, off + 14);
                        int cls = Marshal.ReadByte(buf, off + 18);
                        lpClass[group * 1000 + lp] = cls;
                    }
                    off += size;
                }
            }
            finally { Marshal.FreeHGlobal(buf); }
        }
        catch (Exception ex) { ClassInfo = "unknown:" + Clean(ex.Message).Replace(' ', '_'); return; }
        if (lpClass.Count == 0) { ClassInfo = "unknown:no_cpu_sets"; return; }
        int minClass = int.MaxValue; maxClass = -1;
        foreach (int c in lpClass.Values) { if (c < minClass) minClass = c; if (c > maxClass) maxClass = c; }
        hybrid = minClass != maxClass;
        var keys = new List<int>(lpClass.Keys); keys.Sort();
        var p = new List<string>(); var e = new List<string>(); var ec = new List<string>();
        foreach (int key in keys)
        {
            int g = key / 1000, n = key % 1000;
            string s = g == 0 ? n.ToString(Inv) : g.ToString(Inv) + ":" + n.ToString(Inv);
            int c = lpClass[key];
            if (!hybrid || c == maxClass) p.Add(s);
            else { e.Add(s); string cs = c.ToString(Inv); if (!ec.Contains(cs)) ec.Add(cs); }
        }
        PList = string.Join(",", p.ToArray()); EList = string.Join(",", e.ToArray());
        ClassInfo = hybrid ? "P=" + maxClass.ToString(Inv) + ",E=" + string.Join("/", ec.ToArray()) : "all=" + maxClass.ToString(Inv);
    }

    // PDH "Processor Information" instance "group,number" -> 1 (P set), 0 (E set), -1 (_Total / unknown).
    static int SetOf(string inst)
    {
        int r;
        if (nameSet.TryGetValue(inst, out r)) return r;
        r = -1;
        int comma = inst.IndexOf(',');
        int g, n;
        if (comma > 0 && inst.IndexOf("_Total", StringComparison.OrdinalIgnoreCase) < 0 &&
            int.TryParse(inst.Substring(0, comma), NumberStyles.Integer, Inv, out g) &&
            int.TryParse(inst.Substring(comma + 1), NumberStyles.Integer, Inv, out n))
        {
            int cls;
            if (lpClass.Count == 0 || !hybrid) r = 1;          // no / equal classes: everything is "P", e_* stay blank
            else if (lpClass.TryGetValue(g * 1000 + n, out cls)) r = cls == maxClass ? 1 : 0;
            else NoteOnce("lp:" + inst, "no CPU set for processor instance " + inst + " (left out of p_*/e_*)");
        }
        nameSet[inst] = r;
        return r;
    }

    // Wildcard counter -> names/vals (valid items only). Returns the count, -1 on failure.
    static int ReadArray(IntPtr counter)
    {
        names.Clear(); vals.Clear();
        if (counter == IntPtr.Zero) return -1;
        for (int attempt = 0; attempt < 4; attempt++)
        {
            uint size = arrBufSize, count;
            uint rc = PdhGetFormattedCounterArrayW(counter, PDH_FMT, ref size, out count, arrBuf);
            if (rc == PDH_MORE_DATA)
            {
                if (arrBuf != IntPtr.Zero) Marshal.FreeHGlobal(arrBuf);
                arrBufSize = Math.Max(size, arrBufSize) + 2048;
                arrBuf = Marshal.AllocHGlobal((int)arrBufSize);
                continue;
            }
            if (rc != 0) return -1;
            for (int i = 0; i < (int)count; i++)
            {
                int o = i * 24;                                // PDH_FMT_COUNTERVALUE_ITEM_W: szName@0, CStatus@8, double@16
                uint cs = (uint)Marshal.ReadInt32(arrBuf, o + 8);
                if (cs != 0 && cs != 1) continue;
                IntPtr pn = Marshal.ReadIntPtr(arrBuf, o);
                names.Add(pn == IntPtr.Zero ? "" : Marshal.PtrToStringUni(pn));
                vals.Add(BitConverter.Int64BitsToDouble(Marshal.ReadInt64(arrBuf, o + 16)));
            }
            return vals.Count;
        }
        return -1;
    }

    static bool IsAlive()
    {
        if (hGame != IntPtr.Zero) return WaitForSingleObject(hGame, 0) == WAIT_TIMEOUT;
        try { Process.GetProcessById(gamePid).Dispose(); return true; }
        catch (ArgumentException) { return false; }
        catch { return true; }
    }

    static string ObjName(IntPtr h)
    {
        uint need;
        if (h == IntPtr.Zero || !GetUserObjectInformationW(h, UOI_NAME, textBuf, 1022, out need)) return "";
        Marshal.WriteInt16(textBuf, 1022, 0);
        return Clean(Marshal.PtrToStringUni(textBuf));
    }

    static string InputDesktop()
    {
        IntPtr h = OpenInputDesktop(0, false, DESKTOP_READOBJECTS);
        if (h == IntPtr.Zero) return "denied";                 // usually the secure desktop (lock screen / UAC)
        try { return ObjName(h); }
        finally { CloseDesktop(h); }
    }

    static string SchemeName()
    {
        IntPtr p;
        if (PowerGetActiveScheme(IntPtr.Zero, out p) != 0 || p == IntPtr.Zero) return "";
        Guid g;
        try { g = (Guid)Marshal.PtrToStructure(p, typeof(Guid)); } finally { LocalFree(p); }
        if (lastSchemeName == null || g != lastScheme)
        {
            lastScheme = g;
            string n = null;
            uint size = 0;
            uint rc = PowerReadFriendlyName(IntPtr.Zero, ref g, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, ref size);
            if ((rc == 0 || rc == ERROR_MORE_DATA) && size > 0 && size < 65536)
            {
                IntPtr b = Marshal.AllocHGlobal((int)size + 2);
                try
                {
                    Marshal.WriteInt16(b, (int)size, 0);
                    if (PowerReadFriendlyName(IntPtr.Zero, ref g, IntPtr.Zero, IntPtr.Zero, b, ref size) == 0) n = Clean(Marshal.PtrToStringUni(b));
                }
                finally { Marshal.FreeHGlobal(b); }
            }
            lastSchemeName = string.IsNullOrEmpty(n) ? g.ToString() : n;
        }
        return lastSchemeName;
    }

    static string OverlayName()
    {
        if (overlayFn == null) return "";
        Guid g;
        if (overlayFn(out g) != 0) return "";
        string s = g.ToString();
        switch (s)
        {
            case "961cc777-2547-4f9d-8174-7d86181b8a7a": return "best_efficiency";
            case "00000000-0000-0000-0000-000000000000": return "balanced";
            case "3af9b8d9-7c97-431d-ad78-34a8bfea439f": return "better_performance";
            case "ded574b5-45a0-4f42-8737-46345c09c238": return "best_performance";
        }
        return s;
    }

    static void Num(double v, string fmt) { if (!double.IsNaN(v) && !double.IsInfinity(v)) sb.Append(v.ToString(fmt, Inv)); }

    // One row. aliveOverride: -1 = query the game handle, 0/1 = forced (0 for the final row after the game exited).
    static void Sample(TextWriter w, int aliveOverride)
    {
        long s0 = Stopwatch.GetTimestamp();
        markCyc = ThreadCyc();
        ulong c0 = markCyc;
        if (query != IntPtr.Zero)
        {
            uint prc = PdhCollectQueryData(query);
            if (prc != 0) NoteOnce("collect:" + prc.ToString("X8", Inv), "PdhCollectQueryData returned 0x" + prc.ToString("X8", Inv));
        }
        long q = Mark(P_COLLECT, s0), t = q;
        DateTime utc = DateTime.UtcNow;
        sb.Length = 0;
        sb.Append(((q - originQpc) / (double)Stopwatch.Frequency).ToString("0.000", Inv)).Append(',');
        long ms = (utc.Ticks - UnixEpochTicks) / 10000;       // == DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() (Get-Epoch)
        sb.Append((ms / 1000).ToString(Inv)).Append('.').Append((ms % 1000).ToString("000", Inv)).Append(',');
        sb.Append(utc.ToLocalTime().ToString("HH:mm:ss.fff", Inv)).Append(',');

        try   // idle_s: last input first, then the tick count (never negative), uint32 wrap-safe
        {
            LASTINPUTINFO li; li.cbSize = 8; li.dwTime = 0;
            if (GetLastInputInfo(ref li)) { uint idle = unchecked(GetTickCount() - li.dwTime); sb.Append((idle / 1000.0).ToString("0.000", Inv)); }
            else NoteOnce("idle", "GetLastInputInfo failed");
        }
        catch (Exception ex) { NoteOnce("idle-x", "idle_s: " + ex.Message); }
        sb.Append(',');

        uint fpid = 0;
        try { IntPtr hw = GetForegroundWindow(); if (hw != IntPtr.Zero) GetWindowThreadProcessId(hw, out fpid); }
        catch (Exception ex) { NoteOnce("fg", "fg_pid: " + ex.Message); }
        sb.Append(fpid.ToString(Inv)).Append(',').Append(fpid != 0 && fpid == (uint)gamePid ? '1' : '0').Append(',');
        int alive = aliveOverride >= 0 ? aliveOverride : (IsAlive() ? 1 : 0);
        sb.Append(alive == 1 ? '1' : '0').Append(',');
        t = Mark(P_USER, t);

        try { sb.Append(InputDesktop()); } catch (Exception ex) { NoteOnce("desk", "input_desktop: " + ex.Message); }
        sb.Append(',');
        t = Mark(P_DESK, t);
        try
        {
            int run = 0;
            if (SystemParametersInfoW(SPI_GETSCREENSAVERRUNNING, 0, ref run, 0)) sb.Append(run != 0 ? '1' : '0');
            else NoteOnce("ss", "SPI_GETSCREENSAVERRUNNING failed");
        }
        catch (Exception ex) { NoteOnce("ss-x", "screensaver: " + ex.Message); }
        sb.Append(',');
        t = Mark(P_USER, t);

        // CPU: the "_Total" instances, then the P/E means over the per-logical-processor instances.
        double util = double.NaN, perf = double.NaN, bas = double.NaN;
        double pEff = 0, eEff = 0, pUtil = 0, eUtil = 0; int npEff = 0, neEff = 0, npUtil = 0, neUtil = 0;
        double tzPassive = double.NaN, tzTemp = double.NaN;
        double pkgW = double.NaN, pp0W = double.NaN, pp1W = double.NaN, dramW = double.NaN;
        try
        {
            freqBy.Clear();
            int n = ReadArray(counters[C_FREQ_ALL]);
            for (int i = 0; i < n; i++) { if (names[i] == TOTAL) bas = vals[i]; else freqBy[names[i]] = vals[i]; }
            n = ReadArray(counters[C_PERF_ALL]);
            for (int i = 0; i < n; i++)
            {
                if (names[i] == TOTAL) { perf = vals[i]; continue; }
                int set = SetOf(names[i]);
                if (set < 0) continue;
                double f;
                if (!freqBy.TryGetValue(names[i], out f) || f <= 0) f = bas;
                if (double.IsNaN(f)) continue;
                double eff = vals[i] * f / 100.0;
                if (set == 1) { pEff += eff; npEff++; } else { eEff += eff; neEff++; }
            }
            n = ReadArray(counters[C_UTIL_ALL]);
            for (int i = 0; i < n; i++)
            {
                if (names[i] == TOTAL) { util = vals[i]; continue; }
                int set = SetOf(names[i]);
                if (set == 1) { pUtil += vals[i]; npUtil++; } else if (set == 0) { eUtil += vals[i]; neUtil++; }
            }
            n = ReadArray(counters[C_TZ_PASSIVE]);
            for (int i = 0; i < n; i++) if (double.IsNaN(tzPassive) || vals[i] < tzPassive) tzPassive = vals[i];
            n = ReadArray(counters[C_TZ_TEMP]);
            for (int i = 0; i < n; i++) if (vals[i] > 0 && (double.IsNaN(tzTemp) || vals[i] > tzTemp)) tzTemp = vals[i];
            // RAPL power (mW, mean over the last interval) by channel suffix, summed over packages; _Total / others ignored
            n = ReadArray(counters[C_POWER]);
            for (int i = 0; i < n; i++)
            {
                string nm = names[i]; double wv = vals[i] / 1000.0;
                if (nm.EndsWith("_PKG", StringComparison.OrdinalIgnoreCase)) pkgW = (double.IsNaN(pkgW) ? 0 : pkgW) + wv;
                else if (nm.EndsWith("_PP0", StringComparison.OrdinalIgnoreCase)) pp0W = (double.IsNaN(pp0W) ? 0 : pp0W) + wv;
                else if (nm.EndsWith("_PP1", StringComparison.OrdinalIgnoreCase)) pp1W = (double.IsNaN(pp1W) ? 0 : pp1W) + wv;
                else if (nm.EndsWith("_DRAM", StringComparison.OrdinalIgnoreCase)) dramW = (double.IsNaN(dramW) ? 0 : dramW) + wv;
            }
        }
        catch (Exception ex) { NoteOnce("pdh-x", "PDH read: " + ex.Message); }
        Num(util, "0.00"); sb.Append(',');
        Num(perf, "0.00"); sb.Append(',');
        Num(bas, "0"); sb.Append(',');
        Num(perf * bas / 100.0, "0"); sb.Append(',');
        Num(npEff > 0 ? pEff / npEff : double.NaN, "0"); sb.Append(',');
        Num(neEff > 0 ? eEff / neEff : double.NaN, "0"); sb.Append(',');
        Num(npUtil > 0 ? pUtil / npUtil : double.NaN, "0.00"); sb.Append(',');
        Num(neUtil > 0 ? eUtil / neUtil : double.NaN, "0.00"); sb.Append(',');
        Num(tzPassive, "0.##"); sb.Append(',');
        Num(double.IsNaN(tzTemp) ? double.NaN : Math.Round(tzTemp - 273.15, 1), "0.0"); sb.Append(',');
        t = Mark(P_PDH, t);

        try
        {
            SYSTEM_POWER_STATUS ps;
            if (GetSystemPowerStatus(out ps))
            {
                if (ps.ACLineStatus != 255) sb.Append(ps.ACLineStatus == 1 ? '1' : '0');
                sb.Append(',').Append(ps.SystemStatusFlag == 1 ? '1' : '0').Append(',');
                if (ps.BatteryLifePercent != 255) sb.Append(((int)ps.BatteryLifePercent).ToString(Inv));
                sb.Append(',');
            }
            else { sb.Append(",,,"); NoteOnce("pwr", "GetSystemPowerStatus failed"); }
        }
        catch (Exception ex) { sb.Append(",,,"); NoteOnce("pwr-x", "power status: " + ex.Message); }
        t = Mark(P_PWR, t);
        // scheme / overlay: latest values of the power poller thread (blank when its last completed round is stale)
        string schemeV = pollScheme, overlayV = pollOverlay;
        long pd = Interlocked.Read(ref pollDoneQpc);
        if (pd == 0 || Stopwatch.GetTimestamp() - pd > staleTicks)
        {
            if (pd != 0) NoteOnce("poll-stale", "power query (scheme/overlay) older than " + (staleTicks / Stopwatch.Frequency).ToString(Inv) + " s: blank cells until it answers again");
            schemeV = null; overlayV = null;
        }
        sb.Append(schemeV ?? "").Append(',').Append(overlayV ?? "");
        sb.Append(','); Num(pkgW, "0.000");
        sb.Append(','); Num(pp0W, "0.000");
        sb.Append(','); Num(pp1W, "0.000");
        sb.Append(','); Num(dramW, "0.000");

        sb.Append("\r\n");
        w.Write(sb.ToString());
        w.Flush();
        long s1 = Mark(P_WRITE, t);
        long d = s1 - s0, dc = (long)(markCyc - c0);
        if (Rows == 0)
        {
            firstSampleTicks = d; firstSampleCyc = dc;
            FirstRowS = (DateTime.UtcNow.ToFileTimeUtc() - createdFt) / 1e7;
            FirstRowT = (q - originQpc) / (double)Stopwatch.Frequency;
            thrAfterFirst = ThreadCycles();                       // per-thread split of the steady CPU (diagnostics)
            cpuAfterFirst = OwnCpuS(); pcAfterFirst = ProcCyc(); qAfterFirst = Stopwatch.GetTimestamp();
        }
        else
        {
            sampleTicks += d; if (d > sampleMaxTicks) sampleMaxTicks = d;
            sampleCyc += dc; if (dc > sampleCycMax) sampleCycMax = dc;
        }
        Rows++;
    }

    // ---- stop file watch. A File.Exists costs ~0.35 ms CPU on the test machine (file system filter stack): checking it at
    // every 250 ms wake was ~40 % of the driver's own CPU. A change notification of the stop file's folder
    // (FILE_NOTIFY_CHANGE_FILE_NAME: a file created / renamed / deleted there) wakes the loop instead; the stop file is then
    // checked, plus once per tick as a safety net. Changes between a signal and the re-arm are kept by the OS. ----
    static IntPtr hNote = IntPtr.Zero;
    static IntPtr[] waitBoth;                                 // { game, notification } when both exist

    static void WatchStopDir(string stopFile)
    {
        hNote = IntPtr.Zero; waitBoth = null;
        try
        {
            string dir = Path.GetDirectoryName(Path.GetFullPath(stopFile));
            IntPtr h = string.IsNullOrEmpty(dir) ? INVALID_HANDLE_VALUE : FindFirstChangeNotificationW(dir, false, FILE_NOTIFY_CHANGE_FILE_NAME);
            if (h != IntPtr.Zero && h != INVALID_HANDLE_VALUE) hNote = h;
            else NoteOnce("watch", "stop file watch unavailable (FindFirstChangeNotification error " + Marshal.GetLastWin32Error() + "): stop file checked at every wake (<= 250 ms)");
        }
        catch (Exception ex) { NoteOnce("watch-x", "stop file watch: " + ex.Message + " (stop file checked at every wake, <= 250 ms)"); }
        if (hNote != IntPtr.Zero && hGame != IntPtr.Zero) waitBoth = new IntPtr[] { hGame, hNote };
        StopWatch = hNote != IntPtr.Zero ? "notify" : "poll";
    }

    static void DropWatch(string why)
    {
        if (hNote != IntPtr.Zero)
        {
            NoteOnce("watch-lost", "stop file watch lost (" + why + "): stop file checked at every wake (<= 250 ms)");
            try { FindCloseChangeNotification(hNote); } catch { }
            hNote = IntPtr.Zero; StopWatch = "poll(lost)";
        }
        waitBoth = null;
    }

    // Wait up to ms for the game handle / the stop folder notification: 1 = game exited, 2 = stop folder changed, 0 = timeout.
    static int WaitTick(uint ms)
    {
        Wakes++;
        uint r;
        if (waitBoth != null) r = WaitForMultipleObjects(2, waitBoth, false, ms);
        else if (hGame != IntPtr.Zero) r = WaitForSingleObject(hGame, ms);
        else if (hNote != IntPtr.Zero) { r = WaitForSingleObject(hNote, ms); if (r == WAIT_OBJECT_0) r = WAIT_OBJECT_0 + 1; }
        else { Thread.Sleep((int)ms); return 0; }
        if (r == WAIT_TIMEOUT) return 0;
        if (r == WAIT_OBJECT_0 && hGame != IntPtr.Zero) return 1;
        if (r == WAIT_OBJECT_0 + 1 && hNote != IntPtr.Zero)
        {
            if (!FindNextChangeNotification(hNote)) DropWatch("FindNextChangeNotification error " + Marshal.GetLastWin32Error());
            return 2;
        }
        // WAIT_FAILED / unexpected (not seen in tests): never spin - drop the handles, poll the game by pid and the stop file
        int err = Marshal.GetLastWin32Error();
        DropWatch("wait result 0x" + r.ToString("X", Inv) + " error " + err);
        if (hGame != IntPtr.Zero)
        {
            NoteOnce("wait-failed", "wait on the game handle failed (0x" + r.ToString("X", Inv) + ", error " + err + "): game existence polled once per tick");
            try { CloseHandle(hGame); } catch { }
            hGame = IntPtr.Zero; GamePolled = true;
        }
        Thread.Sleep((int)ms);
        return 0;
    }

    // ---- Run: header, then the loop until game exit / stop file / MaxSec. Blocking. ----
    public static void Run(string outPath, string stopFile, int intervalMs, double maxSec, long originQpcArg)
    {
        originQpc = originQpcArg;
        samplerTid = (int)GetCurrentThreadId(); thrAfterFirst = null; SteadyByThread = "";
        Reason = ""; Rows = 0; Skipped = 0; sampleTicks = 0; sampleMaxTicks = 0; firstSampleTicks = 0; LoopS = 0; LoopCpuS = 0;
        sampleCyc = 0; sampleCycMax = 0; firstSampleCyc = 0; pcAfterFirst = 0; Wakes = 0; StopChecks = 0; StopWatch = "";
        Array.Clear(partTicks, 0, NP); Array.Clear(partMax, 0, NP); Array.Clear(partFirst, 0, NP);
        Array.Clear(partCyc, 0, NP); Array.Clear(partCycFirst, 0, NP);
        long freq = Stopwatch.Frequency;
        try
        {
            using (var fs = new FileStream(outPath, FileMode.Create, FileAccess.Write, FileShare.ReadWrite | FileShare.Delete, 4096))
            using (var w = new StreamWriter(fs, new UTF8Encoding(false), 4096))
            {
                w.Write(Header); w.Write("\r\n"); w.Flush();
                if (GameGone) { Reason = "game_exit"; return; }
                long iv = Math.Max(1L, intervalMs * freq / 1000);
                staleTicks = Math.Max(5 * freq, 3 * iv);
                WatchStopDir(stopFile);                         // armed before the first check: no stop file is missed
                // Row 1 should already have scheme/overlay: wait (<= 2 s; stop file / game exit still noticed) for the first
                // round of the power poller started in Init.
                long pwEnd = Stopwatch.GetTimestamp() + 2 * freq;
                while (!pollReady.WaitOne(100))
                    if (Stopwatch.GetTimestamp() >= pwEnd || File.Exists(stopFile) || !IsAlive()) break;
                // >= min(interval, 0.25 s) after the PDH pre-collect, so the first row's rates span a real interval.
                long t0 = Math.Max(Stopwatch.GetTimestamp(), preQpc + Math.Min(iv, freq / 4));
                long deadline = t0 + (long)(maxSec * freq);
                double cpu0 = OwnCpuS();
                ulong pc0 = ProcCyc();
                long l0 = Stopwatch.GetTimestamp();
                long k = 0;
                bool gone = false, checkStop = true;
                while (true)
                {
                    if (gone) { Reason = "game_exit"; Sample(w, 0); break; }   // one last off-grid row, game_alive=0
                    if (checkStop)
                    {
                        checkStop = hNote == IntPtr.Zero;               // no notification: check at every wake
                        StopChecks++;
                        if (File.Exists(stopFile)) { Reason = "stop_file"; break; }
                    }
                    long now = Stopwatch.GetTimestamp();
                    if (now >= deadline) { Reason = "max_sec"; break; }
                    long due = t0 + k * iv;
                    if (now >= due)
                    {
                        if (now - due > iv)                     // late by more than one interval: skip to the next future tick
                        {
                            long j = (now - t0) / iv + 1;
                            Skipped += j - k;
                            k = j;
                            continue;
                        }
                        if (GamePolled && !IsAlive()) { gone = true; continue; }
                        Sample(w, -1);
                        k++;
                        checkStop = true;                       // safety net: the stop file is also checked once per tick
                        continue;
                    }
                    long waitMs = ((Math.Min(due, deadline) - now) * 1000 + freq - 1) / freq;
                    long cap = hNote != IntPtr.Zero ? 1000 : 250;
                    if (waitMs > cap) waitMs = cap; else if (waitMs < 1) waitMs = 1;
                    int sig = WaitTick((uint)waitMs);
                    if (sig == 1) gone = true;
                    else if (sig == 2) checkStop = true;
                }
                long l1 = Stopwatch.GetTimestamp();
                double cpu1 = OwnCpuS();
                ulong pc1 = ProcCyc();
                LoopS = (l1 - l0) / (double)freq;
                LoopCpuS = cpu1 - cpu0;
                double cycHz = TscMhz * 1e6;
                LoopCycCpuPct = cycHz > 0 && LoopS > 0 && pc0 > 0 ? (pc1 - pc0) / cycHz / LoopS * 100 : -1;
                double tms = 1000.0 / freq;
                FirstSampleMs = Rows > 0 ? firstSampleTicks * tms : 0;
                SampleMsMean = Rows > 1 ? sampleTicks * tms / (Rows - 1) : FirstSampleMs;
                SampleMsMax = Rows > 1 ? sampleMaxTicks * tms : FirstSampleMs;
                double steadyWall = Rows > 1 ? (l1 - qAfterFirst) / (double)freq : 0;
                SteadyTickCpuPct = steadyWall > 0 ? (cpu1 - cpuAfterFirst) / steadyWall * 100 : -1;
                SteadyCpuPct = cycHz > 0 && steadyWall > 0 && pcAfterFirst > 0 ? (pc1 - pcAfterFirst) / cycHz / steadyWall * 100 : SteadyTickCpuPct;
                if (thrAfterFirst != null && cycHz > 0 && steadyWall > 0 && pcAfterFirst > 0)
                    SteadyByThread = ByThread(thrAfterFirst, ThreadCycles(), pc1 - pcAfterFirst, cycHz * steadyWall / 100);
            }
        }
        finally { Cleanup(); }
    }

    static void Cleanup()
    {
        pollStop = true;                                       // background thread: not joined (may sit in an RPC call)
        try { pollWake.Set(); } catch { }
        try { if (query != IntPtr.Zero) PdhCloseQuery(query); } catch { }
        query = IntPtr.Zero;
        for (int i = 0; i < NC; i++) counters[i] = IntPtr.Zero;
        try { if (hNote != IntPtr.Zero) FindCloseChangeNotification(hNote); } catch { }
        hNote = IntPtr.Zero; waitBoth = null;
        try { if (hGame != IntPtr.Zero) CloseHandle(hGame); } catch { }
        hGame = IntPtr.Zero;
        if (arrBuf != IntPtr.Zero) { Marshal.FreeHGlobal(arrBuf); arrBuf = IntPtr.Zero; arrBufSize = 0; }
        if (textBuf != IntPtr.Zero) { Marshal.FreeHGlobal(textBuf); textBuf = IntPtr.Zero; }
    }
}
