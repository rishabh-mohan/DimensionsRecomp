// Tests and microbench for the opt-in state-call elision (LEGO_NATIVE_ELIDE_STATE_CALLS=1) and the
// StateCallLedger columns added with it. test_state_shadow.py pastes the actual draw.cpp helpers
// (ReadElideStateCalls .. SameDrawBlendFactor) at the marker below and builds this with
// clang++ -std=c++20 -O2 -march=x86-64-v3. The fakes mirror only the plume fields those helpers read.
//   --unit <dir>        unit tests (shadow, env parse, lookup gates, ledger columns, CSV)
//   --oracle [options]  randomized device/plume event sequences; exit 3 on a wrong binding
//   --bench <label>     microbench, RESULT lines for run_benches-style parsing
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <random>
#include <string>
#include <vector>

#include "bench_common.h"
#include "draw_cached_flag.h"
#include "draw_state_shadow.h"
#include "state_call_diagnostic.h"

struct ID3D12RootSignature { int id = 0; };

namespace plume {
enum class RenderFormat : uint32_t { UNKNOWN = 0, R32_UINT = 42, R16_UINT = 57 };
struct RenderBuffer { virtual ~RenderBuffer() = default; };
struct D3D12Buffer : RenderBuffer { uint64_t gpuVA = 0; };
struct RenderBufferReference { const RenderBuffer* ref = nullptr; uint64_t offset = 0; };
struct RenderIndexBufferView {
  RenderBufferReference buffer;
  uint32_t size = 0;
  RenderFormat format = RenderFormat::UNKNOWN;
};
struct RenderPipelineLayout { virtual ~RenderPipelineLayout() = default; };
struct D3D12PipelineLayout : RenderPipelineLayout { ID3D12RootSignature* rootSignature = nullptr; };
struct RenderCommandList { virtual ~RenderCommandList() = default; };
struct D3D12CommandList : RenderCommandList {
  ID3D12RootSignature* cachedGraphicsRootSignature = nullptr;
  bool cachedGraphicsRootValid = false;
  bool descriptorHeapsSet = false;
};
struct OtherCommandList : RenderCommandList {};  // e.g. PreparedCommandList
}  // namespace plume

namespace legodimensions::gpu_native {
using u32 = uint32_t;
struct DrawPreparationContext { int unused = 0; };
struct DrawDeviceView {
  plume::RenderPipelineLayout* pipeline_layout = nullptr;
  plume::RenderCommandList* commands = nullptr;
  uint64_t recording_serial = 0;
};
bool g_full_preparation = false;
bool NativeFullDrawPreparationEnabled() { return g_full_preparation; }
namespace {
// @@EXTRACTED@@
}  // namespace
}  // namespace legodimensions::gpu_native

