# Rating: M16 story-miss shader dump plan (Option A, `dump` word in M3's manual kit)

M10 (Agent 10 successor), 2026-11-26 03:25. Static review of a plan. No code has been delivered yet, and I ran nothing.

## Files

| file | sha256/16 | bytes | role |
|---|---|---|---|
| build\agent16\pack\PLAN-story-dump.md | F2E1638295613D7E | 7148 | the plan |
| build\agent3\gameplay\gameplay-run.ps1 | 7204852317BAFE96 | 25724 | base the §4 sketch applies to (live, mapfix) |
| harness\run-game.ps1 | C2533FDF | - | -Env splitter (read only) |
| DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp | - | - | mechanism (read only) |

## Base

The live M3 kit after mapfix (m3-mapfix-rating B1D6EE9C, G1/G2 closed): RUN-MANUAL 7BC9E5FF, RUN-EXPLORE 2B37AB02, RUN-GAMEPLAY F048275C, GPPIN_01 = 72048523.

## Verdict

**SAFE-IF D1-D6, for the plan and for M3's concrete delta kit.mapfix-to-dump.diff 6DE548E6** (see the last section). After install, the remaining evidence is the D1/D3 items (pincheck, tamper, dryruns), sent to me before any GO.

## What I checked

- **Mechanism, in shaders.cpp.**
  - L151 reads LEGO_DUMP_MISSING_SHADERS, and L583 uses it as the root.
  - L161/L192 implement the 256-container cap, and L197 emits the `missing_placement_shader_identity` event.
  - L236: capture forces the full path, i.e. the miss cache is OFF.
  - With the cache OFF, the `shader_miss_cache_insert` events (L364) disappear from the trace. The dump session's trace is therefore not comparable to 024219's on insert or miss-cache counts (see D4).
- **The env route works.**
  - gameplay-run.ps1 L175 is the only place the native env is built.
  - run-game.ps1 strips inherited LEGO_* vars (L185), and its -Env is split on ';' (L9, L77 Split-Items). So the `;`-joined `-Env` string in the §4 sketch works, provided no path contains ';'. $kit = $PSScriptRoot is absolute and has no ';' or spaces.
- **Word handling.**
  - L44 holds the known-word list; L45-46 refuse unknown words with exit 2.
  - The sketch adds 'dump' there and refuses `dump` without `manual` (exit 2), right after L48, before the first write at L71.
  - RUN-MANUAL.cmd always passes `manual %*`, so `RUN-MANUAL.cmd dump` gives the words "manual dump". RUN-EXPLORE/RUN-GAMEPLAY with dump would be refused.
- **Manual sessions don't run the post.** LATEST is written at L301 as "(no post)", so gameplay_post's missing-draws CHECK (which reads draw_missing_*) is not part of a manual session. M16's dump_post.py reads the identity events.
- **Correct "no piggyback on EXPLORE2" decision (§3).** It would need a re-pin of all three cmds, and the slowdown would confound EXPLORE2's prompt read-out.
- **Size.** Dumps are < 1 MB, and the trace size is unchanged (it is already on in the native arm). No pinned bin is written (R4): the dump root is outside the bin copy.

## Conditions

- **D1 (sequence):**
  - M3 prepares the diff in scratch only while EXPLORE2 runs. Nothing is installed before EXPLORE2 ends and I rate the delta.
  - The rating packet must contain:
    - the diff;
    - the candidate ps1 sha;
    - the 3 re-pinned cmds, with a swap-back proof that only GPPIN_01 changed vs 7BC9E5FF/2B37AB02/F048275C;
    - a 5.1 ParseFile result;
    - pincheck ×3;
    - tamper results;
    - the dryrun log shas.
- **D2 (code requirements beyond the §4 sketch):**
  - (a) Also refuse `dump` when no native trace arm is selected (`manual dump xenosonly`). Otherwise the word is a silent no-op.
  - (b) Prefer the dump root under `$runsRoot` (runs\shader-dumps-native-<stamp>) over the kit root. That keeps the kit dir clean, and a dryrun's dir is removed with dryrun-runs anyway. Either way, the dryrun must count a leftover dump dir as bad.
  - (c) Log `DIAGNOSTIC: dump on, timing invalid` and put `dump` into the L301 LATEST line.
  - (d) The value must be an absolute path with no ';'. Assert it in the script before launch.
- **D3 (tamper and dryrun must show):**
  - `RUN-EXPLORE.cmd dump` and `RUN-GAMEPLAY.cmd dump` exit 2 before any write.
  - `RUN-MANUAL.cmd dryrun dump` shows `LEGO_DUMP_MISSING_SHADERS=<abs>` in the run-game env line, with no dump dir left behind.
  - `RUN-MANUAL.cmd dryrun` (without dump) shows no such var.
