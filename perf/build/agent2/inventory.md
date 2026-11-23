<!-- inventory:begin -->
**Build inventory** (generated 05:39 by `build/agent2/inventory.py`; sizes are file bytes in MiB/GiB (2^20/2^30 B, as Explorer shows them), bin file counts include MANIFEST.txt; delete nothing until Agent 1 or the user says so)

| Bin | Snapshot / patch level | exe sha256 (16) | MANIFEST sha256 (16) | Native GPU fingerprint | Disk size | What it is for |
|---|---|---|---|---|---|---|
| `build/baseline-bin` | pristine 127e04b + SDK 2897c31 (no sprint patch), OFF; staged 11-21 19:01 | FB922AC9E29D68F6 | 5A6845109D4DA919 | n/a (OFF) | 214.0 MiB (8 files) | reference: the unpatched game (perf and functional baseline) |
| `build/agent2/devoff1-bin` | S1, OFF (p1 and p2 touch only native files; p2 came after it); MANIFEST-S1-2041; staged 11-21 21:07 | D95273C99370D46B | 1E81AA5E0C8A4309 | n/a (OFF) | 214.2 MiB (8 files) | history: first dev OFF build (superseded by devoff2, devoff3) |
| `build/agent2/native-bin` | S1 + p1 device.cpp + p2 plume_d3d12, native; MANIFEST-S1-2041; staged 11-21 21:47 | 3B329E9550A1178C | 91F2F817B0D6D205 | befeb1184e6c7abc | 363.5 MiB (9 files) | history: first native build (superseded) |
| `build/agent2/devoff2-bin` | S2 (S1+p1/p2 + 18 rows), OFF; STATE-S2-2315, tag snap2; staged 11-21 23:18 | 7F0B1C1C84BC66FF | B87DC2D2CA22379F | n/a (OFF) | 214.3 MiB (8 files) | the A side of build B (devoffB vs devoff2); superseded by devoff3 |
| `build/agent2/native2-bin` | S2, native; STATE-S2-2315, tag snap2; staged 11-21 23:22 | 5D1B2DC655616027 | D6E7F14F23373FA7 | b7cc74f980e016c3 | 363.7 MiB (9 files) | history: superseded by native3 |
| `build/agent2/devoffB-bin` | B = S2 + codegen batch-nolr, OFF (snapB); STATE-S2-2315, tag snapB; staged 11-22 02:40 | C3F8686EBDD83340 | 8709476FF4778768 | n/a (OFF) | 198.3 MiB (8 files) | codegen option B; B gate PASS |
| `build/agent2/devoff3-bin` | S3 (game 001336f + SDK c5fe668 + plume/simde edits), OFF; also the OFF build of S3d/S3e (OFF builds skip draw.cpp); STATE-S3-0241, tag snap3; staged 11-22 02:44 | 2522D43605D8A9BF | B9C5175DA1904235 | n/a (OFF) | 214.3 MiB (8 files) | current dev OFF build |
| `build/agent2/native3-bin` | S3, native; STATE-S3-0241, tag snap3; staged 11-22 02:45 | 7F7F8586D219465C | B50FE8D4A16565DA | 8f849b69907d4006 | 363.7 MiB (9 files) | S3 native; the reference native3d was compared with |
| `build/agent2/native3d-bin` | S3d = S3 + Agent 4 draw.cpp 5EA1F357 (= game 08933a7 + SDK c5fe668 + plume/simde edits), native; STATE-S3d-0342, tag snap3d; staged 11-22 03:46 | B90DF683D0A57A21 | 368F9CE650EC56CE | 335ff2d47268f3a1 | 363.7 MiB (9 files) | current native build (n-rows PASS, 0 hash=0 lines in n0/n2/n3: Agents 8 and 10, 05:00); reference for nativeB |
| `build/agent2/nativeB-bin` | S3d + codegen batch-nolr, native (snapB3); STATE-S3d-0342, tag snapB3n; staged 11-22 04:34 | 01C4D5A3E36FAC50 | E5CBF30A6132B00E | 81d1c3a71be3c096 | 347.7 MiB (9 files) | codegen B on native: Agent 10's native-hook checks (1a static PASS, Agents 9 and 10; 1b route pair PASS vs native3d, Agent 10 05:24) and Agent 8's nativeB pair |

- Every exe re-hashed at 05:39: all 10 match their MANIFEST rows. Staged bins total 2.79 GiB. rexruntime.dll per bin is in `build/agent2/inventory.tsv`.
- Patch levels (applied to the snapshot `build/agent2/snap1`; rows in `PATCHES-S*.tsv`, listed in every MANIFEST): S1 = p1 device.cpp + p2 plume_d3d12.cpp; S2 = S1 + 18 rows; S3 = S2 + 28 rows = game 001336f + SDK c5fe668 + the uncommitted plume/simde edits; S3d = S3 + Agent 4 draw.cpp = game 08933a7 (same SDK and edits). B = Agent 9's codegen option batch-nolr (`build/agent9/install/batch-nolr`, 430 TUs). OFF = NATIVE_GPU=OFF, native = NATIVE_GPU=ON.