namespace {
using namespace legodimensions::gpu_native;
using IB = DrawStateShadow::IndexBuffer;
constexpr auto R16 = plume::RenderFormat::R16_UINT;
constexpr auto R32 = plume::RenderFormat::R32_UINT;

uint64_t g_recording_serial = 0;  // process-wide, as in device.cpp

// D3D12's index buffer and blend factor state for one list, plus the plume flags the shadow reads,
// driven as plume and device.cpp drive them. After a reset the D3D12 state counts as unknown.
struct SimList final : plume::D3D12CommandList {
  bool ib_set = false, blend_set = false;
  IB ib{};
  std::array<float, 4> blend{};
  uint64_t ib_calls = 0, blend_calls = 0;
  void NotifyHeaps() { descriptorHeapsSet = false; }  // notifyDescriptorHeapWasChangedExternally
  void NotifyCommandState() {                          // notifyCommandStateWasChangedExternally
    cachedGraphicsRootSignature = nullptr;
    cachedGraphicsRootValid = false;
  }
  void Notify() {
    NotifyHeaps();
    NotifyCommandState();
  }
  void Reset() {  // end() + begin() in BeginFrameCommandsLocked, then ++g_recording_serial
    Notify();
    ib_set = blend_set = false;
    ++g_recording_serial;
  }
  void BindLayout(const plume::D3D12PipelineLayout& layout) {  // setGraphicsPipelineLayout
    cachedGraphicsRootSignature = layout.rootSignature;
    cachedGraphicsRootValid = true;
  }
  void BindDescriptorSets() { descriptorHeapsSet = true; }  // checkDescriptorHeaps
};

// What plume's setIndexBuffer hands IASetIndexBuffer (plume_d3d12.cpp setIndexBuffer).
IB Bound(const plume::RenderIndexBufferView& view) {
  const auto* buffer = static_cast<const plume::D3D12Buffer*>(view.buffer.ref);
  return {buffer ? buffer->gpuVA + view.buffer.offset : 0, view.size, uint32_t(view.format)};
}
BENCH_NOINLINE void SetIndexBuffer(SimList& list, const plume::RenderIndexBufferView& view) {
  list.ib = Bound(view);
  list.ib_set = true;
  ++list.ib_calls;
}
BENCH_NOINLINE void SetBlendFactor(SimList& list, const std::array<float, 4>& value) {
  list.blend = value;
  list.blend_set = true;
  ++list.blend_calls;
}

struct Sim {
  SimList list;
  ID3D12RootSignature draw_root{1}, helper_root{2};
  plume::D3D12PipelineLayout draw_layout, helper_layout;
  bool check_after_binds = false;  // negative control
  Sim() {
    draw_layout.rootSignature = &draw_root;
    helper_layout.rootSignature = &helper_root;
    list.Reset();
  }
  // DispatchDraw's order: shadow lookup, layout and descriptor binds, blend factor, index buffer.
  // Returns whether the draw sees exactly the requested index buffer and blend factor.
  bool Draw(const plume::RenderIndexBufferView& index, const std::array<float, 4>& blend,
            StateCallLedger* ledger, const DrawPreparationContext* preparation = nullptr) {
    const DrawDeviceView view{&draw_layout, &list, g_recording_serial};
    DrawStateShadow* shadow =
        check_after_binds ? nullptr : InlineDrawStateShadow(preparation, &list, view);
    list.BindLayout(draw_layout);
    list.BindDescriptorSets();
    if (check_after_binds) shadow = InlineDrawStateShadow(preparation, &list, view);
    if (!SameDrawBlendFactor(shadow, ledger, blend)) SetBlendFactor(list, blend);
    if (!SameDrawIndexBuffer(shadow, ledger, index)) SetIndexBuffer(list, index);
    const IB want = Bound(index);
    return list.ib_set && list.ib.address == want.address && list.ib.size == want.size &&
           list.ib.format == want.format && list.blend_set &&
           std::memcmp(list.blend.data(), blend.data(), sizeof(blend)) == 0;
  }
};

void TestShadow() {
  int list_a = 0, list_b = 0, layout_a = 0, layout_b = 0;
  DrawStateShadow s;
  const IB ib{0x1000, 256, 42};
  BENCH_CHECK(s.Begin(&list_a, 1, &layout_a));
  BENCH_CHECK(!s.SameIndexBuffer(ib));  // first request is always emitted
  BENCH_CHECK(s.SameIndexBuffer(ib));
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 256, 42}));  // address
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 128, 42}));  // size
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 128, 57}));  // format
  BENCH_CHECK(s.SameIndexBuffer({0x1004, 128, 57}));
  BENCH_CHECK(!s.Begin(&list_a, 1, &layout_a));  // same key keeps what is bound
  BENCH_CHECK(s.SameIndexBuffer({0x1004, 128, 57}));
  BENCH_CHECK(s.Begin(&list_a, 2, &layout_a));  // same list reopened: serial decides
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 128, 57}));
  BENCH_CHECK(s.Begin(&list_b, 2, &layout_a));
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 128, 57}));
  BENCH_CHECK(s.Begin(&list_b, 2, &layout_b));
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 128, 57}));
  BENCH_CHECK(s.SameIndexBuffer({0x1004, 128, 57}));
  s.Invalidate();
  BENCH_CHECK(!s.SameIndexBuffer({0x1004, 128, 57}));

  const float nan = std::numeric_limits<float>::quiet_NaN();
  float other_nan;
  const uint32_t other_bits = 0x7FC00001u;
  std::memcpy(&other_nan, &other_bits, sizeof(other_nan));
  BENCH_CHECK(!s.SameBlendFactor({1, 1, 1, 1}));
  BENCH_CHECK(s.SameBlendFactor({1, 1, 1, 1}));
  BENCH_CHECK(!s.SameBlendFactor({1, 1, 1, 0.5f}));
  BENCH_CHECK(!s.SameBlendFactor({0.0f, 0, 0, 0}));
  BENCH_CHECK(!s.SameBlendFactor({-0.0f, 0, 0, 0}));  // -0 and +0 are different calls
  BENCH_CHECK(!s.SameBlendFactor({nan, 0, 0, 0}));
  BENCH_CHECK(s.SameBlendFactor({nan, 0, 0, 0}));  // identical bits, NaN or not
  BENCH_CHECK(!s.SameBlendFactor({other_nan, 0, 0, 0}));
  // The two states are tracked independently; Invalidate and a new key drop both.
  BENCH_CHECK(s.SameIndexBuffer({0x1004, 128, 57}));
  s.Invalidate();
  BENCH_CHECK(!s.SameBlendFactor({other_nan, 0, 0, 0}) && !s.SameIndexBuffer({0x1004, 128, 57}));
  BENCH_CHECK(s.Begin(&list_a, 3, &layout_a));
  BENCH_CHECK(!s.SameBlendFactor({other_nan, 0, 0, 0}) && !s.SameIndexBuffer({0x1004, 128, 57}));
}

