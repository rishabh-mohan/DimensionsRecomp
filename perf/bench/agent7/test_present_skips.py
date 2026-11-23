"""Agent 7 unit test for the two exact present skips (task #6 edits a and b).

* Extracts the production DisplayGammaIsIdentity from device.cpp and checks it
  against a float32 model of the apply_gamma_table pass (ramp level v read
  from R10G10B10A2_UNORM as v/1023, stored to RGBA8 UNORM as round(f*255)):
  soundness (classified identity => the pass is an exact copy of every
  channel, with at least 0.1 ULP of rounding margin), the title-format linear
  ramps (DecodeDisplayGamma of 16-bit i*257 words, and 10-bit round(i*1023/255))
  are recognised, and non-identity ramps are rejected.
* PresentRectCoversTarget against FitPresentRect over a sweep of source and
  window sizes: the rect stays in bounds and "covers" is exactly "no texel of
  the target lies outside the copy viewport".
No game, GPU or window. Usage: python bench/agent7/test_present_skips.py [--compiler clang++]
"""
import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "DimensionsRecomp" / "rexlego" / "src"
OUT = ROOT / "build" / "agent7" / "unit"


def function(text, signature):
    start = text.index(signature)
    depth = 0
    for i in range(text.index("{", start), len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError(signature)


HARNESS = r'''
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <span>
#include <vector>
#include "gpu_native/display_gamma_lut.h"
#include "gpu_native/present_rect.h"
using namespace legodimensions::gpu_native;
#define CHECK(x) do { if (!(x)) { std::printf("CHECK failed line %d: %s\n", __LINE__, #x); std::exit(1); } } while (0)

@@IDENTITY@@

static uint32_t Store8(float f) {  // RGBA8 UNORM store, round to nearest even
  return uint32_t(std::nearbyint(std::fmin(std::fmax(f, 0.0f), 1.0f) * 255.0f));
}
static bool PassIsExactCopy(const DisplayGammaTable& t, double* worst_ulp = nullptr) {
  double worst = 0;
  bool exact = true;
  for (int i = 0; i < 256; ++i)
    for (int shift : {20, 10, 0}) {
      const uint32_t level = (t.words[i] >> shift) & 0x3FF;
      exact &= Store8(float(level) / 1023.0f) == uint32_t(i);
      worst = std::fmax(worst, std::fabs(255.0 * level / 1023.0 - i));
    }
  if (worst_ulp) *worst_ulp = worst;
  return exact;
}
static uint32_t Pack(uint32_t r, uint32_t g, uint32_t b) { return (r << 20) | (g << 10) | b; }
static DisplayGammaTable Rounded() {
  DisplayGammaTable t;
  for (uint32_t i = 0; i < 256; ++i) {
    const uint32_t v = uint32_t(std::lround(i * 1023.0 / 255.0));
    t.words[i] = Pack(v, v, v);
  }
  return t;
}

int main() {
  // Title format: 3 planes of 256 big-endian 16-bit words, >> 6 to 10 bits.
  std::vector<uint8_t> converted(1536);
  for (uint32_t plane = 0; plane < 3; ++plane)
    for (uint32_t i = 0; i < 256; ++i) {
      const uint32_t word = i * 257;
      converted[plane * 512 + i * 2] = uint8_t(word >> 8);
      converted[plane * 512 + i * 2 + 1] = uint8_t(word);
    }
  DisplayGammaTable decoded;
  CHECK(DecodeDisplayGamma(converted, decoded));
  double worst = 0;
  CHECK(DisplayGammaIsIdentity(decoded) && PassIsExactCopy(decoded, &worst) && worst < 0.25);
  std::printf("decoded 16-bit linear ramp: identity, worst %.4f ULP\n", worst);
  const DisplayGammaTable rounded = Rounded();
  CHECK(DisplayGammaIsIdentity(rounded) && PassIsExactCopy(rounded, &worst) && worst <= 0.5);
  std::printf("10-bit rounded linear ramp: identity, worst %.4f ULP\n", worst);

  DisplayGammaTable zero{}, gamma22, swapped = rounded;
  CHECK(!DisplayGammaIsIdentity(zero));
  for (uint32_t i = 0; i < 256; ++i) {
    const uint32_t v = uint32_t(std::lround(std::pow(i / 255.0, 1 / 2.2) * 1023.0));
    gamma22.words[i] = Pack(v, v, v);
  }
  CHECK(!DisplayGammaIsIdentity(gamma22) && !PassIsExactCopy(gamma22));
  std::swap(swapped.words[10], swapped.words[11]);  // one swapped pair of entries
  CHECK(!DisplayGammaIsIdentity(swapped));
  DisplayGammaTable inverted = rounded;  // channel identity broken in blue only
  for (uint32_t i = 0; i < 256; ++i) inverted.words[i] = (inverted.words[i] & ~0x3FFu) | (1023 - (inverted.words[i] & 0x3FF));
  CHECK(!DisplayGammaIsIdentity(inverted));

  // Soundness: every single-entry, single-channel perturbation of +-1..8 levels.
  uint32_t accepted = 0, exact = 0, total = 0;
  for (uint32_t i = 0; i < 256; ++i)
    for (int shift : {20, 10, 0})
      for (int delta = -8; delta <= 8; ++delta) {
        if (!delta) continue;
        DisplayGammaTable t = rounded;
        const int level = int((t.words[i] >> shift) & 0x3FF) + delta;
        if (level < 0 || level > 1023) continue;
        t.words[i] = (t.words[i] & ~(0x3FFu << shift)) | (uint32_t(level) << shift);
        ++total;
        const bool copy = PassIsExactCopy(t, &worst);
        exact += copy;
        if (DisplayGammaIsIdentity(t)) {
          ++accepted;
          CHECK(copy && worst < 0.4);
        }
      }
  std::printf("perturbations: %u total, %u exact copies, %u classified identity (all exact, margin >= 0.1 ULP)\n",
              total, exact, accepted);

  // Random tables near identity: classifier => exact copy with margin.
  std::mt19937 rng(7);
  std::uniform_int_distribution<int> noise(-3, 3);
  uint32_t fuzz_accepted = 0;
  for (int round = 0; round < 20000; ++round) {
    DisplayGammaTable t;
    for (uint32_t i = 0; i < 256; ++i) {
      uint32_t channel[3];
      for (uint32_t& c : channel) {
        const int v = int(std::lround(i * 1023.0 / 255.0)) + (rng() % 4 ? 0 : noise(rng));
        c = uint32_t(std::clamp(v, 0, 1023));
      }
      t.words[i] = Pack(channel[0], channel[1], channel[2]);
    }
    if (DisplayGammaIsIdentity(t)) {
      ++fuzz_accepted;
      CHECK(PassIsExactCopy(t, &worst) && worst < 0.4);
    }
  }
  std::printf("fuzz: %u of 20000 near-identity tables classified identity, all exact\n", fuzz_accepted);

  // Clear skip: FitPresentRect stays in bounds; covers <=> no uncovered texel.
  static_assert(PresentRectCoversTarget(FitPresentRect(1280, 720, 1920, 1080), 1920, 1080));
  static_assert(PresentRectCoversTarget(FitPresentRect(1280, 720, 3840, 2160), 3840, 2160));
  static_assert(!PresentRectCoversTarget(FitPresentRect(1280, 720, 1920, 1200), 1920, 1200));
  static_assert(!PresentRectCoversTarget(FitPresentRect(1280, 720, 1281, 720), 1281, 720));
  static_assert(PresentRectCoversTarget(FitPresentRect(0, 720, 800, 600), 800, 600));
  const uint32_t sources[][2] = {{1280, 720}, {1920, 1080}, {1024, 768}, {640, 480}, {3840, 2160}, {1, 1}, {1366, 768}};
  uint64_t rects = 0, covering = 0;
  for (const auto& source : sources)
    for (uint32_t w = 1; w <= 4000; w += 7)
      for (uint32_t h = 1; h <= 2400; h += 3) {
        const PresentRect r = FitPresentRect(source[0], source[1], w, h);
        CHECK(r.width >= 1 && r.height >= 1 && r.x + r.width <= w && r.y + r.height <= h);
        const bool covers = PresentRectCoversTarget(r, w, h);
        CHECK(covers == (uint64_t(r.width) * r.height == uint64_t(w) * h));
        ++rects;
        covering += covers;
      }
  std::printf("present rects: %llu checked, %llu cover the target\n",
              (unsigned long long)rects, (unsigned long long)covering);
  std::printf("PASS present skips: identity ramp classifier is sound; clear skip only on full coverage\n");
  return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="clang++")
    args = parser.parse_args()
    device = (SRC / "gpu_native" / "device.cpp").read_text()
    identity = function(device, "bool DisplayGammaIsIdentity(const DisplayGammaTable& table)")
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / "present_skips.cpp"
    source.write_text(HARNESS.replace("@@IDENTITY@@", identity))
    exe = OUT / "present_skips.exe"
    subprocess.run([args.compiler, "-std=c++20", "-O1", "-UNDEBUG", f"-I{SRC}", str(source), "-o", str(exe)],
                   check=True, timeout=120)
    subprocess.run([str(exe)], check=True, timeout=120)


if __name__ == "__main__":
    main()
