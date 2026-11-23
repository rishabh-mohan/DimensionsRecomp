# S4b functional-run queue (Agent 7, task #19; draft 14:30, board run 2)

This is the run side of S4b, for Agent 3 (runs) and Agent 2 (bins, #15). Every run is **FUNCTIONAL ONLY**: hidden
desktop, never timed, one game at a time. Runs go through `harness/run-game.ps1` and Agent 3's S4a tools in
`build/agent3/s4a/` (`s4a-queue.ps1`, `s4a_check.py`, `postcheck.ps1`, `attach.ps1`). Nothing here has run. No builds,
no git writes. `queue-s4b.jsonl` (same folder, written by `make_queue.py`) is a machine-readable copy of the agent rows
in Agent 3's queue.jsonl format.

## Sources

- **C1 v2:**
  - `build/agent12/s4-c1v2/NOTE.md` (test plan, L122-135);
  - b2r §34 (SAFE, and ON is SAFE to test), §21 A-D (L1059-1063) and §28.
- **P2 counter:** `build/agent12/s4-p2c/NOTE.md` and b2r §30.
- **#18/#20:** `build/agent7/s4-r1r2/NOTE.md` test plan 1-7, and b2r §31 (row 32, `s4-r1r2.diff` BD0C4A93…).
- **M1:** `build/agent5/s4-m1/NOTE.md`, and b2r §33 plus its addendum (the bench gate).
- **#24:** b2r §26 ("Landing OFF needs" 1-3, "Before ON needs" 4-6) and §32 (N1-N4 PASS, draft 01D9F8F3…).
- **#26:** SESSION2 14:02 (a codegen option, default OFF; 20 db16cyc sites in 10 TUs), S4-DRAFT L212-217 and W10 (L293).
  Agent 9 is staging it; at 14:15 there was no NOTE and no rating yet.
- **Runs and flags:**
  - `perf-notes/agent3-run-harness.md` §1, §4 and §8;
  - `build/agent3/s4a/queue.jsonl`;
  - S4-DRAFT §2b and the W6/W7 rows (L288-289);
  - SESSION2 L2366, 14:02 and 14:08.

## Bins (placeholders; Agent 2 maps them in #15)

| placeholder | what | rows |
|---|---|---|
| `<S4B-OFF>` | devoff S4b, every switch OFF (on devoff4 for the A line, devoffB4 for the B line) | most |
| `<S4B-NAT>` | native S4b, every switch OFF | 2, 5 |
| `<S4B-CTR>` | `<S4B-OFF>` plus `-DREX_D3D12_DEFERRED_COUNTERS=1` on SDK `d3d12/deferred_command_list.cpp` only. No header or layout change, so only rexgpu-xenos is rebuilt | 9, 16 |
| `<S4B-CG26>` | `<S4B-OFF>` regenerated with #26's codegen option ON (W10's arm) | 21 |

**References:**
- `R1` = `build/agent3/runs/20261122-133333-s4a-r1-off-devoff4` (S4a OFF, PASS). Second base:
  `20261122-131206-s4a-ref-devoff3`.
- `RN` = Agent 3's S4a native4 r5 re-run, if it passed. Attempt 1 (`20261122-135155-s4a-r5-off-native4`) was a
  harness fault. Otherwise use `20261122-055439-bgate-rev-native3d`.
- `RA` = `20261122-140637-s4a-udiag-attract` (S4a attract scene, u-diag cvars).
- `RT` = `20261122-133730-s4a-udiag` (S4a title, uncapped, u-diag cvars).
- On the B line, use devoffB4/nativeB4 OFF runs as the first base if they exist, with R1/RN second.

## Before row 1 (no game)

- **G1 (Agent 2):** the manifest checks, and every staged diff applied at its rated hash:
  - C1 v2 `keep-watch-v2.diff` 418D3D39… plus `keep-watch-rexlego.diff` 4D0C1079… (keep CRLF);
  - #18/#20 `s4-r1r2.diff` BD0C4A93…, or 2516F199… plus 51999104…;
  - P2c as in its NOTE;
  - M1 EBECE86E… (rebase it if P3 lands first);
  - #24 01D9F8F3… plus the CMake edit;
  - #26 after Agent 10's rating.

  Check also that the new cvars exist with their defaults.
- **G2 (Agent 9 or 2, ~3 min):** #26 OFF. The regenerated text must be byte-identical to the pin: the sha256 of every
  `generated/` file (on B, batch-nolr SHA256SUMS 24CE1493…). Row 1 covers #26 OFF at run time only if G2 passed.
- **G3 (Agent 2):** #24's map check on the Xenos bin: 27 → 31 hooked aliases (N2), with skip_lr off.
- **G4 (Agent 5):** M1's microbench (`bench/agent5/m1_copybench.cpp`), built and run without `--skip-check`. Pass:
  exit 0 and 0 failures on both check lines. It gates rows 19-20 only.

## Conventions

- **Scenarios** (est = Agent 3's estimate from launch to close):
  - `M` = `-Seconds 420 -InputScript harness\routes\b-gate-menus-long.txt` (boot → title → start → menu walk → back →
    idle to attract; 54 steps; est 265 s).
  - `A` = `-Seconds 420 -StatsWarmup 20 -InputScript harness\routes\attract-long.txt` (the 3D attract scene, no Toy
    Pad; est 440 s).
  - `B90` = `-Seconds 90`, no input (boot and title; est 115 s).
  - `T180` = `-Seconds 180 -StatsWarmup 20`, no input, idle title (the timing windows' scene; est ~205 s).
  - `L` = title → menu walk → one level load (~10 min). It **needs the user**: the Toy Pad answer (harness §4
    question 2: tag dumps or a virtual-tag tool), then either a scripted level route with the tags placed over TCP,
    or the user at the keyboard on the real desktop.
- **Cvars and env:**
  - `-Cvar` items go into the run's toml at launch.
  - C1's two cvars and `d3d12_submit_split_kb` are kInitOnly. Set them at launch only, never from the dev console
    (b2r §34).
  - `d3d12_submit_split_kb` stays 0 on native.
  - #24 is env-only (`LEGO_GPU_WAIT_*`, Xenos only). run-game strips inherited `LEGO_*`, so #24 is OFF unless `-Env`
    sets it.
- **`BASE`** means all of:
  - exit 0, a clean WM_CLOSE, every route step done, no dumps, [error] 0;
  - logdiff NEW 0 / MORE 0 / FLAG 0 (GONE = Toypad lines only);
  - the same front-end scenes (218/222 boot, 226/1022 title, 220/528 and 220/534 menus, 219/226 loading), with
    marks first-frame .. up-2 identical;
  - no STUCK-LOCK and no `PhysicalHeap::Protect failed`;
  - TimerQueue ticks rise, and the slow state is noted.

  **`BASE + X`** is BASE, with NEW keys allowed only for lines matching X (`s4a_check.py --allow-new X`).
- **With `slow_frame_log_ms` set,** every slow-frame line changes and the log rotates at 5 MB. Join all `game*.log`
  files and compare by field (Agent 3's r2 method).
- **`<N>`** is the #18 split size: about half the median KB per list from row 9 (I post it). If row 9 can't run,
  N = 64. The stress value is 16. Substitute it in the `<N>` rows before the runner reaches them.
- **Readers:**
  - A3 = Agent 3: the check text, ~3 min, read while the next run plays.
  - The item owners: A12 = Agent 12 (C1, P2c), A7 = Agent 7 (#18/#20), A9 = Agent 9 (#24, #26), A5 = Agent 5 (M1)
    and A4 = Agent 4 (native re-pin).

## The queue (in run order: all OFF, then each item ON alone, then the W6/W7 arms)

| # | item | bin | cvars / env | scenario (est s) | passes if | reader (min) | user |
|---|---|---|---|---|---|---|---|
| 1 | OFF: all, devoff | `<S4B-OFF>` | none | M (265) | BASE vs R1, with no line from any S4b item (`C1 keep-watch`, `d3d12_submit_split`, `deferred_counters`, `GPU wait`, `memexport full-buffer`). This run is the OFF step of every item: #18 (cvar 0), #20 (macro 0), C1 v2, P2c, M1, #24 (env unset) and #26 (with G2) | A3 3 | no |
| 2 | OFF: all, native | `<S4B-NAT>` | `native_settings_frontend=false` | M (265) | BASE vs RN (draws from frames.csv). No C1 line. It is Agent 4's re-pin input: C1 and #24's CMake edit change the native fingerprint once | A3 3, A4 5 | no |
| 3 | OFF: all, attract | `<S4B-OFF>` | none | A (440) | exit 0, every step, no dumps, [error] 0; vs RA NEW 0 / MORE 0 / FLAG 0 (GONE = RA's u-diag lines). The attract base for rows 8, 12 and 17 | A3 3 | no |
| 4 | ON: C1 v2 with verify | `<S4B-OFF>` | `physical_protect_hold_global_lock=true;physical_protect_keep_watch=true;physical_protect_keep_watch_verify=true` | M (265) | BASE vs row 1 + `C1 keep-watch`. Init `on (with physical_protect_hold_global_lock)`; at least one `first kept protect` line (gate D, and A's positive control); the last `kept so far` line gives the count. 0 verify-mismatch (K) lines (gate A, menus part). 0 `Recovered stale physical page protection` and 0 `Unhandled guest physical write fault` (gate D) | A3 3, A12 5 | no |
| 5 | ON: C1 v2, native (gate C) | `<S4B-NAT>` | `native_settings_frontend=false;physical_protect_hold_global_lock=true;physical_protect_keep_watch=true` | M (265) | BASE vs row 2 + `C1 keep-watch`. Init `on, but blocked`; exactly one `blocked for this process (native renderer)` line; no `kept` line | A3 3, A12 2 | no |
| 6 | ON: C1 v2 without the hold | `<S4B-OFF>` | `physical_protect_keep_watch=true` | B90 (115) | exit 0. The init WARN `on, but physical_protect_hold_global_lock is off…`, no `kept` line, and no other NEW key | A3 2 | no |
| 7 | ON: C1 v2 with verify, level | `<S4B-OFF>` | as row 4 | L (~600) | Row 4's checks through the level load: 0 K lines (completes gate A), the kept count rises, gate D's zero lines, no hang or stall (b2r §21 A and D; §28: an ON run must include a level load) | A3 3, A12 5 | **yes** |
| 8 | ON: P2 counter (P2 ON) | `<S4B-OFF>` | `shared_memory_single_hold_rearm=true;slow_frame_log_ms=1` | A (440) | exit 0, every step, no dumps, [error] 0; logdiff by field vs row 3 (or RA). The last slow-frame line matches `memexport full-buffer (\d+)x \(total (\d+)\)`. total = 0 closes P2's memexport gate; total > 0 goes to Agent 1 (hold cap) | A3 3, A12 3 | no |
| 9 | ON: #20 counters | `<S4B-CTR>` | none (split 0) | M (265) | BASE vs row 1 + `deferred_counters`, about every 10 s. A7 reads the median KB per list (`<N>` is about half of it, for rows 10-16 and 25) and the repeat share per command type (step 2's go/no-go) | A3 3, A7 5 | no |
| 10 | ON: #18 at `<N>` (W7's #18 arm) | `<S4B-OFF>` | `d3d12_submit_split_kb=<N>` | M (265) | BASE vs row 1 + `d3d12_submit_split`. Init `d3d12_submit_split_kb: splitting submissions at N KB of deferred commands`. Every `d3d12_submit_split:` line has `failed=0`; splits > 0; submissions per frame above OFF; the same scenes (the frame comparison) | A3 3, A7 3 | no |
| 11 | ON: #18 stress | `<S4B-OFF>` | `d3d12_submit_split_kb=16` | M (265) | as row 10 | A3 3, A7 3 | no |
| 12 | ON: #18 hold paths | `<S4B-OFF>` | `d3d12_submit_split_kb=<N>` | A (440) | as row 10, against row 3. `held_pipelines` > 0 (every run starts with an empty shader storage); `held_query` > 0 if the attract scene runs occlusion queries; `held_scratch` = 0 expected | A3 3, A7 3 | no |
| 13 | ON: #18 with memexport readback | `<S4B-OFF>` | `d3d12_submit_split_kb=<N>;d3d12_readback_memexport=true` | M (265) | as row 10. Any NEW key besides the split lines means adding an OFF control with `d3d12_readback_memexport=true` alone | A3 3, A7 2 | no |
| 14 | ON: debug-layer control (#18 OFF) | `<S4B-OFF>` | `d3d12_debug=true` | M (265) | exit 0, every step. Its debug-layer messages are row 15's control | A3 3 | no |
| 15 | ON: #18 with the debug layer | `<S4B-OFF>` | `d3d12_debug=true;d3d12_submit_split_kb=<N>` | M (265) | no debug-layer message that row 14 lacks; `failed=0` | A3 3, A7 3 | no |
| 16 | ON: #18 with #20's counters | `<S4B-CTR>` | `d3d12_submit_split_kb=<N>` | M (265) | as row 10 + `deferred_counters`: more lists per 10 s than row 9, and a repeat share in row 9's range | A3 3, A7 3 | no |
| 17 | ON: #24 P1 (stats, back-off OFF) | `<S4B-OFF>` | `-Env LEGO_GPU_WAIT_STATS=1` | A (440) | exit 0, every step, no dumps; vs row 3 the only NEW lines are `GPU wait`. In the `GPU wait stats` lines (parse by field name, §32), l1_waits, l1_polls, l2_tries and kicks are all > 0. l2_tries = 0 means a skip_lr bin, with H2 silently off. A9 sizes S and Q from it | A3 3, A9 5 | no |
| 18 | ON: #24 at Q = 250 | `<S4B-OFF>` | `-Env LEGO_GPU_WAIT_BACKOFF_US=250;LEGO_GPU_WAIT_STATS=1` | M (265) | BASE vs row 1 + `GPU wait`: one `GPU wait back-off: ON (…)` line, the same exit, no new STUCK-LOCK, `sleep_fail` = 0 | A3 3, A9 3 | no |
| 19 | ON: M1 (after G4) | `<S4B-OFF>` | `shared_memory_upload_nontemporal_copy=true` | M (265) | BASE vs row 1 (NEW 0 / MORE 0). The same scenes stand in for the frame hash, since the hidden desktop can't take screenshots. M1 logs nothing, so run.json's cvars are the only proof it was ON | A3 3, A5 3 | no |
| 20 | ON: M1, level | `<S4B-OFF>` | as row 19 | L (~600) | as row 19 through the level load; no crash | A3 3, A5 3 | **yes** |
| 21 | ON: #26 (only if built) | `<S4B-CG26>` | none | M (265) | BASE vs row 1. Output-identical expected: `_mm_pause` only replaces the db16cyc spin hint | A3 3, A9 3 | no |
| 22 | W6: `#8 + #5` | `<S4B-OFF>` | `shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true` | M (265) | BASE vs row 1; no hang or stall (fix (i), b2r §23) | A3 3 | no |
| 23 | W6: `#8 + #5`, level | `<S4B-OFF>` | as row 22, plus `slow_frame_log_ms=1` | L (~600) | fix (i)'s level-load check (b2r §23): logdiff NEW 0, no hang or stall, no `PhysicalHeap::Protect failed`. Also reads P2's `total` in a level (b2r §30) | A3 3, A12 3 | **yes** |
| 24 | W6: `#8 + #5 + #4` (C1 ON, verify off) | `<S4B-OFF>` | `shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true;physical_protect_keep_watch=true` | M (265) | as row 4 without the K check (W6 times C1 with verify off); kept count ≥ 1 | A3 3, A12 3 | no |
| 25 | W7: `#18` on the timing scene | `<S4B-OFF>` | `d3d12_submit_split_kb=<N>;framerate_limit=0` | T180 (205) | exit 0, no dumps; vs RT the only NEW lines are split lines (GONE = RT's u-diag lines); `failed=0`. Record splits per frame for W7 | A3 2, A7 3 | no |
| 26 | optional: every S4b switch ON | `<S4B-OFF>` | row 24's cvars, plus `d3d12_submit_split_kb=<N>;shared_memory_upload_nontemporal_copy=true` and `-Env LEGO_GPU_WAIT_BACKOFF_US=250` | M (265) | BASE + each item's lines; `failed=0`; kept ≥ 1; no STUCK-LOCK. An interaction smoke, not a W6/W7 arm, run only after rows 4-24 pass | A3 3 | no |

**Notes on the arms:**
- W6's s0 is row 1. Its #8 arm is S4a r3 (PASS) plus row 8.
- W7's `#18 + #19` and `#18 + #19 + #20` arms have no rows. #19 isn't rated or soaked, and #20 step 2 (the filter)
  isn't staged.
- The slow-frame line's new suffix (b2r §30) is ` | memexport full-buffer Nx (total M)`.

## Time

- **Agent runs: 22** (rows 1-6, 8-19, 21, 22, 24 and 25):
  - 16 × M + 4 × A + B90 + T180 = 4,240 + 1,760 + 115 + 205 = 6,320 s ≈ 105 min;
  - plus ~10 s between launches, so **≈ 109 min (1 h 49 min)**.
- **User runs: 3** (rows 7, 20 and 23), ~10 min each, so ≈ 30 min.
- **Total: 25 runs, ≈ 139 min (~2 h 20 min) of game time.** Optional row 26 adds ~5 min.
- **Reading:**
  - A3 ≈ 73 min; the owners ≈ 68 min (A12 21, A7 25, A9 11, A5 6, A4 5).
  - Nearly all of it overlaps the next run. The tail after the last run is ~5 min.
- **Without the conditional rows** (no #26-ON bin: row 21; M1's bench not passed: rows 19-20; no debug layer: rows
  14-15): 18 agent runs, ≈ 91 min, plus 2 user runs.

## The ~30 min subset

Run order 1 → 4 → 10 → 8 → 2 → 5. That is 5 × M + 1 × A = 1,325 + 440 = 1,765 s, plus the gaps, so ≈ 30 min.

- **1:** S4b OFF = S4a, the gate for everything else.
- **4:** C1's positive control, gate D, and the menus part of gate A.
- **10:** #18 ON at `<N>` = 64 (no counters bin in the subset), checking `failed=0`.
- **8:** P2's memexport `total`, the open W6 gate. Compare with RA, since row 3 isn't in the subset.
- **2:** native OFF, Agent 4's re-pin input.
- **5:** C1's gate C on native.

If time runs short, drop from the end: 5 first, then 2.

## Runs that need the user

Rows 7, 20 and 23 each need a level load. That needs the Toy Pad answer (harness §4 question 2; S4-DRAFT §4a), then
either a scripted level route with tags placed over TCP, or the user at the keyboard on the real desktop (~10 min
each).

If there are no tags:
- gate A and §28 stay open, so C1 can't be timed ON in W6. W6 falls back to s0 vs #8 (S4-DRAFT L288);
- fix (i)'s and M1's level-load checks stay open.

## Open items

1. **Agent 2's #15 bin names:** not found at 14:15. `build/agent2/b4-dryrun-1404.txt` proposes devoffB4-bin and
   nativeB4-bin for the B line at the S4a level.
2. **What S4b holds:** C1 v2 and #26 are in (SESSION2 L2366), and #24 is granted (14:02). #18/#20 (Agent 1, 13:58), P2c
   and M1 are candidates. Drop the rows of anything left out.
3. **#26:** not staged or rated yet (Agent 9, due 14:50). G2 is its OFF test.
4. **M1:** G4 is pending, and M1 has no proof line.
5. **RN:** waiting for the re-run of S4a r5.
6. **Rows 14-15 (debug layer):**
   - They need the Windows "Graphics Tools" feature (d3d12SDKLayers.dll).
   - `d3d12_debug` is defined at `src/ui/d3d12/d3d12_provider.cpp` :23, with an ID3D12InfoQueue at :361.
   - Agent 3 checks that the messages reach game.log. If they don't, mark NOTE step 4 as not testable headless.
7. **An M1 arm in W6:** if Agent 5's W6 draft adds one, add one row: row 24 plus
   `shared_memory_upload_nontemporal_copy=true`.
