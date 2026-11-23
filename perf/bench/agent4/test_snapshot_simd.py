"""SnapshotDevice / SnapshotDrawDevice: the SSE2 fallback (x86-64-v2) against the AVX2 path (x86-64-v3).

Extracts the real code from draw.cpp (kSnapshotBytes .. SnapshotStateDevice) and compiles it with a
D3DDevice of the real size and vertex_shader offset (gpu_native/d3d.h), at -march=x86-64-v3 and at
-march=x86-64-v2. Each build runs a deterministic scenario (edge bytes of every 16/32/64-byte lane,
both vertex-constant bounds, the snapshot end, then a 4000-step random walk), checked step by step
against a scalar memcmp model, with delta snapshots on and off. Both builds must pass and print the
same trace. The v3 code generation must equal the baseline tree's byte for byte (AVX2 path
unchanged); the baseline is also tried at v2, where it is expected not to build.
Usage (devshell): python bench/agent4/test_snapshot_simd.py [--tree T] [--baseline B] [--out O] [--bench]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BEGIN = 'constexpr size_t kSnapshotBytes ='
END = '\nbool OverlapDrawBatches() {'

PREFIX = r'''
#include <immintrin.h>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
#include <new>
#include <type_traits>
#include <vector>

using u8 = std::uint8_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
struct be_u32 { u32 raw; };
// The real guest device's size and vertex_shader offset (gpu_native/d3d.h static_asserts).
struct D3DDevice { u8 head[0x3310]; be_u32 vertex_shader; u8 tail[0x6080 - 0x3314]; };
static_assert(sizeof(D3DDevice) == 0x6080 && offsetof(D3DDevice, vertex_shader) == 0x3310);
enum RendererOptimization : unsigned { kDeviceSnapshotPool = 1 };
inline bool RendererOptimizationEnabled(RendererOptimization) { return false; }
template <class Device, size_t Bytes>
struct DeviceSnapshotPool { std::shared_ptr<Device> Capture(const Device*) { std::abort(); } };

// ---- draw.cpp ----
'''

MAIN = r'''
// ---- end draw.cpp ----
#include <chrono>
#include "bench_common.h"

namespace {
alignas(64) D3DDevice g_device;
u8 g_model_kept[kSnapshotBytes];
u64 g_model_sequence = 0;
bool g_model_full = false;
u64 g_trace = 1469598103934665603ull;
int g_failures = 0;
u64 g_rng = 0x9E3779B97F4A7C15ull;

u64 Next() { g_rng ^= g_rng << 13; g_rng ^= g_rng >> 7; g_rng ^= g_rng << 17; return g_rng; }
u8* Bytes() { return reinterpret_cast<u8*>(&g_device); }
u64 Fnv(const u8* bytes, size_t size, u64 hash) {
  for (size_t i = 0; i < size; ++i) { hash ^= bytes[i]; hash *= 1099511628211ull; }
  return hash;
}
#define EXPECT(cond)                                                                   \
  do {                                                                                 \
    if (!(cond)) {                                                                     \
      std::printf("FAIL line %d: %s (step %s)\n", __LINE__, #cond, name);              \
      ++g_failures;                                                                    \
    }                                                                                  \
  } while (0)

// One SnapshotDrawDevice call checked against the scalar model of `kept` / `kept_sequence`.
void Step(const char* name, bool print = true) {
  const u8* source = Bytes();
  const bool expect_same = g_model_sequence != 0 &&
      std::memcmp(source + kVertexConstantsEnd, g_model_kept + kVertexConstantsEnd,
                  kSnapshotBytes - kVertexConstantsEnd) == 0 &&
      std::memcmp(source, g_model_kept, kVertexConstantsBegin) == 0;
  const bool expect_delta = expect_same && g_model_full && DeltaSnapshotsEnabled();
  DrawSnapshot snapshot = SnapshotDrawDevice(&g_device);
  const u8* own = reinterpret_cast<const u8*>(snapshot.device.get());
  const u8* state = reinterpret_cast<const u8*>(SnapshotStateDevice(snapshot));
  const bool delta = BlockOf(snapshot.device.get()).base != nullptr;
  EXPECT(snapshot.sequence == g_model_sequence + 1);
  EXPECT(snapshot.same_as == (expect_same ? g_model_sequence : 0));
  EXPECT(delta == expect_delta);
  EXPECT(std::memcmp(own + kVertexConstantsBegin, source + kVertexConstantsBegin,
                     kVertexConstantsEnd - kVertexConstantsBegin) == 0);
  EXPECT(std::memcmp(state, source, kVertexConstantsBegin) == 0);
  EXPECT(std::memcmp(state + kVertexConstantsEnd, source + kVertexConstantsEnd,
                     kSnapshotBytes - kVertexConstantsEnd) == 0);
  if (!delta) {
    EXPECT(std::memcmp(own, source, kSnapshotBytes) == 0);
    std::memcpy(g_model_kept, source, kVertexConstantsBegin);
    std::memcpy(g_model_kept + kVertexConstantsEnd, source + kVertexConstantsEnd,
                kSnapshotBytes - kVertexConstantsEnd);
    g_model_full = true;
  }
  g_model_sequence = snapshot.sequence;
  g_trace = Fnv(own + kVertexConstantsBegin, kVertexConstantsEnd - kVertexConstantsBegin, g_trace);
  g_trace = Fnv(state, kVertexConstantsBegin, g_trace);
  g_trace = Fnv(state + kVertexConstantsEnd, kSnapshotBytes - kVertexConstantsEnd, g_trace);
  g_trace = g_trace * 31 + snapshot.same_as * 2 + (delta ? 1 : 0);
  if (print)
    std::printf("%-26s seq=%llu same_as=%llu delta=%d\n", name, (unsigned long long)snapshot.sequence,
                (unsigned long long)snapshot.same_as, delta ? 1 : 0);
}

void Bench() {
  constexpr size_t kCalls = 20000;
  bench::RunCases(
#if defined(__AVX2__)
      "snapshot AVX2",
#else
      "snapshot SSE2",
#endif
      {
          {"SnapshotDrawDevice repeat (delta)", [] {
             return bench::NsPerOp(kCalls, [] {
               for (size_t i = 0; i < kCalls; ++i) bench::DoNotOptimize(SnapshotDrawDevice(&g_device).sequence);
             }); }},
          {"SnapshotDrawDevice changed (full)", [] {
             return bench::NsPerOp(kCalls, [] {
               for (size_t i = 0; i < kCalls; ++i) {
                 Bytes()[0] ^= 1;
                 bench::DoNotOptimize(SnapshotDrawDevice(&g_device).sequence);
               }
             }); }},
          {"SnapshotDevice", [] {
             return bench::NsPerOp(kCalls, [] {
               for (size_t i = 0; i < kCalls; ++i) bench::DoNotOptimize(SnapshotDevice(&g_device).get());
             }); }},
      });
}
}  // namespace

int main(int argc, char** argv) {
  std::printf("path=%s\n",
#if defined(__AVX2__)
              "AVX2"
#else
              "SSE2"
#endif
  );
  std::printf("kSnapshotBytes=0x%zx delta_snapshots=%d\n", kSnapshotBytes, DeltaSnapshotsEnabled() ? 1 : 0);
  for (size_t i = 0; i < sizeof(D3DDevice); ++i) Bytes()[i] = u8(Next());
  Step("first snapshot");
  Step("unchanged");
  Bytes()[kVertexConstantsBegin] ^= 1;
  Step("constant at begin");
  Bytes()[kVertexConstantsEnd - 1] ^= 0x80;
  Step("constant at end-1");
  for (size_t i = kVertexConstantsBegin; i < kVertexConstantsEnd; ++i) Bytes()[i] = u8(Next());
  Step("all constants");
  const size_t edges[] = {0, 15, 16, 31, 32, 47, 48, 63, 64, 0x3FF, 0x400,
                          kVertexConstantsBegin - 64, kVertexConstantsBegin - 1, kVertexConstantsEnd,
                          kVertexConstantsEnd + 15, kVertexConstantsEnd + 31, kVertexConstantsEnd + 63,
                          kSnapshotBytes - 64, kSnapshotBytes - 33, kSnapshotBytes - 32,
                          kSnapshotBytes - 17, kSnapshotBytes - 16, kSnapshotBytes - 1,
                          offsetof(D3DDevice, vertex_shader)};
  for (size_t offset : edges) {
    char name[48];
    std::snprintf(name, sizeof(name), "byte 0x%zx", offset);
    Bytes()[offset] ^= 0x10;
    Step(name);
    Step("unchanged");
  }
  Bytes()[kSnapshotBytes] ^= 0xFF;
  Step("byte past kSnapshotBytes");
  for (int i = 0; i < 4000; ++i) {
    const u64 r = Next();
    const u8 flip = u8(1 + (r >> 40) % 255);
    switch (r % 4) {
      case 0: break;
      case 1: Bytes()[kVertexConstantsBegin + (r >> 8) % (kVertexConstantsEnd - kVertexConstantsBegin)] ^= flip; break;
      case 2: Bytes()[(r >> 8) % kSnapshotBytes] ^= flip; break;
      case 3: Bytes()[(r >> 8) % sizeof(D3DDevice)] ^= flip; break;
    }
    Step("random", false);
  }
  for (int i = 0; i < 16; ++i) {
    const char* name = "SnapshotDevice";
    Bytes()[(Next() >> 8) % kSnapshotBytes] ^= 0x5A;
    const auto copy = SnapshotDevice(&g_device);
    EXPECT(std::memcmp(copy.get(), &g_device, kSnapshotBytes) == 0);
    g_trace = Fnv(reinterpret_cast<const u8*>(copy.get()), kSnapshotBytes, g_trace);
  }
  std::printf("trace=%016llx failures=%d\n", (unsigned long long)g_trace, g_failures);
  if (argc > 1 && std::strcmp(argv[1], "--bench") == 0) Bench();
  return g_failures ? 1 : 0;
}
'''

SNAPSHOT_VARS = ['LEGO_NATIVE_DRAW_MERGE', 'LEGO_NATIVE_DELTA_SNAPSHOTS', 'LEGO_NATIVE_DEVICE_SNAPSHOT_POOL']


def extract(tree: Path) -> str:
    text = (tree / 'rexlego/src/gpu_native/draw.cpp').read_text(encoding='utf-8')
    begin = text.index(BEGIN)
    return text[begin:text.index(END, begin)]


def compile_cpp(source: Path, output: Path, march: str, extra=()) -> subprocess.CompletedProcess:
    cmd = ['clang++', '-std=c++20', '-O2', f'-march={march}', '-D_CRT_SECURE_NO_WARNINGS',
           f'-I{HERE}', *extra, str(source), '-o', str(output)]
    return subprocess.run(cmd, capture_output=True, text=True)


def asm_lines(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines()
            if not re.match(r'\s*\.(file|ident)\b', line)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree', default=str(ROOT / 'DimensionsRecomp'))
    parser.add_argument('--baseline', default=str(ROOT / 'baseline/DimensionsRecomp'))
    parser.add_argument('--out', default=str(ROOT / 'build/agent4/snapshot-simd'))
    parser.add_argument('--bench', action='store_true')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    trees = {'dev': Path(args.tree).resolve(), 'base': Path(args.baseline).resolve()}
    sources = {key: extract(tree) for key, tree in trees.items()}
    env = {k: v for k, v in os.environ.items() if k not in SNAPSHOT_VARS}
    failures = []

    # Scenario at v3 and v2, delta snapshots on (default) and off.
    traces = {}
    for march in ('x86-64-v3', 'x86-64-v2'):
        work = out / 'dev' / march
        work.mkdir(parents=True, exist_ok=True)
        source = work / 'snapshot.cpp'
        source.write_text(PREFIX + sources['dev'] + MAIN)
        exe = work / 'snapshot.exe'
        built = compile_cpp(source, exe, march)
        if built.returncode:
            print(built.stdout, built.stderr)
            return f'dev build failed at {march}'
        for deltas in ('on', 'off'):
            run_env = dict(env, LEGO_NATIVE_DELTA_SNAPSHOTS='0') if deltas == 'off' else env
            r = subprocess.run([str(exe)] + (['--bench'] if args.bench and deltas == 'on' else []),
                               env=run_env, capture_output=True, text=True)
            (work / f'run-deltas-{deltas}.log').write_text(r.stdout + r.stderr)
            lines = r.stdout.splitlines()
            path = lines[0] if lines else ''
            expected_path = 'path=AVX2' if march == 'x86-64-v3' else 'path=SSE2'
            body = [line for line in lines[1:] if not line.startswith('RESULT')]
            traces[(march, deltas)] = body
            summary = next((line for line in body if line.startswith('trace=')), 'no trace')
            print(f'{march} deltas {deltas}: {path} {summary} rc={r.returncode}')
            for line in lines:
                if line.startswith('RESULT'):
                    print('  ' + line)
            if r.returncode or path != expected_path:
                failures.append(f'{march} deltas {deltas}: rc={r.returncode} {path}')
    for deltas in ('on', 'off'):
        if traces[('x86-64-v3', deltas)] != traces[('x86-64-v2', deltas)]:
            failures.append(f'v2 and v3 traces differ (deltas {deltas})')
        else:
            print(f'v2 == v3 trace, deltas {deltas}: {len(traces[("x86-64-v3", deltas)])} lines identical')

    # Code generation at v3: baseline vs dev, byte for byte (no main; external-linkage functions).
    asm = {}
    for key, text in sources.items():
        work = out / 'codegen' / key
        work.mkdir(parents=True, exist_ok=True)
        source = work / 'snapshot.cpp'
        source.write_text(PREFIX + text + '\n')
        result = compile_cpp(source, work / 'snapshot.s', 'x86-64-v3', ['-S'])
        if result.returncode:
            print(result.stdout, result.stderr)
            return f'{key} codegen failed'
        asm[key] = asm_lines(work / 'snapshot.s')
    if asm['dev'] == asm['base']:
        print(f'v3 code generation identical to baseline: {len(asm["dev"])} asm lines')
    else:
        failures.append('v3 code generation differs from baseline')

    # The baseline at v2 (informational: the AVX2 intrinsics need the target feature).
    work = out / 'codegen' / 'base-v2'
    work.mkdir(parents=True, exist_ok=True)
    source = work / 'snapshot.cpp'
    source.write_text(PREFIX + sources['base'] + '\n')
    result = compile_cpp(source, work / 'snapshot.o', 'x86-64-v2', ['-c'])
    first_error = next((line for line in result.stderr.splitlines() if 'error' in line), '')
    print(f'baseline at x86-64-v2: {"builds" if result.returncode == 0 else "does not build"}'
          + (f' ({first_error.strip()[:160]})' if first_error else ''))

    if failures:
        print('FAILED: ' + '; '.join(failures))
        return 1
    print('test_snapshot_simd: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
