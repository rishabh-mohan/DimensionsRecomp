# PENDING-DIFFS: candidate changes that are not in the committed trees

Written by Agent 2 on 2026-11-23 at 06:35, for board task #28 part (2). Every path is relative to the workspace root. Nothing was built, applied or committed. Every check was read-only: `git --no-optional-locks`, `git apply --check`, `Get-FileHash` and byte compares.

**Update 2026-11-23 10:15 (board task #34, docs only):** #19 now has its rate request, `build/agent7/s4-r1s2/RATE-REQUEST.md` (Agent 7: first written 08:12, rev 1 08:40, task #33 corrections 09:04-09:59), but it is still not rated: Agent 10 rates it after the break. The diff is unchanged and `SHA256SUMS.txt` still matches 12/12. Also added: in snap1, which has no `.git`, the `git -C <sdk root> apply` form in `CHECKS.txt` L22-23 skips all 5 files. Changed: the §1 and §2a #19 rows, §5 item 4 and the §6 sources table; nothing else.

**Update 2026-11-23 07:49 (board task #31, after Agent 10's N4 in `build/agent10/t27/r33-popin.md` L137-141):** #21 is rated; #33 and #34 are staged together and rated, and #33's stale placeholder cvar name is replaced by the real one; codegen B's formal read-out says drop; #19 is still not rated. Changed: §1 rows CG26 arm B, codegen B, B4, #21, #19, #33 and #34; §2a rows codegen B, #21, #19, #33 and #34; §5 items 1, 3, 4 and 5; §6 (a table of the new sources). Each new fact cites its source path. All other lines are as of 06:35, and the annex predates this update.

## 0. Baseline and method

- **Baseline ("HEAD" below):** `DimensionsRecomp` b0bd3b4 with `rexglue-sdk` 5350b1d, on `perf/opt`.
  - For every tracked file in scope, the working tree equals HEAD and `build/agent2/snap1` (`build/agent2/COMMIT-CHECK.md`, PASS).
  - Re-checked at 06:29-06:33: both HEADs are unchanged. `git status --untracked-files=no` lists only the submodule entries: `rexglue-sdk` and `thirdparty/plume` in the game repo, and `thirdparty/simde` in the SDK.
    - Porcelain v2 flags them `S.M.`, `SCM.` and `S.M.`. All three have modified content.
    - plume also shows a different commit: the checkout is e0c8871 and the gitlink is ceaeeee (§3).
    - Inside the submodules, only the 3 plume files and the 1 simde file of §3 are modified.
- **sha256:** full `Get-FileHash` values.
  - The game repo has `core.autocrlf=true`, so its text files are hashed in their CRLF working-tree form.
  - SDK files are byte-identical to their blobs.
- **"Applies to HEAD?":** `git --no-optional-locks -C <repo> apply --check [-R] <diff>`, run against the working tree. My helper ran these at 06:01 and I re-ran 4 of them at 06:22.
  - "yes" means the forward check exits 0 and `-R` exits 1: the change applies and is not in HEAD yet.
  - For an after-file, "yes" means its staged before-file has HEAD's sha256.
- **Run apply checks with `-C <repo>`.** The workspace root sits inside an enclosing git work tree. Run from there, `git apply --check` prints `Skipped patch` and exits 0 without checking anything.
- **Item numbers** #19/#21/#26/#33/#34 are rows of `perf-notes/S4-DRAFT.md` §1, not board task numbers.
- **Annex:** `build/agent2/pending/PENDING-DIFFS-draft.md` (sha256 in §6), written by my read-only helper and spot-checked by me: 7 hashes and 4 apply checks agree. It has:
  - the supporting inputs (kits, tools and reports, each with its sha256);
  - per-item notes that cite their sources by line number;
  - 16 "not found or unclear" points.

  Where the annex and this file differ, this file wins.

## 1. Summary

| item | what it would change | tree diff | applies to HEAD? | status (11-23 06:30; task #31 rows updated 07:49) | owner |
|---|---|---|---|---|---|
| **CG26 arm A** (#26 `db16cyc_pause` ON) | One line, `db16cyc_pause = true`, in `DimensionsRecomp/rexlego/legodimensions_config.toml`. A regen then puts 20 `simde_mm_pause();` into 10 generated TUs (`generated/` is untracked). | yes | **yes** | Staged 11-22 14:14. Agent 10 rated it (~14:45, b2r row 37): SAFE to test after 4 gates. **Not built** (CG26 bin recipe: HANDOFF §4.1). | Agent 9 (toml); Agent 2 (CG26 build) |
| CG26 arm B | The same line, in codegen B's toml. | yes | no (its base is batch-nolr) | Staged and rated with arm A. It belongs to the B line only. Codegen B's formal read-out says drop B (codegen B row), so arm B goes with it; the retire action is left for after the break. | Agent 9 |
| **CTR** | Nothing in the trees. One SDK TU (`deferred_command_list.cpp`) is compiled with `-DREX_D3D12_DEFERRED_COUNTERS=1`, then `rexgpu-xenos.dll` is relinked. | none (by design) | n/a | The code is in HEAD (#20 step 1, rated SAFE). The variant is prepared and dry-run. **Not built** (recipe: HANDOFF §4.1). | Agent 7 (code); Agent 2 (variant) |
| **codegen B** | 16 added lines in the codegen toml (9 root keys, comments and a blank line), then a regen. | none: a whole-file toml | yes, as a whole-file replacement (HEAD's toml is a strict subset of it) | Rated SAFE except skip_lr, which is not set. **Formal read-out: drop B, no gain** (`build/agent8/readout/w-followup/W4c.md` L7 and L16: paired median frame time +2.6 % [−1.2, +6.5], B lower in 1 of 6 rounds; fps −1.7 % [−4.9, +1.7]; "Don't adopt B for performance"). Agent 7's T-std read-out agrees: +2.7 % [−0.8, +6.3] (same file, L7). This settles the old lean (S4-DRAFT L13-14). The retire/keep action is left for after the break. | Agent 9 |
| **B4** | Nothing in the trees: a build plan (codegen B + S4a). | none | n/a | Deferred since 11-22 16:17. **Stale:** it pins the S4a SDK install, which S4b replaced. It is built on codegen B, which the W4c read-out says to drop; no note formally drops B4 yet (after the break). | Agent 2 |
| **#21** S4-T1 rev 2 | Env `LEGO_NATIVE_CHAIN_PRIORITY=1` raises the thread priority of the native worker chain (unset = OFF). rexlego, 3 files, +51/-0. | yes | **yes** (`--directory=rexlego`) | Staged 11-22 22:48. RATE-REQUEST.md sent 23:25. **Rated** by Agent 10 (`build/agent10/t27/r21-s4t1.md`, 06:32): (a) the default-off test bed is SAFE; (b) value 3 in F1, F3, W1 and W8b is SAFE-IF these 5 conditions hold: Agent 11's `host_execution_throttling_optout` stays at its default (false); F1 first, and W8b only after F1 and W1 pass; idle host; never copy `cache/` or a seed between bin dirs, and read F1 (b) on r2; a th2 hang is checked first against F-CA, a th2-only deadlock that exists without #21; (c) ACCEPTED, with a §9.2 wording fix and a SHOULD for Agent 7 (record F-CA under MP4 gap 2). **Not built.** All 3 files are native fingerprint inputs, so native4b-bin baselines must be re-pinned before any timing comparison (r21-s4t1.md L45). | Agent 7 |
| **#19** R1 stage 2 | Cvar `d3d12_async_submit` (OFF, kInitOnly) moves the submit to a worker. SDK, 5 files, +320/-1. | yes | **yes** | Staged 11-22 23:10, PROOFS ALL PASS. **Rate request written:** `build/agent7/s4-r1s2/RATE-REQUEST.md` (Agent 7, task #32: first 08:12, rev 1 08:40; task #33 corrections 09:04-09:59). It asks Agent 10, after the break: (a) is it SAFE to build into devoff4b as a default-off test bed; (b) is it SAFE to test ON (`d3d12_submit_split_kb=<N>` plus `d3d12_async_submit=true`) in the rows, the soak and W7; (c) are the threading and ownership rules and the code-read items accepted. **Not rated:** no rating is requested before the break. Not built, and no syntax check yet. The diff is unchanged and SHA256SUMS.txt matches 12/12 (re-checked 11-23 10:15). **Apply trap:** snap1's SDK has no `.git`, so the `git -C <sdk root> apply` form in `build/agent7/s4-r1s2/CHECKS.txt` L22-23 prints "Skipped patch" for all 5 files and exits 0 without applying anything (CHECKS.txt L24 now warns). Copy `build/agent7/s4-r1s2/new/sdk/` instead, or use the `--directory` form in RATE-REQUEST.md §2, and confirm 5 "Checking patch" lines. | Agent 7 |
| **#33** (with #34) | "Don't wait for pipelines": opt-in cvar `d3d12_pipeline_creation_no_wait` (default false, `kRequiresRestart`). When ON, the end of a submission no longer waits for pipelines that are still being created; their draws stay skipped until the pipeline is ready (pop-in instead of a stall). Memexport and occlusion-query draws still wait. It takes effect only with async shader compilation, creation threads and bindless. SDK, 4 files, 10 hunks, +105/-24; #34 is folded in. | yes | **yes** (`-C DimensionsRecomp/rexglue-sdk`) | Staged 11-23 06:28 by Agent 6 in `build/agent6/s33-popin/` (design: `perf-notes/agent6-attract-stalls.md`, then `build/agent6/s33-popin/DESIGN.md`). The user had approved it as an opt-in that is OFF by default. **Rated** by Agent 10 (`build/agent10/t27/r33-popin.md`, 07:34): OFF SAFE; ON as an opt-in test SAFE-IF 4 conditions: the default stays false with `kRequiresRestart`; row 1 (cvar off, patched bin against base bin) shows identity before anyone reads ON timings; the user's row-3 review on a visible desktop gates any recommendation; the first test bin leaves out hunk #5 (S1). No BLOCKER. S2: run the resolve-after-drop diagnostic (d) before any recommendation. **Not built.** | Agent 6 |
| **#34** | Counters for #33: `kDroppedDraw` and `kPipelineAwait` in `frame_stats.h`, a dropped-draw count in `IssueDraw`, and 3 more fields at the end of the slow-frame line (r33-popin.md L26-28). | yes, inside #33's patch (hunks #3, #4 and #10; r33-popin.md L139) | **yes**, with #33 | Staged and rated with #33; no separate diff. | Agent 6 |
| plume / simde edits | 3 files in `DimensionsRecomp/thirdparty/plume`; 1 in `DimensionsRecomp/rexglue-sdk/thirdparty/simde`. | patches saved | already in the live submodules | **Not candidates.** Uncommitted by design and rebuilt from tracked scripts and patches. Checks PASS (§3). | Agent 1 (policy) |

## 2. Files

### 2a. Diffs and configs

| item | path | sha256 | base | applies to HEAD? | status | owner |
|---|---|---|---|---|---|---|
| CG26 arm A | `build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-A.diff` | `95D901B9784705FA656145487B5611BA95A606E4DBD28FA7BE60C9E93B8F2620` | HEAD's `rexlego/legodimensions_config.toml` (`7F775847DB9CC2DA89DC3EDE57A0AD5F30FDF58D98F5021A0E27A4E0E4DA95BF`, 18145 B) | **yes**: `-C DimensionsRecomp` exit 0, `-R` exit 1 | staged, rated, not built | Agent 9 |
| CG26 arm A, after-file | `build/agent9/s4/spin/db16cyc-pause/toml/new-A/rexlego/legodimensions_config.toml` | `11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF` | before = `build/agent9/s4/spin/db16cyc-pause/toml/base-A/rexlego/legodimensions_config.toml` (`7F775847…`, = HEAD) | **yes** (copy it over the toml) | as above; 18167 B | Agent 9 |
| CG26 arm A, build copy | `build/agent2/cg26/DimensionsRecomp/rexlego/legodimensions_config.toml` | `11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF` | = new-A | n/a: the regen input in my CG26 prep tree, not meant for the live tree | the regen has not run | Agent 2 |
| CG26 regen tool | `build/agent2/cg26/tool/rexglue.exe` | `9145166CDBEF5500E6E2607ED80AA6FC94CA1772DE2D3E87FF9E13BEAD87D586` | the S4b SDK build | n/a | ready | Agent 2 |
| CG26 arm B | `build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-B.diff` | `5D5892D33D09AF9D6889AF5BC991C82CD4443A8F7493053584BF6889261585B3` | codegen B's toml (`E60EAF1C…`) | **no**: exit 1 | staged, rated; B line only | Agent 9 |
| CG26 arm B, after-file | `build/agent9/s4/spin/db16cyc-pause/toml/new-B/rexlego/legodimensions_config.toml` | `FFC119BFE2639E30E8CEC4E5258F1428DB06C62E0E880003DCF9EF1113B7B570` | before = base-B (`E60EAF1C…`) | no | as arm B | Agent 9 |
| CG26 tool option (**not pending**) | `build/agent9/s4/spin/db16cyc-pause/db16cyc-pause.diff` | `AC554DBBD965BF941BADE6391D0E0F483BE075B8A72434EEE8CB9D189ED61452` | SDK HEAD^ | **already in HEAD**: forward exit 1, `-R` exit 0 | committed in SDK 5350b1d (the option defaults to OFF) | Agent 9 |
| CTR | no diff | n/a | SDK HEAD `src/graphics/d3d12/deferred_command_list.cpp` L21-27 (`#ifndef REX_D3D12_DEFERRED_COUNTERS` → 0). Neither repo has a CMake option for it. | n/a | prepared, not built (inputs: §2c) | Agent 7 / Agent 2 |
| codegen B | `build/agent9/configs/batch-nolr.toml` | `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` | HEAD's toml + 16 lines at L24-39, with none removed (815 → 831 lines) | yes, as a whole-file copy; no git diff exists | rated SAFE except skip_lr (not set); formal read-out: drop, no gain (`build/agent8/readout/w-followup/W4c.md`); retire or keep after the break | Agent 9 |
| codegen B, install copy | `build/agent9/install/batch-nolr/legodimensions_config.toml` | `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` | = batch-nolr | as above | The toml of the codegen tree behind devoffB-bin and nativeB-bin. That tree's outputs are pinned by `build/agent9/install/batch-nolr/SHA256SUMS.txt` (`24CE1493FB8DAE37E00B556EB8871D633921E44378D960DE4359B104B16CDB8E`). | Agent 9 |
| codegen B, superseded | `build/agent9/configs/batch.toml` | `B272725044741AE84942B22A0F51ECC13FD16E90BE3A5C3E7E6A4F74B5DAF950` | not diffed | not checked | superseded: it sets skip_lr, and is kept for diffs only | Agent 9 |
| codegen B, rollback 1 | `build/agent9/configs/rb1-nolocal.toml` | `AE9F8F967FBB264919A63463CA4958F856C18A0405A4895440D6C36A31084EEC` | batch-nolr without the 4 `*_as_local` keys and `cr_compare_so_zero` | not checked | unused rollback | Agent 9 |
| codegen B, rollback 2 | `build/agent9/configs/rb2-nomusttail.toml` | `FC034D495DAC395F45CDC0AC0DC7BFD88C8D2046A09590B88563B63BE1C82924` | batch-nolr without `musttail_calls` | not checked | unused rollback | Agent 9 |
| B4 | no diff | n/a | The plan: snapB (S2) + 35 copies from snap1 → devoffB4; snapB3 (S3d) + 6 S4a copies → nativeB4. Both link `build/agent2/snap1-sdk/install` at S4a. | n/a | deferred, stale (scripts: §2c) | Agent 2 |
| #21 | `build/agent7/s4-t1/s4-t1.diff` | `46FFD2E9044094DCE17C364C382F7BF2563E071E0DF81750C1DE1BC38BE38050` | snap1 rexlego, = HEAD (the before-files match HEAD, §2b) | **yes**: `-C DimensionsRecomp --directory=rexlego` exit 0, `-R` exit 1 | staged (rev 2); rated: (a) SAFE, (b) SAFE-IF 5 conditions, (c) ACCEPTED (`build/agent10/t27/r21-s4t1.md`); not built | Agent 7 |
| #19 | `build/agent7/s4-r1s2/s4-r1s2.diff` | `06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7` | the S4b SDK, = HEAD (the orig files match HEAD, §2b) | **yes**: `-C DimensionsRecomp/rexglue-sdk` exit 0, `-R` exit 1 (the live SDK repo; in snap1, which has no `.git`, use the forms in RATE-REQUEST.md §2, see §1) | staged; rate request `build/agent7/s4-r1s2/RATE-REQUEST.md` (09:59); not rated, Agent 10 rates it after the break; diff unchanged, SHA256SUMS.txt 12/12 (re-checked 10:15) | Agent 7 |
| #33 (with #34) | `build/agent6/s33-popin/s33-popin.patch` (LF, 220 lines, 11003 B) | `0D23024484CCDEE1B15AF3EB79DC28759F9D422E78536F4766C83C2071CC2EFD` | SDK HEAD 5350b1d; 4 files: `include/rex/graphics/d3d12/pipeline_cache.h`, `src/graphics/d3d12/command_processor.cpp`, `src/graphics/d3d12/pipeline_cache.cpp`, `src/graphics/frame_stats.h` | **yes**: `-C DimensionsRecomp/rexglue-sdk` exit 0, `-R` exit 1 (Agent 2, 11-23 07:39) | staged 06:28; rated (`build/agent10/t27/r33-popin.md`); not built. S1: build the first test bin without hunk #5 (patch L82-93, the `CanEndSubmissionImmediately()` change); `build/agent6/s33-popin/CHECK.txt` says which lines to delete. A copy without hunk #5 passed `apply --check` at 07:37 and was withdrawn at 07:40 to keep this round docs-only; the rated patch is unchanged (CHECK.txt). Agent 6 recorded the rating, docs only, in DESIGN.md §10 and CHECK.txt; Agent 10 checked them at 07:44 (r33-popin.md L162). | Agent 6 |
| #34 | inside `s33-popin.patch` (hunks #3, #4 and #10) | as #33 | as #33 | as #33 | staged and rated with #33 | Agent 6 |

### 2b. After-files of #21 and new files of #19

| item | staged file | sha256 | before (= HEAD working tree) | target |
|---|---|---|---|---|
| #21 | `build/agent7/s4-t1/after/src/gpu_native/native_worker.cpp` | `071E2F4B784D40DEF4A58870F438EFDB194B96E2D2FCF0A8349E8DDD7141BFDA` | `7157E8F2EDC3D5C438E3F2F21B50051693A3046B36A4BD8EE096901DF8FE0E2F` | `DimensionsRecomp/rexlego/src/gpu_native/native_worker.cpp` |
| #21 | `build/agent7/s4-t1/after/src/gpu_native/native_recording.cpp` | `00F03D84A0C594FA6DC4850CE36AB77847453A913AA077286F6D0D11B900EC6C` | `48F0C429DDB89E452794365788C8B34EA9510A4B10B86F93771F418F3E53AA9B` | `DimensionsRecomp/rexlego/src/gpu_native/native_recording.cpp` |
| #21 | `build/agent7/s4-t1/after/src/gpu_native/native_preparation.h` | `88C57831AF2B200A36E966C000F4D783004D26EB984A54BDEEADE245709CCFE0` | `889F3FA6F207011B03D044E745C2952C68200A44C99BE6E13EB810357D3D41A5` | `DimensionsRecomp/rexlego/src/gpu_native/native_preparation.h` |
| #19 | `build/agent7/s4-r1s2/new/sdk/include/rex/graphics/d3d12/command_processor.h` | `EF0DC13DA29703C7FEDC13FE7C8542E592FB82460817F1B88C4930D92F12CD4C` | `67F4E8380C879377F06B6E3DD879EE737A82BBBE9682F123247ED5D0671FF325` | `DimensionsRecomp/rexglue-sdk/include/rex/graphics/d3d12/command_processor.h` |
| #19 | `build/agent7/s4-r1s2/new/sdk/include/rex/graphics/d3d12/deferred_command_list.h` | `E7512824D8E6F9673C59457CD28FA34DD7795E4D495B3BAB76D07774AEA60650` | `9F6CC70A6922232D4FF7A32303E8B785A01D1C7A3CF54373369EF6B23F8AF0F0` | `DimensionsRecomp/rexglue-sdk/include/rex/graphics/d3d12/deferred_command_list.h` |
| #19 | `build/agent7/s4-r1s2/new/sdk/src/graphics/d3d12/command_processor.cpp` | `05BBCE8B7E3FB27D43F364031082F73DFCD5BD223307DB794FB3C6DD6E91807C` | `027204B53A271D69275FCC6FEC6B2222905155E1FD67808F88A79329F4022C0E` | `DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/command_processor.cpp` |
| #19 | `build/agent7/s4-r1s2/new/sdk/src/graphics/d3d12/shared_memory.cpp` | `9E908D31E6F64A31A55126CB0E97B37F1DD1A677B7026872A839FAE53A8FEB8A` | `2A5ADF13B5E433F1F10B5C6AF9C14F8812527C4E155A5146B166723457B6EBB4` | `DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/shared_memory.cpp` |
| #19 | `build/agent7/s4-r1s2/new/sdk/src/graphics/d3d12/texture_cache.cpp` | `4183887C9D625B97D8DDB7B5D2BF5F28D2B9B122DBF3488BDA1753100CB9BAB4` | `949CCF4F4D80975D4DF3E833604BDBEC8C1442D787E2492085F0FA966E7F8C99` | `DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/texture_cache.cpp` |

Supporting files:

- **#21:** `build/agent7/s4-t1/RATE-REQUEST.md` (`AFE56587D955BD7AE1CD38D579BF371ABC3231E214C1C2DB640224CF35137BB1`) and `build/agent7/s4-t1/SHA256SUMS.txt` (all 7 listed files match).
- **#19:** `build/agent7/s4-r1s2/PROOFS.txt` (P1-P10 ALL PASS) and `build/agent7/s4-r1s2/SHA256SUMS.txt` (matches).
- More in annex §1b.

### 2c. Prepared inputs of the build-only items (my files)

| item | path | sha256 | note |
|---|---|---|---|
| CTR | `build/agent2/ctr/list-ctl.tsv` | `6A357FEFBB0CE06A4BE09229FB9B32F6F0ED6576BF73ABD5753C441EFC8AD494` | Control TU list. It holds absolute paths on this machine, so regenerate it if the workspace moves. |
| CTR | `build/agent2/ctr/list-on.tsv` | `A63A77CD86AB7DA09C75468EE1DBF6857DE3E5D4F12B97AED2E9412CE6256305` | ON TU list. Same caveat. |
| CTR | `build/agent2/ctr/log-ctl/`, `build/agent2/ctr/log-on/`, `build/agent2/ctr/link-dry/` | annex §1b | Recompile and relink dry runs, 11-22 20:31. |
| B4 | `build/agent2/run-b4.ps1` | `56A04A77810AA6A6E10A8B1C88941573511743EC9A8F6D99FCBE1A4F2C960416` | Build driver. Its header says it links the S4a SDK and that "B4 runs before any S4b SDK build". |
| B4 | `build/agent2/prep-b4.py` | `943EFE88F979FF0916C323F98FF328D548B96E522360B2A6A865C68C29DDB770` | Makes the copies into snapB/snapB3. `--go` never ran. |
| B4 | `build/agent2/b4-dryrun.py` | `A67C92BBBD8252E75CE66CB5FBFC692076D4C3C0120D98AF9BBE5A1227002D68` | Read-only planner. |
| B4 | `build/agent2/b4-dryrun-1424.txt` | `8EE275D1CE170F561A8AC0F563082D5CF12C5368A67CEBD5F6F384820B63D4FD` | 0 FAIL / 0 WARN on 11-22, against the S4a install. The install-DLL checks would fail now. |
| B4 | `build/agent2/prep-b4-1546.txt` | `BEDBE51A17B6620BF5524AAEE3036AA3613B0B5A25404232B61781F3E25ABC2C` | Dry run: "READY for --go". |

## 3. Submodule edits: uncommitted by design, not candidates

Agent 1 (`perf-notes/SESSION2.md` L3310): third-party worktree changes stay uncommitted, and are rebuilt from tracked scripts and patches.

| submodule | saved patch | sha256 | base | state | rebuilt from (tracked) | checks |
|---|---|---|---|---|---|---|
| `DimensionsRecomp/thirdparty/plume` (3 files: `plume_d3d12.cpp`, `plume_d3d12.h`, `plume_vulkan.cpp`) | `build/agent2/pending/plume-local-on-e0c8871.patch` | `BF38B18300164ECF3817D16082377BBB5BA456D725A86008DE08AF216ADDCBF8` | e0c8871: the submodule's checked-out HEAD and `prepare_plume.py`'s PIN | in the live tree (forward exit 1, `-R` exit 0) | `DimensionsRecomp/tools/gpu-aot/prepare_plume.py` + the 7 `DimensionsRecomp/tools/gpu-aot/patches/plume-*.patch` | `prepare_plume.py --check` PASS (06:24). `build/agent2/plume-rebuild-check.py` PASS (06:27): the PIN plus the 7 patches, applied in prepare_plume order with GNU patch `--fuzz=0` (one hunk at offset 3), give exactly the 3 live files. Report: `build/agent2/pending/plume-rebuild-check.txt`. |
| `DimensionsRecomp/rexglue-sdk/thirdparty/simde` (1 file: `simde/x86/sse.h`) | `build/agent2/pending/simde-local-on-71fd833d.patch` | `2A6DE738794F5DA059934444CC327082DDEEB24D8C78F56DB487A9DF9EBF27DC` | 71fd833d: SDK HEAD's gitlink and `prepare_simde.py`'s PIN | in the live tree (forward exit 1, `-R` exit 0) | byte-identical to the tracked `DimensionsRecomp/rexglue-sdk/patches/simde-native-m64-stream.patch`, which `DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py` applies | same sha256 |

> [!WARNING]
> The game repo's gitlink for plume is ceaeeee0f7e9, which is not in the local plume clone. Agent 1's note (`perf-notes/agent1-pause-state-lines.md` L128-130) says "Do NOT commit the plume pointer". A plain `git submodule update` would look for ceaeeee, not e0c8871 (not tried).

## 4. Removed, and not a pending diff

- **Removed:** `build/agent2/pending/cg26-toml.diff` (`6982CEC5…`, written 06:07:56, deleted 06:27).
  - It was a no-index diff made from the workspace root, and git reads it as a rename (`rexlego/… => agent2/cg26/…`), so it was not a drop-in.
  - Its hunk duplicated toml-A.diff.
- **Not a pending diff:** `rexlego/legodimensions_manifest.toml` in snap1 is the machine-local XEX manifest. It is gitignored by design.

## 5. Open questions for after the pause

1. **Codegen B: the formal read-out says drop** (`build/agent8/readout/w-followup/W4c.md`: no gain, +2.6 % [−1.2, +6.5]). That settles my old lean. The action is left for after the break, and it also decides CG26 arm B and B4:
   - with B dropped, retire arm B, the B rollback configs and the B4 scripts;
   - only if B is kept after all, re-plan B4 on S4b (Agent 7's queue names devoffB4b-* bins) and re-run its dry runs.
2. **CG26 arm A:** land the toml line only together with a regen and Agent 10's 4 gates. My CG26 build recipe is in HANDOFF §4.1.
3. **#21:** rated (`build/agent10/t27/r21-s4t1.md`). Next, after the break: Agent 7's SHOULD (record F-CA under MP4 gap 2, and say whether any earlier th2 run hung) and the §9.2 wording fix; then build it, re-pin the native4b-bin baselines (the native fingerprint changes), and run F1 first and W8b only after F1 and W1 pass, under the 5 conditions.
4. **#19:** the rate request is written (`build/agent7/s4-r1s2/RATE-REQUEST.md`: first 08:12, rev 1 08:40, task #33 corrections 09:04-09:59). Still needed (re-checked 11-23 10:15):
   - a syntax check once compiles are allowed;
   - Agent 10's rating, after the break;
   - for the build, the right apply form: copy `build/agent7/s4-r1s2/new/sdk/` or use the `--directory` form in RATE-REQUEST.md §2, and confirm 5 "Checking patch" lines. In snap1, the `git -C <sdk root>` form in CHECKS.txt L22-23 skips all 5 files and exits 0. RATE-REQUEST.md §2 steps 1-3 also cover the before and after hashes and the full SDK rebuild.
5. **#33 / #34:** staged together and rated (§1). Next, after the break:
   - build the first test bin without hunk #5 (S1; `build/agent6/s33-popin/CHECK.txt` says which lines to delete). The compile risk stays open until it is built;
   - row 1 (cvar off, patched bin against base bin) must show identity before anyone reads ON timings, and the user's row-3 review on a visible desktop gates any recommendation;
   - run the resolve-after-drop diagnostic (d) before recommending ON (S2);
   - for ON and gate arms only, add `d3d12_pipeline_creation_no_wait` to `--allow-new` in Agent 3's s4b kit (N3).
6. **CTR:** a tracked switch, such as a CMake option, would be a new change. None is staged.

## 6. Files of this report

| file | sha256 |
|---|---|
| `build/agent2/pending/PENDING-DIFFS-draft.md` (the annex, with the 06:30 note) | `11455F143BAB9178B4780FD90F6443F560F8A9364D86109F49EC4B33DAF7D14A` |
| `build/agent2/plume-rebuild-check.py` | `962F1A3478753DB0233A0EA20D146396677BB828828A4D982CEED9A534F1BEB9` |
| `build/agent2/pending/plume-rebuild-check.txt` | `69FB136EB577A463DD11846F3B4A62304231B65C285A7532FE1B31DFFC6FC545` |

Sources added by tasks #31 (`Get-FileHash` at 07:49) and #34 (at 10:15); read-only:

| file | sha256 | note |
|---|---|---|
| `build/agent10/t27/r21-s4t1.md` | `C2DB5124DA84A7EAA3C318106CA4D549A049D4427B8D5959234E55F72717DA50` | the #21 rating (06:32) |
| `build/agent10/t27/r33-popin.md` | `ACF0BDB5A526236232A41D2A87FF2AACC17C00BE9ED35D3A227CCA238A0862B0` | the #33/#34 rating (07:34, with an adoption note at L162 added 07:44); its L9-11 list the hashes it rated |
| `build/agent6/s33-popin/s33-popin.patch` | `0D23024484CCDEE1B15AF3EB79DC28759F9D422E78536F4766C83C2071CC2EFD` | the rated patch (06:28), unchanged |
| `build/agent6/s33-popin/DESIGN.md` | `B2E33FE8B99F4041DD880D8A41F735F93FF220B0767DE78937AE131B57BAB318` | written 07:40:47. Agent 10 rated 611B62F5…; Agent 6 has since recorded the rating, docs only (§8 builds without hunk #5, §9 item 5 is S2, §10). This is the version Agent 10 checked at 07:44 (r33-popin.md L162). |
| `build/agent6/s33-popin/CHECK.txt` | `5101A7B136CCCBE48DF420F1435C6743CAEF6B74F7DB86593A219F21FE624696` | written 07:42:49. Agent 10 rated 43A4F211…; Agent 6 has since added the hunk #5 recipe (patch L82-93) and the record of the withdrawn copy without hunk #5. This is the version Agent 10 checked at 07:44 (r33-popin.md L162). |
| `build/agent8/readout/w-followup/W4c.md` | `965F323E151D508A6C8FF4831D6377B27AA47DEB5DB69D9E6E30AA0CF427F221` | the codegen B read-out (06:40) |
| `build/agent7/s4-t1/s4-t1.diff`, `build/agent7/s4-r1s2/s4-r1s2.diff` | as §2a | re-hashed at 07:49: unchanged |
| `build/agent7/s4-r1s2/RATE-REQUEST.md` | `1C2B8688A43ED4DC308E26D52271C3FFD8BEBC50863991624737D20CFC8E40CA` | task #34: #19's rate request (first 08:12, rev 1 08:40, task #33 corrections 09:04-09:59; written 09:59:08); Agent 10 rates it after the break |
| `build/agent7/s4-r1s2/SHA256SUMS.txt` | `8A38FD9D3CD8B3752A5319B09BA3B9F61203ADEA35A5B99F8F6427F725CA9C5B` | task #34: unchanged since 11-22 23:10; all 12 entries match (re-hashed 10:15) |
| `build/agent7/s4-r1s2/s4-r1s2.diff` | `06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7` | task #34: unchanged (SHA256SUMS.txt L12; re-hashed 10:15) |
| `build/agent7/s4-r1s2/CHECKS.txt` | `A5A8F777494D6C9EB2C89C71869D8FAB181F921AB376A7632DBF2B648E9826F2` | task #34: its L24 now warns about the snap1 apply trap (written 09:59:08) |
