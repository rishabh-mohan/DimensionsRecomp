# Agent 4 handoff

Written 2026-11-23, before the break. Agent 4 worked on the native renderer's CPU cost per draw, the placement-shader items #1 (AOT pack) and #2 (miss cache), the native4b re-pin paperwork and the screenshot check kit. Nothing of mine is running, half-applied or waiting in a queue. Only Agent 1 commits or pushes; I have committed nothing.

## 1. What I own

- `build/agent4/**`: specs, checkers, records and scratch trees (key files in section 4).
- `bench/agent4/**`: `check_n_rows.py` (the n2/n3 batch-line check the re-pin matrix uses), `matrix-native-threaded.json` (the parked threaded-modes matrix), the CPU benches and their fixtures.
- `perf-notes/agent4-draw-path.md`, my notes. The top blocks are the session log. S3.5 is the full #1/#2 record, S2.11 the draw.cpp batch procedure, S2.12 the parked T1-T13 plan, S3.4 the trimmed timing matrix, and S2.13 the native first-boot crash and its `native_settings_frontend=false` workaround.
- Code: the live `DimensionsRecomp/rexlego/src/gpu_native/draw.cpp` is my batch 3. The live `gpu_native/shaders.cpp` carries my #2 patch (applied in S4a), but shaders.cpp itself is not an Agent 4 file.

## 2. State

