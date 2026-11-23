// Stand-in for legodimensions.exe, used only by bench\agent8\run\run_selftest.ps1 to test
// run-timing.ps1 and run-matrix.ps1 end to end. Not game code, holds no game data. It:
//   - takes --log_file=PATH (log lines, auto-flushed) and --perf_log_csv=PATH;
//   - writes perf.csv like rexglue's counter.cpp: the same 17-name header, one integer row per
//     frame, flushed every 60 rows through a 4096-byte buffer (so the file can end mid-row), and
//     opened with FileShare.None (the real game's file cannot be read while it runs);
//   - frame i (0-based data row) has frame_time_us = Ft(i), written in real time on a Stopwatch
//     schedule so wall time tracks the summed frame times;
//   - with LEGO_NATIVE_FRAME_METRICS=<file> (like a native ON build): perf.csv keeps only its header and
//     the frames go to <file> the way device.cpp's std::ofstream writes them: header "frame,interval_ms,..."
//     at start, one row per present (interval_ms = Ft(i) / 1000 with 3 decimals), default buffering
//     (1 KB: irregular flushes, partial rows on disk), readable while open, flushed at normal exit.
//     In that mode it also logs the sizes of cache\native-pso.bin and cache\native-pso-recipes.bin
//     (working dir) at start and writes both files at exit unless LEGO_NATIVE_PSO_CACHE=0 (a stand-in
//     for the native PSO cache, so the matrix seed_cache chain can be tested);
//   - with LEGO_SAMPLE_PROFILE set and LEGO_SAMPLE_PROFILE_TRIGGER=<file>: records while the file
//     exists and writes profile-<GetTickCount64>.bin (LSP1, one module, dummy samples) next to the
//     exe when the file is deleted, like the original sample_profiler.cpp;
//   - shows a visible top-level window and exits with code 0 on WM_CLOSE.
// Build (C# 5): csc /nologo /target:winexe /out:<dir>\legodimensions.exe fakegame_timing.cs
using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

class FakeTimingGame : Form
{
    [DllImport("kernel32.dll")] static extern ulong GetTickCount64();

    const string Header = "frame_time_us,fps,draw_calls,command_buffer_stalls,vertices_processed,xma_frames_decoded,"
        + "audio_frame_latency_us,buffer_queue_depth,functions_dispatched,interrupt_dispatches,active_threads,"
        + "apc_queue_depth,critical_region_contentions,texture_cache_hits,texture_cache_misses,pipeline_cache_hits,"
        + "pipeline_cache_misses";
    const string NativeHeader = "frame,interval_ms,cpu_ms,native_vsync";
    static readonly string[] CacheNames = { "native-pso.bin", "native-pso-recipes.bin" };

    // The known pattern; run_selftest.ps1 has the same function.
    public static int Ft(long i)
    {
        if (i % 50 == 49) return 120000;
        if (i % 50 == 24) return 40000;
        if (i % 5 == 2) return 20000;
        return 16000;
    }

    readonly StreamWriter log;
    readonly string csvPath, nativePath;
    volatile bool stop;
    Thread writer, sampler;

    FakeTimingGame(string logPath, string csvPath)
    {
        this.csvPath = csvPath;
        nativePath = Environment.GetEnvironmentVariable("LEGO_NATIVE_FRAME_METRICS");
        Text = "Fake Dimensions (timing self-test)";
        Width = 480;
        Height = 270;
        if (!string.IsNullOrEmpty(logPath)) log = new StreamWriter(logPath, false) { AutoFlush = true };
        Log("info", "fake timing game start; args=" + string.Join(" ", Environment.GetCommandLineArgs()));
        if (!string.IsNullOrEmpty(nativePath)) LogCache();
        writer = new Thread(WriteFrames) { IsBackground = true };
        writer.Start();
        if (Environment.GetEnvironmentVariable("LEGO_SAMPLE_PROFILE") != null)
        {
            sampler = new Thread(Sampler) { IsBackground = true };
            sampler.Start();
            Log("info", "fake sampler on, trigger=" + Environment.GetEnvironmentVariable("LEGO_SAMPLE_PROFILE_TRIGGER"));
        }
        FormClosing += (s, e) =>
        {
            Log("info", "window close requested; shutting down");
            stop = true;
            if (writer != null) writer.Join(5000);
            Log("info", "perf.csv closed");
            if (!string.IsNullOrEmpty(nativePath)) SaveCache();
        };
    }

