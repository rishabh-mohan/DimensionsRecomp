# Agent 2: build pipeline - RESUME NOTE (board run 2; run-2 task #1 = old #28, S4b + S4c on the S3d line with C1 v3: devoff4b + native4b staged, CTR + CG26 wait for Agent 1's wake-up; updated 22:43)

**22:43 update:** native4b-bin STAGED 22:40:17 (task-277 exit 0, total wall 6425 s: configure 20:53:23, gen-check
886/886 PASS 5.3 s, gate PASS, native build = full rebuild 485 edges 20:53:30 -> 22:39:53 = 6400 s, slowed ~5x by Agent
3's Normal-priority game runs; stage 19 s, 8 files 363.8 MB). MANIFEST.txt 32559 B sha256 B63769FE46CC0459; exe
DC6484C224585E54 (315811328 B), map 03CBC65FEA77674C; xenos E3CB99CF + rexruntime A33801D1 (= devoff4b's); wav, ttf,
amd_fidelityfx, TracyClient = native4-bin's. MANIFEST 124 PASS / 0 FAIL / 46 NOTE; strings PASS; LEGO_GPU_WAIT_BACKOFF_*
absent from the native exe (ok). Native GPU fingerprint 9b40acbbef4c57b3 = Agent 4's step 1b
(`build/agent4/repin/dryrun-native4b-1b-2055.txt`, 0 FAIL / 0 WARN). Map check `s4b/checks/mapcheck-native4b.txt` PASS
(same mode vs native4-bin: 109 hooked, same names + objects; publics 358797 vs 358795). Subagent d5d1cb4d (22:42):
independent check + full-map diff -> `s4b/checks/sub2/mapcheck-native4b-sub2*.txt`, `mapdiff-native4b-vs-native4.txt`.
Told Agents 4 (pin step 3), 1 and 3 at ~22:44. Subagent result 22:53 (`sub2/mapcheck-native4b-sub2-vs-agent2.txt`
A31BAFA1BFB226DC: AGREE): hook-level same mode PASS (109, same objects); the +2 publics are C1 v3's new import pair
`?BlockPhysicalProtectKeepWatch@Memory@memory@rex@@SAXXZ` + `__imp_` (rexruntime.dll), plus a net-0 `__xmm@` swap in
pipeline_library.cpp.obj = the 16 ASCII bytes of the native GPU fingerprint (9b40acbb... vs 5e3ff55d...); its extra
check e) says FAIL only for that (benign). Perf note (verified, snap1 pipeline_recipes.h:247-256): native4b rejects
native-pso-recipes.bin / native-pso-seed.bin recorded with another fingerprint, so warm up both builds before an A/B.
**22:56 Agent 1: stopped for the night.** Open question from Agent 1 (I answered "unknown"): where do
native-pso-recipes.bin / native-pso-seed.bin (and native-pso.bin) live (per bin or shared), and does a start with a
mismatched fingerprint overwrite them at exit? When woken: a read-only grep of rexlego/src/gpu_native for
native-pso-recipes / native-pso-seed and the write path. CG26 is a relink of devoff4b's objects, so its fingerprint
constant (pipeline_library.cpp.obj) can't change; it stays devoff4b's. Remaining when Agent 1 wakes me after the windows (<= -j10): CTR
(~10 min), CG26 (~25-35 min unloaded), W5 re-hash, tell Agents 3/4/1, `@@done 1`. Nothing builds past 23:40.
Agent 1 (22:45): after the windows, Agent 3's two quiet-host L-route rows go first (~20 min), then CTR + CG26 at
<= -j10 when Agent 1 wakes me; stop at 23:50. Agent 9 (22:44): #18 kit `build/agent9/cg26-check/` (README.md;
cg26_check.py A179EB13, 14/14 tests OK); codegen budget 1.5-2.5 min (one thread). DELETE cg26's
`generated/default/codegen.stamp` BEFORE the regen (Agent 9, 22:49; the stamp then gets a fresh mtime). Source check
(snap1 SDK, 22:51): fingerprint = sdk version + flags + each input's file NAME + content hash (XEX, manifest, toml(s),
templates), not paths or mtimes (output_stamp.cpp:67-99), so a touch never forces a regen and a copied tree keeps its
fingerprint; codegen.stamp is WriteIfChanged, codegen.d + codegen.build.stamp are always rewritten, even when a module
is skipped as up to date (project_recompiler.cpp:358-375, 435-470). After my staging, run (my --out, since I own
only build/agent2/**): `if (Test-Path perf-notes\WINDOW-HOLD.txt) { 'HOLD'; exit 1 }; cmd /c start "" /belownormal
/wait /b python build\agent9\cg26-check\cg26_check.py --arm A --gen build\agent2\cg26\DimensionsRecomp\rexlego\generated
--ref build\agent2\snap1\DimensionsRecomp\rexlego\generated --config
build\agent2\cg26\DimensionsRecomp\rexlego\legodimensions_config.toml --tool build\agent2\cg26\tool\rexglue.exe
--tool-sha 9145166CDBEF5500E6E2607ED80AA6FC94CA1772DE2D3E87FF9E13BEAD87D586 --bin build\agent2\devoff4b-cg26-bin --out
build\agent2\cg26\checks\kit18; "exit $LASTEXITCODE"` (0 PASS, 1 FAIL, 2 INCOMPLETE, 3 HELD). Stage CG26 with
`cg26/stage-cg26.py [--dry-run]` (wraps stage-variant.py; MANIFEST notes name the tool, toml and 10 ON TU sha256s).

**20:55 update:** devoff4b-bin STAGED 20:49:07 (task-90 exit 0, total 3486 s: SDK + install 1360 s, game 2093 s incl.
gen-check 729 s + full rebuild 462 edges 1339 s at -j8). MANIFEST DE11A914079D7DF7, exe DFBE1D43B28861A6, rexruntime
A33801D1538D6175, xenos E3CB99CFDEA95E66, map 52155274A978A946; MANIFEST 102 PASS / 0 FAIL; strings PASS. Map check
`s4b/checks/mapcheck-devoff4b.txt` PASS (31 hooked by name + object); independent subagent map check (conv d5d1cb4d)
writes `s4b/checks/sub2/`. OFF logs copied to `s4b/logs-off/` (the native run appends to snap4b-run.txt/steps).
native4b: task-277 `run-s4b.ps1 -Stage native -C1 v3 -Jobs 8` from 20:53:11; configure 20:53:23, gen-check 886/886
PASS, gate PASS, `snap1-on/native-gpu-build.txt` = 9b40acbbef4c57b3 (= Agent 4's), build 485 edges from 20:53:30.
cg26 toml already = new-A (11707872, 20:54:29). stop-snap.ps1 now also kills run-s4b/prep-s4b/recompile/relink/
stage-variant and ctr/ + cg26/ orphans. Next: native4b staged -> tell Agents 4, 1, 3 -> CTR -> CG26 -> `@@done 1`.

**22:30 update (Agent 1, ~22:28):** after native4b's staging start NO new build tonight; CTR and CG26 move to after
tonight's windows (<= -j10, when Agent 1 wakes me). Agent 3's back-to-back game runs (Normal priority, from 21:09)
starve the Below Normal native build: 424/485 at 22:26 (~2-3 edges/min). Done meanwhile: subagent map check of
devoff4b (own parser) PASS, full-map diff clean (`s4b/checks/sub2/`); the exe now imports VCRUNTIME140_1.dll (CRT
tlsdyn.obj, S4c thread_local) but rexruntime.dll already did in devoff3/devoff4/native4 (`s4b/checks/pe-imports-2113.txt`).
cg26-check.py fixed (Agent 9, 22:15): codegen.build.stamp = codegen.stamp's "fingerprint" (snap1 58c23c7e...), now
checked as == the new fingerprint + fingerprint changed + outputs list (883) unchanged; self-test
`cg26/checks/selftest-stampfix.txt` behaves as expected. `holdrun.py` (HOLD-aware runner, for the codegen) tested.
Resume recipe (when woken): HOLD check; CTR = recompile.py x2 (`ctr/list-ctl.tsv`, `ctr/list-on.tsv` +
`--define REX_D3D12_DEFERRED_COUNTERS=1`, `--obj-filter /Release/`, snap1-sdk ccdb) -> relink.py x2 (SDK DLL edge,
compare ctl with devoff4b-bin's xenos) -> stage-variant.py -> devoff4b-ctr-bin. CG26 = holdrun.py + absolute
`cg26\tool\rexglue.exe codegen legodimensions_manifest.toml` (cwd cg26/DimensionsRecomp/rexlego) -> cg26-check.py
--stage -> recompile.py x2 (snap1-off ccdb) -> relink.py x2 (ctl compare with snap1-off exe/map) -> map check (same
mode vs devoff4b) -> stage-variant.py -> devoff4b-cg26-bin.

**Run-2 task #1 status 20:40** (Agent 1 'go' 19:31; -j8 max, Below Normal, >= 4 GB free RAM; HOLD check before every
command; builds done before ~23:40; the 20:17-20:23 hook failures were machine overload, retry rule unchanged):
- 19:49 prep dry run `build/agent2/prep-s4b-dryrun-1949.txt` 91 PASS / 0 FAIL; run-s4b -DryRun exit 0; 19:50 prep apply
  `prep-s4b-apply-1950.txt` (16 files; verify 23844 files / 15 backups / 0 problems PASS); tree check (subagent)
  `s4b/checks/tree-check-2007.txt` PASS; report paths sent to Agent 10 at 20:15.
- task-90 `run-s4b.ps1 -Stage off -C1 v3 -Jobs 8` from 19:51:02: SDK full rebuild 223/223 exit 0 (1263 s, slowed by
  Defender), install OK 20:13:45, game configure 4 s, gen-check 729 s (overload), gate PASS, game build = full rebuild
  (462 edges; SDK headers changed) from 20:26:18; then the driver stages devoff4b-bin and compares.
- Checks ready: `s4b/mapcheck-s4c.py` (self-test: same-mode PASS, negative FAIL as expected), `s4b/rehash-w5.py`
  (20:35 PASS: 27 W5 rows + devoff3-bin/devoff4-bin unchanged, `s4b/checks/w5-rehash-2035.txt`), `stage-variant.py`.
- CTR: `ctr/list-ctl.tsv`, `ctr/list-on.tsv`; recompile.py dry runs OK (`--obj-filter /Release/`); relink.py dry run OK
  (DLL edge, input 35 replaced; no PRE_LINK / .def).
- CG26: `cg26/tool` (rexglue.exe 9145166C, rexruntime.dll A33801D1), `cg26/DimensionsRecomp/rexlego` (manifest
  7F0106F4 with file_path 5 levels up, config 7F775847, generated/ = robocopy of snap1's 887 files), `cg26/cg26-check.py`
  (self-test on the copy: 0 differing; the pinned db16cyc sites per TU = the expected 20). Next: copy the new-A toml
  (11707872), run `..\..\tool\rexglue.exe codegen legodimensions_manifest.toml` in cg26/DimensionsRecomp/rexlego,
  `cg26-check.py --stage`, recompile 2 x 10 TUs (snap1-off ccdb), relink ctl (compare with the snap1-off exe/map) + ON.
- Agent 4: expected native4b fingerprint 9b40acbbef4c57b3; tell Agent 4 when the native configure is done and when
  native4b-bin is staged.
- After devoff4b: message Agents 3 + 1 (gates, map 31, W5 re-hash), then native (nativecfg, then native at -j8) ->
  CTR -> CG26 (stage-variant.py) -> `@@done 1`.

# (older) RESUME NOTE (board run 2; task #28 S4b + S4c on the S3d line: prep in progress, waiting for Agent 1's 'go'; updated 17:09)

**Task #28 (board run 2, from Agent 1): S4b + S4c on the S3d line, start at Agent 1's 'go' (after W5, or 17:10 if
W5 doesn't start).** Window rule: before 'go' file tools only (no run_command, no subagents); while
perf-notes/WINDOW-HOLD.txt exists no tool calls at all; after 'go' check HOLD before every command, and if it appears
during the build stop ninja within 2 min. Order: C1 v3 (keep-watch-v3 DECCFE33, then rexlego 4D0C1079 = memory_watch.cpp
by the staged after-file 70829846, CRLF, mtime = now) -> M1 -> P2c -> r1r2 -> #26 tool, option OFF (db16cyc-pause.diff
AC554DBB) -> S4c (s4c-24-30.diff DC02104E, fallback s4c-24-only.diff A279DC71; #24 + #30 both OFF). -j10 max, Below
Normal. Bins: devoff4b, native4b, devoff4b-ctr, and devoff4b-cg26 only if Agent 10's #26 gates hold (toml line + new
tool in one build; exactly 20 pauses in the arm's 10 TUs; codegen.partition.json kept). Checks: map by name and object,
not address (27 -> 31 hooked aliases, build/agent9/s4/fence-wait/s4c/expected-map.txt); the S4c TU 01D9F8F3 (LF) or
34D281E0 (CRLF); re-hash build/agent1/w5/W5-INPUTS-1642.txt (devoff3-bin and devoff4-bin unchanged). Then message
Agents 3, 4 and 1, and `@@done 28` (bins + MANIFEST hashes, build times, checks, W5 re-hash). B4 stays deferred.
Subagents (max 2, read/stage/check only): a read of the composed tree vs the staged after-files; the map check.
- **Status 17:09** (Agent 1 announced an agy-grid restart; nothing of mine is running; no 'go' received yet):
  - DONE (file tools only): `build/agent2/s4b-compose-check.py` rewritten 17:03 (479 lines): the #26 SDK step in both
    orders (o1 C1 -> M1 -> P2c -> r1r2 -> #26, o2 C1 -> M1 -> r1r2 -> P2c -> #26); S4c as the last step [6] (`--s4c
    24-30|24-only|both`, default 24-30: CMakeLists 3690D5D7 -> 1BF46D78 / 9A4606A7, TU 01D9F8F3 or 34D281E0, the #30
    option OFF, the #24 block under `if(NOT LEGODIMENSIONS_NATIVE_GPU)` with LEGO_GPU_WAIT_HOOK_GETDATA=1); live ==
    snap1 is now required (S4a is live: SDK 3bb65bb, game 1bd322e). Not run yet.
  - TODO at 'go': (1) HOLD check, then `python build\agent2\s4b-compose-check.py --c1 v3`. (2) Write `prep-s4b.py`
    (from prep-s4a.py: base = newest STATE-S4a-*; C1 v3 / M1 / P2c / r1r2 / #26 git-applied to scratch copies of the
    snap1 SDK files; memory_watch.cpp by the staged after-file copy; S4c CMakeLists + the new TU (its STATE row gets
    '-' live columns, PATCHES before 'ABSENT'); mtime = now on every copy; `--dry-run`) and `run-s4b.ps1` (from
    run-s4a.ps1: SDK build + install, devoff4b, native4b with configure; stage-snap-bin -PatchTagList
    S1,S2,S3,S3d,S4a,S4b; Below Normal; HOLD watcher), dry-run both with -C1 v3, send the reports to Agent 10.
    (3) CTR helper (deferred_command_list.cpp with -DREX_D3D12_DEFERRED_COUNTERS=1, rexgpu-xenos.dll relinked in a
    scratch dir) and the CG26 / G2 helpers. (4) Open: an S4b SDK build in place changes snap1-sdk/install, which
    snapB-off / snapB3-on link (B4 deferred): clone snap1-sdk first (0.45 GiB) or accept; ask Agent 1.

**Task #15 (board run 2, from Agent 1, 13:45): post-W4b prep, no builds. DONE ~14:20 (`@@done 15`). (1)
`build/agent2/apply-s4a-live.ps1` for Agent 1 (`-Go` after W4b): dry run 13:51 exit 0, 6/6 PASS
(`apply-s4a-live-dryrun-1351.txt`). (2) B line + S4a = devoffB4 + nativeB4: plan + `build/agent2/b4-dryrun.py` (14:24,
0 FAIL / 0 WARN, `b4-dryrun-1424.txt`; its new [10] simulates stage-snap-bin's -GameSnap gate, so option B copies 35
files into snapB, not 4): ~7-9 min at -j10 (devoffB4 option B), ~0.55 GiB, no SDK build; build B4 while
snap1-sdk/install is still S4a. (3) Deletable list: ~1.74 GiB always, ~6.8-7.4 if S3d wins, ~3.3-4.1 if B wins; nothing
deleted. (4) S4b draft + `build/agent2/s4b-compose-check.py` (14:32 `--c1 both`, 0 FAIL, `s4b-compose-1432-c1both.txt`):
C1 -> M1 -> P2c -> r1r2 applies in both P2c/r1r2 orders to the same files (command_processor.cpp 027204B5 = Agent 10's
composite). C1 is one variable, S4B_C1 = v2|v3, that Agent 1 sets at build time (v3 = keep-watch-v3 DECCFE33 if Agent
10 rates it SAFE first, else v2 = keep-watch-v2 418D3D39; Agent 10 rated v3 SAFE at ~14:38, b2r row 36 / S35, so v3
is expected at GO); the v2 and v3 finals differ only in xmemory.cpp (DC23757A /
BCA5E1CF), and the rexlego step is the same for both. memory_watch.cpp (CRLF) lands by copying the staged after-file
70829846. Every file a driver copies gets mtime = now after its hash check (Agent 1, 14:41; section 4). Details: section "Task #15" below, before
"S4a (task #4)"; (5) the S4b bin names for Agent 7's queue (`<S4B-OFF>` etc.) are in its section 5. Agent 1 (~13:58):
notes and dry runs until 15:00, then nothing until Agent 1 says W4b is done. Nothing of mine is running.**

**Task #4 (board run 2, from Agent 1): build S4a = devoff4 + native4, every new switch OFF; I am the only builder
(-j10 max). Windows Update restarted the PC at 08:29-08:34 and ended every session; recovery was done before this
task (git fsck clean, game 08933a7, SDK c5fe668). Base: the S3d line (the snap1 trees behind devoff3-bin and
native3d-bin). S4a = S3d + #7 u diag, #8 P2, #5 fix (i), #38 precise wait (4 new cvars, all default false) and #32
warm boot (always on, no switch; Agent 10: output-identical, SAFE) in the SDK, + #2 miss cache (rexlego
gpu_native/shaders.cpp) in native4 only. Left out: C1 (#4: xmemory.h = full rebuild), the #24 hook, the P2 counter,
#18/#20, #26. Built in place, no clone: no W4b input links into the snap1 trees (single hardlinks, staged bins are
copies, no snap1 refs in bench/agent8 or harness). Caveats: snapB-off/snapB3-on link against snap1-sdk/install, so a
future B-line rebuild picks up the S4a SDK (incl. the always-on #32); snap-patch plans against STATE-S4a show these
6 files as live != snap1 until Agent 1 applies them live. Prep (`prep-s4a.py`): dry run 13:21 49/49 PASS, apply
13:24:57 all PASS, `snap-patch.py verify S4a` PASS. devoff4: DONE 13:31:43 (371.2 s), `build/agent2/devoff4-bin`,
MANIFEST 16DCC939..., 81 PASS / 0 FAIL / 54 NOTE; announced to Agents 1, 3, 6 and 10 at ~13:34. Agent 6 (13:34): the
snap1 pipeline_cache.cpp passed its one-line check against live (only L564; `build/agent6/s10-2/linecheck-1331.txt`).
Agent 10 (~13:41, its task #12 item 1): the S4a apply record is ALL PASS (b2r row 30/§29): in all 6 rows before =
live = the rated base and after = snap1 = its own strict apply; #32 changes exactly L564. For C1 later (Agent 10):
keep-watch.diff applies to S4a snap1 byte for byte; keep-watch-rexlego.diff is LF-only but memory_watch.cpp is CRLF,
so keep the CRLF (the file must hash 70829846... afterwards), else copy the staged new/ file.
native4: DONE 13:38:35 (333.2 s), `build/agent2/native4-bin`, MANIFEST 00D33D4F..., 107 PASS / 0 FAIL / 38 NOTE,
native GPU fingerprint 5e3ff55de10f4f64 (native3d: 335ff2d47268f3a1); announced to the same four at ~13:42. No builds
after 13:38:35. The live DimensionsRecomp and
rexglue-sdk trees are untouched (Agent 1 applies and commits after the functional checks). Hard stops: builds 14:00
(run-s4a refuses to start from 13:50), last game launch 14:15 (Agent 3 only), games closed 14:20, notes only
14:20-14:30, then nothing until Agent 1 says W4b (timing window 4, when the user is back ~14:50) is done. Details:
"S4a (task #4)" section below, before "S4 estimate".**

**Task #1 is DONE (`@@done 1` about 03:05). Task #14 (session 3 part 2): step 1, S3d -> `native3d-bin`, is DONE and
staged (03:46; hashes posted to Agents 1, 4, 8 and 10; Agent 1 re-hashed: match). Step 2, the B rollback, is NOT
needed (Agent 10's tie-break cleared B; rb1/rb2 stay prepared and unbuilt). Step 3, nativeB: DONE,
staged 04:34:06 as `nativeB-bin` (`rb-chain.ps1 -Variant nb -Jobs 10` from 04:12:09, once Agent 9 had acked the
-GuardOnly diff (04:06) and Agent 8's last -Profile run had ended (04:09:51)); 149 PASS / 0 FAIL / 34 NOTE; hashes
posted to Agents 1, 8, 9 and 10. Task #14 is DONE (`@@done 14` at 04:37). Agent 8's idle-machine window (04:41 to
~05:50: s0-s2, native3d, the nativeB pair, attract + Agent 3's warm devoff3 run) gave me its all-clear at 05:38 for
the inventory run (done 05:39:16, 7.8 s). Then S11, the reverse-order native pair, Agent 11's throttling pairs and
maybe an attract re-run; then (Agent 8, 06:19) #25 base 06:33 to ~06:52, q to ~07:15 if its gate passes, maybe
Agent 5's a-vol; hard end 07:30. Agent 8 messages me when the last run ends (the build all-clear), and gives a gap
between runs if a build gets a GO first. Agent 1 (05:31): while a game runs (Agent 8's queue until
about 07:15), no recursive searches or scans of the SDK, DimensionsRecomp or build trees; targeted reads
only, <= 2 threads. Agent 1 (05:55): 06:33-07:15 are Agent 8's attract scenes on an idle machine: no builds or
compiles, no recursive searches, no reads over ~100 MB, batched tool calls, 1 thread (I have nothing pending).
Agent 10 (06:19): the reversed-order 1b tie-break passes every must-match item again; only the front-end exit
timing is reopened (nativeB leaves ~12 s earlier on native; not a fail item, no rollback); Agent 1 picks (a)
accept, (b) diff the fade code's codegen snap1 vs snapB3, or (c) more runs. No builds
or game runs from 08:30 (window 4 waits for the user, asleep until about 10:00; questions go to Agent 1). Only
Agent 2 builds (<= -j10). Nothing of mine is running.
Standby (Agent 1, 04:39): at most one more native build before 08:30, S3e -> `native3e-bin` (Agent 4's `|| !vs`
draw.cpp variant), only if Agent 8's native3d rows (~05:03) still show hash=0 lines and only at Agent 1's explicit GO
with the new draw.cpp sha256. It is prepared, not built (S3e section below; Agent 9 OK at 05:00). Agent 1
(04:55): the GO needs Agent 4's read of the native3d rows (~05:02) and its step 1, Agent 10's SAFE, Agent 9's OK of
the S3e diffs, then Agent 1's GO with the sha; start only after Agent 8's window (~05:50), never after 06:45.
05:00, Agent 8: the native3d rows show 0 hash=0 lines (n0, n2, n3), so the native3e trigger is NOT met; S3e
stays prepared and unbuilt unless Agent 1 says otherwise.
Agent 1 (05:05): native3d passed; draw.cpp is committed as game 08933a7 (pushed); NO S3e/native3e tonight; keep
the S3e tools unused for S4. Checked 05:06: 08933a7 changes only draw.cpp against 001336f (+5 lines), and its blob
(cbf8567d) == snap1's and live draw.cpp (checkout 5EA1F357, 306,557 B), so S3d == game 08933a7 + SDK c5fe668 +
the uncommitted pre-sprint plume and simde edits. "Build inventory" (Agent 1, 04:39, due 06:30): DONE at 05:39,
inserted by `python build/agent2/inventory.py --insert` (all 10 exe re-hashes match their MANIFEST rows, 0
problems): staged bins 2.79 GiB; build/agent2 in total 12.41 GiB; the "yes" rows (could be deleted
later) 5.56 GiB (5.1 GiB of it the snapB/snapB3 trees, after the B decision); free C 244.4 GiB. The tables are
just below, also in `build/agent2/inventory.md` and `.tsv`; re-running the same command refreshes them (it
replaces the block between the inventory markers; a full run walks the build trees, so only when no game runs).
Delete nothing until Agent 1 or the user says so.**

**Task #30 (Agent 11, 06:49): build-time and disk estimates for the first S4 batch, for `perf-notes/S4-DRAFT.md`
(Agent 11's `@@done 30` is due 08:15). Estimates only, nothing built: section "S4 estimate (task #30)" below, done
07:08, from `build/agent2/s4-estimate.py` -> `s4-estimate.txt` (read-only ninja log/deps analysis); the summary line
went to Agent 11. Agent 1 (~06:56): no builds and no new bin dirs tonight (S4 is not built tonight; Agent 4's s35 pack
stays on scratch, no bin); reads and estimates are OK at <= 2 threads; tell Agent 1 before starting anything else;
from 08:30 notes only. Agent 8: its last run ended 07:00:02 and its slot is over. Standby: nothing of mine is running,
no timers; window 4 waits for the user (~10:00). Agent 1 (07:08): C1 staging went to Agent 12, so no task for me
tonight; answer Agent 11 by message; no builds or bin dirs.**

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

**Staged bins** (in `build/agent2/`; file counts exclude MANIFEST.txt; MB here = MiB, 2^20 B; MANIFEST = PASS/FAIL/NOTE counts, sha256)

| Dir | Staged | Files, size | MANIFEST | exe sha256 | Notes |
|---|---|---|---|---|---|
| `devoff1-bin` | 21:08 | 7, 214.2 MB | all PASS, 1E81AA5E... | D95273C9... | S1 OFF |
| `native-bin` | 21:48 | 8, 363.5 MB | 48/48, 91F2F817... | 3B329E95... | S1 native, fingerprint `befeb1184e6c7abc` |
| `devoff2-bin` | 23:18:53 | 7, 214.3 MB | 49/49, B87DC2D2CA22379F... | 7F0B1C1C84BC66FF... | S2 OFF; map 3A7BEEF03A527FC4... |
| `native2-bin` | 23:22:38 | 8, 363.7 MB | 72/72, D6E7F14F23373FA7... | 5D1B2DC655616027... | S2 native, fingerprint `b7cc74f980e016c3`; map 1FFB7EA997DFCBE7... |
| `devoffB-bin` | 02:40:30 | 7, 198.3 MB | 74/0/19, 8709476FF4778768... | C3F8686EBDD83340... | B = S2 + batch-nolr, OFF; map 44332E6C8E68508B... |
| `devoff3-bin` | 02:44:18 | 7, 214.2 MB | 73/0/47, B9C5175DA1904235... | 2522D43605D8A9BF... | S3 OFF; map CE2836A0574BDB56... |
| `native3-bin` | 02:46:01 | 8, 363.7 MB | 96/0/33, B50FE8D4A16565DA... | 7F7F8586D219465C... | S3 native, fingerprint `8f849b69907d4006`; map F96136D0A323980E... |
| `native3d-bin` | 03:46:18 | 8, 363.7 MB | 103/0/34, 368F9CE650EC56CE... | B90DF683D0A57A21... | S3d native (S3 + Agent 4's draw.cpp 5EA1F357...), fingerprint `335ff2d47268f3a1`; map 1C9AB7E3E471A6BA... |
| `nativeB-bin` | 04:34:06 | 8, 347.7 MB | 149/0/34, E5CBF30A6132B00E... | 01C4D5A3E36FAC50... | nativeB = S3d + batch-nolr, native (snapB3), vs native3d-bin; fingerprint `81d1c3a71be3c096`; map C9259B05689E3AA5... |

- rexruntime.dll / rexgpu-xenos.dll: S1 FDB315DC... / BFE1DF8B...; S2 and B 1C45C86977EC594C... / 77A5300B885C5274...;
  S3, S3d and nativeB D1D66AC3716835AC... / EE0A661FB0C30FCB... (the S3 SDK rebuild relinked xenos too; S3d did not rebuild
  the SDK). No staged bin has PDBs.
- Boots (Agent 8's slot): devoffB and devoff3 PASS (`runs/0247-devoffB`, `runs/0254-devoff3`); native3 PASS (Agent 7,
  03:02: frontend on, no throw, bilinear present; exe, rexruntime, fingerprint and fix-a rows match; `runs/0256-native3`).

**Build B (DONE)**
- `b-chain.ps1 -Jobs 10`, 02:21:07-02:40:31, 1164 s (build 1060 s): verify S2 PASS; prep-b gen-check 870/870; pins
  SHA256SUMS 24CE1493FB8DAE37... / config E60EAF1CEB575572...; gate 432 PASS; stage 0 FAIL.
- snapB = snap1 at S2 + `build/agent9/install/batch-nolr` (never `install/batch`); its `rexlego/generated` is a real
  dir and every write stays under snapB; `codegen-frozen2.exe`. CompareBin vs devoff2: exe differs, map NOTE, the
  other 5 identical.
- Agent 9: review ok (02:25); static check PASS (`build/agent9/logs/mapcmp-AB.txt`: same 164,786 sub_ functions and
  27 hooked aliases; .text 159.3 -> 142.6 MB, -10.52%; 19 warnings, as snap1). Rollback copies are in
  `build/agent9/repin/`, for use only after a gate FAIL and Agent 1's GO.

**S3 (DONE; Agent 1 approved step 3 at 02:47)**
- Inputs: game `001336f` + SDK `c5fe668` (from Agent 10's 4 hashes: 11DE333F rex_app.cpp, 4331A312 audio_system.cpp,
  4EC71328 settings_registry.cpp, 9CBE6DBF settings_preferences.cpp) + the pre-sprint plume/simde edits, as in
  S1/S2. Recorded in the PATCHES-S3.tsv / STATE-S3 header lines and in each MANIFEST (`S3-notes.txt`). Generated code
  = the pinned S1 output; batch-nolr only in B.
- Agent 10's `build/agent10/s3/S3-include.tsv` (A1E7C83F..., 28 INCLUDE / 0 EXCLUDE vs STATE-S2-2315) ->
  `S3-rules.txt` -> `snap-patch.py apply S3 ... --note-file=build\agent2\S3-notes.txt` at 02:41:38: COPY 28 (3 new),
  DELETE 0, HELD BACK 0, errors 0. PATCHES-S3.tsv 2DA2AB6C...; STATE-S3-0241.tsv 4F791C2E80594C03...; verify S3 PASS.
- devoff3: `run-s3.ps1 -Stage off`, 02:42:07-02:44:19 (SDK build + install + game 113.6 s, stage 16.1 s). native3:
  `run-s3.ps1 -Stage native` (with configure), 02:44:40-02:46:03 (build 51.8 s, stage 27.6 s). MANIFEST patch rows
  S1 2 / S2 18 / S3 28.
- Checks: both exes contain 'which can hang when the guest pauses'; native3 has the 3 LEGO_NATIVE_* toggles;
  rexruntime has audio_shutdown_detach_worker; native3's MANIFEST lists settings_registry A37337001EBDC277 ->
  4EC71328043FA6BA and settings_preferences C78112AA6E50F79D -> 9CBE6DBF9CEDA62D. The fingerprint changed because it
  hashes 271 inputs (`snap1-on/generate-native-gpu-fingerprint.cmake`), including both settings files and draw.cpp.
- snap1-off `compile_commands.json`: 477 entries, 0 gpu_native files, so draw.cpp is not in OFF builds and devoff3
  stays valid for S3d (reported 02:50). snap1-on: 533 entries, 39 gpu_native.
- Tool edits: snap-patch.py `--note/--note-file` (`patch-s3-tools.py snap-patch`; `s3-tools-test.py` PASS);
  stage-snap-bin.ps1 lists the PATCHES of S1..S<N> for S<N> (`patch-s3-tools.py stage`, 45F62362 -> A685B9D1).
- Downstream: Agent 11 `testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default`; Agent 8 boots; Agent 7
  `native3_boot_check.py`; Agents 5 and 4 use native3.

**S3d (DONE; Agent 1's GO 03:35, with Agent 4's draw.cpp sha256)**
- Live `rexlego/src/gpu_native/draw.cpp` 5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410 (306,557 B,
  mtime 03:34:59, Agent 4) was the only change against HEAD `001336f`.
- `prep-s3d.py 5EA1F357... --go 03:35 --owner A4` (03:42): 9/9 PASS; `S3d-rules.txt` 714CBC5E..., `S3d-notes.txt`
  C9B1707C.... `snap-patch.py plan S3d` -> COPY 1, errors 0 (`snap1/PLAN-S3d-0342.txt`); `apply` at 03:42:56:
  PATCHES-S3d.tsv 0250A3D000CB11C5..., STATE-S3d-0342.tsv AC7B88D344A2C446..., backup under `snap1-backup-S3d/`;
  `verify S3d` PASS (23843 files, 0 problems). snap1 is now S3d.
- `run-s3d.ps1`, 03:43:18-03:46:18 (build 102.7 s, stage 74.5 s): stage 0 FAIL, 103 PASS / 34 NOTE. Against
  native3-bin: exe differs (PASS), map NOTE; rexruntime, rexgpu-xenos, TracyClient, the wav, the ttf and
  amd_fidelityfx are identical. MANIFEST patch rows S1 2 (S1+p1, S1+p2) / S2 18 / S3 28 / S3d 1. Fingerprint
  335ff2d47268f3a1 (native3: 8f849b69907d4006; it hashes draw.cpp). Hashes: exe
  B90DF683D0A57A21F4DC24F8EA69F75FC954ADD4712B830A08C28F82FF521944, map 1C9AB7E3E471A6BA..., rexruntime
  D1D66AC3716835AC..., rexgpu-xenos EE0A661FB0C30FCB..., MANIFEST 368F9CE650EC56CE....
- devoff3-bin stays the OFF build of S3d: OFF builds don't compile draw.cpp.

**S3e (PREPARED 04:46, NOT BUILT; Agent 1 05:05: not tonight, keep the tools unused for S4)**
- For S4: the S3e tools assume snap1 is at S3d (newest STATE-S3d-*.tsv) and one draw.cpp row; for another base
  or tag, regenerate them the same way (make-s3e-clones.py pattern) and get Agent 9's review again.
- native3e-bin = S3d + exactly Agent 4's next live write of `rexlego/src/gpu_native/draw.cpp` (the `|| !vs` variant),
  native only, compared with native3d-bin. Only if Agent 8's native3d profile rows (~05:03) still show hash=0 lines.
  Tell Agent 8 before it starts and when it ends.
- Tools: `make-s3e-clones.py` (run 04:46; refuses to rerun without --force) generated `prep-s3e.py` 23536F1FB33DACC8
  and `run-s3e.ps1` FD188929D9831E64 from prep-s3d.py BD4D94DA / run-s3d.ps1 FE159F8A (both unchanged): token swaps
  (S3d -> S3e, the base S3 -> S3d, native3d -> native3e, native3-bin -> native3d-bin, s3d -> s3e) plus exact
  replacements, each with an expected count. It also patched stop-snap.ps1 C6B75748 -> 705233E59C9ED056 (adds
  run-s3e.ps1; backup `stop-snap.ps1.pre-S3e`). Diffs in `S3e-diffs/`: prep-s3e.py.vs-s3d 8A3BFEE3 (+36/-32),
  run-s3e.ps1.vs-s3d 794839B6 (+25/-25), stop-snap.ps1.S3e 88A5B710 (+2/-1).
- run-s3e's driver guard also lists run-s3d, rb-chain, run-rbN, prep-rbN, run-nb and prep-nb. stage-snap-bin.ps1 is
  unchanged: for S3e it lists the PATCHES rows of S1, S2, S3 and S3e; S3d's one row (draw.cpp) is superseded by S3e's
  (the last row per file wins), as the 4th line of S3e-notes.txt says.
- Tests (04:47): prep-s3e.py parses; run-s3e.ps1 and stop-snap.ps1 have 0 parse errors; all three ASCII, LF.
  `prep-s3e.py 5ea1f3576dcc2f90 --go 04:55 --dry-run`: 8/9 PASS, the only FAIL "live draw.cpp != snap1 draw.cpp"
  (no new write yet), exit 1, nothing written (SDK DLLs == native3d-bin: PASS). `run-s3e.ps1 -Jobs 10` without
  S3e-notes.txt: exit 4 before any build (log moved to `rbt-logs/test-snap3e-run.txt`). stop-snap.ps1 was not run.
- Agent 9 (05:00): OK, no objections (`perf-notes/agent9-codegen.md` S4.0). Hashes rechecked; make-s3e-clones.py
  A16E05AD rerun in a scratch copy gives all 7 outputs byte for byte; every changed line checked; the guard matches
  all 10 sample driver names and not itself; with the live hash faked in-process the dry run is 9/9 (rules and
  notes 4 lines each, nothing written). Cosmetic nit: the stop-snap.ps1 comment says "04:5x"; left as is, so the
  reviewed hash 705233E5 stays.
- At the GO, in order:
  1. `python build\agent2\prep-s3e.py <sha> --go HH:MM --owner A4`: must be 9/9 PASS; writes S3e-rules.txt and
     S3e-notes.txt.
  2. `python build\agent2\snap-patch.py plan S3e build\agent2\S3e-rules.txt --note-file=build\agent2\S3e-notes.txt`
     (COPY 1, errors 0), then `apply S3e` with the same arguments (backup `snap1-backup-S3e/`), then
     `snap-patch.py verify S3e` PASS. snap1 is then S3e.
  3. `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s3e.ps1 -Jobs 10` as a run_command
     background task: snap1-on, tag snap3e, then stage-snap-bin -> `native3e-bin` with -CompareBin native3d-bin. ETA
     about 6-8 min from the GO (S3d: build 102.7 s + stage 74.5 s). Log `snap3e-run.txt` (+ snap3e-steps.txt,
     snap3e-stage-native.log).
  4. Check: 0 FAIL; exe differs from native3d-bin and the other 6 files are identical; MANIFEST patch rows S1+p1/p2,
     S2 18, S3 28, S3e 1; log the fingerprint. Post exe, rexruntime, MANIFEST and fingerprint to Agents 1, 4 and 8
     (and 9, 10); tell Agent 8 that the build has ended; update this block and the inventory.

**Task #14 (session 3 part 2; files: build/agent2/** and this file)**
- Step 2, B rollback: NOT needed (Agent 1, after Agent 10's tie-break cleared B); rb1/rb2 stay prepared and unbuilt.
  Only at Agent 1's GO: `rb-chain.ps1 -Variant rb1|rb2 -Jobs 10`. prep-rbN copies snap1 (now S3d) to snapB3 with
  `install/rb1-nolocal` or `install/rb2-nomusttail`; game tree snapB3-off; A = devoff3-bin; out devoffRB1-bin or
  devoffRB2-bin. snapB3 holds one variant at a time, so switching variants needs `-Resync`.
- Step 3, nativeB: DONE 04:34:06, staged as `nativeB-bin` (RESULT at the end of this list). Agent 1's GO
  conditions:
  1. native3d staged: YES.
  2. disk estimate <= 40 GB: YES. About 3.5 GB: the snapB3 copy ~2.1 (snapB 1.5 + rexlego/out 0.6), snapB3-on ~1.0,
     nativeB-bin ~0.36. Agent 1 OK at 03:50.
  3. Agent 9 OK of the diffs: YES (03:51). Agent 9's independent dry run is byte-identical. Non-blocking nits:
     run-nb's guard doesn't list prep-*.py (rb-chain covers that); an explicit -Compare isn't checked against the tag;
     the fingerprint against A is only logged.
  4. Agent 8 says the last -Profile run is done: YES (n-prof ended 04:09:51, no build tools running; msg 04:11).
     Agent 3's functional runs may overlap the build; Agent 8's s0-s2 and native3d profiles wait for it to end.
  5. Agent 9 acks the post-review rb-chain.ps1 65A2CFE4 (-GuardOnly) diff: YES (04:06; Agent 1 added this condition
     at 04:02). Agent 9's own difflib diff of pre-GuardOnly (3660069E) against the current file is byte-identical to
     443CC9C0: +3/-1, and the exit 0 comes after every step-0 guard and before $log. The nb command leaves it unset,
     so it's a no-op there.
  Start only when 4 and 5 have both arrived. If it hasn't started by 06:40, tell Agent 1 (timer task-523) and send
  `@@done 14` without nativeB. Never start it after 07:00.
  - Command (run_command background task): `powershell -NoProfile -ExecutionPolicy Bypass -File
    build\agent2\rb-chain.ps1 -Variant nb -Jobs 10`. It runs verify S3d, then prep-nb.py, then run-nb.ps1.
    - prep-nb.py: robocopy snap1 -> snapB3 including rexlego/out, the batch-nolr step 4, gen-check. Its notes must
      say S3d.
    - run-nb.ps1: native configure of the fresh snapB3-on, gen-check against batch-nolr, gate, build, rexruntime ==
      install/bin, then stage nativeB-bin with -CompareBin native3d-bin.
    ETA ~25 min. Logs: rb-chain-nb.txt, rb-chain-nb-verify.txt, rb-chain-nb-prep.log, rb-chain-nb-run.log,
    snapB3-prep.txt, snapB3n-run.txt, snapB3n-steps.txt, snapB3n-stage.log.
  - Then check 0 FAIL, exe differs and the other files == native3d-bin. Post the exe, rexruntime, MANIFEST and
    fingerprint to Agents 1, 8, 9 and 10, then `@@done 14`.
  - RESULT (DONE): `rb-chain-nb.txt` 04:12:09-04:34:06, 1316.9 s, exit 0. verify S3d PASS (1.0 s). prep-nb 93.4 s:
    install pins 24CE1493 / E60EAF1C, robocopy snap1 -> snapB3 45.2 s, gen-check 870/870. run-nb 1221.4 s:
    configure, gen-check, gate PASS, native build (END 04:33:31, exit 0, 1151.5s), stage. Stage: 149 PASS / 0 FAIL /
    34 NOTE; MANIFEST patch rows S1 0 (labelled S1+p1/S1+p2) / S2 18 / S3 28 / S3d 1. Against native3d-bin: exe
    differs (PASS), map NOTE; rexruntime, rexgpu-xenos, TracyClient, the wav, the ttf and amd_fidelityfx are
    identical.
  - Hashes: exe 01C4D5A3E36FAC50C16B6CF8C0B6ACA6FC7D285BE67D66B30B229B7E2FEF5C5C (299,045,376 B); map
    C9259B05689E3AA5... (43,689,378 B); rexruntime D1D66AC3716835AC...; rexgpu-xenos EE0A661FB0C30FCB...; MANIFEST
    E5CBF30A6132B00E8D8F67E1C7C0B748AED6E486C0B61DDC2BBE06F110F2A966.
  - Native GPU fingerprint 81d1c3a71be3c096 (native3d: 335ff2d47268f3a1). Expected: of the fingerprint's inputs, 13
    differ from snap1: 12 batch-nolr files in rexlego/generated/default/ and rexlego/legodimensions_config.toml. No
    hand-written source differs.
  - Disk: snapB3 2.10 GB (24,987 files), snapB3-on 0.92 GB (588 files), nativeB-bin 0.34 GB: 3.36 GB in total (the
    estimate was ~3.5). Free C 247.5 GB at 04:35.
  - Agent 9, static check of nativeB vs native3d-bin (04:47): all PASS. mapcmp: the same 164,786 sub_ functions,
    __imp__ aliases and 109 hooked; .text -10.38%, exactly the devoff2 -> devoffB delta
    (`build/agent9/logs/mapcmp-native.txt`). The fingerprint differs by design (`build/agent9/fpcheck.py`: the same
    271 inputs, the 13 that differ are all codegen). Warnings: none in generated code, the rest pre-existing.
    MANIFEST pins (SHA256SUMS 24ce1493), gate PASS (525 DB entries, 432 TUs), host regs 378 (0 new / 0 gone).
  - Agent 10, nativeB 1a static (04:55): PASS (statecmp + --full MATCH, sumscheck MATCH, lrsites PASS, hookset PASS
    with 181 hooks, warncmp CHECK host-only); both pair runs start cold (fresh run dirs); 1b verdict within 20 min
    of the pair logs.
  - Agent 10, nativeB 1b route pair vs native3d (05:24, codegen-review "1b verdict"): PASS. B 54/54, exit 0, no
    errors, logdiff NEW 0 / MORE 0, slot heap and pool copy MATCH, the same 26 scene teardowns in order. Caveats:
    the placement relocation lr=83F9B660 site is not covered (heap-layout dependent, not a diff); the front-end
    exit came at a different press (same class as OFF pair 1). Recommends no rollback; optional reversed-order
    tie-break pair before 08:30 if the slot has room; level-change route for both in window 4.
- Tools (03:24-03:53):
  - `make-rb-clones.py` (run 03:46; refuses to rerun without --force) wrote prep-rb1.py 94C6C91698D88447, run-rb1.ps1
    0665AA37C8EF434F, prep-rb2.py E0A003731BD95532, run-rb2.ps1 118C2D6E0A498A0F and prep-nb.py 0FAF4A924AEEE498, and
    patched stop-snap.ps1 B9AECC6A -> C6B757480AFEA48F (backup `stop-snap.ps1.pre-RB`). Diffs in `RB-diffs/`:
    prep-rb1 DA5EDDBC, run-rb1 FEECE89A, prep-rb2 A6FA98BB, run-rb2 C07F412B, prep-nb F5B9A4B7, stop-snap.RB
    87D09AB2, run-nb.ps1.vs-run-b 48168743.
  - `run-nb.ps1` 979F4309EE10E9EF, written by hand from run-b.ps1 and the native parts of run-s3d.ps1.
  - `rb-chain.ps1` 65A2CFE4BE73E146. Agent 9 reviewed 3660069E; the only change since is the `-GuardOnly` switch
    (diff `RB-diffs/rb-chain.ps1.GuardOnly.diff` 443CC9C0, pre-image `rb-chain.ps1.pre-GuardOnly`).
  - `rb-tools-test.ps1` 1C056614683DC726: 48/48 PASS (run 2, 03:58). Run 1 was 44/4; its 4 FAILs were the test's own
    log filter (it caught rb-chain-guardonly-diff.py), since fixed. Console copies are in `rbt-logs/`; snapB3 was
    never created.

**Live tree edit (my only one)**
- 21:57:57: live `DimensionsRecomp/thirdparty/plume/plume_d3d12.cpp` B88E4E86... -> 564568D4... (S1+p2, Agent 1's
  step 1); backup `build/agent2/live-backup/plume_d3d12.cpp.B88E4E86`. No other live edit since.

**Other**
- (b), the FFX-headers rexruntime for native: not picked (S3 took fix (a)); my build plan stays in section (b) of
  `perf-notes/agent7-s3-proposal.md`.
- The relaunch checkpoint (01:22-01:27) and the batch 1/2 details are further down in this file.

**Scripts** (all in `build/agent2/`)
- `snap.py`; `snap-patch.py` (plan/apply/verify/revert, `--note`/`--note-file`); `make-rules-from-tsv.py`;
  `build-snap.ps1` (-Phase sdk|game|all, -Native, -Tag, -Jobs, -PrelinkJobs, -SkipConfigure, -KeepGoing, plus the B
  options); `gen-check.py`; `snap-gate.py`; `codegen-frozen/` (frozen and frozen2 stand-ins); `stage-snap-bin.ps1`
  (-Variant, -SnapTag, -BuildTag, -OutDir, -CompareBin, -CompareWhy, -ManifestNotesFile, ...); `run-s2.ps1`;
  `run-s3.ps1 -Stage off|native`; `run-s3d.ps1`; `prep-s3d.py`; `prep-b.py`, `run-b.ps1`, `b-chain.ps1`;
  `patch-b-tools.py`, `patch-s3-tools.py`, `patch-s3d-tools.py`, `patch-stop-s3d.py` (each run once; they refuse once
  their backups exist); `s3-tools-test.py`, `s3d-tools-test.ps1`; `stop-snap.ps1`; `splice-notes-top.py`; task #14:
  `make-rb-clones.py` (-> `prep-rb1.py`, `prep-rb2.py`, `prep-nb.py`, `run-rb1.ps1`, `run-rb2.ps1`), `run-nb.ps1`,
  `rb-chain.ps1`, `rb-tools-test.ps1`, `rb-chain-guardonly-diff.py`, `notes-resume-t14.py`; standby: `make-s3e-clones.py`
  (-> `prep-s3e.py`, `run-s3e.ps1`), `notes-s3e-prep.py`, `notes-standby-0457.py`, `inventory.py`.
- If Agent 1 opens a window mid-build, run `powershell -NoProfile -ExecutionPolicy Bypass -File
  build\agent2\stop-snap.ps1` within about 2 min, then re-run the same stage later; ninja resumes.
- Keep every intermediate (snap1, snap1-sdk, snap1-off, snap1-on, snapB, snapB-off, the backups, the staged bins and
  every `*.pre-B`, `*.pre-nolr`, `*.pre-S3`, `*.pre-S3d`, `*.pre-RB`, `*.pre-GuardOnly`, `*.pre-S3e`, `snap1-backup-S3d`;
  snapB3, snapB3-on and nativeB-bin) until Agent 1 says otherwise. Free C: 265.7 GB at 04:49.
- agy-grid delivers only the `@@to` line itself, so every message is ONE line; the
  details live in this file.

| Step | Result | Wall | Evidence |
|---|---|---|---|
| 1 SIMDe | `prepare_simde.py --check` PASS (dev + baseline share it via the junction) | - | - |
| 2 rexglue target | build/sdk `--target rexglue`; frozen copy `build/agent2/codegen-tool/rexglue.exe` (sha256 FA9EE64C...) == install/bin | 103.3 s | - |
| 2 codegen | "XEX patch applied successfully ... new version: 0.0.23.3"; 887 files, 467.3 MB, 438 `legodimensions_recomp.N.cpp` + init + register | 129.8 s | `build/agent2/gen-noflag/`, codegen logs |
| 2 codegen `--pointer_table_scan --ignore-stamp` | 0 written, 883 unchanged: the flag changes nothing for this XEX | 100.6 s | `codegen-pts.log` |
| 2 junction | `DimensionsRecomp\rexlego\generated -> baseline\DimensionsRecomp\rexlego\generated` | - | announced ~19:10 |
| 2 SDK header list | 101 headers (64 `include/rex`, 37 thirdparty fmt/simde/spdlog), identical in all 5 scanned generated TUs | 7 s | `build/agent2/sdk-headers-dev.txt`, list below |
| 3 SDK | run 2 (after SIMDe) exit 1 only from the 7 PPC `.map` nm edges; install 30 s; ctest **216/216 pass**, 4 skipped (BitStream), excl. `ppc_tests_NOT_BUILT` and `^ppc\.` | 90.2 s + 30 s + 6.7 s | `build/agent2/sdk-*.log` |
| 4 OFF game | `build-game-baseline.ps1`: run 1 FAIL (partition coupling, below), run 2 `-k 0` all other 450 edges OK, run 3 shim TU + link | 196.9 s / ~17.7 min / 18 s | `game-build-run1/run2.log`, `game-build.log` |
| 4 staged | `build/baseline-bin` re-staged 19:01:22 with TracyClient.dll: 7 files, 214.0 MB; `MANIFEST.txt` has sha256, import tables, 37 PASS checks | 8 s | `stage-baseline-bin.ps1` |
| 5 ON configure | build/dev, NATIVE_GPU=ON, Agent 6 stubs, shim, frozen codegen; 1292 DB entries (70 rexlego/src .cpp TUs, 440 generated, the rest SDK + plume) | 369.9 s, re-run 24.1 s | `dev-on-configure.log` |
| 5 generated headers | 12 build/dev headers (9 `gpu_native/shaders/*.h` incl. `copy_color_ps.h`, `native_gpu_build_info.h`, 2 overlay) from each edge's OWN command | ~6 s | `dev-gen-headers.ps1/.log` |
| 5 compile-one sweep | **70/70** rexlego/src TUs pass `compile-one -SyntaxOnly -Db build\dev\compile_commands.json` (6 jobs) | 276 s | `build/agent2/c1-sweep/summary.txt` |
| 6 PPC map fix | `rexglue-sdk/cmake/ppc_test_pipeline.cmake`: nm runs under `cmake -P` with stdout on a pipe and the map is written byte-exact. **166/166** script-mode and **168/168** ninja-built maps are byte-identical to nm's stdout | 18 s + 49 s | `build/agent2/ppcmap-test/test_ppcmap3.log` |

## Task #15 (board run 2, 13:45-14:20): post-W4b prep, dry runs only, nothing built

Agent 1's task #15: prepare the post-W4b steps so they take minutes. No builds, game runs or git writes; no writes to
the live repos or the snap trees; at most 2 threads; W4b inputs untouched. Agent 1 (~13:58): no builds before W4b;
notes and dry runs until 15:00, then nothing until Agent 1 says W4b is done. The three scripts below are read-only for
every tree; they write only their report file (s4b-compose-check.py also its scratch copies in `build/agent2/s4b-check/`).

### 1. Live apply of S4a: `build/agent2/apply-s4a-live.ps1` (Agent 1 runs it after W4b)

- Dry run (the default, read-only): `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\apply-s4a-live.ps1`.
  Per file: the live sha256, the S4a before and after hashes, the snap1 source hash, then PASS (live == before), DONE
  (live == after) or FAIL.
- `-Go` refuses with exit 2 unless every file is PASS (DONE is accepted only with `-Resume`), and with exit 3 while any
  `legodimensions*`, `ninja`, `clang*`, `lld-link`, `ld.lld` or `cmake` process runs. Otherwise it backs up the 6 live
  files to `build\agent2\live-backup-S4a-<stamp>\`, writes each snap1 file byte for byte over the live file (mtime =
  now, so the next live build recompiles it), re-hashes it and requires == after. On any error it restores all 6 from
  the backup and exits 4. No git commands; Agent 1 commits.
- Exit codes: 0 ready (dry run) or done (-Go); 1 dry run not all PASS; 2 refused on hashes; 3 refused on processes;
  4 rolled back.
- **Dry run 13:51:48: exit 0, 6/6 PASS, snap1 == after 6/6** (`build/agent2/apply-s4a-live-dryrun-1351.txt`). At that
  moment clang++ (pid 7020, Agent 7's syntax check) was running, so -Go would have refused (exit 3); at 13:55 and
  14:08 Agent 3's legodimensions was running. Run -Go on a quiet machine.

| Item | Live file | before = live now | after = snap1 |
|---|---|---|---|
| #7 u diag | rexglue-sdk/src/graphics/d3d12/shared_memory.cpp | B120D07C... 14,514 B | BB0838CE... 20,888 B |
| #8 P2 | rexglue-sdk/src/graphics/shared_memory.cpp | 15C89EDB... 24,698 B | 0BE4BADC... 26,439 B |
| #5 fix (i) | rexglue-sdk/src/system/xmemory.cpp | 6E8FA1BA... 107,670 B | 141FB1A9... 108,907 B |
| #38 precise wait | rexglue-sdk/src/core/timer_queue.cpp | D8724B29... 12,839 B | 015C04A2... 16,091 B |
| #32 warm boot | rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp | 5DBED81F... 161,305 B | DA777443... 161,303 B |
| #2 miss cache | rexlego/src/gpu_native/shaders.cpp (game repo) | E87A2DEE... 41,029 B | 9567FE3F... 51,261 B |

- #2 is a native fingerprint input (native4 5e3ff55de10f4f64, native3d 335ff2d47268f3a1), so live native builds get a
  new fingerprint after the apply.

### 2. B line + S4a: devoffB4 + nativeB4 (only if W4b favours B and the user picks it)

- Meaning: B's codegen (generated/ = Agent 9's batch-nolr set, pins SHA256SUMS 24CE1493 and config.toml E60EAF1C;
  codegen-frozen2) + the S4a sources. nativeB4 = nativeB's tree (snapB3, S3d level) + the 6 S4a files. devoffB4 =
  devoff4's rexlego (S3d + #2; OFF builds don't compile gpu_native) + B's codegen. So devoffB4 vs devoff4 and nativeB4
  vs native4 each differ only in codegen. (devoffB itself was built from snapB at the S2 level.)
- No SDK build: both B trees link snap1-sdk/install, the S4a SDK since 13:27 (its rexruntime.dll, rexgpu-xenos.dll and
  TracyClient.dll == the devoff4-bin and native4-bin rows). **Build B4 while the install is still S4a:** an S4b SDK
  build in snap1-sdk changes what every tree links (or clone snap1-sdk first, 0.45 GiB).

| Bin | Steps | Est. at -j10 |
|---|---|---|
| nativeB4 -> `build/agent2/nativeB4-bin` | back up snapB3's 6 S4a files to `build/agent2/snapB3-backup-S4a/`; copy the 6 snap1 files (hashes as in section 1) + a PATCHES-B4 row; build-snap game -Native on snapB3-on (configure ~25 s, gen-check vs batch-nolr ~5 s, gates); 4 compile edges (device 31.3 s, pipeline_library 26.9 s, shaders 24.4 s, shader_archive 17.0 s: ~31 s) + fingerprint + exe link (last 4 s); stage + MANIFEST + the S4a static checks | ~4.5-5.5 min (S4a native: 333 s end to end) |
| devoffB4, option B (recommended) -> `build/agent2/devoffB4-bin` | back up (to `build/agent2/snapB-backup-B4/`) and copy from snap1 35 files (lists in `b4-dryrun.py` [2] and [10]; 3 are new): the 4 rexlego files gpu_native/draw.cpp 50AA3B1D -> 5EA1F357, gpu_native/shaders.cpp E87A2DEE -> 9567FE3F, settings_preferences.cpp C78112AA -> 9CBE6DBF, settings_registry.cpp A3733700 -> 4EC71328, plus 31 build-neutral files the stage gate checks (the 29 rexglue-sdk rows of S3 and S4a, .gitignore 09246E1B -> 600E2436, .gitmodules E7D25A21 -> C6E62916); build-snap game on snapB-off: 3 compile edges (install/share rex_app.cpp 21.4 s, S3 drift; settings_preferences 20.9 s; settings_registry 15.7 s: ~21 s) + link 5.5 s; stage + MANIFEST + checks | ~2-3 min |
| devoffB4, option A (clean) -> the same bin folder | a new build dir `build/agent2/snapB3-off` (home snapB3/DimensionsRecomp/rexlego, prefix snap1-sdk/install, NATIVE_GPU=OFF, Release, codegen-frozen2); full build: 903 edges, last 1,039 s | ~19-20 min, +0.6 GiB |

- Option B makes snapB/rexlego == snapB3/rexlego outside generated/ and out/ (b4-dryrun [3]: 284 files each, the only 3
  differences are in its apply list), so it is source-identical to option A. snapB's own rexglue-sdk is never built
  (snapB-off has no .ninja_deps path outside snapB/rexlego).
- **Stage gate (b4-dryrun [10], 14:24):** stage-snap-bin.ps1 with `-GameSnap` requires every PATCHES row's file in the
  game snapshot to equal its last after (L188-195). With `-PatchTagList S1,S2,S3,S3d,S4a` that is 55 rows, 52 files
  (snap1 == last after 52/52). snapB3 + the 6 S4a copies: 0 rows fail (nativeB4, and option A). snapB + only the 4
  rexlego copies: **31 rows would fail** (29 rexglue-sdk, .gitignore, .gitmodules; snapB is at S2), so option B copies
  all 35; then 0 fail. The 31 extra copies are build-neutral: none is in snapB-off's .ninja_deps or named in its
  build.ninja (no compile, link or configure input).
- Staging at GO: `stage-snap-bin.ps1 -Variant off|native -SnapTag S4a -BuildTag <tag> -GameTree snapB-off|snapB3-on
  -OutDir devoffB4-bin|nativeB4-bin -GameSnap snapB|snapB3\DimensionsRecomp -PatchTagList S1,S2,S3,S3d,S4a -CompareBin
  devoff4-bin|native4-bin` (+ S4a's -RuntimeStrings, -XenosStrings and -ExeStrings). Same SDK install as S4a, so every
  staged file but the exe and map must equal the S4a bin's, and the exe must differ (default -CompareWhy: the
  generated code changed).
- Totals: option B **~7-9 min** for both bins; option A ~25 min. At GO, ~10 min more to write `prep-b4.py` +
  `run-b4.ps1` from prep-s4a.py, run-s4a.ps1 and run-nb.ps1 (build-snap.ps1 `-Phase game [-Native] -Tag -SnapDir
  -GameDir -CodegenExe -GenBase build\agent9\install\batch-nolr\generated`; stage-snap-bin.ps1 `-Variant off|native
  -SnapTag -BuildTag -GameTree -OutDir -GameSnap -ManifestNotesFile`). Every copy (the 35 snapB files, the 6 snapB3
  files, any restore from a backup) gets mtime = now after its hash check: see the mtime rule in section 4.
- Disk: nativeB4-bin ~0.34 GiB + devoffB4-bin ~0.19 GiB + backups < 1 MiB = **~0.55 GiB** (option A ~1.15 GiB); free C
  266.8 GiB. Pristine clones of the B trees don't help: CMakeCache holds absolute paths, so a clone means two fresh
  configures and full builds (~37-40 min).
- **Must stay byte-identical** (MANIFEST + sizes before and after; `b4-dryrun.py --full-hash` re-hashes every bin file,
  ~2.3 GB, only when no game runs): devoff2-bin B87DC2D2, devoffB-bin 8709476F, devoff3-bin B9C5175D, native3d-bin
  368F9CE6, nativeB-bin E5CBF30A, devoff4-bin 16DCC939, native4-bin 00D33D4F; snap1, snap1-sdk (incl. install),
  snap1-off, snap1-on; build/sdk/install, build/baseline-bin, the rexlego\generated junction, bench/agent8,
  build/agent8, harness. Changed by design: snapB3 + snapB3-on (option B: also snapB + snapB-off), the new bin
  folders and the backups. The bin files carry 2-36 hardlinks (other agents' run folders); B4 writes only the two
  build dirs and the new folders, so it can't reach them. The two build-dir exes have 1 link each.
- If S4b on B follows at once and time is short, B4 can be skipped (S4b contains S4a); B4 is the cheap checkpoint that
  isolates S4a on the B line.

`build/agent2/b4-dryrun.py` (read-only, 1 thread, ~5 s; writes only `b4-dryrun-<HHMM>.txt`). **Run 14:04: 0 FAIL,
0 WARN** (`build/agent2/b4-dryrun-1404.txt`); **re-run 14:24 with the new [10] (stage-gate simulation): 0 FAIL, 0 WARN,
3 s** (`build/agent2/b4-dryrun-1424.txt`; [1]-[8] unchanged, free disk 264.7 GiB):
- the 6 files are at after in snap1, at before in snapB3 and snapB;
- snapB is exactly at S2 and snapB3 exactly at S3d (46/46 files each);
- both CMakeCaches as expected (homes, prefix snap1-sdk/install, OFF/ON, Release, codegen-frozen2);
- the install DLLs == the S4a bins; both exes relink (install .lib 13:26:57 is newer); snapB-off sees 2 newer
  installed headers (codegen function_types.h and config.h, in no game TU's deps);
- batch-nolr pins ok; both trees' config.toml == the pin; 871 generated files each (only default/codegen.d differs,
  by design);
- the 7 bins match their MANIFEST rows (file count, sizes); the 5 proposed folders are absent;
- dirty prediction from .ninja_deps: snapB3-on drift 0, 4 edges with the apply; snapB-off drift 1, 3 with the apply.
- The 14:02 run's 53 FAIL + 1 WARN were two checker bugs, both fixed: bin link counts are informational now, and the
  level check accounts for files that later stages changed again.

### 3. Deletable after W4b (nothing deleted; Agent 1 or the user decides)

Sizes from the 05:39 inventory, small folders measured at 14:05 (MiB/GiB = 2^20/2^30 B). The staged bin files carry
2-36 hardlinks (other agents' run folders): deleting a bin folder frees nothing until those links are gone. The snap
and build trees have single links.

| Group | build/agent2/... | Frees | When |
|---|---|---|---|
| A test outputs | gen-noflag 467.3 MiB, probe-toggle 3.0, ppcmap-test 2.6, c1-sweep 0.3, __pycache__ 0.2, compile-one-test 0.1, recovered 0.1, cf2-test, nmtest, scratch-inc, s4b-check ~0 | ~0.47 GiB | any time after W4b |
| B apply backups | snap1-backup-S2 0.7 MiB, -S3 0.4, -S3d 0.3 (committed); snap1-backup-S4a 0.3 and s4a/ 0.7 only after Agent 1 commits S4a | ~2.4 MiB | after the commits |
| C history bins | devoff1-bin 214.2 MiB, native-bin 363.5, native2-bin 363.7, native3-bin 363.7 | 1.27 GiB, once unlinked | after W4b |
| D if the S3d line wins | snapB 1.50 GiB, snapB-off 0.58, snapB3 2.10, snapB3-on 0.92; devoffB-bin + nativeB-bin 0.53 once unlinked | 5.1-5.6 GiB | after the user picks S3d |
| E if the B line wins | snap1-off 0.62 GiB + snap1-on 0.96, once B4 (or S4b on B) is built and checked; with option A also snapB + snapB-off (2.08); devoff2/devoff3/native3d-bin 0.77 only with Agent 1/user OK, once unlinked | 1.58 GiB (+0.77) | after B4 is checked |

- Keep in every case: snap1 (2.19 GiB) and snap1-sdk (0.45 GiB; its install is the prefix of every tree, B included),
  codegen-frozen, codegen-tool, compat, live-backup, the notes and logs; devoff4-bin and native4-bin until S4a is
  committed.
- Totals: always (A + B + C) **~1.74 GiB**; if S3d wins **~6.8-7.4 GiB**; if B wins **~3.3-4.1 GiB**. Other agents'
  folders are not mine to size.

### 4. S4b draft (plan only; Agent 1's FYI: u_block = 0.93, so S4b is the full rebuild right after W4b, on the picked line)

Inputs, all staged on scratch and rated; each base is the S4a output (= snap1 now). Hashes are the first 8 hex digits.

| Item | Staging (owner) | Files (SDK unless noted) | before -> after |
|---|---|---|---|
| C1 (#4) = variable S4B_C1: Agent 1 sets it at build time, v3 if Agent 10 rates v3 SAFE first, else v2. Agent 10, ~14:38 (b2r row 36, S35): v3 is SAFE at the default and ON is SAFE to test; all applies land at offset 0, which matches my 14:32 run. So v3 is expected | v2: `build/agent12/s4-c1v2/keep-watch-v2.diff` 418D3D39 (A12; RESULT PASS 13:49, syntax PASS). v3: `build/agent12/s4-c1v3/keep-watch-v3.diff` DECCFE33 (A12; RESULT PASS 14:22:38, syntax PASS; v2 + an init latch for both cvars + a load-first blocked flag, no header change; A12: the S4b tests use v2, v3 is for Agent 10 to rate) | include/rex/graphics/shared_memory.h; include/rex/system/xmemory.h; src/graphics/primitive_processor.cpp; src/graphics/shared_memory.cpp; src/system/xmemory.cpp | 4D861738 -> 82A66445; 80100865 -> 5A70782E; E07F6902 -> 470BA4BE; 0BE4BADC -> A4A31038 (these 4 are the same in v2 and v3); 141FB1A9 -> DC23757A (v2, 119,957 B) or BCA5E1CF (v3, 121,109 B) |
| C1, game repo (same for v2 and v3) | `build/agent12/s4-c1/keep-watch-rexlego.diff` 4D0C1079 (v1, reused) | rexlego/src/gpu_native/memory_watch.cpp (CRLF, 166 lines) | 19AE1606 -> 70829846 = `build/agent12/s4-c1/new/game/rexlego/src/gpu_native/memory_watch.cpp` |
| M1 (#11) | `build/agent5/s4-m1/m1-nontemporal-copy.diff` EBECE86E (A5) | src/graphics/d3d12/shared_memory.cpp | BB0838CE -> 2A5ADF13 |
| P2 counter | `build/agent12/s4-p2c/memexport-full-buffer-counter.diff` 29E02E24 (A12) | src/graphics/d3d12/command_processor.cpp | 3AB3AA53 -> 474C1CBA |
| #18/#20 | `build/agent7/s4-r1r2/s4-r1r2.diff` BD0C4A93 (A7; re-staged 14:01, comment-only nit) | src/graphics/d3d12/command_processor.cpp; include/rex/graphics/d3d12/command_processor.h; include/rex/graphics/d3d12/deferred_command_list.h; src/graphics/d3d12/deferred_command_list.cpp | 3AB3AA53 -> 760833A5; 41F32B80 -> 67F4E838; DA2F58B6 -> 9F6CC70A; FFDF7FB6 -> 30FF5744 |
| #24 N1-fixed | `build/agent9/s4/fence-wait/` (draft + n1-n4 diff; A9) | a new rexlego hook TU + rexlego CMakeLists.txt | no final diff yet; landing OFF needs the rexlego grants, the syntax compile and my batch-nolr build with the map check (b2r §26) |
| #30 | S4-DRAFT L178/L182 | a rexlego CMakeLists.txt option, native only | goes in with #24 and C1: one native re-pin |
| #26 | A9 (codegen db16cyc -> `_mm_pause`) | the codegen tool + a regen | last; +3-4 min when bundled; needs a new pinned generated set (B line: an Agent 9 batch-nolr regen) |

**Composition check with the C1 variable: `build/agent2/s4b-compose-check.py --c1 both`, run 14:32:39, 0 FAIL, 4.7 s**
(`build/agent2/s4b-compose-1432-c1both.txt`, sha 61CC9FBF; script sha DE30592B). The script now takes `--c1 v2|v3|both`
(default: env S4B_C1, else v2) and runs both orders per variant (o1-v2, o2-v2, o1-v3, o2-v3):
- all 5 diffs (C1 v2 418D3D39, C1 v3 DECCFE33, M1, P2c, r1r2) hash to their records; the 10 snap1 bases equal the
  first befores, which are the same for v2 and v3;
- in all 4 orders every lone step == its record (C1 v3 applies with no offsets) and o1 == o2 per variant;
  command_processor.cpp ends at 027204B5 for both variants; xmemory.cpp ends at the variant's C1 after (v2 DC23757A,
  119,957 B; v3 BCA5E1CF, 121,109 B);
- v2 vs v3: 9 of the 10 final files are identical, only xmemory.cpp differs; memory_watch.cpp as below, same for both.
- v3 changes no header, so the rebuild scope and the times below are the same for v2 and v3.

**First composition check (v2 only): `build/agent2/s4b-compose-check.py`, run 14:12:55, 0 FAIL, 38 s**
(`build/agent2/s4b-compose-1413.txt`; scratch copies of the snap1 files in `build/agent2/s4b-check/`,
`git -c core.autocrlf=false apply` outside any work tree):
- the 4 SDK diffs hash to their records; all 10 base files in snap1 equal the first staged before (live too, except
  the 3 S4a files, which stay pre-S4a until Agent 1's apply);
- order o1 C1 v2 -> M1 -> P2c -> r1r2 and order o2 C1 v2 -> M1 -> r1r2 -> P2c both apply with exit 0, every lone step
  == its record, and o1 == o2 for all 10 files. P2c and r1r2 share command_processor.cpp but commute: the second one
  applies with offsets only (9-22 lines), and both orders give **027204B53A271D69... (273,790 B)** = Agent 10's
  composite (b2r §30/§31; re-confirmed by Agent 10 at ~14:12 for the re-staged r1r2). For the chained step the before
  check is the first step's after (474C1CBA, or 760833A5 in o2), and the final hash must be 027204B5.
- memory_watch.cpp: live = snap1 = 19AE1606 (166 CRLF lines); a plain `git -c core.autocrlf=false apply --check` of the
  LF diff fails ("patch does not apply" at :28), as Agent 10 said. So land it by copying the staged after-file
  (70829846; its orig/ = 19AE1606) once live == 19AE1606 is checked.

Apply order on S4a (by file overlap): C1 = S4B_C1 (v2 or v3: 5 SDK files) + memory_watch.cpp (same for both) -> M1 ->
P2c -> r1r2 (either order) -> #24 + #30 (CMake/fingerprint; one native re-pin with C1) -> #26 regen last. At GO the
S4b prep/build driver takes the same single variable (`-C1 v2|v3`, default $env:S4B_C1, else v2): it picks the C1 diff
and the xmemory.cpp after record from it, writes the variant into the PATCHES rows and the MANIFESTs, and changes
nothing else (same bin names, same steps).

**mtime rule for every copy (Agent 1, 14:41, from Agent 4's finding):** a copied file keeps its old mtime, so the
native fingerprint and index steps miss it. So the S4b and B4 drivers set mtime = now on every file they copy into a
tree, right after the copy and its hash check:
- memory_watch.cpp (the staged after-file 70829846);
- B4 option B's 35 snapB copies and nativeB4's 6 snapB3 copies;
- any S4b copies into snapB/snapB3 on the B line;
- every rollback restore from a backup.

Files that git apply writes get a new mtime anyway. apply-s4a-live.ps1 already gets one too, because it writes the
bytes with [IO.File]::WriteAllBytes.

Build scope and time: C1's xmemory.h is in the generated-code closure (through the PCH: all 440 generated TUs, main.cpp,
18-22 rexlego TUs and 199 SDK TUs), so S4b is a full rebuild of the SDK and of both game trees; r1r2's d3d12 headers
(in no game TU's deps) only add SDK TUs. At -j10, one after the other (S4 estimate (1) below):
- S3d line: SDK ~5-6 min + devoff ~15-19 min + native ~17-21 min = **~37-46 min**, + apply, MANIFESTs and gates ~5 min.
- B line: SDK ~5-6 min + OFF ~19 min (last full build 1,039 s) + native ~21 min (1,151 s) + ~5-8 min = **~48-51 min**.
- #26 bundled: +3-4 min (regen ~130 s + gen-check ~61 s), or Agent 9 supplies the regenerated set.
- Disk: built in place, the 2 new bins ~0.56 GiB + backups; cloning the S3d trees first +4.2 GiB; a #26 regen snapshot
  ~4.2 GiB.
- With B4: B4 needs the S4a install, so build B4 before the S4b SDK lands in snap1-sdk (or clone snap1-sdk).

### 5. S4b bin names for Agent 7's queue (`build/agent7/s4b-queue/QUEUE.md`, 14:22; provisional until Agent 1's S4b task)

| Placeholder | S3d line | B line | What |
|---|---|---|---|
| `<S4B-OFF>` | `build/agent2/devoff4b-bin` | `build/agent2/devoffB4b-bin` | S4b OFF build, every switch OFF |
| `<S4B-NAT>` | `build/agent2/native4b-bin` | `build/agent2/nativeB4b-bin` | S4b native build, every switch OFF |
| `<S4B-CTR>` | `build/agent2/devoff4b-ctr-bin` | `build/agent2/devoffB4b-ctr-bin` | `<S4B-OFF>` with only rexgpu-xenos.dll replaced: deferred_command_list.cpp (in `rexgpu-xenos.dir`, checked in snap1-sdk) recompiled with `-DREX_D3D12_DEFERRED_COUNTERS=1` and the DLL relinked in a scratch dir; every other file identical to `<S4B-OFF>`; the CTR DLL must contain the `deferred_counters` text and the OFF DLL must not |
| `<S4B-CG26>` | `build/agent2/devoff4b-cg26-bin` | `build/agent2/devoffB4b-cg26-bin` | `<S4B-OFF>` with #26's codegen ON (a regenerated set: ~10 TUs + link, built in a copy, never in the junction); only after Agent 10's rating |

- G1 (mine): every diff hash-checked (diff, input before, output after) as in S4a, with the C1 diff and the xmemory.cpp
  after taken from S4B_C1 (v2: 418D3D39 / DC23757A; v3: DECCFE33 / BCA5E1CF); the composition as in section 4
  (027204B5 for both; memory_watch.cpp by the staged after-file copy, CRLF kept, 70829846 for both); the static check
  of the new cvars and strings. The bin names above are the same for v2 and v3; the MANIFEST records the variant.
- G2: the #26 tool with the option OFF must regenerate the pinned set byte for byte (S3d line: the pinned baseline set;
  B line: batch-nolr SHA256SUMS 24CE1493), ~3 min; I run it in the S4b build if Agent 9 doesn't.
- G3 (mine): on the OFF bin of the line that runs rows 17-18, the map must resolve sub_83FBF7D0, sub_83FAF180,
  sub_83FB09E8 and sub_83FC0C10 to gpu_wait_backoff.cpp.obj: 27 -> 31 hooked aliases (29 if #24 lands without
  LEGO_GPU_WAIT_HOOK_GETDATA, which defines only H0 and H1: Agent 9 R2.11.2).

## S4a (task #4, board run 2): devoff4 + native4, every new switch OFF (13:20-13:40)

Procedure: my S3d procedure on the snap1 trees (snap1, snap1-sdk, snap1-off, snap1-on), built in place, with apply
backups in `build/agent2/snap1-backup-S4a/`. `build/agent2/prep-s4a.py` git-applies each staged diff to a scratch
copy of the snap1 file (`GIT_CEILING_DIRECTORIES=R` and `-c core.autocrlf=false`, because R sits inside a parent repo
and the global autocrlf is true). It checks the input hash before and the output hash after against the staging
record, then copies the result into snap1. The live files == the snap1 before-hashes; live was neither read for the
apply nor written.

| Item | File (under DimensionsRecomp/) | Before (S3d) | After (S4a) | Source (sha256) |
|---|---|---|---|---|
| #7 u diag (A12) | rexglue-sdk/src/graphics/d3d12/shared_memory.cpp | B120D07C6709D0D2 (14,514 B) | BB0838CE3909E18A (20,888 B) | `build/agent12/s4-diag/upload-hash-log.diff` (D2905301) |
| #8 P2 (A12) | rexglue-sdk/src/graphics/shared_memory.cpp | 15C89EDB4B197C17 (24,698 B) | 0BE4BADCAC666BEE (26,439 B) | `build/agent12/s4-p2/single-hold-rearm.diff` (77BEB64E) |
| #5 fix (i) (A12) | rexglue-sdk/src/system/xmemory.cpp | 6E8FA1BA80EF9271 (107,670 B) | 141FB1A947D59156 (108,907 B) | `build/agent12/s4-fixi/protect-hold-g.diff` (80CAD795) |
| #38 precise wait (A11) | rexglue-sdk/src/core/timer_queue.cpp | D8724B29C43286B0 (12,839 B) | 015C04A22DACC592 (16,091 B), == `stage/timer_queue.cpp` | `build/agent11/timerq/stage/timerq.diff` (D07A2DC4) |
| #32 warm boot, always on | rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp | 5DBED81F611E25B1 (161,305 B) | DA77744302CFC149 (161,303 B) | mine: `build/agent2/s4a/pc-warmboot.diff` (080122DD, 695 B) |
| #2 miss cache (A4), native4 only | rexlego/src/gpu_native/shaders.cpp | E87A2DEE43D38D8E (41,029 B) | 9567FE3F3B63637D (51,261 B), == `build/agent4/s34/shaders.cpp` | `build/agent4/s34/shaders-s34.patch` (328BDAE1) |

- Agent 1's `build/agent11/timerq/timerq.diff` does not exist; the diff is under `stage/` (R-root relative paths).
  Agent 12's diffs are SDK-root relative (LF); Agent 4's patch is DimensionsRecomp-root relative with CRLF content
  (shaders.cpp is CRLF, the SDK files are LF).
- #32: L564 `creation_thread_original_count` -> `creation_thread_needed_count` in the `while
  (creation_threads_.size() < ...)` loop, the only match; uses of needed_count 1 -> 2, original_count 6 -> 5.
- Records: `snap1/PATCHES-S4a.tsv` (B9612DA2), `snap1/STATE-S4a-1325.tsv` (87DB470A), `build/agent2/S4a-notes.txt`
  (6AC482D8), `build/agent2/s4a/HASHES.txt` (D9BEA59D); logs `s4a-prep-dryrun.txt` (work-132122) and
  `s4a-prep-apply.txt` (work-132457); `snap-patch.py verify S4a`: 23,843 files, 6 backups, 0 problems.
- Where each file lands: rexgpu-xenos.dll = both shared_memory.cpp + pipeline_cache.cpp; rexruntime.dll = xmemory.cpp
  + timer_queue.cpp (rexcore); native exe = shaders.cpp. OFF builds compile no gpu_native file, so devoff4 has no #2.
- Static check (S2b step 1): PASS. shared_memory_upload_hash_log, shared_memory_single_hold_rearm,
  physical_protect_hold_global_lock and timer_queue_precise_wait are each defined once as `REXCVAR_DEFINE_BOOL(name,
  false, ...)` and absent from the S3d files; the staged DLLs contain them (rexgpu-xenos.dll the 2 shared_memory
  cvars, rexruntime.dll the other 2). shaders.cpp reads `LEGO_NATIVE_SHADER_MISS_CACHE` (env var, default OFF);
  native4's legodimensions.exe contains it (MANIFEST PASS line).

### Build times (-j10)

| Step | devoff4 (`run-s4a.ps1 -Stage off`, 13:25:32-13:31:43) | native4 (`run-s4a.ps1 -Stage native`, 13:33:01-13:38:35) |
|---|---|---|
| SDK build (snap1-sdk) | 84.8 s (9 edges) | - (uses the devoff4 SDK install) |
| SDK install | 102.6 s | - |
| configure | skipped (-SkipConfigure) | 7.7 s |
| gen-check | 91.2 s | 5.5 s |
| gate | 3.4 s | 1.0 s |
| game build | 10.2 s (1 edge: the relink) | 91.2 s (6 edges: fingerprint, shaders.cpp, device.cpp, pipeline_library.cpp, shader_archive.cpp, link) |
| build total | 297.1 s | 107.0 s |
| stage + MANIFEST | 68.7 s | 173.7 s (native3d's took 74.5 s) |
| total wall | 371.2 s | 333.2 s (incl. ~50 s of guards, DLL checks and post-stage compares) |

Against the task #30 estimate (right column of (1)): the SDK took 187 s (estimate ~2 min; the install alone took
102.6 s vs 50-65 s); devoff4's game side took ~105 s + 69 s of staging (estimate ~1.5-2 min). gen-check took 91.2 s
in devoff4 but 5.5 s in native4 (the second probably had a warm file cache). native4: build 107.0 s, in line with the
~2-3 min estimate for the build part; the staging (173.7 s) took over twice native3d's.

### Staged bins

`build/agent2/devoff4-bin` (7 files, 214.3 MB; exe and map differ from devoff3 because the game relinked against the
S4a SDK):

| File | Size (B) | sha256 | vs devoff3-bin |
|---|---|---|---|
| legodimensions.exe | 170,335,232 | 6BE3C713229232B29C183D27B397A3560B46E2279C6AF47C64CF8A2EFA287376 | differs |
| legodimensions.map | 39,162,310 | DCC51E2B7A0040E20E017C1FE9877CA88926B543B75B58884CEF05CAACF95253 | differs |
| rexruntime.dll | 10,898,432 | 870276A6D0E8DE570848FB811591BA5B0AFD8B36413A09F154D0BCAF4902AECA | differs (expected) |
| rexgpu-xenos.dll | 3,406,848 | 59662F767F8B9C7CA78C38370EC6ED6CFB499805F833B458543C206254F65BE5 | differs (expected) |
| TracyClient.dll | 233,472 | 85044850B6C663B5CE8722285D13070381C33C9ABC49D06B3E59BA0277F8FF4E | == |
| achievement_unlocked.wav | 191,018 | A707019154484B9DE0AD310826668C0B58C22B8A842227293421643901BC29A5 | == |
| FiraSans-Regular.ttf | 456,996 | C29556A2719BF613EF3D5E070E40D903A8965D9C081BECA1375DC1E6E0F93C23 | == |
| **MANIFEST.txt** | 24,908 | **16DCC9399239E5774BF571869B5248DF36DB0D374BF6A159BF1A9839784CAD6D** | 81 PASS / 0 FAIL / 54 NOTE; patch rows S1 0, S2 18, S3 28, S3d 1, S4a 6 |

`build/agent2/native4-bin` (8 files, 363.8 MB; exe and map differ from native3d (S4a SDK + #2); rexruntime.dll and
rexgpu-xenos.dll == devoff4-bin's; native GPU fingerprint 5e3ff55de10f4f64, native3d's 335ff2d47268f3a1):

| File | Size (B) | sha256 | vs native3d-bin |
|---|---|---|---|
| legodimensions.exe | 315,811,328 | 65432C81D8C7D29A35D80A5D971F2373A1188BC43FF3F92232CD1A8A500FB811 | differs |
| legodimensions.map | 43,741,350 | 136CF59158249EED500F3860FB8B49435AE9754786F7BD31C2B97A568F9B8734 | differs |
| rexruntime.dll | 10,898,432 | 870276A6D0E8DE570848FB811591BA5B0AFD8B36413A09F154D0BCAF4902AECA | differs (expected; == devoff4-bin) |
| rexgpu-xenos.dll | 3,406,848 | 59662F767F8B9C7CA78C38370EC6ED6CFB499805F833B458543C206254F65BE5 | differs (expected; == devoff4-bin) |
| amd_fidelityfx_dx12.dll | 6,675,664 | 12A5081257EC95B0B53AD51B4A87FB3C03F97FE0BBB59F9496968F8D50EF93A6 | == |
| TracyClient.dll | 233,472 | 85044850B6C663B5CE8722285D13070381C33C9ABC49D06B3E59BA0277F8FF4E | == |
| achievement_unlocked.wav | 191,018 | A707019154484B9DE0AD310826668C0B58C22B8A842227293421643901BC29A5 | == |
| FiraSans-Regular.ttf | 456,996 | C29556A2719BF613EF3D5E070E40D903A8965D9C081BECA1375DC1E6E0F93C23 | == |
| **MANIFEST.txt** | 27,221 | **00D33D4FFB46776DED60F60C2793C01029E435492013D92B39F2AE39634214DE** | 107 PASS / 0 FAIL / 38 NOTE; patch rows S1 0, S2 18, S3 28, S3d 1, S4a 6 |

### Tool changes (all in build/agent2)

- `stage-snap-bin.ps1` (backup `stage-snap-bin.ps1.pre-S4a`, D68B4533): new `-XenosStrings` (strings that must be in
  rexgpu-xenos.dll) and `-PatchTagList` (overrides the default patch tags; not `-PatchTags`, which would collide with
  `$patchTags` because PowerShell variable names are case-insensitive).
- `stop-snap.ps1`: also stops `run-s4a.ps1` and `prep-s4a.py`.
- New `run-s4a.ps1` (`-Stage off|native`, `-Jobs 10`; refuses to start from 13:50, no relink from 13:58). Guards: time,
  -Jobs cap, no other build driver, notes file, verify S4a, the 6 PATCHES rows, out folder not staged yet; native also
  needs devoff4-bin staged with the same DLLs as install/bin. Builds via `build-snap.ps1`, stages with `-PatchTagList
  S1,S2,S3,S3d,S4a` plus string checks, compares with devoff3-bin/native3d-bin (rexruntime.dll and rexgpu-xenos.dll
  must differ, else exit 15). Logs: `snap4a-run.txt`, `snap4a-steps.txt`, `snap4a-stage-off.log`,
  `snap4a-stage-native.log`.
- New `prep-s4a.py` (dry run / apply, above).
- Launch `run-s4a.ps1` alone in its own command: its driver guard matched my own parent shell once, when the same
  command line also named `stage-snap-bin.ps1` (exit 4).

Skipped (per Agent 1): C1 (#4), the #24 hook, the P2 counter, #18/#20, #26. Nothing applied to the live trees, no git
writes.

## S4 estimate (task #30, for Agent 11's `perf-notes/S4-DRAFT.md`; 07:08; estimates only, nothing built)

Method: `build/agent2/s4-estimate.py` (read-only) parses `.ninja_log` + `.ninja_deps` of my 5 trees (snap1-sdk,
snap1-off, snap1-on, snapB-off, snapB3-on), finds every edge whose recorded deps contain a changed file (PCH users
included) and takes compile wall at -j10 = PCH + max(work/10, longest TU). Full report:
`build/agent2/s4-estimate.txt`. Calibration: for the S3d draw.cpp rebuild it predicts 58 s of compile; the measured
build took 102.7 s, so fingerprint + link + ninja/custom overhead is ~45 s per native build. The logged TU times come
from builds on a busy machine: +-30%. Ranges span the S3d line (snap1 trees) and the B line (snapB-off/snapB3-on),
whichever S4 builds on.

**Cost driver: `rex/system/xmemory.h` is in the generated-code closure.** Through the PCH it reaches all 440 generated
TUs (432 with codegen B), main.cpp and 18-22 rexlego TUs, plus 199 SDK TUs, so changing it is in effect a full rebuild
of both game trees. `rex/thread/timer_queue.h` behaves the same (keep S4 to `timer_queue.cpp`). The other listed SDK
headers (graphics/command_processor.h, shared_memory.h, d3d12/command_processor.h, deferred_command_list.h,
pipeline_cache.h) are in no game TU's deps.

### (1) First S4 batch: SDK runtime files + gpu_native files + 1 new hook, every new switch OFF, no regen

| Step | xmemory.h changed (as listed) | xmemory.h unchanged (only the .cpp files + SDK-internal headers) |
|---|---|---|
| SDK (snap1-sdk, shared) | 200 edges, ~1,710 s work: ~4 min compile + ~25 s relinks (rexruntime.dll 18 s) + install 50-65 s = **~5-6 min** (cf. S1 SDK 269.6 s + install 50.9 s) | 18 edges (the 9 .cpp files alone: 127 s; longest d3d12/command_processor.cpp 36.5 s): ~36 s compile + relinks + install = **~2 min** |
| devoff | 460 edges on the S3d line (452 on B), 7,680 s work (10,020 on B): ~13 min compile (~17 min on B) + link 6 s + gen-check 61 s + gate 3 s + stage 16-25 s = **~15-19 min** (cf. full OFF builds: S1 789 s, B 1,039 s) | 0 game compile edges: re-run CMake + relink + gen-check + gate + stage = **~1.5-2 min** (cf. devoff3: 113.6 s incl. SDK, + stage 16.1 s) |
| native | 485 edges on the S3d line (477 on B3), 9,410-11,140 s work: ~16-19 min compile + fingerprint 8-14 s + link 4-8 s + re-run CMake 7-25 s + stage 30-75 s = **~17-21 min** (cf. full nativeB 1,151 s) | 7 TUs + the new hook TU: ~31-39 s compile (longest device.cpp, rebuilt through the fingerprint header) + ~45 s overhead + re-run CMake + stage = **~2-3 min** (cf. S3d 102.7 s + stage 74.5 s) |
| **Total at -j10, one after the other** | **~37-46 min** | **~6-10 min** (incl. apply, MANIFESTs, gates) |

- New hook .cpp: the 6 existing hooks_*.cpp TUs take 15-24 s each, so it runs beside the other TUs (+0-5 s wall). It
  is native-only if it goes into the gpu_native source list (OFF builds compile no gpu_native code); the
  CMakeLists.txt edit makes both trees re-run CMake (7-25 s each). If the hook also needs a recomp config change (a
  TOML hook/override), that is a regen: see (3).
- Every listed gpu_native file (and native_preparation.h) is a fingerprint input: `native_gpu_build_info.h` is
  regenerated, which also recompiles device.cpp, pipeline_library.cpp and shader_archive.cpp (part of the 7 edges).
- Disk: built in place (my S2/S3/S3d procedure on the snap1 trees, with apply backups): only the 2 new bin dirs,
  devoff ~214 MiB + native ~364 MiB = **~0.56 GiB**, plus a few MB of backups and logs. If the S3d trees must stay
  intact, clone them first: snap1 2.19 GiB + snap1-sdk 0.45 + snap1-off 0.62 + snap1-on 0.96 = **+4.2 GiB** (2-4 min
  of copying).

### (2) Native AOT shader pack (`LEGO_NATIVE_RUNTIME_SHADER_CACHE` -> a real pack)

- The pack is Agent 4's `build/agent4/s35` output (its `-Go` run was still pending at 07:06): `runtime-cache.cpp` with
  4 entries (the placement VS/PS containers) plus a merged `lego-microcode-index.cpp` (19,116 old + 6 new rows).
- Swap-in: `-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=<copy of runtime-cache.cpp>` (a cache variable, now the 869 B stub),
  and the index replaces the fixed-path `rexlego/out/native-gpu/lego-microcode-index.cpp` in the snapshot (1,652,630 B
  in snap1). Both are fingerprint inputs. `snap-native-inputs.py` copies only from live DimensionsRecomp/, so S4 needs
  a hashed copy from build/agent4 (a small option or a separate step, ~10-15 min of prep, not build time).
- Extra edges: re-run CMake; runtime-cache.cpp in the prelink tool (2-4 s with the stub) and runtime_shader_cache.cpp
  (2-3 s); lego_gpu_prelink_runtime.exe relink 1-2 s; runtime prelink + embed (0.6-2.9 s with the stub; ~28 ms per
  shader, so seconds for 4); the index TU 3-4 s; the fingerprint, which recompiles
  device/pipeline_library/shader_archive (~31-39 s); exe link 4-8 s.
- **Bundled into the (1) native build: under +1 min and under 1 MB of extra disk.** On its own (own native bin): ~2-3
  min incl. stage, +~364 MiB for the bin. devoff is unaffected (OFF has no gpu_native).
- For comparison only: changing the MAIN cache (`LEGO_NATIVE_SHADER_CACHE`, 9,532 shaders) would cost ~4-8 min
  (prelink-tool compile of the 35 MB TU 40-60 s, main prelink 64-115 s, embed 62-199 s, then fingerprint + relink) and
  rewrite the 502 MB linked C++.

### (3) Agent 9's codegen change (db16cyc -> `_mm_pause`, `src/codegen/builders/system.cpp`)

- Codegen tool: system.cpp 8 s + rexglue.exe relink: under 1 min. Regen: ~130 s (887 files, 467.3 MB) + gen-check
  ~61 s; or Agent 9 supplies the regenerated tree, as with batch-nolr for build B.
- Rebuild: codegen only rewrites files whose content changed, so only TUs with a db16cyc site recompile, as long as
  `_mm_pause` needs no change to the PCH or a shared header (if the PCH changes, everything rebuilds). The site count
  is unknown; I have not scanned the 467 MB (Agent 9 can count). db16cyc is a spin-wait hint, so few TUs is plausible
  (then ~2-4 min per bin), unverified. If the generator splits TUs by size, added lines could also move functions
  between files.
- Worst case (most TUs, or the PCH): full game rebuilds, devoff ~13-17 min (S1 789 s, B 1,039 s) + native ~16-19 min
  (nativeB 1,151 s) + gates and stage ~3 min: **~35-45 min for both bins.** Bundled with (1) when xmemory.h changes:
  **+3-4 min only** (both game trees rebuild fully anyway).
- Disk: own snapshot like build B: snapshot ~2.1 GiB + OFF tree ~0.6 + native tree ~0.95 + 2 bins ~0.56 = **~4.2 GiB**
  (measured for nativeB alone: 3.36 GB). In place: bins only (+0.47 GiB if the regen output is kept for a diff).

### (4) Disk now

- Free C: **241.45 GiB** (259,261,992,960 B) at 07:02. All of the above together stays under ~10 GiB.
- One bin dir: devoff ~214 MiB (8 files incl. MANIFEST), native ~364 MiB (9 files; nativeB 347.7 MiB). All staged bins
  now: 2.79 GiB (inventory, 05:39).

## Batches 1 and 2: run details (moved out of the RESUME block at 00:45)

**Batch 2 (S2)**
- **S2 applied at 23:15:03** (Agent 1's GO at 23:09). `snap1/PLAN-S2-2314.txt`: same 23805, differing 38 = COPY 18
  (781,066 B), DELETE 0, HELD BACK 20 (all A9 'excluded', 0 'not selected'), 0 errors, 0 warnings. Apply copied 18
  and deleted 0 in 5.5 s: `snap1/PATCHES-S2.tsv` sha256 b25547164383cc75..., `snap1/STATE-S2-2315.tsv` sha256
  48869f6b684076bb.... `verify S2`: 23843 files, 16 backups checked, 0 extra, 0 problems, RESULT: PASS. The first
  plan run (23:13:44) crashed on a BOM in PATCHES-S1.tsv (problem 30) and copied nothing.
- **devoff2: DONE, staged at 23:18:53 to `build/agent2/devoff2-bin`** (`run-s2.ps1 -Stage off`, 23:15:15-23:18:53,
  218.9 s in all). SDK build 23.4 s (8 edges: 5 audio TUs plus relinks of rexruntime.dll, rexgpu-xenos.dll and
  rexglue.exe), install 65.1 s, gen-check 61.4 s PASS, gate 3.2 s PASS, game 32.6 s (2 edges: `rex_app.cpp.obj`,
  which includes audio_system.h, and the exe link). The POST_BUILD copy refreshed rexruntime.dll, so the relink
  contingency was not needed. Stage 24.7 s: 7 files, 214.3 MB, MANIFEST 49 PASS / 0 FAIL, sha256 B87DC2D2CA22379F....
  - exe 170,334,720 B, 7F0B1C1C84BC66FF...; map 39,159,858 B, 3A7BEEF03A527FC4...; rexruntime.dll 10,889,728 B,
    1C45C86977EC594C... (contains `audio_shutdown_detach_worker` and its description); rexgpu-xenos.dll 3,385,344 B,
    77A5300B885C5274.... TracyClient.dll, the wav and the ttf are unchanged from devoff1-bin.
- **native2: DONE, staged at 23:22:38 to `build/agent2/native2-bin`** (`run-s2.ps1 -Stage native`, 23:19:08-23:22:38,
  209.9 s in all). Configure 7.2 s, exit 0 (so the 7-patch `prepare_plume.py --check` passed), gate 3.5 s PASS,
  build 124 s (23 edges: the fingerprint, the 18 gpu_native TUs that include device.h, rex_app.cpp, main.cpp and the
  link; 172 warnings, all -Wdeprecated-declarations; 0 errors). rexruntime.dll already equalled install/bin, so the
  relink contingency was not needed. Stage 55.6 s: 8 files, 363.7 MB, MANIFEST 72 PASS / 0 FAIL, sha256
  D6E7F14F23373FA7....
  - exe 315,790,336 B, 5D1B2DC655616027..., native GPU fingerprint `b7cc74f980e016c3` (S1 was `befeb1184e6c7abc`);
    it contains the 3 LEGO_NATIVE_* names. map 43,709,997 B, 1FFB7EA997DFCBE7....
  - rexruntime.dll (1C45C86977EC594C...) and rexgpu-xenos.dll (77A5300B885C5274...) are the same files as in
    devoff2-bin. amd_fidelityfx_dx12.dll (12A50812...), TracyClient.dll, the wav and the ttf are unchanged from
    native-bin.
- **Window 3** (Agent 1): the user starts it at 00:15 (ends about 01:00-01:15). All heavy work must finish or pause
  by 00:10 and stay off until Agent 1 announces the end.
- **Scope = Agent 10's owner list only**: `build/agent10/b3/S2-include.tsv` (22:31, sha256 E1FF0497...). 19 INCLUDE
  rows: A7 #20 `device.cpp` (contains p1), `device.h`, `fps_counter.h`; A6 `draw.cpp`, `pipeline_snapshot.h`;
  A5 batch 2 `buffers.cpp`, `textures.cpp` and 6 headers incl. the NEW `upload_legacy_paths.h` (all of these in
  `rexlego/src/gpu_native/`); A12 #22 `rexglue-sdk/src/audio/audio_system.cpp` and
  `rexglue-sdk/include/rex/audio/audio_system.h`; A6 #26 `tools/gpu-aot/prepare_plume.py`, `test_prepare_plume.py`
  and the NEW `patches/plume-winsdk-compat.patch`; A2 p2 `thirdparty/plume/plume_d3d12.cpp` (live already equals
  snap1 S1+p2, so it is a hash pin, not a copy). The 20 EXCLUDE rows (A9 #15 B codegen files, not final) stay at
  S1, and so does every file not on the list (S1 plus p1/p2).
- Rules: `build/agent2/S2-rules.txt`, generated 22:40:14 by `python build\agent2\make-rules-from-tsv.py
  build\agent10\b3\S2-include.tsv e1ff04974373119b build\agent2\S2-rules.txt` (include = `owner | rel | live
  sha256`, exclude = `!owner | rel`). All 15 pre-checked files matched their live hashes, and the full sha256s
  Agent 6 sent at 22:44 for the 3 #26 files equal the rules' hashes (checked 22:45). The new literals
  (`LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD`, `LEGO_NATIVE_FPS_CELL_RECTS`, `LEGO_NATIVE_TEXTURE_STAGING_POOL`,
  `audio_shutdown_detach_worker`) are in live and absent from snap1.
- Commands, in order (from R):
  1. `python build\agent2\snap-patch.py plan S2 build\agent2\S2-rules.txt`. Expect COPY 18, HELD BACK 20 (all
     'excluded') and 0 errors. A 'not selected' file is an unexpected live change: it stays at S1; tell Agent 1.
  2. `python build\agent2\snap-patch.py apply S2 build\agent2\S2-rules.txt`, then `... verify S2` (RESULT: PASS).
     Replaced S1 files are backed up in `build/agent2/snap1-backup-S2/`; the log is `snap1/PATCHES-S2.tsv` plus
     `STATE-S2-*.tsv` and `DIFF-S2-*.txt`.
  3. Background: `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s2.ps1 -Stage off`. This
     builds and installs the SDK in snap1-sdk, builds the game in snap1-off with -SkipConfigure, and stages
     `build/agent2/devoff2-bin`.
  4. Then `... run-s2.ps1 -Stage native`: snap1-on WITH configure, staged to `build/agent2/native2-bin`.
  Logs: `build/agent2/snap2-run.txt`, `snap2-steps.txt`, `snap2-stage-<stage>.log`. run-s2 exit codes: 0 done,
  10 build failed, 11 relink failed, 12 rexruntime.dll still differs, 13 stage failed.
- **Why native2 re-configures:** snap1-on has a CONFIGURE_DEPENDS glob on `rexlego/src/gpu_native/*.h`
  (rexlego/CMakeLists.txt:731), and S2 adds a header. The configure runs the new 7-patch `prepare_plume.py --check`
  (FATAL_ERROR on failure). It already passed on live (Agent 6, 22:23) and on snap1's plume with p2, using both the
  live and the S1 scripts (Agent 10, 22:25-22:27). If it still fails (build-snap exit 21, so run-s2 exit 10;
  see `snap2-native-configure.log`), tell Agents 6 and 1 at once and do not edit Agent 6's files. devoff2 is
  unaffected.
- **rexruntime contingency:** the audio change lands in rexruntime.dll, which reaches a game dir only through the
  exe's POST_BUILD copy. If `<tree>\rexruntime.dll` differs from `snap1-sdk\install\bin\rexruntime.dll` after the
  game phase, run-s2 renames the exe and map to `*.pre-S2` and re-runs the game phase as tag `snap2r`, which
  relinks and re-copies.
- Stage checks: both stages pass `-RuntimeStrings` (the audio cvar name and its description); native also passes
  `-ExeStrings` (the 3 LEGO_NATIVE_* names). The native fingerprint WILL change from S1's `befeb1184e6c7abc`,
  because device.h, device.cpp, draw.cpp and prepare_plume.py are fingerprint inputs.
- If Agent 1 opens a new window mid-build, run `powershell -NoProfile -ExecutionPolicy Bypass -File
  build\agent2\stop-snap.ps1` within about 2 min (it also kills run-s2), then re-run the same stage later; ninja
  resumes.
- ETAs from the end of the window: applied +3 min, SDK installed +8, devoff2 staged +15, native2 staged +30.

**Batch 1 (S1): done**
- **S1** was taken at 20:41:57 (`python build\agent2\snap.py S1`). Manifest: `build/agent2/snap1/MANIFEST-S1-2041.tsv`,
  sha256 f81b1499481ee903.... Patches are logged in `snap1/PATCHES-S1.tsv`:
  - **p1** (20:55): Agent 7's perf-csv-rows `device.cpp` 4C15043E -> 4DC63FA0, for the native build only.
  - **p2** (21:34): `plume_d3d12.cpp` B88E4E86 -> 564568D4. Line 505 becomes `static_cast<D3D12_HEAP_TYPE>(5)`
    (problem 27).
  - Native inputs N1 (11 files), N1i (4) and N1d (`research/dxc-1.9.2609`, 33) match Agent 6's table
    (`snap1/NATIVE-INPUTS-*-2055.tsv`). S1 has Agent 12's closure headers (checked 21:37).
- SDK (`snap1-sdk`, incremental): 269.6 s at -j10; install 50.9 s into `snap1-sdk/install`.
- devoff1 (`snap1-off`): game 789.6 s at -j10, 0 errors. Staged at 21:08 to `devoff1-bin`: 7 files, 214.2 MB, all
  PASS; MANIFEST sha256 1E81AA5E...; exe 170,334,720 B, D95273C9....
- native (`snap1-on`, configured 20:58): run 1 stopped at [459/553], on plume only. Run 2 after p2: 438.8 s, exit 0
  (202 -Wdeprecated-declarations, 4 -Wunused-value). Staged at 21:48 to `native-bin`: 8 files, 363.5 MB, 48/48 PASS;
  MANIFEST 91F2F817...; exe 315,745,280 B, 3B329E95..., fingerprint `befeb1184e6c7abc`; map 48428DB0...;
  rexruntime FDB315DC... and rexgpu-xenos BFE1DF8B..., the same files as in devoff1-bin.

## Step 6: PPC .map fix (19:49; Agent 9 needs it for the dev PPC suite)
- File: `DimensionsRecomp/rexglue-sdk/cmake/ppc_test_pipeline.cmake` (sha256 `a807021ed5b0d377...`). Two hunks:
  1. **The symbol-map rule** is now `${CMAKE_COMMAND} -DPPC_NM=<nm> -DPPC_NM_INPUT=<obj, cygwin path>
     -DPPC_NM_OUTPUT=<map> -P ${CMAKE_CURRENT_FUNCTION_LIST_FILE}`, with `DEPENDS <obj> <this file>` and the same
     COMMENT and VERBATIM. Before, it was `nm --numeric-sort <obj> > <map>`, which crashes the bundled Cygwin nm
     with 0xC0000005 because its stdout is a file.
  2. **A script-mode block at the top of the same file** (`if(CMAKE_SCRIPT_MODE_FILE AND DEFINED PPC_NM_OUTPUT)`)
     runs `execute_process(COMMAND nm --numeric-sort <obj> OUTPUT_VARIABLE ...)`, so stdout is a pipe. A non-zero
     exit is a FATAL_ERROR; otherwise the block writes the map. When the file is included normally (configure),
     the block is skipped.
- **Writing the map byte-exact.** `file(WRITE)` opens its file in text mode, so on Windows every LF became CRLF. The
  first test got 0/166 identical, with one extra byte per line. The map is now written with
  `file(CONFIGURE OUTPUT <map> CONTENT <nm output> @ONLY NEWLINE_STYLE LF)`, which writes in binary mode.
  - With @ONLY, file(CONFIGURE) changes only `@VAR@` references and `#cmakedefine` lines. The step fails
    (FATAL_ERROR) if nm's output contains `@` or `#cmakedefine`; the output for these objects has neither.
  - Empty output gives an empty map, as `nm > map` would. That happens for an all-commented test such as
    `instr_vpkpx.s`.
  - `execute_process` drops only NUL bytes and the CR of CR-LF pairs. nm's stdout has neither: 0 CR in 42,373 bytes
    over 166 objects.
- **Tests** (`build/agent2/ppcmap-test/test_ppcmap.py`). Everything is written in that scratch dir: build/sdk is only
  read, the baseline and `rexglue-sdk/out` are untouched, and no `.ninja_log` is edited.
  - (a) Script mode on all 166 `build/sdk/tests/ppc/obj/*.o`: **166/166 maps are byte-identical** to nm's stdout
    captured on a pipe (2 are empty, matching empty output), with 0 CR bytes. A missing input fails the step
    (exit 1) and writes no map.
  - (b) Control: `nm --numeric-sort <obj> > file` still crashes with 0xC0000005 and leaves a 0-byte file.
  - (c) Configure mode: a scratch project includes the pipeline and calls `ppc_add_test_binary()` for all 168
    `tests/ppc/asm/*.s`, as `tests/ppc/CMakeLists.txt` does.
    - The clean Ninja build runs 168 assemble, 168 link and 168 map edges, exit 0. **168/168 maps are
      byte-identical**, and the `.bin` files match build/sdk for the 166 tests both have.
    - A second build reports "no work to do".
    - An incremental build after the pipeline edit re-ran CMake and exactly the 168 map edges.
  - (d) The frozen 0.0.23.3 `rexglue.exe recompile-tests` on those maps: exit 0, 1496 TEST_CASEs.
- **Effect on the trees.** In `rexglue-sdk/out`, the first build after this change re-runs every map edge (the
  command is new) and then `recompile-tests`. The PPC suite no longer needs excluding for the nm crash. build/sdk
  (the baseline) keeps the original pipeline from its own snapshot and is not rebuilt.

## Answers for Agent 1 (19:10)

### Staging: build/baseline-bin
- **Files:**
  - legodimensions.exe (170,414,080 B, sha256 `FB922AC9E29D68F6...`);
  - legodimensions.map (39,101,836 B, `FDFE9965C6D918C1...`);
  - rexruntime.dll (`E01D461823AE3647...`);
  - rexgpu-xenos.dll (`49825FC8326614D6...`), from build/sdk/install/bin, identical to the SDK out tree;
  - TracyClient.dll, from install/bin; nothing imports it;
  - achievement_unlocked.wav and FiraSans-Regular.ttf.

  Full hashes, import tables and checks are in `build/baseline-bin/MANIFEST.txt`.
- README-dev's runtime list is covered (exe, rexruntime.dll, wav, rexgpu-xenos.dll, font). Its `mods` folder row is
  for the installer package, not for running the game.
- **No PDBs exist.** The exe links without `/DEBUG`, and the SDK install and out trees have none. Symbols are in
  legodimensions.map. On request I can make a symbolized relink twin from the same objects
  (`/DEBUG /OPT:REF /OPT:ICF`, so the optimised layout is kept) into `build/agent2/sym` in about 1-2 min.

### (a) Tracy: not active in anything we build (Release)
- `build/sdk` is Ninja Multi-Config (Debug;Release;RelWithDebInfo) and its compile DB lists all three configs.
  The Release entries are 887 SDK TUs with neither `TRACY_ENABLE` nor `REXGLUE_ENABLE_PROFILING`. The only Release
  TU with `TRACY_ENABLE` is `thirdparty/tracy/public/TracyClient.cpp` itself. The 639 hits I saw first were the
  Debug and RelWithDebInfo entries.
- Why: `src/core/CMakeLists.txt:126-131` and `src/system/CMakeLists.txt:96-103` link `TracyClient` and define
  `REXGLUE_ENABLE_PROFILING` only for `$<NOT:$<CONFIG:Release>>`. TracyClient's PUBLIC definitions are
  TRACY_ENABLE, TRACY_ON_DEMAND, TRACY_DELAYED_INIT, TRACY_MANUAL_LIFETIME and TRACY_FIBERS.
- Game TUs in build/baseline: none. build/dev (in-tree SDK, Release): only TracyClient.cpp.
- llvm-readobj: neither the exe, rexruntime.dll nor rexgpu-xenos.dll imports TracyClient.dll, and rexruntime.dll has
  no Tracy strings.
- Project default: `option(REXGLUE_ENABLE_TRACY ... ON)` (SDK `CMakeLists.txt:24`). In Release that only builds and
  installs TracyClient.dll; Debug and RelWithDebInfo builds would be instrumented (on demand).

### (b) Dev OFF build 1 (from a snapshot; mirrors the baseline, so only the sources differ)
- **The snapshot** `build/agent2/snap1/DimensionsRecomp` holds real copies of the live
  `DimensionsRecomp/{rexglue-sdk,rexlego,thirdparty,tools}` and the top-level files.
  - Excluded: `rexglue-sdk/out`, `rexlego/out`, `research/` and `.git` directories. The submodule `.git` files are
    kept (problem 16).
  - `rexlego/generated` was copied once from the pristine 0.0.23.3 output.
  - `game_root` in the manifest is re-pointed for the deeper path.
- **`build\agent2\snap.py <TAG>` refreshes the snapshot.** It copies changed files with mtime = now, so ninja
  rebuilds whatever depends on them. It also re-copies tampered files and deletes removed ones. It writes
  `snap1/MANIFEST-<TAG>-<HHMM>.tsv` (size, mtime and sha256 per file) and `snap1/DIFF-<TAG>-<HHMM>.txt`, which flags
  changed closure headers.

| Tag | Time | Files | Change | Wall |
|---|---|---|---|---|
| S0 | 19:16-19:20 | 23,738 | first copy; generated 887 files | 269.5 s |
| S0b | 19:23 | +20 | 19 file symlinks copied by content (libmspack sources the SDK compiles); new `tests/ppc/asm/seq_tailcall_musttail.s`; changed `src/core/threading_win.cpp` | 6.6 s |
| S0c | 19:26 | +31 | the submodule `.git` files; Agent 6's FSR3 libs (`rexglue-sdk/bin/ffx_sdk/*.lib`); changed `rexlego/src/gpu_native/draw.cpp` and the pipeline | 8.2 s |
| S0d | 19:46 | 23,789 | changed `include/rex/logging/macros.h` (closure; Agent 12, 19:27), `src/ui/rex_app.cpp` (Agent 12) and the pipeline | 8.2 s |

- **`build\agent2\build-snap.ps1 -Phase sdk|game|all [-Jobs N] [-Affinity F] [-SkipConfigure] [-KeepGoing]`**
  - **SDK:** `cmake --preset win-amd64` (Ninja Multi-Config, FidelityFX OFF, x86-64-v2) in
    `build/agent2/snap1-sdk`, with `REXGLUE_BUILD_TESTS=OFF`. Release build, then install to `snap1-sdk/install`.
    build/sdk/install is never touched.
  - **Game:** `build/agent2/snap1-off`: NATIVE_GPU=OFF, Release, x86-64-v3, `CMAKE_PREFIX_PATH=snap1-sdk/install`,
    the frozen codegen tool, and no shim.
  - **Gate:** `snap-gate.py` must pass before the game build. It checks that every include dir is inside snap1*,
    that there are 440 generated TUs, that rexglue_DIR is right, and that the installed rex, fmt, spdlog and simde
    headers hash-equal the snapshot.
  - Step log: `build/agent2/snap1-steps.txt`. Logs: `snap1-*.log`. `-Affinity F` pins every step to CPUs 0-3.
- **History:**
  - SDK configure attempt 1 (19:23) failed in 5 s because the submodule `.git` files were missing (problem 16).
  - Attempt 2 (19:26) was still in its try_compile checks at 19:41 under the load. It then died with its task
    (problem 18), so -j10 never started.
  - Attempt 3, from S0d and pinned to CPUs 0-3: the configure ran 19:46:51-19:51:04 (252.6 s, exit 0), and the SDK
    build at -j3 started at 19:51:04.
- **Timeline from here:** see the top of this note.

### (c) ON build: the same tree (recommended) or its own tree
- The generated TUs' compile commands are flag-identical in OFF build/baseline and ON build/dev; only tree paths and
  the PCH location differ. Only the rexlego/src TUs gain `-DLEGODIMENSIONS_NATIVE_GPU=1` and the two metadata defines.
- The ON block works in find_package mode: `probe-toggle.ps1` configured one find_package tree OFF (11.5 s) and then
  ON (7.8 s), both exit 0. The install exports `rex::renderdoc`, the FidelityFX runtime is passed explicitly,
  and the FSR3 libs are read from `<snapshot>/rexglue-sdk/bin/ffx_sdk/`.
- **Probe result (19:07, `build/agent2/probe-toggle.log`):** one find_package tree (dev rexlego against
  build/sdk/install) was configured OFF (9.8 s) and then ON with Agent 6's stub flags (10.5 s), both exit 0.
  Compile DB diff OFF -> ON:
  - **generated: 440/440 identical; PCH identical;**
  - rexlego/src: 33 changed + 38 ON-only;
  - other, changed (3): `share/rexglue/rex_app.cpp`, `share/rexglue/windowed_app_main_sdl.cpp`,
    `res/legodimensions.rc`;
  - other, ON-only (18): SDK `texture/{util,info}.cpp`, plume_d3d12 + D3D12MA, miniz, zstd,
    `gpu-aot/generate_microcode_index.cpp` and `prelink_shader_cache.cpp`, and the 4 `rexlego/out/native-gpu`
    cache/index TUs.

  `compile-one -SyntaxOnly` of SDK `texture/util.cpp` and `info.cpp` with that DB: exit 0 (6-7 s each). So toggling
  ON in the OFF tree recompiles no generated TU. Still unknown until Agent 6's real inputs land: the compile time of
  the real bank TUs (embedded caches).
- **Agent 6's inputs.** The FSR3 libs are in the live tree and in S0c. Between 20:00 and 20:30 Agent 6 replaces the
  stub `lego-microcode-index.cpp` with the real index (19,116 records) and stages the DXIL cache and the instanced
  and float-blend banks in `rexlego/out/native-gpu/aot/`; the temporal bank stays a stub. The final flags arrive at
  about 20:30 in `perf-notes/agent6-native-aot.md` section 5. I copy the inputs into the snapshot and hash them.
- **Same tree:** stage the OFF outputs first, then reconfigure `snap1-off` with NATIVE_GPU=ON and Agent 6's final
  flags, and build. That is about 70 src TUs, the ON-only TUs, 12 shader headers and the link: **about 6-10 min,
  with no generated-TU recompile** (ninja reruns an edge only if its command or inputs change). Toggling back for a
  later OFF build costs the same few minutes.
- **Own tree** (README-dev style, `REXSDK_DIR=<snapshot>/rexglue-sdk`): about 30 min cold (in-tree SDK about 9 min,
  440 TUs about 18, the rest about 3), and there is no CPU to pre-build it before 20:45.

### Junction warning (step 2)
`DimensionsRecomp\rexlego\generated` is a junction into the pristine baseline output. Never run codegen into it.
Every tree pins `-DREXGLUE_HOST_CODEGEN_EXECUTABLE=build/agent2/codegen-tool/rexglue.exe` (the frozen 0.0.23.3
tool, == build/sdk/install/bin/rexglue.exe), so its in-build codegen edge rewrites nothing (0 written). For codegen
experiments, use a copy of the manifest whose output directory is under your own build/agentN.

### SDK headers in the generated-code closure (step 2)
Editing ANY of these forces a rebuild of all 440 generated TUs (about 17-18 min at -j10), plus every SDK library that
includes them.
- **How they were found:** `clang -M` on `legodimensions_recomp.{0,219,437}.cpp`, `legodimensions_init.cpp` and
  `legodimensions_register.cpp`, using build/dev's real compile commands (`build/agent2/sdk-headers.py`). All five
  include the identical set.
- Paths are relative to `DimensionsRecomp/rexglue-sdk/` (the dev tree you edit). In the find_package trees the same
  files arrive as installed copies under `<install>/include/`.

The list:
- `include/rex/` (64): assert.h, chrono/chrono.h, chrono/clock.h, cvar.h, filesystem.h, filesystem/device.h,
  filesystem/entry.h, filesystem/file.h, filesystem/vfs.h, filesystem/wildcard.h, hook.h, image_info.h, literals.h,
  logging.h, logging/api.h, logging/assert.h, logging/format.h, logging/macros.h, logging/types.h, math.h, memory.h,
  memory/arena.h, memory/mapped_memory.h, memory/ring_buffer.h, memory/utils.h, perf/counter.h, platform.h,
  platform/dynlib.h, platform/fpscr.h, ppc.h, ppc/context.h, ppc/func.h, ppc/function.h, ppc/intrinsics.h,
  ppc/stack.h, stream.h, string.h, string/buffer.h, string/key.h, string/numeric.h, string/utf8.h,
  system/achievement_manager.h, system/achievement_store.h, system/export_resolver.h, system/function_dispatcher.h,
  system/kernel_state.h, system/mmio_handler.h, system/thread_state.h, system/util/native_list.h,
  system/util/object_table.h, system/util/xdbf_utils.h, system/xam/app_manager.h, system/xam/content_manager.h,
  system/xam/user_profile.h, system/xcontent.h, system/xmemory.h, system/xobject.h, system/xtypes.h, thread.h,
  thread/fiber.h, thread/mutex.h, thread/timer_queue.h, types.h, vec128.h
- `thirdparty/fmt/include/fmt/` (2): base.h, format.h
- `thirdparty/simde/simde/` (21): check.h, debug-trap.h, hedley.h, simde-align.h, simde-arch.h, simde-common.h,
  simde-constify.h, simde-detect-clang.h, simde-diagnostic.h, simde-f16.h, simde-features.h, simde-math.h,
  x86/avx.h, x86/avx2.h, x86/mmx.h, x86/sse.h, x86/sse2.h, x86/sse3.h, x86/sse4.1.h, x86/sse4.2.h, x86/ssse3.h
- `thirdparty/spdlog/include/spdlog/` (14): common.h, details/backtracer.h, details/circular_q.h, details/log_msg.h,
  details/log_msg_buffer.h, details/null_mutex.h, details/periodic_worker.h, details/registry.h,
  details/synchronous_factory.h, fmt/fmt.h, logger.h, spdlog.h, tweakme.h, version.h
- Also in the closure, not SDK: `generated/default/legodimensions_{pch,init,funcs}.h` plus the TU's own
  `legodimensions_funcs.N.h`, and the tree's `cmake_pch.hxx`.

Closure headers already edited for batch 1:
- `include/rex/ppc/intrinsics.h` and `include/rex/math.h` (Agent 10).
- `include/rex/system/xmemory.h`, `include/rex/logging/api.h` and `include/rex/logging/macros.h` (Agent 12,
  18:50). Agent 12 changed `macros.h` again at 19:27 (in S0d) and plans no more closure edits.

Problems and fixes (session 3):

1. **Partition coupling (repo bug at 127e04b).** `rexlego/src/native_lock_elide.cpp` is the only src file that
   includes partition headers, `legodimensions_funcs.{154,254,302,389,393,395,410}.h`, chosen to match the
   author's history-dependent `generated/default/codegen.partition.json` (not in the repo). A fresh codegen
   partitions differently, so `sub_83F99290` and `sub_83F9ABE0` are undeclared (3 errors). Fix without touching
   the snapshot or the generated tree: `build/agent2/compat/` (`native_lock_elide_compat.h` = PCH +
   2x `DECLARE_REX_FUNC`, force-included into that TU only by `project-include.cmake` through
   `-DCMAKE_PROJECT_INCLUDE`), in build/baseline and build/dev. Proper fix belongs in the source.
2. CMake 3.28 does **not** honour `SHELL:` in the per-source `COMPILE_OPTIONS` property (clang got
   `'SHELL:-include "..."'` as one file name). Use the joined `-include<path>` form (clang JoinedOrSeparate).
3. `CMAKE_PROJECT_INCLUDE` runs for every `project()`; in build/dev that includes the SDK + thirdparty, so the
   shim is guarded on `PROJECT_NAME STREQUAL legodimensions`.
4. The 9 dxc shader-header edges in build/dev have order-only deps on SDK targets (`ninja -t commands` closure:
   1140 commands, 1131 non-dxc), so they are NOT built through ninja; `ninja -t commands -s` gives each own command.
5. README-dev string check: short literals (<= 15 chars) can be absent from a binary built by clang -O3 (MSVC SSO
   `std::string` built from instruction immediates). `d3d12_bindless` and `GPU/D3D12` are absent from a FRESH
   rexgpu-xenos.dll (DLL 18:02:58 newer than its obj 18:02:48, which has them). Check 16+ char strings.
6. No PDBs in this configuration: the exe links without `/DEBUG`; SDK install/out have none. Symbols = .map.
7. No copy rule for rexgpu-xenos.dll into build/baseline in find_package mode; staged from build/sdk/install/bin
   (== SDK out tree, sha256 49825FC8...). exe/rexruntime.dll need only system DLLs (VC++ runtime in System32).
8. PowerShell: `H` is the `Get-History` alias (my function was shadowed); `$r` is `$R`; `Start-Process -PassThru`
   needs `$p.Handle` cached or `ExitCode` is null.
9. The in-build codegen edge ran its 109.5 s analysis once in build/baseline (0 written); stamp now current.
10. x86: SDK x86-64-v2 + game x86-64-v3 kept (README-dev's documented pair; build/dev gives the same pair).
11. **Correction (Tracy):** my 18:5x note that the baseline SDK libraries were compiled with Tracy on was wrong. The
    639 `TRACY_ENABLE` hits were the Debug and RelWithDebInfo entries of build/sdk's multi-config compile DB; in
    Release only TracyClient.cpp has it. See (a) above.
12. PowerShell 5.1: `Tee-Object -Append` writes UTF-16LE into an existing UTF-8 log, and pipeline output inside a
    function leaks into its return value (the probe's `$c1 -ne 0` became an array test and printed a bogus
    "configure failed"). Fix: `filter Log { $_ | Out-File -Append -Encoding utf8 $log; Write-Host $_ }`.
13. agy-grid delivers only the text on the `@@to` line itself; every message is one line and details live here.
14. Agent 8 (19:0x) fixed the dev tree's `native_lock_elide.cpp`: it declares its 21 callees with
    `DECLARE_REX_FUNC` and compiles with or without the shim. The shim is now only needed for build/baseline
    (snapshot 127e04b). build/dev still carries it (harmless); it goes at the next build/dev reconfigure. New trees
    (snap1-*) are configured without it.
15. Snapshot copies: the libmspack sources the SDK compiles are file symlinks, and moltenvk has 8 directory links.
    S0 skipped all 27 reparse points. snap.py now copies file symlinks by content (19) and skips the directory links
    (moltenvk is macOS-only).
16. The SDK configure needs each submodule's `.git` FILE: `thirdparty/CMakeLists.txt:72` checks
    `EXISTS <submodule>/.git` and fails with "Git submodule 'cli11' is not initialized". snap.py keeps the `.git`
    files (31) and skips `.git` directories. git itself is not needed: the version falls back to
    0.10.0.0-dev.unknown, as in the baseline.
17. The first snapshot copy took 269.5 s (23.7k files, about 1.5 GB, through `\\?\` paths). Refreshes take 6-9 s.
18. Processes started under a run_command task die with it. At 19:40 I killed only the build-snap.ps1 PowerShell, so
    that the slow SDK configure could finish without a -j10 build following it. That ended task-398, and its
    process tree took the configure with it. CMake writes CMakeCache.txt only at the end of a configure, so every
    check result was lost and attempt 3 started from scratch. To stop a build, kill its task or run
    `build/agent2/stop-snap.ps1`; to keep a child alive, don't end its task.
19. Step 6: CMake `file(WRITE)` writes in text mode on Windows, so LF becomes CRLF. Use
    `file(CONFIGURE ... NEWLINE_STYLE LF)` (binary mode) when the bytes matter. `execute_process` drops NUL bytes and
    the CR of CR-LF pairs from captured output.
20. PowerShell: `[IO.File]` methods resolve relative paths against the process cwd, not the `Set-Location`
    directory, so use full paths.

# Session 2 resume note (16:55, superseded by the block above)

**Paused 16:55 for the agy-grid restart. Nothing of mine is running. All trees are consistent, and
Ninja resumes incrementally.** Free C: 23.57 GB at 16:48.

Problems and fixes (session 4, 19:57-21:50):

21. **The notes were wiped at 19:59:40.** `open(p,'wb').write(open(p,'rb').read()...)` truncated this file before it
    read it. A subagent replayed my transcript into `build/agent2/recovered/` (`recover-notes.py`; REPORT.txt has
    19/19 checks passing), and I copied the 19:57 state back. Rule: never read and write the same file in one
    expression. `build/agent2/splice-notes-top.py` reads the file first, backs it up, writes `.new` and then
    `os.replace`s it.
22. **`start "" /b /wait /affinity F` hides exit codes.** The S0d pre-build ran under it, so both the S0d gate (which
    had in fact failed on version.h, item 24) and the SDK -j3 build looked like exit 0. Fix: `build-snap.ps1`'s
    Step() also fails a step (exit 98) when its log has `^ninja: build stopped`, `^ninja: error`, `^FAILED: ` or
    `^CMake Error`. The -j10 runs don't use -Affinity.
23. **A fresh build dir re-runs codegen, and `snap.py` rewrites only `game_root`, not `[entrypoint] file_path`.**
    The S0d game build failed at 20:11:25 with "Entrypoint XEX not found .../snap1/.../rexlego/../../game/disc/Default.xex".
    The fix has two parts:
    - `REXGLUE_HOST_CODEGEN_EXECUTABLE=build/agent2/codegen-frozen/codegen-frozen.exe`, a stand-in that keeps the
      pinned 0.0.23.3 output and writes nothing.
    - `gen-check.py`, a build-snap step before the gate: snap1's generated output == baseline, 886/886.
    The codegen edge re-runs on every build because its stamp is older than the snapshot manifest. Restat means
    nothing downstream rebuilds.
24. **The gate rejected `include/rex/version.h`.** That header is configure-generated (configure_file from
    `version.h.in` into `snap1-sdk/include/rex`). `snap-gate.py` now passes it when the snapshot has `<rel>.in` and
    the installed copy hash-equals the configured one.
25. **I missed the 20:15 S1 deadline** because the timer was delivered late. S1 was taken at 20:41:57, and Agent 1
    confirmed there were no live edits after 20:15.
26. **`snap-native-inputs.py` N1d exited 1** because `| Select-Object -First 4` closed the pipe while it printed rows
    (BrokenPipe). The copy and its TSV had already completed (33 rows). Don't truncate its output with a pipe.
27. **Plume needs a newer d3d12.h** (native build run 1, 21:07-21:28).
    - `thirdparty/plume/plume_d3d12.cpp:505` returns `D3D12_HEAP_TYPE_GPU_UPLOAD` unconditionally in
      `toD3D12(RenderHeapType)`.
    - This machine has only Windows SDK 10.0.22621.0, whose d3d12.h lacks that enumerator. Its value is 5 in WinSDK
      >= 10.0.26100, the Agility SDK and DirectX-Headers. Plume configures with "D3D12 Agility SDK: OFF".
    - Nobody had compiled plume_d3d12.cpp on this machine before: the step-5 compile-one sweep covered only
      rexlego/src. Every rexlego/src TU waits behind plume, so run 1 stopped at [459/553] with only this error.
    - Fix S1+p2 (Agent 1's spec): `return static_cast<D3D12_HEAP_TYPE>(5);` on the same line, so the line count is
      unchanged. `prepare_plume.py --check` still passes, because no patch hunk is near line 505.
    - Behaviour is unchanged. Without the Agility SDK, plume never queries OPTIONS16, so
      `capabilities.gpuUploadHeap = uma`, and UMA devices take the custom-pool fallback (`gpuUploadHeapFallback`).
    - Agent 6 makes the same change in the live tree.
    - Run 2 (21:36:54-21:44:14): 438.8 s, 96 edges, exit 0, 0 errors. 206 warnings: 202 -Wdeprecated-declarations
      (native renderer) and 4 -Wunused-value (thirdparty miniz.h).
28. **The orchestrator's PreToolUse hook rejected one run_command** (exit 1, no reason given). It grepped
    plume_d3d12.cpp and `prepare_plume.py`, probably with a git subcommand string in the pattern. Simpler commands
    without such strings passed. Never bypass the hook.
29. **edit_file did not match a target that contained text with double backslashes** (the old RESUME block). Python
    splices (`splice-notes-top.py`) avoid that, and new notes use forward slashes in paths.
30. **`snap-patch.py plan S2` crashed with an IndexError** (23:13:44, sorting the PATCHES rows in `make_plan`).
    `snap1/PATCHES-S1.tsv` starts with a UTF-8 BOM (it was written from PowerShell), so its `#` header line was read
    as a 1-column row. Fix: `load_tsv_rows` opens every TSV with `utf-8-sig`. The plan re-ran clean at 23:14:44; the
    crashed run copied nothing (plan mode only writes the PLAN file, and it died before that).

## Done (session 2)

1. devshell: clang 23.1.6, MSVC 14.40.33807, WinSDK 10.0.22621.0, CMake 3.28.3, Ninja 1.11.0.
   Deleted `toolchain/_downloads/*.tar.zst` (276 MB) and the stale `.parts/` (31.6 MB).
2. plume: gitlink `ceaeeee` is unfetchable, so it is on public pin `e0c8871` with 6 patches from
   `tools/gpu-aot/prepare_plume.py`. `--check` **PASS**. Plume submodules use `--depth 1` (100 s).
3. SDK `thirdparty/FidelityFX-SDK` is **initialised** at `eee08db` ("Linux fix"). Shallow fetch took
   983 s at ~115 KB/s. Agent 6 can use the FSR3 headers now (`sdk/include`); prebuilt DLLs are in
   `PrebuiltSignedDLL/`.
4. Snapshot `baseline/DimensionsRecomp` = `git archive` of 127e04b + SDK 2897c31, verified at 832 + 1338
   files. 24 SDK gitlinks and plume are junctions to the dev checkouts, so **simde, plume and
   FidelityFX are shared with dev**. `thirdparty/snapdragon-gsr` is empty: no URL, and nothing
   references it at 2897c31.
5. `build/sdk-dev` configured (configure-only; FidelityFX OFF; tests ON; 339 s; 2664 DB entries).
   `env/compile-one.ps1` is written and tested:
   - `clock.cpp` to an obj: 8.4 s
   - `-SyntaxOnly`: 3.5 s
   - fallback when the PCH is missing: 10.1 s
   Usage: `powershell -NoProfile -File env\compile-one.ps1 <file.cpp> -OutDir build\agentN\obj [-SyntaxOnly] [-Db <compile_commands.json>] [-Config Release] [-Target <obj-substr>] [-PrintOnly] [extra clang flags]`.
6. `build/sdk` configured (322.5 s; FidelityFX OFF, the same as dev, per Agent 1 16:48 (5)).
   **Build run 1 stopped at [929/1410] after 456.9 s.** The bundled Cygwin `tools/binutils/powerpc-none-elf-nm.exe`
   crashes with 0xC0000005 whenever its stdout is a *file* (cmd `>`, as in `cmake/ppc_test_pipeline.cmake`).
   Into a pipe it works. As a result, 7 `tests/ppc/bin/instr_*.map` edges failed. This is environmental
   (likely an old `cygwin1.dll` on Windows 26100); `as` and `ld` work.
7. Manifests are written: `baseline/DimensionsRecomp/rexlego/legodimensions_manifest.toml`
   (game_root `../../../game/disc`) and a dev copy. Agent 3 has `game/disc/Default.xex` + `.xexp` in place.

## Not done / found at the pause

- `python DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py --check` **FAILS** ("Native __m64
  streaming-store fix is missing", exit 2). Build run 1 compiled against unpatched SIMDe, so apply
  the fix before resuming. simde is not in my claim list, so `@@claim DimensionsRecomp/rexglue-sdk/thirdparty/simde/**` first.
  Ninja then recompiles the SIMDe users on its own.
- Plan change (Agent 1 16:48): the baseline game is **NATIVE_GPU=OFF** (README-dev step 4). The native ON
  inputs come from Agent 6 (J1) for a compile-only ON configure in `build/dev`. Copy
  `legodimensions.map` next to every staged exe.

## Exact next commands

```powershell
$R = '<workspace>'; Set-Location $R
# 0. SIMDe fix (after @@claim). simde is shared with baseline through the junction.
python DimensionsRecomp\rexglue-sdk\scripts\prepare_simde.py; python DimensionsRecomp\rexglue-sdk\scripts\prepare_simde.py --check
# 1. keep the run-1 logs (the codegen watcher keys on "END   build" in the steps file)
Rename-Item build\agent2\sdk-baseline-steps.txt sdk-baseline-steps-run1.txt; Rename-Item build\agent2\sdk-build.log sdk-build-run1.log
# 2. resume the SDK build past the PPC nm failures (run_command background task, NOT Start-Process)
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-sdk-baseline.ps1 -SkipConfigure -KeepGoing -CtestExclude '<ppc test regex from sdk-ctest-list.log>'
# 3. codegen watcher (second background task): waits for rexglue.exe, then runs codegen.
#    The log must show "XEX patch applied successfully ... new version: 0.0.23.3".
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\codegen-watch.ps1
New-Item -ItemType Junction DimensionsRecomp\rexlego\generated -Target $R\baseline\DimensionsRecomp\rexlego\generated
# 4. baseline game, NATIVE_GPU=OFF, x86-64-v3, Release, from baseline\DimensionsRecomp\rexlego into build\baseline.
#    Then stage the exe, rexruntime.dll, rexgpu-xenos.dll, PDBs and legodimensions.map into build\baseline-bin.
```

PPC follow-up, off the critical path: produce the 7 maps through a pipe, then add matching
`.ninja_log` entries (MurmurHash64A of the edge command), or report the PPC suite as blocked.

---

# Session 1 report (history): toolchain + baseline builds (PARTIAL)

Status at 12:35: **partial, stopped on the orchestrator's battery stop-plan.** The LLVM download
could not finish by 12:45, so per the plan nothing was built and the SDK submodule init was not
started. `env/devshell.ps1` is written and tested (VS x64 env, CMake, Ninja), but **clang is not
installed yet**. Do not announce the devshell until LLVM is extracted.

## What is installed and where

All paths relative to `games/lego-dimensions-recomp/`.

| Item | State | Notes |
|---|---|---|
| `env/devshell.ps1` | done, tested | VS 2022 x64 env (cached), CMake + Ninja on PATH, picks up `toolchain/llvm-*` automatically once extracted |
| `env/.cache/vsenv-x64.json` | generated | cached `vcvars64.bat` delta, machine-specific, rebuilt automatically if VS/MSVC changes (or `-Refresh`) |
| `toolchain/segdl.ps1` | done | resumable multi-connection curl downloader (range requests, numbered chunks, join plus SHA256 check) |
| `toolchain/_downloads/clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst.parts/` | **11.5%** | 13 chunk files, 31,652,927 of 276,226,344 bytes. Resume with the command below; keep `-Segments 10` |
| `toolchain/llvm-23.1.6/` | **missing** | extract after the download completes |
| `env/compile-one.ps1` | not written | needs `build/sdk/compile_commands.json` |
| `build/sdk`, `build/agent2/gpu-aot` | not created | no builds this session (stop-plan) |
| SDK submodules / `thirdparty/plume` | not initialised | stop-plan: init is heavy and the network is very slow (see below) |

## Versions on the machine (checked)

| Tool | Version | Path |
|---|---|---|
| Visual Studio 2022 Community | 17.10.35004.147 | `C:\Program Files\Microsoft Visual Studio\2022\Community` |
| MSVC | 14.40.33807 | `...\VC\Tools\MSVC\14.40.33807\bin\HostX64\x64` |
| Windows SDK | 10.0.22621.0 | `C:\Program Files (x86)\Windows Kits\10` (rc.exe, mt.exe x64) |
| CMake | 3.28.3-msvc11 | VS bundled `...\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin` |
| Ninja | 1.11.0 | VS bundled `...\CommonExtensions\Microsoft\CMake\Ninja` |
| git | 2.56.1.windows.1 | `C:\Program Files\Git\cmd` |
| tar | bsdtar 3.8.9 (libarchive, has zstd and xz) | `C:\Windows\System32\tar.exe` |
| PowerShell | Windows PowerShell 5.1.26100 | agents' shell |
| clang | **none on PATH**. `VC\Tools\Llvm` exists but holds no `clang.exe` (VS clang component not installed) | |
| Free disk on C: | 63.3 GB | |

CMake 3.28 satisfies the SDK (`cmake_minimum_required(3.25)`, presets v6). The SDK requires
**Clang >= 18** (`rexglue-sdk/CMakeLists.txt:119-122`), stricter than the 17 in README-dev.

## LLVM choice

- Latest stable per the GitHub API (`releases/latest`): **LLVM 23.1.6**, published 2026-11-17.
- Chosen archive: `clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst`, 276,226,344 bytes,
  sha256 `7623f582089983c1cb51030cf1996514b19464e5669099571b399e8543770155` (GitHub asset digest).
- Alternatives: `.tar.xz` 901,284,676 bytes, sha256 `16af05919cf36958dfb4ddaa4fc4d9d4ff577f5daeb76bc112ea49cd8ced82b2`;
  `LLVM-23.1.6-win64.msi` 639,686,385 bytes.
- The zst is 3.3x smaller, and the system tar can unpack it. That gap is bigger than compression
  alone would explain, so after extracting, **check** that `bin/` has clang, clang++, clang-cl,
  lld-link, llvm-ar, llvm-ranlib, llvm-rc, llvm-mt and clang-scan-deps, and that
  `lib/clang/23/include` and `lib/clang/23/lib/windows/clang_rt.builtins-x86_64.lib` exist.
  If anything is missing, use the `.tar.xz` instead.

## Network (why the download did not finish)

| Measurement | Result |
|---|---|
| Wi-Fi link speed | 866.7 Mbps |
| Single curl, GitHub release asset | 66 KB/s (8 s sample); 23.1 MB in 695 s (about 33 KB/s average) |
| Cloudflare speed test, run at the same time | 21.6 KB/s |
| Interface counters | rx 94 KB/s, **tx 113 KB/s** (12 agents' API traffic) |
| 10 parallel range connections (segdl) | about 75 KB/s in total, 0.7 MB in 4 min: **no gain** |

The bottleneck is the shared link (probably the busy uplink), not one connection. At this rate the
remaining 232 MB of LLVM takes about 55 min. Full clones of the SDK submodules (FFmpeg, SDL3,
tracy, imgui, glslang, spirv-tools, ...) would take many hours. Next session, either use a
faster or quieter network, or allow `--depth 1` for the submodule clones (needs orchestrator OK,
because the granted command is `git submodule update --init --recursive`).

## devshell.ps1: test results

Command: `powershell -NoProfile -Command ". games/lego-dimensions-recomp/env/devshell.ps1; ..."`, run from the workspace root.

- First load (cache miss, runs `vcvars64.bat`): 16.05 s wall for the whole child PowerShell (bare startup 1.32 s).
  With `-Refresh -Jobs 3`, after the final edit: 13.47 s.
- Cached load: 3.01 s wall including startup. After the final edit, which skips `vswhere` when the cache is valid,
  it measured 3.24 s and 3.48 s against a bare startup of 1.15 s. No measurable gain: the shared CPU is noisy and
  the PS 5.1 JSON parse dominates.
- Tested on Windows PowerShell 5.1 only. `pwsh` (PowerShell 7) is not installed.
- Resolves `cl`/`link` from MSVC 14.40.33807 HostX64\x64, `rc`/`mt` from WinSDK 10.0.22621.0 x64,
  and `cmake`/`ninja` from VS. INCLUDE has 8 entries.
- Sets `CMAKE_GENERATOR=Ninja` and `CMAKE_BUILD_PARALLEL_LEVEL=4` (`-Jobs N` overrides; verified with `-Jobs 2`),
  plus `LEGO_ROOT`, `LEGO_GAME`, `LEGO_SDK`, `LEGO_SDK_BUILD` and `LEGO_LLVM`.
- Sourcing it again in the same session does not grow PATH (43 entries before and after).
- With no LLVM present it prints a warning and leaves `CC`/`CXX` unset (observed). Once
  `toolchain/llvm-<ver>/bin/clang.exe` exists it puts that `bin` first and sets `CC=clang`, `CXX=clang++`
  (not yet exercised).
- Only environment variables change. The script runs in its own scope, so no variables or functions leak into the caller.

## Exact commands run (in order)

```powershell
# latest release + asset digests
Invoke-RestMethod https://api.github.com/repos/llvm/llvm-project/releases/latest
Invoke-RestMethod https://api.github.com/repos/llvm/llvm-project/releases/tags/llvmorg-23.1.6
# single-connection download (killed after 695 s, 23,097,344 bytes kept as chunk seg000_000)
curl.exe -L --fail --retry 3 -s -S -o clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.6/clang%2Bllvm-23.1.6-x86_64-pc-windows-msvc.tar.zst
# segmented download (stopped at 12:30 on the stop-plan)
powershell -NoProfile -ExecutionPolicy Bypass -File toolchain\segdl.ps1 -Url <same url> -Size 276226344 -OutFile toolchain\_downloads\clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst -Segments 10 -Sha256 7623f582...0155
# devshell test (see above)
```

Read-only inspection: `git log`/`git describe`/`git submodule status`/`git ls-files -s` in both repos, plus `vswhere`.

## Failures and fixes

1. **Slow network** (see table). Fix tried: the segmented downloader, which did not help. Stopped on the stop-plan;
   partial data is kept and resumes.
2. **My cleanup command killed its own shell**: a `CommandLine -like '*segdl.ps1*'` filter matched the
   cleanup command itself. Re-ran it excluding `$PID`. No other effect.
3. **Predicted, not yet hit:** in `rexglue-sdk`, `git submodule status` fails with
   `fatal: no submodule mapping found in .gitmodules for path 'thirdparty/FidelityFX-SDK'`. The index has a
   gitlink (`160000 eee08db1688ac3d1275a70b728f4a8ba22914213`) with no `.gitmodules` entry. A bare
   `git submodule update --init --recursive` will very likely die on it ("No url found for submodule path").
   Fix: pass the mapped paths explicitly (command below). FidelityFX is optional (`REXGLUE_ENABLE_FIDELITYFX=OFF`).

## Findings that affect the next session

- **SDK artifacts ignore the binary dir.** `rexglue-sdk/CMakeLists.txt:258-260` sets
  `CMAKE_{RUNTIME,LIBRARY,ARCHIVE}_OUTPUT_DIRECTORY` to `${REXGLUE_ROOT}/out/${REX_PLATFORM}` as normal
  variables, so a `-D` on the command line cannot override them. Even with `-B build/sdk`, the libs, exes and DLLs land
  in `DimensionsRecomp/rexglue-sdk/out/win-amd64/<Config>/` (git-ignored). Consequences: claim
  `DimensionsRecomp/rexglue-sdk/out/**` for the baseline build, and **other agents must not link SDK
  targets in their own trees at the same time**, because they would overwrite the same files. Object-only
  checks through `compile-one.ps1` are safe.
- The preset sets `binaryDir` and `CMAKE_INSTALL_PREFIX` inside the source tree. Override both on the command line (below).
- `REXGLUE_BUILD_TESTS` is OFF by default. The tests are `tests/unit` and `tests/ppc` (PPC asm, bundled `tools/binutils`);
  `tests/regression` is Linux-only.
- `thirdparty/CMakeLists.txt` adds xxHash, disasm, fmt, spdlog, utfcpp, vulkan-headers, VMA,
  vulkan-loader (EXCLUDE_FROM_ALL), moltenvk, sdl3, spirv-headers, glslang and catch2, plus FidelityFX through a guarded include.
- gpu-aot: all 19 checks listed in its `CMakeLists.txt` have sources present. The folder has 102 `test_*.cpp`;
  the rest are not in the portable list. It only needs a C++20 compiler, no SDK or submodules.
- To verify next session: whether CMake 3.28 writes a usable `compile_commands.json` for **Ninja Multi-Config**
  and which config's flags it holds. `compile-one.ps1` must select the Release entries (`/Release/` object
  paths, `-O3`). If 3.28 falls short, drop a newer portable CMake into `toolchain/cmake-*`; devshell prefers it automatically.

## Resume plan (next session, in order)

```powershell
$R = "<workspace>"
# 1. resume the LLVM download (absolute paths; must keep -Segments 10)
powershell -NoProfile -ExecutionPolicy Bypass -File $R\toolchain\segdl.ps1 `
  -Url "https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.6/clang%2Bllvm-23.1.6-x86_64-pc-windows-msvc.tar.zst" `
  -Size 276226344 -OutFile "$R\toolchain\_downloads\clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst" `
  -Segments 10 -Sha256 7623f582089983c1cb51030cf1996514b19464e5669099571b399e8543770155
# 2. extract, rename (no '+' in the path), check the file list from "LLVM choice"
Set-Location $R\toolchain; tar -xf _downloads\clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst
Rename-Item clang+llvm-23.1.6-x86_64-pc-windows-msvc llvm-23.1.6
. $R\env\devshell.ps1; clang++ --version      # then post "devshell ready"
# 3. submodules (explicit paths because of the unmapped FidelityFX-SDK gitlink)
Set-Location $R\DimensionsRecomp\rexglue-sdk
$paths = git config -f .gitmodules --get-regexp '\.path$' | ForEach-Object { ($_ -split ' ', 2)[1] }
git submodule update --init --recursive --jobs 8 -- $paths
Set-Location $R\DimensionsRecomp; git submodule update --init thirdparty/plume
# 4. SDK baseline (claim DimensionsRecomp/rexglue-sdk/out/** first)
. $R\env\devshell.ps1
cmake --preset win-amd64 -S $R\DimensionsRecomp\rexglue-sdk -B $R\build\sdk `
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DREXGLUE_BUILD_TESTS=ON -DCMAKE_INSTALL_PREFIX=$R/build/sdk/install
cmake --build $R\build\sdk --config Release -j 12
cmake --install $R\build\sdk --config Release
ctest --test-dir $R\build\sdk -C Release --output-on-failure
# 5. env/compile-one.ps1 <source> -OutDir <dir> [-SyntaxOnly]: look up the Release entry for <source> in
#    build/sdk/compile_commands.json, rewrite -o (and any -MF/-MD dep file) into -OutDir, and for
#    -SyntaxOnly replace "-c ... -o ..." with -fsyntax-only. Then post "SDK built; compile-one ready".
# 6. gpu-aot portable checks
cmake -S $R\DimensionsRecomp\tools\gpu-aot -B $R\build\agent2\gpu-aot -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++
cmake --build $R\build\agent2\gpu-aot -j 4
ctest --test-dir $R\build\agent2\gpu-aot --output-on-failure
```

## What is left

LLVM download (88.5%) and extract; the "devshell ready" announcement; SDK submodule init plus `thirdparty/plume`;
the SDK configure, build, install and tests (unit plus PPC asm) with timings; `env/compile-one.ps1`; the gpu-aot
portable checks; and filling this report in with build times and test results.
