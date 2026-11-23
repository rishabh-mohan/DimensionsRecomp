// Stand-in for legodimensions.exe, used only to test harness/run-game.ps1 end to end.
// It is not game code and holds no game data. It:
//   - takes --log_file=PATH and writes log lines in the game's format, with the boot markers
//     runstats.py looks for (OFF-build "DXGI adapter" and native-build "Native GPU" lines);
//   - takes --perf_log_csv=PATH and writes the game's 17-column perf.csv (flushed every 60 rows);
//   - writes frames.csv at about 60 Hz when LEGO_NATIVE_FRAME_METRICS is set;
//   - with LEGO_SAMPLE_PROFILE + LEGO_SAMPLE_PROFILE_TRIGGER, "records" while the trigger file
//     exists and writes a synthetic LSP1 profile-<tick>.bin (with an LSPX trailer) next to the exe
//     when it is deleted, like rexlego/src/sample_profiler.cpp (selftest.ps1 writes a matching map);
//   - with --input_backend=xinput, polls slot 0 of xinput1_4.dll every frame like the game's XInput driver
//     (XInputGetState + XInputGetKeystroke), logs a "fake xinput: ..." line for each change and keystroke and
//     moves to the next fake scene on each A press (perf.csv draws 900 + 10 * scene, vertices 120000 + scene),
//     to test the harness's virtual pad (harness/vpad, run-game.ps1 -InputScript);
//   - exits on WM_CLOSE, like the game's window close button.
// Self-test switches:
//   --fake_crash_after=S   throw an unhandled exception after S seconds (a crash)
//   --fake_ignore_close    ignore WM_CLOSE, so the harness has to kill it
// Build: csc /nologo /target:winexe /out:build\agent3\selftest-bin\fakedimensions.exe harness\selftest\fakegame.cs
using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

class FakeGame : Form
{
    readonly StreamWriter log, csv, perf;
    readonly Stopwatch clock = Stopwatch.StartNew();
    readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer();
    readonly double crashAfter;
    readonly bool ignoreClose;
    double last;
    int frame, perfRows;

    // XInput (only with --input_backend=xinput). Same layouts as xinput.h.
    [StructLayout(LayoutKind.Sequential)]
    struct XState { public uint Packet; public ushort Buttons; public byte Lt, Rt; public short Lx, Ly, Rx, Ry; }
    [StructLayout(LayoutKind.Sequential)]
    struct XKey { public ushort Vk, Unicode, Flags; public byte User, Hid; }
    [DllImport("xinput1_4.dll")] static extern uint XInputGetState(uint index, out XState state);
    [DllImport("xinput1_4.dll")] static extern uint XInputGetKeystroke(uint index, uint reserved, out XKey key);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern IntPtr GetModuleHandleW(string name);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern uint GetModuleFileNameW(IntPtr module, StringBuilder buf, uint size);
    public bool xinput;
    bool padLogged;
    uint padR = uint.MaxValue;
    ushort padB;
    short padLx, padLy;
    int scene;