| Item | State | Where |
|---|---|---|
| #1 AOT pack: the 4 native placement shaders that are missing (VS 0xAC449538 / PS 0xAC448F28 and a second pair) | Scratch pack PASS (s35 run-071627, 2026-11-22 07:16): the production lookup resolves all 4 containers. No pack bin is built. S4-DRAFT row 1: proposed; it waits for the user's visual check. | `build/agent4/s35/`, `build/agent4/s34/aot-pack-proposal.md`, notes S3.5 |
| #2 miss-cache stopgap `LEGO_NATIVE_SHADER_MISS_CACHE` | In the snap1 tree since S4a (checked in native4-bin; native4b-bin is built from the same tree). OFF by default, rated SAFE (S4-DRAFT row 2). The ON smoke passed (2026-11-22). Moot if #1 lands. | `build/agent4/r2t6/miss-cache-on-smoke-spec.md`, `build/agent4/s34/` |
| Re-pin native4 -> native4b (S4b + S4c, fingerprint `9b40acbbef4c57b3`) | Step 1b dry run PASS (2026-11-22 20:55). Pin record PASS (22:43, 0 FAIL, 0 WARN). Agent 3, 2026-11-23: boot check rpb0 PASS; matrix rpm4 PASS on every section 3(b) check. Agent 1 announces the pin. | `build/agent4/repin/` |
| Screenshot check kit (the "before" half of #1) | Ready since the morning of 2026-11-23, after a review and tests: `collect-shots.ps1` passed 19 scratch tests (fake runs, and the real run.json and input.csv of two attract-long runs). Not run when this was written. | `build/agent4/screenshot-kit/README.md` |
| Threaded-modes matrix and the T1-T13 plan | Parked until a timing window (S4-DRAFT row 3, window W8b). | `bench/agent4/matrix-native-threaded.json`, notes S2.12 and S3.4 |

## 3. Open items

1. **Dump the attract's shaders before building any pack bin.** In the 3D attract, native drops about 43 of 59 draws per frame (later 45-155). Those draws use 46 more vertex-shader objects and 3 pixel-shader objects, first bound ~117.7 s into the traced run. They account for 115,571 dropped-draw rows, against 46,549 for the two title-screen VS. The evidence is in `build/agent4/screenshot-kit/native4-drops-r6off.txt`. The only shader dump so far (`build/agent8/matrix/20261122-0509/runs/0509-sd-r1`) had no input and never reached the attract, so the 4-shader pack may not cover these draws.
   - Do one native run with `LEGO_DUMP_MISSING_SHADERS=1` on `harness/routes/attract-long.txt`. Add `LEGO_NATIVE_TRACE_DIR` for the timeline; `-Env` values need absolute paths.
   - Agent 7 checks any new containers, then `build/agent4/s35/run_pack.ps1` takes them as extra inputs.
2. **Then the pack.** Build it on the current native line (native4b once it is pinned): Agent 2 builds native4bp as in `build/agent4/repin/REPIN.md` section 4.2. The agents run `build/agent4/r2t6/VISUAL-CHECK.md` sections 2-3 first. Read its correction note: without input the game never reaches the 3D attract, so add the attract-long route. Then the user looks: run kit command B with the pack bin and compare it with the kit's reference shots and MISSING list. After the user's yes, do REPIN section 4.2 steps 3-4 (`repin_check.ps1 -Line snap1 -Pack`, then `matrix-repin-packhit.json`).
   - Keep the kit's `build/agent4/screenshot-kit/shots/` (both runs' "before" shots, local only). For the pack run, rename it to `shots-before/` (collect-shots won't write into a folder that holds PNGs) and keep the tag `sc-native`: collect-shots only pairs the newest `sc-ref` and `sc-native` runs. If the original reference PNGs were deleted, it reports the reference run as INCOMPLETE; compare the new native shots with `shots-before/` by hand.
3. **Fix `build/agent4/repin/repin_check.ps1` before the next re-pin.** I left it unchanged on purpose, although REPIN.md L53 says to add native4b to `$PINS` after the pin.
   - `$PINS` (L130) holds the pins older than native4b. [4] (L373) and [5] (L412) FAIL when a built or staged fingerprint is in `$PINS` while C1 and S4c are in the tree. So don't just add `9b40acbbef4c57b3`: every check of `build/agent2/snap1-on` and `native4b-bin` would then FAIL, including REPIN section 4.2 step 1.
   - The pack changes fingerprint inputs: the merged `out/native-gpu/lego-microcode-index.cpp`, the runtime cache file and the regenerated `runtime-linked-dxil-cache.cpp`. So native4bp gets a new fingerprint.
   - The fix, in this order: key [4]'s old-pin FAIL on the pack state (`$cacheState` 'pack', L291), so that only "pack applied but still an old fingerprint" FAILs. Add `build/agent2/native4b-bin` to `$oldBins` (L390), so [5] reports it as a frozen old-pin bin. Then add `'9b40acbbef4c57b3' = 'native4b (S4b + S4c)'` to `$PINS`.
4. **native4b's fingerprint changed** (`5e3ff55de10f4f64` -> `9b40acbbef4c57b3`). Its first start rejects native4's `native-pso-recipes.bin` and `native-pso-seed.bin`, so it builds PSOs cold until it has recorded its own. Seeds and recipes for native4b must be recorded by native4b. The pack bin changes the fingerprint again.
5. **The kit.** If it was run, the result is in the table in `build/agent4/screenshot-kit/README.md` or in Agent 1's notes. If not, it is ready for the next free hour and needs no build, as long as `build/agent2/devoff4-bin` and `build/agent2/native4-bin` still exist. The pop-in look (#33) needs its option built first.
6. **Timing numbers are machine-specific.** The numbers in my notes come from this machine with its current drivers and OS. After a hardware, driver or OS change, re-run the reference arms before comparing.
7. **Scratch.** These folders hold scratch from finished work and can be deleted (Agent 1's call): `build/agent4/s32tree` (75 MB, 2,286 files), `s32ctrl`, `obj`, `s34/obj`, `fixtures-*` and `state_shadow*`. Keep `repin/`, `r2t6/`, `s34/` (proposal and patch), `s35/` (pack tools and the run-071627 output) and `screenshot-kit/`.

## 4. Key files

sha256, first 16 hex digits, as of this handoff.

| File | sha256 | What |
|---|---|---|
| `build/agent4/screenshot-kit/README.md` | 6177F640617B8006 | the kit, one page |
| `build/agent4/screenshot-kit/collect-shots.ps1` | 071258EFA60E8B3E | copies the shots, checks both runs and the pad, writes `compare.html` |
| `build/agent4/screenshot-kit/native4-drops-r6off.txt` | 5BB27977B7D4D01B | native4's dropped draws over time, from the r6off-t trace |
| `build/agent4/screenshot-kit/missing_timeline.py` | 23EB6EB023735B80 | builds that file from a trace's `events.tsv` |
| `build/agent4/r2t6/VISUAL-CHECK.md` | 548326DD5E54FEBD | the pack's visual-check plan; read the correction note first |
| `build/agent4/repin/REPIN.md` | 4552644B213FD332 | the re-pin procedure; section 4.2 is the pack re-pin |
| `build/agent4/repin/repin_check.ps1` | 81BE81D8BA3FFE02 | re-pin checker, read-only unless `-Go` (only on Agent 1's word) |
| `build/agent4/repin/matrix-repin-native4b.json` | 2580067D38AEC968 | the 4-run re-pin matrix (rpm4) |
| `build/agent4/repin/matrix-repin-native4b-boot.json` | 37DFC58F77CADA7D | the frontend-on boot runs (rpb0) |
| `build/agent4/repin/matrix-repin-packhit.json` | 490964ACF9E8D9B2 | the pack-hit matrix, t0 vs t0p |
| `build/agent4/repin/dryrun-native4b-1b-2055.txt` | 2EB43DEF9F3AFD49 | the step 1b dry run (expected fingerprint) |
| `build/agent4/repin/pin-native4b-2243.txt` | 87DC898A67D7684A | the pin record |
| `build/agent4/r2t6/miss-cache-on-smoke-spec.md` | 3066D227050E7AED | #2's ON smoke: commands and pass rules |
| `build/agent4/r2t6/mc_smoke_check.py` | EB13FA9605E1CF48 | its checker; `mc_smoke_selftest.py` (42943833ED9D8F06) passes 15/15 |
| `build/agent4/r2t6/native4-check.txt` | 159F1CA15C4B70B6 | native4-bin contains the #2 patch |
| `build/agent4/s34/aot-pack-proposal.md` | B89DFA7311F002A2 | the #1 proposal |
| `build/agent4/s34/miss-cache-review.md` | 7AA19D11F71D4C2D | the #2 review |
| `build/agent4/s34/shaders-s34.patch` | 328BDAE19ABFC6C8 | the #2 patch (in the tree since S4a) |
| `build/agent4/s35/README.md` | 5D372A664A9EECC9 | the scratch pack: procedure and pass criteria |
| `build/agent4/s35/run_pack.ps1` | D29E23BEBD05C91A | builds the pack in scratch |
| `build/agent4/s35/run-071627/SHA256SUMS.txt` | B27DAA5FA52A3267 | the PASS run's outputs: `runtime-cache.cpp` AEA36683202B9753, `lego-microcode-index.cpp` E4C05782462452C3, `index-addition.cpp` 154242FB07BEDC92 |
| `bench/agent4/check_n_rows.py` | 7AFBD5E0B30A2F45 | the n2/n3 row check |
| `bench/agent4/matrix-native-threaded.json` | 76FE0BAAD3BF36BC | the parked threaded-modes matrix |
| `perf-notes/agent4-draw-path.md` | C0F64079C5110DB6 | my notes (1,263 lines) |
| `DimensionsRecomp/rexlego/src/gpu_native/draw.cpp` | 5EA1F3576DCC2F90 | live, batch 3 |
| `DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp` | 9567FE3F3B63637D | live, with the #2 patch (not my file) |