void TestLookupGates() {
  // Runs with LEGO_NATIVE_ELIDE_STATE_CALLS=1 and full preparation off.
  Sim sim;
  plume::D3D12Buffer buffer;
  buffer.gpuVA = 0x40000;
  const plume::RenderIndexBufferView index{{&buffer, 0}, 512, R16};
  const std::array<float, 4> blend{1, 1, 1, 1};
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 1 && sim.list.blend_calls == 1);
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 1 && sim.list.blend_calls == 1);
  // A preparation context bypasses the shadow (its list records tapes, not the frame list).
  DrawPreparationContext preparation;
  BENCH_CHECK(sim.Draw(index, blend, nullptr, &preparation) && sim.list.ib_calls == 2);
  // A list that is not plume::D3D12CommandList (PreparedCommandList) bypasses it too.
  plume::OtherCommandList other;
  const DrawDeviceView other_view{&sim.draw_layout, &other, g_recording_serial + 1000};
  BENCH_CHECK(InlineDrawStateShadow(nullptr, &other, other_view) == nullptr);
  // Back on the frame list: a new key, so emitted once, then skipped.
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 3 && sim.list.blend_calls == 3);
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 3);
  // Each tripwire alone forces a re-emit: heaps, root validity, another root signature.
  sim.list.descriptorHeapsSet = false;
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 4 && sim.list.blend_calls == 4);
  sim.list.cachedGraphicsRootValid = false;
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 5);
  sim.list.BindLayout(sim.helper_layout);
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 6);
  // Resetting the list bumps the serial.
  sim.list.Reset();
  BENCH_CHECK(sim.Draw(index, blend, nullptr) && sim.list.ib_calls == 7 && sim.list.blend_calls == 7);
  // The diagnostic sees every request and counts the skips.
  StateCallLedger ledger;
  BENCH_CHECK(ledger.BeginDraw(&sim.list, g_recording_serial));
  BENCH_CHECK(sim.Draw(index, blend, &ledger) && sim.list.ib_calls == 7);
  const auto& c = ledger.Counts();
  BENCH_CHECK(c.index_buffers == 1 && c.skipped_index_buffers == 1);
  BENCH_CHECK(c.blend_factors == 1 && c.skipped_blend_factors == 1);
}