    FakeGame(string logPath, string csvPath, string perfPath, double crashAfter, bool ignoreClose)
    {
        this.crashAfter = crashAfter;
        this.ignoreClose = ignoreClose;
        Text = "Fake Dimensions (harness self-test)";
        Width = 640;
        Height = 360;
        if (!string.IsNullOrEmpty(logPath)) log = new StreamWriter(logPath, false) { AutoFlush = true };
        Log("info", "gpu", "DXGI adapter: Harness Fake Adapter (vendor 0x0000, device 0x0000, 0 MB dedicated)");
        Log("info", "core", "XEX patch applied successfully: base version: 0.0.0.3, new version: 0.0.23.3");
        Log("info", "core", "Initializing shader storage for title 5752084B...");
        Log("warning", "core", "Config: unknown cvar 'fake_selftest_cvar'");
        Log("info", "core", "cwd=" + Environment.CurrentDirectory + " args=" + string.Join(" ", Environment.GetCommandLineArgs()));
        if (!string.IsNullOrEmpty(csvPath))
        {
            csv = new StreamWriter(csvPath, false);
            csv.WriteLine("frame,interval_ms,texture_ms,draw_calls,sync_ms,pipeline_creations,pipeline_creation_ms,"
                + "scene_render_width,scene_render_height,output_width,output_height,presentation_focused,native_vsync,native_fps_limit_cvar");
        }
        if (!string.IsNullOrEmpty(perfPath))
        {
            perf = new StreamWriter(perfPath, false);
            perf.WriteLine("frame_time_us,fps,draw_calls,command_buffer_stalls,vertices_processed,xma_frames_decoded,"
                + "audio_frame_latency_us,buffer_queue_depth,functions_dispatched,interrupt_dispatches,active_threads,"
                + "apc_queue_depth,critical_region_contentions,texture_cache_hits,texture_cache_misses,pipeline_cache_hits,pipeline_cache_misses");
        }
        timer.Interval = 15;
        timer.Tick += (s, e) => Present();
        timer.Start();
        FormClosing += (s, e) =>
        {
            if (this.ignoreClose) { e.Cancel = true; Log("info", "core", "ignoring WM_CLOSE (self-test)"); return; }
            Log("info", "core", "window close requested; shutting down");
            if (csv != null) csv.Flush();
            if (perf != null) perf.Flush();
        };
    }

    void Log(string level, string cat, string msg)
    {
        if (log == null) return;
        lock (log)
            log.WriteLine("[{0}] [{1}] [{2}] [t{3}] {4}", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff", CultureInfo.InvariantCulture),
                level, cat, Environment.CurrentManagedThreadId, msg);
    }

    void PollPad()
    {
        XState s;
        uint r = XInputGetState(0, out s);
        if (!padLogged)
        {
            padLogged = true;
            var path = new StringBuilder(520);
            GetModuleFileNameW(GetModuleHandleW("xinput1_4.dll"), path, 520);
            Log("info", "input", "fake xinput: xinput1_4.dll from " + path);
        }
        if (r != padR || s.Buttons != padB || s.Lx != padLx || s.Ly != padLy)
        {
            if (r == 0 && (s.Buttons & 0x1000) != 0 && (padB & 0x1000) == 0) scene++;
            Log("info", "input", string.Format(CultureInfo.InvariantCulture, "fake xinput: result {0} buttons 0x{1:X4} lx {2} ly {3} packet {4} scene {5}",
                r, s.Buttons, s.Lx, s.Ly, s.Packet, scene));
            padR = r; padB = s.Buttons; padLx = s.Lx; padLy = s.Ly;
        }
        XKey k;
        for (int n = 0; n < 32 && XInputGetKeystroke(0, 0, out k) == 0; n++)
            Log("info", "input", string.Format(CultureInfo.InvariantCulture, "fake xinput: key 0x{0:X4} flags {1}", k.Vk, k.Flags));
    }

