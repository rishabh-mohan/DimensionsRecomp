// d3d12_library_probe.cpp -- standalone real-driver probe of ID3D12PipelineLibrary save/load
// behaviour, Serialize concurrency, and parallel PSO creation/loading (Agent 6 helper, perf effort).
// Build: bench/agent6/build_d3d12_probe.ps1
// Run:   build/agent6/d3d12_library_probe.exe [--pilot] [--n N] [--m M] [--k K] [--ops OPS]
//        [--probe SEC] [--reps R] [--debug] [--warp] [--skipopt]
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <d3dcompiler.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#define HX(h) ((unsigned long)(h))
#define CHECK(x) do { HRESULT hr_ = (x); if (FAILED(hr_)) { printf("FAILED hr=0x%08lX at line %d: %s\n", HX(hr_), __LINE__, #x); fflush(stdout); _exit(1); } } while (0)

static double g_qpf;
static double now_ms() { LARGE_INTEGER c; QueryPerformanceCounter(&c); return double(c.QuadPart) * g_qpf; }
static ULONGLONG ft(FILETIME t) { return (ULONGLONG(t.dwHighDateTime) << 32) | t.dwLowDateTime; }
static double cpu_s() { FILETIME a, b, k, u; GetProcessTimes(GetCurrentProcess(), &a, &b, &k, &u); return double(ft(k) + ft(u)) * 1e-7; }
struct SysT { ULONGLONG idle, tot; };
static SysT sys_t() { FILETIME i, k, u; GetSystemTimes(&i, &k, &u); return {ft(i), ft(k) + ft(u)}; }
static double busy_pct(SysT a, SysT b) { double tot = double(b.tot - a.tot); return tot > 0 ? 100.0 * (1.0 - double(b.idle - a.idle) / tot) : 0; }

struct St { double med = 0, mn = 0, mx = 0, p99 = 0; size_t n = 0; };
static St stats(std::vector<double> v) {
  St s; if (v.empty()) return s;
  std::sort(v.begin(), v.end()); s.n = v.size(); s.mn = v.front(); s.mx = v.back();
  s.med = (v.size() & 1) ? v[v.size() / 2] : 0.5 * (v[v.size() / 2 - 1] + v[v.size() / 2]);
  s.p99 = v[std::min(v.size() - 1, size_t(std::ceil(0.99 * double(v.size()))) - 1)];
  return s;
}
static std::string fs(const St& s, int p = 3) { char b[200]; snprintf(b, sizeof b, "med %.*f (min %.*f, max %.*f, n=%zu)", p, s.med, p, s.mn, p, s.mx, s.n); return b; }
static std::string fp(const St& s, int p = 3) { char b[200]; snprintf(b, sizeof b, "med %.*f, p99 %.*f, max %.*f (n=%zu)", p, s.med, p, s.p99, p, s.mx, s.n); return b; }

static std::vector<std::pair<std::string, std::string>> g_rows;
static void row(const char* key, const char* f, ...) {
  char b[700]; va_list ap; va_start(ap, f); vsnprintf(b, sizeof b, f, ap); va_end(ap);
  g_rows.push_back({key, b}); printf("  %-50s %s\n", key, b); fflush(stdout);
}

static ID3D12Device1* g_dev; static ID3D12RootSignature* g_rs; static ID3DBlob* g_vs;
static int g_ops = 200; static bool g_skipopt = false;

static const char* kVS =
    "cbuffer RC : register(b0) { float k; };\n"
    "struct O { float4 p : SV_Position; float2 uv : TEXCOORD0; float4 c : COLOR0; };\n"
    "O main(float3 pos : POSITION, float2 uv : TEXCOORD0, float4 c : COLOR0) { O o; o.p = float4(pos * k, 1); o.uv = uv; o.c = c; return o; }\n";

