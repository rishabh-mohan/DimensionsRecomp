# RESUME.md draft-2 touch-ups (07:10): W5b pooled numbers, read-out times, rpm4 log, f10 dir, HANDOFF notes,
# Agent 1's fresh-clone check (cite its HANDOFF section 3), #19/#33 staged state, PENDING-DIFFS, export details.
# Gated on the 07:03 sha; each target must occur exactly once; LF only, no BOM; personal-details check; backup on apply.
import hashlib, re, shutil, sys, time
sys.stdout.reconfigure(errors='backslashreplace')
P = 'perf-notes/RESUME.md'
EXPECT = 'BA95FA199D8A364174AD9964A589C416A930F7850743584494444A4B8E3A15E4'
raw = open(P, 'rb').read()
sha = hashlib.sha256(raw).hexdigest().upper()
if sha != EXPECT:
    print('GATE FAIL sha', sha); sys.exit(1)
t = raw.decode('utf-8')

R = [
# 1 header
("This is draft 2 (Nov 23, 07:15). It has the formal read-outs of W6 and W4c (Agent 8) and W9 (Agent 7), Agent 12's gates, Agent 6's logdiffs and the four finding-10 rows. Agent 8's W9 read-out and the W5b read-outs are due ~10:00; they are folded in when they land.",
 "This is draft 2 (Nov 23, 07:12). It has the formal read-outs of W6 and W4c (Agent 8) and W9 (Agent 7), Agent 7's pooled W5b numbers, Agent 12's gates, Agent 6's logdiffs and the four finding-10 rows. Agent 8's W9 read-out and the W5b verdicts (Agents 7 and 8) are due ~10:00; they are folded in when they land."),
# 2 handoff pointer
("- `build/agent<N>/HANDOFF.md`: each agent's last notes before the pause.",
 "- `build/agent<N>/HANDOFF.md`: each agent's last notes before the pause. Read Agent 1's first: the git rules, the fresh-clone steps and the notes export."),
# 3 d11p in section 1
("    - the precise timer wait (d11p): ~0.2 core less (runner summaries; its read-outs are pending).",
 "    - the precise timer wait (d11p): −0.20 core [−0.23, −0.17] (−8%), with fps −0.7% [−1.8, +0.3] and no p99 or 1% low change (Agent 7's pooled W5b numbers; the verdicts are pending)."),
# 4 #19 staged
("  - #19 (`d3d12_async_submit`, a design);",
 "  - #19 (R1 stage 2, cvar `d3d12_async_submit`, off, kInitOnly): staged in `build/agent7/s4-r1s2/` (SDK, 5 files, +320/−1); its proofs P1-P10 pass; not rated yet, and no rate request is written;"),
# 5 #33 staged + PENDING-DIFFS
("  - #33 (the placeholder `d3d12_async_pipeline_no_wait`).",
 "  - #33, the pop-in opt-in: staged in `build/agent6/s33-popin/` as cvar `d3d12_pipeline_creation_no_wait` (default false, kRequiresRestart; SDK, 4 files, +105/−24), with a dropped-draw counter on the slow-frame line (#34's idea); not built or applied.\n  - Agent 2's list of the unbuilt diffs, with apply checks against HEAD: `build/agent2/PENDING-DIFFS.md`. Its status column dates from 06:30, so it predates #21's rating and the staged #33."),
# 6 not committed: harness
("- **`perf-notes/`, `bench/` and `build/`** (notes, scripts, matrices, results and bins).",
 "- **`perf-notes/`, `bench/`, `build/` and `harness/`** (notes, scripts, matrices, results and bins). They travel only through the notes export or a copy of the workspace."),
# 7 export
("  - Agent 1 stages an export in `build/agent1/perf-export/`. `export_perf.py` replaces the workspace path, other profile paths and the account name with placeholders. About 47 exported files mention the user's schedule, which is part of the same decision (SESSION2 L3327).",
 "  - Agent 1's export (`build/agent1/HANDOFF.md` §5): `python build/agent1/export/export_perf.py` is a dry run, and `--copy` writes `build/agent1/perf-export/perf/`. It replaces the workspace path, other profile paths and the account name with placeholders (07:02 run: 4529 files, 0 leftovers). About 47 exported files mention the user's schedule, which is part of the same decision (SESSION2 L3327). Nothing has been pushed."),
# 8 fresh clone
("   - The SDK's `.gitmodules` has no mapping for `thirdparty/FidelityFX-SDK` or `thirdparty/snapdragon-gsr`. So `git submodule status` fails there, and a fresh recursive clone probably fails too (untested; this predates the sprint).",
 "   - **A fresh clone works** (Agent 1, Nov 23, 07:04; the commands are in `build/agent1/HANDOFF.md` §3): clone `perf/opt` from the user's forks, init `rexglue-sdk` (its fork, `perf/opt` at 5350b1d), then fetch plume's pin and run the two prepare scripts as in steps 2-3. `git status` then matches the live workspace, and the 4 patched files are byte-identical to the live ones.\n   - The SDK's `.gitmodules` has no mapping for `thirdparty/FidelityFX-SDK` or `thirdparty/snapdragon-gsr`, so `git submodule status` fails there. Agent 1's test initialized only `thirdparty/simde` of the SDK's third-party trees; a full recursive init is untested and probably fails too (this predates the sprint)."),
# 9 plume gitlink
("2. **plume.** The game's gitlink (`ceaeeee`) isn't in the local plume clone, so `git submodule update` won't give a buildable plume.",
 "2. **plume.** The game's gitlink (`ceaeeee`) is in neither the local plume clone nor the public plume repo, so `git submodule update` fails (\"not our ref\"). Keep the gitlink as it is; don't commit a new plume pointer."),
# 10 plume pin
("   - Check out the prepare script's pin, `e0c8871`, in `DimensionsRecomp/thirdparty/plume`.",
 "   - Fetch the prepare script's pin, `e0c8871`, by sha and check it out in `DimensionsRecomp/thirdparty/plume`."),
# 11 build step
("5. **Build.** Release; the game for x86-64-v3, the SDK for x86-64-v2. Each staged bin in `build/agent2/<name>-bin/` has a `MANIFEST.txt`.",
 "5. **Build.** Release; the game for x86-64-v3, the SDK for x86-64-v2. The game also needs the game files and a recompile to regenerate `rexlego/generated`, which isn't in git (`perf-notes/agent3-build.md`). Each staged bin in `build/agent2/<name>-bin/` has a `MANIFEST.txt`."),
# 12 W5b row
("| **d11p: 0.20 [0.21] core less (−8%), fps unchanged in both passes.** d11t saves about the same but lost 0.8% fps in the second pass. Read-outs pending | **d11p** |",
 "| **Agent 7's pooled numbers (36 kept runs, both passes; the verdicts are pending): d11p −0.20 core [−0.23, −0.17] (−8.0%); median +0.5% [−0.9, +1.9], fps −0.7% [−1.8, +0.3]; no p99 or 1% low change.** d11t saves a little more (−0.22 core [−0.25, −0.19]), but its fps is −1.1% [−2.1, −0.0]. Both cut the TimerQueue thread's busy time from 23% to ~2%. Long frames (Agent 7's tail check): d11p had 6 frames over 8 ms in 12 runs (d11: 2) and none over 16.7 ms; d11t had 6 over 16.7 ms, all in one burst in run 0221-r5. The runner summaries said the same (d11p 0.20 [0.21] core less, fps unchanged) | **d11p** |"),
# 13 read-outs line
("W9 by Agent 7 (`build/agent7/readout/W9.md`, 06:45). Agent 8's W9 and the W5b read-outs (Agents 7 and 8) are due ~10:00 in the same folders.",
 "W9 by Agent 7 (`build/agent7/readout/W9.md`, 07:02). Agent 7's pooled W5b numbers are in `build/agent7/readout/pool-W5b.md` (07:02) and its long-frame check in `tail-check.md` (06:54). Agent 8's W9 and the W5b read-outs (Agents 7 and 8) are due ~10:00 in the same folders."),
# 14 d11p decision
("   - **d11p:** clean gates and logdiffs; the read-outs are pending.",
 "   - **d11p:** clean gates and logdiffs, and Agent 7's pooled W5b numbers back the lean (§5); the verdicts are pending."),
# 15 handoffs in step 0
("   - every agent's HANDOFF.md read.",
 "   - `build/agent1/HANDOFF.md` read, then every other agent's (at 07:10, those of agents 7, 8 and 11 weren't written yet)."),
# 16 no builds during timed runs
("   - **GPU warm-up for every window:** add discarded runs until `gpu.csv` shows the steady clock (5-13 minutes on this laptop), and rotate the first arm across rounds (W6.md L226).",
 "   - **GPU warm-up for every window:** add discarded runs until `gpu.csv` shows the steady clock (5-13 minutes on this laptop), and rotate the first arm across rounds (W6.md L226).\n   - **No builds on the machine during timed or hang-sensitive runs.** Finding 10's stall is host-side: 0 of 4 quiet runs hung, against 4 of 6 under a -j8 build (§6, item 3; `build/agent1/HANDOFF.md` §6)."),
# 17 rpm4 log
("and the 4-run matrix rpm4 (`build/agent3/runs/rpm4-20261123-0620`), PASS on every section 3(b) check",
 "and the 4-run matrix rpm4 (`build/agent3/runs/rpm4-20261123-0620`; check log `build/agent3/s4b/logs/rpm4.3b.txt`), PASS on every section 3(b) check"),
# 18 W7 / #19
("3. **W7 / item #19** (R1 stage 2: hand the submit to a worker, `d3d12_async_submit`). The design isn't rated yet.\n   - Steps: staging, Agent 10's rating, a build, then functional runs and a 10-minute soak.",
 "3. **W7 / item #19** (R1 stage 2: hand the submit to a worker, `d3d12_async_submit`). Staged in `build/agent7/s4-r1s2/` with its proofs, functional rows, soak plan and a draft W7 matrix; not rated yet.\n   - Steps: a rate request, Agent 10's rating, a build, then the functional runs and a 10-minute soak."),
# 19 pop-in
("   - Steps: implementation (Agent 6 proposed it), Agent 10's rating, a build and functional runs. Then the user judges the pop-in by eye.\n   - #34, a counter for the draws #33 drops, is optional.",
 "   - Agent 6 staged it in `build/agent6/s33-popin/` (DESIGN.md with its risks and test plan, `s33-popin.patch`, CHECK.txt), not built or applied (`build/agent6/HANDOFF.md`, open item 7). Its dropped-draw counter covers #34.\n   - Steps: Agent 10's rating, a build and the functional runs of DESIGN.md's test plan. Then the user judges the pop-in by eye at the visible desktop."),
# 20 launcher/readout pins on a new PC
("Copying or editing the scripts is fine before a launch; the next launch pins the new hashes.",
 "Copying or editing the scripts is fine before a launch; the next launch pins the new hashes. Re-pin the read-out kits too: their pins include binary and script hashes (`build/agent1/HANDOFF.md` §3)."),
# 21 f10 row in section 10
("| finding-10 and re-pin runs | `build/agent3/runs/`; `build/agent3/s4b/logs/` |",
 "| finding-10 and re-pin runs, the finding-10 results | `build/agent3/runs/`; `build/agent3/s4b/logs/`; `build/agent3/f10/` (RESULTS.md, f10-table.md) |"),
# 22 #19/#33 + PENDING-DIFFS rows in section 10
("| #21 (S4-T1) | `build/agent7/s4-t1/`; `build/agent10/t27/r21-s4t1.md` |",
 "| #21 (S4-T1) | `build/agent7/s4-t1/`; `build/agent10/t27/r21-s4t1.md` |\n| #19 (R1 stage 2), #33 (the pop-in opt-in) | `build/agent7/s4-r1s2/`; `build/agent6/s33-popin/` |\n| unbuilt diffs, with apply checks against HEAD | `build/agent2/PENDING-DIFFS.md` |"),
# 23 handoffs row
("| per-agent handoffs | `build/agent<N>/HANDOFF.md` |",
 "| per-agent handoffs (Agent 1's first) | `build/agent<N>/HANDOFF.md` |"),
]

