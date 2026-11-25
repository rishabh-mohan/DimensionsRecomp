# SESSION3: M2 (successor of Agent 2) log, task S3T-2

Overseer: Agent 4. Rules: build/agent1/session3/BRIEF-COMMON.md. No git writes, never touch Minecraft.

## 2026-11-25

- 01:21 apply re-check vs game HEAD c9e215f (notes-only over b0bd3b4) and SDK 5350b1d, live + snap1:
  `session3/apply-check-s3.py` -> `session3/apply-check-0121.txt`. All results as in PENDING-DIFFS, 0 "Skipped patch".
  Only change: `build/agent10/t27/r21-s4t1.md` now 7736004D2DFC1B46... (Agent 10's 07:49 follow-up).
- `session3/s33-popin-no5.patch` = rated #33 (0D230244...) minus hunk #5: 10495 B, sha256 4061ED2D3F3379444... (full:
  4061ED2DB7BBB64D7ECFA024F3F3379444493D085F8A6FB0CB51B1D25AE67E76). +101/-23 in 4 files.
- `session3/deps-s33.txt`: #33 touches only rexgpu-xenos.dll objects (10 TUs); the game includes no rex/graphics headers.
- 01:26 LOAD GO (builds only): one build at a time, <=2 threads, Idle priority, no game runs.
- 01:27 scripts: recompile.py, relink.py, holdrun.py now run children at Idle by default (`--priority idle|belownormal`);
  relink.py `--link-flag` (appended to LINK_FLAGS; used as `-Xlinker /threads:2`); recompile.py `--include-first DIR`.
  Backups `*.pre-S3` (recompile 966C0F04, relink 6BB8E89C, holdrun 9D9BD293).
- 01:28 CG26 started: deleted cg26 `generated/default/codegen.stamp`; regen under holdrun at Idle, log `cg26/codegen.log`.
- M7 relay: for non-repo applies use `git -c core.autocrlf=false apply` (global autocrlf=true writes CRLF).
- 01:30:52 regen exit 0 (141.8 s). 01:31 gates FAIL (1): codegen.d prerequisite ORDER differs (manifest before config),
  same set after the tree-path swap. Changed `cg26/cg26-check.py` (backup .pre-S3 6D202527) to accept a set-equal
  depfile with a NOTE. 01:32 gates-0132.txt PASS (20 pauses), staged cg26/tu, tu-ctl, lists.
- 01:33 recompile ctl 10 TUs -j2 Idle 90.2 s; 01:34 on 55.9 s; 0 failures.
- 01:35 relink ctl (/threads:2) == snap1-off exe + map except timestamps; relink on: exe 45952D171D6204A1, map 1ECC3480.
  `mapcheck --mode same` vs devoff4b: 1 FAIL by script design (expects gpu_wait_backoff.cpp.obj to define no sub_;
  true only for native); per-object sets equal devoff4b. `--mode s4c` vs devoff4-bin: PASS (mapcheck-cg26-s4c.txt).
- 01:35:52 staged `devoff4b-cg26-bin`, MANIFEST sha256 917AE86E6C0CC9B370901397EF8FD72F65449E5EC9594D14D9902215BBBC1D5C.
  01:36 Agent 9 kit18 (static) RESULT PASS -> cg26/checks/kit18. Reported to the Overseer.
- 01:36:15-25 CTR recompiles ctl (E049CA08, 6.5 s) and on (904BFA74, 2.0 s) ran before the Overseer's 01:36:32 "no
  further builds tonight" arrived; disclosed. Nothing else started. CTR relink/stage, #33, devoff4bv, #19 wait for a
  morning GO. Prepared: `session3/prep-s33.py` (dry run PASS, 10 objects), `session3/BUILD-PLANS.md`.
- PENDING-DIFFS.md: 11-25 update note + r21-s4t1.md row.

## 11-25 night, new M2 (successor; conv a657e030)

