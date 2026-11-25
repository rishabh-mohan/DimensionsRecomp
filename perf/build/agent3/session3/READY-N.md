# READY-N.md: the #18 "ready-N" gate that #19 and W7 wait on (S3T-3, M3)

Paper only. Sources: QUEUE.md L91-92, L110-117, L126 and L154 (`build/agent7/s4b-queue/`); RATE-REQUEST.md §10 L366-368, L435-455 (`build/agent7/s4-r1s2/`); agent7 HANDOFF L97 and L123; s4b-queue.ps1 L69-74 (ReadN) and L132-136; CP = `build/agent7/s4-r1r2/new/sdk/src/graphics/d3d12/command_processor.cpp`; `session3/DRAW-BYTES.md` (E2.2, sha256 81596BE9, cites spot-checked by M3).

## 1. What the gate is

- **`<N>` is the #18 split size.** It goes into `d3d12_submit_split_kb=<N>`, and a submission ends at the first draw or resolve tail once the deferred list has ≥ N KB in it (CP L3107-3111, L3713-3716, L4364-4394).
- **The rule** (QUEUE.md L91-92): N ≈ **half the median KB per list from row 9**. Row 9 is s4b09, on `devoff4b-ctr-bin` with #20's `deferred_counters:` line, which gives lists and KB per ~10 s. "**If row 9 can't run, N = 64.** The stress value is 16." The ~30 min subset (L154) already ran row 10 "at N = 64 (no counters bin)", on paper.
- **The marker** is `build/agent3/s4b/ready-N`, with the number on its first line. s4b-queue's ReadN (L69-74) puts it in for `<N>`, and rows wait while it is missing (L132-136). RATE-REQUEST L366-368 says the same for #19: "waits for Agent 3's ready-N gate (from the s4b10/s4b16 counters)".
- **Who waits on it:**
  - S4b rows 10, 12, 13, 15, 16 (M/A routes) and 25 (W7 title scene, uncapped).
  - #19 rows i, c, f, g (M route), d (title, uncapped) and e (level soak, 600 s).
  - W7 s18 and s19 (title); s19h uses N/2.
  - #19 rows a, b and j don't need it.
- **Who sets it:** QUEUE.md says "Agent 7 posts N". The marker sits in Agent 3's folder, so M3 writes it, but **only on the Overseer's word**.

## 2. What data exists

- **No list-size data at all.**
  - Row 9 never ran, nor did rows 10, 11 and 16. The `devoff4b-ctr-bin` bin doesn't exist; only partial work is in `build/agent2/ctr/`, and building it is forbidden under HOLD.
  - A search of every game*.log under `build/` and `bench/` since 11-21 found `deferred_counters:` / `d3d12_submit_split` lines only in **synthetic** preflight fixtures (`build/agent3/s4b/preflight/synth/s4b09|10|25`, made-up values).
  - perf.csv has `draw_calls` but no bytes or submissions.
- **Draw counts per frame** (perf.csv, devoff4b OFF):

| scene | run | p10 / median / p90 / p99 / max draws | frames > 330 draws |
|---|---|---|---|
| W7 title scene | W6 matrix 20261123-0009 s0/p2/p2f | 218 / 226 / - / - / 228 | ~0 |
| M route (`b-gate-menus-long`) | s4b01 20261122-205356 | 218 / 220 / 228 / 5620 / 12398 | 9.9 % (310 frames > 2600) |
| L route (level) | s4bL0 20261122-210059 | 218 / 220 / 788 / 5316 / 13239 | 17.9 % (970 frames > 2600) |

- **Bytes per draw** (DRAW-BYTES.md, read from the code, not measured):
  - min 56 B, typical ~200 B (130-280), max ~0.8 KB.
  - Plus ~3 KB fixed per frame and ~0.35 KB of re-bind per extra submission.
  - Title ≈ **47 KiB/frame** typical (13-186). Level static (785 draws) ≈ 156. Heavy (6k draws) ≈ 1175.
  - 330 draws ≈ 64 KiB at the typical size.
