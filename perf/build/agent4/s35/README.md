# build/agent4/s35: scratch AOT pack for the placement shaders (task (b), notes §S3.5)

Agent 4, 2026-11-22. **Scratch only.** Nothing here is applied, built, staged or copied into the game/SDK trees, the generated junction or any bin dir. The proposal it implements is [aot-pack-proposal.md](../s34/aot-pack-proposal.md) (Path A, steps 1-4 only).

## Why

Native placement draws bind VS `0xAC449538` (backing `0xED23D3E0`) and PS `0xAC448F28` (backing `0xED23D540`). Neither is in the AOT microcode index of any native2/native3 run (Agent 7, `perf-notes/agent7-present.md`, task #13 §3). A miss registers nothing, so every SetShader and the per-frame retry repeat the full FindShaderByMicrocode lookup under LockRecording: BindShader is 49 % of render-thread CPU in n-prof (6.10 of 12.36 ms/f). The draws that bind them are dropped through `binding_failed` (draw.cpp:2712-2725). This directory compiles and indexes the 4 captured placement containers offline and proves, through the production lookup code, that they would resolve.

## Approval and gates

- **Agent 1, 06:14, confirmed 06:31:** packing is OK on scratch only, in `build/agent4/s35/`. At most 2 threads at BelowNormal. No live apply, no bin, no writes to the game/SDK trees, the generated junction or any bin dir. Stop by 08:25 whatever the state; anything unfinished waits for S4.
- **Gate 1, MET at 06:22:** Agent 7 cleared the PS words (`build/agent7/sd/ps-words-check.txt`). Each PS physical section is `[64 B literal constants][microcode]`, with the microcode at physical offset 0x40, sizes 0x90 / 0x78, ending at physical_size 208 / 184. The VSs have their microcode at offset 0. The interpolator words match (0x2042 / 0x1021). Packing all 4 is OK if the entries cover the whole physical section.
- **Gate 2, MET at 07:01:** Agent 8 posted that its last run ended at 07:00:02, that its slot is over, and that none of its games or runners is running. `run_pack.ps1 -Go` also refuses to start inside Agent 1's 06:33-07:15 quiet window and after 08:05. The run started at 07:16:27.
- **Screenshot check:** the native vs Xenos screenshot check is an S4 step with the user (Agent 1, 06:14). It can't go in window 4, because W4b is frozen at d0/B/d3/d11t.

## Inputs (pinned, read in place, copied into `run-*/runtime-input/`)

From Agent 8's dump run `build/agent8/matrix/20261122-0509/runs/0509-sd-r1/shader-dumps/placement-containers/` (`LEGO_DUMP_MISSING_SHADERS=1`). The structure columns are from `check_pack.py precheck` (PlanOnly, 06:36: PRECHECK PASS).

| File | Role | Bytes | Stage | Physical | Microcode (offset+size) | sha256 |
|---|---|---:|---|---:|---|---|
| `vs-ACAF01F01E1C03D2.bin` | placement VS `0xAC449538` | 1304 | 0 (VS) | 324 | 0+324 | `6C4F65C3161DF6BEE23F9C551F34971D60275BB49C3DB6327CFF9084F4317A66` |
| `ps-75A4D1ABA62F7594.bin` | placement PS `0xAC448F28` (zero-prefix bucket) | 1716 | 1 (PS) | 208 | 64+144 | `09D05274AFBC26A2605D0B91E5C2A0E0C95303C4C0C84F4D463105EB678D66EE` |
| `vs-CCD7655302B54D80.bin` | second placement VS | 944 | 0 (VS) | 288 | 0+288 | `F4EE30B28DEE9E4AB5AE2E9204D54195A0AC9D8D5497B7F2C8FAC11D90EEC65E` |
| `ps-E81FD692C3AB35E1.bin` | second placement PS | 1640 | 1 (PS) | 184 | 64+120 | `58B4FA21E35500529895AA400F4B307F0DD09BBBBDB71F5C7C8E8748B31170F1` |

Both PS physical sections start with zero words, so their whole-section rows go into the zero-prefix bucket. Expected index addition: 6 rows. Each PS gets 2 rows (whole physical section, literal block included, and the instruction stream). Each VS gets 1 row, because its two signatures are identical and the indexer dedupes them.

**Not packed:**
- The start-up `vs-A58EBA12…` is the memexport VS. It is intentionally not shipped, because the compiler rejects it (`DimensionsRecomp/tools/gpu-aot/README.md:152-155`).
- The start-up `ps-93B9F93B…` is not a placement container.
- `placement-raw/` is never compiler input (README:146-147).

## Tools (sha256-pinned in `run_pack.ps1`, re-checked after the run)

| Pin | Path | sha256 |
|---|---|---|
| gradient | `build/agent6/aot/gradient-build/gradient_compiler.exe` | `705980C4F6071E9B675DFBB57A33ED64C0C74BA6F8172FD7094850A76371A653` |
| dxcompiler | `build/agent6/aot/gradient-build/dxcompiler.dll` | `0689E2FEE0A1C9DF8662A59680469F24E2A3AD7CE6BBBCC9284F7A83172BFC59` |
| dxil | `build/agent6/aot/gradient-build/dxil.dll` | `64BE2368211D257A038A7D4EA6BB3E24C878EB8D588C7B8414FCCF759B69C2AC` |
| fmt | `build/agent6/aot/gradient-build/fmt.dll` | `BB89FF51186F9E8F8F7CAE69E5A229C9D1D322562B033C0D8DD35071434A1FE5` |
| common | `DimensionsRecomp/rexlego/out/native-gpu/current-compiler/gradients/source/shader_common.h` | `362E9EDBA0B9E4AC156982E7D75A70AF1341C6E1F1F52139BE03978DB3AA1E8F` |
| indexer | `build/agent6/aot/microcode-index/lego_gpu_microcode_index.exe` | `3B5A68FE447DF23D46BCFF7913E590A8AF4A14A2FBBE28453B17EB23144BB9A1` |
| oldindex | `build/agent2/snap1/DimensionsRecomp/rexlego/out/native-gpu/lego-microcode-index.cpp` (19,116 records; native3d-bin's index; same sha as live) | `2DB859177B4656477D2858B87F37E7F068CABA420362FA21AFA1B3C8C6DD13A2` |
| maincache | `build/agent2/snap1/DimensionsRecomp/rexlego/out/native-gpu/aot/lego-dxil-cache.cpp` (9,601 entries, 35,058,115 B) | `FF9386C1CD435E7EE12781F43A6F42F97AED7062A4147D4E649AF2450157A819` |
| merge | `DimensionsRecomp/tools/gpu-aot/merge_microcode_index.py` | `20986E998AB8B6F83FC0390A15A45DABB86F37E81206A9ED06D06E205DDB1BE2` |
| lookup | `DimensionsRecomp/tools/gpu-aot/test_placement_capture_lookup.py` | `856D0A8E0E827D6AECF99FC0D34DDCCB0FE0F182D9EE372A20048FDC3350058B` |
| archive | `DimensionsRecomp/rexlego/src/gpu_native/shader_archive.cpp` (live; the lookup test compiles FindShaderByMicrocode from it) | `1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC` |
| archiveh | `DimensionsRecomp/rexlego/src/gpu_native/shader_archive.h` | `83B030F92C504D1FF5AD554371745A8DA38C52310B290DA9246A212CC3F743D5` |
| snaparch | `build/agent2/snap1/.../shader_archive.cpp` (native3d-bin's copy, equal to live) | `1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC` |

`check_pack.py` and `run_lookup.py` are mine; their sha256 is logged, not pinned. clang++ comes from `env/devshell.ps1` (llvm-23.1.6); python is 3.11.9.

## Files

- `run_pack.ps1`: the driver. `-PlanOnly` writes only `plan-HHmmss.txt`. `-Go -GateEvidence "..."` writes one `run-HHmmss/` directory. Before anything else it sets its own process to BelowNormal with the affinity mask (default 0x3, 2 CPUs; 1-2 CPUs allowed), so every child inherits both.
- `check_pack.py`: `precheck <dir>` parses the containers. `prelookup <run>` runs the static checks before any lookup, because a failed lookup ends in `std::abort`. `post <run> --out <run>/pack-check.json` runs every check.
- `run_lookup.py`: runs the unchanged `test_placement_capture_lookup.py` with `SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX)`, which its clang++ and `captured-lookup.exe` children inherit, so a failure exits with an error code instead of a crash dialog.
- `run-HHmmss/` contains:
  - `runtime-input/`, `logs/` (stdout/stderr of every tool), `hlsl/` (the HLSL dump), `work/` (the tools' cwd) and `tmp/` (TMP/TEMP);
  - `runtime-cache.cpp`, `index-addition.cpp`, `lego-microcode-index.cpp`, `merge-report.json`;
  - `lookup/`, `lookup-main/`, `pack-check.json`, `side-effects.txt`, `SHA256SUMS.txt`, `pack-log.txt`.
- `LATEST.txt`: the last run and its verdict.

## Steps (`-Go`)

1. Stage the 4 containers into `runtime-input/`, re-verify their sha256 and run `precheck`.
2. `gradient_compiler.exe runtime-input runtime-cache.cpp shader_common.h`, with `XENOS_RECOMP_DXIL_ONLY=1` and `XENOS_RECOMP_HLSL_DUMP=hlsl` (timeout 900 s).
3. `lego_gpu_microcode_index.exe index-addition.cpp runtime-input`.
4. `merge_microcode_index.py <oldindex> index-addition.cpp lego-microcode-index.cpp --report merge-report.json`. The merge refuses conflicts and asserts that every old row is kept.
   - 4b. `check_pack.py prelookup`. No lookup starts unless it passes.
5. `run_lookup.py test_placement_capture_lookup.py runtime-input lego-microcode-index.cpp runtime-cache.cpp lookup` (timeout 600 s).
6. The same with `--main-cache <maincache>` into `lookup-main/`, which exposes the main archive as gameplay does.
7. The finally block always runs:
   - diff the top-level listings of the 11 watched read-only dirs;
   - re-check every pin;
   - `check_pack.py post`;
   - write `SHA256SUMS.txt` and `LATEST.txt`;
   - log the VERDICT.

A timed-out tool has its process tree killed (`taskkill /T /F`).

## Pass criteria (VERDICT PASS = all of them)

- All tools exit 0.
- `runtime-cache.cpp` has exactly 4 entries, one per container hash, each with `dxilSize > 0`. The spec-constant masks are recorded.
- Per container, the index addition has:
  - a row with size == physical_size, i.e. the whole physical section with the 64 B literal block included (Agent 7's condition);
  - a row with size == microcode_size, i.e. the instruction stream;
  - the right stage on every row.
- The merge keeps all 19,116 old rows, and new = old ∪ addition with no duplicates. `merge-report.json` agrees.
- Negative controls: none of the 4 container hashes, and none of the new signatures, is in the old index; none of the 4 is in the main cache. This is why they missed.
- `lookup` and `lookup-main` both print `PASS: 4 captured containers`. That is the production FindShaderByMicrocode, compiled from live `shader_archive.cpp`, resolving both the physical start and physical+offset of every container to its exact XXH3 container hash.
- No listing change in the watched dirs, and every pin unchanged after the run.

## Why existing lookups don't change

FindShaderByMicrocode (`shader_archive.cpp:319-358`) works like this:
1. It takes the candidates of the span's prefix bucket (an unordered_multimap).
2. It hashes the guest span once per distinct candidate size (memoized within one lookup).
3. It returns the first candidate whose size-hash matches and whose container resolves through FindShader (main cache, then runtime cache).

A new row can match only a span that is byte-identical to one of the 4 new sections over that section's full length (64-bit XXH3). The negative control shows that no old row has any of the new signatures. Every old row is kept, so every span that resolved before still has its old candidate. The only cost is slightly bigger buckets, mainly the zero-prefix bucket, which gets 2 rows; `pack-check.json` reports `old_rows_same_prefix_and_stage` for each added row.

## Not done here (S4)

- **Spec-constant variants:** entries with a non-zero spec mask are DXIL libraries. They resolve only through the build-time prelinked runtime-linked cache (`lego_gpu_prelink_runtime`), which is part of Agent 2's S4 build.
- **Swap-in and bin (Agent 2, after Agent 1's GO):**
  - **Runtime cache.** `LEGO_NATIVE_RUNTIME_SHADER_CACHE` is a CACHE FILEPATH (`rexlego/CMakeLists.txt:283-285`). Agent 2's ON builds point it at a stub: `snap1-on` and `snapB3-on` use `<snap>/DimensionsRecomp/rexlego/out/native-gpu/stubs/runtime-cache.cpp`. Point it at a snapshot copy of `run-071627/runtime-cache.cpp` instead.
  - **Index.** `LEGO_NATIVE_MICROCODE_INDEX` is fixed at `${CMAKE_CURRENT_SOURCE_DIR}/out/native-gpu/lego-microcode-index.cpp` (CMake 274-275). Put `run-071627/lego-microcode-index.cpp` there in the snapshot, but only if the snapshot's copy is still the merge base `2DB85917…13A2`. If it isn't, re-merge `index-addition.cpp` into the new base with `merge_microcode_index.py`, which refuses conflicts.
  - **Prelink.** `LEGO_NATIVE_RUNTIME_PRELINKED_BANK` is empty in those builds. So the build re-runs `lego_gpu_prelink_runtime` (CMake 408-426 and 511-519) and writes `<snap>/rexlego/out/native-gpu/runtime-linked-dxil-cache.cpp`. That step is what makes the spec-mask 1/2 entries usable. In snap1, `rexlego/out` and `out/native-gpu` are plain directories, not junctions, so that write stays inside the snapshot.
  - **Copying.** `build/agent2/snap-native-inputs.py` copies only from the live `DimensionsRecomp/` tree. These two files live in `build/agent4/s35/run-071627/`, so they need either a direct copy with a sha check or Agent 2's own tooling.
  - There is no bin tonight.
- **Functional n-rows** on that bin (Agent 8). Pass rule: the miss lines for these 4 hashes disappear, with no new warning type (proposal §5).
- **Native vs Xenos screenshot check, with the user, in S4.** The placement draws stop being dropped, so the image changes.
- **(c) `LEGO_NATIVE_SHADER_MISS_CACHE`:** Agent 10 rated it SAFE at default OFF (batch2-review §18 plus addendum, row 19). It is parked for S4 and needs Agent 1's GO. The ON run must show `shader_miss_cache_insert` for VS `AC449538` and PS `AC448F28`.

## Results

PlanOnly (06:36, 1 CPU, `plan-063629.txt`): PLAN OK. All 14 pins and 4 inputs ok; PRECHECK PASS.

### `-Go`: `run-071627/`, VERDICT PASS (07:16:27-07:16:50)

The run used:
- `-GateEvidence "Agent 8 07:00:02: last run ended; slot over, no game or runner running (posted 07:01)"`;
- affinity 0x3 (2 CPUs) at BelowNormal;
- script sha256 `D29E23BEBD05C91A661E4A8E3E98BA3B2E3CFBDA485DF7B6ECFA7085C15E8669`.

Before it, a parse test of the main cache passed: `check_pack.read_cache` read 9,601 rows, and 9,601 are declared. `LATEST.txt` = `run-071627 PASS 07:16:50`.

| Step | Exit | Wall | Output |
|---|---:|---:|---|
| precheck | 0 | 0.2 s | 4 containers, structure OK |
| gradient_compiler | 0 | 0.3 s | `AOT coverage: 4 of 4 unique shaders (100.00%)`; 4 HLSL files in `hlsl/` |
| indexer | 0 | 0.7 s | `Indexed 6 shader microcode blobs` |
| merge | 0 | 0.4 s | 19,116 -> 19,122 rows, all prior records preserved |
| prelookup | 0 | 0.5 s | PRELOOKUP PASS |
| lookup | 0 | 6.9 s | `PASS: 4 captured containers` |
| lookup-main | 0 | 9.7 s | `PASS: 4 captured containers` |
| post check | 0 | 1.0 s | POST PASS: 28 of 28 checks ok, 0 fails |

- **VERDICT line:** `PASS (tools: ok; check exit: 0; side effects: 0; pins changed after: 0)`.
- **`side-effects.txt`:** none; the top level of all 11 watched dirs is unchanged.
- **`tmp/`:** 0 files left.

**Runtime cache.** `runtime-cache.cpp` has 4 entries, DXIL only: 9,340 B compressed, 18,936 B decompressed. SPIR-V is empty.

| Container | Role | dxilOffset | dxilSize | Spec mask |
|---|---|---:|---:|---:|
| `75A4D1ABA62F7594` | placement PS `0xAC448F28` | 0 | 4,644 | 2 |
| `ACAF01F01E1C03D2` | placement VS `0xAC449538` | 4,644 | 5,420 | 1 |
| `CCD7655302B54D80` | second VS | 10,064 | 5,100 | 1 |
| `E81FD692C3AB35E1` | second PS | 15,164 | 3,772 | 2 |

Spec masks 1 (VS) and 2 (PS) are the normal case. Re-counted at 07:20, the main cache has 8,329 entries with mask 2, 1,203 with mask 1 and 69 with mask 0. The build prelinks those through `lego_gpu_prelink` (CMake 428-432). These 4 entries are DXIL libraries too, so they need the S4 build's runtime prelink (see "Not done here").

**Index addition.** `index-addition.cpp` has 6 rows. The merged `lego-microcode-index.cpp` has 19,122 rows, all unique.

| Prefix | Microcode hash | Container | Size | Stage | Texmask | Old rows with this prefix and stage |
|---|---|---|---:|---:|---:|---:|
| `C77B3ABB6F87ACD9` (zero bytes) | `0DD13E570A16128B` | `75A4D1AB…` PS | 208, whole section | 1 | 1 | 6,636 |
| `D86762B2726966CC` | `D7F9D5BAED92E535` | `75A4D1AB…` PS | 144, instructions | 1 | 1 | 180 |
| `C77B3ABB6F87ACD9` (zero bytes) | `7143F73A2A70F633` | `E81FD692…` PS | 184, whole section | 1 | 0 | 6,636 |
| `F96898C29CD2C2A3` | `1ACEA61058153A20` | `E81FD692…` PS | 120, instructions | 1 | 0 | 0 |
| `DCD4AD8441398283` | `033935513ABF2DCB` | `ACAF01F0…` VS | 324, both | 0 | 0 | 21 |
| `98D43959C65B882A` | `3720347783993E3D` | `CCD76553…` VS | 288, both | 0 | 0 | 22 |

The prefix is `XXH3_64bits` of the first 8 bytes (`shader_archive.cpp:339`), not the raw bytes. So `C77B3ABB6F87ACD9` is the bucket of every section that starts with 8 zero bytes. It already held 6,636 stage-1 rows and 1,209 stage-0 rows; the two PS whole-section rows add 2.

**Negative controls (all ok):**
- none of the 4 container hashes is in the old index;
- none of the 6 new signatures is in the old index;
- none of the 4 containers is in the main cache (9,601 entries).

**Output sha256.** Every other file of the run is listed in `run-071627/SHA256SUMS.txt`.

| File | Bytes | sha256 |
|---|---:|---|
| `runtime-cache.cpp` | 33,765 | `AEA36683202B97535C52DFA7D7548EEBA1D3512E70717C2DE381FB59CC29A734` |
| `lego-microcode-index.cpp` (merged) | 1,672,272 | `E4C05782462452C3104A165AF588F21F42910FBD07A75A0071A34F89E3060617` |
| `index-addition.cpp` | 656 | `154242FB07BEDC92075585D96C714CFA5273824EEE4B5FA9690F46CFBD3398F6` |
| `merge-report.json` | 155 | `6DF8E65FF6A642357D5128FAD7A0E972E67E6A88E57F9790D7446A791D11AA1F` |
| `pack-check.json` | 12,132 | `0985CFF7CA53F2AE796E3CF0CBBCFFC703B59438F615DD4EC114860E34C0A0EB` |

Nothing was applied, staged or built. The S4 steps are under "Not done here (S4)" above.