// Pixel shader: g_ops straight-line ALU statements; `tag` lands in an asfloat() literal so each variant's bytecode differs.
static std::string ps_src(uint32_t tag) {
  std::string s; char b[256];
  snprintf(b, sizeof b, "cbuffer RC : register(b0) { float k; };\n"
           "float4 main(float4 p : SV_Position, float2 uv : TEXCOORD0, float4 c : COLOR0) : SV_Target {\n"
           " float C = asfloat(0x%08Xu);\n float4 a = c * C + uv.xyxy; float4 b = p * k;\n", 0x3F800000u + (tag & 0x7FFFFFu));
  s += b;
  for (int i = 0; i < g_ops; i++) {
    switch (i & 3) {
      case 0: snprintf(b, sizeof b, " a = mad(a, b.yzwx, float4(%d.5, C, %d.25, -C));\n", i % 17, i % 13); break;
      case 1: snprintf(b, sizeof b, " b = sin(a * %d.125 + b.wzyx) * C;\n", 1 + i % 7); break;
      case 2: snprintf(b, sizeof b, " a.xy = a.xy * rsqrt(abs(b.zw) + %d.0) + C;\n", 1 + i % 5); break;
      default: snprintf(b, sizeof b, " b += dot(a, b) * float4(%d.0, C, %d.0, k);\n", i % 11, 1 + i % 3); break;
    }
    s += b;
  }
  s += " return a + b;\n}\n";
  return s;
}

static ID3DBlob* compile(const std::string& src, const char* target) {
  ID3DBlob *code = nullptr, *err = nullptr;
  HRESULT hr = D3DCompile(src.data(), src.size(), "gen.hlsl", nullptr, nullptr, "main", target,
                          g_skipopt ? D3DCOMPILE_SKIP_OPTIMIZATION : 0, 0, &code, &err);
  if (FAILED(hr)) { printf("D3DCompile failed 0x%08lX: %s\n", HX(hr), err ? (const char*)err->GetBufferPointer() : "?"); fflush(stdout); _exit(2); }
  if (err) err->Release();
  return code;
}

