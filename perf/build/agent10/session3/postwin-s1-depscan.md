# postwin S1: ninja deps scan for the #33 headers (M10, 2026-11-25 06:28)

Context: S1 of postwin-rating.md (3B0C445D8402924D, 9350 B). Read-only. Script:
scratch-r19build/ninja_deps_scan.py (4F3CBDB2). Raw output is in
scratch-r19build/s1-snap1-{sdk,off,on}.out.txt.

## Result: PASS

| .ninja_deps | outputs with deps | d3d12/pipeline_cache.h | graphics/frame_stats.h |
|---|---|---|---|
| build/agent2/snap1-sdk | 759 | 8 (all rexgpu-xenos Release) | 5 (all rexgpu-xenos Release) |
| build/agent2/snap1-off | 478 | 0 (no path ends in pipeline_cache.h) | 0 (no path ends in frame_stats.h) |
| build/agent2/snap1-on | 532 | 0 (no path ends in pipeline_cache.h) | 0 (no path ends in frame_stats.h) |

Union of the snap1-sdk consumers is 10 rexgpu-xenos objects:
- d3d12/: command_processor, deferred_command_list, graphics_system,
  pipeline_cache, primitive_processor, render_target_cache, shared_memory,
  texture_cache;
- graphics/: command_processor, shared_memory.

This is exactly the 10 "ON object" lines in both
build/agent2/devoff4b-s33-bin/MANIFEST.txt and devoff4b-s33d-bin/MANIFEST.txt.
The 2 patched .cpp files (d3d12/command_processor.cpp, d3d12/pipeline_cache.cpp)
are in that set. Each header resolves to one path only (snap1 rexglue-sdk). The
game builds (snap1-off, snap1-on) have no consumers.

Conclusion: the dependency-scoped s33/s33d builds recompiled every TU that
consumes the changed headers. Nothing outside rexgpu-xenos.dll can see the
layout change. S1 is closed.
