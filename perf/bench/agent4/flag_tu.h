// Item 6 benches: the out-of-line flag functions that do not change, verbatim from textures.cpp:1478
// and hooks_portrait.cpp:57, plus the composite per-draw entry points. Each function body lives in its
// own TU (flag_tu.cpp, old_composite.cpp, new_composite.cpp), as in the game, so calls stay calls.
#pragma once
#include <cstddef>
#include <cstdint>

namespace shipped {
bool NativeTextureTimingEnabled();  // textures.cpp:1478 (unchanged, out of line)
bool PortraitProbeEnabled();        // hooks_portrait.cpp:57 (unchanged, out of line)
}  // namespace shipped

// old_composite.cpp: the checks as baseline draw.cpp / long_probe.h make them.
uint64_t OldPerDraw(size_t draws);
uint64_t OldTimingChecks(size_t checks);
uint64_t OldLongProbeChecks(size_t checks);
bool OldLongProbeValue();

// new_composite.cpp: the same checks through draw_cached_flag.h and the dev long_probe.h.
uint64_t NewPerDraw(size_t draws);
uint64_t NewTimingChecks(size_t checks);
uint64_t NewLongProbeChecks(size_t checks);
bool NewTimingValue();
bool NewPortraitValue();
bool NewLongProbeValue();
bool LongProbeEnabledForPortrait();
