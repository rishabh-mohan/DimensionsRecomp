# Agent 12 handoff (2026-11-23, before the break)

Agent 12, task #24, written 2026-11-23 at about 06:15. The project pauses from about 13:00 today for a few days to a
week. All paths are relative to the workspace root.

## Rules that still apply

- **Commits:** only Agent 1 commits or pushes. The S4b/S4c code is on GitHub: rexglue-sdk `perf/opt` 5350b1d and
  DimensionsRecomp `perf/opt` b0bd3b4.
  - The commits are the source of truth. The `build/agent12/s4-*` folders hold the staged copies that were reviewed.
  - The status lines in the s4-* NOTE files date from staging ("staged only, not built"). That code has since been
    built and committed (see "What I own").
- **HOLD:** before every command, check that `perf-notes/WINDOW-HOLD.txt` doesn't exist. While it exists, make no
  tool calls.
- **Processes:** run python at Below Normal, one process at a time, with `python -B`. Agent 12 does no builds and no
  game runs.
- **Other agents' folders are read-only:** `build/agent8/matrix/`, `build/agent3/`, `build/agent6/`,
  `bench/agent5/` and the rest.

## State at the break

- **Nothing of mine is running.** No background task, no subagent at work, and no staged change waiting to be
  applied.
- **Night windows of 2026-11-23: all 7 PASS** (`build/agent12/w6-gates/NIGHT-RESULTS.md`).
  - The two W6 windows PASS with G8 = raw FAIL + "WARN, finding 10, Agent 1 22:25". The raw FAIL is gate A's
    minidump, and the timed runs are clean.
  - W9, W5b and W4c exit 0.
- **The gate kit** `build/agent12/w6-gates/run_gates.py` is ready for W7-W10. It reads the matrix path and the arms
  from matrix.json.
  - The G12 gap bug was fixed and tested on 2026-11-23. Every night window had read "1439/1440 min later".
  - A read-only checker confirmed NIGHT-RESULTS.md against the sources, plus the fix's edge cases.
- **C1 v3 is committed.** The 5 SDK files in `build/agent12/s4-c1v3/new/sdk/` are byte-identical to rexglue-sdk
  5350b1d (`git hash-object` against `git rev-parse`, 06:04).
  - Agent 10's rating is in b2r §35: SAFE at the default, and ON is SAFE to test when set at launch.
  - Both cvars default to OFF.
- **`build/agent12/s4-c1v3/NOTE.md` changes.**
  - New section: "Verify-mode caveats (2026-11-23)", which Agent 1 asked for.
  - New dated update: v3, not v2, is in S4b.
  - NOTE.md is documentation only and isn't in that folder's HASHES.txt. Its hash now differs from the one b2r §35
    quotes (9C9DCDCF…). The code files and diffs are unchanged.

## What I own

