// Item 4 (perf-notes/agent4-draw-path.md): the Select_g_* TLS accessors on the per-draw path.
// Old: every use calls CurrentDrawPreparation() (out of line in device.cpp) - 12 calls on an indexed
// draw without preparation. New: BindNativeDrawVertexBuffers, DispatchDraw and BindConstants read it
// once each (3 calls) and pass it to the Select_g_*(preparation) overloads. "inline" is the old
// sequence with an inline accessor (needs device.cpp, Agent 7). Unit test: same objects, same uses.
#include <vector>

#include "bench_common.h"
#include "tls_tu.h"

namespace {

// Stand-ins for QuadIndexCache, VertexBindingCache, ...: non-trivial, so the thread_local copies get a
// TLS init guard as the real ones do.
struct Cache {
  std::vector<int> items;
  uint64_t uses = 0;
};

#define SELECTOR(name)                                                         \
  Cache name##_serial;                                                         \
  Cache& Select_##name(const DrawPreparationContext* preparation) {            \
    if (preparation) {                                                         \
      static thread_local Cache state;                                         \
      return state;                                                            \
    }                                                                          \
    return name##_serial;                                                      \
  }                                                                            \
  template <DrawPreparationContext* (*Get)()>                                  \
  Cache& Select_##name() { return Select_##name(Get()); }
SELECTOR(prepared_draw)
SELECTOR(vertex_bindings)
SELECTOR(vertex_input_usage)
SELECTOR(draw_timing)

template <DrawPreparationContext* (*Get)()>
BENCH_NOINLINE uint64_t OldDraw() {
  uint64_t seen = 0;
  ++Select_draw_timing<Get>().uses;  // DrawTimer: ++g_draw_timing.calls
  bench::ClobberMemory();
  if (Get()) ++seen;  // BindNativeDrawVertexBuffers
  ++Select_vertex_bindings<Get>().uses;
  bench::ClobberMemory();
  for (int i = 0; i < 2; ++i) {  // DispatchDraw: alias_decided twice
    if (auto* prepared = Get(); prepared && prepared->alias_decided) ++seen;
    bench::ClobberMemory();
  }
  auto* commands = Get() ? Get()->commands : BeginFrameCommands();
  bench::DoNotOptimize(commands);
  const auto view = Get() ? Get()->view : CurrentDrawDeviceView();
  bench::DoNotOptimize(view);
  ++Select_prepared_draw<Get>().uses;  // pipeline.Resolve
  bench::ClobberMemory();
  ++Select_prepared_draw<Get>().uses;  // vertex_layout.Resolve
  bench::ClobberMemory();
  ++Select_vertex_input_usage<Get>().uses;
  bench::ClobberMemory();
  if (Get()) ++seen;  // write marking
  bench::ClobberMemory();
  ++Select_prepared_draw<Get>().uses;  // BindConstants: g_prepared_draw.constants (unchanged)
  return seen;
}

BENCH_NOINLINE uint64_t NewDraw() {
  uint64_t seen = 0;
  {
    const DrawPreparationContext* const preparation = CurrentDrawPreparation();
    if (preparation) ++seen;
    ++Select_vertex_bindings(preparation).uses;
    bench::ClobberMemory();
  }
  DrawPreparationContext* const preparation = CurrentDrawPreparation();
  ++Select_draw_timing(preparation).uses;  // DrawTimer timer(preparation)
  bench::ClobberMemory();
  for (int i = 0; i < 2; ++i) {
    if (preparation && preparation->alias_decided) ++seen;
    bench::ClobberMemory();
  }
  auto* commands = preparation ? preparation->commands : BeginFrameCommands();
  bench::DoNotOptimize(commands);
  const auto view = preparation ? preparation->view : CurrentDrawDeviceView();
  bench::DoNotOptimize(view);
  ++Select_prepared_draw(preparation).uses;
  bench::ClobberMemory();
  ++Select_prepared_draw(preparation).uses;
  bench::ClobberMemory();
  ++Select_vertex_input_usage(preparation).uses;
  bench::ClobberMemory();
  if (preparation) ++seen;
  bench::ClobberMemory();
  ++Select_prepared_draw<CurrentDrawPreparation>().uses;  // BindConstants (unchanged)
  return seen;
}

