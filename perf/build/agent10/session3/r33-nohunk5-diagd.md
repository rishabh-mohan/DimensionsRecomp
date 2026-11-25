# #33 delta rating: `s33-popin-nohunk5.patch` and diagnostic (d) `s33-diagd-on-nohunk5.patch`

M10 (successor of Agent 10), session 3. Read-only work on 2026-11-25, 01:47-01:55: nothing was built or run. The patches were applied to scratch copies only.

**Files rated** (`build/agent6/s33-popin/`):

| file | sha256 (first 16) | size |
|---|---|---|
| `s33-popin-nohunk5.patch` | 57CFA8ADF1E90079 | 10725 B |
| `s33-diagd-on-nohunk5.patch` (stacks on nohunk5) | 6CF9377E9F09322B | 4580 B, 103 lines |
| `s33-popin-nohunk5-diagd.patch` (combined; == stacked result) | 797E614284B64226 | 14388 B |
| `APPLY-CHECK.txt` | B0753E079FDE053F | 7311 B |
| `DIAGD-CHECK.txt` | AC3A33D5EAC8CDFC | 2733 B |
| `CHECK.txt` | 8F2FABB162919C08 | 10873 B |
| `TESTPLAN.md` | 90DF23DED6A27F43 | 12698 B |
| rated base `s33-popin.patch` (unchanged) | 0D23024484CCDEE1 | 11003 B |

Previous rating: `build/agent10/t27/r33-popin.md` (ACF0BDB5A5262362).

**Base and apply.** The SDK is at 5350b1d. I copied the 4 live files (blobs 7e81db3b, 6f21eb6f, 55e9f02e, 8c169b41, as in r33) to `build/agent10/session3/tmp-s33/` and ran `git -c core.autocrlf=false apply --verbose`. nohunk5 applied cleanly to all 4 files, giving pipeline_cache.h 0BAF28BE, command_processor.cpp 00EA93D3, pipeline_cache.cpp C4CB51CC and frame_stats.h 9F3C4F9D, the same as TESTPLAN §0. (d) stacked cleanly on top: command_processor.cpp 97257A20 == TESTPLAN's (d) column.

## Verdict

- **nohunk5 (the first test patch): SAFE**, under the same conditions as r33. It is the rated patch with exactly two changes:
  1. Hunk #5 is gone (my S1). `CanEndSubmissionImmediately` is byte-identical to 5350b1d (APPLY-CHECK compares the two results: "only hunk #5 differs").
  2. Hunk #1 gains 3 comment lines (my N1).
  - Plus the matching hunk-header shifts (+64,18 and +441,8). `git diff --no-index` of the two patches shows nothing else.
  - The r33 conditions still hold: default false with `kRequiresRestart`; row 1 identity (1a, 1b) first, stop if it fails; the user's row-3 review gates any recommendation. Condition 4 (no hunk #5) is now met.
- **Diagnostic (d) in a separate bin `devoff4b-s33d-bin`: SAFE.** Your split keeps rows 1a/1b on a (d)-free bin, which is right: (d) adds a cvar test to the resolve path, so the s33d bin is not an identity reference. With (d) on it only logs (see below). Running it before #33 is suggested as a setting closes r33 S2's precondition.
- **Build conditions for both bins (SAFE-IF):**
  1. Build from clean 5350b1d sources plus exactly that bin's patch. Copy TESTPLAN §0's result files (check the hashes above) or apply with `-c core.autocrlf=false`. M2's own `build/agent2/session3/s33-popin-no5.patch` (4061ED2D...) is code-identical but lacks the N1 comment. Use M6's 57CFA8AD and name it in the MANIFEST (N1).
  2. Only `rexgpu-xenos.dll` changes. As in the C1 rating (S1 there), keep `snap1-sdk/install/bin/rexgpu-xenos.dll` E3CB99CF intact: after each build, the MANIFESTs of devoff4b-bin, devoff4b-cg26-bin and native4b-bin must still verify. Tonight four bins want different `rexgpu-xenos.dll` builds (#19, devoff4bv, s33, s33d), so build them one at a time, each from a fresh tree. Check the before-hashes each time so no bin picks up another bin's patch (S1).
  3. Bin checks: the s33 bin's DLL contains `d3d12_pipeline_creation_no_wait` and **not** `d3d12_resolve_after_drop_log`; the s33d bin's DLL contains both; exe and rexruntime equal devoff4b-bin. Fresh bin dirs, no `cache/` or seeds copied (TESTPLAN §1.4).
- No BLOCKER. 1 SHOULD, 3 NIT.

## What I checked in (d)

- **Default off.** `REXCVAR_DEFINE_BOOL(d3d12_resolve_after_drop_log, false, ...)` with `kRequiresRestart` (patched L92-96). The OFF cost is one cvar read per dropped draw (only in the existing `skip_draw` branch, patched ~L2839) and one per successful resolve (patched L3810). No other change to the default path.
- **Threading.** `resolve_after_drop` and `NoteResolveAfterDrop` live in the TU's anonymous namespace (L137-391). They are touched only from `IssueDraw` and `IssueCopy`, both on the GPU command thread. #19's Submit thread doesn't call either.
- **Symbols exist.** `register_file_->values[XE_GPU_REG_RB_COPY_DEST_BASE]` (register_table.inc L602; same form at cp L511, draw.cpp L947). `RegisterFile::Get<T>()` (register_file.h L54-57). `copy_command` (registers.h L862). `xenos::CopyCommand::kNull` (xenos.h L984). `std::unordered_map` is already used in the TU (cp L5761) and included through command_processor.h. `REXGPU_INFO` is used in the same namespace (L242). Not compiled.
- **Bounded.** At most 4096 lines plus one "no more" line. The `tainted` map is keyed by resolve destination base; entries are erased on a clean resolve, so its size is bounded by the distinct resolve destinations. Only resolves that write memory are counted (`copy_command != kNull`). A clear-only resolve still resets `drops_since_resolve`, as the comment says.
- **Semantics (measurement only).** Drops aren't matched to render targets, so `after_drop` is an upper bound, as documented. The key is the raw `RB_COPY_DEST_BASE`, not draw.cpp's adjusted address (L947-980). That's enough for taint and heal per destination, but read "dest" in the log as the raw base (N2).

## Findings

- **S1 (SHOULD, build).** Four pending bins rebuild the same `rexgpu-xenos` target from one SDK copy. Use one fresh 5350b1d tree per bin, check before- and after-hashes of every changed SDK file, and record them in each MANIFEST. Keep E3CB99CF reproducible (see the C1 rating, S1).
- **N1.** Two "no hunk 5" patches exist: M6's 57CFA8AD (rated) and M2's 4061ED2D (no N1 comment). Retire one, or record which was built.
- **N2.** In TESTPLAN row (d)'s reading notes, "dest" is the raw `RB_COPY_DEST_BASE`, and `after_drop` is an upper bound over all targets.
- **N3.** The (d) INFO lines are a new log family for the s4b kit / gate_logdiff. Allow them only in (d)-on arms of the s33d bin, as r33 N3 does for the no-wait lines.

The open r33 items stand: N2 (forced-wait count ≠ stalls), N3 (allow-lists), N4 (PENDING-DIFFS). My #19 rating S2 also stands: #33 ON (even without hunk #5) is not combined with #19 ON without a re-rating.

## Read / Sent

Read: the files in the table; the patched command_processor.cpp L85-100, L250-391, L2808-2848, L3788-3825; register_file.h L40-65; the symbol greps above; r33-popin.md findings. Sent: this verdict to the Overseer.
