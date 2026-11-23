# PENDING-DIFFS (draft): candidate changes that are NOT in the committed trees

Written 2026-11-23 06:10 by Agent 2's read-only helper (board task #28, the wrap-up). Updated 06:21 with the 3 files Agent 2 put in `build/agent2/pending/` at 06:07:55-56 (the cg26-toml.diff row in §1a, §1c, §2f). It is a draft for Agent 2. Nothing was built, run or changed; this file is the only write. All paths are workspace-relative.

> **Note (Agent 2, 06:30):** this draft is the detailed annex of `build/agent2/PENDING-DIFFS.md`, which supersedes it where they differ. Two changes since 06:21:
> - `build/agent2/pending/cg26-toml.diff` was **deleted** at 06:27. It was redundant with toml-A.diff and was not a drop-in (§2f). For HEAD, use `toml-db16cyc-pause-A.diff` with `-C DimensionsRecomp`, or copy new-A.
> - §3 point 15 is **closed**. `build/agent2/plume-rebuild-check.py` (06:27) rebuilt the 3 plume files from e0c8871 + the 7 tracked patches, in prepare_plume.py order with GNU patch `--fuzz=0`, and they equal the live files (report: `build/agent2/pending/plume-rebuild-check.txt`). `prepare_plume.py --check` also passed at 06:24.

## 0. Baseline and method

- **Committed trees** (both on `perf/opt`), re-checked with `rev-parse` at 06:01:53:
  - `DimensionsRecomp` HEAD `b0bd3b4aba5fe4d26572d89910836ee7db48fcea` ("S4b/S4c: keep-watch memory_watch, GPU wait back-off hooks, probe option; SDK at S4b").
  - `DimensionsRecomp/rexglue-sdk` HEAD `5350b1de99276b7a7be701bf00914f1ee58ce9bc` ("S4b: C1 v3 keep-watch, M1 non-temporal copy, P2 counter, r1r2, db16cyc_pause option").