    void Present()
    {
        double now = clock.Elapsed.TotalMilliseconds;
        if (crashAfter > 0 && now > crashAfter * 1000)
        {
            Log("critical", "core", "self-test crash");
            throw new InvalidOperationException("harness self-test crash");
        }
        if (xinput) PollPad();
        frame++;
        if (frame == 1) Log("info", "gpu", "first frame presented (self-test)");
        if (frame > 1)
        {
            double dt = now - last;
            if (csv != null)
                csv.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0},{1:F3},0,{2},0.1,{3},{4},640,360,640,360,{5},0,60",
                    frame, dt, 800 + frame % 50, frame < 30 ? 1 : 0, frame < 30 ? 2.5 : 0.0, Form.ActiveForm == this ? 1 : 0));
            if (perf != null)
            {
                long us = (long)(dt * 1000);
                perf.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0},{1},{2},0,{3},0,0,0,{4},1,40,0,0,{5},{6},{7},{8}",
                    us, us > 0 ? 1000000 / us : 0, xinput ? 900 + 10 * scene : 900 + frame % 40, xinput ? 120000 + scene : 120000 + frame % 1000,
                    50000, 300, frame < 30 ? 5 : 0, 400, frame < 30 ? 3 : 0));
                if (++perfRows % 60 == 0) perf.Flush();
            }
        }
        if (csv != null && frame % 120 == 0) csv.Flush();
        last = now;
    }

    // Synthetic sampler: same trigger protocol and file format as sample_profiler.cpp.
    static void Sampler(string trigger, Action<string, string, string> log)
    {
        bool rec = false;
        long q0 = 0;
        while (true)
        {
            bool on = File.Exists(trigger);
            if (on && !rec) { rec = true; q0 = Stopwatch.GetTimestamp(); log("info", "prof", "sample profiler: recording (self-test)"); }
            if (!on && rec)
            {
                rec = false;
                long q1 = Stopwatch.GetTimestamp();
                long rounds = (q1 - q0) * 1000 / Stopwatch.Frequency;
                string exe = Process.GetCurrentProcess().MainModule.FileName;
                string path = Path.Combine(Path.GetDirectoryName(exe), "profile-" + Environment.TickCount + ".bin");
                using (var w = new BinaryWriter(File.Create(path)))
                {
                    w.Write(Encoding.ASCII.GetBytes("LSP1"));
                    w.Write(1u);
                    byte[] name = Encoding.ASCII.GetBytes(Path.GetFileName(exe));
                    w.Write(0x140000000UL); w.Write(0x10000u); w.Write((uint)name.Length); w.Write(name);
                    long n = Math.Min(rounds, 20000);
                    long quarter = n / 4;
                    w.Write((ulong)(n + quarter));
                    for (long i = 0; i < n; i++) { w.Write(1u); w.Write(2u); w.Write(0x140001010UL); w.Write(0x140002020UL); }
                    for (long i = 0; i < quarter; i++) { w.Write(2u); w.Write(1u); w.Write(0x140003010UL); }
                    var body = new MemoryStream();
                    var b = new BinaryWriter(body);
                    b.Write((ulong)Stopwatch.Frequency); b.Write((ulong)q0); b.Write((ulong)q1); b.Write((ulong)rounds);
                    b.Write(1u); b.Write(2u);
                    foreach (var t in new[] { Tuple.Create(1u, "fake-main"), Tuple.Create(2u, "fake-render") })
                    { byte[] tn = Encoding.UTF8.GetBytes(t.Item2); b.Write(t.Item1); b.Write((uint)tn.Length); b.Write(tn); }
                    b.Flush();
                    w.Write(Encoding.ASCII.GetBytes("LSPX")); w.Write(1u); w.Write((uint)body.Length); w.Write(body.ToArray());
                }
                log("info", "prof", "sample profiler: wrote " + path);
            }
            Thread.Sleep(50);
        }
    }

    [STAThread]
    static int Main(string[] args)
    {
        string logPath = null, perfPath = null;
        double crash = 0;
        bool ignore = false, xin = false;
        foreach (var a in args)
        {
            if (a.StartsWith("--log_file=")) logPath = a.Substring(11);
            else if (a.StartsWith("--perf_log_csv=")) perfPath = a.Substring(15);
            else if (a.StartsWith("--fake_crash_after=")) crash = double.Parse(a.Substring(19), CultureInfo.InvariantCulture);
            else if (a == "--fake_ignore_close") ignore = true;
            else if (a == "--input_backend=xinput") xin = true;
        }
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.ThrowException);
        var form = new FakeGame(logPath, Environment.GetEnvironmentVariable("LEGO_NATIVE_FRAME_METRICS"), perfPath, crash, ignore);
        form.xinput = xin;
        string trig = Environment.GetEnvironmentVariable("LEGO_SAMPLE_PROFILE_TRIGGER");
        if (Environment.GetEnvironmentVariable("LEGO_SAMPLE_PROFILE") != null && !string.IsNullOrEmpty(trig))
            new Thread(() => Sampler(trig, form.Log)) { IsBackground = true }.Start();
        Application.Run(form);
        return 0;
    }
}