void TestEnvParse() {
  const struct { const char* value; bool on; } cases[] = {
      {"1", true}, {"0", false}, {"", false}, {"11", false}, {"1 ", false}, {"true", false}, {" 1", false}};
  for (const auto& c : cases) {
    BENCH_CHECK(_putenv_s("LEGO_NATIVE_ELIDE_STATE_CALLS", c.value) == 0);
    BENCH_CHECK(ReadElideStateCalls() == c.on);
  }
  BENCH_CHECK(_putenv_s("LEGO_NATIVE_ELIDE_STATE_CALLS", "") == 0);  // "" removes the variable
  BENCH_CHECK(!ReadElideStateCalls());
  BENCH_CHECK(_putenv_s("LEGO_NATIVE_ELIDE_STATE_CALLS", "1") == 0);
}

std::vector<std::string> Split(const std::string& line) {
  std::vector<std::string> fields(1);
  for (char c : line) {
    if (c == ',') fields.emplace_back();
    else fields.back() += c;
  }
  return fields;
}

void TestLedger(const std::filesystem::path& directory) {
  StateCallLedger ledger;
  int list = 0, fb_a = 0, fb_b = 0;
  const std::array<float, 6> viewport{0, 0, 1280, 720, 0, 1};
  const std::array<int32_t, 4> scissor{0, 0, 1280, 720};
  auto feed = [&](const void* fb, uint32_t format, const std::array<float, 4>& blend,
                  const std::array<float, 6>& vp, const std::array<int32_t, 4>& sc) {
    ledger.Framebuffer(fb);
    ledger.IndexBuffer(0x10, 64, format);
    ledger.BlendFactor(blend);
    ledger.Viewport(vp);
    ledger.Scissor(sc);
  };
  BENCH_CHECK(ledger.BeginDraw(&list, 1));
  feed(&fb_a, 57, {1, 1, 1, 1}, viewport, scissor);
  BENCH_CHECK(ledger.BeginDraw(&list, 1));
  feed(&fb_a, 57, {1, 1, 1, 1}, viewport, scissor);
  ledger.SkippedIndexBuffer();
  ledger.SkippedBlendFactor();
  auto c = ledger.Counts();
  BENCH_CHECK(c.framebuffers == 2 && c.equal_framebuffers == 1);
  BENCH_CHECK(c.index_buffers == 2 && c.equal_index_buffers == 1 && c.skipped_index_buffers == 1);
  BENCH_CHECK(c.blend_factors == 2 && c.equal_blend_factors == 1 && c.skipped_blend_factors == 1);
  BENCH_CHECK(c.viewports == 2 && c.equal_viewports == 1 && c.scissors == 2 && c.equal_scissors == 1);
  // Changed values are not equal; -0 is not +0.
  BENCH_CHECK(ledger.BeginDraw(&list, 1));
  feed(&fb_b, 42, {-0.0f, 1, 1, 1}, {0, 0, 640, 720, 0, 1}, {0, 0, 640, 720});
  c = ledger.Counts();
  BENCH_CHECK(c.equal_framebuffers == 1 && c.equal_index_buffers == 1 && c.equal_blend_factors == 1 &&
              c.equal_viewports == 1 && c.equal_scissors == 1);
  // A new recording forgets every last request, as it does for layouts and tables.
  BENCH_CHECK(ledger.BeginDraw(&list, 2));
  feed(&fb_b, 42, {-0.0f, 1, 1, 1}, {0, 0, 640, 720, 0, 1}, {0, 0, 640, 720});
  c = ledger.Counts();
  BENCH_CHECK(c.recordings == 2 && c.equal_framebuffers == 1 && c.equal_index_buffers == 1 &&
              c.equal_blend_factors == 1 && c.equal_viewports == 1 && c.equal_scissors == 1);
  BENCH_CHECK(ledger.BeginDraw(&list, 2));
  feed(&fb_b, 42, {-0.0f, 1, 1, 1}, {0, 0, 640, 720, 0, 1}, {0, 0, 640, 720});
  c = ledger.Counts();
  BENCH_CHECK(c.equal_framebuffers == 2 && c.equal_index_buffers == 2 && c.equal_blend_factors == 2 &&
              c.equal_viewports == 2 && c.equal_scissors == 2);

  // CSV: one header and one row per present, with matching field counts and values.
  std::filesystem::create_directories(directory);
  const auto output = directory / "state_calls.csv";
  std::filesystem::remove(output);
  {
    StateCallCapture capture(output, {});
    for (int draw = 0; draw < 3; ++draw) {
      auto* current = capture.BeginDraw(&list, 9);
      BENCH_CHECK(current != nullptr);
      current->Framebuffer(&fb_a);
      current->IndexBuffer(0x10, 64, 57);
      if (draw) current->SkippedIndexBuffer();
      current->BlendFactor({1, 1, 1, 1});
      current->Viewport(viewport);
      current->Scissor(scissor);
    }
    capture.Present(7);
  }
  std::ifstream file(output);
  std::string comment, header, row, extra;
  BENCH_CHECK(std::getline(file, comment) && std::getline(file, header) && std::getline(file, row));
  BENCH_CHECK(!std::getline(file, extra));
  BENCH_CHECK(comment.find("unobserved_helper_compute_ray_or_external") != std::string::npos);
  BENCH_CHECK(comment.find("skipped=elided_by_LEGO_NATIVE_ELIDE_STATE_CALLS") != std::string::npos);
  const auto names = Split(header), values = Split(row);
  BENCH_CHECK(names.size() == 28 && values.size() == names.size());
  auto value = [&](const char* name) {
    for (size_t i = 0; i < names.size(); ++i)
      if (names[i] == name) return std::stoull(values[i]);
    std::fprintf(stderr, "missing column %s\n", name);
    std::exit(1);
  };
  BENCH_CHECK(value("frame") == 7 && value("draws") == 3);
  BENCH_CHECK(value("framebuffer_calls") == 3 && value("framebuffer_equal") == 2);
  BENCH_CHECK(value("index_calls") == 3 && value("index_equal") == 2 && value("index_skipped") == 2);
  BENCH_CHECK(value("blend_calls") == 3 && value("blend_equal") == 2 && value("blend_skipped") == 0);
  BENCH_CHECK(value("viewport_calls") == 3 && value("viewport_equal") == 2);
  BENCH_CHECK(value("scissor_calls") == 3 && value("scissor_equal") == 2);
}