- **The big unknown is K**, the submissions per frame that already happen without a split:
  - swap (CP L2569/L2575)
  - OnPrimaryBufferEnd: `d3d12_submit_on_primary_buffer_end`, default true, ends a submission whenever the CP catches up with the guest (L2578-2583)
  - occlusion queries
  - memexport readbacks

  KiB per list = (KiB/frame)/K, and no log gives K. The `d3d12_submit_split:` counter line prints only with the cvar on **and** only while a split is due (CP L4364-4409), so a split = 0 run can't measure it.

## 3. Can N be chosen from existing logs, without new runs?

- **The rule's own value: no.** "Half the median KB per list" needs row 9's counters (or any split line), and none exist.
- **The fallback: yes.** N = 64 is the documented value when row 9 can't run, and it can't: no CTR bin, and no build under HOLD.
- **What 64 does, estimated from the draw counts and DRAW-BYTES.md:**
  - **M route rows** (10, 12, 13, 15, 16; #19 i, c, f, g): about 10 % of frames (> ~330 draws) split, and the steady menu frames (~220 draws) don't. Row 10's `splits > 0` / `failed = 0` proofs are reachable. **OK as a functional test.**
  - **Level soak** (#19 e): ~18 % of frames split, and the heavy frames split up to ~18 times. **OK, a real stress.**
  - **W7 title scene** (s4b25, #19 d, W7 s18/s19): 218-228 draws ≈ 47 KiB/frame < 64, so **steady-state frames never split**. N = 64 needs ≥ ~276 B/draw *and* K = 1 to split even once. W7's #18 arm would then measure a no-op, not a treatment. s19h at N/2 = 32 might split about once per frame, but only if K = 1. **This is the risk to flag.** s4b_check already doesn't require `splits > 0` for s4b25 (s4b_check.py L520-526), so the arm would "pass" without testing anything.

## 4. Options (Overseer decides)

| option | runs | N | good | bad |
|---|---|---|---|---|
| **A. Fallback now** | none | 64 | Documented. Unblocks every `<N>` row at once. Fine for M/level rows. | The W7 title arms (s4b25, #19 d, s18/s19) very likely don't split, so W7's #18 result would be empty. |
| **B. Estimate now** | none | 24 (title, if K = 1) | Splits ~2×/frame on the title by the estimate. Still splits on M/level. | MEDIUM-LOW confidence: ±50 % on B/draw, and K unknown (K = 2 → N should be ~12). Heavy frames split ~50×/frame (stress, harmless). Off the documented rule. |
| **C. Measure, then set** (recommended) | 1 run, ~4 min, no build: **s4bN16** = s4b25's exact scene/args at `d3d12_submit_split_kb=16` (staged in `queue-s3.jsonl`, marker `go-n`, checked as row 11 against RT) | half the measured KiB per natural list | Uses the real W7 scene. From the `d3d12_submit_split:` lines: **K = (Δsubmission − Δsplits)/Δframe**, KiB/frame ≈ 16·(Δsplits/Δframe) + leftover, then N = ½ · KiB/frame / K. That follows QUEUE.md's rule with this run standing in for row 9. | Needs LOAD GO. Uncapped title (`framerate_limit=0`) loads the GPU, so the host should be quiet. Check that `failed` and `held_*` stay ~0, or the count of splits that were due is too low. |

**Recommendation: C**, run first in the next LOAD GO window.
- If no run is allowed soon and #19 must move, use **A** (64) for the M/level rows.
- Under A, record that the W7 title arms can't show a #18 effect until N is re-picked: s4b25 will print its splits per frame, which settles the question.

There is one `ready-N` value for all rows. If the title N from C is much smaller than what the level soak should use (heavy frames would split ~50-100×), the Overseer can accept that as stress or give row e its own value. That would need Agent 7's row text to change, which is not ours.

## 5. Writing the marker (only on the Overseer's word)
```powershell
Set-Content -LiteralPath build\agent3\s4b\ready-N -Value '<N>' -Encoding ASCII   # first line = integer only (ReadN: ^\d+$)
```
Rows with `<N>` also need their other markers (`ready-later` and `ready-s4b-off`; #19 rows `ready-s4r1s2`; row g `ready-dbg`).