| Dir | Size | Files | Role | Could be deleted later? |
|---|---|---|---|---|
| `build/agent2/snap1` | 2.19 GiB | 25054 | snapshot of DimensionsRecomp at the current patch level (S3d); the base of every snapshot build and of snap-patch.py | no (keep) |
| `build/agent2/snap1-sdk` | 461.3 MiB | 2103 | SDK build + install of snap1 (rexruntime.dll, rexgpu-xenos.dll) | no (keep) |
| `build/agent2/snap1-off` | 634.7 MiB | 504 | OFF game tree of snap1 (devoff1/2/3) | no (keep) |
| `build/agent2/snap1-on` | 987.8 MiB | 596 | native game tree of snap1 (native, native2, native3, native3d, native3e) | no (keep) |
| `build/agent2/snap1-backup-S2` | 0.7 MiB | 16 | snap-patch.py apply backup: the snap1 files S2 replaced (for revert) | yes (S3d is accepted and committed: game 08933a7) |
| `build/agent2/snap1-backup-S3` | 0.4 MiB | 25 | apply backup of S3 (for revert) | yes (S3d is accepted and committed: game 08933a7) |
| `build/agent2/snap1-backup-S3d` | 0.3 MiB | 1 | apply backup of S3d (for revert) | yes (S3d is accepted and committed: game 08933a7) |
| `build/agent2/snapB` | 1.50 GiB | 24967 | snap1 at S2 + install/batch-nolr: the source of build B | yes, after the B decision |
| `build/agent2/snapB-off` | 592.4 MiB | 496 | OFF game tree of build B (devoffB) | yes, after the B decision |
| `build/agent2/snapB3` | 2.10 GiB | 24987 | snap1 at S3d + batch-nolr: the source of nativeB (and of the unbuilt rb1/rb2 rollbacks) | yes, after the nativeB checks / B decision |
| `build/agent2/snapB3-on` | 945.5 MiB | 588 | native game tree of nativeB | yes, after the nativeB checks / B decision |
| `build/agent2/codegen-frozen` | 0.3 MiB | 4 | codegen stand-ins (codegen-frozen/-frozen2.exe) used by every snapshot build | no (keep) |
| `build/agent2/codegen-tool` | 13.8 MiB | 3 | frozen rexglue.exe + DLLs (baseline / dev configure, codegen-watch) | no (keep) |
| `build/agent2/compat` | 0.0 MiB | 2 | CMake project include + native_lock_elide_compat.h, used by build-snap.ps1 | no (keep) |
| `build/agent2/live-backup` | 0.2 MiB | 1 | backup of my one live edit (plume_d3d12.cpp B88E4E86) | no (keep) |
| `build/agent2/gen-noflag` | 467.3 MiB | 887 | session-1 codegen output check (887 files); the pinned code is in baseline/ | yes (test output) |
| `build/agent2/c1-sweep` | 0.3 MiB | 141 | session-1 compile-one sweep outputs | yes (test output) |
| `build/agent2/cf2-test` | 0.0 MiB | 6 | task #1 codegen-frozen2 test | yes (test output) |
| `build/agent2/compile-one-test` | 0.1 MiB | 1 | session-1 compile-one test | yes (test output) |
| `build/agent2/nmtest` | 0.0 MiB | 19 | session-1 nm pipe test | yes (test output) |
| `build/agent2/ppcmap-test` | 2.6 MiB | 692 | step 6 PPC .map fix test (its logs are the evidence) | yes, after the report |
| `build/agent2/probe-toggle` | 3.0 MiB | 27 | session-1 find_package toggle probe tree | yes (test output) |
| `build/agent2/scratch-inc` | 0.0 MiB | 2 | session-1 scratch include test | yes (test output) |
| `build/agent2/recovered` | 0.1 MiB | 3 | notes recovered after a restart | yes (history) |
| `build/agent2/__pycache__` | 0.2 MiB | 12 | Python bytecode cache | yes |
| `build/agent2/notes-backup` | 0.5 MiB | 8 | backups of perf-notes/agent2-baseline.md | later (small) |
| `build/agent2/rbt-logs` | 0.0 MiB | 27 | tool test logs (rb-tools-test, S3e guard test) | later (small) |
| `build/agent2/B-diffs` | 0.1 MiB | 5 | review diffs (build B tools) | later (small) |
| `build/agent2/RB-diffs` | 0.1 MiB | 8 | review diffs (rb1/rb2/nb tools) | later (small) |
| `build/agent2/S3-diffs` | 0.0 MiB | 2 | review diffs (S3 tools) | later (small) |
| `build/agent2/S3d-diffs` | 0.0 MiB | 2 | review diffs (S3d tools) | later (small) |
| `build/agent2/S3e-diffs` | 0.0 MiB | 3 | review diffs (S3e tools) | later (small) |
| `build/baseline` | 634.2 MiB | 504 | baseline game build tree (the source of baseline-bin) | no (keep) |
| `build/sdk` | 473.1 MiB | 2741 | SDK baseline build; its compile_commands.json is compile-one's default DB and snap-gate uses it | no (keep) |
| `build/dev` | 9.0 MiB | 117 | session-1 NATIVE_GPU=ON configure of the live repo (compile-one -Db build\dev\...) | later, once no agent uses compile-one on it |
| `build/sdk-dev` | 29.7 MiB | 159 | session-1 SDK dev configure (configure only, tests ON) | later, if nobody uses its DB |
| `baseline` | 695.7 MiB | 3078 (+25 links not followed) | baseline snapshot (127e04b + SDK 2897c31); its rexlego/generated is the pinned generated code (the live repo junctions to it; gen-check reference) | no (keep) |
| `build/agent2/*.* (top-level files)` | 24.6 MiB | 270 | scripts, logs, rules, notes, PATCHES copies | later (small); keep the scripts |

- Total of the "yes" rows (could be deleted later): 5.56 GiB. build/agent2 in total (dirs, top-level files and its staged bins): 12.41 GiB. Free C: 244.4 GiB at 05:39.
- Not sized here: agent1, agent3, agent4, agent5, agent6, agent7, agent8, agent9, agent10, agent11, agent12 under build/ (the other agents' dirs; not mine to judge).
<!-- inventory:end -->