struct OracleOptions {
  bool silent_external = false;        // external write without notify (contract violation)
  bool rebind_after_external = false;  // draw-layout rebind between an external write and a draw
  bool check_after_binds = false;      // shadow looked up after the layout bind
  uint64_t steps = 300000;
  uint32_t seed = 1;
};

int RunOracle(const OracleOptions& options, const char* expect) {
  Sim sim;
  sim.check_after_binds = options.check_after_binds;
  std::mt19937 rng(options.seed);
  auto chance = [&](uint32_t percent) { return rng() % 100 < percent; };
  plume::D3D12Buffer buffers[4];
  buffers[0].gpuVA = 0x10000;
  buffers[1].gpuVA = 0x20000;
  buffers[2].gpuVA = 0x10100;  // aliases buffers[0] + 0x100: an identical D3D12 binding
  buffers[3].gpuVA = 0x90000;  // overlay vertices/indices
  const std::vector<plume::RenderIndexBufferView> indices = {
      {{&buffers[0], 0}, 4096, R16},     {{&buffers[0], 0}, 4096, R32},
      {{&buffers[0], 0x100}, 4096, R16}, {{&buffers[2], 0}, 4096, R16},
      {{&buffers[1], 0}, 2048, R32},     {{&buffers[1], 0}, 4096, R32},
      {{nullptr, 0}, 0, R16}};
  const float nan = std::numeric_limits<float>::quiet_NaN();
  const std::vector<std::array<float, 4>> blends = {
      {1, 1, 1, 1}, {0, 0, 0, 0}, {-0.0f, 0, 0, 0}, {0.5f, 0.5f, 0.5f, 1}, {nan, 0, 0, 0}};
  StateCallLedger ledger;
  uint64_t draws = 0, ledger_ib_skips = 0, ledger_blend_skips = 0;
  size_t last_index = 0, last_blend = 0;
  bool external_pending = false;
  for (uint64_t step = 0; step < options.steps; ++step) {
    const uint32_t event = rng() % 100;
    if (event < 60) {
      if (!chance(70)) last_index = rng() % indices.size();
      if (!chance(70)) last_blend = rng() % blends.size();
      StateCallLedger* current = ledger.BeginDraw(&sim.list, g_recording_serial) ? &ledger : nullptr;
      const uint64_t ib_before = sim.list.ib_calls, blend_before = sim.list.blend_calls;
      if (!sim.Draw(indices[last_index], blends[last_blend], current)) {
        std::printf("ORACLE_MISMATCH step=%llu draw=%llu\n", (unsigned long long)step,
                    (unsigned long long)draws);
        return 3;
      }
      if (current) {
        ledger_ib_skips += sim.list.ib_calls == ib_before;
        ledger_blend_skips += sim.list.blend_calls == blend_before;
      }
      ++draws;
      external_pending = false;
    } else if (event < 63) {
      sim.list.Reset();
      external_pending = false;
    } else if (event < 67) {  // raw writer (the native overlay's IASetIndexBuffer), then notify calls
      sim.list.ib = Bound({{&buffers[3], 0}, 768, R16});
      sim.list.ib_set = true;
      if (chance(50)) {  // a generic external writer may set the blend factor too
        sim.list.blend = {0.25f, 0.25f, 0.25f, 0.25f};
        sim.list.blend_set = true;
      }
      // device.cpp calls both. Plume caches neither state, so a writer that otherwise changed only
      // descriptor heaps, or only PSO/root state, may call just the matching notify.
      if (!options.silent_external) {
        const uint32_t notify = rng() % 3;
        if (notify != 2) sim.list.NotifyHeaps();
        if (notify != 1) sim.list.NotifyCommandState();
      }
      external_pending = true;
    } else if (event < 77) {  // helper with its own root signature (depth conversion, clears)
      sim.list.BindLayout(sim.helper_layout);
      sim.list.BindDescriptorSets();
    } else if (event < 85) {  // plume work rebinding the draw layout, no index/blend writes
      if (external_pending && !options.rebind_after_external) continue;
      sim.list.BindLayout(sim.draw_layout);
      sim.list.BindDescriptorSets();
    } else if (event < 92) {  // raw compute (FSR3) followed by both notify calls
      sim.list.Notify();
    } else {  // external SetDescriptorHeaps followed by notifyDescriptorHeapWasChangedExternally
      sim.list.NotifyHeaps();
    }
  }
  const auto& counts = ledger.Counts();
  const uint64_t ib_skips = draws - sim.list.ib_calls, blend_skips = draws - sim.list.blend_calls;
  std::printf("ORACLE pass draws=%llu ib_calls=%llu blend_calls=%llu ib_skipped=%llu blend_skipped=%llu\n",
              (unsigned long long)draws, (unsigned long long)sim.list.ib_calls,
              (unsigned long long)sim.list.blend_calls, (unsigned long long)ib_skips,
              (unsigned long long)blend_skips);
  BENCH_CHECK(counts.skipped_index_buffers == ledger_ib_skips);
  BENCH_CHECK(counts.skipped_blend_factors == ledger_blend_skips);
  if (!std::strcmp(expect, "elision")) BENCH_CHECK(ib_skips > draws / 10 && blend_skips > draws / 10);
  if (!std::strcmp(expect, "none")) BENCH_CHECK(ib_skips == 0 && blend_skips == 0);
  return 0;
}