    void Log(string level, string msg)
    {
        if (log == null) return;
        lock (log) log.WriteLine("[{0}] [{1}] [fake] {2}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff", CultureInfo.InvariantCulture), level, msg);
    }

    static string CacheDir() { return Path.Combine(Environment.CurrentDirectory, "cache"); }

    void LogCache()
    {
        var sb = new StringBuilder("fake pso cache at start:");
        foreach (var n in CacheNames)
        {
            var f = new FileInfo(Path.Combine(CacheDir(), n));
            sb.Append(' ').Append(n).Append('=').Append(f.Exists ? f.Length.ToString(CultureInfo.InvariantCulture) + " B" : "missing");
        }
        Log("info", sb.ToString());
    }

    void SaveCache()
    {
        if (Environment.GetEnvironmentVariable("LEGO_NATIVE_PSO_CACHE") == "0") { Log("info", "fake pso cache off (LEGO_NATIVE_PSO_CACHE=0): not saved"); return; }
        try
        {
            string d = CacheDir();
            Directory.CreateDirectory(d);
            string stamp = DateTime.Now.Ticks.ToString(CultureInfo.InvariantCulture) + " pid " + Process.GetCurrentProcess().Id.ToString(CultureInfo.InvariantCulture);
            File.WriteAllText(Path.Combine(d, CacheNames[0]), "FAKE PSO BLOB " + stamp + "\n");
            File.WriteAllText(Path.Combine(d, CacheNames[1]), "FAKE PSO RECIPES " + stamp + "\n");
            Log("info", "pipeline cache saved (fake) in " + d);
        }
        catch (Exception ex) { Log("error", "fake pso cache not saved: " + ex.Message); }
    }

    void WriteFrames()
    {
        if (string.IsNullOrEmpty(csvPath)) return;
        var fs = new FileStream(csvPath, FileMode.Create, FileAccess.Write, FileShare.None, 4096);
        var w = new StreamWriter(fs, new UTF8Encoding(false), 1024);
        w.NewLine = "\r\n";   // the game's CRT text mode writes CRLF
        w.WriteLine(Header);
        StreamWriter nw = null;
        if (!string.IsNullOrEmpty(nativePath))
        {
            // device.cpp: std::ofstream (shared read), header at static init, default buffering
            nw = new StreamWriter(new FileStream(nativePath, FileMode.Create, FileAccess.Write, FileShare.Read, 1024), new UTF8Encoding(false), 128);
            nw.NewLine = "\r\n";
            nw.WriteLine(NativeHeader);
        }
        var clock = Stopwatch.StartNew();
        double dueUs = 0;
        long i = 0;
        var sb = new StringBuilder();
        while (!stop)
        {
            int ft = Ft(i);
            dueUs += ft;
            while (!stop && clock.Elapsed.TotalMilliseconds * 1000.0 < dueUs) Thread.Sleep(1);
            if (stop) break;
            sb.Length = 0;
            if (nw != null)
            {
                // native ON build: no perf.csv rows; the first present writes no row, so row 1 is frame 1
                sb.Append(i + 1).Append(',').Append((ft / 1000.0).ToString("F3", CultureInfo.InvariantCulture)).Append(",4.250,0");
                nw.WriteLine(sb.ToString());
                i++;
                continue;
            }
            sb.Append(ft).Append(',').Append(1000000 / ft).Append(',').Append(100 + i % 7);
            for (int k = 3; k < 17; k++) sb.Append(k == 10 ? ",42" : ",0");
            w.WriteLine(sb.ToString());
            i++;
            if (i % 60 == 0) w.Flush();
        }
        w.Flush();
        w.Close();
        if (nw != null) { nw.Flush(); nw.Close(); }
    }

    void Sampler()
    {
        string trigger = Environment.GetEnvironmentVariable("LEGO_SAMPLE_PROFILE_TRIGGER");
        bool recording = false, was = false;
        long rounds = 0;
        while (!stop)
        {
            bool down = trigger != null && File.Exists(trigger);
            if (recording && !down && was)
            {
                WriteProfile(rounds);
                recording = false;
                Log("info", "fake profile written");
            }
            if (down && !was && !recording) { recording = true; rounds = 0; Log("info", "fake profile recording"); }
            was = down;
            if (recording) rounds += 50;
            Thread.Sleep(50);
        }
    }

    void WriteProfile(long rounds)
    {
        string dir = Path.GetDirectoryName(Application.ExecutablePath);
        string path = Path.Combine(dir, "profile-" + GetTickCount64().ToString(CultureInfo.InvariantCulture) + ".bin");
        using (var f = new BinaryWriter(File.Create(path)))
        {
            f.Write(Encoding.ASCII.GetBytes("LSP1"));
            f.Write((uint)1);
            byte[] name = Encoding.ASCII.GetBytes("legodimensions.exe");
            f.Write((ulong)0x140000000UL);
            f.Write((uint)0x100000);
            f.Write((uint)name.Length);
            f.Write(name);
            f.Write((ulong)rounds);
            for (long k = 0; k < rounds; k++)
            {
                f.Write((uint)1234);
                f.Write((uint)1);
                f.Write((ulong)(0x140001000UL + (ulong)(k % 16)));
            }
        }
    }

    [STAThread]
    static int Main(string[] args)
    {
        string logPath = null, csv = null;
        foreach (var a in args)
        {
            if (a.StartsWith("--log_file=")) logPath = a.Substring(11);
            else if (a.StartsWith("--perf_log_csv=")) csv = a.Substring(15);
        }
        Application.Run(new FakeTimingGame(logPath, csv));
        return 0;
    }
}
