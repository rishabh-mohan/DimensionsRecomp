// Offline minidump analyzer for bench/agent11/testg_dump.ps1 (test G, task #23).
// Loaded with Add-Type by Windows PowerShell 5.1, so C# 5 only (no $"..", no => members, no ?.).
// Input: an x64 minidump such as TestGWin.MiniDump writes (MiniDumpWithHandleData |
// MiniDumpWithUnloadedModules | MiniDumpWithThreadInfo: threads + stacks, modules, thread info,
// thread names, handles; no code memory). Output: a plain-text report: header, one block per thread
// (id, name, suspend count, priority, CPU time, start address, RIP, RSP, heuristic call stack) and a
// summary (suspended threads, waits with their first non-system frame, running threads, UI thread).
//   Call stack: no unwinding (no PDBs, no code memory in the dump). The captured stack is scanned
//   from RSP upward for 8-byte values that point into a loaded module right after a CALL instruction
//   (E8 rel32 with a target inside the image, or FF /2 in any addressing form, optional REX prefix),
//   checked against the module file on disk (-BinDir, the dump's directory, then the path recorded
//   in the dump; TimeDateStamp and SizeOfImage must match the dump). Values in modules whose file
//   cannot be read are kept and marked '?'. Stale return addresses left in locals can show up.
//   Symbols: an MSVC /MAP file next to the module (publics and statics, nearest lower symbol, map
//   timestamp must match), else the nearest lower PE export, marked "(nearest export)".
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;

public static class TestGDump
{
    [DllImport("dbghelp.dll", CharSet = CharSet.Ansi)]
    static extern uint UnDecorateSymbolName(string name, StringBuilder output, uint maxLength, uint flags);

    const uint UNDNAME_NAME_ONLY = 0x1000;
    static readonly string[] SystemModules = { "ntdll", "kernelbase", "kernel32", "win32u" };
    static readonly Regex WaitExport = new Regex(@"^(Nt|Zw)\w*(Wait|DelayExecution|RemoveIoCompletion|GetMessage)");
    static readonly Dictionary<string, string> WaitHints = new Dictionary<string, string>
    {
        { "NtWaitForAlertByThreadId", "SRW lock / condition variable / WaitOnAddress" },
        { "NtDelayExecution", "Sleep" },
        { "NtWaitForSingleObject", "WaitForSingleObject" },
        { "NtWaitForMultipleObjects", "WaitForMultipleObjects" },
        { "NtRemoveIoCompletion", "I/O completion port" },
        { "NtRemoveIoCompletionEx", "I/O completion port" },
        { "NtWaitForWorkViaWorkerFactory", "idle thread-pool worker" },
        { "NtWaitForKeyedEvent", "keyed event (critical section / loader lock)" },
        { "NtUserMsgWaitForMultipleObjectsEx", "message loop (MsgWaitForMultipleObjectsEx)" },
        { "NtUserGetMessage", "message loop (GetMessage)" },
        { "NtUserWaitMessage", "message loop (WaitMessage)" },
    };

    static uint U32(byte[] b, int o) { return BitConverter.ToUInt32(b, o); }
    static ulong U64(byte[] b, int o) { return BitConverter.ToUInt64(b, o); }
    static ushort U16(byte[] b, int o) { return BitConverter.ToUInt16(b, o); }

    static string Undecorate(string n)
    {
        if (n.Length < 2 || n[0] != '?') return n;
        try
        {
            var b = new StringBuilder(1024);
            return UnDecorateSymbolName(n, b, (uint)b.Capacity, UNDNAME_NAME_ONLY) != 0 ? b.ToString() : n;
        }
        catch (Exception) { return n; }
    }

    // ------------------------------------------------------------------ PE file on disk
    public sealed class PeFile : IDisposable
    {
        public string FilePath;
        public long Length;
        public uint TimeStamp, SizeOfImage, ExportRva, ExportSize;
        public ulong ImageBase;
        uint[] secVa, secVSize, secRaw, secRawSize, secChar;
        FileStream fs;
        readonly Dictionary<long, byte[]> pages = new Dictionary<long, byte[]>();
        uint[] expRva;
        string[] expName;

        public static PeFile Open(string path, out string error)
        {
            error = null;
            var pe = new PeFile();
            pe.FilePath = path;
            try
            {
                pe.fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, 4096, FileOptions.RandomAccess);
                pe.Length = pe.fs.Length;
                byte[] dos = pe.ReadFile(0, 64);
                if (dos == null || dos[0] != 0x4D || dos[1] != 0x5A) { error = "not a PE file"; pe.Dispose(); return null; }
                long lfanew = U32(dos, 0x3C);
                byte[] nt = pe.ReadFile(lfanew, 24 + 240);
                if (nt == null || U32(nt, 0) != 0x00004550) { error = "no PE signature"; pe.Dispose(); return null; }
                int nSec = U16(nt, 6);
                pe.TimeStamp = U32(nt, 8);
                int optSize = U16(nt, 20);
                int magic = U16(nt, 24);
                if (magic == 0x20B)
                {
                    pe.ImageBase = U64(nt, 24 + 24); pe.SizeOfImage = U32(nt, 24 + 56);
                    if (U32(nt, 24 + 108) > 0) { pe.ExportRva = U32(nt, 24 + 112); pe.ExportSize = U32(nt, 24 + 116); }
                }
                else if (magic == 0x10B)
                {
                    pe.ImageBase = U32(nt, 24 + 28); pe.SizeOfImage = U32(nt, 24 + 56);
                    if (U32(nt, 24 + 92) > 0) { pe.ExportRva = U32(nt, 24 + 96); pe.ExportSize = U32(nt, 24 + 100); }
                }
                else { error = "unknown optional header magic 0x" + magic.ToString("X"); pe.Dispose(); return null; }
                byte[] sh = pe.ReadFile(lfanew + 24 + optSize, nSec * 40);
                if (sh == null) { error = "truncated section table"; pe.Dispose(); return null; }
                pe.secVa = new uint[nSec]; pe.secVSize = new uint[nSec]; pe.secRaw = new uint[nSec];
                pe.secRawSize = new uint[nSec]; pe.secChar = new uint[nSec];
                for (int i = 0; i < nSec; i++)
                {
                    int o = i * 40;
                    pe.secVSize[i] = U32(sh, o + 8); pe.secVa[i] = U32(sh, o + 12); pe.secRawSize[i] = U32(sh, o + 16);
                    pe.secRaw[i] = U32(sh, o + 20); pe.secChar[i] = U32(sh, o + 36);
                }
                return pe;
            }
            catch (Exception e) { error = e.Message; pe.Dispose(); return null; }
        }