// Full preparation replays tapes onto the frame list without passing through the shadow.
int RunFullPreparationOracle(uint64_t steps) {
  Sim sim;
  std::mt19937 rng(7);
  plume::D3D12Buffer buffer;
  buffer.gpuVA = 0x30000;
  const plume::RenderIndexBufferView a{{&buffer, 0}, 1024, R16}, tape{{&buffer, 0x200}, 1024, R16};
  const std::array<float, 4> blend{1, 1, 1, 1}, tape_blend{0, 0, 0, 1};
  for (uint64_t step = 0; step < steps; ++step) {
    if (rng() % 4 == 0) {  // ReplayFullDrawBatch: tape commands on the same raw list
      sim.list.ib = Bound(tape);
      sim.list.ib_set = true;
      sim.list.blend = tape_blend;
      sim.list.blend_set = true;
      continue;
    }
    if (!sim.Draw(a, blend, nullptr)) {
      std::printf("ORACLE_MISMATCH full_preparation step=%llu\n", (unsigned long long)step);
      return 3;
    }
  }
  std::printf("ORACLE pass full_preparation ib_calls=%llu blend_calls=%llu\n",
              (unsigned long long)sim.list.ib_calls, (unsigned long long)sim.list.blend_calls);
  return 0;
}

void Bench(const char* label) {
  Sim sim;
  plume::D3D12Buffer buffer;
  buffer.gpuVA = 0x10000;
  const plume::RenderIndexBufferView a{{&buffer, 0}, 4096, R16}, b{{&buffer, 0x100}, 4096, R16};
  const std::array<float, 4> blend_a{1, 1, 1, 1}, blend_b{0.5f, 0.5f, 0.5f, 1};
  constexpr size_t kOps = size_t(1) << 18;
  // One op = the per-draw work around the two calls: lookup, layout/heap binds, blend, index buffer.
  auto loop = [&](bool gated, bool change) {
    return bench::NsPerOp(kOps, [&] {
      for (size_t i = 0; i < kOps; ++i) {
        const bool second = change && (i & 1);
        const auto& index = second ? b : a;
        const auto& blend = second ? blend_b : blend_a;
        DrawStateShadow* shadow = nullptr;
        if (gated) {
          const DrawDeviceView view{&sim.draw_layout, &sim.list, g_recording_serial};
          shadow = InlineDrawStateShadow(nullptr, &sim.list, view);
        }
        sim.list.BindLayout(sim.draw_layout);
        sim.list.BindDescriptorSets();
        if (!gated || !SameDrawBlendFactor(shadow, nullptr, blend)) SetBlendFactor(sim.list, blend);
        if (!gated || !SameDrawIndexBuffer(shadow, nullptr, index)) SetIndexBuffer(sim.list, index);
        bench::ClobberMemory();
      }
    });
  };
  const std::string group = std::string("state_shadow_") + label;
  bench::RunCases(group.c_str(), {
      {"draw_direct_repeat", [&] { return loop(false, false); }},
      {"draw_gated_repeat", [&] { return loop(true, false); }},
      {"draw_direct_change", [&] { return loop(false, true); }},
      {"draw_gated_change", [&] { return loop(true, true); }},
  });
}

}  // namespace