| Path | What | State |
|---|---|---|
| `build/agent12/w6-gates/` | The W6+ gate kit: `run_gates.py` + `run_gates.ps1` (G1-G12, one table + the RECORD line); `w6_env_record.py` (G11 power overlay, G12 quiet gate); `W6-GATES.md` (gates G1-G12, rules R0-R7); `RUN-GATES-FIXTURES.md`; the W5/W4b fixtures and `fixture_facts.ps1`; evidence `out-*.txt` / `gates-*.json`; `NIGHT-RESULTS.md`; `HASHES.txt` (06:08, 52 files) | Ready. Tests 2026-11-23: w6_env_record selftest 16/16 (06:07); run_gates selftest 51/51; W5 `EXPECT: OK (57/57)`; W4b `EXPECT: OK (53/53)` (05:54) |
| `build/agent12/w6-gates/night/` | `run-night-gates.ps1` (the 7 night dirs with their flags); `recheck-kit.ps1` (the kit's tests); the per-window `out-` / `gates-` / `err-` files | Done 05:55 |
| `build/agent12/p2c-check/` | `p2c_check.py`, the P2c memexport full-buffer counter check that G4 uses; `run_tests.ps1`, fixtures, NOTE.md, HASHES.txt | Tests 13/13 (2026-11-22 20:26) |
| `build/agent12/s4-c1v3/` | C1 v3 = v2 + the init latch: diffs, `make_c1v3.py`, `orig/` `v2/` `new/` copies, HASHES.txt, NOTE.md | In 5350b1d (commit subject "S4b: C1 v3 keep-watch, …") |
| `build/agent12/s4-c1v2/`, `build/agent12/s4-c1/` | C1 v2 (b2r §34) and v1 | Replaced by v3 |
| `build/agent12/s4-p2/` | P2 `shared_memory_single_hold_rearm` (default OFF) | On GitHub (S4a commit 3bb65bb, by its subject) |
| `build/agent12/s4-fixi/` | Fix (i) `physical_protect_hold_global_lock` (default OFF) | On GitHub (3bb65bb) |
| `build/agent12/s4-diag/` | The u diagnostic `shared_memory_upload_hash_log` (b2r §20) | On GitHub (3bb65bb) |
| `build/agent12/s4-p2c/` | The P2c memexport full-buffer counter (b2r §30) | In 5350b1d ("P2 counter") |
| `build/agent12/s4/`, `build/agent12/s4a-specs/` | S4 analysis outputs (waits, gpucmd compare, upload hashes), old notes snapshots, and Agent 3's S4a run specs | Historical |
| `build/agent12/s3flip/` | The S3 audio default-on diff and its syntax checks | Historical |
| `build/agent12/gcr/`, `pause/`, `bench/`, `bench-data/`, `logs/`, `obj/`, `pristine/`, `batch2-*` | Earlier tasks: lock and audio-shutdown replica tests, pause stress, I/O benches b1-b5, compile checks, pristine copies, the batch 2 audio diff | Historical. `bench-data/scatter.bin` is a 256 MB bench input that no open item needs |
| `bench/agent12/` | Scripts from earlier tasks: per-stage syntax checks, S4 analysis scripts, bench build/run | Historical |
| `perf-notes/agent12-io-memory.md` | My running notes. The top RESUME block is the latest state | Updated 2026-11-23 |

## Open items

### C1 and P2

Agent 10 (b2r row 42/§41): C1 ships only as p2fc (C1 + P2 + P2c) until one of the tests in items 2 and 3 settles
it.

1. **Row 7's F 92 is explained but not confirmed.**
   - Row 7 is `20261122-214221-s4b-07-c1v-level`: C1 + verify, P2 off. It had K 0 and F 92.
   - The explanation (code + logs) is a verify-mode false positive when P2 is off. I sent it to Agents 10, 3 and 1
     at 22:31 on 2026-11-22.
   - MakeRangeValid sets the valid bits under the global lock G (L356-371) and releases G. Then it arms the watch
     (L373-377), and only then re-hashes the pages (L381-383).
   - A write fault in that gap runs the F check (L577-583) against the hash from the page's previous upload.
   - With P2, G is held from L351-354 to L384, so there is no gap.
   - The line numbers are in `build/agent12/s4-c1v3/new/sdk/src/graphics/shared_memory.cpp`, which is the 5350b1d
     file. Details: `build/agent12/s4-c1v3/NOTE.md`, "Verify-mode caveats".
2. **s4bV0 hasn't run.** `build/agent3/runs/` had no s4bV0 dir at 06:03.
   - Spec: C1 off, otherwise as row 7 (L route + tags, 600 s).
   - Prediction: F > 0 on pages 01AE8000-022BF000, on thread XThread90B8 (F80001A8).
   - F = 0 refutes the explanation and makes C1 suspect.
3. **The verify-only fix, the alternative, isn't written.** Zero `keep_watch_verify_hashes_[page]` inside the G
   block at L356-371, re-run row 7, and expect F 0.
4. **Until item 2 or 3 settles it, C1 without P2 is "unverified, not failed".** Any C1 + verify run should have P2
   on, because P2 closes the gap.
5. **Read s4bLV (p2fc + verify, L route, 1800 s) and the finding-10 rows f10a/f10b with Agent 1's final rule
   (22:56).** A STUCK-LOCK is "WARN, finding 10" only if all three of these hold; anything else is FAIL:
   1. It is on CS 0x84959EDC, with the owner tid 0x17 parked in sub_83FAF180 at lr 83FAF188 or 83FAF200, and the
      waiter at lr 82A2A270.
   2. It recovers by itself, with no crash or WER.
   3. The run reaches the level. For s4bLV, that also means 3/3 LOADs and K 0 / F 0.

   Waivers given so far:
   - gate A, s4b24 `20261122-220520` and s4b20 `20261122-221447`: "Agent 1 22:25";
   - gate B `20261122-222313`: "Agent 1 22:55".
6. **P2's precondition holds in every run measured** (b2r §22/§25: the memexport full-buffer path must not run).
   - P2c total is 0 in the four W6 G4 arms: side 1 p2f, side 2 p2fc, side 3 p2fc attract, and gate A p2fcv. It is
     also 0 in s4b23.
   - No hold cap is staged. One is needed only if a later run shows total > 0.
   - No routes other than these were measured.
7. **Default-ON for C1 or P2 isn't decided.** Both default to OFF. Landing C1 ON needs a full SDK install and game
   rebuild, then re-pinned native baselines (b2r §35).

### The cp-state analysis

The analysis is Agent 6's: `build/agent6/hang/cp-state-s4b24-s4b20.md`, last updated 05:51.

- **All 4 finding-10 hangs are the same hang:** gate A, s4b-24, s4b-20 and gate B. Gate B's dump was read at 05:45
  (§7.3).
  - The lock is the same CS 0x84959EDC, with the same owner (render tid 0x17 in the fence poll) and the same waiter.
  - The CP was in IssueDraw's memexport readback full-path sync (AwaitAllQueueOperationsCompletion →
    CheckSubmissionFence).
  - Gate A and gate B were in the submit half (EndSubmission → D3D12 → driver).
  - s4b-24 and s4b-20 were in the wait half (WaitForSingleObject on the fence event, INFINITE).