        public void Dispose() { if (fs != null) { fs.Dispose(); fs = null; } }

        byte[] ReadFile(long off, int len)
        {
            if (off < 0 || len < 0 || off + len > Length) return null;
            var b = new byte[len];
            fs.Seek(off, SeekOrigin.Begin);
            int got = 0;
            while (got < len) { int k = fs.Read(b, got, len - got); if (k <= 0) return null; got += k; }
            return b;
        }

        int Section(uint rva)
        {
            for (int i = 0; i < secVa.Length; i++)
            {
                uint size = Math.Max(secVSize[i], secRawSize[i]);
                if (rva >= secVa[i] && rva - secVa[i] < size) return i;
            }
            return -1;
        }

        public bool IsCode(uint rva) { int s = Section(rva); return s >= 0 && (secChar[s] & 0x20000020) != 0; }

        long FileOffset(uint rva, int s)
        {
            uint d = rva - secVa[s];
            return d < secRawSize[s] ? (long)secRaw[s] + d : -1;
        }

        int ByteAt(long off)
        {
            if (off < 0 || off >= Length) return -1;
            long page = off >> 12;
            byte[] p;
            if (!pages.TryGetValue(page, out p))
            {
                p = ReadFile(page << 12, (int)Math.Min(4096L, Length - (page << 12)));
                if (p == null) return -1;
                pages[page] = p;
            }
            int i = (int)(off & 4095);
            return i < p.Length ? p[i] : -1;
        }

        byte[] ReadRva(uint rva, int len)
        {
            int s = Section(rva);
            if (s < 0) return null;
            long off = FileOffset(rva, s);
            return off < 0 ? null : ReadFile(off, len);
        }

        string ReadCString(uint rva)
        {
            int s = Section(rva);
            if (s < 0) return null;
            long off = FileOffset(rva, s);
            if (off < 0) return null;
            byte[] b = ReadFile(off, (int)Math.Min(512L, Length - off));
            if (b == null) return null;
            int n = Array.IndexOf(b, (byte)0);
            return Encoding.ASCII.GetString(b, 0, n < 0 ? b.Length : n);
        }

        // The n bytes that end right before rva, from the section holding rva-1 (bytes before the
        // section start read as 0), or null when that part of the image is not backed by the file.
        byte[] Before(uint rva, int n)
        {
            if (rva < 1) return null;
            int s = Section(rva - 1);
            if (s < 0 || FileOffset(rva - 1, s) < 0) return null;
            var r = new byte[n];
            for (int i = 0; i < n; i++)
            {
                long a = (long)rva - n + i;
                if (a < secVa[s]) continue;
                int b = ByteAt(FileOffset((uint)a, s));
                if (b < 0) return null;
                r[i] = (byte)b;
            }
            return r;
        }

        // Is the instruction that ends right before rva a CALL? E8 rel32 whose target is code in
        // this image, or FF /2 (call r/m64) in any addressing form, with an optional REX prefix.
        public bool PrecededByCall(uint rva)
        {
            if (rva < 2 || !IsCode(rva - 1)) return false;
            byte[] b = Before(rva, 8);          // b[8 - k] is the byte at rva - k
            if (b == null) return false;
            if (b[3] == 0xE8)
            {
                long target = (long)rva + BitConverter.ToInt32(b, 4);
                if (target >= 0 && target < SizeOfImage && IsCode((uint)target)) return true;
            }
            for (int k = 2; k <= 8; k++)
            {
                int p = 8 - k;
                if (b[p] >= 0x40 && b[p] <= 0x4F) p++;
                if (p > 6 || b[p] != 0xFF) continue;
                int modrm = b[p + 1];
                if (((modrm >> 3) & 7) != 2) continue;
                int mod = modrm >> 6, rm = modrm & 7, len = 2;
                if (mod != 3 && rm == 4)
                {
                    if (p + 2 > 7) continue;
                    len++;
                    if (mod == 0 && (b[p + 2] & 7) == 5) len += 4;
                }
                if (mod == 0 && rm == 5) len += 4;
                else if (mod == 1) len += 1;
                else if (mod == 2) len += 4;
                if (p + len == 8) return true;
            }
            return false;
        }