int main(int argc, char** argv) {
  std::vector<std::string> args(argv + 1, argv + argc);
  auto has = [&](const char* flag) {
    for (const auto& a : args) if (a == flag) return true;
    return false;
  };
  g_full_preparation = has("--full-prep");
  if (has("--unit")) {
    BENCH_CHECK(args.size() >= 2);
    TestShadow();
    TestLookupGates();
    TestLedger(args[1]);
    TestEnvParse();
    std::printf("PASS unit: shadow keys/compares, lookup gates and tripwires, ledger columns, CSV, env parse\n");
    return 0;
  }
  if (has("--oracle")) {
    if (g_full_preparation) return RunFullPreparationOracle(100000);
    OracleOptions options;
    options.silent_external = has("--silent-external");
    options.rebind_after_external = has("--rebind-after-external");
    options.check_after_binds = has("--check-after-binds");
    const char* expect = has("--expect-elision") ? "elision" : has("--expect-none") ? "none" : "";
    int result = 0;
    for (uint32_t seed = 1; seed <= 4 && !result; ++seed) {
      options.seed = seed;
      result = RunOracle(options, expect);
    }
    return result;
  }
  if (has("--bench")) {
    BENCH_CHECK(args.size() >= 2);
    Bench(args[1].c_str());
    return 0;
  }
  std::fprintf(stderr, "usage: --unit <dir> | --oracle [...] | --bench <label>\n");
  return 2;
}
