# native4bp pack + bin (S5 phase 0.4b), agent16

Pipeline: dumped placement containers -> tools/gpu-aot (gradient compiler, microcode indexer, merge) -> lookup proof
-> native4bp bin (per-TU recompile + relink of the nativefinal2 recipe, staged next to nativefinal2-bin).
Everything is written under `build\agent16\pack\`. Nothing in agent2, other agent dirs, the repos or the dump dir is written
(the driver diffs listings of the watched dirs before and after each run and fails if anything changed).

## Files

| file | sha256 | role |
|---|---|---|
| `native4bp.ps1` | `83A8B01F375C7EDD5CC8E526A7B4306C9F72A41603F41CA08758542D8939F18C` | launcher: Idle priority + affinity 0x3 (inherited by children), `env\devshell.ps1 -Jobs 1 -Quiet`, then `python native4bp.py @args` |
| `native4bp.py` | `37FD3989880479C7D384D2F3FD8B61604360D1ECB6E8DA3BF81BFC0A180CA3E1` | driver: modes `plan` / `pack` / `bin`; refuses to run if not Idle and inside 0x3 |
| `check_pack.py` | `223A3A356287048AAA57E32DBCE5CEBC51A287DE405E5C5EFA50B452AF2D11F9` | s35 check_pack generalized to N containers (expected set = `<run>\runtime-input\STAGED.tsv`) |
| `run_lookup.py` | `5182AEB0487DE86A36F06BB7CDE9F78AFCB6323ACAFD4C2C678A1EE1FB6650EF` | s35 wrapper (SetErrorMode, then runpy test_placement_capture_lookup.py) |

## Commands

```
cd <workspace>
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native4bp.ps1 plan --input build\agent16\dump\pack-input-20261125-172422
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native4bp.ps1 pack --input build\agent16\dump\pack-input-20261125-172422
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native4bp.ps1 bin      # uses LATEST-pack.txt
```

Options: `--exclude NAME` (repeatable), `--no-default-exclude`, `--pack-run DIR`, `--bin-out NAME` (default `native4bp-bin`;
bin refuses to overwrite an existing dir), `--no-ctl`, `--jobs N` (default 2). `pack` without `--input` = the 4 s35 containers only.

## Modes

**plan**: writes only `plan-<stamp>.txt`. Checks every pack and bin pin (table below), checks the input dir against its
SHA256SUMS.txt, shows which containers are selected or excluded, finds clang++, and prints every command pack and bin would run.

**pack** -> `run-<stamp>\` (s35 layout):
1. Stage: the 4 pinned s35 containers plus every SHA256SUMS-verified container from `--input`, deduplicated by sha256.
   placement-raw is refused. Root/create-path dumps are excluded by default (see below). Any other container that fails the
   structure check fails the run. Writes `STAGED.tsv`.
2. `gradient_compiler.exe runtime-input runtime-cache.cpp shader_common.h` (XENOS_RECOMP_DXIL_ONLY=1, HLSL dump to `hlsl\`).
3. `lego_gpu_microcode_index.exe index-addition.cpp runtime-input`.
4. `merge_microcode_index.py` over the merge base nativefinal2 actually used:
   snap1 `out\native-gpu\lego-microcode-index.cpp` 2DB85917 (read from the snap1-on ccdb and verified by sha256).
5. `check_pack.py prelookup`, then `test_placement_capture_lookup.py` twice (pack alone, then with the snap1 main cache),
   then `check_pack.py post` -> `pack-check.json`.
6. Pins re-checked, watched-dir diff -> `side-effects.txt`, `SHA256SUMS.txt`, `LATEST-pack.txt`.

**bin** -> `binwork-<stamp>\{ctl,on}` and `<bin-out>\`. This is the build-final2 "nat" recipe on the build/agent2/snap1-on objects,
with recompile.py / relink.py / stage-variant.py / verify-bins.py used unchanged. Each variant (CTL = nf2 inputs, ON = pack inputs) runs:
1. A derived ccdb: the runtime-cache define changes from the stub (E66C9AA3) to the pack runtime-cache.cpp. The linked-bank
   metadata path changes to this variant's own embed output.
2. Recompile the prelink tool's runtime-cache TU and relink `lego_gpu_prelink_runtime.exe`. Run it (LEGO_GPU_PRELINK_JOBS=2)
   to get `runtime-linked-dxil-cache.cpp`, which links the spec-mask DXIL libraries.
3. `embed_linked_bank.py --runtime` (snap1 copy, llvm-mc) -> `linked-bank.obj` + `linked-bank-metadata.cpp`.
4. Fingerprint: final2's `fp-on.cmake` with paths swapped (ON also swaps the index, runtime cache and runtime-linked cache)
   -> `gen\native_gpu_build_info.h` + `gen\native-gpu-build.txt`. Python recomputes it independently over the same input list.
5. Recompile 7 TUs (index, runtime_shader_cache, runtime_linked_shader_cache, device, pipeline_library, shader_archive,
   final2-overlay shaders.cpp) with `--include-first gen`. Relink legodimensions.exe, replacing those 7 objs and `linked-bank.obj`.
6. CTL gates, all required: prelink output = snap1 A479268E; embed = snap1-on generated; fingerprint 1616ce65e973c583 with
   header+txt identical to final2 gen-on; exe = nf2 except TimeDateStamp; map = nf2 except the Timestamp line.
7. ON gates: new fingerprint in the exe and the old one absent; no overlay/agent16 path bytes; exe differs from nf2;
   pe-check (exports/imports) = nf2; mapcheck `--mode same` vs the nf2 map.
8. `stage-variant.py --base nativefinal2-bin` replaces exe+map and writes a MANIFEST in agent2 format (header line is
   stage-variant's fixed "Agent 2 (board run 2 task #1)" text). Then `verify-bins.py`, then `LATEST-bin.txt`.

## Pins (checked by plan/pack/bin)

| key | path | sha256 |
|---|---|---|
| gradient | build\agent6\aot\gradient-build\gradient_compiler.exe | 705980C4F6071E9B675DFBB57A33ED64C0C74BA6F8172FD7094850A76371A653 |
| dxcompiler / dxil / fmt | build\agent6\aot\gradient-build\*.dll | 0689E2FE… / 64BE2368… / BB89FF51… |
| common | DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h | 362E9EDBA0B9E4AC156982E7D75A70AF1341C6E1F1F52139BE03978DB3AA1E8F |
| indexer | build\agent6\aot\microcode-index\lego_gpu_microcode_index.exe | 3B5A68FE447DF23D46BCFF7913E590A8AF4A14A2FBBE28453B17EB23144BB9A1 |
| oldindex (merge base) | build\agent2\snap1\...\out\native-gpu\lego-microcode-index.cpp | 2DB859177B4656477D2858B87F37E7F068CABA420362FA21AFA1B3C8C6DD13A2 |
| maincache | build\agent2\snap1\...\out\native-gpu\aot\lego-dxil-cache.cpp | FF9386C1CD435E7EE12781F43A6F42F97AED7062A4147D4E649AF2450157A819 |
| merge | DimensionsRecomp\tools\gpu-aot\merge_microcode_index.py | 20986E998AB8B6F83FC0390A15A45DABB86F37E81206A9ED06D06E205DDB1BE2 |
| lookup | DimensionsRecomp\tools\gpu-aot\test_placement_capture_lookup.py | 856D0A8E0E827D6AECF99FC0D34DDCCB0FE0F182D9EE372A20048FDC3350058B |
| archive / snaparch | shader_archive.cpp (repo = snap1) | 1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC |
| recompile / relink / stage | build\agent2\{recompile,relink,stage-variant}.py | 855BCC79… / F3C6EEAF… / D2BD1C63… |
| verifybins | build\agent2\session3\verify-bins.py | 80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E |
| ccdb / ninja | build\agent2\snap1-on\{compile_commands.json,build.ninja} | A8146295… / 5AB81775… |
| fpon / gen-on h / txt | build\agent2\final2\b\nat\… | EF78BF00… / 8511FF42… / BC37A606… |
| stubcache | snap1 out\native-gpu\stubs\runtime-cache.cpp | E66C9AA34C301C60003F18AE62B6496041F59123DC1372DAC5C393C7BE88053D |
| rlcache | snap1 out\native-gpu\runtime-linked-dxil-cache.cpp | A479268EB611CDC52FD52AD1F76A5857587CD67E776F431E9B1BE320FFD4896D |
| prelinkexe | build\agent2\snap1-on\lego_gpu_prelink_runtime.exe | 4BB316E898757F192899E52EE06D2C3B67E4E261983B48BA015419488A7283A8 |
| nf2 exe / map / MANIFEST | build\agent2\nativefinal2-bin\… | 090A420B… / B669786E… / 4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163 |

The full list, with complete hashes, is `PINS_PACK` / `PINS_BIN` in `native4bp.py`. The s35 containers are pinned by the sha256 values in build\agent4\s35\README.md.

## Inputs and exclusions

`pack-input-20261125-172422` has 79 placement containers plus 2 root (create-path) dumps. The pack set is the 4 s35 containers
+ the 79 = **83**. Default exclusions:
- `vs-A58EBA123EFB541C.bin` (704 B): a memexport VS from the create path. gradient_compiler rejects memexport, and the file is not a placement container.
- `ps-93B9F93B535E7CCA.bin` (156 B): a create-path dump with no virtual/physical placement layout, so it is not compiler/indexer input.

## Pass criteria

- **pack**: every tool exits 0. Both lookups print `PASS: N captured containers ...` with N = the staged count. check_pack post
  has 0 FAIL, and the runtime cache holds exactly the staged set (overlaps with the old index or main cache are only warnings).
  The run causes no side effects, and the pins are unchanged afterwards. Verdict line `VERDICT PASS`.
- **bin**: all CTL gates PASS (proves the recipe reproduces nativefinal2). All ON gates PASS. stage-variant exits 0.
  verify-bins `RESULT: 0 FAIL`. `LATEST-bin.txt` = PASS.

## Results (2026-11-25)

| run | exit | wall | result |
|---|---|---|---|
| plan (`plan-20261125-173719.txt`) | 0 | seconds | PLAN OK: 0 bad pins, 0 input failures, 83 selected, 2 excluded (`plan-…173707` = first try, failed the self-check because of a ctypes bug, since fixed) |
| pack, real (`run-20261125-173813`) | 0 | 8.1 s | PASS: 423 checks, 0 FAIL, 0 warnings; lookup 83/83 and lookup-main 83/83; index 19116 -> 19267 rows; spec masks {0:22, 1:17, 2:44}; runtime-cache.cpp 9E11C59C…2915; index 401C1801…84F6 |
| pack, s35 stand-in (`run-20261125-174025`) | 0 | 5.2 s | PASS, 4/4; byte-identical to s35 (runtime-cache AEA36683…A734, index E4C05782…0617) |
| bin (`binwork-20261125-173830`, log `bin-console-1.txt`) | 0 | 70.1 s | PASS: all CTL + ON gates |

- **CTL**: the relinked exe = nativefinal2 except 1 TimeDateStamp; the map is equal except the Timestamp line. Prelink, embed and fingerprint
  (1616ce65e973c583) are byte-identical.
- **native4bp-bin**: MANIFEST sha256 `C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690`; exe
  `FA761654D665BC928B9FC82AC5DCE58E25EE2E87BF60ED519CC5480A3012187C`; map `493DA6DA6660CC9F9C5C923E4E29F9336AEA82721C5BB88B7DD044FB2D73CE2D`.
  The other 6 files are unchanged copies of nativefinal2-bin. verify-bins: 8 rows, 0 FAIL.
- **New native GPU fingerprint `39129c4c059be5f0`**, from `binwork-20261125-173830\on\gen\native-gpu-build.txt`
  (cmake = Python recompute over 271 inputs; the exe contains it and does not contain 1616ce65e973c583).
- The runtime-linked cache went from 0 entries (nf2, stub runtime cache) to 122 entries. runtime-linked-dxil-cache.cpp A858A335…E39B;
  linked-bank.obj 612932DE…3A40.

## Fingerprint behaviour

The fingerprint is a sha256 over the native GPU input list, which includes the runtime cache, the index and the runtime-linked cache.
It therefore changes with any pack change: 1616ce65e973c583 -> 39129c4c059be5f0. native-pso-recipes.bin and the seed are keyed by the fingerprint,
so **the first boot of native4bp is cold** (recipes rebuild). Compare warm-vs-warm runs only.

## Rollback

nativefinal2-bin (MANIFEST 4E5E2620…) stays the pin and is untouched. To roll back, run that dir. Its PSO recipes, keyed by
1616ce65e973c583, are still valid. native4bp-bin and the binwork/run dirs can be deleted at any time.

## Open risks

- Spec-mask DXIL libraries (61 of 83 containers have spec mask 1 or 2) only work through the runtime prelink output, which is
  embedded here. A runtime that skipped the linked bank would miss them.
- The memexport VS `vs-A58EBA123EFB541C` is left out (the compiler rejects memexport), so that draw still takes the miss path.
- Draws that missed before now get native shaders. Any draw that starts rendering, or renders differently, is a **visual change**.
  It needs a visual check before native4bp replaces nativefinal2.
- The lookup proof is static (production lookup over the captured containers). In-game hit rates are not measured here.
- The MANIFEST header says "Agent 2 (board run 2 task #1)". That text is fixed in stage-variant.py; the title after it is correct.
