# Agent 1 HANDOFF (orchestrator), 2026-11-23

Paths are relative to the workspace root, the folder that holds `DimensionsRecomp/`, `build/`,
`bench/`, `harness/` and `perf-notes/`. First version 07:10; updated 10:17 with the readout verdicts
and the wrap-up status. Final pass 12:35: the notes destination (section 5) and the final git state.
Updated 13:52: at 13:49 the user chose a public `perf/` folder in DimensionsRecomp for the notes
(sections 2, 3, 5 and 6).

Read in this order after the break: `perf-notes/RESUME.md` (sections 1 and 7 first), this file, then
`build/agentN/HANDOFF.md` for each agent (2-12). RESUME is the fuller document; where it and this
file differ on anything outside sections 1-3 and 5 here, RESUME wins.

## 1. What I own

- Orchestration of the 12-agent agy-grid. The board is `.agy-grid/board.md`; agy-grid rewrites it, so
  never edit it. Board task numbers continue from #35. These are grid task numbers; S4 item numbers
  (#19, #21, #33, ...) are a separate list (RESUME L7).
- Git. I am the only agent that commits or pushes (section 2).
- The night-launcher GO files (`build/agent1/night/`), the hold manager (`build/agent1/hold/`), the
  session log `perf-notes/SESSION2.md` and the notes export (`build/agent1/export/`, section 5).
- The decisions and board tasks that only I start after the break (section 6, items 1-4).

## 2. Git state and rules

| Repo | Branch | HEAD | Remote `mine` |
|---|---|---|---|
| DimensionsRecomp | perf/opt | b0bd3b4 "S4b/S4c: keep-watch memory_watch, GPU wait back-off hooks, probe option; SDK at S4b" | github.com/rishabh-mohan/DimensionsRecomp |
| rexglue-sdk (submodule of DimensionsRecomp) | perf/opt | 5350b1d "S4b: C1 v3 keep-watch, M1 non-temporal copy, P2 counter, r1r2, db16cyc_pause option" | github.com/rishabh-mohan/rexglue-sdk |

- Final check 11-23 12:31: both repos on `perf/opt` at these HEADs, equal to `mine/perf/opt`
  (`git ls-remote`); `git status` shows only the two expected entries below. No code commits after
  the 11-23 05:40 push.
- 11-23 afternoon: the notes export was committed on top of b0bd3b4 and pushed to `mine`. That commit
  changes only `.gitignore` (a `!/perf/` line) and `perf/` (section 5). b0bd3b4 stays the last code
  commit; the SDK is unchanged.
- Commit only in these two repos, on `perf/opt`, and push to `mine`. Never push to `origin` (the
  upstream NeverCookFirst repos), never to `main`, never force. Commit the SDK first, then the
  superproject gitlink. Confirm with `git ls-remote mine perf/opt`.
- SSH push without prompts: `$env:GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=20'`.
  PowerShell shows git's stderr progress as "NativeCommandError"; check `$LASTEXITCODE` instead.
- Never commit in the workspace root: it sits untracked inside an unrelated parent repo.
- Not in git, by design: `rexlego/generated` (recompiled game code), game data, logs, binaries, dumps.
  The DimensionsRecomp `.gitignore` ignores `/*` except listed folders; a new top-level folder needs a
  `!/name/` line.
- Uncommitted on purpose: ` M thirdparty/plume` and ` m rexglue-sdk` (its `thirdparty/simde`). Both
  are rebuilt from tracked files by `tools/gpu-aot/prepare_plume.py` (Plume pin e0c8871 + the
  `tools/gpu-aot/patches/plume-*.patch` files) and `rexglue-sdk/scripts/prepare_simde.py` (SIMDe pin
  71fd833d + `rexglue-sdk/patches/simde-native-m64-stream.patch`). `--check` verifies without
  changing anything. Do NOT commit the plume pointer: the upstream gitlink ceaeeee0 is kept as is.
- Agent 2's COMMIT-CHECK (`build/agent2/COMMIT-CHECK.md`): PASS. Tracked files = HEAD = index = the
  tested S4b source (`build/agent2/snap1`), re-checked 06:33.

## 3. Fresh clone (new PC), verified 11-23 07:04

Done from GitHub over https in a scratch folder outside the workspace:

```
git clone -b perf/opt https://github.com/rishabh-mohan/DimensionsRecomp.git
cd DimensionsRecomp
git submodule update --init rexglue-sdk                  # the fork, perf/opt at 5350b1d
git -C rexglue-sdk submodule update --init --recursive   # SDK thirdparty (large; the test did only thirdparty/simde)
git submodule update --init thirdparty/plume             # FAILS, see below; this creates the plume checkout
git -C thirdparty/plume fetch origin e0c8871b930dc1a6544bf457f2348c456b9d7e13
git -C thirdparty/plume checkout e0c8871b930dc1a6544bf457f2348c456b9d7e13
python tools/gpu-aot/prepare_plume.py                    # applies the plume patches; prints PASS with --check
python rexglue-sdk/scripts/prepare_simde.py              # applies the SIMDe patch; prints PASS with --check
```

- The plume step fails with `upload-pack: not our ref ceaeeee0...`: the upstream gitlink is not on the
  public zolaware/plume repo. Fetching the pin by sha works.
- Result: `git status` shows ` m rexglue-sdk` and ` M thirdparty/plume` (SDK: ` m thirdparty/simde`),
  the same as the live workspace. The 4 patched files are byte-identical to the live ones
  (plume_d3d12.cpp 564568D4, plume_d3d12.h 2F8B444C, plume_vulkan.cpp 71938A4C, simde/x86/sse.h DB31E25D).
- `DimensionsModManager` and `DimensionsSaveConverter` (upstream submodules) are not needed for the
  perf work.
- The game still needs the game files and a recompile to regenerate `rexlego/generated`; see
  `perf-notes/agent3-build.md` and the per-agent build notes. The workspace-side folders (`harness/`,
  `bench/`, `build/`, `perf-notes/`) are not in git as such: the clone has a scrubbed, text-only
  export of them in `perf/` (section 5; `perf-notes/` is `perf/notes/`). Binaries, logs and anything
  else the export leaves out travel only with a copy of the workspace.
- New PC: take new baselines before comparing anything with these results, and re-pin the launchers
  and readout kits (their pins include binary and script hashes). RESUME section 9 has the list.

## 4. Timed-window rules (for the next session)

- One-line GO file per window. The launcher refuses a GO on a sha, pin or arm mismatch, if the
  estimate + 10 min passes the window's end, or if it is read at or after the cut-off.
- Quiet gate: 3 quiet 1-minute samples before each window. It checks only at the start: in W5b's
  second pass, load came back about 6 minutes later and hit the first 4 scored runs. Follow the
  window hygiene in RESUME section 7, step 0 (from `build/agent7/readout/W5b.md` section 7).
- Pre-go self-match: never put the text of the runner script names into the command that runs
  pre-go; the process check matches command lines. Agent 10's N-4 is the same fail-safe effect: the
  07:33:42 SCRNSAVE install refusal matched an unrelated pid, and a re-run worked.
- SCRNSAVE: the 00:03:40 W6 refusal came from the launcher deleting `SCRNSAVE.EXE`, which made
  run-matrix throw under StrictMode (hand fix at 00:05:37). Agent 5's code fix (grid task #26) was
  installed at 07:33:57 on 11-23: `bench/agent8/run/run-matrix.ps1` 1A522CDF,
  `bench/agent5/launch/run-night.ps1` 565D30D4, launch README B7CEBD63. Post-install tests:
  test-scrnsave `-Set installed -E2E` 45/45, test-day 27/27, run-tests go group 16/16 (with the
  test-only `-StopAt`). Agent 10 checked them at 07:56 (`build/agent10/t27/scrnsave-delta.md`
  section 5).
- Pins: each launcher start re-hashes the pinned files and rewrites `status/pins.txt`
  (`run-night.ps1` L967, L973); nothing reads it back, so a script change needs no manual re-pin.
  Before the next window, re-run the plan-only staging (`build/agent8/HANDOFF.md`, open item 1).
- Day launcher: staged only, in `build/agent5/day-draft/` (run-day.ps1 B67EBD6C). Condition 1 closed
  at 07:56. Condition 2 (install into `bench/agent5/day/`) and condition 3 (Agent 11's rating, which
  I assign) wait until after the break (RESUME section 6, item 6).
- No builds on the machine during timed or hang-sensitive runs (finding 10, section 6, item 8).
- Caveats for comparisons: a Defender exclusion for `build/` was added on 11-22 at about 23:16, so
  compare with W4b/W5 and older only with a caveat. The night windows ran with the best_performance
  power overlay (the launcher never changed it); W4b and W5 ran best_efficiency.

## 5. Notes export

- `python build/agent1/export/export_perf.py` is a dry run; `--copy` writes
  `build/agent1/perf-export/perf/` plus `MANIFEST.tsv` and `EXCLUDED.tsv`. Run it at Idle priority.
- Text only, with size caps; no game assets, generated code, disassembly, binaries, dumps, raw
  per-frame data or copies of source files that are in git.
- Each copy is scrubbed: the workspace path becomes `<workspace>` and the account name `<user>`
  (plain, JSON-escaped and file:/// forms, and since 13:57 also profile paths cut off part-way
  through the name in truncated lines); a final pass counts leftovers. Run before the notes commit:
  4617 files, 39.9 MB, 8423 edits in 1418 files, 0 leftovers; 1 file flagged as disassembly and left
  out (`EXCLUDED.tsv`). Re-run `--copy` after any later change, before using it.
- The notes still mention the user's schedule in about 60 files; the user accepted that. At 13:49
  they chose a public `perf/` folder in DimensionsRecomp: the export is committed under `perf/` on
  perf/opt in the commit after b0bd3b4 (plus a `!/perf/` line in its `.gitignore`) and pushed to
  `mine`.
- To update it: re-run `--copy`, delete `DimensionsRecomp/perf/`, copy the new
  `build/agent1/perf-export/perf/` in, stage with `git add -A -- perf` (that path only; never the
  plume or SDK pointers) and commit on perf/opt.

## 6. Open items

Mine, after the break unless noted:

1. Notes destination: done. At 13:49 the user chose the public `perf/` folder, and the export is
   committed and pushed (section 5). Refresh it the same way before any later notes commit.
2. The native4b pin announcement (RESUME section 7, step 2). Agent 4's re-pin steps 0-4 passed;
   step 5 is my board announcement, and until then the native pin stays native4. After it, Agent 4
   fixes `build/agent4/repin/repin_check.ps1` in the order in `build/agent4/HANDOFF.md` L29-32.
3. Board tasks to assign first: Agent 10 rates #19 from `build/agent7/s4-r1s2/RATE-REQUEST.md`
   (1C2B8688, after the task #33 corrections; Agent 10's HANDOFF L72 still quotes the 08:40 rev);
   Agent 11 rates the day draft (RESUME section 6, item 6). Then follow RESUME section 7 in order.
4. Screenshot check: `build/agent4/screenshot-kit/README.md`, about 25 min, needs the user at the
   visible desktop. It didn't happen on 11-23 (no answer by 12:30), so it moves to after the break.

Other agents' items (details in RESUME section 6):

5. Keep/drop path: C1 on by default needs s4bLV and s4bV0 (or the verify-only fix); q500 needs one
   functional `LEGO_GPU_WAIT_STATS` run with sleep_fail == 0; then a confirmation window with the
   winners together (they were never timed together), then a final build with the kept defaults on.
6. #33 pop-in (opt-in, default OFF): Agent 10 rated it (`build/agent10/t27/r33-popin.md`): OFF SAFE,
   ON SAFE-IF 4 conditions. Build the first test bin without hunk #5 (patch L82-93;
   `build/agent6/s33-popin/DESIGN.md` section 8) and run diagnostic (d) before suggesting it
   (DESIGN.md section 9, item 5). The rated patch is `s33-popin.patch` 0D230244; nothing is built.
7. Unbuilt pending diffs: `build/agent2/PENDING-DIFFS.md` (640F3642, refreshed 10:15): CG26 arm A,
   #21 (rated) and #19 (rate request written, not rated).
8. Finding 10 is host-side: 0/4 hangs on a quiet host vs 4/6 under a -j8 build, p = 0.07
   (`build/agent3/f10/RESULTS.md`). Load is the likely trigger, not proven; not reproducing the hang
   doesn't fix it.
9. F-CA, a th2-only deadlock path that exists without #21 (`build/agent10/t27/r21-s4t1.md`), is
   recorded under MP4 gap 2 (`build/agent7/s4-t1/check/MP4-STATIC.md`). Check any th2 hang against
   it first.

## 7. Night of 11-22/23

Seven windows in `build/agent8/matrix/`: W6 20261123-0009, W9 -0108, W5b -0155, W4c -0239,
W6-2 -0313, W9-2 -0401, W5b-2 -0451. All 135 runs exited 0, with no hangs or dumps (Agent 6,
`build/agent6/wnight/RESULTS.md`); all 7 windows PASS the gates (Agent 12,
`build/agent12/w6-gates/NIGHT-RESULTS.md`).

Formal readouts, each recomputed by the other agent (they agree):

| Window | Readout | Verdict |
|---|---|---|
| W6 x2 | `build/agent8/readout/w-followup/W6.md` | Keep p2fc (P2 + fix (i) + C1 v3, verify off) vs s0: median -10.3 % [-13.6, -6.9], fps +18.0 % [+14.1, +22.0], -0.25 core. All of it comes from C1; p2 and p2f alone are null. Lead: heavy frames +2-3 %. |
| W9 x2 | `build/agent7/readout/W9.md` rev 1 | Keep q500: -0.75 core [-0.86, -0.64] (-30 %), no p99 or 1 % low loss. Drop q0. The q125/q250 wobble came from the host. |
| W5b x2 | `build/agent7/readout/W5b.md` rev 1 | d11p, narrowly over d11t: both save about 0.2 core (-8 %). d11t costs about 1 % fps over all runs, but not without the flagged runs. |
| W4c | `build/agent8/readout/w-followup/W4c.md` | Drop codegen B: +2.6 % [-1.2, +6.5], no gain. |

None of the winners is on by default. They were timed separately (W5b on S4a devoff4, W6 and W9 on
devoff4b). Not tested yet: a C1-only arm, p2fc with verify on, and the winners together.

## 8. Wrap-up, 11-23 morning

Grid tasks #20-#34; the board's closed list has each summary. HANDOFF sha256 prefixes as of 10:17.

| Agent | Grid tasks | State | HANDOFF |
|---|---|---|---|
| 2 | #28 commit check (PASS), #31 and #34 PENDING-DIFFS refreshes; old #1 DEFERRED | done | C3F02BF1 |
| 3 | #23 finding-10 quiet-host rows | done | 4BF508AC |
| 4 | #29 screenshot kit | done | 38CD991A |
| 5 | #26 SCRNSAVE fix, installed 07:33:57 | done | 488D14CA |
| 6 | #22 gate B dumpstacks and wrap-up; #33 rating recorded in DESIGN.md section 10 | done | 12797533 |
| 7 | #21 W9/W5b readouts; #32 rate request for #19; #33 doc fixes in s4-r1s2 (RATE-REQUEST now 1C2B8688) | done | AC4A9C93 |
| 8 | #20 W6/W4c readouts | done | 87F2675C |
| 9 | #30 handoff | done | 3F27B281 |
| 10 | #27 reviews (#21, #33, SCRNSAVE, day draft, RESUME) | done | 72E7E005 |
| 11 | #25 RESUME, final 7616A164 | done | 833CA243 |
| 12 | #24 night gates | done | E7BE1F44 |

Final state, 12:35: no open grid tasks and all agents idle. agy-grid has no stop command; nothing
runs until a new task is posted. My wrap-up cron is cancelled.