static D3D12_INPUT_ELEMENT_DESC g_il[3] = {
    {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    {"TEXCOORD", 0, DXGI_FORMAT_R32G32_FLOAT, 0, 12, D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0},
    {"COLOR", 0, DXGI_FORMAT_R8G8B8A8_UNORM, 0, 20, D3D12_INPUT_CLASSIFICATION_PER_VERTEX_DATA, 0}};

static D3D12_GRAPHICS_PIPELINE_STATE_DESC make_desc(ID3DBlob* ps) {
  D3D12_GRAPHICS_PIPELINE_STATE_DESC d = {};
  d.pRootSignature = g_rs;
  d.VS = {g_vs->GetBufferPointer(), g_vs->GetBufferSize()};
  d.PS = {ps->GetBufferPointer(), ps->GetBufferSize()};
  auto& rt = d.BlendState.RenderTarget[0];
  rt.SrcBlend = rt.SrcBlendAlpha = D3D12_BLEND_ONE; rt.DestBlend = rt.DestBlendAlpha = D3D12_BLEND_ZERO;
  rt.BlendOp = rt.BlendOpAlpha = D3D12_BLEND_OP_ADD; rt.LogicOp = D3D12_LOGIC_OP_NOOP;
  rt.RenderTargetWriteMask = D3D12_COLOR_WRITE_ENABLE_ALL;
  d.SampleMask = UINT_MAX;
  d.RasterizerState.FillMode = D3D12_FILL_MODE_SOLID; d.RasterizerState.CullMode = D3D12_CULL_MODE_BACK;
  d.RasterizerState.DepthClipEnable = TRUE;
  d.DepthStencilState.DepthFunc = D3D12_COMPARISON_FUNC_LESS;
  d.DepthStencilState.FrontFace = {D3D12_STENCIL_OP_KEEP, D3D12_STENCIL_OP_KEEP, D3D12_STENCIL_OP_KEEP, D3D12_COMPARISON_FUNC_ALWAYS};
  d.DepthStencilState.BackFace = d.DepthStencilState.FrontFace;
  d.InputLayout = {g_il, 3};
  d.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
  d.NumRenderTargets = 1; d.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM;
  d.SampleDesc = {1, 0};
  return d;
}

struct Var { ID3DBlob* ps = nullptr; ID3D12PipelineState* pso = nullptr; double t_fxc = 0, t_pso = 0; };

// Runs f(i) for i in [0,n) on `threads` threads pulling indices from an atomic counter; returns wall ms.
template <class F> static double par(int threads, size_t n, F f) {
  std::atomic<size_t> next{0}; double t0 = now_ms(); std::vector<std::thread> th;
  for (int t = 0; t < threads; t++) th.emplace_back([&] { for (size_t i; (i = next.fetch_add(1)) < n;) f(i); });
  for (auto& t : th) t.join();
  return now_ms() - t0;
}
static double build(std::vector<Var>& v, uint32_t tagBase, int threads, bool create) {
  return par(threads, v.size(), [&](size_t i) {
    double t0 = now_ms(); v[i].ps = compile(ps_src(tagBase + uint32_t(i)), "ps_5_0"); double t1 = now_ms(); v[i].t_fxc = t1 - t0;
    if (create) { auto d = make_desc(v[i].ps); CHECK(g_dev->CreateGraphicsPipelineState(&d, IID_PPV_ARGS(&v[i].pso))); v[i].t_pso = now_ms() - t1; }
  });
}
static std::vector<double> col(const std::vector<Var>& v, double Var::*m) { std::vector<double> r; for (auto& x : v) r.push_back(x.*m); return r; }
static std::wstring nm(const wchar_t* p, size_t i) { wchar_t b[64]; swprintf(b, 64, L"%ls%zu", p, i); return b; }
static size_t blob_size(ID3D12PipelineState* p) { ID3DBlob* b = nullptr; CHECK(p->GetCachedBlob(&b)); size_t s = b->GetBufferSize(); b->Release(); return s; }

int main(int argc, char** argv) {
  LARGE_INTEGER qf; QueryPerformanceFrequency(&qf); g_qpf = 1000.0 / double(qf.QuadPart);
  bool pilot = false, debug = false, warp = false; size_t N = 1000, M = 200, K = 300; double probe_s = 2.5; int R = 7;
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i]; auto nx = [&]() -> const char* { return i + 1 < argc ? argv[++i] : "0"; };
    if (a == "--pilot") pilot = true; else if (a == "--debug") debug = true; else if (a == "--warp") warp = true;
    else if (a == "--skipopt") g_skipopt = true;
    else if (a == "--n") N = strtoull(nx(), nullptr, 10); else if (a == "--m") M = strtoull(nx(), nullptr, 10);
    else if (a == "--k") K = strtoull(nx(), nullptr, 10); else if (a == "--ops") g_ops = atoi(nx());
    else if (a == "--probe") probe_s = atof(nx()); else if (a == "--reps") R = atoi(nx());
    else { printf("unknown arg %s\n", a.c_str()); return 1; }
  }
  printf("== d3d12_library_probe ==\ncommand line:"); for (int i = 0; i < argc; i++) printf(" %s", argv[i]); printf("\n");
  {
    RTL_OSVERSIONINFOW vi = {sizeof vi};
    auto fn = (LONG(WINAPI*)(PRTL_OSVERSIONINFOW))(void*)GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "RtlGetVersion");
    if (fn) fn(&vi);
    DWORD ubr = 0, sz = sizeof ubr;
    RegGetValueW(HKEY_LOCAL_MACHINE, L"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", L"UBR", RRF_RT_REG_DWORD, nullptr, &ubr, &sz);
    char cpu[128] = "?"; DWORD cs = sizeof cpu;
    RegGetValueA(HKEY_LOCAL_MACHINE, "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", "ProcessorNameString", RRF_RT_REG_SZ, nullptr, cpu, &cs);
    MEMORYSTATUSEX ms = {sizeof ms}; GlobalMemoryStatusEx(&ms);
    row("OS", "Windows %lu.%lu.%lu.%lu", vi.dwMajorVersion, vi.dwMinorVersion, vi.dwBuildNumber, ubr);
    row("CPU / RAM", "%s, %lu logical processors, %.1f GiB RAM", cpu, GetActiveProcessorCount(ALL_PROCESSOR_GROUPS), double(ms.ullTotalPhys) / 1073741824.0);
  }
  if (debug) {
    ID3D12Debug* dbg = nullptr;
    if (SUCCEEDED(D3D12GetDebugInterface(IID_PPV_ARGS(&dbg)))) { dbg->EnableDebugLayer(); row("debug layer", "ENABLED (timings NOT meaningful)"); }
    else { row("debug layer", "requested but NOT installed"); debug = false; }
  }
  IDXGIFactory4* fac = nullptr; CHECK(CreateDXGIFactory2(0, IID_PPV_ARGS(&fac)));
  IDXGIAdapter1* ad = nullptr; UINT adIdx = 0;
  if (warp) CHECK(fac->EnumWarpAdapter(IID_PPV_ARGS(&ad)));
  else for (; fac->EnumAdapters1(adIdx, &ad) != DXGI_ERROR_NOT_FOUND; adIdx++) {
    DXGI_ADAPTER_DESC1 d; ad->GetDesc1(&d);
    if (!(d.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) && SUCCEEDED(D3D12CreateDevice(ad, D3D_FEATURE_LEVEL_11_0, __uuidof(ID3D12Device), nullptr))) break;
    ad->Release(); ad = nullptr;
  }
  if (!ad) { printf("NO HARDWARE D3D12 ADAPTER - stopping\n"); return 3; }
  {
    DXGI_ADAPTER_DESC1 ah; ad->GetDesc1(&ah); LARGE_INTEGER umd = {}; ad->CheckInterfaceSupport(__uuidof(IDXGIDevice), &umd);
    char an[256]; WideCharToMultiByte(CP_UTF8, 0, ah.Description, -1, an, sizeof an, nullptr, nullptr);
    row("adapter", "#%u %s%s (vendor 0x%04X device 0x%04X, %.1f GiB VRAM)", adIdx, an, warp ? " [WARP SMOKE TEST ONLY]" : "",
        ah.VendorId, ah.DeviceId, double(ah.DedicatedVideoMemory) / 1073741824.0);
    row("UMD driver version", "%u.%u.%u.%u", HIWORD(umd.HighPart), LOWORD(umd.HighPart), HIWORD(umd.LowPart), LOWORD(umd.LowPart));
  }
  CHECK(D3D12CreateDevice(ad, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&g_dev)));
  ID3D12Device1* dev = g_dev;
  D3D12_FEATURE_DATA_SHADER_CACHE scf = {}; dev->CheckFeatureSupport(D3D12_FEATURE_SHADER_CACHE, &scf, sizeof scf);
  row("D3D12_SHADER_CACHE_SUPPORT flags", "0x%X (LIBRARY bit %d)", unsigned(scf.SupportFlags), (scf.SupportFlags & D3D12_SHADER_CACHE_SUPPORT_LIBRARY) ? 1 : 0);
  ID3D12InfoQueue* iq = nullptr; if (debug) dev->QueryInterface(IID_PPV_ARGS(&iq));
  {
    D3D12_ROOT_PARAMETER rp = {}; rp.ParameterType = D3D12_ROOT_PARAMETER_TYPE_32BIT_CONSTANTS; rp.Constants.Num32BitValues = 1;
    rp.ShaderVisibility = D3D12_SHADER_VISIBILITY_ALL;
    D3D12_ROOT_SIGNATURE_DESC rd = {1, &rp, 0, nullptr, D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT};
    ID3DBlob *rb = nullptr, *re = nullptr; CHECK(D3D12SerializeRootSignature(&rd, D3D_ROOT_SIGNATURE_VERSION_1, &rb, &re));
    CHECK(dev->CreateRootSignature(0, rb->GetBufferPointer(), rb->GetBufferSize(), IID_PPV_ARGS(&g_rs)));
  }
  g_vs = compile(kVS, "vs_5_0");
  LARGE_INTEGER qc; QueryPerformanceCounter(&qc);
  const uint32_t seed = uint32_t((ULONGLONG(qc.QuadPart) * 2654435761ull) ^ GetCurrentProcessId()) & 0x7FFFFFu;
  row("HLSL tag seed (fresh per run)", "0x%06X, PS ops %d%s", seed, g_ops, g_skipopt ? " (D3DCOMPILE_SKIP_OPTIMIZATION)" : "");

  // ---- pilot: per-PSO costs and blob sizes, alias/dedupe behaviour of the library ----
  {
    std::vector<Var> pv(4); build(pv, seed + 0x100000, 1, true);
    for (size_t i = 0; i < pv.size(); i++)
      printf("  pilot %zu: fxc %.1f ms, create %.1f ms, DXBC %zu B, cached blob %zu B\n", i, pv[i].t_fxc, pv[i].t_pso, pv[i].ps->GetBufferSize(), blob_size(pv[i].pso));
    ID3D12PipelineLibrary* pl = nullptr; CHECK(dev->CreatePipelineLibrary(nullptr, 0, IID_PPV_ARGS(&pl)));
    size_t s0 = pl->GetSerializedSize(); CHECK(pl->StorePipeline(L"a", pv[0].pso)); size_t s1 = pl->GetSerializedSize();
    HRESULT ha = pl->StorePipeline(L"b", pv[0].pso); size_t s2 = pl->GetSerializedSize();
    CHECK(pl->StorePipeline(L"c", pv[1].pso)); size_t s3 = pl->GetSerializedSize();
    HRESULT hd = pl->StorePipeline(L"c", pv[2].pso);
    row("pilot library size steps", "empty %zu, +pso0 %zu, +pso0 alias (hr 0x%08lX) %zu, +pso1 %zu; duplicate name hr 0x%08lX", s0, s1, HX(ha), s2, s3, HX(hd));
    pl->Release(); for (auto& v : pv) { v.pso->Release(); v.ps->Release(); }
    if (pilot) { row("process CPU time total", "%.2f s", cpu_s()); return 0; }
  }

  // ---- build the library: N distinct PSOs (compile + create on 2 threads), stored serially ----
  std::vector<Var> lv(N);
  double c0 = cpu_s(), wb = build(lv, seed, 2, true), cb = cpu_s() - c0;
  ID3D12PipelineLibrary* lib = nullptr; CHECK(dev->CreatePipelineLibrary(nullptr, 0, IID_PPV_ARGS(&lib)));
  std::vector<double> tst; size_t blobSum = 0;
  for (size_t i = 0; i < N; i++) {
    auto n = nm(L"lib_", i); blobSum += blob_size(lv[i].pso);
    double t0 = now_ms(); CHECK(lib->StorePipeline(n.c_str(), lv[i].pso)); tst.push_back(now_ms() - t0);
    lv[i].pso->Release(); lv[i].pso = nullptr;
  }
  row("library build", "N=%zu distinct PSOs, %.1f s wall on 2 threads, %.1f CPU-s", N, wb / 1000, cb);
  row("per-PSO D3DCompile ms (build)", "%s", fs(stats(col(lv, &Var::t_fxc)), 1).c_str());
  row("per-PSO CreateGraphicsPipelineState ms (build)", "%s", fs(stats(col(lv, &Var::t_pso)), 1).c_str());
  row("StorePipeline ms (serial)", "%s", fp(stats(tst), 4).c_str());
  row("sum of GetCachedBlob sizes", "%.2f MB (%.1f KB/PSO)", blobSum / 1e6, blobSum / 1e3 / double(N));

  // ---- (a) GetSerializedSize ----
  std::vector<double> ta; size_t S = 0;
  for (int r = 0; r < R; r++) { double t0 = now_ms(); S = lib->GetSerializedSize(); ta.push_back(now_ms() - t0); }
  const double MB = S / 1e6; St sa = stats(ta);
  row("S = GetSerializedSize()", "%zu bytes = %.2f MB (%.1f KB/PSO)", S, MB, S / 1e3 / double(N));
  row("(a) GetSerializedSize ms", "%s", fs(sa, 4).c_str());

  // ---- (b) OLD path: fresh vector resize + Serialize; cold new[] Serialize ----
  std::vector<double> tr, tw, tc; std::vector<uint8_t> ref;
  for (int r = 0; r < R; r++) {
    std::vector<uint8_t> v; double t0 = now_ms(); v.resize(S); double t1 = now_ms();
    CHECK(lib->Serialize(v.data(), S)); double t2 = now_ms();
    tr.push_back(t1 - t0); tw.push_back(t2 - t1); if (r == R - 1) ref.swap(v);
  }
  bool identCold = true;
  for (int r = 0; r < R; r++) {
    uint8_t* p = new uint8_t[S]; double t0 = now_ms(); CHECK(lib->Serialize(p, S)); tc.push_back(now_ms() - t0);
    identCold = identCold && memcmp(p, ref.data(), S) == 0; delete[] p;
  }
  St sr = stats(tr), sw = stats(tw), sc = stats(tc);
  row("(b) OLD vector::resize(S) ms", "%s", fs(sr).c_str());
  row("(b) OLD Serialize into warm (resized) buffer ms", "%s = %.0f MB/s", fs(sw).c_str(), MB / (sw.med / 1000));
  row("(b) Serialize into cold new[] buffer ms", "%s = %.0f MB/s", fs(sc).c_str(), MB / (sc.med / 1000));
  row("(b) OLD lock hold = (a)+resize+Serialize, med ms", "%.3f", sa.med + sr.med + sw.med);

  // ---- (c) NEW path: pre-faulted buffer outside the lock; under the lock re-query size + Serialize ----
  const size_t cap = S + S / 16 + 65536; uint8_t* nb = new uint8_t[cap];
  double t0 = now_ms(); for (size_t o = 0; o < cap; o += 4096) nb[o] = 0; const double tpf = now_ms() - t0;
  std::vector<double> tn, tA;
  for (int r = 0; r < R; r++) {
    double a0 = now_ms(); size_t s2 = lib->GetSerializedSize(); double a1 = now_ms(); CHECK(lib->Serialize(nb, s2)); double a2 = now_ms();
    tn.push_back(a2 - a1); tA.push_back(a2 - a0);
  }
  St sn = stats(tn);
  row("(c) pre-fault cap bytes (outside lock) ms", "%.3f (cap %.2f MB, one byte per 4 KiB)", tpf, cap / 1e6);
  row("(c) NEW Serialize into pre-faulted buffer ms", "%s = %.0f MB/s", fs(sn).c_str(), MB / (sn.med / 1000));
  row("(c) NEW lock hold = size re-query + Serialize ms", "%s", fs(stats(tA)).c_str());

  // ---- (d) byte identity, oversize buffer/size, undersize size ----
  auto tail_ok = [&](size_t from) { for (size_t i = from; i < cap; i++) if (nb[i] != 0xCD) return false; return true; };
  memset(nb, 0xCD, cap); HRESULT hrS = lib->Serialize(nb, S);
  bool idS = SUCCEEDED(hrS) && memcmp(nb, ref.data(), S) == 0, tailS = tail_ok(S);
  memset(nb, 0xCD, cap); HRESULT hrB = lib->Serialize(nb, cap);
  bool idB = SUCCEEDED(hrB) && memcmp(nb, ref.data(), S) == 0, tailB = tail_ok(S);
  memset(nb, 0xCD, cap); HRESULT hrM = lib->Serialize(nb, S - 1); bool untM = tail_ok(0);
  HRESULT hrH = lib->Serialize(nb, S / 2); HRESULT hrZ = lib->Serialize(nb, 0);
  row("(d) Serialize(buf>S, size=S) identical to OLD", "%s (hr 0x%08lX), bytes past S untouched: %s", idS ? "YES" : "NO", HX(hrS), tailS ? "yes" : "NO");
  row("(d) Serialize(buf, size=cap>S)", "hr 0x%08lX, first S bytes identical: %s, bytes past S untouched: %s", HX(hrB), idB ? "yes" : "NO", tailB ? "yes" : "NO");
  row("(d) Serialize(size=S-1) / (S/2) / (0)", "hr 0x%08lX / 0x%08lX / 0x%08lX; buffer untouched by S-1 call: %s", HX(hrM), HX(hrH), HX(hrZ), untM ? "yes" : "NO");
  row("(d) cold-buffer outputs identical to OLD", "%s", identCold ? "yes" : "NO");
  lib->Release(); lib = nullptr; delete[] nb; nb = nullptr;

  // ---- (e) reopen from blob + per-PSO LoadGraphicsPipeline ----
  std::vector<double> to; ID3D12PipelineLibrary* lib2 = nullptr;
  for (int r = 0; r < R; r++) {
    ID3D12PipelineLibrary* l = nullptr; double a0 = now_ms(); CHECK(dev->CreatePipelineLibrary(ref.data(), S, IID_PPV_ARGS(&l)));
    to.push_back(now_ms() - a0); if (r < R - 1) l->Release(); else lib2 = l;
  }
  row("(e) CreatePipelineLibrary(blob) ms", "%s", fs(stats(to)).c_str());
  K = std::min(K, N / 4); const size_t ML = std::min(M, (N - K) / 4);
  std::vector<double> tl;
  for (size_t i = 0; i < K; i++) {
    auto n = nm(L"lib_", i); auto d = make_desc(lv[i].ps); ID3D12PipelineState* p = nullptr;
    double a0 = now_ms(); CHECK(lib2->LoadGraphicsPipeline(n.c_str(), &d, IID_PPV_ARGS(&p))); tl.push_back(now_ms() - a0); p->Release();
  }
  row("(e) LoadGraphicsPipeline ms (reopened lib)", "%s", fp(stats(tl), 4).c_str());

  // ---- parallel scaling: CreateGraphicsPipelineState of genuinely new PSOs, 1/2/4 threads ----
  const int TH[3] = {1, 2, 4};
  std::vector<std::vector<Var>> sv(3, std::vector<Var>(M));
  c0 = cpu_s(); double wc = 0;
  for (int t = 0; t < 3; t++) wc += build(sv[t], seed + 0x200000 + uint32_t(t) * 0x10000, 2, false);
  row("scaling setup: fresh HLSL compiles (untimed)", "3 x %zu shaders (fresh seed), %.1f s wall on 2 threads, %.1f CPU-s", M, wc / 1000, cpu_s() - c0);
  double w1 = 0;
  for (int t = 0; t < 3; t++) {
    std::vector<D3D12_GRAPHICS_PIPELINE_STATE_DESC> ds(M); for (size_t i = 0; i < M; i++) ds[i] = make_desc(sv[t][i].ps);
    SysT s0 = sys_t(); double cc = cpu_s();
    double w = par(TH[t], M, [&](size_t i) { CHECK(dev->CreateGraphicsPipelineState(&ds[i], IID_PPV_ARGS(&sv[t][i].pso))); });
    if (t == 0) w1 = w;
    char k[96]; snprintf(k, sizeof k, "create %zu new PSOs, %d thread(s)", M, TH[t]);
    row(k, "%.1f ms wall (%.2f ms/PSO), speedup %.2fx, proc CPU %.1f s, machine busy %.0f%%", w, w / double(M), w1 / w, cpu_s() - cc, busy_pct(s0, sys_t()));
  }
  // ---- parallel scaling: LoadGraphicsPipeline of distinct, never-loaded names, 1/2/4 threads ----
  double l1 = 0;
  for (int t = 0; t < 3; t++) {
    size_t base = K + size_t(t) * ML; std::vector<std::wstring> ns(ML);
    std::vector<D3D12_GRAPHICS_PIPELINE_STATE_DESC> ds(ML); std::vector<ID3D12PipelineState*> out(ML, nullptr);
    for (size_t i = 0; i < ML; i++) { ns[i] = nm(L"lib_", base + i); ds[i] = make_desc(lv[base + i].ps); }
    SysT s0 = sys_t();
    double w = par(TH[t], ML, [&](size_t i) { CHECK(lib2->LoadGraphicsPipeline(ns[i].c_str(), &ds[i], IID_PPV_ARGS(&out[i]))); });
    if (t == 0) l1 = w;
    for (auto p : out) p->Release();
    char k[96]; snprintf(k, sizeof k, "load %zu PSOs from library, %d thread(s)", ML, TH[t]);
    row(k, "%.2f ms wall (%.3f ms/PSO), speedup %.2fx, machine busy %.0f%%", w, w / double(ML), l1 / w, busy_pct(s0, sys_t()));
  }

  // ---- concurrency probe: thread B (main) loads + stores; thread A loops unlocked Serialize ----
  std::vector<ID3D12PipelineState*> fresh; for (auto& v : sv) for (auto& x : v) fresh.push_back(x.pso);
  const size_t lb = K + 3 * ML, lc = N - lb;
  struct Ev { double t0, dt; int kind; };
  size_t jLoad = 0, fsNext = 0; int bFail = 0;
  auto runB = [&](double dur, size_t nStore, std::vector<Ev>& ev) {
    double ts = now_ms(), te = ts + dur, every = dur / double(std::max<size_t>(nStore, 1)), nextStore = ts; size_t stored = 0;
    while (now_ms() < te) {
      size_t idx = lb + (jLoad++ % lc); auto n = nm(L"lib_", idx); auto d = make_desc(lv[idx].ps); ID3D12PipelineState* p = nullptr;
      double a0 = now_ms(); HRESULT hr = lib2->LoadGraphicsPipeline(n.c_str(), &d, IID_PPV_ARGS(&p)); double a1 = now_ms();
      ev.push_back({a0, a1 - a0, 0}); if (FAILED(hr)) bFail++; else p->Release();
      if (stored < nStore && a1 >= nextStore && fsNext < fresh.size()) {
        auto sn = nm(L"fresh_", fsNext); double b0 = now_ms(); hr = lib2->StorePipeline(sn.c_str(), fresh[fsNext]); double b1 = now_ms();
        ev.push_back({b0, b1 - b0, 1}); if (FAILED(hr)) bFail++;
        fsNext++; stored++; nextStore += every;
      }
    }
  };
  using Iv = std::vector<std::pair<double, double>>;
  auto summarize = [&](const char* tag, const std::vector<Ev>& ev, const Iv* iv) {
    std::vector<double> L, Sx, Lov, Sov;
    for (auto& e : ev) {
      bool ov = false;
      if (iv && !iv->empty()) {
        auto it = std::upper_bound(iv->begin(), iv->end(), std::make_pair(e.t0, 1e300));
        if (it != iv->begin()) { --it; ov = e.t0 < it->second; }
      }
      (e.kind ? Sx : L).push_back(e.dt); if (ov) (e.kind ? Sov : Lov).push_back(e.dt);
    }
    char k[120];
    snprintf(k, sizeof k, "probe %s: B LoadGraphicsPipeline ms", tag); row(k, "%s", fp(stats(L), 4).c_str());
    snprintf(k, sizeof k, "probe %s: B StorePipeline ms", tag); row(k, "%s", fp(stats(Sx), 4).c_str());
    if (iv) {
      snprintf(k, sizeof k, "probe %s: B Loads started during a Serialize", tag); row(k, "%s", fp(stats(Lov), 4).c_str());
      snprintf(k, sizeof k, "probe %s: B Stores started during a Serialize", tag); row(k, "%s", fp(stats(Sov), 4).c_str());
    }
    double mx = 0; for (auto x : Lov) mx = std::max(mx, x); for (auto x : Sov) mx = std::max(mx, x);
    return std::make_pair(mx, Lov.size() + Sov.size());
  };
  const size_t half = fresh.size() / 2;
  std::vector<Ev> ev0, ev1;
  runB(probe_s * 1000, half, ev0);
  const size_t capA = S + S / 2 + (size_t(64) << 20); uint8_t* bufA = new uint8_t[capA];
  for (size_t o = 0; o < capA; o += 4096) bufA[o] = 0;
  std::atomic<bool> stopA{false}, startedA{false}; Iv aIv; std::vector<double> aDur; int aFail = 0, aSkip = 0; HRESULT aHr = S_OK;
  std::thread A([&] {
    while (!stopA.load()) {
      size_t sz = lib2->GetSerializedSize();
      if (sz > capA) { aSkip++; startedA = true; Sleep(1); continue; }
      startedA = true; double a0 = now_ms(); HRESULT hr = lib2->Serialize(bufA, sz); double a1 = now_ms();
      aIv.push_back({a0, a1}); aDur.push_back(a1 - a0); if (FAILED(hr)) { aFail++; aHr = hr; }
    }
  });
  while (!startedA.load()) Sleep(0);
  runB(probe_s * 1000, fresh.size() - fsNext, ev1);
  stopA = true; A.join(); delete[] bufA;
  summarize("WITHOUT A", ev0, nullptr);
  St sA = stats(aDur);
  row("probe: A Serialize ms (concurrent with B)", "%s, failures %d (last hr 0x%08lX), oversize skips %d", fp(sA).c_str(), aFail, HX(aHr), aSkip);
  auto ovr = summarize("WITH A", ev1, &aIv);
  row("probe: B call failures (both phases)", "%d", bFail);
  row("probe verdict (heuristic)", "%s: max latency of %zu B calls started inside a Serialize = %.3f ms vs A median Serialize %.3f ms",
      ovr.second == 0 ? "INCONCLUSIVE (no overlap)" : (ovr.first >= 0.5 * sA.med ? "B BLOCKED by Serialize (internal serialization)" : "B NOT blocked by Serialize"),
      ovr.second, ovr.first, sA.med);

  if (iq) {
    UINT64 n = iq->GetNumStoredMessages(); row("debug layer stored messages", "%llu", n);
    for (UINT64 i = 0; i < n && i < 40; i++) {
      SIZE_T len = 0; iq->GetMessage(i, nullptr, &len); auto* m = (D3D12_MESSAGE*)malloc(len);
      if (m && SUCCEEDED(iq->GetMessage(i, m, &len))) printf("    [sev %d id %d] %s\n", int(m->Severity), int(m->ID), m->pDescription);
      free(m);
    }
  }
  row("process CPU time total", "%.1f s", cpu_s());
  printf("\n| metric | value |\n|---|---|\n");
  for (auto& r : g_rows) printf("| %s | %s |\n", r.first.c_str(), r.second.c_str());
  for (auto p : fresh) p->Release();
  lib2->Release();
  return 0;
}