        public string NearestExport(uint rva, out uint disp)
        {
            disp = 0;
            if (expRva == null) LoadExports();
            int i = Array.BinarySearch(expRva, rva);
            if (i < 0) i = ~i - 1;
            if (i < 0) return null;
            while (i > 0 && expRva[i - 1] == expRva[i]) i--;
            int pick = i;
            for (int j = i; j < expRva.Length && expRva[j] == expRva[i]; j++)
                if (!expName[j].StartsWith("Zw", StringComparison.Ordinal)) { pick = j; break; }
            disp = rva - expRva[pick];
            return expName[pick];
        }

        public int ExportCount { get { if (expRva == null) LoadExports(); return expRva.Length; } }

        void LoadExports()
        {
            var rvas = new List<uint>();
            var names = new List<string>();
            try
            {
                byte[] d = (ExportRva != 0 && ExportSize >= 40) ? ReadRva(ExportRva, 40) : null;
                if (d != null)
                {
                    uint ordBase = U32(d, 16), nFunc = U32(d, 20), nNames = U32(d, 24);
                    if (nFunc < 200000 && nNames < 200000)
                    {
                        byte[] funcs = ReadRva(U32(d, 28), (int)nFunc * 4);
                        byte[] nameRvas = ReadRva(U32(d, 32), (int)nNames * 4);
                        byte[] ords = ReadRva(U32(d, 36), (int)nNames * 2);
                        if (funcs != null && nameRvas != null && ords != null)
                        {
                            var named = new bool[nFunc];
                            for (int i = 0; i < nNames; i++)
                            {
                                int o = U16(ords, i * 2);
                                if (o >= nFunc) continue;
                                named[o] = true;
                                uint f = U32(funcs, o * 4);
                                if (f == 0 || (f >= ExportRva && f < ExportRva + ExportSize)) continue;   // forwarder
                                string nm = ReadCString(U32(nameRvas, i * 4));
                                if (string.IsNullOrEmpty(nm)) continue;
                                rvas.Add(f); names.Add(nm);
                            }
                            for (int o = 0; o < nFunc; o++)
                            {
                                if (named[o]) continue;
                                uint f = U32(funcs, o * 4);
                                if (f == 0 || (f >= ExportRva && f < ExportRva + ExportSize)) continue;
                                rvas.Add(f); names.Add("#" + (ordBase + o));
                            }
                        }
                    }
                }
            }
            catch (Exception) { }
            expRva = rvas.ToArray();
            expName = names.ToArray();
            Array.Sort(expRva, expName);
        }
    }

    // ------------------------------------------------------------------ MSVC /MAP symbols
    // Lines of the "Publics by Value" and "Static symbols" tables:
    //   " 0001:00000000       ?Foo@@YAXXZ   0000000140001000 f   foo.obj"
    // RVA = Rva+Base - "Preferred load address". Names stay in the file bytes until looked up.
    public sealed class MapSymbols
    {
        public string FilePath;
        public ulong Preferred;
        public uint TimeStamp;
        public int Count;
        public long LoadMs;
        byte[] data;
        uint[] rvas;
        int[] offs;

        static int IndexOf(byte[] d, string s, int from, int limit)
        {
            byte[] n = Encoding.ASCII.GetBytes(s);
            int last = Math.Min(d.Length, limit) - n.Length;
            for (int i = from; i <= last; i++)
            {
                if (d[i] != n[0]) continue;
                int j = 1;
                while (j < n.Length && d[i + j] == n[j]) j++;
                if (j == n.Length) return i;
            }
            return -1;
        }

        static int Hex(byte c)
        {
            if (c >= '0' && c <= '9') return c - '0';
            if (c >= 'a' && c <= 'f') return c - 'a' + 10;
            if (c >= 'A' && c <= 'F') return c - 'A' + 10;
            return -1;
        }

        static ulong ParseHex(byte[] d, int p)
        {
            ulong v = 0;
            while (p < d.Length && Hex(d[p]) >= 0) { v = (v << 4) | (uint)Hex(d[p]); p++; }
            return v;
        }

        public static MapSymbols Load(string path)
        {
            var sw = Stopwatch.StartNew();
            var m = new MapSymbols();
            m.FilePath = path;
            byte[] d = File.ReadAllBytes(path);
            m.data = d;
            int pl = IndexOf(d, "Preferred load address is ", 0, 1 << 16);
            if (pl >= 0) m.Preferred = ParseHex(d, pl + 26);
            int ts = IndexOf(d, "Timestamp is ", 0, 1 << 16);
            if (ts >= 0) m.TimeStamp = (uint)ParseHex(d, ts + 13);
            var r = new List<uint>(1 << 18);
            var o = new List<int>(1 << 18);
            int start = IndexOf(d, "Publics by Value", 0, d.Length);
            if (start >= 0)
            {
                int i = start, n = d.Length;
                while (i < n && d[i] != '\n') i++;
                while (i < n)
                {
                    int e = i;
                    while (e < n && d[e] != '\n') e++;
                    int p = i;
                    i = e + 1;
                    while (p < e && d[p] == ' ') p++;
                    if (p + 14 > e || d[p + 4] != ':' || Hex(d[p]) < 0 || Hex(d[p + 5]) < 0 || d[p + 13] != ' ') continue;
                    p += 13;
                    while (p < e && d[p] == ' ') p++;
                    int ns = p;
                    while (p < e && d[p] != ' ' && d[p] != '\r') p++;
                    if (p == ns) continue;
                    while (p < e && d[p] == ' ') p++;
                    int hs = p;
                    ulong v = 0;
                    while (p < e && Hex(d[p]) >= 0) { v = (v << 4) | (uint)Hex(d[p]); p++; }
                    if (p - hs < 8 || (p < e && d[p] != ' ' && d[p] != '\r')) continue;
                    if (v < m.Preferred || v - m.Preferred > uint.MaxValue) continue;
                    r.Add((uint)(v - m.Preferred));
                    o.Add(ns);
                }
            }
            m.rvas = r.ToArray();
            m.offs = o.ToArray();
            Array.Sort(m.rvas, m.offs);
            m.Count = m.rvas.Length;
            m.LoadMs = sw.ElapsedMilliseconds;
            return m;
        }

        public string Lookup(uint rva, out uint disp)
        {
            disp = 0;
            int i = Array.BinarySearch(rvas, rva);
            if (i < 0) i = ~i - 1;
            if (i < 0) return null;
            disp = rva - rvas[i];
            int s = offs[i], e = s;
            while (e < data.Length && data[e] != ' ' && data[e] != '\r' && data[e] != '\n') e++;
            return Encoding.ASCII.GetString(data, s, e - s);
        }
    }

    // ------------------------------------------------------------------ dump model
    public sealed class Module
    {
        public int Index;
        public ulong Base;
        public uint Size, CheckSum, TimeStamp;
        public string FullPath, Name, Short;
        public PeFile Pe;              // verified file (TimeDateStamp and SizeOfImage match), or null
        public string FileNote, MapNote;
        public MapSymbols Map;
        public bool PeTried, MapTried, Seen;
    }

    public sealed class Frame
    {
        public ulong Addr;
        public long SpOffset;          // offset from RSP of the stack slot; long.MinValue for RIP
        public Module Mod;
        public bool Unverified;        // module file unreadable: CALL not checked
        public string Where;           // module+0xRVA
        public string Name;            // bare symbol name (map or export), or null
        public string Sym;             // module!name+0xdisp [(nearest export)], or null
        public string Text { get { return Sym ?? Where; } }
    }

    public sealed class ThreadRec
    {
        public int Index;
        public uint Id, SuspendCount, PriorityClass, Priority, StackSize, StackRva, CtxSize, CtxRva;
        public ulong Teb, StackStart, Rip, Rsp;
        public bool HasCtx, HasInfo;
        public uint DumpFlags, DumpError, ExitStatus;
        public ulong CreateTime, ExitTime, KernelTime, UserTime, StartAddress;
        public string Name;
        public Frame Start;
        public readonly List<Frame> Frames = new List<Frame>();
    }

    public static string Analyze(string dumpPath, string binDir, string binNote, int maxFrames)
    {
        return new Analysis().Run(dumpPath, binDir, binNote, maxFrames);
    }

    // Symbols for one RVA of a module file, for tests: map lookup if a .map is given, else exports.
    public static string LookupInFile(string pePath, string mapPath, uint rva)
    {
        uint disp;
        if (!string.IsNullOrEmpty(mapPath))
        {
            MapSymbols m = MapSymbols.Load(mapPath);
            string n = m.Lookup(rva, out disp);
            return string.Format("{0}+0x{1:X} ({2} symbols, {3} ms)", n == null ? "?" : Undecorate(n), disp, m.Count, m.LoadMs);
        }
        string err;
        using (PeFile pe = PeFile.Open(pePath, out err))
        {
            if (pe == null) return "error: " + err;
            string n = pe.NearestExport(rva, out disp);
            return string.Format("{0}+0x{1:X} (nearest export; call before: {2})", n ?? "?", disp, pe.PrecededByCall(rva));
        }
    }

    sealed class Analysis
    {
        FileStream fs;
        long dumpLen;
        string binDir, dumpDir;
        readonly Dictionary<uint, uint[]> streams = new Dictionary<uint, uint[]>();
        readonly List<Module> modules = new List<Module>();
        Module[] modSorted = new Module[0];
        ulong[] modBases = new ulong[0];
        readonly List<ThreadRec> threads = new List<ThreadRec>();

        byte[] Read(long rva, int len)
        {
            if (rva < 0 || len < 0 || rva + len > dumpLen) return null;
            var b = new byte[len];
            fs.Seek(rva, SeekOrigin.Begin);
            int got = 0;
            while (got < len) { int k = fs.Read(b, got, len - got); if (k <= 0) return null; got += k; }
            return b;
        }

        string ReadMdString(long rva)
        {
            byte[] l = Read(rva, 4);
            if (l == null) return null;
            uint n = U32(l, 0);
            if (n > 65536) return null;
            byte[] s = Read(rva + 4, (int)n);
            return s == null ? null : Encoding.Unicode.GetString(s);
        }

        byte[] GetStream(uint type)
        {
            uint[] e;
            if (!streams.TryGetValue(type, out e) || e[0] == 0) return null;
            return Read(e[1], (int)Math.Min(e[0], 256u << 20));
        }

        ThreadRec ThreadById(uint id)
        {
            foreach (ThreadRec t in threads) if (t.Id == id) return t;
            return null;
        }

        Module FindModule(ulong addr)
        {
            if (modBases.Length == 0) return null;
            int i = Array.BinarySearch(modBases, addr);
            if (i < 0) i = ~i - 1;
            if (i < 0) return null;
            Module m = modSorted[i];
            return addr - m.Base < m.Size ? m : null;
        }

        static bool IsSystem(Module m)
        {
            return m != null && Array.IndexOf(SystemModules, m.Short.ToLowerInvariant()) >= 0;
        }

        void ReadModules()
        {
            byte[] s = GetStream(4);
            if (s == null || s.Length < 4) return;
            uint n = U32(s, 0);
            for (int i = 0; i < n && 4 + (i + 1) * 108 <= s.Length; i++)
            {
                int o = 4 + i * 108;
                var m = new Module();
                m.Index = i;
                m.Base = U64(s, o); m.Size = U32(s, o + 8); m.CheckSum = U32(s, o + 12); m.TimeStamp = U32(s, o + 16);
                m.FullPath = ReadMdString(U32(s, o + 20)) ?? ("module" + i);
                try { m.Name = Path.GetFileName(m.FullPath); } catch (Exception) { m.Name = m.FullPath; }
                int dot = m.Name.LastIndexOf('.');
                m.Short = dot > 0 ? m.Name.Substring(0, dot) : m.Name;
                modules.Add(m);
            }
            modSorted = modules.ToArray();
            modBases = new ulong[modSorted.Length];
            for (int i = 0; i < modSorted.Length; i++) modBases[i] = modSorted[i].Base;
            Array.Sort(modBases, modSorted);
        }

        void ReadThreads()
        {
            byte[] s = GetStream(3);
            if (s == null || s.Length < 4) return;
            uint n = U32(s, 0);
            for (int i = 0; i < n && 4 + (i + 1) * 48 <= s.Length; i++)
            {
                int o = 4 + i * 48;
                var t = new ThreadRec();
                t.Index = i;
                t.Id = U32(s, o); t.SuspendCount = U32(s, o + 4); t.PriorityClass = U32(s, o + 8); t.Priority = U32(s, o + 12);
                t.Teb = U64(s, o + 16); t.StackStart = U64(s, o + 24); t.StackSize = U32(s, o + 32); t.StackRva = U32(s, o + 36);
                t.CtxSize = U32(s, o + 40); t.CtxRva = U32(s, o + 44);
                if (t.CtxSize >= 0x100)
                {
                    byte[] c = Read(t.CtxRva, 0x100);
                    if (c != null) { t.Rsp = U64(c, 0x98); t.Rip = U64(c, 0xF8); t.HasCtx = true; }
                }
                threads.Add(t);
            }
        }

        void ReadThreadInfo()
        {
            byte[] s = GetStream(17);
            if (s == null || s.Length < 12) return;
            uint hdr = U32(s, 0), entry = U32(s, 4), n = U32(s, 8);
            if (entry < 64) return;
            for (long i = 0; i < n; i++)
            {
                long o = hdr + i * entry;
                if (o + 64 > s.Length) break;
                int p = (int)o;
                ThreadRec t = ThreadById(U32(s, p));
                if (t == null) continue;
                t.HasInfo = true;
                t.DumpFlags = U32(s, p + 4); t.DumpError = U32(s, p + 8); t.ExitStatus = U32(s, p + 12);
                t.CreateTime = U64(s, p + 16); t.ExitTime = U64(s, p + 24); t.KernelTime = U64(s, p + 32);
                t.UserTime = U64(s, p + 40); t.StartAddress = U64(s, p + 48);
            }
        }

        void ReadThreadNames()
        {
            byte[] s = GetStream(24);
            if (s == null || s.Length < 4) return;
            uint n = U32(s, 0);
            for (int i = 0; i < n && 4 + (i + 1) * 12 <= s.Length; i++)
            {
                int o = 4 + i * 12;
                ThreadRec t = ThreadById(U32(s, o));
                if (t == null) continue;
                string nm = ReadMdString((long)U64(s, o + 4));
                if (!string.IsNullOrEmpty(nm)) t.Name = nm;
            }
        }

        void EnsurePe(Module m)
        {
            if (m.PeTried) return;
            m.PeTried = true;
            var cands = new List<string>();
            if (binDir != null) cands.Add(Path.Combine(binDir, m.Name));
            if (dumpDir != null) cands.Add(Path.Combine(dumpDir, m.Name));
            cands.Add(m.FullPath);
            string note = null;
            foreach (string c in cands)
            {
                bool exists;
                try { exists = File.Exists(c); } catch (Exception) { exists = false; }
                if (!exists) continue;
                string err;
                PeFile pe = PeFile.Open(c, out err);
                if (pe == null) { if (note == null) note = c + ": " + err; continue; }
                if (pe.TimeStamp == m.TimeStamp && pe.SizeOfImage == m.Size) { m.Pe = pe; m.FileNote = c; return; }
                if (note == null) note = string.Format("{0}: timestamp {1:x8}/size 0x{2:X} differ from the dump, not used", c, pe.TimeStamp, pe.SizeOfImage);
                pe.Dispose();
            }
            m.FileNote = "NO FILE (" + (note ?? "not found in the bin dir, the dump dir or at its path") + "): frames marked '?'";
        }

        void EnsureMap(Module m)
        {
            if (m.MapTried) return;
            m.MapTried = true;
            EnsurePe(m);
            var dirs = new List<string>();
            if (m.Pe != null) dirs.Add(Path.GetDirectoryName(m.Pe.FilePath));
            if (binDir != null) dirs.Add(binDir);
            if (dumpDir != null) dirs.Add(dumpDir);
            var tried = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (string d in dirs)
            {
                string f = Path.Combine(d, m.Short + ".map");
                if (!tried.Add(f) || !File.Exists(f)) continue;
                try
                {
                    MapSymbols ms = MapSymbols.Load(f);
                    if (ms.TimeStamp != 0 && ms.TimeStamp != m.TimeStamp)
                    {
                        m.MapNote = string.Format("{0}: timestamp {1:x8} != module {2:x8}, not used", f, ms.TimeStamp, m.TimeStamp);
                        continue;
                    }
                    m.Map = ms;
                    m.MapNote = string.Format("map {0}: {1} symbols, parsed in {2} ms", f, ms.Count, ms.LoadMs);
                    return;
                }
                catch (Exception e) { m.MapNote = f + ": " + e.Message; }
            }
        }

        Frame Describe(ulong addr, long spOffset, bool unverified)
        {
            var f = new Frame();
            f.Addr = addr;
            f.SpOffset = spOffset;
            f.Unverified = unverified;
            f.Mod = FindModule(addr);
            if (f.Mod == null) { f.Where = string.Format("0x{0:X} (no module)", addr); return f; }
            f.Mod.Seen = true;
            uint rva = (uint)(addr - f.Mod.Base);
            f.Where = f.Mod.Short + "+0x" + rva.ToString("X");
            EnsureMap(f.Mod);
            uint disp;
            if (f.Mod.Map != null)
            {
                string n = f.Mod.Map.Lookup(rva, out disp);
                if (n != null)
                {
                    f.Name = Undecorate(n);
                    f.Sym = f.Mod.Short + "!" + f.Name + (disp != 0 ? "+0x" + disp.ToString("X") : "");
                    return f;
                }
            }
            if (f.Mod.Pe != null)
            {
                string n = f.Mod.Pe.NearestExport(rva, out disp);
                if (n != null)
                {
                    f.Name = n;
                    f.Sym = f.Mod.Short + "!" + n + "+0x" + disp.ToString("X") + " (nearest export)";
                }
            }
            return f;
        }

        void Walk(ThreadRec t, int maxFrames)
        {
            if (t.HasInfo && t.StartAddress != 0) t.Start = Describe(t.StartAddress, long.MinValue, false);
            if (!t.HasCtx) return;
            t.Frames.Add(Describe(t.Rip, long.MinValue, false));
            if (t.StackSize == 0) return;
            byte[] st = Read(t.StackRva, (int)Math.Min(t.StackSize, 64u << 20));
            if (st == null) return;
            ulong end = t.StackStart + (ulong)st.Length;
            ulong a = (t.Rsp >= t.StackStart && t.Rsp < end) ? t.Rsp : t.StackStart;
            a = (a + 7) & ~7UL;
            for (; a + 8 <= end && t.Frames.Count < maxFrames; a += 8)
            {
                ulong v = U64(st, (int)(a - t.StackStart));
                Module m = FindModule(v);
                if (m == null) continue;
                EnsurePe(m);
                bool unverified = m.Pe == null;
                if (!unverified && !m.Pe.PrecededByCall((uint)(v - m.Base))) continue;
                t.Frames.Add(Describe(v, (long)a - (long)t.Rsp, unverified));
            }
        }

        static string Label(ThreadRec t)
        {
            return "tid " + t.Id + (t.Name != null ? " '" + t.Name + "'" : "");
        }

        static string FrameLine(int i, Frame f)
        {
            string sp = f.SpOffset == long.MinValue ? "rip" : (f.SpOffset < 0 ? "rsp-0x" + (-f.SpOffset).ToString("X") : "rsp+0x" + f.SpOffset.ToString("X"));
            return string.Format("    {0,2} {1,-10} {2:X16}  {3,-30} {4}{5}", i, sp, f.Addr, f.Where, f.Sym ?? "", f.Unverified ? "  ?" : "");
        }

        static Frame FirstOutsideSystem(ThreadRec t)
        {
            foreach (Frame f in t.Frames) if (f.Mod != null && !IsSystem(f.Mod)) return f;
            return null;
        }

        static string WaitName(ThreadRec t)
        {
            if (t.Frames.Count == 0) return null;
            Frame f = t.Frames[0];
            if (f.Mod == null || f.Name == null) return null;
            string s = f.Mod.Short.ToLowerInvariant();
            if (s != "ntdll" && s != "win32u") return null;
            return WaitExport.IsMatch(f.Name) ? f.Name : null;
        }

        static string UiEvidence(ThreadRec t, out bool strong)
        {
            strong = false;
            var parts = new List<string>();
            foreach (Frame f in t.Frames)
            {
                string s = f.Mod == null ? "" : f.Mod.Short.ToLowerInvariant();
                bool win = s == "user32" || s == "win32u";
                bool app = s.StartsWith("sdl") || (f.Name != null && (f.Name.IndexOf("SDL_", StringComparison.Ordinal) >= 0
                    || f.Name.IndexOf("ReXApp", StringComparison.OrdinalIgnoreCase) >= 0));
                if (!win && !app) continue;
                if (win) strong = true;
                if (parts.Count < 3) parts.Add(f.Text);
            }
            return parts.Count == 0 ? null : string.Join("; ", parts.ToArray());
        }

        public string Run(string dumpPath, string bin, string binNote, int maxFrames)
        {
            var sw = Stopwatch.StartNew();
            var sb = new StringBuilder();
            binDir = string.IsNullOrEmpty(bin) ? null : Path.GetFullPath(bin);
            string full = Path.GetFullPath(dumpPath);
            dumpDir = Path.GetDirectoryName(full);
            if (maxFrames < 1) maxFrames = 1;
            using (fs = new FileStream(full, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
            {
                dumpLen = fs.Length;
                byte[] h = Read(0, 32);
                if (h == null || U32(h, 0) != 0x504D444D) throw new InvalidDataException("not a minidump (no MDMP signature): " + full);
                uint nStreams = U32(h, 8), dirRva = U32(h, 12), stamp = U32(h, 20);
                ulong flags = U64(h, 24);
                byte[] dir = Read(dirRva, (int)Math.Min(nStreams, 4096u) * 12);
                if (dir == null) throw new InvalidDataException("truncated stream directory: " + full);
                for (int i = 0; i < dir.Length / 12; i++)
                {
                    uint t = U32(dir, i * 12);
                    if (!streams.ContainsKey(t)) streams[t] = new uint[] { U32(dir, i * 12 + 4), U32(dir, i * 12 + 8) };
                }
                ReadModules();
                ReadThreads();
                ReadThreadInfo();
                ReadThreadNames();

                ushort arch = 0;
                byte[] si = GetStream(7);
                if (si != null && si.Length >= 2) arch = U16(si, 0);
                foreach (ThreadRec t in threads) Walk(t, maxFrames);

                var epoch = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
                sb.AppendLine("Minidump analysis (bench/agent11/testg_dump.ps1)");
                sb.AppendLine(string.Format("dump: {0} ({1:N0} bytes, flags 0x{2:X})", full, dumpLen, flags));
                sb.AppendLine(string.Format("written: {0:yyyy-MM-dd HH:mm:ss} local", epoch.AddSeconds(stamp).ToLocalTime()));
                byte[] mi = GetStream(15);
                if (mi != null && mi.Length >= 24)
                {
                    uint f1 = U32(mi, 4);
                    var parts = new List<string>();
                    if ((f1 & 1) != 0) parts.Add("pid " + U32(mi, 8));
                    if ((f1 & 2) != 0)
                        parts.Add(string.Format("created {0:yyyy-MM-dd HH:mm:ss}, process cpu user {1} s / kernel {2} s",
                            epoch.AddSeconds(U32(mi, 12)).ToLocalTime(), U32(mi, 16), U32(mi, 20)));
                    if (parts.Count > 0) sb.AppendLine("process: " + string.Join(", ", parts.ToArray()));
                }
                if (arch != 9) sb.AppendLine(string.Format("WARNING: processor architecture {0}, not AMD64 (9): the x64 CONTEXT offsets used here are wrong", arch));
                byte[] ex = GetStream(6);
                if (ex != null && ex.Length >= 32)
                    sb.AppendLine(string.Format("exception stream: tid {0}, code 0x{1:X8} at 0x{2:X16}", U32(ex, 0), U32(ex, 8), U64(ex, 24)));
                byte[] hd = GetStream(12);
                string handles = (hd != null && hd.Length >= 12) ? U32(hd, 8).ToString() : "not recorded";
                byte[] um = GetStream(14);
                string unloaded = (um != null && um.Length >= 12) ? U32(um, 8).ToString() : "not recorded";
                sb.AppendLine(string.Format("threads: {0}; modules: {1}; unloaded modules: {2}; handles: {3}; thread names: {4}",
                    threads.Count, modules.Count, unloaded, handles, streams.ContainsKey(24) ? "recorded" : "not recorded"));
                sb.AppendLine("bin dir: " + (binDir ?? "(none)") + (string.IsNullOrEmpty(binNote) ? "" : " (" + binNote + ")"));
                sb.AppendLine("frames: heuristic stack scan from RSP up: values pointing into a module right after a CALL (checked in the module file);");
                sb.AppendLine("        '?' = module file not readable, CALL not checked; stale return addresses left in locals can appear.");
                sb.AppendLine();

                int listed = 0;
                sb.AppendLine("modules (the exe, files of the bin dir, core system DLLs, and every module seen in a frame):");
                sb.AppendLine("  base              size      timestamp name                         file / symbols");
                foreach (Module m in modules)
                {
                    bool inBin = binDir != null && File.Exists(Path.Combine(binDir, m.Name));
                    bool core = Array.IndexOf(new[] { "ntdll", "kernelbase", "kernel32", "user32", "win32u" }, m.Short.ToLowerInvariant()) >= 0;
                    if (!(m.Index == 0 || inBin || core || m.Seen)) continue;
                    listed++;
                    EnsurePe(m);
                    string note = m.FileNote;
                    if (m.Map != null || m.MapNote != null) note += "; " + m.MapNote;
                    else if (m.Pe != null && m.Seen) note += "; " + m.Pe.ExportCount + " exports";
                    sb.AppendLine(string.Format("  {0:X16}  {1:X8}  {2:x8}  {3,-28} {4}", m.Base, m.Size, m.TimeStamp, m.Name, note));
                }
                if (modules.Count > listed) sb.AppendLine(string.Format("  ... and {0} other module(s)", modules.Count - listed));
                sb.AppendLine();

                foreach (ThreadRec t in threads)
                {
                    var head = new StringBuilder();
                    head.AppendFormat("=== thread {0} (#{1}){2}: suspend {3}, priority {4} (class 0x{5:X})", t.Id, t.Index,
                        t.Name != null ? " '" + t.Name + "'" : "", t.SuspendCount, (int)t.Priority, t.PriorityClass);
                    if (t.HasInfo)
                    {
                        head.AppendFormat(", cpu user {0} ms / kernel {1} ms", t.UserTime / 10000, t.KernelTime / 10000);
                        if (t.CreateTime != 0)
                        {
                            try { head.AppendFormat(", created {0:HH:mm:ss.fff}", DateTime.FromFileTime((long)t.CreateTime)); }
                            catch (Exception) { }
                        }
                        if (t.DumpError != 0) head.AppendFormat(", dump error 0x{0:X}", t.DumpError);
                    }
                    sb.AppendLine(head.ToString());
                    if (t.Start != null) sb.AppendLine(string.Format("    start {0:X16}  {1}  {2}", t.Start.Addr, t.Start.Where, t.Start.Sym ?? ""));
                    if (!t.HasCtx) { sb.AppendLine("    no thread context in the dump"); sb.AppendLine(); continue; }
                    sb.AppendLine(string.Format("    rip   {0:X16}  {1}", t.Rip, t.Frames.Count > 0 ? t.Frames[0].Text : ""));
                    sb.AppendLine(string.Format("    rsp   {0:X16}  stack 0x{1:X}-0x{2:X} ({3:N0} bytes captured)", t.Rsp, t.StackStart, t.StackStart + t.StackSize, t.StackSize));
                    for (int i = 0; i < t.Frames.Count; i++) sb.AppendLine(FrameLine(i, t.Frames[i]));
                    if (t.Frames.Count >= maxFrames) sb.AppendLine(string.Format("    (stopped at -MaxFrames {0})", maxFrames));
                    sb.AppendLine();
                }

                sb.AppendLine("=== SUMMARY");
                var susp = threads.FindAll(delegate(ThreadRec t) { return t.SuspendCount > 0; });
                sb.AppendLine(string.Format("suspended threads (SuspendCount > 0): {0}", susp.Count));
                if (susp.Count == 0)
                    sb.AppendLine("  note: the System32 dbghelp/dbgcore writes SuspendCount 0 even for suspended threads (checked 2026-11-21: a thread\n" +
                                  "  suspended twice was recorded as 0), so threads the runtime suspended show up under 'not in a wait' below.");
                foreach (ThreadRec t in susp)
                {
                    Frame app = FirstOutsideSystem(t);
                    sb.AppendLine(string.Format("  {0} x{1}: {2}{3}", Label(t), t.SuspendCount, t.Frames.Count > 0 ? t.Frames[0].Text : "(no context)",
                        app != null && (t.Frames.Count == 0 || app != t.Frames[0]) ? "  <-  " + app.Text : ""));
                }
                var waiting = new List<string>();
                var running = new List<string>();
                foreach (ThreadRec t in threads)
                {
                    if (!t.HasCtx) continue;
                    string w = WaitName(t);
                    Frame app = FirstOutsideSystem(t);
                    if (w != null)
                    {
                        string key = w.StartsWith("Zw", StringComparison.Ordinal) ? "Nt" + w.Substring(2) : w;
                        string hint;
                        WaitHints.TryGetValue(key, out hint);
                        waiting.Add(string.Format("  {0}{1}: {2}{3}  <-  {4}", Label(t), t.SuspendCount > 0 ? " (suspended)" : "", key,
                            hint != null ? " [" + hint + "]" : "", app != null ? app.Text : "(no frame outside ntdll/KernelBase/kernel32/win32u)"));
                    }
                    else
                    {
                        running.Add(string.Format("  {0}{1}: {2}{3}", Label(t), t.SuspendCount > 0 ? " (suspended)" : "", t.Frames[0].Text,
                            app != null && app != t.Frames[0] ? "  <-  " + app.Text : ""));
                    }
                }
                sb.AppendLine(string.Format("waiting threads (RIP in an ntdll/win32u wait; first frame outside ntdll/KernelBase/kernel32/win32u): {0}", waiting.Count));
                foreach (string l in waiting) sb.AppendLine(l);
                sb.AppendLine(string.Format("threads not in a wait (running, spinning, preempted, or an unrecognised wait): {0}", running.Count));
                foreach (string l in running) sb.AppendLine(l);
                ThreadRec ui = null;
                var uiLines = new List<string>();
                foreach (ThreadRec t in threads)
                {
                    bool strong;
                    string ev = UiEvidence(t, out strong);
                    if (ev == null) continue;
                    if (ui == null || (strong && !uiStrong)) { ui = t; uiStrong = strong; }
                    uiLines.Add(string.Format("  {0}: {1}", Label(t), ev));
                }
                if (ui == null) sb.AppendLine("UI thread: not identified (no thread has user32/win32u, SDL or ReXApp frames)");
                else
                {
                    sb.AppendLine(string.Format("UI thread: {0} (most likely; candidates with user32/win32u/SDL/ReXApp frames: {1})", Label(ui), uiLines.Count));
                    foreach (string l in uiLines) sb.AppendLine(l);
                }
            }
            sb.AppendLine(string.Format("analysis: {0:N1} s", sw.Elapsed.TotalSeconds));
            foreach (Module m in modules) if (m.Pe != null) m.Pe.Dispose();
            return sb.ToString();
        }

        bool uiStrong;
    }
}