- 02:33 brief: build cap lifted by the user (all cores); build order devoff4bv -> s33 -> s33d -> CTR -> (#19); hard stop
  03:35, moved to 03:45 by the Overseer at 02:34. Prep only until COMPILE GO.
- 02:34 checks: patches c1-verify-fix.diff 66B9254E, s33-popin-nohunk5.patch 57CFA8AD, s33-popin-nohunk5-diagd.patch
  797E6142 (sha256 match). snap1 SDK blobs: pipeline_cache.h 7e81db3b, d3d12/command_processor.cpp 6f21eb6f,
  pipeline_cache.cpp 55e9f02e, frame_stats.h 8c169b41, shared_memory.cpp 59a636d7 (sha256 A4A31038) = 5350b1d.
  Shared DLL snap1-sdk/install/bin/rexgpu-xenos.dll E3CB99CF. New `session3/verify-bins.py`: devoff4b-bin DE11A914,
  devoff4b-cg26-bin 917AE86E, native4b-bin B63769FE all 0 FAIL (`session3/verify-shared-0234.txt`).
- 02:35 overlays (fresh copy of snap1 src/graphics + patched headers each, `session3/prep-s33.py`, RESULT PASS each):
  `s33/devoff4bv` (1 TU; after F38B47CB), `s33/s33` (10 TUs; after == TESTPLAN ยง0), `s33/s33d` (10 TUs; cp.cpp
  97257A20), `s33/r19` (s4-r1s2.diff 06B0D371; 9 TUs; after == agent7 new/sdk). ninja deps over all 759 snap1-sdk
  Release objects: cp.h/dcl.h are included only by those 9 rexgpu-xenos objects; snap1-off (game) includes none.
- 02:38 new driver `session3/build-bin.py` (CTL recompile+relink --compare devoff4b DLL, ON recompile/relink,
  needles, stage-variant (atomic), verify-bins on new + 3 shared bins, E3CB99CF re-hash). Dry runs: commands and link
  edge OK (37 explicit inputs; every replaced object is one of them).

## 02:41-02:48 builds (COMPILE GO 02:41; all cores, normal priority; last compiler/linker exit 02:47:30)
Driver build/agent2/session3/build-bin.py (log s33/<tag>/build-bin.txt, ctr/build-bin.txt). Each: CTL recompile+relink == devoff4b DLL except 1 TimeDateStamp, ON recompile/relink, needles, atomic stage-variant, verify-bins new + devoff4b/cg26/native4b 0 FAIL, shared DLL E3CB99CF re-hashed after, exe/rexruntime == devoff4b, no cache/.
- devoff4bv-bin (02:43) MANIFEST 353846A3...; DLL 82A0DE74...; C1 verify fix 66B9254E, 1 TU.
- devoff4b-s33-bin (02:44) MANIFEST 50CC5BE2...; DLL 0B57BBD5...; nohunk5 57CFA8AD.
- devoff4b-s33d-bin (02:45) MANIFEST 0B1CD3C2...; DLL 962D88D6...; nohunk5-diagd 797E6142; both needles.
- devoff4b-ctr-bin (02:46) MANIFEST A5367CB5...; DLL FACCF87F...; predecessor objs E049CA08/904BFA74, relink only; CTL PASS; needle deferred_counters:.
- devoff4b-r19-bin (02:47, run 2) MANIFEST 1EBF1163...; DLL 5DCDD8CB...; run 1 (02:46) not staged: driver wrongly required d3d12_submit_split_kb absent from devoff4b (pre-existing cvar) -> added --have. M10 C1-C5 PASS (C2-C4 in s33/r19/r19-checks.txt via session3/r19-checks.py); C2 SHOULD -MD/-MF not done.
- Fix found during build: CTL DIFF in __FILE__ strings (ccdb backslash source vs ninja's forward slash) -> recompile.py --fwd-src; overlay paths -> -fmacro-prefix-map. No overlay path in any staged DLL.

## 07:00 FINAL defaults change set (diff only, no build) - M2
- build/agent2/final/: FINAL-DEFAULTS.diff 955543F5 (11 files; verify-diff.py PASS: apply/after-hashes/-R/live --check, q500 section == 28F0D1DE), DEFAULTS-TABLE.md 14B41251, check-defaults.py 6C7A00EB (synthetic 11/11 + win3 legacy PASS), BUILD-PLAN.md B87ABA79, verify-diff.py 9AAF4BB7, predict-fingerprint.py 1792CDCB.
- 12 SDK defaults -> win3 (9 TUs: 8 rexruntime, 1 rexgpu-xenos); q500 verbatim; miss cache default ON (native, fingerprint 9b40acbb -> 1616ce65 predicted); new proof lines "Final defaults:" (runtime.cpp) and "Final defaults (GPU):" (shared_memory.cpp). Scratch: final/work/.


## 07:20 FINAL build prep after M10 SAFE-IF (C20B6FDB). No compiles; read/write + light self-tests only

- S1: check-defaults.py (D9936C56) requires the full back-off line incl. "; stats OFF; GetData hook built."; N3 native-old forbids
  `Final defaults (GPU):`. work/test-check.py (A5B084C2) SYNTH PASS 16/16; legacy win3 PASS / s0 FAIL. N4: verify-diff.py
  (5B440AFB, RESULT PASS) and predict-fingerprint.py (1772B70D, 9b40 == pinned, predicts 1616ce65e973c583) derive WS from __file__.
- D2 extension = final/prep-final.py (83F732CA) + final/build-final.py (740E5945) + final/pe-check.py (F4368C32); recompile.py
  855BCC79 and relink.py F3C6EEAF unchanged. Replacement objects keep their basenames (lld /MAP names objects by basename, so
  the exe CTL --compare-map can pass). D4: final/fsyntax.py (E9E4E131), 19 commands. D3: final/pe-diff.py (FF5C661C),
  self-tested on s33/devoff4bv/link-ctl (COFF TimeDateStamp only -> PASS).
- BUILD-STEPS.md (EE079AFE) has every command + STOP gate (D1/D3/D5/D6), D7 rules, F1-F7. BUILD-PLAN.md (B0A3B9F6) updated.
- Not run yet (needs ninja/hashing/compilers): prep-final, fsyntax, build-final dry runs. Wait for the Overseer's go.

## 07:26-07:32 FINAL build (GO 07:26, final-build-rating DF596C16 SAFE-IF)
- step0 prep PASS; step1 fsyntax 19/19 PASS (counts 8/1/1/1/4/4 gated).
- rt PASS: CTL == devoff4b rexruntime except TDS; ON C5BC627B; pe-check PASS (10467 exports).
- gpu PASS: CTL == E3CB99CF except TDS; ON CB3A2CC9; +2 imports GetFlagByName/GetFlagSource only.
- xe PASS: CTL exe+map == devoff4b; ON 545D28B9; mapcheck s4c 31.
- nat PASS: CTL exe+map == native4b; ON 5C21941D; 1616ce65 + miss-cache needle; mapcheck same 109.
- xeoff PASS DB263913; natoff PASS 4ADF630E (both differ from ON).
- Stage dry runs x4 PASS. Real staging held: build-final.py 740E5945->5BE1F221 and fsyntax.py
  E9E4E131->66C7D740 were edited after rating; diffs in final/work/*-rated-to-current.diff (F5B111B2, 84AFD255),
  rebuilt-rated hashes MATCH (work/rated-diff.py). Awaiting M10 via Overseer.
- 07:32 STAGED after M10 CONFORM (94CC9FA7): devfinal F9C2BE72, devfinal-off 3F4B7BEB, nativefinal D7C7B706,
  nativefinal-off 0C67CBD6. D6 3-bin re-verify 0 FAIL after each stage. Pins: final/BIN-PINS.md FE4CD4FF.
  Reported to the Overseer 07:33; ready for M8's smoke run + F1-F7. M2 idle.

## 15:54 COMMIT-PLAN.md written (session3/commit-plan/): ง1-ง4 + ง5 part B (final2 plan, commands, ETA ~30 min after push). Flag: commit nohunk5 57CFA8AD, not no5. Waiting for 'pushed <sha>'.

## 16:13 final2 (part B) staged
- Tools: prep-final2 4B20F22A, fsyntax2 3FC03399, build-final2 80C11DCC. Rated CONFORMS by M10 (final2-tools-rating.md 366294FD); NIT hard devfinal2 copy check applied.
- Source: rexglue-sdk a7e79c0 / DimensionsRecomp 2de88ce. The overlay is the committed blobs in snap1's EOL form; shaders.cpp is the CRLF form 4B8250E9.
- Gates: prep PASS, fsyntax 23/23, CTL rt/gpu/xe/nat PASS, needles/pe-check/mapcheck PASS.
- Bins: devfinal2-bin MANIFEST 4A4A13ED, nativefinal2-bin MANIFEST 4E5E2620. verify-bins shows 0 FAIL on these plus the 3 shared bins.
- Pins are in final2/BIN-PINS.md (33F74799). M8 runs the smoke.
