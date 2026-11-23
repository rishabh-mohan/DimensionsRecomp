// harness/nvml.cs - NVIDIA GPU state for run-game.ps1 -GpuLog (Agent 3).
// NVML (nvml.dll, installed in System32 by the driver), queried once per pass of the harness's 1 s sampling
// loop: no extra process and nothing buffered (nvidia-smi -f buffers its file until it exits, so a killed
// logger loses everything; tested 21 Nov). GPU 0 only (the MX570 on this laptop). C# 5 (Windows PowerShell 5.1).
using System;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;

public static class LdNvml {
    [StructLayout(LayoutKind.Sequential)] public struct Util { public uint Gpu; public uint Memory; }
    [DllImport("nvml.dll", EntryPoint = "nvmlInit_v2")] static extern int Init();
    [DllImport("nvml.dll", EntryPoint = "nvmlShutdown")] static extern int Shutdown();
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetHandleByIndex_v2")] static extern int Handle(uint index, out IntPtr dev);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetName", CharSet = CharSet.Ansi)] static extern int GetName(IntPtr dev, StringBuilder name, uint len);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetPerformanceState")] static extern int Pstate(IntPtr dev, out int p);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetClockInfo")] static extern int Clock(IntPtr dev, int type, out uint mhz);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetTemperature")] static extern int Temp(IntPtr dev, int sensor, out uint c);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetPowerUsage")] static extern int Power(IntPtr dev, out uint mw);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetUtilizationRates")] static extern int Utilization(IntPtr dev, out Util u);
    [DllImport("nvml.dll", EntryPoint = "nvmlDeviceGetCurrentClocksThrottleReasons")] static extern int Reasons(IntPtr dev, out ulong r);

    static IntPtr dev = IntPtr.Zero;
    public static string Name = "";

    // null on success, else the reason there is no GPU log.
    public static string Open() {
        try {
            int rc = Init();
            if (rc != 0) return "nvmlInit_v2 returned " + rc;
            rc = Handle(0, out dev);
            if (rc != 0) { dev = IntPtr.Zero; Shutdown(); return "nvmlDeviceGetHandleByIndex_v2(0) returned " + rc; }
            StringBuilder sb = new StringBuilder(96);
            if (GetName(dev, sb, 96) == 0) Name = sb.ToString();
            return null;
        } catch (Exception e) { dev = IntPtr.Zero; return e.GetType().Name + ": " + e.Message; }
    }

    public static void Close() { if (dev != IntPtr.Zero) { try { Shutdown(); } catch { } dev = IntPtr.Zero; } }

    static string Try(Func<string> f) { try { return f(); } catch { return ""; } }

    // "pstate,gr_mhz,mem_mhz,temp_c,power_w,util_gpu,util_mem,throttle"; a field is empty when its query fails.
    // throttle = clock limit reasons bitmask: 0x1 GPU idle, 0x4 software power cap, 0x8 hardware slowdown,
    // 0x20/0x40 software/hardware thermal slowdown.
    public static string Sample() {
        if (dev == IntPtr.Zero) return ",,,,,,,";
        CultureInfo inv = CultureInfo.InvariantCulture;
        string ps = Try(delegate { int v; return Pstate(dev, out v) == 0 ? "P" + v.ToString(inv) : ""; });
        string gr = Try(delegate { uint v; return Clock(dev, 0, out v) == 0 ? v.ToString(inv) : ""; });
        string mem = Try(delegate { uint v; return Clock(dev, 2, out v) == 0 ? v.ToString(inv) : ""; });
        string t = Try(delegate { uint v; return Temp(dev, 0, out v) == 0 ? v.ToString(inv) : ""; });
        string pw = Try(delegate { uint v; return Power(dev, out v) == 0 ? (v / 1000.0).ToString("F2", inv) : ""; });
        string ug = "", um = "";
        try { Util u; if (Utilization(dev, out u) == 0) { ug = u.Gpu.ToString(inv); um = u.Memory.ToString(inv); } } catch { }
        string th = Try(delegate { ulong v; return Reasons(dev, out v) == 0 ? "0x" + v.ToString("X", inv) : ""; });
        return string.Join(",", new string[] { ps, gr, mem, t, pw, ug, um, th });
    }
}