- **Working tree == HEAD == `build/agent2/snap1`** for every tracked file in scope (`build/agent2/COMMIT-CHECK.md` L8-L21, 05:57, PASS). So anything staged against "snap1" or "the S4b sources" has HEAD as its base.
- **sha256** is `Get-FileHash` on single files, 05:57-06:03 (06:12-06:17 for the 3 files in `build/agent2/pending/` and the live plume files). In the game repo (`core.autocrlf=true`), the sha256 of a text file here is its CRLF working-tree form. The LF HEAD blob hashes differently. SDK blobs are byte-identical to the working tree.
- **"applies to HEAD?"**: `git --no-optional-locks -C <repo> apply --check [-R] [--directory=rexlego] <diff>` at 06:01:53, run against the working tree (== HEAD). The exit codes are in §2. For after-files, the staged before-file sha256 is compared with the committed file's sha256.
- **Apply checks need `-C <repo>`.** The workspace root sits inside an enclosing git work tree (`git rev-parse --show-prefix` there is non-empty). Run from the workspace root, `git apply --check -v build/agent2/pending/cg26-toml.diff` printed `Skipped patch '…'` and exited 0, and so did `-R`: nothing was checked. Each `-C` check in §2 either failed in one direction or printed `Checking patch …`, so none of them was skipped.
- **Item numbers** (#19, #21, #26, #33, #34) are the rows of `perf-notes/S4-DRAFT.md` §1 (from L194). They are not the agy-grid board task numbers.
- **Line numbers:**
  - `perf-notes/S4-DRAFT.md`: its 05:55 version (549 lines; still unchanged when re-checked at 06:17). Agent 11 is editing it during the wrap-up, so these can move.
  - `perf-notes/SESSION2.md`: up to L3312 (05:43). At 06:18 it had 3319 lines. L3315-3319 (06:05) are about the day-session draft; their "#26" seems to be a board task (it is about run-day.ps1), not S4 item #26.
  - The other notes cited have not changed since 11-22 23:14 or earlier.

## 1. Tables

### 1a. Candidate tree changes

| item | path | sha256 | base | applies to HEAD? | status | owner | description |
|---|---|---|---|---|---|---|---|
| CG26 arm A (**latest; the arm for the HEAD line**) | `build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-A.diff` | `95D901B9784705FA656145487B5611BA95A606E4DBD28FA7BE60C9E93B8F2620` | base-A toml `7F775847…`, which is byte-identical to HEAD's `rexlego/legodimensions_config.toml` (working-tree form) | **yes**: exit 0. `-R` gives exit 1, so it is not applied yet | **staged** 11-22 14:14 (Agent 9, a9 R2.17). **Rated** by Agent 10 ~14:45: ON is output-identical and SAFE to test after 4 gates (b2r row 37 L49, §36 L1948-1966). **Not built** | Agent 9 | adds one line, `db16cyc_pause = true` (CRLF), as root-key line 24, just before `[functions]` |
| CG26 arm A, after-file | `build/agent9/s4/spin/db16cyc-pause/toml/new-A/rexlego/legodimensions_config.toml` | `11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF` | before = `build/agent9/s4/spin/db16cyc-pause/toml/base-A/rexlego/legodimensions_config.toml`, `7F775847DB9CC2DA89DC3EDE57A0AD5F30FDF58D98F5021A0E27A4E0E4DA95BF` | **yes**: the before-hash equals HEAD's working-tree sha256 | as arm A | Agent 9 | the full toml with the line: 18167 B, 816 CRLF lines (HEAD has 18145 B, 815 lines) |
| CG26 arm A, Agent 2's copy | `build/agent2/cg26/DimensionsRecomp/rexlego/legodimensions_config.toml` | `11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF` | same bytes as new-A | yes (as new-A) | copied 11-22 20:54:29 (agent2-baseline L47). The CG26 regen never ran, and `build/agent2/devoff4b-cg26-bin` does not exist | Agent 2 | the toml the CG26 regen would use (a9 L2387) |
| CG26 arm A, Agent 2's export (06:07:56) | `build/agent2/pending/cg26-toml.diff` | `6982CEC56DAE8EA5A831B088C92429D8FECD9DBF153B7ADF12F709CD5CA9F425` | `index 2233e63..c946aed`: `2233e63` is HEAD's blob of `rexlego/legodimensions_config.toml` (`2233e6343b7d…`); the b-side is Agent 2's copy (row above) | **content yes, paths no**: the same hunk as toml-A.diff, but as a no-index diff made from the workspace root. `-C DimensionsRecomp -p2 --check -v` exits 0 and names it `rexlego/… => agent2/cg26/DimensionsRecomp/rexlego/…`, so a plain apply would not just edit the toml in place (§2f) | written by Agent 2 at 06:07:56, 666 B. Not applied, not built | Agent 2 | arm A's line (`+db16cyc_pause = true`) once more. For HEAD, toml-A.diff or a copy of new-A is the clean form |
| CG26 arm B (B line only) | `build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-B.diff` | `5D5892D33D09AF9D6889AF5BC991C82CD4443A8F7493053584BF6889261585B3` | base-B toml `E60EAF1C…` = codegen B's batch-nolr toml | **no**: exit 1, because its base is the batch-nolr toml, not HEAD's | staged 14:14. Rated with arm A (b2r L1965: it applies on base-B, snapB and batch-nolr). Not built. Its target line is codegen B, whose lean is "drop B" (S4-DRAFT L13-14); no decision yet | Agent 9 | the same line, after `musttail_calls` (new-B line 37) |
| CG26 arm B, after-file | `build/agent9/s4/spin/db16cyc-pause/toml/new-B/rexlego/legodimensions_config.toml` | `FFC119BFE2639E30E8CEC4E5258F1428DB06C62E0E880003DCF9EF1113B7B570` | before = `build/agent9/s4/spin/db16cyc-pause/toml/base-B/rexlego/legodimensions_config.toml`, `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` | no: the before-hash is not HEAD's `7F775847…` | as arm B | Agent 9 | 19024 B |
| CG26 tool (reference only) | `build/agent9/s4/spin/db16cyc-pause/db16cyc-pause.diff` | `AC554DBBD965BF941BADE6391D0E0F483BE075B8A72434EEE8CB9D189ED61452` | `base/` = HEAD^: config.h `D07C575F…`, config.cpp `0ED529B7…`, builders/system.cpp `D1269273…` | **already in HEAD**: forward exit 1, `-R` exit 0. Its `new/` files equal HEAD: `CD39B0E1…`, `4706A7F2…`, `FAD43720…` | committed in SDK `5350b1d` (option default OFF; COMMIT-CHECK L46-48) | Agent 9 | not pending. Listed so it isn't counted twice |
| CTR | no diff file | n/a | HEAD: SDK `src/graphics/d3d12/deferred_command_list.cpp` L21-27 (`#ifndef REX_D3D12_DEFERRED_COUNTERS` → `0`) | **nothing to apply**: no tracked file changes. At HEAD, `git grep` finds the macro only in that file, and in no CMakeLists in either repo | variant prepared as dry runs 11-22 20:15-20:31. **Not built**: `build/agent2/devoff4b-ctr-bin` does not exist. The code is #20 step 1, rated SAFE (S4-DRAFT L224). Agent 10's FYI: the one-TU route is enough (b2r L2218) | code: Agent 7. Variant: Agent 2 | build `deferred_command_list.cpp` with `-DREX_D3D12_DEFERRED_COUNTERS=1` (snap1-sdk ccdb), then relink `rexgpu-xenos.dll` (agent2-baseline L58-60, L679) |
| B4 | no diff file | n/a | planned at the S4a level on Agent 9's batch-nolr codegen (`build/agent2/b4-dryrun-1424.txt`; `build/agent2/run-b4.ps1` L1-4): snapB (S2) + 35 copies from snap1 (devoffB4, option B); snapB3 (S3d) + 6 S4a copies (nativeB4) | n/a: a build plan, not a tree change (see §2c; its delta against HEAD is not verified) | **deferred** since 11-22 16:17-16:48, when W4b showed no frame-time change (S4-DRAFT L401, L471; agent2-baseline L99, L115). Not built: `devoffB4-bin` and `nativeB4-bin` do not exist. `prep-b4.py --go` never ran: there is no `B4-copies-*.tsv` in `build/agent2/` | Agent 2 | the B line + S4a |
| codegen B (**latest B config**) | `build/agent9/configs/batch-nolr.toml` | `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` | HEAD's toml + 16 lines at L24-39, with nothing removed (Compare-Object; 815 → 831 CRLF lines) | as a whole-file replacement, yes: HEAD's toml is a strict subset. No git-format diff exists | rated SAFE except skip_lr (Agent 10, 11-21 23:48; agent1-tracker-s2 L273); skip_lr is not set (B L37). W4b's +6.0 % fps hint (SESSION2 L2788) did not repeat in W4c, where B was slower in 5 of 6 rounds (SESSION2 L3252-3258; the second pass was skipped, L3298). Lean: "drop codegen B" (S4-DRAFT L13-14). Pending: the formal read-outs (Agents 7 and 8, ~10:00) and Agent 6's W4c logdiff | Agent 9 | adds root keys `ctr_as_local`, `xer_as_local`, `reserved_as_local`, `cr_as_local`, `cr_compare_so_zero`, `rlwinm_lowering`, `flush_mode_elision`, `vmx_vector_fallbacks` and `musttail_calls`, plus comments |
| codegen B, install copy | `build/agent9/install/batch-nolr/legodimensions_config.toml` | `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` | the same bytes as the row above | as above | the toml of the batch-nolr codegen tree behind devoffB-bin and nativeB-bin (agent2-baseline L218). That tree's generated outputs are pinned by `build/agent9/install/batch-nolr/SHA256SUMS.txt` `24CE1493FB8DAE37E00B556EB8871D633921E44378D960DE4359B104B16CDB8E` (not walked) | Agent 9 | = CG26 base-B |
| codegen B, superseded | `build/agent9/configs/batch.toml` | `B272725044741AE84942B22A0F51ECC13FD16E90BE3A5C3E7E6A4F74B5DAF950` | not diffed against HEAD | not checked | **superseded**: it has skip_lr and is "kept for diffs only" (a9 L1571) | Agent 9 | the first batch config |
| codegen B, rollback 1 | `build/agent9/configs/rb1-nolocal.toml` | `AE9F8F967FBB264919A63463CA4958F856C18A0405A4895440D6C36A31084EEC` | batch-nolr without the 5 localization keys (key column of a9 L894) | not checked | staged as the rollback for a gate fail; unused (a9 L62; agent10-codegen-review L505) | Agent 9 | B without the `*_as_local` keys and `cr_compare_so_zero` |
| codegen B, rollback 2 | `build/agent9/configs/rb2-nomusttail.toml` | `FC034D495DAC395F45CDC0AC0DC7BFD88C8D2046A09590B88563B63BE1C82924` | batch-nolr without `musttail_calls` (a9 L895) | not checked | as rollback 1 | Agent 9 | B without `musttail_calls` |
| #21 S4-T1 (**rev 2, latest**) | `build/agent7/s4-t1/s4-t1.diff` | `46FFD2E9044094DCE17C364C382F7BF2563E071E0DF81750C1DE1BC38BE38050` | snap1 rexlego (README L3-4). The `before/` files equal the HEAD working tree (rows below) | **yes**: exit 0 with `--directory=rexlego`. `-R` gives exit 1 | **staged**: rev 2 at 11-22 22:48; rev 1 is not kept as a file. RATE-REQUEST.md for Agent 10 at 23:25. The independent review found no BLOCKER (check/DIFF-REVIEW.md). Agent 9's pre-read passes 4/4 (SESSION2 L3182). **Not rated** (S4-DRAFT L225) | Agent 7 | env `LEGO_NATIVE_CHAIN_PRIORITY=1` raises the thread priority of the native worker chain; unset = OFF. +51/-0 in 3 files |
| #21 after-file | `build/agent7/s4-t1/after/src/gpu_native/native_worker.cpp` | `071E2F4B784D40DEF4A58870F438EFDB194B96E2D2FCF0A8349E8DDD7141BFDA` | before `7157E8F2EDC3D5C438E3F2F21B50051693A3046B36A4BD8EE096901DF8FE0E2F` | **yes**: the before-hash equals HEAD's working-tree sha256 | as #21 | Agent 7 | → `DimensionsRecomp/rexlego/src/gpu_native/native_worker.cpp` |
| #21 after-file | `build/agent7/s4-t1/after/src/gpu_native/native_recording.cpp` | `00F03D84A0C594FA6DC4850CE36AB77847453A913AA077286F6D0D11B900EC6C` | before `48F0C429DDB89E452794365788C8B34EA9510A4B10B86F93771F418F3E53AA9B` | **yes** (as above) | as #21 | Agent 7 | → `DimensionsRecomp/rexlego/src/gpu_native/native_recording.cpp` |
| #21 after-file | `build/agent7/s4-t1/after/src/gpu_native/native_preparation.h` | `88C57831AF2B200A36E966C000F4D783004D26EB984A54BDEEADE245709CCFE0` | before `889F3FA6F207011B03D044E745C2952C68200A44C99BE6E13EB810357D3D41A5` | **yes** (as above) | as #21 | Agent 7 | → `DimensionsRecomp/rexlego/src/gpu_native/native_preparation.h` |
| #19 R1 stage 2 (only version) | `build/agent7/s4-r1s2/s4-r1s2.diff` | `06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7` | the S4b SDK = snap1 (README L5). The `orig/` files equal HEAD (rows below) | **yes**: exit 0. `-R` gives exit 1 | **staged** 11-22 23:10: PROOFS ALL PASS, CHECKS.txt 23:13, functional-row and soak drafts 23:31-23:35. **RATE-REQUEST.md not written**: README L18 says "to do (Monday morning)", and it was absent at 05:57. **Not rated** (b2r L1363). S4-DRAFT L223 still reads "design only" | Agent 7 | cvar `d3d12_async_submit` (OFF, kInitOnly) hands the submit to a worker. +320/-1 in 5 files |
| #19 new-file | `build/agent7/s4-r1s2/new/sdk/include/rex/graphics/d3d12/command_processor.h` | `EF0DC13DA29703C7FEDC13FE7C8542E592FB82460817F1B88C4930D92F12CD4C` | orig `67F4E8380C879377F06B6E3DD879EE737A82BBBE9682F123247ED5D0671FF325` | **yes**: orig == HEAD | as #19 | Agent 7 | `new/sdk/` maps to `DimensionsRecomp/rexglue-sdk/` |
| #19 new-file | `build/agent7/s4-r1s2/new/sdk/include/rex/graphics/d3d12/deferred_command_list.h` | `E7512824D8E6F9673C59457CD28FA34DD7795E4D495B3BAB76D07774AEA60650` | orig `9F6CC70A6922232D4FF7A32303E8B785A01D1C7A3CF54373369EF6B23F8AF0F0` | **yes**: orig == HEAD | as #19 | Agent 7 | |
| #19 new-file | `build/agent7/s4-r1s2/new/sdk/src/graphics/d3d12/command_processor.cpp` | `05BBCE8B7E3FB27D43F364031082F73DFCD5BD223307DB794FB3C6DD6E91807C` | orig `027204B53A271D69275FCC6FEC6B2222905155E1FD67808F88A79329F4022C0E` | **yes**: orig == HEAD | as #19 | Agent 7 | |
| #19 new-file | `build/agent7/s4-r1s2/new/sdk/src/graphics/d3d12/shared_memory.cpp` | `9E908D31E6F64A31A55126CB0E97B37F1DD1A677B7026872A839FAE53A8FEB8A` | orig `2A5ADF13B5E433F1F10B5C6AF9C14F8812527C4E155A5146B166723457B6EBB4` | **yes**: orig == HEAD | as #19 | Agent 7 | |
| #19 new-file | `build/agent7/s4-r1s2/new/sdk/src/graphics/d3d12/texture_cache.cpp` | `4183887C9D625B97D8DDB7B5D2BF5F28D2B9B122DBF3488BDA1753100CB9BAB4` | orig `949CCF4F4D80975D4DF3E833604BDBEC8C1442D787E2492085F0FA966E7F8C99` | **yes**: orig == HEAD | as #19 | Agent 7 | `orig/` also holds deferred_command_list.cpp `30FF5744…` (== HEAD), for reference only (unchanged) |
| #33 | none found | n/a | n/a | n/a: `d3d12_async_pipeline_no_wait` is not in SDK HEAD | proposed. The user said yes, as an opt-in that is OFF by default (23:24; SESSION2 L3196; S4-DRAFT L455-457). Not implemented, not rated | Agent 6 (design) | "Don't wait for pipelines": skip the draws whose pipeline isn't ready (S4-DRAFT L249) |
| #34 | none found | n/a | n/a | n/a | proposed with #33, optional; not rated (S4-DRAFT L250) | Agent 6 (design) | a dropped-draw counter for #33 |

### 1b. Supporting inputs (tools, reports, kits; not tree changes)

| item | path | sha256 | bytes, mtime | note |
|---|---|---|---|---|
| CG26 | `build/agent9/s4/spin/db16cyc-pause/HASHES.txt` | `2A94639CAF6F148D8EF52B0A66A59380056DE70246C775667712943683B9D20A` | 3500, 11-22 14:14 | Agent 9's hash list. The 7 toml/diff hashes cited in §2a match it |
| CG26 | `build/agent9/s4/spin/db16cyc-pause/stage.py` | `21EACD7BB1AF31916A7D604F1ABA6133480EFEF1081F62B12F98A4E40F707A79` | 9047, 14:14 | Agent 9's staging script |
| CG26 | `build/agent9/s4/spin/db16cyc-pause/syntax/legodimensions_recomp.383.cpp` | `B35C1310AF0AFA7C3E60BF323F098703097C9BDE811E346E1935A7F3F359F9D9` | 1034974, 14:15 | the TU383 candidate (b2r L1966: minus its 8 pause lines, it equals the snapB control) |
| CG26 | `build/agent9/s4/spin/db16cyc-pause/syntax_check_codegen.ps1` | `44678FD4E4B4BB35D8EFCF96B5DCC15181A90FA3A6BCA358EED7AE6054E84FC4` | 8798, 14:14 | syntax check |
| CG26 | `build/agent9/s4/spin/db16cyc-pause/syntax-20261122-141452.txt` | `1057617DAE254E6429B74E2E4FD226C5B64DFAAAB12A97E9FE3B34BD0BC68587` | 2561, 14:16 | syntax PASS report |
| CG26 | `build/agent2/cg26/tool/rexglue.exe` | `9145166CDBEF5500E6E2607ED80AA6FC94CA1772DE2D3E87FF9E13BEAD87D586` | 3717632, 20:36 | the regen tool with the `db16cyc_pause` option (a9 L2357) |
| CG26 | `build/agent2/cg26/tool/rexruntime.dll` | `A33801D1538D61759D35FD137EBC9F5EAD636D7D26E9A79DC3B4994A22CB9F12` | 10909184, 20:36 | the same as devoff4b-bin's rexruntime `A33801D1538D6175` (agent2-baseline L42) |
| CG26 | `build/agent2/cg26/DimensionsRecomp/rexlego/legodimensions_manifest.toml` | `7F0106F4E2E1C50A02B1FBA1126F81F7869C5A4E95E848A79215E1C10DCE2C3B` | 780, 20:36 | manifest whose file_path points 5 levels up (agent2-baseline L77-78) |
| CG26 | `build/agent2/cg26/DimensionsRecomp/rexlego/generated/` | not hashed | n/a | a robocopy of snap1's 887 files (agent2-baseline L78); not walked |
| CG26 | `build/agent2/cg26/stage-cg26.py` | `8B3DF2B18A47C35E3EF1D6F1969A8E6C6511E77E973213AE80CC8C46DB1C777D` | 4036, 22:47 | stage-variant.py wrapper; writes the sha256 notes for the tool, toml and 10 TUs (a9 L2388-2389) |
| CG26 | `build/agent2/cg26/cg26-check.py` | `6D202527224A3C491C2FB829827450D380AF37952A30B014C27F5971E6731E5E` | 10609, 22:18 | Agent 2's check, with the stamp fix (agent2-baseline L55-57) |
| CG26 | `build/agent2/cg26/checks/selftest-precopy.txt` | `FB1EDDBF4977A8631EC82D216BC98C76424CA64D45BEEDE13E634589EE3456A2` | 2515, 20:39 | self-test |
| CG26 | `build/agent2/cg26/checks/selftest-stampfix.txt` | `B1CA3EE3C396208B4B476AF51314D59C749A0CF48F35BBA20CE8C4038929BBEA` | 2961, 22:25 | self-test after the stamp fix |
| CG26 | `build/agent2/cg26/checks/selftest-stampfix.stdout.txt` | `601651689A2B6EC45047A86B755D900E35402B364152B05473CDE6DD3C7B26AC` | 2986, 22:25 | its stdout |
| CG26 | `build/agent2/cg26/holdrun-selftest.log` | `1880B7AA0F567FC3580160BB9CAACFE7CA0BA2138FA15BEA23C79AA1907FD7F7` | 268, 20:59 | holdrun self-test |
| CG26 | `build/agent2/holdrun.py` | `9D9BD2931174FB9ABC1334C502B9463A28D53EEB613C73FA2B2CA1158089E396` | 3175, 20:59 | HOLD-aware runner for the regen (agent2-baseline L57, L60) |
| CG26 kit (**latest**) | `build/agent9/cg26-check/cg26_check.py` | `DDBA731CC22D74BDA05A50FECF21E0D150BF1E95E3CD25C10B676BDFBCA0A416` | 35446, 22:53 | the current version since 22:53, after the ADVICE text fix (a9 L2337, L2437). Runs 1-2 tested the earlier `A179EB13…`, which agent2-baseline L26 still cites |
| CG26 kit | `build/agent9/cg26-check/README.md` | `FFEBD146C20CF64C116957C355A1847361B2501EF6F3F4B43129DE40176FF8F2` | 9285, 23:00 | one-line command and test table |
| CG26 kit | `build/agent9/cg26-check/test_cg26_check.py` | `40339E0287095AD4008A695F32CBE9C88B5574EAEED38B382D4DC8E71ADEBFF9` | 17848, 22:36 | mock regen tests |
| CG26 kit | `build/agent9/cg26-check/test-20261122-223737.txt` | `D3F18E1C7A94ACBA0808621F996DAE002A18DA6DB717BD085514A2300F67C1FB` | 7048, 22:40 | run 2: ALL OK, 14 of 14 (a9 L2411) |
| CG26 kit | `build/agent9/cg26-check/test-20261122-222640.txt` | `A4FA68BC6B2B896B528422998FFF4EF0C9A461FAD0E8FB16E5FB378026C8B323` | 4653, 22:33 | run 1 (superseded by run 2) |
| CTR | `build/agent2/ctr/list-ctl.tsv` | `6A357FEFBB0CE06A4BE09229FB9B32F6F0ED6576BF73ABD5753C441EFC8AD494` | 425, 20:15 | control TU list (has machine-specific absolute paths) |
| CTR | `build/agent2/ctr/list-on.tsv` | `A63A77CD86AB7DA09C75468EE1DBF6857DE3E5D4F12B97AED2E9412CE6256305` | 424, 20:15 | ON TU list (same) |
| CTR | `build/agent2/ctr/log-ctl/recompile-commands.txt` | `EB1670476453D6FCF8CFA92E60A984C111E0AEE79406C6FCA0CE74F8DB4BC3F0` | 3171, 20:31 | dry run, control |
| CTR | `build/agent2/ctr/log-on/recompile-commands.txt` | `9B8A7F81F73A6B678CCE91D3940FCC9B99A08051F0670EC0C578583AB71FEFFE` | 3202, 20:31 | dry run, ON. L3 is the clang++ command with `-DREX_D3D12_DEFERRED_COUNTERS=1`; L2 is the object `rexgpu-xenos.dir/Release/d3d12/deferred_command_list.cpp.obj` |
| CTR | `build/agent2/ctr/link-dry/relink-command.txt` | `B8AA6B6D2F478EB262B3D76FFC217920802A1C77BA3F2CD379E7F53FFFB90758` | 4870, 20:31 | relink dry run. `ctr/obj-ctl/` and `ctr/obj-on/` are empty |
| CTR + CG26 | `build/agent2/recompile.py` | `966C0F04F4E9197747271F088AF12E0BBCBF39D3E18F57CC293CD071F6BA692A` | 7740, 20:17 | one-TU recompile tool |
| CTR + CG26 | `build/agent2/relink.py` | `6BB8E89C53C0B63FB6D3952EDE9910360F58108EE312F766A797EA97242C4034` | 16314, 20:38 | relink tool |
| CTR + CG26 | `build/agent2/stage-variant.py` | `D2BD1C6358FC19C1EBF160AA7EADF44F3FAE50EA64F5EC78320F463B77E40EB7` | 5297, 20:35 | variant bin staging |
| B4 | `build/agent2/b4-dryrun.py` | `A67C92BBBD8252E75CE66CB5FBFC692076D4C3C0120D98AF9BBE5A1227002D68` | 30004, 14:27 | read-only planner |
| B4 (**latest report**) | `build/agent2/b4-dryrun-1424.txt` | `8EE275D1CE170F561A8AC0F563082D5CF12C5368A67CEBD5F6F384820B63D4FD` | 10393, 14:24 | SUMMARY: 0 FAIL, 0 WARN. Option B needs 35 copies |
| B4 | `build/agent2/b4-dryrun-1404.txt` | `BD98658F7FECB2FA24BDDE5222C358E47BFA522C0269DA4E7E01501E5BE7B0F2` | 9134, 14:04 | superseded by 1424 |
| B4 | `build/agent2/b4-dryrun-1402.txt` | `0690C8F3339795F10B55EAECA834369382034A69A5CB914AF20EBDA0C32A8927` | 15291, 14:02 | superseded by 1424 |
| B4 | `build/agent2/prep-b4.py` | `943EFE88F979FF0916C323F98FF328D548B96E522360B2A6A865C68C29DDB770` | 21190, 15:44 | copies snap1 files into snapB/snapB3 (`--go`; never run) |
| B4 | `build/agent2/prep-b4-1546.txt` | `BEDBE51A17B6620BF5524AAEE3036AA3613B0B5A25404232B61781F3E25ABC2C` | 6032, 15:46 | dry run: 0 FAIL, "READY for --go" |
| B4 | `build/agent2/run-b4.ps1` | `56A04A77810AA6A6E10A8B1C88941573511743EC9A8F6D99FCBE1A4F2C960416` | 16808, 15:46 | build driver. Header: links against the S4a SDK; "B4 runs before any S4b SDK build" |
| codegen B (tools) | `build/agent2/B-diffs/b-chain.new.diff` | `7310180A74E367DCF1D57FA74D976E73D254AF53EA8C2DB4BD86196A77EBCA34` | 3625, 11-22 02:20 | new `b-chain.ps1` (Agent 2's B-line tooling; not a tree diff) |
| codegen B (tools) | `build/agent2/B-diffs/nolr-comments.diff` | `FE497ED39AB0B809594F9D09F8564246E73FAA14178E6D77BAA1CD5DD5945A72` | 4890, 02:20 | patch-b-tools.py, gen-check.py, snap-gate.py vs `*.pre-nolr` |
| codegen B (tools) | `build/agent2/B-diffs/preB-tools.diff` | `0C97791FCC44A8585CACE50FB2446A5513A7907EF0CFB55B0D83E3ED75CFC7A6` | 31647, 02:20 | build-snap.ps1, stage-snap-bin.ps1, gen-check.py, snap-gate.py, stop-snap.ps1 vs `*.pre-B` |
| codegen B (tools) | `build/agent2/B-diffs/prep-b.nolr.diff` | `643F3B6131CDEAADA9D6825629510F83268863D11DDD52BF0736F4B936DF5F26` | 9454, 02:20 | prep-b.py vs `*.pre-nolr` |
| codegen B (tools) | `build/agent2/B-diffs/run-b.nolr.diff` | `CC6EAD365E8EF0309A5C987B4DFDD34E7A6AC1840F4537CB66176EAC10367E35` | 6349, 02:20 | run-b.ps1 vs `*.pre-nolr` |
| #21 | `build/agent7/s4-t1/RATE-REQUEST.md` | `AFE56587D955BD7AE1CD38D579BF371ABC3231E214C1C2DB640224CF35137BB1` | 18608, 23:25 | for Agent 10 (not yet rated) |
| #21 | `build/agent7/s4-t1/SHA256SUMS.txt` | `88757918854576E81F7D1CA9D3BDCF1EA981B0CC02FF74C0BB87572954E05A8F` | 970, 22:48 | all 7 listed files re-hashed at 05:57: match |
| #21 | `build/agent7/s4-t1/README.md` | `D81A55AE95EA979AA4D6D02788DFD84BCDF689AF70357E45BEB34F897281FB3A` | 3374, 23:27 | staging index |
| #21 | `build/agent7/s4-t1/check/DIFF-REVIEW.md` | `820FA1914BF850D22E776CABD34D38771D5409989879988CDD25DA0C62560202` | 15633, 23:25 | review: no BLOCKER; S1 fixed in rev 2 |
| #21 | `build/agent7/s4-t1/FUNCTIONAL-ROWS.md` | `4814ACF28B010ABDE44735E8E24EFC50486370472C1128A3D5DE3D39EAC3184D` | 13944, 23:27 | rows F1/F3/W1 |
| #21 | `build/agent7/s4-t1/make_s4t1.py` | `45FD9737CE9B349A01D2D2B3A4399ED4C56B899743CB934FDCDA772D495E7E38` | 21094, 22:48 | generator + proofs 1-6 |
| #19 | `build/agent7/s4-r1s2/NOTE.md` | `424C8231CB21671F2D435B8F73E5EE8037E05EAC07343B05A6E36CFE54382691` | 19768, 23:20 | design note |
| #19 | `build/agent7/s4-r1s2/SHA256SUMS.txt` | `8A38FD9D3CD8B3752A5319B09BA3B9F61203ADEA35A5B99F8F6427F725CA9C5B` | 1382, 23:10 | diff and new-file hashes re-checked: match |
| #19 | `build/agent7/s4-r1s2/README.md` | `C30CEC564DCA49A7C864F59A4572D556ABD53099D19F43A3B02F947661013F93` | 2154, 23:32 | staging index |
| #19 | `build/agent7/s4-r1s2/PROOFS.txt` | `FF360AC9474397789FB63F44C429A8153E39147635BF04A72AF388AB92A62F11` | 7131, 23:10 | P1-P10 ALL PASS |
| #19 | `build/agent7/s4-r1s2/CHECKS.txt` | `6C4C1A5DEED262F9D9ACC65769045ACFE6A569260DC80E85045E140FAAF32914` | 1627, 23:13 | Agent 7's apply checks on orig/new |
| #19 | `build/agent7/s4-r1s2/make_s4r1s2.py` | `4AD0BD45A51327B82C57C50260373EEC16EA0C3518B991B64B1E8E9D5320E51E` | 29958, 23:10 | generator (E1-E16) |
| #19 | `build/agent7/s4-r1s2/FUNCTIONAL-ROWS.md` | `0FE4E1D92DA092BBEBCDAD94F039A01512757D50EF4E5660865660588441E9EC` | 5512, 23:31 | 9 rows (first draft) |
| #19 | `build/agent7/s4-r1s2/SOAK.md` | `780BF8E93C5363DBB317FCD5504ED27FA243DFF4B10B2484F9330FB1EA28F40D` | 2503, 23:32 | 10-min soak (first draft) |
| #19 | `build/agent7/s4-r1s2/matrix-w7-draft.json` | `6F7DFC63859516A312B6C3234B9621AB13D5BD20BB053DBB5E9BD95357CFBFC9` | 6239, 23:28 | W7 draft (Agent 8 owns the final) |
| #19 | `build/agent7/s4-r1s2/queue-s4r1s2.jsonl` | `175723608FD20891CC0DACB18011856692EDEA7D63283CD378C3846452B81E74` | 5357, 23:31 | Agent 3 queue rows |

### 1c. Other files Agent 2 put in `build/agent2/pending/` (06:07:55-56; outside items a-e)

| path | sha256 | bytes, mtime | base | applies? | note |
|---|---|---|---|---|---|
| `build/agent2/pending/plume-local-on-e0c8871.patch` | `BF38B18300164ECF3817D16082377BBB5BA456D725A86008DE08AF216ADDCBF8` | 35607, 06:07:55 | plume `e0c8871b930d…`, the checked-out HEAD of `DimensionsRecomp/thirdparty/plume` and `prepare_plume.py`'s PIN (L9) | **already in the live plume tree**: forward exit 1, `-R` exit 0 | 700 lines, 32 hunks: `plume_d3d12.cpp` (25; live `564568D4…` = S1+p2, agent10-batch2-review L72), `plume_d3d12.h` (5; live `2F8B444C…`), `plume_vulkan.cpp` (2; live `71938A4C…`). Uncommitted on purpose; it is rebuilt from the tracked `tools/gpu-aot/prepare_plume.py` + `tools/gpu-aot/patches/` (SESSION2 L3310). Game HEAD's gitlink pins plume `ceaeeee0f7e9…`, not e0c8871 (§2f) |
| `build/agent2/pending/simde-local-on-71fd833d.patch` | `2A6DE738794F5DA059934444CC327082DDEEB24D8C78F56DB487A9DF9EBF27DC` | 1122, 06:07:56 | simde `71fd833d9666…` = SDK HEAD's gitlink = the checked-out HEAD = `prepare_simde.py`'s PIN (L9) | **already in the live simde tree**: forward exit 1, `-R` exit 0 | 21 lines, 1 hunk in `simde/x86/sse.h` (`simde_mm_stream_pi`: native `__m64` under Windows Clang). **Byte-identical** to the tracked SDK file `patches/simde-native-m64-stream.patch` (same sha256; last changed in SDK commit f7c8f5e, 2026-10-07), which `scripts/prepare_simde.py` applies (SESSION2 L3310) |

## 2. Per-item notes, with sources

Apply checks against the working tree (== HEAD): the first 9 rows at 06:01:53, the rest at 06:14-06:16.

| command (`git --no-optional-locks -C <dir> apply --check …`) | exit |
|---|---|
| `-C DimensionsRecomp … ../build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-A.diff` | 0 |
| same with `-R` | 1 |
| `-C DimensionsRecomp … ../build/agent9/s4/spin/db16cyc-pause/toml-db16cyc-pause-B.diff` | 1 |
| `-C DimensionsRecomp/rexglue-sdk … ../../build/agent9/s4/spin/db16cyc-pause/db16cyc-pause.diff` | 1 |
| same with `-R` | 0 |
| `-C DimensionsRecomp … --directory=rexlego ../build/agent7/s4-t1/s4-t1.diff` | 0 |
| same with `-R` | 1 |
| `-C DimensionsRecomp/rexglue-sdk … ../../build/agent7/s4-r1s2/s4-r1s2.diff` | 0 |
| same with `-R` | 1 |
| `-C DimensionsRecomp … -p2 -v ../build/agent2/pending/cg26-toml.diff` | 0; git prints `Checking patch rexlego/legodimensions_config.toml => agent2/cg26/DimensionsRecomp/rexlego/legodimensions_config.toml...` |
| no `-C` (from the workspace root): `… -v build/agent2/pending/cg26-toml.diff`, then with `-R` | 0 and 0, but `-v` printed `Skipped patch …`: **not a check** |
| `-C DimensionsRecomp/thirdparty/plume … ../../../build/agent2/pending/plume-local-on-e0c8871.patch` | 1 |
| same with `-R` | 0 |
| `-C DimensionsRecomp/rexglue-sdk/thirdparty/simde … ../../../../build/agent2/pending/simde-local-on-71fd833d.patch` | 1 |
| same with `-R` | 0 |

### 2a. CG26 = #26 `db16cyc_pause` ON

- **What it is.** S4-DRAFT L237 (row 26): a codegen option `db16cyc_pause`, default OFF, set in the codegen config `rexlego/legodimensions_config.toml`. Turning it ON means the toml line, a regen (20 sites in 10 TUs) and a rebuild. The tool side (the SDK option) is committed: SDK HEAD config.cpp L129-130 and builders/system.cpp L53 (`git grep` at HEAD), and COMMIT-CHECK L46-48.
- **Staged** by Agent 9, 11-22 14:14-14:22, under Agent 9's task #17 (a9 R2.17, about L2070-2191; the diff hashes at a9 L2127 and L2131; b2r L49). The arms are "A for S3d and B for batch-nolr" (S4-DRAFT L325). base-A was copied from live at 14:14 and is byte-identical to HEAD's toml today.
- **Rated** by Agent 10 ~14:45 (b2r row 37 L49; §36 L1948-1966). Landing OFF is SAFE. ON is output-identical and SAFE to test after 4 gates:
  1. the toml line and the new tool in one build;
  2. exactly 20 pauses in the arm's 10 TUs;
  3. keep codegen.partition.json;
  4. the functional pair, then a frame-time A/B, measured apart from #24.

  b2r L1965: toml A applies exactly on base-A, live and snap1; toml B on base-B, snapB and batch-nolr.
- **Re-checked today:** arm A applies to HEAD and is not applied yet; arm B does not apply to HEAD; the SDK diff is already in HEAD (table above).
- **Hashes:** the 7 hashes (3 diffs, base-A, new-A, base-B, new-B) match HASHES.txt / a9 L2127-2131 and agent2-baseline. The `base/` and `new/` SDK files match COMMIT-CHECK's before/after (L46-48).
- **Agent 2's prep:** `build/agent2/cg26/` holds:
  - a copy of the tool;
  - the toml (new-A since 20:54:29);
  - the manifest;
  - `generated/` (a copy of snap1's);
  - stage-cg26.py and cg26-check.py.

  Sources: agent2-baseline L47, L55-57, L77-81. The resume recipe is at agent2-baseline L60-63.
- **Agent 9's check kit:** a9 R2.18, L2322-2439 (run command L2349-2353; ALL OK 14/14 at L2411; new checker hash at L2437). agent2-baseline L26 quotes the checker as `A179EB13` (runs 1-2). The file today is `DDBA731C…` (since 22:53).
- **Not built:**
  - agent2-baseline L50 (22:30): "CTR and CG26 move to after tonight's windows"; also L22-25;
  - SESSION2 L3312: no builds this morning;
  - `build/agent2/devoff4b-cg26-bin` does not exist.
- **What would change in the trees if arm A lands:** one tracked line in `rexlego/legodimensions_config.toml`. `rexlego/generated/` is untracked (COMMIT-CHECK L14: 0 generated/ files skipped; it was not in `ls-files` when I checked earlier), so git would not show the regen output. The tool is already in HEAD.

### 2b. CTR = the `REX_D3D12_DEFERRED_COUNTERS=1` build variant

- **The code** is the #20 step 1 counters, in SDK HEAD `src/graphics/d3d12/deferred_command_list.cpp`:
  - L21, a comment: "Build this file with -DREX_D3D12_DEFERRED_COUNTERS=1";
  - L26-27: `#ifndef` / `#define … 0`;
  - guarded blocks at L30-35, L39-216, L236-416, L421-423 and L659-681 (`git grep` at HEAD).
- **No CMake option and no other tracked definition.** At HEAD, `git grep` finds the macro nowhere else in the SDK and nowhere in DimensionsRecomp (exit 1).
  - S4-DRAFT L483: "#20 step 1's counters are a one-TU compile macro, `REX_D3D12_DEFERRED_COUNTERS` (default 0; Agent 7)".
  - b2r L2218 (Agent 10's FYI): the macro is only in that file, so the class layout doesn't change, and the one-TU `recompile.py` + `relink.py` route is enough.
- **So CTR is a build variant only; nothing in the trees changes.** Agent 2's inputs are in `build/agent2/ctr/` (lists at 20:15, recompile and relink dry runs at 20:31, empty obj folders). Recipe: agent2-baseline L58-60. Target bin: agent2-baseline L679 (`build/agent2/devoff4b-ctr-bin`; `devoffB4b-ctr-bin` for the B line). Neither exists.
- **Status:** not built (agent2-baseline L50; SESSION2 L3312). The code is rated as part of #20 step 1 (SAFE, S4-DRAFT L224).
- The .tsv lists and the recompile logs hold machine-specific absolute paths. They are not copied here.
- A tracked switch (e.g. a CMake option) would be a new change. None is staged.

### 2c. B4

- **Plan:** agent2-baseline L119-121 (task #15, section 2): the B line + S4a = devoffB4 + nativeB4. From `b4-dryrun-1424.txt`:
  - [1]: the 6 S4a files;
  - option B's apply list = 4 rexlego files + 31 others = 35 copies into snapB;
  - nativeB4 = 6 copies into snapB3;
  - SUMMARY: 0 FAIL, 0 WARN.

  `prep-b4-1546.txt`: dry run, 0 FAIL, "READY for --go" once the running game ends.
- **`run-b4.ps1` L1-4 and header:** it uses Agent 9's batch-nolr codegen (pins SHA256SUMS `24CE1493…` and toml `E60EAF1C…`) plus the S4a sources, linked against snap1-sdk/install, which is the S4a SDK. The header says "B4 runs before any S4b SDK build".
- **Status: deferred.**
  - S4-DRAFT L401: window 4's result at 16:17 showed no frame-time change, so W5 ran on the S3d line and B4 was deferred.
  - Also S4-DRAFT L471 and agent2-baseline L99 ("B4 stays deferred") and L115.
- **Since then:**
  - snap1 and HEAD moved to S4b/S4c, so run-b4.ps1's pins (the S4a SDK; the compare bins devoff4-bin and native4-bin) no longer match HEAD.
  - Codegen B showed no gain in W4c (lean: drop B).
  - I found no note that formally drops B4.
- **Not verified:** B4's delta against HEAD. HEAD contains S4a (then S4b/S4c), so the tree-level part would probably reduce to codegen B's toml plus a regen. I did not diff snapB/snapB3 against HEAD.

### 2d. Codegen B

- **What it is:** the batch-nolr codegen config (Agent 9, task #8; `build/agent9/configs/batch-nolr.toml`, 11-21 23:52).
- **Against HEAD's toml:** 16 lines are added at B L24-39 and none are removed (Compare-Object at 06:01; 815 → 831 lines). The 16 lines are:
  - 2 comments;
  - the 4 `*_as_local` keys;
  - a comment;
  - `cr_compare_so_zero`, `rlwinm_lowering`, `flush_mode_elision`, `vmx_vector_fallbacks`;
  - a comment;
  - `musttail_calls`;
  - 2 comments (skip_lr/skip_msr "Not for LEGO"; Stage B/C later);
  - a blank line.

  No git-format diff file exists.
- **Rating:** agent1-tracker-s2 L273 (11-21 23:48): SAFE (default and ON) EXCEPT skip_lr, which is not set.
- **Timing:**
  - W4b hint: fps +6.0 % [+0.5, +11.8], n = 3 (SESSION2 L2788).
  - W4c (02:39-03:05): B median +1.3 %, fps -0.4 %, slower in 5 of 6 rounds (SESSION2 L3252-3258). The second pass was skipped (L3298).
  - S4-DRAFT L13: "Lean: drop B". L14: the decisions rest on the formal read-outs (Agents 7 and 8, ~10:00) and Agent 6's logdiffs.
- **Bins on S3d:** devoffB-bin and nativeB-bin (agent2-baseline L218, where nativeB-bin is staged 11-22 04:34; agent8-window3 L198).
- **Other B configs:**
  - batch.toml is superseded (it has skip_lr; a9 L1571);
  - rb1-nolocal and rb2-nomusttail are rollbacks (a9 L894-895) that were never used (agent10-codegen-review L505).
- **`build/agent2/B-diffs/*.diff`** (11-22 02:20) are diffs of Agent 2's own B-line build tools, per their `---`/`+++` headers. They are not tree diffs; listed for completeness.

### 2e. #21, #19, #33, #34

- **#21** (S4-DRAFT L225): S4-T1, env `LEGO_NATIVE_CHAIN_PRIORITY=1`. It touches `native_worker.cpp:346`, `native_recording.cpp:138` and `native_preparation.h:21-26` (line numbers as given in the row). "Not rated".
  - Proposed under Agent 7's task #26 (S4-DRAFT L225, L540); staged under task #17 (README L1).
  - Rev 2 is from 22:48 (README L4). README L28-30 has Agent 7's own apply checks on before/after.
  - README L33-40 is the 23:27 update after Agent 9's pre-read (`build/agent9/s4-t1-preread.md`); no code, diff or hash changed.
  - SHA256SUMS.txt matches all 7 files. Game HEAD has no `LEGO_NATIVE_CHAIN_PRIORITY` (`git grep` exit 1).
- **#19** (S4-DRAFT L223): R1 stage 2, cvar `d3d12_async_submit`, OFF. The row still says "design only", but Agent 7 staged the diff at 23:10 (README L1-18). SDK HEAD has no `d3d12_async_submit` (`git grep`).
  - README L3-4: asked by Agent 1 (~22:29). The target is "ready for Agent 10 by Monday ~09:00, so W7 can run Monday night".
  - README L18: RATE-REQUEST.md "to do (Monday morning)".
  - README L21-22, open dependencies: `<N>` comes from Agent 3's ready-N gate, and a syntax check is needed once compiles are allowed.
  - b2r L1363: not rated; §17 condition 6 calls it the risky part.
- **#33** (S4-DRAFT L249): "Don't wait for pipelines".
  - Scope: SDK `d3d12/pipeline_cache.cpp/.h`, optionally `command_processor.cpp`; placeholder cvar `d3d12_async_pipeline_no_wait` (false).
  - Not rated; its effect is visible (pop-in).
  - Design: `perf-notes/agent6-attract-stalls.md` L215, L301, L441-462.
  - The user said yes, opt-in and OFF by default (SESSION2 L3196; S4-DRAFT L455-457).
  - It needs Agent 6's implementation, Agent 10's rating, a build, and the user's look at it (SESSION2 L3196, L3198).
- **#34** (S4-DRAFT L250): a dropped-draw counter at SDK `d3d12/command_processor.cpp:2727`; optional; not rated. That line number comes from the row. It probably predates the S4b changes to cp.cpp, and I did not look for it in HEAD.
- **Where I looked for #33/#34 code:**
  - depth-1 `*.diff`/`*.patch` under `build/agent6/`: only `draw_async/raw*.patch` and `fix-a/*.patch`, from 11-21 and unrelated;
  - `build/agent6/attract-stalls/` (30 files: analysis reports, no diff);
  - `hang/`, `wnight/`, `w6/` and `s10-2/` (checked earlier): nothing.

### 2f. The 3 files Agent 2 added to `build/agent2/pending/` (06:07:55-56)

Agent 2 wrote these while this draft was being written. Below is what I checked; their purpose is Agent 2's to state.

- **`cg26-toml.diff`** (§1a, CG26 arm A):
  - It has the same hunk as `toml-db16cyc-pause-A.diff`: `@@ -21,6 +21,7 @@`, the same 6 context lines, and `+db16cyc_pause = true` just before `[functions]`. Only the paths differ, plus an `index 2233e63..c946aed` line that toml-A.diff does not have.
  - `2233e63` is HEAD's blob for the toml (`git ls-tree HEAD rexlego/legodimensions_config.toml` → `2233e6343b7d…`), so its base is HEAD.
  - It is a no-index diff made from the workspace root: a-path `DimensionsRecomp/rexlego/legodimensions_config.toml`, b-path `build/agent2/cg26/DimensionsRecomp/rexlego/legodimensions_config.toml`.
  - With `-C DimensionsRecomp -p2`, `--check -v` exits 0 but names the change `rexlego/legodimensions_config.toml => agent2/cg26/DimensionsRecomp/rexlego/legodimensions_config.toml`. git treats the two sides as different files, so a plain `git apply` would not just edit the toml in place. What it would write instead was not tested (that needs a write).
  - I did not run `-R` in DimensionsRecomp: the reverse source path (`agent2/cg26/…`) does not exist there, so it would fail for an unrelated reason. toml-A.diff's `-R` exit 1 already shows the line is not in HEAD.
  - For HEAD, toml-A.diff (run with `-C DimensionsRecomp`) or a copy of new-A gives the intended file.
- **`plume-local-on-e0c8871.patch`** (§1c):
  - `DimensionsRecomp/thirdparty/plume` is checked out at `e0c8871b930d…` (2026-09-03, "add R11G11B10_FLOAT and D24_UNORM_S8_UINT render formats"), which is `tools/gpu-aot/prepare_plume.py`'s PIN (L9). The live tree carries the patch (forward exit 1, `-R` exit 0).
  - SESSION2 L3310 (Agent 1, 05:44): third-party worktree changes stay uncommitted; plume is rebuilt from `tools/gpu-aot/prepare_plume.py` + `tools/gpu-aot/patches/` ("winsdk-compat holds S1+p2"). Both are tracked at game HEAD (`ls-files`: prepare_plume.py, test_prepare_plume.py and 7 `plume-*.patch` files).
  - Game HEAD's gitlink for `thirdparty/plume` is `ceaeeee0f7e9…` (`ls-tree`; last changed in c0172a9, 2026-10-03). The local plume clone does not have that commit (`git log ceaeeee…` → "bad object"). agent1-pause-state-lines.md L128-130 (11-22, file time 01:37) says the same (ceaeeee is not in the public plume clone; HEAD e0c8871 is prepare_plume's PIN) and "Do NOT commit the plume pointer". So a plain `git submodule update` would look for ceaeeee, not e0c8871 (not tried).
  - Not checked: that the 7 tracked patches, applied to e0c8871, give this patch byte for byte. agent1-tracker-s2 L208 records the 7-patch chain as byte-identical to `564568D4` (plume_d3d12.cpp), and agent10-batch2-review L178 records `prepare_plume.py --check` PASS (11-22).
- **`simde-local-on-71fd833d.patch`** (§1c):
  - `DimensionsRecomp/rexglue-sdk/thirdparty/simde` is at `71fd833d9666…`, which is SDK HEAD's gitlink and `scripts/prepare_simde.py`'s PIN (L9). The live tree carries the patch (forward exit 1, `-R` exit 0).
  - It is byte-identical to the tracked `DimensionsRecomp/rexglue-sdk/patches/simde-native-m64-stream.patch` (both `2A6DE738…`, 1122 B, 21 lines; Compare-Object finds no difference). So it is already in the SDK tree, as prepare_simde's input.
  - Sources: SESSION2 L3310; agent1-tracker-s2 L13, L25-29, L49 (S2 build notes on prepare_simde).

## 3. Not found, or unclear

1. **#33:** no diff, patch or after-file anywhere I looked. Design only.
2. **#34:** the same.
3. **CTR:** no diff and no CMake option. By design, the variant is the `-D` define on one TU.
4. **Codegen B:** no git-format diff against HEAD, only full toml files. §2d describes the 16-line delta.
5. **B4:** no tree diff; it is a plan of file copies between snapshot trees. Deferred. Its scripts pin the S4a SDK, so they no longer match HEAD. I found no note that formally drops it.
6. **#19:** RATE-REQUEST.md is not written (README L18 says "to do (Monday morning)"; not in the folder at 05:57).
7. **Agent 10 ratings:** none found for #19, #21, #33 or #34.
8. **Bins:** no CG26, CTR or B4 bin exists (`devoff4b-cg26-bin`, `devoff4b-ctr-bin`, `devoffB4-bin`, `nativeB4-bin`, `devoffB4b-ctr-bin` are all absent).
9. **Older checker:** I did not look for Agent 9's earlier checker version `A179EB13` (runs 1-2) as a file; the kit's test-*/verify-* subfolders were not walked.
10. **Unclear:** whether CG26 arm B is still wanted. It only applies to the codegen-B line, and keep/drop for that line waits for the formal read-outs.
11. **Unclear:** B4's exact tree delta against HEAD (see §2c; inference only).
12. **Not checked:**
    - `git apply --check` of arm B against base-B/batch-nolr; I relied on b2r L1965 and the identical base hash;
    - the apply checks were run against the working tree, not with `--cached` (the game repo's index blobs are LF);
    - #34's cp.cpp line in HEAD.
13. **Line numbers:** S4-DRAFT's line numbers may move this morning (Agent 11 is updating it).
14. **cg26-toml.diff:** a real `git apply` of it was not tried (it writes). git reads its two paths as two different files (§2f), so it is not a drop-in for HEAD; toml-A.diff is.
15. **Plume:** I did not check that the 7 tracked plume patches on e0c8871 reproduce `plume-local-on-e0c8871.patch` exactly. I relied on the 11-22 records (§2f).
16. **Plume pointer:** game HEAD pins plume `ceaeeee…`, which the local plume clone does not have. The 11-22 notes call this deliberate (agent1-pause-state-lines.md L128-130). Unclear whether the resume notes mention it; I did not check them.
