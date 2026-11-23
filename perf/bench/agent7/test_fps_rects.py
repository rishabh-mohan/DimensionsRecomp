"""Agent 7, task #20 item (i): the FPS meter's merged clears cover exactly the same pixels.

Extracts the digit-rect block of PresentTexture (from `constexpr u16 digits[]` up to the
`LEGO_NATIVE_FPS_OVERLAY_BATCHED` line) from the new device.cpp and from the batch-1 copy, compiles
both against the real fps_counter.h, and checks, for every reading 0..9999 and 64 target sizes:
  1. LEGO_NATIVE_FPS_CELL_RECTS set: the rect lists equal batch 1's exactly (old path unchanged).
  2. Default: black shadows then white cells rasterize to the same pixels as batch 1's, and every
     rect lies inside the target.
Plus MergeTouchingRects on 200,000 random cell bitmaps (row-major and shuffled order).

Usage: python bench\\agent7\\test_fps_rects.py [--device D] [--batch1 B] [--include I] [--out O]
Needs clang++ on PATH (. env\\devshell.ps1).
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "DimensionsRecomp", "rexlego", "src")


def extract(path, name, cell_rects_expected):
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    start = text.index("    constexpr u16 digits[] = {")
    end = text.index('      static const bool batched = std::getenv("LEGO_NATIVE_FPS_OVERLAY_BATCHED")')
    block = text[start:end]
    subs = [
        ('static const bool no_overlay = std::getenv("LEGO_NATIVE_NO_FPS_OVERLAY") != nullptr;',
         "const bool no_overlay = false;"),
        ("const bool show_fps = settings ? settings->show_fps : REXCVAR_GET(native_show_fps);",
         "const bool show_fps = true;"),
        ("state.fps_counter.Value()", "fps_value"),
    ]
    if cell_rects_expected:
        subs.append(('static const bool cell_rects = std::getenv("LEGO_NATIVE_FPS_CELL_RECTS") != nullptr;',
                     "const bool cell_rects = test_cell_rects;"))
    for old, new in subs:
        if block.count(old) != 1:
            sys.exit("%s: expected 1 match for %r, found %d" % (path, old, block.count(old)))
        block = block.replace(old, new)
    if ("cell_rects" in block) != cell_rects_expected:
        sys.exit("%s: cell_rects presence mismatch" % path)
    return (
        "u32 %s(u32 fps_value, u32 width, u32 height, bool test_cell_rects, plume::RenderRect* out_pixels,\n"
        "       plume::RenderRect* out_shadows) {\n"
        "  (void)test_cell_rects;\n"
        "  u32 result = 0;\n"
        "  {\n%s"
        "      for (u32 i = 0; i < used; ++i) { out_pixels[i] = pixels[i]; out_shadows[i] = shadows[i]; }\n"
        "      result = used;\n"
        "    }\n"
        "  }\n"
        "  return result;\n"
        "}\n" % (name, block)
    )


HARNESS = r"""
#include "gpu_native/fps_counter.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>
namespace plume {
struct RenderRect {
  int32_t left = 0, top = 0, right = 0, bottom = 0;
  RenderRect() = default;
  RenderRect(int32_t l, int32_t t, int32_t r, int32_t b) : left(l), top(t), right(r), bottom(b) {}
};
}  // namespace plume
using u16 = uint16_t;
using u32 = uint32_t;
using i32 = int32_t;
namespace legodimensions::gpu_native {
@NEW@
@OLD@
}  // namespace legodimensions::gpu_native
using namespace legodimensions::gpu_native;
#define CHECK(c) do { if (!(c)) { std::printf("FAIL line %d: %s\n", __LINE__, #c); std::exit(1); } } while (0)

// Paints the target's bottom-left 64x32 window (the meter's area): black shadows, then white cells.
static void Paint(std::vector<uint8_t>& canvas, u32 width, u32 height, const plume::RenderRect* shadows,
                  const plume::RenderRect* pixels, u32 used) {
  const i32 wx = 0, wy = i32(height) - 32;
  std::fill(canvas.begin(), canvas.end(), uint8_t(2));
  for (int pass = 0; pass < 2; ++pass) {
    const plume::RenderRect* rects = pass ? pixels : shadows;
    for (u32 i = 0; i < used; ++i) {
      const auto& r = rects[i];
      CHECK(r.left >= 0 && r.top >= 0 && r.left < r.right && r.top < r.bottom);
      CHECK(r.right <= i32(width) && r.bottom <= i32(height));
      CHECK(r.left >= wx && r.right <= wx + 64 && r.top >= wy && r.bottom <= wy + 32);
      for (i32 y = r.top; y < r.bottom; ++y)
        for (i32 x = r.left; x < r.right; ++x) canvas[size_t(y - wy) * 64 + size_t(x - wx)] = uint8_t(pass);
    }
  }
}