- **My data is §7.1.** Verify drives the CP's kernel time: a 91-92% kernel share with verify on (row 7, gate A), against 20-36%
  without. Gate B, with verify off, is at 32% (§7.3).
- **The waits match the syncs.** Host-GPU waits ≈ memexport syncs in gate B's slow frames (696/698 and
  2708/2736).
  - P2 doesn't avoid that sync.
  - P2c = 0 doesn't count it.
- **Open: is the GPU the bottleneck, or was the host starved?**
  - All 4 hangs ran under Agent 2's -j8 build (2026-11-22 20:53:30-22:39:52).
  - The deciding test is Agent 3's quiet-host vpad L-route rows f10a/f10b. f10a started at 05:58
    (`build/agent3/runs/20261123-055810-f10a-m1-sfl-level`). Read them with the rule in item 5 above.
- **Addendum, 2026-11-23 06:25 (Agent 1 OK'd it):** quiet host: no hang so far, starved host likely; small margin.
  Source of truth: `build/agent3/f10/RESULTS.md` (a second f10a/f10b pair runs until 07:20); details in Agent 6's doc.
- **Candidates for after S4**, from source reading, not measured:
  - The memexport readback full-path sync (Agent 6 §6): more readback slots per key, a wait on the older
    submission, or batched/on-demand readback.
  - Verify's per-upload VirtualQuery (KeepWatchVerifyReadable → `memory::QueryProtect`). With verify on, it makes
    the CP about 50% kernel-bound (NOTE.md, "Verify-mode caveats").

### Gate kit to-dos

These are small, and none blocks W7-W10.

- **END_RE:** it should accept an empty runner exit code (`runner exit  (`) and treat it as FAIL. Today G3 shows
  CHECK "END missing", so read the window log by hand.
- **Kill lines:** G3 should parse Agent 5's kill lines as FAIL/CHECK: `NOT killed|could not kill|could not be
  killed|runner stopped: NO|process list could not be read|left over from the window`. Today, grep the window log
  by hand. For the 7 night windows that's done, with 0 hits.
- **By design:** G1 is MANUAL. The kit reports G8's raw FAIL, and the finding-10 waiver goes into the read-out by
  hand.
- **Cosmetic:** because of rounding, a G12 gap of 30-30.5 min prints "30 min later" together with the WARN.

### Read-out caveat

- The night windows ran the power overlay `best_performance`, but W5 ran `best_efficiency`.
- Don't compare absolute numbers across that change. This matters for W5b against W5.

## How to resume

1. Check that `perf-notes/WINDOW-HOLD.txt` doesn't exist.
2. Read the top RESUME block of `perf-notes/agent12-io-memory.md`, then this file.
3. Run the kit's tests:

   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\night\recheck-kit.ps1
   ```

   Expect: envrec 16/16; selftest 51/51; W5 `EXPECT: OK (57/57)`, exit 0; W4b `EXPECT: OK (53/53)`, exit 1 (from
   G10).
4. Gate a finished window:

   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\run_gates.ps1 build\agent8\matrix\<dir> [--one-bin] [--side <run dir>]... [--gate-a <run dir>] --json <out>
   ```

   - Flags:
     - `--one-bin`: when every arm uses the same bin;
     - `--side` / `--gate-a`: only for windows with P2/C1 arms (W6).
     - `night/run-night-gates.ps1` shows the full W6 call.
   - Exit codes:
     - 0 PASS;
     - 1 FAIL;
     - 2 usage;
     - 3 soft (CHECK, NO WINDOW);
     - 4 HOLD;
     - 5 `--expect` mismatch;
     - 6 kit crash.
   - Then grep the window log in `bench/agent5/launch/status/` for the kill lines, and apply any waivers by hand.
5. Check file integrity against `build/agent12/w6-gates/HASHES.txt` (06:08) with Get-FileHash.

## Key files

- `build/agent12/w6-gates/NIGHT-RESULTS.md`: the night verdicts.
- `build/agent12/w6-gates/W6-GATES.md`: the gate and rule definitions.
- `build/agent12/w6-gates/RUN-GATES-FIXTURES.md`: the kit's fixtures and tests.
- `build/agent12/w6-gates/run_gates.py`, `run_gates.ps1`, `w6_env_record.py`: the kit.
- `build/agent12/p2c-check/p2c_check.py` and its `NOTE.md`.
- `build/agent12/s4-c1v3/NOTE.md`: C1 v3 and the verify-mode caveats.
- `build/agent6/hang/cp-state-s4b24-s4b20.md`: Agent 6's cp-state analysis.
- `perf-notes/agent10-batch2-review.md`: Agent 10's ratings (§20, §30, §34, §35, row 42/§41).
- `perf-notes/agent12-io-memory.md`: my notes.
- `bench/agent5/launch/status/`: the window logs that G3 and G12 read.