struct Uses {
  uint64_t values[8];
  bool operator==(const Uses&) const = default;
};
Uses Snapshot(DrawPreparationContext* context) {
  return {{prepared_draw_serial.uses, vertex_bindings_serial.uses, vertex_input_usage_serial.uses,
           draw_timing_serial.uses, Select_prepared_draw(context).uses,
           Select_vertex_bindings(context).uses, Select_vertex_input_usage(context).uses,
           Select_draw_timing(context).uses}};
}
void ResetUses(DrawPreparationContext* context) {
  for (Cache* cache : {&prepared_draw_serial, &vertex_bindings_serial, &vertex_input_usage_serial,
                       &draw_timing_serial, &Select_prepared_draw(context),
                       &Select_vertex_bindings(context), &Select_vertex_input_usage(context),
                       &Select_draw_timing(context)})
    cache->uses = 0;
}

void UnitTests() {
  DrawPreparationContext context{true, &context, 7};
  for (DrawPreparationContext* active : {static_cast<DrawPreparationContext*>(nullptr), &context}) {
    SetDrawPreparation(active);
    uint64_t seen[3]{};
    Uses uses[3];
    for (int variant = 0; variant < 3; ++variant) {
      SetDrawPreparation(nullptr);
      ResetUses(&context);
      SetDrawPreparation(active);
      for (int i = 0; i < 1000; ++i)
        seen[variant] += variant == 0 ? OldDraw<CurrentDrawPreparation>()
                         : variant == 1 ? NewDraw()
                                        : OldDraw<CurrentDrawPreparationInline>();
      SetDrawPreparation(nullptr);
      uses[variant] = Snapshot(&context);
    }
    BENCH_CHECK(seen[0] == seen[1] && seen[0] == seen[2]);
    BENCH_CHECK(uses[0] == uses[1] && uses[0] == uses[2]);
    BENCH_CHECK(seen[0] == (active ? 4000u : 0u));
    BENCH_CHECK(uses[0].values[active ? 4 : 0] == 3000);  // prepared_draw: three uses per draw
  }
  SetDrawPreparation(nullptr);
  std::puts("tls_accessor unit tests: OK");
}

DrawPreparationContext g_context{false, &g_context, 7};

template <class F>
double Draws(DrawPreparationContext* active, F draw) {
  constexpr size_t kDraws = 2'000'000;
  SetDrawPreparation(active);
  const double ns = bench::NsPerOp(kDraws, [&] {
    uint64_t seen = 0;
    for (size_t i = 0; i < kDraws; ++i) seen += draw();
    bench::DoNotOptimize(seen);
  });
  SetDrawPreparation(nullptr);
  return ns;
}

}  // namespace

int main() {
  UnitTests();
  bench::RunCases("tls_accessor", {
      {"no preparation: old 12 accessor calls", [] {
         return Draws(nullptr, [] { return OldDraw<CurrentDrawPreparation>(); }); }},
      {"no preparation: new 3 accessor calls", [] { return Draws(nullptr, [] { return NewDraw(); }); }},
      {"no preparation: old sequence, inline accessor", [] {
         return Draws(nullptr, [] { return OldDraw<CurrentDrawPreparationInline>(); }); }},
      {"preparation: old 14 accessor calls", [] {
         return Draws(&g_context, [] { return OldDraw<CurrentDrawPreparation>(); }); }},
      {"preparation: new 3 accessor calls", [] { return Draws(&g_context, [] { return NewDraw(); }); }},
      {"preparation: old sequence, inline accessor", [] {
         return Draws(&g_context, [] { return OldDraw<CurrentDrawPreparationInline>(); }); }},
  });
  return 0;
}
