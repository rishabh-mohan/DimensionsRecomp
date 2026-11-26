# M2 zpd-log v2: delta rating (re-ack of Z2 for ov 6DE509E3)

M10, 2026-11-25 18:42. Static review only (QUIET MODE): file reads, `git show` of the a7e79c0 blob, hashes of small files. Nothing was compiled or run.

## Files (build/agent2/s5/zpd-log/)

| file | sha256/16 | bytes |
|---|---|---|
| zpd-log.diff (v2) | 5CAD04BBCDF20ED3 | 9119 |
| ov/src/graphics/d3d12/command_processor.cpp | 6DE509E3FB683A2E | 279210 (6039 lines) |
| DELTA-v2.md | 6C6519D63DE2418A | 2551 |
| check.txt | 7C46A3EE7113AB81 | 1551 |
| check.py | 49D1395CFD8FF17D | 7237 |

Base: rexglue-sdk a7e79c0 `src/graphics/d3d12/command_processor.cpp`, blob sha 00EA93D3, per check.txt. v1 was diff 2FB24916, ov DF84086F, rated in zpd-log-rating.md 68813034.

## Verdict

- **Code: SAFE.** My S1 from 68813034 is fixed.
- **Stacked bin: SAFE-IF Z1-Z5 from 68813034**, with Z2 now naming **ov 6DE509E3** (it replaces DF84086F). The stk TU 9B92AAF9 is unchanged.

## What I checked

- **The diff is still add-only**, +86/-0 in 12 hunks, with one file touched.
  - The three handler sites now set only `disable_reason` before calling DisableHostOcclusionQueries(): "no sample count memory", "begin at another address…" and "end at another address" / "end without an active query".
  - The `++disabled` in those sites is gone.
- **DisableHostOcclusionQueries() counts at the top**, guarded by `occlusion_query_resources_available_` (ov L5901-5904).
- **Every caller of DisableHostOcclusionQueries at HEAD is covered:**
  - handler L451/L481/L492;
  - BeginGuestOcclusionQuery L5844, which now sets its reason (ov L5929);
  - ShutdownOcclusionQueryResources L5801. It runs after the "shutdown" log line (diff hunk at ShutdownContext), so the logged counts don't include it.
- **"At most once per run" holds.** The function sets `occlusion_query_resources_available_ = false`. The only place that sets it true is InitializeOcclusionQueryResources, called once from setup (HEAD L1921).
- **The "disabled" line is logged.** All the disable paths that matter run inside ExecutePacketType3_EVENT_WRITE_ZPD, including the begin-while-active path via BeginGuestOcclusionQuery. OcclusionQueryPacketScope's destructor therefore sees `disabled` change and logs it.
- **Off == HEAD.** Compared with v1, the only difference is where one uint64 increment happens, plus one `const char*` store on the begin-while-active path. Query, draw and submission semantics are unchanged.
- **Thread safety is the same as v1.** Everything runs on the GPU commands thread.
- **ov matches.** The ov hash is 6DE509E3 = check.txt L15. I spot-checked the ov lines at L174, 515, 547, 560, 5903 and 5929 against the diff. I relied on check.txt L11-13 (git apply --check, scratch apply, ov == base + diff) and didn't re-run them, because python and scripts aren't allowed in quiet mode.

## Conditions

- Z1-Z5 from 68813034 are unchanged, except that Z2 names ov 6DE509E3.
- **V1:** re-run check.py after the lift. RESULT must be PASS with ov 6DE509E3, and the compile check (Z1) must be done on this ov, not DF84086F.

## Findings

- **N1 (NIT):** `disable_reason` is a single last-writer field. ShutdownOcclusionQueryResources sets no reason, but it runs after the last log line, so that doesn't matter.
- **N2 (NIT), not reviewed here:** the post changes for Z4/Z5 (nops_smoke_post.py) and the new synth_post.py cases. They have not been run (quiet mode). They belong to the nops-kit delta, which M2 sends after the lift.