fails = 0
for i, (o, n) in enumerate(R, 1):
    c = t.count(o)
    if c != 1:
        print(f'FAIL {i}: count {c}'); fails += 1; continue
    t = t.replace(o, n)
if fails:
    print('ABORT:', fails, 'failures'); sys.exit(1)

out = t.encode('utf-8')
assert b'\r' not in out and not out.startswith(b'\xef\xbb\xbf')
pat1 = re.compile(r'<user>|rishabh', re.I)
pat2 = re.compile(r'github|https?://|file:///|[A-Za-z]:\\|\\Users\\|/Users/', re.I)
for ln, line in enumerate(t.split('\n'), 1):
    if pat1.search(line) or pat2.search(line):
        print('PERSONAL HIT', ln, line[:120]); fails += 1
if fails:
    print('ABORT: personal-details hits'); sys.exit(1)

mode = sys.argv[1] if len(sys.argv) > 1 else '--dry'
if mode == '--apply':
    bak = f'build/agent11/resume/RESUME.{time.strftime("%H%M")}-{EXPECT[:8]}.md'
    shutil.copyfile(P, bak)
    open(P, 'wb').write(out)
    print('WROTE', hashlib.sha256(out).hexdigest().upper(), len(out), 'B LF', out.count(b'\n'), 'CR 0, no BOM; backup', bak)
else:
    print('DRY ok:', len(R), 'replacements; new size', len(out), 'LF', out.count(b'\n'))