int main() {
  const u32 widths[] = {64, 65, 66, 67, 100, 1280, 1920, 3840};
  const u32 heights[] = {32, 33, 34, 35, 100, 720, 1080, 2160};
  std::array<plume::RenderRect, 60> op, os, np, ns, cp, cs;
  std::vector<uint8_t> a(64 * 32), b(64 * 32);
  unsigned long long cases = 0, old_clears = 0, new_clears = 0, ratio_max_num = 0, ratio_max_den = 1;
  u32 worst_value = 0, min_new = 1000, max_new = 0;
  for (u32 w : widths) for (u32 h : heights) for (u32 value = 0; value <= 10000; ++value) {
    const u32 ou = BuildOld(value, w, h, false, op.data(), os.data());
    const u32 cu = BuildNew(value, w, h, true, cp.data(), cs.data());
    const u32 nu = BuildNew(value, w, h, false, np.data(), ns.data());
    CHECK(cu == ou);
    for (u32 i = 0; i < ou; ++i) {
      CHECK(cp[i].left == op[i].left && cp[i].top == op[i].top && cp[i].right == op[i].right && cp[i].bottom == op[i].bottom);
      CHECK(cs[i].left == os[i].left && cs[i].top == os[i].top && cs[i].right == os[i].right && cs[i].bottom == os[i].bottom);
    }
    CHECK(ou > 0 && nu > 0 && nu <= ou);
    Paint(a, w, h, os.data(), op.data(), ou);
    Paint(b, w, h, ns.data(), np.data(), nu);
    CHECK(a == b);
    ++cases;
    old_clears += 2ull * ou;
    new_clears += 2ull * nu;
    if (static_cast<unsigned long long>(nu) * ratio_max_den > ratio_max_num * ou) { ratio_max_num = nu; ratio_max_den = ou; worst_value = value; }
    min_new = std::min(min_new, nu);
    max_new = std::max(max_new, nu);
  }
  std::printf("digit cases: %llu (readings 0..10000 x %zu sizes), all pixel-identical; cell-rect path identical to batch 1\n",
              cases, std::size(widths) * std::size(heights));
  std::printf("clears per present: batch 1 mean %.1f, merged mean %.1f (%.0f%%); merged rects %u..%u; worst ratio %llu/%llu at %u\n",
              double(old_clears) / cases, double(new_clears) / cases, 100.0 * new_clears / old_clears, min_new, max_new,
              ratio_max_num, ratio_max_den, worst_value);
  for (u32 value : {30u, 60u, 120u, 144u, 165u, 240u, 1000u, 8888u}) {
    const u32 ou = BuildOld(value, 1920, 1080, false, op.data(), os.data());
    const u32 nu = BuildNew(value, 1920, 1080, false, np.data(), ns.data());
    std::printf("  %4u fps: %3u -> %3u clears\n", value, 2 * ou, 2 * nu);
  }

  // Random cell bitmaps: any order, any pattern; the union must not change.
  std::mt19937 rng(20261121);
  for (int trial = 0; trial < 200000; ++trial) {
    const int cols = 1 + int(rng() % 12), rows = 1 + int(rng() % 10), size = 1 + int(rng() % 4);
    const int ox = int(rng() % 5), oy = int(rng() % 5);
    std::vector<plume::RenderRect> cells;
    for (int r = 0; r < rows; ++r) for (int c = 0; c < cols; ++c)
      if (rng() % 3) cells.emplace_back(ox + c * size, oy + r * size, ox + (c + 1) * size, oy + (r + 1) * size);
    if (trial & 1) std::shuffle(cells.begin(), cells.end(), rng);
    std::vector<plume::RenderRect> merged = cells;
    const u32 n = MergeTouchingRects(merged.data(), u32(merged.size()));
    CHECK(n <= cells.size());
    const int W = ox + cols * size, H = oy + rows * size;
    std::vector<uint8_t> u(size_t(W) * H, 0), v(size_t(W) * H, 0);
    for (const auto& r : cells) for (int y = r.top; y < r.bottom; ++y) for (int x = r.left; x < r.right; ++x) u[size_t(y) * W + x] = 1;
    for (u32 i = 0; i < n; ++i) {
      const auto& r = merged[i];
      CHECK(r.left < r.right && r.top < r.bottom);
      for (int y = r.top; y < r.bottom; ++y) for (int x = r.left; x < r.right; ++x) { CHECK(u[size_t(y) * W + x]); v[size_t(y) * W + x] = 1; }
    }
    CHECK(u == v);
  }
  std::printf("random bitmaps: 200000 (half shuffled), unions identical\n");
  std::printf("PASS\n");
  return 0;
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default=os.path.join(SRC, "gpu_native", "device.cpp"))
    ap.add_argument("--batch1", default=os.path.join(ROOT, "build", "agent7", "batch1", "device.cpp"))
    ap.add_argument("--include", default=SRC)
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "agent7", "test-fps-rects"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    code = HARNESS.replace("@NEW@", extract(a.device, "BuildNew", True)).replace(
        "@OLD@", extract(a.batch1, "BuildOld", False))
    cpp = os.path.join(a.out, "fps_rects_test.cpp")
    exe = os.path.join(a.out, "fps_rects_test.exe")
    open(cpp, "w", encoding="utf-8").write(code)
    cmd = ["clang++", "-std=c++20", "-O2", "-UNDEBUG", "-Wall", "-I" + a.include, cpp, "-o", exe]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout + r.stderr)
        sys.exit("compile failed")
    if r.stderr.strip():
        print(r.stderr.strip())
    r = subprocess.run([exe], capture_output=True, text=True)
    print(r.stdout.strip())
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
