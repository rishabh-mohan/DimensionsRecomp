# Checkpoint export by Agent 1 (2026-11-22 01:27:52)

Live tree = S2 + #27 (Agent 11 exit fix: xam_ui.cpp, xboxkrnl_hal.cpp) + Agent 9's 20 codegen source files (all options default OFF).
Verified by Agent 2's live-vs-S2 check at 01:22 (snap1/PLAN-CHK-0122.txt).
Nothing in either repo was changed by this export.

HEADs (branch perf/opt):
- game  (DimensionsRecomp)        127e04b2e0d5535f5839ff33ee37d3c6c2ee6f58   diff:  34 files changed, 1779 insertions(+), 297 deletions(-)
- sdk   (DimensionsRecomp/rexglue-sdk) 2897c31b1407dd96480dc25965f8ee7807f00e0f   diff:  43 files changed, 2885 insertions(+), 344 deletions(-)
- plume (thirdparty/plume)        e0c8871b930dc1a6544bf457f2348c456b9d7e13 (prepare_plume.py pin; the superproject records ceaeeee, which is not fetchable; NOT part of our work)

Files:
- game.diff          tracked changes in the game repo (submodule pointers excluded)
- sdk.diff           tracked changes in the SDK
- plume-dirty.diff   the 3 dirty plume files (prepare_plume output + S1 p2 cast), for reference only
- untracked-game/, untracked-sdk/   copies of new untracked files (no __pycache__), same relative paths
- SHA256SUMS.txt

Restore onto a clean checkout of the HEADs above:
  git -C DimensionsRecomp apply --binary <dir>\game.diff
  git -C DimensionsRecomp\rexglue-sdk apply --binary <dir>\sdk.diff
  then copy untracked-game\* into DimensionsRecomp\ and untracked-sdk\* into DimensionsRecomp\rexglue-sdk\
  (plume: run tools/gpu-aot/prepare_plume.py as usual)

Untracked files copied (24):
game/rexlego/src/gpu_native/draw_cached_flag.h
game/rexlego/src/gpu_native/draw_log_throttle.h
game/rexlego/src/gpu_native/draw_state_shadow.h
game/rexlego/src/gpu_native/pipeline_async.h
game/rexlego/src/gpu_native/pipeline_parallel.h
game/rexlego/src/gpu_native/pipeline_snapshot.h
game/rexlego/src/gpu_native/pipeline_stats.h
game/rexlego/src/gpu_native/texture_scratch.h
game/rexlego/src/gpu_native/upload_legacy_paths.h
game/tools/gpu-aot/patches/plume-winsdk-compat.patch
game/tools/native-cpu/README.md
game/tools/native-cpu/analyze_profile.py
game/tools/native-cpu/run_selftest.ps1
game/tools/native-cpu/selftest/map_hooks.py
game/tools/native-cpu/selftest/profiler_selftest.cpp
sdk/include/rex/threading_suspend.h
sdk/include/rex/threading_timeout.h
sdk/include/rex/threading_timing.h
sdk/src/codegen/builders/flush_mode.h
sdk/src/codegen/builders/rotate_mask.h
sdk/tests/ppc/asm/instr_cr_so_fold.s
sdk/tests/ppc/asm/instr_rlw_lowering.s
sdk/tests/ppc/asm/seq_tailcall_musttail.s
sdk/tests/ppc/opt_config.toml