- **D4 (keep the dump separate from the Toypad manual test; answer to the Overseer):** a combined session is acceptable only under these rules:
  - (a) Only after EXPLORE2 has confirmed all three prompts accepted (mapfix G4). If any prompt still fails, the next manual session is a Toypad debug session WITHOUT `dump`, to keep one variable.
  - (b) The Toypad verdict rests on the sidecar and LED evidence (LOAD → pulse stop) only, never on frame timing.
  - (c) If a prompt or hand move fails in a dump session, it is not conclusive: re-test without `dump` before any change to the mapping or the sidecar.
  - (d) The session's frames.csv, fps, worst frames and missing-draw counts are void for perf and for comparison with 024219: the miss cache is OFF, the pool-copy hashes add CPU cost, and there are no insert events. Mark the session DIAGNOSTIC in its notes.
  - (e) M3's ctl rules (a)-(i), the 1200 s cap, the hold file and the M1-M6 conditions still apply unchanged.
- **D5 (P1 and P2):**
  - The exe string scan must run at Idle priority, with no game running and not within ~6 min of a timed window.
  - It is read-only, and the result (found yes/no plus the exe sha8) goes into the packet.
  - One kit at a time, interactive desktop.
- **D6 (post):**
  - M16's dump_post is read-only on M3's dirs and writes only under build\agent16\dump\.
  - If the identity-event count is ≥ 256, report the capture as capped and incomplete; never pack from a capped capture without saying so.
  - Root create-path files (shaders.cpp:738) are flagged and not packed (as the plan says).

## Findings

- **NIT (was SHOULD on the plan):** the dump root is under the kit dir, not $runsRoot (D2b). I accept it in the concrete delta because the dryrun leftover check exists.
- **NIT:** the plan sketch didn't refuse `dump` with xenosonly (D2a). Fixed in the concrete delta.
- **NIT:** the plan's line numbers (shaders.cpp:146-207, :236, :521, :579-617, :738) match the source I read where I checked them (151, 161, 192, 197, 236, 583, 613). I did not re-read hooks_buffer.cpp:331-345.

## Concrete delta (M3, kit.mapfix-to-dump.diff), added 03:26

| file | sha256/16 | bytes | role |
|---|---|---|---|
| kit.mapfix-to-dump.diff | 6DE548E6953DB4CB | - | 4 files, +18/-6 |
| cand-dump/gameplay-run.ps1 | D97C9228422E1362 | 26874 | live 72048523 |
| cand-dump/RUN-MANUAL.cmd | 2B60C24FA9AF66C5 | 5689 | live 7BC9E5FF |
| cand-dump/RUN-EXPLORE.cmd | 6A0FE718993FFCFD | 5493 | live 2B37AB02 |
| cand-dump/RUN-GAMEPLAY.cmd | 134CBD48FCBC59EF | 5193 | live F048275C |
| scratch/test-dump-rgargs.txt | AC1ED6F0 | - | M3's Rg-Args unit test |

The candidates are in M3's brain scratch\cand-dump. All shas match the brief.

### What I checked

- **ps1.** Live vs candidate gives `git diff --numstat` 15/3, the same hunks as the diff file. LF only. PS 5.1 ParseFile: 0 errors.
  - 'dump' is added to $known.
  - `dump` without `manual` exits 2, and `dump` with `xenosonly` exits 2. Both checks come after the word parse and before the first write. This covers D2a.
  - Rg-Args adds `;LEGO_DUMP_MISSING_SHADERS=<kit>\shader-dumps-native-<stamp>` to the native arm's single -Env item only. The xenos arm gets no -Env (unit-test case).
  - Cmd-Line already quotes args that contain `;`.
  - A DIAGNOSTIC Say line and a LATEST suffix are added. This covers D2c.
  - In dryrun, a leftover dump dir counts as bad.
- **cmds.** Line by line vs live, each of the 3 differs only in GPPIN_01 (72048523 → D97C9228). Line counts are unchanged and the files are all CRLF.
- **Unit test.** test-dump-rgargs AC1ED6F0 ends "rgargs test: ALL OK":
  - no dump env without 'dump';
  - with dump, 2 env items in one -Env arg, and the dump root = kit\shader-dumps-native-<stamp>;
  - xenos: no -Env.

### Status of D2

- (a) Done.
- (c) Done.
- (b) Not taken: the dump root is the kit root, not $runsRoot. I accept this. It is a NIT now, because the dryrun leftover check exists, the root is absolute, and it is outside the bin copy.
- (d) No explicit assert, but the path is built from $PSScriptRoot (absolute; this WS has no ';' or spaces). NIT.

### Still required (D1/D3), after EXPLORE2 ends and before any GO

- Install exactly D97C9228 / 2B60C24F / 6A0FE718 / 134CBD48 and run pincheck ×3.
- The tamper test must include `RUN-EXPLORE.cmd dump`, `RUN-GAMEPLAY.cmd dump` and `RUN-MANUAL.cmd dump xenosonly`, each exit 2 with nothing written.
- Dryruns:
  - `RUN-MANUAL dryrun`: no dump var.
  - `RUN-MANUAL dump dryrun`: the run-game env line shows LEGO_DUMP_MISSING_SHADERS=<abs>, and no dump dir is left.
  - `RUN-EXPLORE dryrun`.
  - All must be ALL PASS, with the log shas sent to me.
- P1 (M16's exe string scan) per D5.
- D4 governs when a dump session may be combined with the Toypad test.
